from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class PhysicalInventorySession(models.Model):
    _name = "physical.inventory.session"
    _description = "Physical Inventory Count"
    _order = "id desc"

    def _default_location_id(self):
        return self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        ).lot_stock_id

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda self: _("New"))
    date = fields.Date(default=fields.Date.context_today, required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    location_id = fields.Many2one(
        "stock.location", string="Stock Location", required=True,
        default=_default_location_id,
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [False, company_id])]",
    )
    partner_id = fields.Many2one("res.partner", string="Invoice Customer",
        domain="[('company_id', 'in', [False, company_id])]",)
    barcode_input = fields.Char(string="Scan Barcode", copy=False)
    line_ids = fields.One2many("physical.inventory.line", "session_id", string="Counted Products", copy=False)
    invoice_id = fields.Many2one("account.move", string="Generated Invoice", readonly=True, copy=False)
    state = fields.Selection([("draft", "Draft"), ("done", "Completed")],
                             default="draft", required=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("physical.inventory.session") or _("New")
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done(self):
        if any(s.state == "done" for s in self):
            raise UserError(_("A completed inventory count cannot be deleted."))

    # Barcode scanning

    @api.onchange("barcode_input")
    def _onchange_barcode_input(self):
        if not self.barcode_input:
            return
        barcode = self.barcode_input.strip()
        self.barcode_input = False  # always get the field ready for the next scan
        if not self.location_id:
            return {"warning": {"title": _("Location Required"),
                                "message": _("Select the stock location before scanning.")}}
        products = self.env["product.product"].search(
            [("barcode", "=", barcode), ("is_storable", "=", True)], limit=2)
        if not products:
            return {"warning": {"title": _("Barcode Not Found"),
                                "message": _("No storable product was found for barcode %s.") % barcode}}
        if len(products) > 1:
            return {"warning": {"title": _("Duplicate Barcode"),
                                "message": _("More than one product uses barcode %s.") % barcode}}
        if self.line_ids.filtered(lambda l: l.product_id == products):
            return {"warning": {"title": _("Already Scanned"),
                                "message": _("%s is already in this count. Edit its counted quantity.")
                                % products.display_name}}
        self.line_ids = [Command.create({"product_id": products.id})]

    def _prepare_invoice_vals(self, shortages):
        self.ensure_one()
        return {
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "invoice_date": self.date,
            "company_id": self.company_id.id,
            "ref": self.name,
            "invoice_origin": self.name,
            "invoice_line_ids": [
                Command.create({
                    "product_id": line.product_id.id,
                    "quantity": line.shortage_qty,
                    "product_uom_id": line.product_id.uom_id.id,
                })
                for line in shortages
            ],
        }

    def _apply_inventory_adjustment(self):
        """Set on-hand stock to the counted quantity with the standard quant API
        (stock.quant.inventory_quantity + action_apply_inventory). This is the only
        place stock moves are created; the invoice never touches stock."""
        self.ensure_one()
        Quant = self.env["stock.quant"].with_context(
            inventory_mode=True,
            inventory_name=_("Physical Inventory %s", self.name),
            set_inventory_quantity_auto_apply=True,)
        to_apply = Quant
        for line in self.line_ids:
            if len(self.line_ids) > 1 and line.counted_qty > line.existing_qty:
                continue
            product = line.product_id
            rounding = product.uom_id.rounding
            quants = Quant.search([
                ("product_id", "=", product.id),
                ("location_id", "child_of", self.location_id.id),
                ("company_id", "=", self.company_id.id),
            ]).sorted("id")
            diff = line.counted_qty - sum(quants.mapped("quantity"))
            if float_is_zero(diff, precision_rounding=rounding):
                continue
            if diff < 0:
                remaining = -diff
                for quant in quants.filtered(lambda q: q.quantity > 0):
                    take = min(quant.quantity, remaining)
                    quant.inventory_quantity = quant.quantity - take
                    to_apply |= quant
                    remaining -= take
                    if float_is_zero(remaining, precision_rounding=rounding):
                        break
            else:
                if product.tracking != "none":
                    raise UserError(_(
                        "%s is tracked by lot/serial. Quantity increases must be entered "
                        "with the standard Physical Inventory so the lot is known.")
                        % product.display_name)
                if quants:
                    quant = quants[0]
                    quant.inventory_quantity = quant.quantity + diff
                else:
                    quant = Quant.create({
                        "product_id": product.id,
                        "location_id": self.location_id.id,
                        "inventory_quantity": diff,
                    })
                to_apply |= quant
        if to_apply:
            to_apply.action_apply_inventory()

    def action_create_invoice_and_apply(self):
        if len(self.line_ids) == 1:
            line = self.line_ids[0]
            if line.counted_qty > line.existing_qty:
                raise UserError(_(
                    "%s: Counted quantity cannot be greater than recorded stock "
                    " Please use the standard "
                    "Physical Inventory workflow for stock replenishment."
                ) % line.product_id.display_name)
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("This inventory count has already been completed."))
        if not self.partner_id:
            raise UserError(_("Please select the customer before creating the invoice."))
        shortages = self.line_ids.filtered(
            lambda l: not float_is_zero(l.shortage_qty, precision_rounding=l.product_id.uom_id.rounding))
        if not shortages:
            raise UserError(_("There are no stock shortages to invoice."))

        invoice = self.env["account.move"].with_company(self.company_id).create(
            self._prepare_invoice_vals(shortages))
        self._apply_inventory_adjustment()
        self.write({"invoice_id": invoice.id, "state": "done"})
        return invoice.get_formview_action()


class PhysicalInventoryLine(models.Model):
    _name = "physical.inventory.line"
    _description = "Physical Inventory Count Line"
    _order = "id"

    _sql_constraints = [
        ("session_product_uniq", "unique(session_id, product_id)",
         "A product can only be counted once per inventory count."),
    ]
    session_id = fields.Many2one("physical.inventory.session", required=True,
                ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product", required=True,
                domain=[("is_storable", "=", True)])
    barcode = fields.Char(related="product_id.barcode", readonly=True)
    uom_id = fields.Many2one(related="product_id.uom_id", readonly=True)
    existing_qty = fields.Float(string="Recorded Stock",
                digits="Product Unit of Measure",
                compute="_compute_existing_qty", store=True, readonly=True)
    counted_qty = fields.Float(string="Counted Quantity",
                digits="Product Unit of Measure",
                compute="_compute_counted_qty", store=True, readonly=False)
    shortage_qty = fields.Float(string="Quantity to Invoice",
                compute="_compute_shortage_qty",digits="Product Unit of Measure")
    unit_price = fields.Float(related="product_id.lst_price", string="Sales Price", readonly=True)
    subtotal = fields.Monetary(compute="_compute_subtotal", currency_field="currency_id")
    currency_id = fields.Many2one(related="session_id.company_id.currency_id", readonly=True)

    @api.depends("product_id", "session_id.location_id")
    def _compute_existing_qty(self):
        Quant = self.env["stock.quant"]
        for line in self:
            qty = 0.0
            location = line.session_id.location_id
            if line.product_id and location:
                res = Quant._read_group(
                    [("product_id", "=", line.product_id.id),
                     ("location_id", "child_of", location.id)],
                    [], ["quantity:sum"])
                qty = res[0][0] or 0.0
            line.existing_qty = qty

    @api.depends("existing_qty")
    def _compute_counted_qty(self):
        for line in self:
            line.counted_qty = line.existing_qty

    @api.depends("existing_qty", "counted_qty")
    def _compute_shortage_qty(self):
        for line in self:
            line.shortage_qty = max(line.existing_qty - line.counted_qty, 0.0)

    @api.depends("shortage_qty", "unit_price")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.shortage_qty * line.unit_price

    @api.constrains("counted_qty")
    def _check_counted_qty(self):
        for line in self:
            if line.counted_qty < 0:
                raise ValidationError(_("Counted quantity cannot be negative."))