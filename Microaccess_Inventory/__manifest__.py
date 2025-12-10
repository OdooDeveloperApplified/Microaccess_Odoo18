{
    'name': 'Microaccess Inventory',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified Inventory',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','sale','repair','purchase','stock','stock_account','Microaccess_Sales','purchase_stock'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/inventory_template_views.xml', 
        'reports/inventory_delivery_challan_views.xml', 
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
}