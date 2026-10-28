{
    'name': 'Service Client',
    'category': 'Tools',
    'author': 'Agus Muhammad Ramdan',
    'website': "https://www.agusramdan.web.id",
    'version': '13.0.0.1.0',
    'depends': ['base', 'web', 'base_setup', 'amr_resource'],
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['pyjwt'],
    },
    'data': [
        'security/ir.model.access.csv',

        'views/ir_actions_views.xml',
        'views/service_endpoint_views.xml',
        'views/service_credential_views.xml',
        'views/service_client_views.xml',
        'views/res_config_settings_views.xml',
        'views/service_client_log_views.xml',

        'views/menuitem.xml',

        'wizards/service_credential.xml',
        'wizards/service_endpoint_check.xml',
    ],
}
