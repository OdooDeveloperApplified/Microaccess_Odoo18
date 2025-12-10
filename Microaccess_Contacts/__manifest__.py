{
    'name': 'Microaccess Contacts',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified contacts',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','contacts','hr','account','web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/contacts_template_views.xml',
        'views/contacts_category_master_views.xml',
    ],
    
    'assets': {},
    'installable': True,
    'auto_install': False,
}