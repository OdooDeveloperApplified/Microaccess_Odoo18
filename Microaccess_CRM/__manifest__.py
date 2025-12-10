{
    'name': 'Microaccess CRM',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified CRM',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail', 'sale', 'crm', 'sale_crm', 'sale_management'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        

        'views/crm_leads_views.xml',
        'views/crm_master_views.xml',
       
        
        'wizard/combined_weekly_report_wizard.xml',
        
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
}