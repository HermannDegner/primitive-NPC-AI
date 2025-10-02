#!/usr/bin/env python3
"""
洞窟雨水システム導入前後の生存性比較テスト
- 従来システム（無限水源のみ）
- 新システム（有限洞窟水 + 無限水源）
- 生存率、渇死率、生存期間の比較
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from environment import Environment
from npc import NPC
import random
import time
import copy

def create_harsh_environment(enable_cave_water=True):
    """厳しい環境を作成（水源を制限）"""
    env = Environment(size=120, n_caves=6 if enable_cave_water else 0, n_water=2)  # 水源を極端に制限
    
    # 水源を遠い場所に配置して水取得を困難にする
    env.water_sources = {
        "water_distant1": (10, 10),    # 左上端
        "water_distant2": (110, 110),  # 右下端
    }
    
    # 洞窟水システムが無効な場合は洞窟水ストレージを削除
    if not enable_cave_water:
        if hasattr(env, 'cave_water_storage'):
            delattr(env, 'cave_water_storage')
        env.caves = {}
    
    return env

def create_test_npcs(env, num_npcs=8):
    """テスト用のNPCを作成（中央付近にランダム配置）"""
    roster = {}
    
    for i in range(num_npcs):
        name = f"NPC_{chr(65+i)}"
        preset = {
            "exploration_range": 25 + random.randint(0, 15),
            "risk_tolerance": 0.4 + random.random() * 0.4,
            "cooperation": 0.6 + random.random() * 0.4,
            "empathy": 0.5 + random.random() * 0.4
        }
        
        # 中央付近にランダム配置
        start_pos = (50 + random.randint(-20, 20), 50 + random.randint(-20, 20))
        
        npc = NPC(name, preset, env, roster, start_pos)
        npc.thirst = random.randint(60, 100)  # 初期渇きレベル
        npc.hunger = random.randint(30, 60)   # 初期空腹レベル
        roster[name] = npc
    
    # 各NPCにrosterを設定
    for npc in roster.values():
        npc.roster = roster
    
    return roster

def run_survival_test(enable_cave_water=True, ticks=200, test_name="テスト"):
    """生存テストを実行"""
    print(f"\n=== {test_name} ===")
    
    env = create_harsh_environment(enable_cave_water)
    roster = create_test_npcs(env, 8)
    
    # 統計情報
    survival_stats = {
        "deaths": [],
        "death_causes": {"thirst": 0, "hunger": 0, "predator": 0},
        "avg_survival_time": 0,
        "final_survivors": 0,
        "critical_events": []
    }
    
    water_access_stats = {
        "cave_water_used": 0,
        "regular_water_used": 0,
        "water_shortage_events": 0
    }
    
    print(f"初期状況: NPCs {len(roster)}体, 水源 {len(env.water_sources)}個")
    if hasattr(env, 'cave_water_storage'):
        print(f"洞窟水システム: 有効 (洞窟 {len(env.caves)}個)")
    else:
        print("洞窟水システム: 無効")
    
    for t in range(1, ticks + 1):
        # 環境更新
        env.ecosystem_step(list(roster.values()), t)
        
        # 死亡チェックと統計更新
        for npc_name, npc in list(roster.items()):
            if not npc.alive:
                if npc_name not in [d["name"] for d in survival_stats["deaths"]]:
                    death_cause = "unknown"
                    if npc.thirst >= 200:
                        death_cause = "thirst"
                        survival_stats["death_causes"]["thirst"] += 1
                    elif npc.hunger >= 200:
                        death_cause = "hunger"
                        survival_stats["death_causes"]["hunger"] += 1
                    else:
                        death_cause = "predator"
                        survival_stats["death_causes"]["predator"] += 1
                    
                    survival_stats["deaths"].append({
                        "name": npc_name,
                        "time": t,
                        "cause": death_cause,
                        "thirst": npc.thirst,
                        "hunger": npc.hunger
                    })
                    print(f"💀 T{t}: {npc_name} 死亡 - 原因: {death_cause} (渇き:{npc.thirst:.1f}, 空腹:{npc.hunger:.1f})")
        
        # NPC行動
        alive_npcs = [npc for npc in roster.values() if npc.alive]
        for npc in alive_npcs:
            old_thirst = npc.thirst
            old_hunger = npc.hunger
            
            # 水分補給試行
            if npc.thirst > 70:
                npc.seek_water(t)
                
                # 水分補給統計
                if npc.thirst < old_thirst:
                    recovery = old_thirst - npc.thirst
                    if hasattr(npc, 'log') and npc.log:
                        last_action = npc.log[-1] if npc.log else {}
                        if last_action.get('action') == 'drink_cave_water':
                            water_access_stats["cave_water_used"] += recovery
                        else:
                            water_access_stats["regular_water_used"] += recovery
            
            # 食料探索
            if npc.hunger > 60:
                npc.seek_food(t)
            
            # 水不足緊急事態の検出
            if npc.thirst > 150:
                water_access_stats["water_shortage_events"] += 1
        
        # 20tick毎にレポート
        if t % 40 == 0:
            alive_count = len([npc for npc in roster.values() if npc.alive])
            dead_count = len(roster) - alive_count
            print(f"T{t}: 生存 {alive_count}体 | 死亡 {dead_count}体 | 天気: {env.weather.condition}")
            
            if alive_count > 0:
                avg_thirst = sum(npc.thirst for npc in roster.values() if npc.alive) / alive_count
                avg_hunger = sum(npc.hunger for npc in roster.values() if npc.alive) / alive_count
                print(f"  平均渇き: {avg_thirst:.1f} | 平均空腹: {avg_hunger:.1f}")
    
    # 最終統計
    final_survivors = len([npc for npc in roster.values() if npc.alive])
    survival_rate = (final_survivors / len(roster)) * 100
    
    if survival_stats["deaths"]:
        avg_survival_time = sum(d["time"] for d in survival_stats["deaths"]) / len(survival_stats["deaths"])
    else:
        avg_survival_time = ticks  # 全員生存
    
    survival_stats["final_survivors"] = final_survivors
    survival_stats["avg_survival_time"] = avg_survival_time
    
    # 結果レポート
    print(f"\n--- {test_name} 結果 ---")
    print(f"最終生存率: {survival_rate:.1f}% ({final_survivors}/{len(roster)}体)")
    print(f"平均生存時間: {avg_survival_time:.1f}tick")
    
    print(f"死亡原因内訳:")
    print(f"  渇死: {survival_stats['death_causes']['thirst']}体")
    print(f"  餓死: {survival_stats['death_causes']['hunger']}体")
    print(f"  捕食: {survival_stats['death_causes']['predator']}体")
    
    print(f"水利用統計:")
    total_water = water_access_stats["cave_water_used"] + water_access_stats["regular_water_used"]
    if total_water > 0:
        cave_ratio = (water_access_stats["cave_water_used"] / total_water) * 100
        print(f"  洞窟水: {water_access_stats['cave_water_used']:.1f}L ({cave_ratio:.1f}%)")
        print(f"  通常水: {water_access_stats['regular_water_used']:.1f}L")
        print(f"  水不足事件: {water_access_stats['water_shortage_events']}回")
    
    return {
        "survival_rate": survival_rate,
        "avg_survival_time": avg_survival_time,
        "death_causes": survival_stats["death_causes"],
        "water_stats": water_access_stats
    }

def compare_systems(runs_per_test=3, ticks_per_run=200):
    """システム比較テストを実行"""
    print("=== 洞窟雨水システム生存性比較テスト ===\n")
    
    # 従来システム（洞窟水なし）のテスト
    print("🟡 従来システム（無限水源のみ）テスト開始...")
    traditional_results = []
    for i in range(runs_per_test):
        result = run_survival_test(
            enable_cave_water=False, 
            ticks=ticks_per_run, 
            test_name=f"従来システム 実行{i+1}"
        )
        traditional_results.append(result)
    
    # 新システム（洞窟水あり）のテスト  
    print("\n🔵 新システム（洞窟雨水 + 無限水源）テスト開始...")
    new_results = []
    for i in range(runs_per_test):
        result = run_survival_test(
            enable_cave_water=True, 
            ticks=ticks_per_run, 
            test_name=f"新システム 実行{i+1}"
        )
        new_results.append(result)
    
    # 統計比較
    print("\n" + "="*60)
    print("システム比較結果")
    print("="*60)
    
    # 従来システム統計
    trad_avg_survival = sum(r["survival_rate"] for r in traditional_results) / len(traditional_results)
    trad_avg_time = sum(r["avg_survival_time"] for r in traditional_results) / len(traditional_results)
    trad_thirst_deaths = sum(r["death_causes"]["thirst"] for r in traditional_results)
    trad_total_deaths = sum(sum(r["death_causes"].values()) for r in traditional_results)
    
    print(f"🟡 従来システム (平均 {runs_per_test}回実行):")
    print(f"  生存率: {trad_avg_survival:.1f}%")
    print(f"  平均生存時間: {trad_avg_time:.1f}tick")
    print(f"  渇死率: {(trad_thirst_deaths/trad_total_deaths*100) if trad_total_deaths > 0 else 0:.1f}% ({trad_thirst_deaths}体)")
    
    # 新システム統計
    new_avg_survival = sum(r["survival_rate"] for r in new_results) / len(new_results)
    new_avg_time = sum(r["avg_survival_time"] for r in new_results) / len(new_results)
    new_thirst_deaths = sum(r["death_causes"]["thirst"] for r in new_results)
    new_total_deaths = sum(sum(r["death_causes"].values()) for r in new_results)
    
    new_cave_water = sum(r["water_stats"]["cave_water_used"] for r in new_results)
    new_regular_water = sum(r["water_stats"]["regular_water_used"] for r in new_results)
    new_total_water = new_cave_water + new_regular_water
    
    print(f"\n🔵 新システム (平均 {runs_per_test}回実行):")
    print(f"  生存率: {new_avg_survival:.1f}%")
    print(f"  平均生存時間: {new_avg_time:.1f}tick")
    print(f"  渇死率: {(new_thirst_deaths/new_total_deaths*100) if new_total_deaths > 0 else 0:.1f}% ({new_thirst_deaths}体)")
    print(f"  洞窟水依存度: {(new_cave_water/new_total_water*100) if new_total_water > 0 else 0:.1f}%")
    
    # 改善度計算
    survival_improvement = new_avg_survival - trad_avg_survival
    time_improvement = new_avg_time - trad_avg_time
    thirst_death_reduction = (trad_thirst_deaths/trad_total_deaths*100 if trad_total_deaths > 0 else 0) - (new_thirst_deaths/new_total_deaths*100 if new_total_deaths > 0 else 0)
    
    print(f"\n📊 改善効果:")
    print(f"  生存率変化: {survival_improvement:+.1f}%")
    print(f"  生存時間変化: {time_improvement:+.1f}tick")
    print(f"  渇死率変化: {-thirst_death_reduction:+.1f}%")
    
    if survival_improvement > 0:
        print(f"✅ 洞窟雨水システムにより生存性が改善されました！")
    elif survival_improvement < 0:
        print(f"⚠️ 洞窟雨水システムにより生存性が悪化しました。")
    else:
        print(f"➡️ 洞窟雨水システムによる生存性への影響は中立的でした。")
    
    return {
        "traditional": traditional_results,
        "new": new_results,
        "improvement": {
            "survival_rate": survival_improvement,
            "survival_time": time_improvement,
            "thirst_death_reduction": thirst_death_reduction
        }
    }

if __name__ == "__main__":
    print("生存性比較テストを開始...")
    print("⚠️ 水源を極端に制限した厳しい環境でテストします")
    
    results = compare_systems(runs_per_test=2, ticks_per_run=150)  # 短縮版テスト
    
    print("\nテスト完了! 洞窟雨水システムの生存性への影響を確認しました。")