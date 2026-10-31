# -*- coding: utf-8 -*-

{
    'name': 'Resource Server',
    'category': 'Tools',
    'description': "Allow users to validate access token and protect resources.",
    'maintainer': 'Agus Muhammad Ramdan',
    'website': "https://www.agusramdan.web.id",
    'depends': ['base', 'web', 'base_setup', ],
    'version': '13.0.1.1.0',
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/registry_rules.xml',
        'data/oidc_algorithms.xml',
        'views/trust_registry_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/create_user_wizard.xml',
    ],
    'external_dependencies': {'python': ['jwt', 'cryptography']},
    'license': 'LGPL-3',
}
