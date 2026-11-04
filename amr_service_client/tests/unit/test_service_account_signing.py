"""Focused offline service-account assertion construction tests.

The signer is mocked: these tests do not verify cryptographic signatures.
They do not test client_server_kid_gap or unsigned decode behavior.
"""
import datetime
import unittest
from unittest import mock

import requests
from test_auth_providers import providers


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"access_token": "synthetic-access-token", "expires_in": 125}


class ServiceAccountSigningTests(unittest.TestCase):
    def test_grant_scope_claims_signing_and_token_request(self):
        private_key = "synthetic-private-key-not-real"
        credentials = {
            "client_id": "synthetic-client",
            "token_uri": "https://synthetic.invalid/token",
            "private_key": private_key,
            "private_key_id": "synthetic-kid",
            "scope": ["read:synthetic", "write:synthetic"],
            "connect_timeout": 3,
            "read_timeout": 8,
        }
        provider = providers.ServiceAccountProvider({}, credentials)
        fixed_now = 1_700_000_000
        fixed_jti = "synthetic-jti"
        response = FakeResponse()
        with mock.patch.object(providers.time, "time", return_value=fixed_now), \
                mock.patch.object(providers.uuid, "uuid4", return_value=fixed_jti), \
                mock.patch.object(providers.jwt, "encode", return_value="synthetic-assertion") as signer, \
                mock.patch.object(requests, "post", return_value=response) as post:
            result = provider._request_token(audience="synthetic-resource")

        self.assertEqual(signer.call_count, 1)
        args, kwargs = signer.call_args
        expected_claims = {
            "iss": "synthetic-client",
            "sub": "synthetic-client",
            "aud": "https://synthetic.invalid/token",
            "iat": fixed_now,
            "exp": fixed_now + 300,
            "jti": fixed_jti,
            "resource": "synthetic-resource",
            "scope": "read:synthetic write:synthetic",
        }
        self.assertTrue(args[0] == expected_claims)
        self.assertTrue(args[1] == private_key, "signing key mismatch")
        self.assertTrue(kwargs == {"algorithm": "RS256", "headers": {"kid": "synthetic-kid"}})

        self.assertEqual(post.call_count, 1)
        post_args, post_kwargs = post.call_args
        expected_form = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": "synthetic-assertion",
            "audience": "synthetic-resource",
            "scope": "read:synthetic write:synthetic",
        }
        self.assertTrue(post_args == ("https://synthetic.invalid/token",))
        self.assertTrue(post_kwargs == {
            "headers": {"Accept": "application/json"},
            "data": expected_form,
            "timeout": (3, 8),
        })
        self.assertEqual(result["access_token"], "synthetic-access-token")
        self.assertEqual(result["expires_in"], 125)
        self.assertEqual(result["cache_ttl"], 65)

    def test_es256_fallback_kid_and_unsupported_algorithm(self):
        credentials = {
            "client_id": "synthetic-client",
            "token_uri": "https://synthetic.invalid/token",
            "private_key": "synthetic-private-key-not-real",
            "kid": "synthetic-fallback-kid",
            "algorithm": "ES256",
        }
        provider = providers.ServiceAccountProvider({}, credentials)
        with mock.patch.object(providers.jwt, "encode", return_value="synthetic-es-assertion") as signer:
            assertion = provider._create_jwt_assertion(audience="synthetic-resource")
        self.assertEqual(assertion, "synthetic-es-assertion")
        self.assertEqual(signer.call_count, 1)
        args, kwargs = signer.call_args
        self.assertTrue(args[1] == credentials["private_key"], "signing key mismatch")
        self.assertEqual(kwargs.get("algorithm"), "ES256")
        self.assertEqual(kwargs.get("headers"), {"kid": "synthetic-fallback-kid"})

        unsupported = dict(credentials, algorithm="HS256")
        provider = providers.ServiceAccountProvider({}, unsupported)
        with mock.patch.object(providers.jwt, "encode") as signer:
            try:
                provider._create_jwt_assertion(audience="synthetic-resource")
            except ValueError as error:
                observed = (type(error) is ValueError and str(error) == "Unsupported algorithm")
            else:
                observed = False
        self.assertTrue(observed, "expected exact unsupported-algorithm ValueError")
        self.assertEqual(signer.call_count, 0)


if __name__ == "__main__":
    unittest.main()
