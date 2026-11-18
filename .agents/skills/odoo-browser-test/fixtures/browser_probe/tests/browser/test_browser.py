from odoo.tests import HttpCase, tagged

@tagged('-at_install', 'post_install')
class BrowserProbe(HttpCase):
    def test_positive(self):
        self.browser_js('/web/login', "console.log('test successful')", timeout=30)

    def test_negative(self):
        self.browser_js('/web/login', "console.error('intentional negative control')", timeout=10)
