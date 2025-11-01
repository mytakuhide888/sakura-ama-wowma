# -*- coding: utf-8 -*-
import os
import sys

from django.core.management.base import BaseCommand

from dotenv import load_dotenv

load_dotenv()

from sp_api.api import Sellers
from sp_api.base.marketplaces import Marketplaces
from sp_api.base import SellingApiException


class Command(BaseCommand):
    help = "SP-API ping using Sellers.get_marketplace_participations()"

    def handle(self, *args, **options):
        refresh_token = os.getenv("SP_API_REFRESH_TOKEN") or os.getenv("LWA_REFRESH_TOKEN")
        lwa_app_id = os.getenv("LWA_APP_ID") or os.getenv("LWA_CLIENT_ID")
        lwa_client_secret = os.getenv("LWA_CLIENT_SECRET")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        role_arn = os.getenv("ROLE_ARN")

        marketplace_id = os.getenv("SPAPI_MARKETPLACE_ID", "A1VC38T7YXB528")

        creds = {
            "refresh_token": refresh_token or "",
            "lwa_app_id": lwa_app_id or "",
            "lwa_client_secret": lwa_client_secret or "",
            "aws_access_key": aws_access_key or "",
            "aws_secret_key": aws_secret_key or "",
        }
        if role_arn:
            creds["role_arn"] = role_arn

        try:
            client = Sellers(credentials=creds, marketplace=Marketplaces.JP)

            # library version compatibility: try several method names
            method = None
            for name in (
                "get_marketplace_participations",
                "getMarketplaceParticipations",
            ):
                cand = getattr(client, name, None)
                if callable(cand):
                    method = cand
                    break
            if method is None:
                # No known method found; surface available attributes to help troubleshooting
                attrs = ",".join([a for a in dir(client) if not a.startswith("_")])
                raise AttributeError(
                    f"Sellers API method not found on client (looked for get_marketplace_participations). "
                    f"Available: {attrs}"
                )

            res = method()

            # Resolve HTTP status code across library versions
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
                for p in payload.get("payload", payload) if isinstance(payload, dict) else payload:
                    mk = p.get("marketplace", {})
                    name = mk.get("name") or mk.get("defaultCountryCode") or mk.get("id")
                    if name:
                        marketplaces.append(name)
            except Exception:
                pass

            print(f"status={status or 'unknown'} marketplace_id={marketplace_id} marketplaces={marketplaces}")
        except SellingApiException as e:
            code = getattr(e, "code", None)
            status = getattr(e, "status_code", None)
            msg = str(e)
            print(f"SP-API Sellers ping failed: code={code} status={status} msg={msg}", file=sys.stderr)
            sys.exit(1)
