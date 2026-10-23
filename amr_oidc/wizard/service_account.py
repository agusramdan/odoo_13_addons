# -*- coding: utf-8 -*-

import json
import base64
from odoo import models, fields


class OidcServiceAccountWizard(models.TransientModel):
    _name = 'oidc.service.account.wizard'
    _description = 'Export Service Account'

    client_id = fields.Many2one('oidc.client', required=True, readonly=True)
    algorithm = fields.Selection(
        [
            # https://pyjwt.readthedocs.io/en/stable/algorithms.html
            ("ES256", "ES256 - ECDSA using SHA-256"),
            ("ES256K", "ES256K - ECDSA with secp256k1 curve using SHA-256"),
            ("ES384", "ES384 - ECDSA using SHA-384"),
            ("ES512", "ES512 - ECDSA using SHA-512"),
            ("RS256", "RS256 - RSASSA-PKCS1-v1_5 using SHA-256"),
            ("RS384", "RS384 - RSASSA-PKCS1-v1_5 using SHA-384"),
            ("RS512", "RS512 - RSASSA-PKCS1-v1_5 using SHA-512"),
            ("PS256", "PS256 - RSASSA-PSS using SHA-256 and MGF1 padding with SHA-256"),
            ("PS384", "PS384 - RSASSA-PSS using SHA-384 and MGF1 padding with SHA-384"),
            ("PS512", "PS512 - RSASSA-PSS using SHA-512 and MGF1 padding with SHA-512"),
        ],
        default="RS256",
    )
    client_email = fields.Char(readonly=True,related='client_id.client_email')
    file_name = fields.Char(readonly=True)
    file_data = fields.Binary(readonly=True)
    json_content = fields.Text(readonly=True)

    # def export_service_account(self):
    #     self.ensure_one()
    #     key_pair = self.env['amr.token.helper'].generate_key(self.algorithm)
    #     result = self.env['amr.token.helper']._service_account_endpoint_defaults()
    #     # "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    #     # "token_uri": "https://oauth2.googleapis.com/token",
    #     # "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    #     # "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xxxx%40xxxx.iam.gserviceaccount.com",
    #     # "universe_domain": "googleapis.com"
    #
    #     return {
    #         "type": "service_account",
    #         "client_id": self.client_id,
    #         "client_email": self.client_id.client_email,
    #         "auth_uri": result['authorization_endpoint'],
    #         "token_uri": result['token_endpoint'],
    #         "issuer": result['issuer'],
    #         "private_key_id": key_pair['kid'],
    #         "private_key": key_pair['private_key'],
    #         "scope": "",
    #         "auth_method": "private_key_jwt",
    #         "algorithm": key_pair['algorithm'],
    #     }

    def action_generate(self):
        self.ensure_one()
        data = self.client_id.export_service_account(self.algorithm)
        json_text = json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        )

        filename = (
            f'service_account_{self.client_id.client_id}_{self.algorithm}.json'
        )

        self.write({
            'file_name': filename,
            'json_content': json_text,
            'file_data': base64.b64encode(
                json_text.encode()
            )
        })
        return {
            "type": "ir.actions.act_window",
            "name": self._description,
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context
        }

    def action_save(self):
        key_pair = json.loads(self.json_content)
        # sudo: preserve source duplicate lookup; key policy deferred.
        if self.env['oidc.client.key'].sudo().search(
                [('client_id', '=', self.client_id.id), ('kid', '=', key_pair['private_key_id'])]):
            raise UserWarning("Already save")

        # sudo: preserve source public-key persistence; key policy deferred.
        self.env['oidc.client.key'].sudo().create({
            'client_id': self.client_id.id,
            'kid': key_pair['private_key_id'],
            'algorithm': key_pair['algorithm'],
            'public_key': key_pair['public_key'],
            # 'private_key': key_pair['private_key'],
            'active': True,
        })
        return {
            "type": "ir.actions.act_window_close"
        }
