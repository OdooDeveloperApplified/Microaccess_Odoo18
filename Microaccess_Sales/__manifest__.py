{
    'name': 'Microaccess Sales',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified Sales',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','sale', 'stock', 'product', 'web','repair'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_master_remarks_views.xml',
        'views/sales_template_views.xml',
        'views/revision_history_views.xml',
        'views/revision_history_line_views.xml',
        'views/sale_order_cancel_wizard.xml',
        'reports/company_footer_template.xml',
        'reports/footer_template.xml',
        'reports/custom_report.xml',  
    ],
    
    'assets': {},
    'installable': True,
    'auto_install': False,
}