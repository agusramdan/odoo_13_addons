{
    'name': 'Cron Execution Audit',
    'version': '13.0.1.0.0',
    'category': 'Technical',
    'summary': 'Best-effort external-transaction audit for scheduled actions',
    'maintainer': 'Agus Muhammad Ramdan',
    'website': "https://www.agusramdan.web.id",
    'depends': ['base'],
    'data': ['security/ir.model.access.csv', 'views/cron_audit_views.xml'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
