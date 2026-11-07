import ast
from pathlib import Path


def _registered_provider_model_sources(addon):
    models = addon / "models"
    tree = ast.parse((models / "__init__.py").read_text())
    modules = [
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is None
        for alias in node.names
    ]
    return [models / (module + ".py") for module in modules]


def test_provider_manifest_has_only_core_addon_dependencies():
    manifest = Path(__file__).parents[2] / "__manifest__.py"
    text = manifest.read_text()
    assert "'depends': ['base', 'base_setup', 'web']" in text
    assert "amr_token" not in text
    assert "amr_resource" not in text


def test_provider_routes_do_not_inherit_legacy_controller():
    controller = Path(__file__).parents[2] / "controllers" / "main.py"
    text = controller.read_text()
    assert "amr_token" not in text
    assert "amr_resource" not in text
    assert "class ControllerOIDC(Controller):" in text


def test_provider_registered_sources_do_not_lookup_legacy_helper():
    addon = Path(__file__).parents[2]
    sources = _registered_provider_model_sources(addon)
    assert sources
    assert all(source.is_file() for source in sources)
    for source in sources:
        contents = source.read_text()
        assert "amr.token.helper" not in contents
        assert "amr.resource.helper" not in contents


def test_provider_validation_pins_algorithm_and_projects_only_contract_claims():
    addon = Path(__file__).parents[2]
    token_helper = (addon / "models" / "token_helper.py").read_text()
    controller = (addon / "controllers" / "main.py").read_text()

    assert "algorithm != self.get_signature_algorithm()" in token_helper
    assert "return self.make_response(active=False)" in controller
    assert "allowed = ('sub', 'aud', 'iss', 'exp', 'iat', 'scope', 'jti', 'token_type', 'client_id')" in controller
    assert "payload.update((key, claims[key]) for key in allowed if key in claims)" in controller
    assert "return self.make_response(sub=claims['sub'])" in controller
    assert all(claim not in controller for claim in ("'uid'", "'user_id'", "'name'", "'login'", "'db'"))


def test_legacy_addon_is_only_one_way_alias():
    addon = Path(__file__).parents[2].parent / "amr_token"
    manifest = (addon / "__manifest__.py").read_text()
    assert "'depends': ['amr_oidc']" in manifest
    assert not (addon / "models" / "res_users.py").exists()
    assert not (addon / "models" / "res_config_settings.py").exists()


def test_provider_logs_do_not_include_credentials_or_token_values():
    addon = Path(__file__).parents[2]
    sources = _registered_provider_model_sources(addon)
    contents = "\n".join(source.read_text() for source in sources)
    assert '"ExpiredSignatureError %s",assertion' not in contents
    assert '"Failed to validate token with public key: %s", e' not in contents
