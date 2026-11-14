# -*- coding: utf-8 -*-
# amr.resource-owned helper tests stay with that addon; package tests use tests/unit.
from . import test_access_token_audience_presence
from . import test_public_key_ownership
from . import test_public_key_orm
from . import test_jwks_route
from . import test_introspect_query_rejection
from . import test_replay_acl
from . import test_oidc_client_identity
from . import test_client_secret_verifier
from . import test_client_registration
from . import test_fresh_issuer_subject
from . import test_provider_selected_uat
