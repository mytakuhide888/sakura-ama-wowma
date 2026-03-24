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
            "--level1-map",
            type=str,
            default=str(Path("docs/category_mapping/level_1_cat.txt")),
            help="TSV mapping of Ama level1 to allowed Wow level1 (columns: AmaPath第一階層\tWowPath第一階層)",
        )
        parser.add_argument(
            "--level2-map",
            type=str,
            default=str(Path("docs/category_mapping/level_2_cat.txt")),
            help="TSV mapping of Ama level1+level2 to Wow level1+level2",
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

        level1_map = self.load_level1_map(Path(options["level1_map"]))
        level2_map = self.load_level2_map(Path(options["level2_map"]))
        self.stdout.write(f"Loaded level2_map entries: {len(level2_map)}")
        wow_records = self.filter_wow_by_level1(level1_map)
        ama_records = list(AmaCategory.objects.all())
        self.stdout.write(f"Loaded Ama: {len(ama_records)}, Wow (filtered): {len(wow_records)}")

        wow_index = self.build_wow_index(wow_records, synonyms)
        auto_rows, review_rows, review_lvl2_rows = self.match_all(
            ama_records,
            wow_index,
            synonyms,
            level1_map,
            level2_map,
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
        # Allow alnum + Japanese + whitespace, collapse everything else to space
        # カタカナ長音「ー」(U+30FC)、ヴ等の拡張カタカナも許可
        t = re.sub(r"[^0-9a-zA-Zぁ-んァ-ヶー一-龥\s]+", " ", t)
        tokens = [tok for tok in re.split(r"\s+", t) if tok]
        normed = []
        for tok in tokens:
            normed.append(synonyms.get(tok, tok))
        return " ".join(normed)

    def load_level1_map(self, path: Path):
        mapping = set()
        if not path.exists():
            return mapping
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines[1:]:  # skip header
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            ama = parts[0].strip().strip('"')
            wow = parts[1].strip().strip('"')
            if ama and wow:
                mapping.add((ama, wow))
        return mapping

    def load_level2_map(self, path: Path):
        """Load level2 mapping: (AmaL1, AmaL2) -> (WowL1, WowL2)"""
        mapping = {}
        if not path.exists():
            return mapping
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in lines[1:]:  # skip header
            if not line.strip() or line.strip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            ama_l1 = parts[0].strip().strip('"')
            ama_l2 = parts[1].strip().strip('"')
            wow_l1 = parts[2].strip().strip('"')
            wow_l2 = parts[3].strip().strip('"')
            if ama_l1 and ama_l2 and wow_l1 and wow_l2:
                key = (ama_l1, ama_l2)
                if key not in mapping:
                    mapping[key] = []
                mapping[key].append((wow_l1, wow_l2))
        return mapping

    def filter_wow_by_level1(self, level1_map):
        wow = list(WowCategory.objects.all())
        if not level1_map:
            return wow
        allowed = set([wow1 for ama1, wow1 in level1_map])
        return [w for w in wow if w.level_1_cat_name in allowed]

    def build_wow_index(self, wow_records, synonyms):
        idx1 = defaultdict(list)
        idx2 = defaultdict(list)
        idx_by_wow_l1 = defaultdict(list)  # Wowma第1階層（原文）でインデックス
        idx_by_wow_l1l2 = defaultdict(list)  # Wowma第1+第2階層（原文）でインデックス
        sonota_by_l1 = {}  # 「その他」カテゴリ（第1階層→カテゴリID）
        sonota_by_l1l2 = {}  # 「その他」カテゴリ（第1+第2階層→カテゴリID）
        norm_cache = {}
        first_tokens = set()
        for w in wow_records:
            levels = [w.level_1_cat_name, w.level_2_cat_name, w.level_3_cat_name, w.level_4_cat_name]
            levels = [lv for lv in levels if lv]
            norm_levels = [self.normalize(lv, synonyms) for lv in levels]
            norm_path = " / ".join(norm_levels)
            norm_cache[w.product_cat_id] = (levels, norm_levels, norm_path)
            # Wowma第1階層（原文）でインデックス作成
            if levels:
                idx_by_wow_l1[levels[0]].append(w.product_cat_id)
            # Wowma第1+第2階層（原文）でインデックス作成
            if len(levels) >= 2:
                idx_by_wow_l1l2[(levels[0], levels[1])].append(w.product_cat_id)
                # 「その他」カテゴリをL1+L2レベルで記録
                if levels[1].startswith("その他"):
                    if levels[0] not in sonota_by_l1:
                        sonota_by_l1[levels[0]] = (w.product_cat_id, levels)
            # 「その他」カテゴリをL2+L3レベルで記録
            if len(levels) >= 3 and levels[2].startswith("その他"):
                key = (levels[0], levels[1])
                if key not in sonota_by_l1l2:
                    sonota_by_l1l2[key] = (w.product_cat_id, levels)
            if norm_levels:
                idx1[norm_levels[0]].append(w.product_cat_id)
                first_tokens.add(norm_levels[0])
            if len(norm_levels) >= 2:
                idx2[" ".join(norm_levels[:2])].append(w.product_cat_id)
        return {
            "idx1": idx1, "idx2": idx2,
            "idx_by_wow_l1": idx_by_wow_l1, "idx_by_wow_l1l2": idx_by_wow_l1l2,
            "sonota_by_l1": sonota_by_l1, "sonota_by_l1l2": sonota_by_l1l2,
            "norm_cache": norm_cache, "first_tokens": list(first_tokens)
        }

    def fuzzy(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def match_all(self, ama_records, wow_index, synonyms, level1_map, level2_map, auto_threshold=0.7, review_threshold=0.4):
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
            ama_norm_path = " / ".join(norm_levels)

            candidates = []
            used_level2 = False

            # level2_mapを使ってAmazon第1+第2階層から対応するWowma第1+第2階層を取得
            if len(levels) >= 2:
                ama_key = (levels[0], levels[1])
                if ama_key in level2_map:
                    used_level2 = True
                    for wow_l1, wow_l2 in level2_map[ama_key]:
                        cands = wow_index["idx_by_wow_l1l2"].get((wow_l1, wow_l2), [])
                        candidates.extend(cands)

            # level2_mapにマッチがない場合はlevel1_mapにフォールバック
            if not candidates:
                # level1_mapを使ってAmazon第1階層から対応するWowma第1階層を取得
                allowed_wow_levels = [wow for ama, wow in level1_map if ama == levels[0]]
                allowed_wow_levels = set(allowed_wow_levels)

                # Wowma第1階層（原文）でインデックスを引く（level1_mapに基づく）
                for wow_l1 in allowed_wow_levels:
                    cands = wow_index["idx_by_wow_l1"].get(wow_l1, [])
                    candidates.extend(cands)

            # 重複を除去
            candidates = list(set(candidates))

            best = None
            best_level2 = None
            best_prefix = None

            for cid in candidates:
                w_levels, w_norm, w_norm_path = wow_index["norm_cache"][cid]
                wow_path = "/".join([lv for lv in w_levels if lv])
                score = self.fuzzy(ama_norm_path, w_norm_path)

                # prefix-based hierarchical match (prefer long shared prefix)
                common_prefix = 0
                for ama_tok, wow_tok in zip(norm_levels, w_norm):
                    if ama_tok == wow_tok:
                        common_prefix += 1
                    else:
                        break
                if common_prefix >= 2:
                    prefix_score = common_prefix / max(len(norm_levels), len(w_norm))
                    if best_prefix is None or common_prefix > best_prefix[0] or (
                        common_prefix == best_prefix[0] and prefix_score > best_prefix[1]
                    ):
                        best_prefix = (common_prefix, prefix_score, cid, wow_path)

                if len(norm_levels) >= 3 and len(w_norm) >= 3:
                    if best is None or score > best[0]:
                        best = (score, cid, wow_path)
                elif len(norm_levels) >= 2 and len(w_norm) >= 2:
                    if best_level2 is None or score > best_level2[0]:
                        best_level2 = (score, cid, wow_path)

            # level2マップを使った場合はスコアにボーナスを付与
            score_bonus = 0.15 if used_level2 else 0.0
            reason_suffix = "_l2map" if used_level2 else ""

            chosen_reason = None
            if best_prefix and (best is None or best_prefix[1] >= best[0] + 0.05):
                # prefer strong prefix match unless fuzzy is clearly better
                _, pscore, cid, wow_path = best_prefix
                effective_score = min(1.0, pscore + score_bonus)
                if effective_score >= auto_threshold:
                    auto_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{effective_score:.3f}", f"prefix_match{reason_suffix}", ""])
                    continue
                elif effective_score >= review_threshold:
                    review_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{effective_score:.3f}", f"prefix_match{reason_suffix}", ""])
                    continue

            if best:
                score, cid, wow_path = best
                effective_score = min(1.0, score + score_bonus)
                if effective_score >= auto_threshold:
                    auto_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{effective_score:.3f}", f"auto_fuzzy{reason_suffix}", ""])
                elif effective_score >= review_threshold:
                    review_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{effective_score:.3f}", f"needs_review{reason_suffix}", ""])
                else:
                    # スコアが低い場合は「その他」カテゴリにフォールバック
                    sonota = self._find_sonota_fallback(levels, level1_map, level2_map, wow_index)
                    if sonota:
                        sonota_cid, sonota_levels = sonota
                        sonota_path = "/".join(sonota_levels)
                        auto_rows.append([a.product_cat_id, ama_path, sonota_cid, sonota_path, "0.600", "sonota_fallback", ""])
            elif best_level2:
                score, cid, wow_path = best_level2
                effective_score = min(1.0, score + score_bonus)
                if effective_score >= 0.75:
                    auto_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{effective_score:.3f}", f"auto_level2{reason_suffix}", ""])
                elif effective_score >= review_threshold:
                    review_lvl2_rows.append([a.product_cat_id, ama_path, cid, wow_path, f"{effective_score:.3f}", f"level2_fallback{reason_suffix}", ""])
                else:
                    # スコアが低い場合は「その他」カテゴリにフォールバック
                    sonota = self._find_sonota_fallback(levels, level1_map, level2_map, wow_index)
                    if sonota:
                        sonota_cid, sonota_levels = sonota
                        sonota_path = "/".join(sonota_levels)
                        auto_rows.append([a.product_cat_id, ama_path, sonota_cid, sonota_path, "0.600", "sonota_fallback", ""])
            else:
                # マッチがない場合は「その他」カテゴリにフォールバック
                sonota = self._find_sonota_fallback(levels, level1_map, level2_map, wow_index)
                if sonota:
                    sonota_cid, sonota_levels = sonota
                    sonota_path = "/".join(sonota_levels)
                    auto_rows.append([a.product_cat_id, ama_path, sonota_cid, sonota_path, "0.600", "sonota_fallback", ""])

        return auto_rows, review_rows, review_lvl2_rows

    def _find_sonota_fallback(self, ama_levels, level1_map, level2_map, wow_index):
        """「その他」カテゴリへのフォールバックを検索"""
        # level2_mapにマッチがあれば、そのL1+L2に対応する「その他」を探す
        if len(ama_levels) >= 2:
            ama_key = (ama_levels[0], ama_levels[1])
            if ama_key in level2_map:
                for wow_l1, wow_l2 in level2_map[ama_key]:
                    key = (wow_l1, wow_l2)
                    if key in wow_index["sonota_by_l1l2"]:
                        return wow_index["sonota_by_l1l2"][key]

        # level1_mapからWowma L1を取得し、そのL1に対応する「その他」を探す
        allowed_wow_l1 = [wow for ama, wow in level1_map if ama == ama_levels[0]]
        for wow_l1 in allowed_wow_l1:
            if wow_l1 in wow_index["sonota_by_l1"]:
                return wow_index["sonota_by_l1"][wow_l1]

        return None

    def write_tsv(self, path: Path, header, rows):
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
