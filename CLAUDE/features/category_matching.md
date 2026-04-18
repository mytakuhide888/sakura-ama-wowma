# カテゴリマッチング

最終更新: 2026-04-18

---

## 概要

Amazon商品カテゴリ（英語）と Wowma 商品カテゴリ（日本語）を自動マッチングする仕組み。
管理コマンド `match_categories` で実行し、結果をDBに反映する。

---

## 達成状況

| 指標 | 改善前 | **最終（Phase 27）** |
|------|--------|---------------------|
| auto | 0件 | **21,147件（98.6%）** |
| review | 3,304件 | **294件（1.4%）** |
| review_level2 | 215件 | **5件** |
| VPS DB反映 | 未 | **済み（2026-04-18）** |

> **Phase 26 (2026-04-05)**: review=0, review_level2=0 の全件自動化達成  
> **Phase 27 (2026-04-06)**: レビュー結果62件NG修正を反映  
> **VPS 本番実行 (2026-04-18)**: auto=21,147件確定、DBへ一括反映

---

## 仕組み（マッチング優先順位）

```
1. level_4_cat.txt  Amazon (L1,L2,L3,L4) → Wowma (L1,L2)  最高優先
2. level_3_cat.txt  Amazon (L1,L2,L3)    → Wowma (L1,L2)
3. level_2_cat.txt  Amazon (L1,L2)       → Wowma (L1,L2)  +0.15スコアボーナス
4. level_1_cat.txt  Amazon L1            → Wowma L1       検索範囲の絞り込み
5. synonyms.tsv     英語↔日本語 同義語辞書               fuzzy matchingの精度向上
6. sonota_fallback  スコア低い場合「その他」カテゴリへ自動振り分け
7. sonota_l3fallback level3_mapマッチ後にそのL2内の「その他」へフォールバック
8. sonota_l2fallback L2のみパスのフォールバック（Phase 26追加）
```

---

## マッピングファイル構成

| ファイル | 内容 | 件数 |
|---------|------|------|
| `docs/category_mapping/level_1_cat.txt` | Amazon L1 → Wowma L1 | 47エントリ（19カテゴリ） |
| `docs/category_mapping/level_2_cat.txt` | Amazon L2 → Wowma L2 | 553件 |
| `docs/category_mapping/level_3_cat.txt` | Amazon L3 → Wowma L2 | 1,662件 |
| `docs/category_mapping/level_4_cat.txt` | Amazon L4 → Wowma L2 | 67件 |
| `docs/category_mapping/synonyms.tsv` | 英語↔日本語 同義語 | 15,145件 |

---

## カバレッジ

| 階層 | カバレッジ |
|------|----------|
| L1 | 100%（19/19カテゴリ） |
| L2 | 100%（553件） |
| L3 | 99.8%（565/566種類） |
| L4 | 100%（1,846語） |
| L5 | 100%（1,727語） |

---

## 実行コマンド

### VPSでのマッチング実行

```bash
source /home/django/djangoenv/bin/activate
cd /home/django/sample
python manage.py match_categories \
  --synonyms docs/category_mapping/synonyms.tsv \
  --level1-map docs/category_mapping/level_1_cat.txt \
  --level2-map docs/category_mapping/level_2_cat.txt \
  --outdir codex_out \
  --auto-threshold 0.595 --review-threshold 0.35
```

### DBへの反映（match_categories実行後）

```python
# manage.py shell で実行
import csv
from pathlib import Path
from yaget.models import AmaCategory

tsv_path = Path('codex_out/category_match_auto.tsv')
updates = {}
with open(tsv_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        updates[int(row['AmaCatID'])] = int(row['WowCatID_candidate'])

objs = AmaCategory.objects.filter(product_cat_id__in=list(updates.keys()))
for obj in objs:
    obj.wow_cat_id = updates[obj.product_cat_id]
AmaCategory.objects.bulk_update(objs, ['wow_cat_id'], batch_size=500)
```

---

## 注意事項

- `level_1_cat.txt` と `level_2_cat.txt` でWowmaカテゴリ名の**表記を統一**すること
- Amazon L1カテゴリ名は**大文字/小文字を正確に一致**させること（例: `Books` not `books`）
- `synonyms.tsv` のコメント行は `#` で始まる
- ローカルWSLではDjango環境なし → VPSでのみ実行可能

---

## 残課題

| # | 課題 | 優先度 |
|---|------|--------|
| - | VPS本番の review 294件の内訳確認（閾値0.595で未達のもの） | 低 |
| - | 閾値の微調整検討（現在: auto=0.595, review=0.35） | 低 |

---

## フェーズ別履歴サマリ

| Phase | 主な内容 | auto件数 |
|-------|---------|---------|
| 1 | 正規表現バグ修正 | 261件 |
| 2 | level_2_cat.txt 新規作成 | 3,473件 |
| 3 | 「その他」フォールバック実装 | 4,911件 |
| 4〜8 | 全階層カバレッジ達成 | 7,666件 |
| 9〜17 | level_3_map大規模拡張、synonyms大量追加 | 〜 |
| 24〜25 | review=0件達成 | 19,616件 |
| 26 | 全件自動化（review=0, review_level2=0） | 21,446件 |
| 27 | レビュー結果反映 | 21,446件 |
| VPS反映 | DB一括update | **21,147件確定** |
