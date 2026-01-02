{
    'name': 'Migration',
    'version': '18.0.1.0.0',
    'category': 'CRM',
    'depends': ['crm', 'sale_management', 'base', 'purchase', 'Microaccess_Sales'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/contact.xml',
        'views/migration_connection.xml'
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
