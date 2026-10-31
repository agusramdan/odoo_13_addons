"""Private offline approval-binding tracer; not an integration contract."""

import hashlib
import hmac


_MAGIC = b'AMR-APPROVAL-TRACER\x00'
_MAX_FIELD = (1 << 32) - 1


def _approval_eligible(approval, plan, inventory, key, key_version, environment):
    """Verify opaque inputs against a key supplied by a trusted caller."""
    if (type(approval) is not dict or type(plan) is not bytes or
            type(inventory) is not bytes or type(key) is not bytes or not key or
            type(key_version) is not str or not key_version or
            type(environment) is not str or not environment):
        return False
    if (type(approval.get('key_version')) is not str or
            type(approval.get('environment')) is not str or
            approval.get('key_version') != key_version or
            approval.get('environment') != environment):
        return False
    plan_mac = approval.get('plan_mac')
    inventory_mac = approval.get('inventory_mac')
    if (type(plan_mac) is not bytes or len(plan_mac) != 32 or
            type(inventory_mac) is not bytes or len(inventory_mac) != 32):
        return False
    try:
        version_bytes = key_version.encode('utf-8')
        environment_bytes = environment.encode('utf-8')
        def mac(domain, payload):
            digest = hmac.new(key, _MAGIC, hashlib.sha256)
            for field in (domain, version_bytes, environment_bytes, payload):
                if len(field) > _MAX_FIELD:
                    raise ValueError
                digest.update(len(field).to_bytes(4, 'big'))
                digest.update(field)
            return digest.digest()
        expected_plan = mac(b'plan', plan)
        expected_inventory = mac(b'inventory', inventory)
    except (UnicodeError, OverflowError, ValueError):
        return False
    return (hmac.compare_digest(plan_mac, expected_plan) and
            hmac.compare_digest(inventory_mac, expected_inventory))
