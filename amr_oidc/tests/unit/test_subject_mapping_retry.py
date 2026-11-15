"""Offline component tests for issuer subject collision retry control flow.

The fake store models exact-search and synthetic uniqueness outcomes; it does
not establish native ORM, PostgreSQL, or database transaction behavior.
"""
import contextlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

ADDON = Path(__file__).resolve().parents[2]


def load_support():
    path = ADDON / "tests" / "support.py"
    spec = importlib.util.spec_from_file_location("subject_retry_test_support", str(path))
    if spec is None or spec.loader is None:
        raise ImportError("cannot create isolated support module spec")
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    return support


class SavepointCursor(object):
    @contextlib.contextmanager
    def savepoint(self):
        yield


class RecordSet(list):
    def __getattr__(self, name):
        if not self:
            raise AttributeError(name)
        return getattr(self[0], name)


class SubjectStore(object):
    """Narrow fake honoring equality domains and inactive-row uniqueness."""

    def __init__(self, module, records, context=None, hooks=None):
        self.module = module
        self.records = records
        self.context = dict(context or {})
        self.hooks = hooks if hooks is not None else {}

    def sudo(self):
        return self

    def with_context(self, **values):
        context = dict(self.context)
        context.update(values)
        return SubjectStore(self.module, self.records, context, self.hooks)

    def search(self, domain):
        matches = []
        for record in self.records:
            if self.context.get("active_test", True) and not record.active:
                continue
            if all(operator == "=" and getattr(record, field) == value
                   for field, operator, value in domain):
                matches.append(record)
        return RecordSet(matches)

    def create(self, values):
        if self.context.get("_oidc_subject_capability") is not self.module._CREATE_CAPABILITY:
            raise self.module.AccessError("issuer capability missing")
        before_create = self.hooks.pop("before_create", None)
        if before_create:
            before_create(values, self.records)
        for record in self.records:
            if (record.namespace == values["namespace"]
                    and (record.user_id == values["user_id"]
                         or record.subject == values["subject"])):
                raise self.module.psycopg2.IntegrityError("synthetic unique collision")
        record = SimpleNamespace(**values)
        self.records.append(record)
        return RecordSet([record])


class SubjectMapperRetryTests(unittest.TestCase):
    def setUp(self):
        support = load_support()
        self.module = support.load("models/oidc_issuer_principal_subject.py")
        self.records = []
        self.store = SubjectStore(self.module, self.records)
        self.model = self.module.OidcIssuerPrincipalSubject()
        self.model.env = SimpleNamespace(cr=SavepointCursor())
        self.model.sudo = lambda: self.store

    def test_unique_collision_with_archived_subject_retries_new_random_value(self):
        issuer = "https://issuer.example.invalid"
        collision_bytes = b"a" * 32
        replacement_bytes = b"b" * 32
        archived = SimpleNamespace(
            namespace=issuer, user_id=1, subject=collision_bytes.hex(), active=False)
        self.records.append(archived)

        with mock.patch.object(
                self.module.secrets, "token_bytes",
                side_effect=(collision_bytes, replacement_bytes)) as token_bytes:
            result = self.model._get_or_create_subject(issuer, 2)

        self.assertEqual(result, replacement_bytes.hex())
        self.assertEqual(token_bytes.call_count, 2)
        self.assertFalse(archived.active)
        self.assertEqual(
            [(record.user_id, record.subject) for record in self.records],
            [(1, collision_bytes.hex()), (2, replacement_bytes.hex())])

    def test_unique_error_after_same_principal_winner_returns_existing_subject(self):
        issuer = "https://issuer.example.invalid"
        winner_subject = "d" * 64

        def insert_concurrent_winner(values, records):
            records.append(SimpleNamespace(
                namespace=values["namespace"], user_id=values["user_id"],
                subject=winner_subject, active=True))

        self.store.hooks["before_create"] = insert_concurrent_winner
        with mock.patch.object(
                self.module.secrets, "token_bytes", return_value=b"x" * 32) as token_bytes:
            result = self.model._get_or_create_subject(issuer, 42)

        self.assertEqual(result, winner_subject)
        self.assertEqual(token_bytes.call_count, 1)
        self.assertEqual(len(self.records), 1)
        self.assertEqual(self.records[0].namespace, issuer)
        self.assertEqual(self.records[0].user_id, 42)
        self.assertEqual(self.records[0].subject, winner_subject)

    def test_repeated_unique_collisions_exhaust_three_attempts_without_reserving(self):
        issuer = "https://issuer.example.invalid"
        collision_bytes = b"c" * 32
        archived = SimpleNamespace(
            namespace=issuer, user_id=1, subject=collision_bytes.hex(), active=False)
        self.records.append(archived)

        with mock.patch.object(
                self.module.secrets, "token_bytes",
                side_effect=(collision_bytes, collision_bytes, collision_bytes)) as token_bytes:
            with self.assertRaisesRegex(
                    self.module.UserError, "Unable to reserve a unique issuer subject"):
                self.model._get_or_create_subject(issuer, 2)

        self.assertEqual(token_bytes.call_count, 3)
        self.assertEqual(len(self.records), 1)
        self.assertEqual(self.records[0].user_id, 1)
        self.assertEqual(self.records[0].subject, collision_bytes.hex())


if __name__ == "__main__":
    unittest.main()
