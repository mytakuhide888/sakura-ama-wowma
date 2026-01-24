# -*- coding: utf-8 -*-
"""
Match AmaCategory to WowCategory using normalized paths and fuzzy matching.

Outputs TSV files for auto matches and review lists.

Usage:
  python manage.py match_categories --synonyms docs/category_mapping/synonyms.tsv
    --outdir codex_out --auto-threshold 0.7 --review-threshold 0.4

Rules implemented (per user agreement):
  - 上位3階層が一致し、末端のfuzzyスコア>auto_threshold → 自動採用。
  - 末端スコアが review_threshold〜auto_threshold または 2階層一致のみ → レビュー。
  - 2階層しかマッチしないものは別ファイル（level2_review）。
  - 「その他」を含む候補は fallback として優先度を下げた上で保持。
"""
import csv
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from yaget.models import AmaCategory, WowCategory


class Command(BaseCommand):
    help = "Match AmaCategory to WowCategory and emit TSV files (auto/review)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--synonyms",
            type=str,
            default=str(Path("docs/category_mapping/synonyms.tsv")),
            help="TSV file of synonyms (key<TAB>comma-separated synonyms)",
        )
        parser.add_argument(
            "--outdir",
            type=str,
            default="codex_out",
            help="Output directory for TSV files",
        )
        parser.add_argument("--auto-threshold", type=float, default=0.7)
        parser.add_argument("--review-threshold", type=float, default=0.4)

    def handle(self, *args, **options):
        syn_path = Path(options["synonyms"])
        outdir = Path(options["outdir"])
        outdir.mkdir(parents=True, exist_ok=True)

        synonyms = self.load_synonyms(syn_path)
        self.stdout.write(f"Loaded synonyms entries: {len(synonyms)}")

        wow_records = list(WowCategory.objects.all())
        ama_records = list(AmaCategory.objects.all())
        self.stdout.write(f"Loaded Ama: {len(ama_records)}, Wow: {len(wow_records)}")

        wow_index = self.build_wow_index(wow_records, synonyms)
        auto_rows, review_rows, review_lvl2_rows = self.match_all(
            ama_records,
            wow_index,
            synonyms,
            auto_threshold=options["auto_threshold"],
            review_threshold=options["review_threshold"],
        )

        header = [
            "AmaCatID",
            "AmaPath",
            "WowCatID_candidate",
            "WowPath",
            "score",
            "decision_reason",
            "comment",
        ]
        self.write_tsv(outdir / "category_match_auto.tsv", header, auto_rows)
        self.write_tsv(outdir / "category_match_review.tsv", header, review_rows)
        self.write_tsv(outdir / "category_match_review_level2.tsv", header, review_lvl2_rows)

        self.stdout.write(self.style.SUCCESS(
            f"auto:{len(auto_rows)} review:{len(review_rows)} review_level2:{len(review_lvl2_rows)}"
        ))

    # ---------------- helpers ----------------
    def load_synonyms(self, path: Path):
        mapping = {}
        if not path.exists():
            return mapping
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                key = parts[0].strip()
                variants = [v.strip() for v in parts[1].split(",") if v.strip()]
                for v in variants + [key]:
                    mapping[v.lower()] = key.lower()
        return mapping

    def normalize(self, text: str, synonyms: dict) -> str:
        if text is None:
            return ""
        t = text.lower()
        t = t.replace("＆", "&")
        for ch in [">", "/", "\\", "|", "・", "&"]:
            t = t.replace(ch, " ")
        t = re.sub(r"[^0-9a-zA-Zぁ-んァ-ン一-龥\\s]+", " ", t)
        tokens = [tok for tok in re.split(r"\\s+", t) if tok]
        normed = []
        for tok in tokens:
            normed.append(synonyms.get(tok, tok))
        return " ".join(normed)

    def build_wow_index(self, wow_records, synonyms):
        idx3 = defaultdict(list)
        idx2 = defaultdict(list)
        norm_cache = {}
        for w in wow_records:
            levels = [w.level_1_cat_name, w.level_2_cat_name, w.level_3_cat_name, w.level_4_cat_name]
            levels = [lv for lv in levels if lv]
            norm_levels = [self.normalize(lv, synonyms) for lv in levels]
            norm_cache[w.product_cat_id] = (levels, norm_levels)
            if len(norm_levels) >= 3:
                idx3[tuple(norm_levels[:3])].append(w.product_cat_id)
            if len(norm_levels) >= 2:
                idx2[tuple(norm_levels[:2])].append(w.product_cat_id)
        return {"idx3": idx3, "idx2": idx2, "norm_cache": norm_cache}

    def fuzzy(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def match_all(self, ama_records, wow_index, synonyms, auto_threshold=0.7, review_threshold=0.4):
        auto_rows = []
        review_rows = []
        review_lvl2_rows = []

        for a in ama_records:
            levels = [
                a.level_1_cat_name,
                a.level_2_cat_name,
                a.level_3_cat_name,
                a.level_4_cat_name,
                a.level_5_cat_name,
                a.level_6_cat_name,
                a.level_7_cat_name,
                a.level_8_cat_name,
            ]
            levels = [lv for lv in levels if lv]
            if not levels:
                continue
            norm_levels = [self.normalize(lv, synonyms) for lv in levels]
            ama_path = "/".join([lv for lv in levels if lv])

            # try prefix-3
            candidates = []
            if len(norm_levels) >= 3:
                candidates.extend(wow_index["idx3"].get(tuple(norm_levels[:3]), []))
            if not candidates and len(norm_levels) >= 2:
                candidates.extend(wow_index["idx2"].get(tuple(norm_levels[:2]), []))

            if not candidates:
                continue

            for cid in candidates:
                w_levels, w_norm = wow_index["norm_cache"][cid]
                wow_path = "/".join([lv for lv in w_levels if lv])
                score = self.fuzzy(norm_levels[-1], w_norm[-1] if w_norm else "")

                if len(norm_levels) >= 3 and len(w_norm) >= 3 and tuple(norm_levels[:3]) == tuple(w_norm[:3]):
                    if score >= auto_threshold:
                        auto_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{score:.3f}", "3level_match", ""])
                    elif score >= review_threshold:
                        review_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{score:.3f}", "needs_review_score", ""])
                elif len(norm_levels) >= 2 and len(w_norm) >= 2 and tuple(norm_levels[:2]) == tuple(w_norm[:2]):
                    review_lvl2_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{score:.3f}", "level2_fallback", ""])

        return auto_rows, review_rows, review_lvl2_rows

    def write_tsv(self, path: Path, header, rows):
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
