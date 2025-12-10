{
    'name': 'SO Confirmation Changes Report',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified Sales',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_change_report_wizard_view.xml',
      
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
}