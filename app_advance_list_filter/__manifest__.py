{
    'name': 'Advance List Filter/Search',
    'version': '18.0.0.1',
    'summary': 'Search directly inside List View columns',
    'depends': ['web'],
    'author': 'Applified',
    'assets': {
        'web.assets_backend': [
            ('after', 'web/static/src/views/list/list_renderer.xml', 'app_advance_list_filter/static/src/xml/list_renderer.xml'),
            'app_advance_list_filter/static/src/js/list_renderer.js',
            'app_advance_list_filter/static/src/style.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}