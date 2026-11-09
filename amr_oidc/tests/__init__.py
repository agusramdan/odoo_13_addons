# -*- coding: utf-8 -*-
# amr.resource-owned helper tests stay with that addon; package tests use tests/unit.
from .integration import test_access_token_audience_presence
from .integration import test_public_key_ownership
from .integration import test_public_key_orm
from .integration import test_jwks_route
from .integration import test_introspect_query_rejection
from .integration import test_replay_acl
from .integration import test_oidc_client_identity
from .integration import test_client_secret_verifier
from .integration import test_client_registration
from .integration import test_provider_selected_uat
