# -*- coding: utf-8 -*-
import sys

from django.core.management.base import BaseCommand
from django.conf import settings

import environ

from yaget.models import LwaCredential

from sp_api.api import Sellers
from sp_api.base.marketplaces import Marketplaces
from sp_api.base import SellingApiException


class Command(BaseCommand):
    help = "SP-API ping using Sellers.get_marketplace_participations() with DB refresh_token"

    def handle(self, *args, **options):
        # Load .env (no environment-variable side effects; read values directly)
        env = environ.Env()
        try:
            env.read_env(str(getattr(settings, "BASE_DIR", ".")) + "/.env")
        except Exception:
            env.read_env(".env")

        # Refresh token: prefer DB, then fall back to .env
        refresh_token = (
            LwaCredential.objects.values_list("refresh_token", flat=True).first()
            or env("SP_API_REFRESH_TOKEN", default=None)
            or env("LWA_REFRESH_TOKEN", default=None)
        )
        if not refresh_token:
            self.stderr.write("No refresh_token found (DB or .env). Abort.")
            sys.exit(1)

        # LWA credentials from .env
        lwa_app_id = env("LWA_CLIENT_ID", default=None) or env("LWA_APP_ID", default=None)
        lwa_client_secret = env("LWA_CLIENT_SECRET", default=None)
        if not lwa_app_id or not lwa_client_secret:
            self.stderr.write("Missing LWA_CLIENT_ID/LWA_CLIENT_SECRET in .env. Abort.")
            sys.exit(1)

        # AWS signing keys (user or role)
        aws_access_key = (
            env("AWS_ACCESS_KEY_ID", default=None)
            or env("SP_API_ACCESS_KEY", default=None)
            or env("SP_API_ACCESS_KEY_ID", default=None)
        )
        aws_secret_key = env("AWS_SECRET_ACCESS_KEY", default=None) or env("SP_API_SECRET_KEY", default=None)
        role_arn = env("ROLE_ARN", default=None) or env("SP_API_ROLE_ARN", default=None)
        if not role_arn and (not aws_access_key or not aws_secret_key):
            self.stderr.write("Missing AWS keys (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY) or ROLE_ARN. Abort.")
            sys.exit(1)

        creds = {
            "refresh_token": refresh_token,
            "lwa_app_id": lwa_app_id,
            "lwa_client_secret": lwa_client_secret,
        }
        if role_arn:
            creds["role_arn"] = role_arn
        else:
            creds["aws_access_key"] = aws_access_key
            creds["aws_secret_key"] = aws_secret_key

        try:
            client = Sellers(credentials=creds, marketplace=Marketplaces.JP)

            # Compatibility across versions
            method = None
            for name in (
                "get_marketplace_participations",
                "getMarketplaceParticipations",
                "get_marketplace_participation",
                "getMarketplaceParticipation",
            ):
                cand = getattr(client, name, None)
                if callable(cand):
                    method = cand
                    break
            if method is None:
                attrs = ",".join([a for a in dir(client) if not a.startswith("_")])
                raise AttributeError(
                    "Sellers API method not found (get_marketplace_participations). Available: " + attrs
                )

            res = method()

            # Resolve HTTP status code
            status = None
            try:
                status = getattr(getattr(res, "raw", None), "status_code", None)
            except Exception:
                status = None
            if status is None:
                status = getattr(getattr(res, "_response", None), "status_code", None)

            payload = getattr(res, "payload", None) or {}
            marketplaces = []
            try:
                data = payload.get("payload") if isinstance(payload, dict) and "payload" in payload else payload
                if isinstance(data, list):
                    for p in data:
                        mk = (p or {}).get("marketplace", {})
                        name = mk.get("name") or mk.get("id") or mk.get("defaultCountryCode")
                        if name:
                            marketplaces.append(name)
                elif isinstance(data, dict):
                    if "marketplace" in data:
                        mk = data.get("marketplace", {})
                        name = mk.get("name") or mk.get("id") or mk.get("defaultCountryCode")
                        if name:
                            marketplaces.append(name)
                    elif "participations" in data and isinstance(data["participations"], list):
                        for p in data["participations"]:
                            mk = (p or {}).get("marketplace", {})
                            name = mk.get("name") or mk.get("id") or mk.get("defaultCountryCode")
                            if name:
                                marketplaces.append(name)
            except Exception:
                pass

            self.stdout.write(f"status={status or 'unknown'} marketplaces={marketplaces}")
        except SellingApiException as e:
            code = getattr(e, "code", None)
            status = getattr(e, "status_code", None)
            msg = str(e)
            self.stderr.write(f"SP-API Sellers ping failed: code={code} status={status} msg={msg}")
            sys.exit(1)