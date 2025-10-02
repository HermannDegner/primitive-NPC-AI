#!/usr/bin/env python3
"""
簡易生存性テスト - 洞窟雨水システムの影響を確認
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from environment import Environment
from npc import NPC
import random

def quick_survival_test():
    """クイック生存性テスト"""
    print("=== 簡易生存性テスト ===\n")
    
    # テスト1: 従来システム（洞窟水なし）
    print("🟡 従来システムテスト（洞窟水なし）")
    env1 = Environment(size=100, n_caves=0, n_water=3)
    env1.caves = {}  # 洞窟を無効化
    if hasattr(env1, 'cave_water_storage'):
        delattr(env1, 'cave_water_storage')
    
    roster1 = {}
    for i in range(4):
        name = f"NPC_{chr(65+i)}"
        preset = {"exploration_range": 20, "risk_tolerance": 0.5, "cooperation": 0.7, "empathy": 0.6}
        npc = NPC(name, preset, env1, roster1, (40 + i*5, 40 + i*5))
        npc.thirst = 80 + random.randint(0, 30)
        roster1[name] = npc
    
    for npc in roster1.values():
        npc.roster = roster1
    
    # 50tickシミュレーション
    deaths1 = 0
    thirst_deaths1 = 0
    total_water_consumed1 = 0
    
    for t in range(1, 51):
        env1.ecosystem_step(list(roster1.values()), t)
        
        for npc in roster1.values():
            if not npc.alive and npc.thirst >= 200:
                thirst_deaths1 += 1
            if not npc.alive:
                deaths1 += 1
        
        # NPC行動
        for npc in roster1.values():
            if npc.alive and npc.thirst > 60:
                old_thirst = npc.thirst
                npc.seek_water(t)
                if npc.thirst < old_thirst:
                    total_water_consumed1 += (old_thirst - npc.thirst)
    
    survivors1 = len([npc for npc in roster1.values() if npc.alive])
    survival_rate1 = (survivors1 / len(roster1)) * 100
    
    print(f"結果: 生存率 {survival_rate1:.1f}% ({survivors1}/4体)")
    print(f"渇死: {thirst_deaths1}体, 総水消費: {total_water_consumed1:.1f}L\n")
    
    # テスト2: 新システム（洞窟水あり）
    print("🔵 新システムテスト（洞窟水あり）")
    env2 = Environment(size=100, n_caves=4, n_water=3)
    
    roster2 = {}
    for i in range(4):
        name = f"NPC_{chr(65+i)}"
        preset = {"exploration_range": 20, "risk_tolerance": 0.5, "cooperation": 0.7, "empathy": 0.6}
        npc = NPC(name, preset, env2, roster2, (40 + i*5, 40 + i*5))
        npc.thirst = 80 + random.randint(0, 30)
        roster2[name] = npc
    
    for npc in roster2.values():
        npc.roster = roster2
    
    # 50tickシミュレーション
    deaths2 = 0
    thirst_deaths2 = 0
    total_water_consumed2 = 0
    cave_water_consumed2 = 0
    
    for t in range(1, 51):
        env2.ecosystem_step(list(roster2.values()), t)
        
        for npc in roster2.values():
            if not npc.alive and npc.thirst >= 200:
                thirst_deaths2 += 1
            if not npc.alive:
                deaths2 += 1
        
        # NPC行動と洞窟水使用統計
        for npc in roster2.values():
            if npc.alive and npc.thirst > 60:
                old_thirst = npc.thirst
                npc.seek_water(t)
                if npc.thirst < old_thirst:
                    recovery = old_thirst - npc.thirst
                    total_water_consumed2 += recovery
                    
                    # 洞窟水使用判定
                    if hasattr(npc, 'log') and npc.log:
                        last_action = npc.log[-1] if npc.log else {}
                        if last_action.get('action') == 'drink_cave_water':
                            cave_water_consumed2 += recovery
    
    survivors2 = len([npc for npc in roster2.values() if npc.alive])
    survival_rate2 = (survivors2 / len(roster2)) * 100
    cave_water_ratio = (cave_water_consumed2 / total_water_consumed2 * 100) if total_water_consumed2 > 0 else 0
    
    print(f"結果: 生存率 {survival_rate2:.1f}% ({survivors2}/4体)")
    print(f"渇死: {thirst_deaths2}体, 総水消費: {total_water_consumed2:.1f}L")
    print(f"洞窟水依存度: {cave_water_ratio:.1f}% ({cave_water_consumed2:.1f}L)")
    
    # 比較結果
    print(f"\n📊 比較結果:")
    improvement = survival_rate2 - survival_rate1
    thirst_change = thirst_deaths1 - thirst_deaths2
    
    print(f"生存率変化: {improvement:+.1f}%")
    print(f"渇死減少: {thirst_change:+}体")
    
    if improvement > 0:
        print("✅ 洞窟雨水システムにより生存性が改善!")
    elif improvement < 0:
        print("⚠️ 洞窟雨水システムにより生存性が悪化")
    else:
        print("➡️ 洞窟雨水システムの影響は中立")
        
    # 洞窟水システムの機能確認
    if hasattr(env2, 'cave_water_storage'):
        print(f"\n🏞️ 洞窟水状況:")
        for cave_id, data in env2.cave_water_storage.items():
            print(f"  {cave_id}: {data['water_amount']:.1f}L / {data['max_capacity']:.1f}L")

if __name__ == "__main__":
    quick_survival_test()