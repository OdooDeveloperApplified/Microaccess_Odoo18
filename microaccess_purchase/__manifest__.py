{
    'name': 'PO Confirmation Changes Report',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified purchase',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_change_report_wizard.xml', 
        
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
}