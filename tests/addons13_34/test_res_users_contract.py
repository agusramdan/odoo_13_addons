"""P-05 res.users token lookup and URL helper source contract."""
import unittest
from types import SimpleNamespace
from unittest import mock

from support import ADDON, load_res_users_model


class TestResUsersTokenHelpers(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ADDON / "models" / "res_users.py").is_file(), "candidate res.users extension is missing")
        self.module = load_res_users_model()
        self.model = self.module.ResUsers

    def _record(self):
        return object.__new__(self.model)

    def _require(self, method):
        self.assertTrue(callable(self.model.__dict__.get(method)), f"candidate {method} method is missing")

    def test_username_lookup_prioritizes_login_then_email_then_domain(self):
        self._require("get_user_by_username")
        record = self._record()
        user = object()
        record.search = mock.Mock(side_effect=[False, user])
        record._get_login_order = mock.Mock(return_value="login_order")
        record._get_login_domain = mock.Mock(return_value=[("login", "ilike", "synthetic")])

        result = self.model.get_user_by_username(record, "synthetic")

        self.assertIs(result, user)
        self.assertEqual(record.search.call_args_list, [
            mock.call([("login", "=", "synthetic")], order="login_order", limit=1),
            mock.call([("email", "=", "synthetic")], order="login_order", limit=1),
        ])
        record._get_login_domain.assert_not_called()

    def test_username_lookup_falls_back_to_login_domain(self):
        self._require("get_user_by_username")
        record = self._record()
        user = object()
        record.search = mock.Mock(side_effect=[False, False, user])
        record._get_login_order = mock.Mock(return_value="order")
        record._get_login_domain = mock.Mock(return_value=[("login", "ilike", "synthetic")])

        self.assertIs(self.model.get_user_by_username(record, "synthetic"), user)
        record._get_login_domain.assert_called_once_with("synthetic")

    def test_access_token_generation_policy_and_mobile_alias(self):
        self._require("is_user_allow_create_token")
        self._require("get_mobile_access_token")
        record = self._record()
        self.assertTrue(self.model.is_user_allow_create_token(record))
        record.get_access_token = mock.Mock(return_value="synthetic-token")
        self.assertEqual(self.model.get_mobile_access_token(record, create=False), "synthetic-token")
        record.get_access_token.assert_called_once_with(create=False)

    def test_cached_token_uses_selected_user_and_audience(self):
        self._require("_get_access_token")
        record = self._record()
        record.id = 1
        selected_user = object()
        record.browse = mock.Mock(return_value=selected_user)
        token_helper = mock.Mock()
        token_helper.generate_user_token.return_value = ("synthetic-token", {}, 60)
        record.env = {"amr.token.helper": token_helper}

        result = self.model._get_access_token(record, 2, "synthetic-audience", 7)

        self.assertEqual(result, "synthetic-token")
        record.browse.assert_called_once_with(2)
        token_helper.generate_user_token.assert_called_once_with(selected_user, audience="synthetic-audience")

    def test_access_token_uses_five_minute_bucket_and_enforces_policy(self):
        self._require("get_access_token")
        record = self._record()
        record.id = 5
        record._get_access_token = mock.Mock(return_value="synthetic-token")
        with mock.patch.object(self.module.time, "time", return_value=900):
            self.assertEqual(self.model.get_access_token(record, audience="service-a"), "synthetic-token")
        record._get_access_token.assert_called_once_with(5, "service-a", 3)

        record.is_user_allow_create_token = mock.Mock(return_value=False)
        with self.assertRaisesRegex(self.module.UserError, "not allowed"):
            self.model.get_access_token(record)

    def test_create_access_token_delegates_helper_and_model(self):
        self._require("create_access_token")
        record = self._record()
        token_helper = mock.Mock()
        token_model = mock.Mock()
        record.env = {"amr.token.helper": token_helper, "amr.token": token_model}
        token_helper.generate_user_token.return_value = ("synthetic-token", {}, 60)
        token_model.create_access_token.return_value = "synthetic-record"

        result = self.model.create_access_token(record, audience="service-a", label="mobile")

        token_helper.generate_user_token.assert_called_once_with(record, audience="service-a")
        token_model.create_access_token.assert_called_once_with(user=record, label="mobile")
        self.assertEqual(result, "synthetic-record")

    def test_access_token_url_preserves_existing_query_fragment_and_audience(self):
        self._require("add_url_access_token")
        record = self._record()
        record.get_access_token = mock.Mock(return_value="synthetic-token")

        result = self.model.add_url_access_token(
            record, url="https://app.example.invalid/path?x=1#section",
            param_name="access_token", create=False,
        )

        record.get_access_token.assert_called_once_with(
            create=False, audience="https://app.example.invalid",
        )
        self.assertEqual(result, "https://app.example.invalid/path?x=1&access_token=synthetic-token#section")

    def test_non_access_token_url_type_delegates_to_auto_login(self):
        self._require("add_url_access_token")
        record = self._record()
        record.get_auto_login_url = mock.Mock(return_value="https://app.example.invalid/web_token_access")

        result = self.model.add_url_access_token(record, url="https://app.example.invalid", url_type="auto_login")

        self.assertEqual(result, "https://app.example.invalid/web_token_access")
        record.get_auto_login_url.assert_called_once_with(url="https://app.example.invalid")

    def test_auto_login_url_includes_token_and_path_fragment_redirect(self):
        self._require("get_auto_login_url")
        record = self._record()
        record.get_access_token = mock.Mock(return_value="synthetic-token")

        result = self.model.get_auto_login_url(
            record, url="https://app.example.invalid/app#home",
            web_token_access_path="/web_token_access",
        )

        record.get_access_token.assert_called_once_with(create=True, audience="https://app.example.invalid")
        self.assertTrue(result.startswith("https://app.example.invalid/web_token_access?"))
        self.assertIn("token_access=synthetic-token", result)
        self.assertIn("redirect=%2Fapp%23home", result)


if __name__ == "__main__":
    unittest.main()
