# -*- coding: utf-8 -*-
import os
import sys

from django.core.management.base import BaseCommand

from dotenv import load_dotenv

load_dotenv()

from sp_api.api import CatalogItems
from sp_api.base.marketplaces import Marketplaces
from sp_api.base import SellingApiException


class Command(BaseCommand):
    help = "Fetch a single ASIN via Catalog Items v2022-04-01"

    def add_arguments(self, parser):
        parser.add_argument("--asin", required=True, help="ASIN to fetch")
        parser.add_argument("--marketplace-id", dest="marketplace_id", required=False,
                            default=os.getenv("SPAPI_MARKETPLACE_ID", "A1VC38T7YXB528"))

    def handle(self, *args, **options):
        asin = options["asin"]
        marketplace_id = options["marketplace_id"]

        refresh_token = os.getenv("SP_API_REFRESH_TOKEN") or os.getenv("LWA_REFRESH_TOKEN")
        lwa_app_id = os.getenv("LWA_APP_ID") or os.getenv("LWA_CLIENT_ID")
        lwa_client_secret = os.getenv("LWA_CLIENT_SECRET")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        role_arn = os.getenv("ROLE_ARN")

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
            client = CatalogItems(credentials=creds, marketplace=Marketplaces.JP)
            # Try new get_catalog_item first
            try:
                res = client.get_catalog_item(
                    asin=asin,
                    marketplaceIds=[marketplace_id],
                    includedData=["summaries", "identifiers", "images"],
                )
            except TypeError:
                # Fallback for older client signatures
                res = client.get_catalog_item(asin, marketplaceIds=[marketplace_id])

            payload = getattr(res, "payload", {})
            data = None
            if isinstance(payload, dict) and payload.get("asin"):
                data = payload
            elif isinstance(payload, dict) and payload.get("payload"):
                data = payload["payload"]

            if not data:
                # Fallback: search by ASIN as keyword
                search = client.search_catalog_items(
                    keywords=[asin], marketplaceIds=[marketplace_id], includedData=["summaries", "identifiers"]
                )
                sp = getattr(search, "payload", {})
                if isinstance(sp, dict) and sp.get("numberOfResults", 0) > 0:
                    items = sp.get("items") or []
                    data = items[0] if items else None

            if not data:
                print(f"No data for ASIN={asin}")
                return

            item_asin = data.get("asin") or asin
            name = None
            summaries = data.get("summaries") or []
            if summaries and isinstance(summaries, list):
                name = summaries[0].get("itemName") or summaries[0].get("brand")

            print(f"asin={item_asin} name={name or ''}")
        except SellingApiException as e:
            code = getattr(e, "code", None)
            status = getattr(e, "status_code", None)
            msg = str(e)
            print(f"SP-API Catalog fetch failed: code={code} status={status} msg={msg}", file=sys.stderr)
            sys.exit(1)

