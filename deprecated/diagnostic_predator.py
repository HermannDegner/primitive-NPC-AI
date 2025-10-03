#!/usr/bin/env python3
"""
捕食者システム診断スクリプト
なぜ捕食者が攻撃していないか調査
"""

import sys
from main_backup import run_ssd_enhanced_simulation

def diagnostic_simulation():
    """診断用のシミュレーション実行"""
    print("🔍 捕食者システム診断開始")
    
    # 短時間のシミュレーション実行
    try:
        roster, ssd_logs, env_logs, seasonal_logs = run_ssd_enhanced_simulation(5)
        
        print(f"📊 シミュレーション完了")
        print(f"生存者: {len([npc for npc in roster.values() if npc.is_alive()])}/{len(roster)}")
        
        # 死因分析
        deaths = [npc for npc in roster.values() if not npc.is_alive()]
        if deaths:
            print(f"💀 死者: {len(deaths)}人")
            for npc in deaths:
                print(f"  - {npc.name}")
        else:
            print("💀 死者: なし")
        
        # ログ分析
        predator_logs = []
        for log in env_logs:
            if any(word in log.lower() for word in ['predator', '捕食', '🐺', 'kill', 'injury']):
                predator_logs.append(log)
        
        if predator_logs:
            print(f"\n🐺 捕食者関連ログ ({len(predator_logs)}件):")
            for log in predator_logs:
                print(f"  {log}")
        else:
            print("\n🐺 捕食者関連ログ: なし")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnostic_simulation()