from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_enable_a4_printing = fields.Boolean(related='pos_config_id.enable_a4_printing', 
        readonly=False)