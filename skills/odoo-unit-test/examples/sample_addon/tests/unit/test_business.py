from mock_odoo import MockFactory

def test_per_addon_unit_location():
    order = MockFactory.record(id=1, state='draft')
    order.write({'state': 'approved'})
    assert order.state == 'approved'
