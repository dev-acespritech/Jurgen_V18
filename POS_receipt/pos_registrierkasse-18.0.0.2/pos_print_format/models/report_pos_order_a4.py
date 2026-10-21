from odoo import _, api, models
from odoo.exceptions import UserError


class ReportPosOrderA4(models.AbstractModel):
    _name = 'report.pos_print_format.report_pos_order_a4'
    _description = 'POS Order A4 Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pos.order'].browse(docids)
        disabled = docs.filtered(lambda o: not o.config_id.enable_a4_printing)
        if disabled:
            raise UserError(_(
                "A4 printing is not enabled for the shop of order %s.",
                disabled[0].pos_reference or disabled[0].name))
        return {'doc_ids': docids,
            'doc_model': 'pos.order',
            'docs': docs,
            'data': data,
        }