#!/usr/bin/env python3
"""
SSD Village Simulation - Main Entry Point
構造主観力学(SSD)理論に基づく原始村落シミュレーション
https://github.com/HermannDegner/Structural-Subjectivity-Dynamics

分割されたモジュール構成:
- config.py: 設定とプリセット
- environment.py: 環境システム
- social.py: 社会システム
- ssd_core.py: SSD理論コア
- npc.py: NPCエージェント
- utils.py: ユーティリティ関数
- simulation.py: メインシミュレーション
"""

# メインシミュレーションを実行
if __name__ == "__main__":
    try:
        from simulation import run_simulation, analyze_results
        
        print("=== SSD Village Simulation ===")
        print("構造主観力学理論に基づく原始村落シミュレーション")
        print("https://github.com/HermannDegner/Structural-Subjectivity-Dynamics")
        print()
        
        # シミュレーション実行
        final_npcs, df_logs, df_weather, df_ecosystem = run_simulation(ticks=500)
        
        # 結果分析
        analyze_results(final_npcs, df_logs, df_weather, df_ecosystem)
        
    except ImportError as e:
        print(f"モジュールインポートエラー: {e}")
        print("必要なモジュールファイルが見つかりません。")
        print("以下のファイルが同じディレクトリにあることを確認してください:")
        print("- config.py")
        print("- environment.py") 
        print("- social.py")
        print("- ssd_core.py")
        print("- npc.py")
        print("- utils.py")
        print("- simulation.py")
    except Exception as e:
        print(f"実行エラー: {e}")
        import traceback
        traceback.print_exc()