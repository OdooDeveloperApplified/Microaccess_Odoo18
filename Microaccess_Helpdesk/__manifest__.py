{
    'name': 'Microaccess Helpdesk',
    'version': '18.0.1.0',
    'category': 'HR',
    'author': 'Applified',
    'website': 'https://www.microaccess.com',
    'depends': ['base', 'mail','sale','repair','helpdesk_timesheet','helpdesk','stock','stock_account','Microaccess_Sales', 'rating','sale_project'],
    'data': [
        'security/ir.model.access.csv',
        'data/returnable_goods_sequence.xml',
        'data/custom_rating_email_template.xml',
        'wizard/change_stages_wizard.xml',
        'wizard/in_progress_report_wizard.xml',
      
        'views/helpdesk_template_views.xml',
        'views/service_product_views.xml',
        'views/helpdesk_master_remarks_views.xml',
        'views/returnable_goods_views.xml',
        'views/returnable_goods_lines_views.xml',
        'views/custom_rating_views.xml',
        'wizard/returnable_challan_close_wizard.xml',
        'wizard/return_received_wizard.xml',

        'reports/outward_challan_views.xml',
        'reports/inward_challan_views.xml',
        
    ],
    'assets': {
        "web.assets_frontend": [
            'Microaccess_Helpdesk/static/src/img/rating_5.png',
            'Microaccess_Helpdesk/static/src/img/rating_1.png',
            'Microaccess_Helpdesk/static/src/img/rating_3.png',
            'Microaccess_Helpdesk/static/src/img/rating_4.png',

        ],
    },
    'installable': True,
    'auto_install': False,
}