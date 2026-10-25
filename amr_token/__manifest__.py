# -*- coding: utf-8 -*-

{
    'name': "Token Provider",
    'summary': "Token Provider",
    'description': "Token Provider",
    'author': "Agus Muhammad Ramdan",
    'website': "https://www.agusramdan.web.id",
    'category': 'API',
    'version': '13.0.0.0.8',
    'depends': ['base', 'base_setup', 'web', 'amr_resource'],
    'external_dependencies': {
        'python': ['pyjwt'],
    },
    'data': [
        'security/ir.model.access.csv',

        'views/res_config_settings_views.xml',
    ],
}
