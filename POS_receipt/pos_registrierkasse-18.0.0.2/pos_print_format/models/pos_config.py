from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_a4_printing = fields.Boolean(string='Enable A4 Printing',default=False,
        help="Print an A4 PDF after payment instead of the standard POS receipt "
             "(this shop only).",)