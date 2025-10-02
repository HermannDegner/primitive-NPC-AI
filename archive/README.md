# アーカイブフォルダー

このフォルダーには、primitive-NPC-AIプロジェクトの古いファイルと実行結果が保存されています。

## フォルダー構造

### `/test_outputs/`

- 各種テスト実行の出力ファイル
- `output_run_*.txt`: 複数回実行したテスト結果
- `output.txt`: メイン出力ファイル
- `simulation_output.txt`: シミュレーション出力

### `/results/`

- シミュレーション実行結果
- `group_hunt_summary.txt`: グループ狩猟の要約
- `mass_death_analysis_results.json`: 大量死亡分析結果
- `simulation_results_10runs.json`: 10回実行のシミュレーション結果

### `/analysis_tools/`

- 分析・解析ツール
- `boundary_formation_test.py`: 境界形成テスト
- `cooperation_analysis.py`: 協力行動分析
- `mass_death_analysis.py`: 大量死亡分析

### `/scripts/`

- 実行用スクリプト
- `run_10_tests.*`: 10回テスト実行スクリプト（bat, ps1, py）

### `/test_files/`

- テストファイル群
- `test_*.py`: 各機能のテストファイル
- `simple_cooperation_test.py`: シンプル協力テスト

### ルートレベル

- `priority_village_sim*.py`: 優先度付き村シミュレーションの各バージョン
- `SSDNPCAI*.py`: SSD NPC AIシステムの各バージョン
- `ssd_village.py`: SSD村システム

## 整理日

2025年10月2日

## 注意事項

これらのファイルは開発過程で生成された履歴ファイルです。必要に応じて参照できますが、現在のメインシステムには影響しません。