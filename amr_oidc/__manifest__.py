# -*- coding: utf-8 -*-
# Port of addons_oidc @ 6725f802acde636be0b25e2c140d15dccd37b0db.
{
    'name': 'OIDC',
    'version': '13.0.1.0.0',
    'category': 'API',
    'summary': 'OIDC, JWT',
    'description': 'OIDC, JWT',
    'author': 'Agus Muhammad Ramdan',
    'website': 'https://www.agusramdan.web.id',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'amr_token'],
    'external_dependencies': {
        'python': ['pyjwt', 'cryptography'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/oidc_client_views.xml',
        'views/oidc_authorization_code_views.xml',
        'views/login_template.xml',
        'views/menuitem.xml',
        'wizard/service_account.xml',
    ],
}
