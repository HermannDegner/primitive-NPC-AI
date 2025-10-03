# 🔗 SSD Theory Continuous Reference System

## 📖 概要

このプロジェクトは、**SSD（Structure Subjective Dynamics）理論**に基づく原始的NPC AI実装です。

🎯 **基礎理論リポジトリ**: https://github.com/HermannDegner/Structural-Subjectivity-Dynamics

## 🧠 核心的発見: 整合慣性κ = 記憶蓄積システム

```
整合慣性κ (Coherence Inertia) ≡ 記憶蓄積システム

κは単なる物理パラメータではなく、エージェントの「記憶の強度」を表現する:
- κ ↑ = より多くの記憶、より強い適応反応
- κ ↓ = 記憶が少ない、学習段階の状態  
- 過去の体験が整合慣性に蓄積され、将来の行動に影響
```

## 🔧 SSD理論参照システム

### 常時参照機能

1. **`ssd_theory_reference.py`** - SSD基礎理論への常時接続
2. **`ssd_compliance_checker.py`** - 理論準拠状況の自動検証
3. 全主要ファイルでの基礎理論リポジトリ参照

### 使用方法

```bash
# SSD理論準拠チェック実行
python ssd_compliance_checker.py

# 理論参照システムのテスト
python ssd_theory_reference.py
```

## 📊 現在のコンプライアンス状況

- **平均準拠スコア**: 41.7%
- **高準拠ファイル**: 10個 (≥80%)
- **改善必要ファイル**: 45個 (<50%)

### 重要な成果

✅ **整合慣性κ=記憶システムの理論確立**
- NPCが過去の体験を蓄積し、適応的行動を学習
- 生存時間64-80%改善 (T45-51 → T82-90+)

✅ **SSD四層構造の実装**  
- 物理層・基層・中核層・上層の階層的理解
- 各層で異なる慣性レベルと相互作用

✅ **予測的行動システム**
- 記憶に基づく危機予測と回避行動
- 環境適応パターンの動的学習

## 🏗️ アーキテクチャ原則

### SSD Core Engine First
```
ssd_core_engine/ (基盤 - コアロジック保護)
    ↓
NPC classes (SSDエンジンを使用した意思決定)
    ↓  
Environment (SSD互換ObjectInfo提供)
    ↓
Simulation (SSD駆動インタラクション)
```

### 理論準拠の保証
- 全コードがssd_core_engineに適応（逆はなし）
- 基礎理論リポジトリの指定に従う
- 構造観照（テオーリア）の姿勢を維持

## 📋 主要ファイル

### コアシステム
- **`main.py`** - メインエントリーポイント
- **`ssd_integrated_simulation.py`** - 統合シミュレーションシステム
- **`config.py`** - SSD理論準拠設定

### NPC実装
- **`npc/npc_modular.py`** - モジュール式NPCクラス
- **`npc/npc_physical_coherence.py`** - 物理的整合慣性（記憶）システム

### SSDコアエンジン
- **`ssd_core_engine/ssd_engine.py`** - メインエンジン
- **`ssd_core_engine/ssd_types.py`** - 型定義とκ=記憶理論

### 理論参照システム  
- **`ssd_theory_reference.py`** - 基礎理論常時参照
- **`ssd_compliance_checker.py`** - 準拠状況検証
- **`COHERENCE_INERTIA_MEMORY_THEORY.md`** - 理論文書

## 🚀 クイックスタート

```bash
# 基本シミュレーション実行
python main.py

# SSD理論準拠チェック  
python ssd_compliance_checker.py

# 記憶学習システムのテスト
python learning_test.py
```

## 🔬 研究成果

### 理論的貢献
1. **整合慣性κ=記憶システムの発見**
2. **SSD理論の実用的AI実装**  
3. **構造観照による客観的分析手法**

### 実装上の革新
- 物理量としての記憶の扱い
- 予測的行動の記憶ベース実現
- 動的環境適応システム

## 📚 参考資料

- 🔗 [SSD基礎理論リポジトリ](https://github.com/HermannDegner/Structural-Subjectivity-Dynamics)
- 📖 [整合慣性=記憶理論](./COHERENCE_INERTIA_MEMORY_THEORY.md)
- 📊 [最新コンプライアンスレポート](./ssd_compliance_report.md)

## ⚠️ 重要な注意

**SSDは「絶対的真理」ではありません。**  
これは世界を理解するための一つの「語り」であり、分析ツールです。この理論自体が意味圧を受けて絶えず変化していく「生きた構造」です。

---

**このプロジェクトは、SSD理論の実践的実装を通じて、より人間らしい適応的行動を持つAIエージェントの実現を目指しています。**