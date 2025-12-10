{
    'name': 'Microaccess Repair',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified Repair',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','repair', 'stock', 'Microaccess_Sales'],
    'data': [
        'security/ir.model.access.csv',
        'data/repair_sequence.xml',
        'reports/repair_delivery_challan_views.xml',
        'views/repair_template_views.xml',
        'views/repair_tag_views.xml',
       
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
}