# Archive Directory

このディレクトリには、プロジェクトの重要なバックアップファイルが保管されています。

## 📁 保管ファイル

### `main_backup.py`
- **用途**: 統合シミュレーションシステムのフォールバック版
- **説明**: `integrated_simulation.py`に問題が発生した場合の緊急用バックアップ
- **機能**: 完全なSSD拡張シミュレーション機能

## 🚨 緊急時の復旧手順

### 1. メインシステムに問題がある場合
```bash
# アーカイブからルートディレクトリに復元
copy archive\main_backup.py .
```

### 2. フォールバック機能の確認
```bash
python main.py --ticks 10
```

### 3. 問題解決後の再アーカイブ
```bash
# 問題解決後、再度アーカイブに戻す
move main_backup.py archive\
```

## 📋 保守手順

### 定期的なアーカイブ更新
- integrated_simulation.pyに重要な変更がある場合
- main_backup.pyを最新版に更新してアーカイブ

### アーカイブの整合性確認
```bash
# アーカイブ版の動作テスト
cd archive
python -c "from main_backup import run_ssd_enhanced_simulation; print('✅ Archive backup is functional')"
```

## 💡 利点

- **ディスク容量の節約**: 通常時はアーカイブに保管
- **クリーンな構造**: メインディレクトリの整理
- **確実な保管**: 必要時に即座に復元可能
- **バージョン管理**: アーカイブ内で過去バージョンの管理可能