import json
import base64
from odoo import models, fields
from odoo.exceptions import ValidationError, AccessError


class ServiceCredentialWizard(models.TransientModel):
    _name = "service.credential.wizard"
    _description = "Service Credential Wizard"

    credential_type = fields.Selection(
        [
            ("service_account", "Service Account"),
            ("client_secret", "Client Secret"),
            ("api_key", "API Key"),
            ("bearer", "Bearer Token"),
            ("basic", "Basic Auth"),
        ],
        required=True,
        default="service_account",
    )
    version = fields.Char(default="1.0")

    json_content = fields.Text(readonly=True)
    generated_file = fields.Binary(readonly=True)
    generated_filename = fields.Char(readonly=True)

    # service account
    client_id = fields.Char()
    private_key_id = fields.Char()
    private_key = fields.Text()
    private_key_file = fields.Char()
    token_uri = fields.Char()
    issuer_profile_id = fields.Many2one("oidc.issuer.register", string="Issuer Profile", groups="amr_resource.group_oidc_trust_admin")
    client_secret = fields.Char()
    header = fields.Char(default="X-API-Key")
    value = fields.Char()

    # Bearer
    token = fields.Char()

    # Basic
    username = fields.Char()
    password = fields.Char()

    # def __init__(self, pool, cr):
    #     super().__init__(pool, cr)
    #     self.generated_file = None

    def _oauth_token_uri(self):
        self.ensure_one()
        if self.credential_type not in ("client_secret", "service_account"):
            return self.token_uri
        profile = self.issuer_profile_id
        if not profile:
            return self.token_uri
        if not self.env.user.has_group("amr_resource.group_oidc_trust_admin"):
            raise AccessError("You are not allowed to use issuer profiles.")
        if self.token_uri:
            raise ValidationError("Choose an issuer profile or enter a token URI, not both.")
        if not profile.active or not profile.token_endpoint or profile.client_id != self.client_id:
            raise ValidationError("The issuer profile is inactive or does not match this client.")
        return profile.token_endpoint

    def action_generate(self):
        self.ensure_one()

        data = {
            "version": self.version,
            "type": self.credential_type,
        }

        if self.credential_type == "service_account":
            data.update({
                "client_id": self.client_id,
                "private_key_id": self.private_key_id,
                "token_uri": self._oauth_token_uri(),
            })

            if self.private_key:
                data["private_key"] = self.private_key

            if self.private_key_file:
                data["private_key_file"] = self.private_key_file
        elif self.credential_type == "client_secret":
            data.update({
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "token_uri": self._oauth_token_uri(),
            })
        elif self.credential_type == "api_key":
            data.update({
                "header": self.header,
                "value": self.value,
            })
        elif self.credential_type == "bearer":
            data.update({
                "token": self.token,
            })
        elif self.credential_type == "basic":
            data.update({
                "username": self.username,
                "password": self.password,
            })

        self.json_content = json.dumps(data, indent=4)
        self.generated_file = base64.b64encode(self.json_content.encode("utf-8"))
        self.generated_filename = "%s.json" % self.credential_type

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
        credential = self.env["service.credential"].browse(self.env.context.get("active_id"))
        credential.write({"credential_json": self.json_content})
        return {
            "type": "ir.actions.act_window_close"
        }

    def action_save_to_credential(self):
        self.ensure_one()
        self.action_generate()
        credential = self.env["service.credential"].browse(self.env.context.get("active_id"))

        credential.write({
            "credential_json": self.json_content,
            "source": "database",
        })

        return {
            "type": "ir.actions.act_window_close"
        }
