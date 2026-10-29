{
    'name': 'Report Layout Customization (Offer, Sales Order, Invoice)',
    'version': '18.0.1.1.0',
    'category': 'Sales/Accounting',
    'summary': 'Inherits sale & invoice QWeb report templates: address font, gray bordered table header, smaller QR',
    'license': 'LGPL-3',
    'depends': ['web', 'sale_management', 'account'],
    'data': [
        'views/report_style.xml',
        'views/sale_report_inherit.xml',
        'views/invoice_report_inherit.xml',
    ],
    'installable': True,
    'application': False,
}
