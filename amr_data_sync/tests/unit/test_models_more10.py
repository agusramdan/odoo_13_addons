"""Additional decision-path coverage for support models (offline doubles only)."""
import unittest

from test_models_support import (
    BaseModel, Record, Records, SearchModel, load_model,
)


class DataCompanyAdditionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_class = load_model(
            "data_company.py", "test_data_company_more10", include_utils=True
        ).ExternalDataLookup

    def test_lookup_company_rejects_missing_input_and_missing_external_id(self):
        model = self.model_class()
        searches = []
        model.search = lambda *args, **kwargs: searches.append((args, kwargs))

        self.assertIsNone(model.lookup_company(None, external_app_name="app"))
        self.assertIsNone(model.lookup_company({"name": "without id"}, external_app_name="app"))
        self.assertEqual(searches, [])

    def test_lookup_company_server_fallback_keeps_server_app_when_second_search_misses(self):
        search = SearchModel([Records(), Records([Record(company_id=False)])])
        model = self.model_class()
        model.search = search.search
        server = Record(get_application_name=lambda: "server-app")

        result = model.lookup_company({"id": 23}, server_sync=server,
                                      external_app_name="old-app")

        self.assertFalse(result)
        self.assertEqual([domain[1] for domain, _limit in search.domains], [
            ("external_app_name", "=", "old-app"),
            ("external_app_name", "=", "server-app"),
        ])

    def test_reverse_mapping_uses_server_scope_then_application_scope_for_remaining_ids(self):
        first = Records([Record(company_id=Record(id=2), external_id=20)])
        second = Records([Record(company_id=Record(id=1), external_id=10),
                          Record(company_id=Record(id=3), external_id=30)])
        search = SearchModel([first, second])
        model = self.model_class()
        model.search = search.search
        server = Record(id=9, get_application_name=lambda: "server-app")
        internal = BaseModel()
        internal.ids = [1, 2, 3]

        mapping, unmapped = model.reverse_mapping(internal, server_sync=server,
                                                  external_app_name="configured-app")

        self.assertEqual(mapping, {2: [20], 1: [10], 3: [30]})
        self.assertEqual(unmapped, set())
        self.assertEqual(search.domains, [
            ([ ("company_id", "in", [1, 2, 3]), ("server_sync_id", "=", 9) ], None),
            ([ ("company_id", "in", [1, 3]), ("external_app_name", "=", "server-app") ], None),
        ])

    def test_reverse_mapping_without_app_returns_partial_results_when_nonraising(self):
        row = Record(company_id=Record(id=4), external_id=40)
        model = self.model_class()
        model.search = lambda domain: Records([row])
        internal = BaseModel()
        internal.ids = [4, 5]

        mapping, unmapped = model.reverse_mapping(
            internal, server_sync=Record(id=3, get_application_name=lambda: "server-app"),
            raise_not_found_exception=False,
        )

        self.assertEqual(mapping, {4: [40]})
        self.assertEqual(unmapped, {5})

    def test_reverse_mapping_requires_application_name_by_default(self):
        model = self.model_class()
        model.search = lambda _domain: Records()
        internal = BaseModel()
        internal.ids = [1]

        with self.assertRaisesRegex(ValueError, "external_app_name not set"):
            model.reverse_mapping(internal)

    def test_reverse_mapping_empty_input_returns_sentinels_without_search(self):
        model = self.model_class()
        model.search = lambda *_args, **_kwargs: self.fail("unexpected search")

        self.assertEqual(model.reverse_mapping(Records(), external_app_name="app"), ([0], [0]))


if __name__ == "__main__":
    unittest.main()
