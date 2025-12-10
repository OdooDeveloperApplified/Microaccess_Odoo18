{
    'name': 'Microaccess Product',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified Product',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','sale','stock','product'],
    'data': [
        'security/ir.model.access.csv',
        
        'views/product_brand.xml',
        'views/product_template_views.xml',
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
}