# 📁 Primitive NPC AI - プロジェクト構造

## 🏗️ 整理されたディレクトリ構造

```
primitive-NPC-AI/
├── 📄 main.py                     # メインエントリーポイント
├── 📄 config.py                   # SSD理論準拠設定
├── 📄 ssd_integrated_simulation.py # 統合シミュレーションシステム  
├── 📄 ssd_theory_reference.py     # SSD基礎理論参照システム
├── 📄 ssd_compliance_checker.py   # 理論準拠チェッカー
├── 📄 README.md                   # プロジェクト説明
│
├── 📂 ssd_core_engine/           # SSD理論コアエンジン
│   ├── ssd_engine.py            # メインエンジン
│   ├── ssd_types.py             # 型定義・κ=記憶理論
│   ├── ssd_decision.py          # 意思決定システム
│   ├── ssd_prediction.py        # 予測システム
│   └── ...                      # その他コア機能
│
├── 📂 npc/                      # NPCクラス実装
│   ├── npc_modular.py          # モジュール式NPCクラス
│   ├── npc_physical_coherence.py # 物理的整合慣性（記憶）
│   ├── npc_survival.py         # 生存システム
│   └── ...                     # その他NPC機能
│
├── 📂 systems/                  # 環境・システムファイル
│   ├── environment.py          # 環境システム
│   ├── seasonal_system.py      # 季節システム  
│   ├── future_prediction.py    # 未来予測システム
│   ├── utils.py               # ユーティリティ
│   └── predator_territory_system.py # 捕食者・縄張りシステム
│
├── 📂 experiments/              # 実験・テストファイル
│   ├── learning_test.py        # 学習システムテスト
│   ├── memory_coherence_test.py # 記憶整合テスト  
│   ├── long_term_test.py       # 長期実行テスト
│   ├── relief_test.py          # 環境負荷軽減テスト
│   └── ...                     # その他実験
│
├── 📂 validation/               # 検証・デバッグファイル
│   ├── integration_success_summary.py # 統合成功レポート
│   ├── water_access_debug.py          # 水アクセスデバッグ
│   └── water_access_success_validation.py # 水アクセス検証
│
├── 📂 tests/                    # 正式テストスイート
│   └── ...                     # ユニットテスト等
│
├── 📂 docs/                     # ドキュメント
│   ├── COHERENCE_INERTIA_MEMORY_THEORY.md # κ=記憶理論文書
│   ├── SSD_REFERENCE_SYSTEM.md            # SSD参照システム説明
│   └── ssd_compliance_report.md           # 理論準拠レポート
│
├── 📂 deprecated/               # 非推奨ファイル
│   ├── ssd_enhanced_npc.py     # 旧NPCクラス
│   └── integrated_simulation.py # 旧統合システム
│
└── 📂 archive/                  # アーカイブ
    └── ...                     # 過去バージョン
```

## 🎯 各ディレクトリの役割

### 📄 ルートファイル
- **重要度**: 最高
- **内容**: プロジェクトの核心機能
- **SSD準拠**: 必須

### 📂 ssd_core_engine/
- **重要度**: 最高  
- **内容**: SSD理論の物理的実装
- **原則**: コアロジック保護、他からの適応のみ

### 📂 npc/
- **重要度**: 高
- **内容**: κ=記憶システムを持つNPCクラス
- **特徴**: SSDエンジンを使用した意思決定

### 📂 systems/
- **重要度**: 高
- **内容**: 環境・季節・予測などのシステム
- **役割**: SSD互換ObjectInfo提供

### 📂 experiments/
- **重要度**: 中
- **内容**: 研究・実験用スクリプト
- **目的**: 新機能のテストと検証

### 📂 validation/
- **重要度**: 中  
- **内容**: システム検証・デバッグツール
- **用途**: 統合テスト・問題診断

### 📂 docs/
- **重要度**: 高
- **内容**: 理論文書・レポート・説明
- **特徴**: SSD基礎理論への参照

## 🔧 使用方法

### 基本実行
```bash
# メインシミュレーション
python main.py

# SSD理論準拠チェック
python ssd_compliance_checker.py
```

### 実験・テスト
```bash  
# 学習システムテスト
python experiments/learning_test.py

# 長期実行テスト
python experiments/long_term_test.py
```

### 検証・デバッグ
```bash
# 統合状況確認
python validation/integration_success_summary.py

# 水アクセス問題診断  
python validation/water_access_debug.py
```

## 📋 ファイル管理方針

### ✅ 追加時の原則
1. **SSD理論準拠** - 基礎理論リポジトリに準拠
2. **適切なディレクトリ** - 機能に応じた配置
3. **命名規則** - わかりやすく一貫性のある名前

### 🔄 整理のルール
1. **実験ファイル** → `experiments/`
2. **検証ファイル** → `validation/`  
3. **システムファイル** → `systems/`
4. **古いファイル** → `deprecated/` or `archive/`

---

**この整理により、プロジェクトの可読性・保守性・SSD理論準拠が大幅に向上しました。** 🎉