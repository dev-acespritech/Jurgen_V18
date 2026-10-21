import base64

from odoo import _, fields, models
from odoo.addons.pos_registrierkasse.models.utils.order_utils import base64url_to_base64


class PosOrder(models.Model):
    _inherit = 'pos.order'

    a4_printing_enabled = fields.Boolean(related='config_id.enable_a4_printing')

    def action_print_a4(self):
        return self.env.ref('pos_print_format.action_report_pos_order_a4').report_action(self)

    def _a4_get_fiscal_data(self):
        """Fiscal data for the A4 report, taken only from fields written by pos_registrierkasse."""
        self.ensure_one()
        config = self.config_id
        data = {
            'rksv_active': bool(config.pos_use_registrierkasse),
            'signed': False,
            'kassen_id': config.name,
            'receipt_number': self.registrierkasse_receipt_number,
            'signed_date': False,
            'qr_value': False,
            'qr_data_uri': False,
        }
        if not (data['rksv_active'] and self.machine_readable_code and self.order_signature):
            return data

        qr_value = self.machine_readable_code + '_' + base64url_to_base64(self.order_signature)
        parts = self.machine_readable_code.split('_')
        if len(parts) >= 11:
            data['signed_date'] = parts[-9].replace('T', ' ')
        png = self.env['ir.actions.report'].barcode(
            'QR', qr_value, width=400, height=400, barLevel='M', quiet=False)
        data.update({'signed': True,
            'qr_value': qr_value,
            'qr_data_uri': 'data:image/png;base64,' + base64.b64encode(png).decode(),
        })
        return data

    def _a4_get_tax_summary(self):
        self.ensure_one()
        groups = {}
        for line in self.lines:
            rate = line.tax_ids[:1].amount if line.tax_ids else 0.0
            g = groups.setdefault(rate, {'rate': rate, 'base': 0.0, 'tax': 0.0, 'gross': 0.0})
            g['base'] += line.price_subtotal
            g['gross'] += line.price_subtotal_incl
            g['tax'] += line.price_subtotal_incl - line.price_subtotal
        return sorted(groups.values(), key=lambda g: -g['rate'])

    def _a4_get_lines(self):
        self.ensure_one()
        res = []
        for line in self.lines:
            discount = line.discount or 0.0
            unit_price = line.price_unit
            if line.qty and discount < 100:
                unit_price = line.price_subtotal / line.qty / (1 - discount / 100.0)
            res.append({
                'name': line.full_product_name or line.product_id.display_name,
                'qty': line.qty,
                'uom': line.product_id.uom_id.name,
                'unit_price': unit_price,
                'discount': discount,
                'taxes': ', '.join(line.tax_ids.mapped('name')),
                'amount': line.price_subtotal,
            })
        return res

    def _a4_get_payments(self):
        self.ensure_one()
        return self.payment_ids.filtered(lambda p: not getattr(p, 'is_change', False))

    def _a4_has_discount(self):
        self.ensure_one()
        return any(line.discount for line in self.lines)