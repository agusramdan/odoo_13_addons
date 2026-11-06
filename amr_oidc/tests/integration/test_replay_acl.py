"""Effective ORM access checks for JWT assertion replay records."""
import unittest

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("Odoo unavailable; native ORM tests NOT RUN")

from odoo.exceptions import AccessError
from odoo.tests.common import SavepointCase


class TestReplayAcl(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestReplayAcl, cls).setUpClass()
        cls.regular_user = cls.env["res.users"].create({
            "name": "Replay ACL ordinary user",
            "login": "replay-acl-ordinary",
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })
        cls.system_user = cls.env["res.users"].create({
            "name": "Replay ACL system user",
            "login": "replay-acl-system",
            "groups_id": [(6, 0, [cls.env.ref("base.group_system").id])],
        })
        cls.existing_record = cls.env["oidc.jwt.replay"].create({
            "jti": "replay-acl-existing", "iss": "issuer",
            "expired_at": "2099-01-01 00:00:00",
        })

    def _values(self, suffix):
        return {"jti": "replay-acl-" + suffix, "iss": "issuer",
                "expired_at": "2099-01-01 00:00:00"}

    def test_ordinary_user_cannot_create_or_read_replay_records(self):
        Replay = self.env["oidc.jwt.replay"].with_user(self.regular_user)
        with self.assertRaises(AccessError):
            Replay.create(self._values("ordinary"))
        with self.assertRaises(AccessError):
            Replay.search([])
        with self.assertRaises(AccessError):
            Replay.browse(self.existing_record.id).read(["jti"])

    def test_system_user_can_create_but_cannot_read_or_mutate_replay_records(self):
        Replay = self.env["oidc.jwt.replay"].with_user(self.system_user)
        record = Replay.create(self._values("system"))
        with self.assertRaises(AccessError):
            Replay.search([])
        with self.assertRaises(AccessError):
            record.read(["jti"])
        with self.assertRaises(AccessError):
            record.write({"jti": "changed"})
        with self.assertRaises(AccessError):
            record.unlink()
        self.assertNotEqual(self.system_user.id, self.env.ref("base.user_root").id)
        self.assertFalse(Replay.env.su)
