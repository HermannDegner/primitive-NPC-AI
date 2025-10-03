# Primitive NPC AI - SSD Core Engine Architecture

## 🎯 基本設計原則: ssd_core_engine中心アーキテクチャ

**重要**: このプロジェクトはssd_core_engineを**基軸**とした設計です。

### 📐 アーキテクチャ指針

```
ssd_core_engine/  ← 【理論的基盤・変更厳禁】
    ↑ 適合
npc/, environment.py, simulation  ← 【周辺コードはSSDエンジンに適合】
```

**基本原則:**
- ✅ ssd_core_engineの理論的整合性を最優先で保持
- ✅ 全ての周辺コードはSSDエンジン仕様に**合わせて**作成
- ❌ ssd_core_engineを他システムに合わせて変更することは禁止
- ✅ 最大限のSSD機能活用を目標とする

この設計により、理論的に一貫性のある高度なAIシステムを実現しています。

## プロジェクト構造

### コアシステム
- `main.py` - メインエントリーポイント（モジュール化システム）
- `integrated_simulation.py` - 統合シミュレーション実行エンジン
- `ssd_enhanced_npc.py` - SSD拡張NPCクラス
- `environment.py` - 環境システム
- `config.py` - 設定管理

### SSD Core Engine
- `ssd_core_engine/` - 主観的構造動力学エンジン
  - SSD決定システム
  - 意味圧力システム  
  - 整合性跳躍システム
  - 縄張りシステム

### NPCモジュール
- `npc/` - NPCコンポーネント
  - 基本NPC機能
  - 協力システム
  - 狩猟システム
  - 移動システム
  - 生存システム

### サポートシステム
- `seasonal_system.py` - 季節システム
- `predator_territory_system.py` - 捕食者縄張りシステム
- `future_prediction.py` - 未来予測システム
- `utils.py` - ユーティリティ関数

### テストと非推奨ファイル
- `tests/` - テストスクリプト群
- `deprecated/` - 非推奨・未使用ファイル
- `main_backup.py` - フォールバックシステム

## 実行方法

```bash
python main.py --ticks 100
```

## 機能

- ✅ SSD（主観的構造動力学）による意思決定
- ✅ 縄張り行動システム
- ✅ 集団境界形成
- ✅ 季節サイクル
- ✅ 捕食者-獲物相互作用
- ✅ 協力行動
- ✅ 環境適応

## システム特徴

1. **モジュール化アーキテクチャ**: クリーンで保守性の高いコード構造
2. **SSD Engine**: 高度な意思決定メカニズム
3. **フォールバックサポート**: `main_backup.py`による互換性保持
4. **包括的テスト**: `tests/`ディレクトリに整理された豊富なテストスイート