{
    'name': 'POS Print Format',
    'summary': 'Per-shop A4 PDF receipt for RKSV-compliant POS',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'pos_registrierkasse'],
    'data': [
        'views/pos_config_views.xml',
        'views/res_config_settings_views.xml',
        'views/pos_order_views.xml',
        'report/paper_format.xml',
        'report/pos_order_a4_report.xml',
        'report/pos_order_a4_templates.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_print_format/static/src/app/*.js',
            'pos_print_format/static/src/app/*.xml'
        ],
    },
    'installable': True,
    'application': False,
}