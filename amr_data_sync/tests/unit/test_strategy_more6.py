"""Focused mock tests for strategy lookup and cron synchronization paths."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import Mock


UNIT_DIR = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "strategy_more6_support", UNIT_DIR / "test_sync_strategy.py")
_support = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_support)


class StrategyMore6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.strategy_class, cls.UserError = _support.load_strategy_class()

    def strategy(self, **values):
        strategy = self.strategy_class()
        strategy.__dict__.update(values)
        strategy.ensure_one = lambda: strategy
        return strategy

    def test_internal_lookup_uses_explicit_lookup_method_before_field_fallback(self):
        model = types.SimpleNamespace()
        model.sudo = Mock(return_value=model)
        lookup = Mock(return_value="matched-by-method")
        model.find_remote = lookup
        strategy = self.strategy(
            env={"local.item": model}, internal_model="local.item",
            internal_lookup_method="find_remote", internal_lookup_fields="code")
        strategy.get_internal_id_from_external_id = Mock(return_value=None)
        item = {"id": 12, "code": "ABC"}

        self.assertEqual(strategy.internal_lookup(item), "matched-by-method")
        model.sudo.assert_called_once_with()
        lookup.assert_called_once_with(item, sync_strategy=strategy)

    def test_internal_lookup_filters_lookup_fields_to_model_fields(self):
        class Model(object):
            _fields = {"code": object()}

            def sudo(self):
                return self

            def search(self, domain, limit=None):
                self.request = (domain, limit)
                return "field-match"

        model = Model()
        strategy = self.strategy(
            env={"local.item": model}, internal_model="local.item",
            internal_lookup_method="missing_method", internal_lookup_fields="code, absent")
        strategy.get_internal_id_from_external_id = lambda external_id: None

        self.assertEqual(strategy.internal_lookup({"id": 7, "code": "X", "absent": "Y"}),
                         "field-match")
        self.assertEqual(model.request, ([("code", "=", "X")], 1))

    def test_create_sync_cron_adds_missing_cron_and_cron_context_skips_sync(self):
        created_strategy = types.SimpleNamespace(id=41, sync_cron=True)
        cron_model = Mock()
        cron_model.with_context.return_value = cron_model
        cron_model.search.return_value = False
        cron_model.create.return_value = "cron-created"
        parent = self.strategy_class()
        parent.env = {"external.data.sync.cron": cron_model}
        parent._context = {}
        original_create = getattr(_support.FakeModel, "create", None)
        _support.FakeModel.create = lambda recordset, vals_list: [created_strategy]
        try:
            result = self.strategy_class.create(parent, [{"name": "new"}])
        finally:
            if original_create is None:
                del _support.FakeModel.create
            else:
                _support.FakeModel.create = original_create

        self.assertEqual(result, [created_strategy])
        cron_model.with_context.assert_called_once_with(active_test=False)
        cron_model.search.assert_called_once_with([("sync_strategy_id", "=", 41)], limit=1)
        cron_model.create.assert_called_once_with({"sync_strategy_id": 41, "active": True})

        skipped_cron = Mock()
        skipped_cron.with_context.return_value = skipped_cron
        skipped_parent = self.strategy_class()
        skipped_parent.env = {"external.data.sync.cron": skipped_cron}
        skipped_parent._context = {"__from_sync_cron": True}
        original_create = getattr(_support.FakeModel, "create", None)
        _support.FakeModel.create = lambda recordset, vals_list: [created_strategy]
        try:
            self.assertEqual(self.strategy_class.create(skipped_parent, [{}]), [created_strategy])
        finally:
            if original_create is None:
                del _support.FakeModel.create
            else:
                _support.FakeModel.create = original_create
        skipped_cron.with_context.assert_not_called()

    def test_write_updates_existing_cron_active_state(self):
        cron = types.SimpleNamespace(active=False, write=Mock(return_value=True))
        cron_model = Mock()
        cron_model.with_context.return_value = cron_model
        cron_model.search.return_value = cron
        strategy = self.strategy(id=9, sync_cron=False, _context={}, env={
            "external.data.sync.cron": cron_model})
        original_write = getattr(_support.FakeModel, "write", None)
        original_iter = getattr(_support.FakeModel, "__iter__", None)
        _support.FakeModel.write = lambda recordset, vals: True
        _support.FakeModel.__iter__ = lambda recordset: iter([recordset])
        try:
            self.assertTrue(self.strategy_class.write(strategy, {"sync_cron": True}))
        finally:
            if original_write is None:
                del _support.FakeModel.write
            else:
                _support.FakeModel.write = original_write
            if original_iter is None:
                del _support.FakeModel.__iter__
            else:
                _support.FakeModel.__iter__ = original_iter
        cron_model.search.assert_called_once_with([("sync_strategy_id", "=", 9)], limit=1)
        cron.write.assert_called_once_with({"active": True})
        cron_model.create.assert_not_called()

    def test_write_creates_missing_cron_when_enabled_but_not_when_disabled(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                cron_model = Mock()
                cron_model.with_context.return_value = cron_model
                cron_model.search.return_value = False
                strategy = self.strategy(id=15, _context={}, env={
                    "external.data.sync.cron": cron_model})
                original_write = getattr(_support.FakeModel, "write", None)
                original_iter = getattr(_support.FakeModel, "__iter__", None)
                _support.FakeModel.write = lambda recordset, vals: True
                _support.FakeModel.__iter__ = lambda recordset: iter([recordset])
                try:
                    self.assertTrue(self.strategy_class.write(strategy, {"sync_cron": enabled}))
                finally:
                    if original_write is None:
                        del _support.FakeModel.write
                    else:
                        _support.FakeModel.write = original_write
                    if original_iter is None:
                        del _support.FakeModel.__iter__
                    else:
                        _support.FakeModel.__iter__ = original_iter
                if enabled:
                    cron_model.create.assert_called_once_with(
                        {"sync_strategy_id": 15, "active": True})
                else:
                    cron_model.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
