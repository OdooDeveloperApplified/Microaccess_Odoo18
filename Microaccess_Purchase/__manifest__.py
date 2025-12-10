{
    'name': 'Microaccess Purchase',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified purchase',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','sale','repair', 'stock', 'purchase', 'product', 'web','Microaccess_Sales', 'account'],
    'data': [
        'security/security.xml',
        'views/purchase_template_views.xml',
       
        'report/purchase_order_report_inherit.xml',
        'report/quotation_report_inherit.xml',  
        'report/po_custom_report.xml',  
        'report/rfq_custom_report.xml',
        'data/terms_conditions.xml',    
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
}