"""Offline regression for the UT-06 logging observer and its boundaries."""
import ast
import logging
from pathlib import Path
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'integration' / 'test_helper.py'


def method(name):
    tree = ast.parse(SOURCE.read_text())
    return next(node for cls in tree.body if isinstance(cls, ast.ClassDef)
                for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)


class HelperLoggerObserverTests(unittest.TestCase):
    def test_observer_keeps_audit_logging_and_catches_validation_logging(self):
        setup = method('setUp')
        assignment = next(node for node in setup.body if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'log_guard' for t in node.targets))
        guard = eval(compile(ast.Expression(assignment.value), str(SOURCE), 'eval'),
                     {'patch': patch, 'logging': logging})
        audit = logging.getLogger('synthetic.audit')
        validation = logging.getLogger('synthetic.validation')
        records = []

        class Sink(logging.Handler):
            def emit(self, record):
                records.append(record)

        sink = Sink()
        old_level, old_propagate = audit.level, audit.propagate
        audit.setLevel(logging.INFO)
        audit.propagate = False
        audit.addHandler(sink)
        try:
            with guard as spy:
                audit.info('synthetic audit')
                self.assertEqual(len(records), 1)
                self.assertTrue(spy.called)
                spy.reset_mock()
                self.assertFalse(spy.called)
                validation.warning('synthetic validation')
                self.assertTrue(spy.called)
        finally:
            audit.removeHandler(sink)
            audit.setLevel(old_level)
            audit.propagate = old_propagate

    def test_ut06_checks_both_validation_windows(self):
        body = method('test_ut06_verified_jwt_and_failures').body
        def logger_call(node, attr):
            return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == attr
                    and isinstance(node.value.func.value, ast.Attribute)
                    and node.value.func.value.attr == 'logger')
        resets = [i for i, node in enumerate(body) if logger_call(node, 'reset_mock')]
        checks = [i for i, node in enumerate(body) if isinstance(node, ast.Expr)
                  and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
                  and node.value.func.attr == 'assertFalse' and node.value.args
                  and isinstance(node.value.args[0], ast.Attribute)
                  and node.value.args[0].attr == 'called'
                  and isinstance(node.value.args[0].value, ast.Attribute)
                  and node.value.args[0].value.attr == 'logger']
        writes = [i for i, node in enumerate(body) if isinstance(node, ast.Expr)
                  and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
                  and node.value.func.attr == 'write']
        self.assertEqual(len(writes), 2)
        self.assertEqual(len(resets), 2)
        self.assertEqual(len(checks), 2)
        self.assertLess(writes[0], resets[0])
        self.assertLess(resets[0], checks[0])
        self.assertLess(checks[0], writes[1])
        self.assertLess(writes[1], resets[1])
        self.assertLess(resets[1], checks[1])
