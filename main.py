#!/usr/bin/env python3
"""
Enhanced SSD Theory Primitive NPC AI Simulation - Main Entry Point
完全統合版: SSD (4層構造) + 主観的境界システム + スマート環境 + 季節システム

統合実行環境: Enhanced SSD + Seasonal + Boundary + Smart World
作成日: 2024年
バージョン: v3.1 - モジュール化版
"""

try:
    from enhanced_simulation import run_enhanced_ssd_simulation
    from analysis_system import (
        analyze_enhanced_results, 
        analyze_survival_patterns,
        generate_simulation_report
    )
except ImportError as e:
    print(f"⚠️ モジュールのインポートエラー: {e}")
    print("依存ファイルが見つかりません。シミュレーションを実行できません。")
    exit(1)

def main():
    """メインエントリーポイント - Enhanced SSD季節シミュレーション実行"""
    
    print("🌍 Enhanced SSD Theory Simulation - Seasonal Carnivore Survival")
    print("完全統合版: SSD + 境界システム + スマート環境 + 季節システム")
    print("=" * 60)
    
    try:
        # シミュレーション実行（400ティック = 1年間）
        roster, ssd_logs, env_logs, seasonal_logs = run_enhanced_ssd_simulation(ticks=400)
        
        # 結果分析
        print("\n" + "🔍 シミュレーション結果分析中...")
        analyze_enhanced_results(roster, ssd_logs, env_logs, seasonal_logs)
        
        # 生存パターン分析
        analyze_survival_patterns(roster, seasonal_logs)
        
        # 詳細レポート生成
        report = generate_simulation_report(roster, ssd_logs, env_logs, seasonal_logs)
        print(f"\n� 詳細レポート: {len(report)} 項目の分析完了")
        
    except Exception as e:
        print(f"❌ シミュレーション実行エラー: {e}")
        import traceback
        traceback.print_exc()

# メイン実行
if __name__ == "__main__":
    main()