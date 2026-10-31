{
    'name': 'AMR Sentry Reporting',
    'version': '13.0.1.0.0',
    'depends': ['amr_service_client'],
    'external_dependencies': {
        'python': ['sentry_sdk', 'yaml'],
    },
    'installable': True,
}
