# カテゴリマッチング精度改善 - ロードマップ

## 目標

- Wowma第1・第2カテゴリを Amazon上位カテゴリと**ほぼ完全一致**させる
- 下位カテゴリは類推で紐づけ、困難な場合は「その他xx」にフォールバック
- **人間の手動判断を最小限**にする

---

## Phase 1: 致命的バグの修正【最優先】

### 1.1 正規表現の修正

**対象ファイル**: `yaget/management/commands/match_categories.py`

**修正内容**:
```python
# 修正前 (121行目)
t = re.sub(r"[^0-9a-zA-Zぁ-んァ-ン一-龥\s]+", " ", t)

# 修正後（長音ー、カタカナ拡張、中黒を許可）
t = re.sub(r"[^0-9a-zA-Zぁ-んァ-ヶー一-龥\s]+", " ", t)
```

**理由**:
- `ー` (U+30FC) 長音記号
- `ヴ` (U+30F4) 等のカタカナ拡張
- これらが削除されることでsynonymsが機能しない

**期待効果**: synonyms.tsvの7,361件の日本語対応が即座に有効化

### 1.2 修正後の検証

```bash
python manage.py match_categories \
  --synonyms docs/category_mapping/synonyms.tsv \
  --level1-map docs/category_mapping/level_1_cat.txt \
  --outdir codex_out \
  --auto-threshold 0.7 --review-threshold 0.4
```

auto件数が0から大幅増加することを確認。

---

## Phase 2: 第2階層マッピングの導入

### 2.1 level_2_cat.txt の新規作成

**ファイル**: `docs/category_mapping/level_2_cat.txt`

**形式**:
```
AmaPath第一階層	AmaPath第二階層	WowPath第一階層	WowPath第二階層
Musical Instruments	Guitars	楽器・音響機器	ギター
Musical Instruments	Bass Guitars	楽器・音響機器	ベース
Musical Instruments	Drums & Percussion	楽器・音響機器	ドラム・パーカッション
...
```

### 2.2 match_categories.py の拡張

**新機能**:
1. `--level2-map` オプションの追加
2. 第2階層まで完全一致するもののみ候補とする
3. 第3階層以降はfuzzyマッチ

**ロジック変更**:
```
1. 第1階層: level_1_cat.txt で許可リスト絞り込み（既存）
2. 第2階層: level_2_cat.txt で許可リスト絞り込み（新規）
3. 第3階層以降: fuzzyマッチ + synonyms正規化
4. マッチ困難: 「その他」カテゴリへフォールバック
```

### 2.3 主要カテゴリの第2階層マッピング作成

**作成対象**（件数が多い順）:
1. Sports & Outdoors (2,512件)
2. Clothing, Shoes & Jewelry (2,866件)
3. Industrial & Scientific (2,613件)
4. Grocery & Gourmet Food (2,104件)
5. Home & Kitchen (1,997件)
6. Tools & Home Improvement (1,863件)
7. Health & Household (1,300件)
8. Electronics (1,148件)
9. Musical Instruments (784件)

---

## Phase 3: 「その他」フォールバック機能

### 3.1 フォールバックロジックの実装

**条件**:
- 第2階層までマッチしたが、第3階層以降でスコアがreview_threshold未満
- または候補が見つからない

**処理**:
1. 同じWowma第2階層配下の「その他xx」カテゴリを検索
2. 存在すればそこにマッピング
3. 存在しなければWowma第1階層直下の「その他」にマッピング

**例**:
```
Amazon: Musical Instruments/Instrument Accessories/Ukulele Accessories
→ Wowma: 楽器・音響機器/その他楽器・音響機器
```

### 3.2 「その他」カテゴリマスタの作成

各Wowma第2階層に対応する「その他」カテゴリIDをマスタ化:

```python
OTHER_CATEGORY_MAP = {
    ('楽器・音響機器', None): 5605,  # その他楽器・音響機器
    ('スポーツ・アウトドア', None): 4009,  # その他のスポーツ
    ('おもちゃ・趣味', None): 2903,  # その他おもちゃ
    ...
}
```

---

## Phase 4: synonyms.tsv の拡充

### 4.1 不足している翻訳の追加

**優先度高**（カテゴリ名に頻出）:
```
archery	archery,アーチェリー,弓道
airsoft	airsoft,エアソフトガン,サバゲー
stringed	stringed,弦,弦楽
woodwind	woodwind,木管,木管楽器
percussion	percussion,パーカッション,打楽器
brass	brass,金管,金管楽器,ブラス
```

### 4.2 複合カテゴリの分解対応

「Hunting & Fishing」のような複合カテゴリを扱う:
```
hunting	hunting,ハンティング,狩猟
fishing	fishing,フィッシング,釣り
```

→ 正規化時に両方のトークンが残り、マッチ精度向上

---

## Phase 5: 閾値とスコアリングの最適化

### 5.1 閾値の調整検討

| パラメータ | 現在値 | 検討値 |
|-----------|-------|-------|
| auto_threshold | 0.7 | 0.6〜0.65 |
| review_threshold | 0.4 | 0.35 |

**Phase 1-2完了後**に再評価。

### 5.2 スコアリング改善

- 階層一致数による重み付け強化
- 「その他」カテゴリへのマッチはスコア減点
- 完全一致トークン数によるボーナス

---

## 実装順序と優先度

| Phase | 作業内容 | 優先度 | 期待効果 |
|-------|---------|-------|---------|
| 1.1 | 正規表現修正 | **最高** | auto件数 0→数百件 |
| 1.2 | 修正検証 | **最高** | 効果確認 |
| 2.1 | level_2_cat.txt作成 | 高 | 誤マッチ大幅減少 |
| 2.2 | match_categories.py拡張 | 高 | 第2階層フィルタ有効化 |
| 3.1 | フォールバック実装 | 中 | マッチ困難カテゴリ対応 |
| 4.1 | synonyms.tsv拡充 | 中 | 翻訳精度向上 |
| 5.1 | 閾値調整 | 低 | 微調整 |

---

## 検証方法

### 各Phase完了時

```bash
# マッチング実行
python manage.py match_categories \
  --synonyms docs/category_mapping/synonyms.tsv \
  --level1-map docs/category_mapping/level_1_cat.txt \
  --level2-map docs/category_mapping/level_2_cat.txt \
  --outdir codex_out \
  --auto-threshold 0.7 --review-threshold 0.4

# 結果確認
wc -l codex_out/category_match_*.tsv
head -50 codex_out/category_match_auto.tsv
head -50 codex_out/category_match_review.tsv
```

### 成功基準

| 指標 | 目標値 |
|------|-------|
| auto件数 | 5,000件以上 |
| review件数 | 3,000件以下 |
| 誤マッチ率（サンプル検査） | 5%以下 |

---

## ファイル変更一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `yaget/management/commands/match_categories.py` | 修正 | 正規表現修正、第2階層フィルタ追加 |
| `docs/category_mapping/level_2_cat.txt` | 新規 | 第2階層マッピング定義 |
| `docs/category_mapping/synonyms.tsv` | 修正 | 翻訳追加 |

---

## 次のアクション

1. **ユーザー確認**: このロードマップで進めてよいか
2. **Phase 1実施**: 正規表現修正 → 検証
3. **Phase 2実施**: level_2_cat.txt作成開始

---

## 備考

- git操作は人間が実施
- 本番反映前にバックアップ必須
- 各Phase完了ごとに中間報告
