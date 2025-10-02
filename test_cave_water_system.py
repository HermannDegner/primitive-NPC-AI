#!/usr/bin/env python3
"""
洞窟雨水システムの総合テスト
- 雨天時の洞窟水収集
- 晴天時の蒸発システム
- NPCの洞窟水利用行動
- 有限な水資源の競合
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from environment import Environment
from npc import NPC
import random
import time

def create_test_environment():
    """テスト用の環境を作成"""
    env = Environment(size=100, n_caves=4)
    
    # 水源を減らして洞窟水の重要性を高める
    env.water_sources = {
        "water_distant": (25, 25),  # 1つの遠い水源のみ
    }
    
    # 洞窟位置を上書き（既存の洞窟IDを使用）
    cave_positions = [(50, 50), (60, 40), (30, 70), (80, 20)]
    for i, pos in enumerate(cave_positions):
        if f"cave_{i}" in env.caves:
            env.caves[f"cave_{i}"] = pos
    
    # 洞窟雨水システムを初期化（environment.pyで自動的に行われる）
    
    return env

def create_test_npcs(env, num_npcs=4):
    """テスト用のNPCを作成"""
    roster = {}
    
    # 洞窟周辺にNPCを配置
    positions = [(48, 52), (62, 38), (32, 68), (78, 22)]
    
    for i in range(num_npcs):
        name = f"NPC_{chr(65+i)}"
        preset = {
            "exploration_range": 20,
            "risk_tolerance": 0.5 + random.random() * 0.3,
            "cooperation": 0.7 + random.random() * 0.3,
            "empathy": 0.6 + random.random() * 0.3
        }
        
        npc = NPC(name, preset, env, roster, positions[i])
        npc.thirst = 80 + random.randint(0, 40)  # 渇きレベルを設定
        roster[name] = npc
    
    # 各NPCにrosterを設定
    for npc in roster.values():
        npc.roster = roster
    
    return roster

def simulate_cave_water_system(ticks=100):
    """洞窟雨水システムのシミュレーション"""
    print("=== 洞窟雨水システム総合テスト ===\n")
    
    env = create_test_environment()
    roster = create_test_npcs(env)
    
    # 統計情報
    weather_stats = {"clear": 0, "rain": 0, "storm": 0}
    cave_water_history = {cave_id: [] for cave_id in env.caves.keys()}
    npc_water_consumption = {name: {"regular": 0, "cave": 0} for name in roster.keys()}
    
    print("初期状態:")
    print(f"天気: {env.weather.condition}")
    for cave_id in env.caves.keys():
        info = env.get_cave_water_info(cave_id)
        if info:
            print(f"  {cave_id}: {info['water_amount']:.1f}L (最大: {info['max_capacity']:.1f}L)")
    print()
    
    for t in range(1, ticks + 1):
        # 環境更新
        env.ecosystem_step(list(roster.values()), t)
        weather_stats[env.weather.condition] += 1
        
        # 洞窟水情報を記録
        for cave_id in env.caves.keys():
            info = env.get_cave_water_info(cave_id)
            if info:
                cave_water_history[cave_id].append(info['water_amount'])
        
        # NPC行動
        for npc in roster.values():
            if npc.alive and npc.thirst > 50:
                old_thirst = npc.thirst
                npc.seek_water(t)
                
                # 水分補給がされた場合の記録
                if npc.thirst < old_thirst:
                    recovery = old_thirst - npc.thirst
                    # ログから洞窟水使用を判定
                    if hasattr(npc, 'log') and npc.log:
                        last_action = npc.log[-1] if npc.log else {}
                        if last_action.get('action') == 'drink_cave_water':
                            npc_water_consumption[npc.name]["cave"] += recovery
                        else:
                            npc_water_consumption[npc.name]["regular"] += recovery
        
        # 10tick毎に詳細レポート
        if t % 10 == 0:
            print(f"\n--- T{t} レポート ---")
            print(f"天気: {env.weather.condition} | 温度: {env.weather.temperature:.1f}°C")
            
            print("洞窟水状況:")
            for cave_id in env.caves.keys():
                info = env.get_cave_water_info(cave_id)
                if info:
                    pos = env.caves[cave_id]
                    # 洞窟周辺のNPCをチェック
                    nearby_npcs = []
                    for npc in roster.values():
                        if npc.alive:
                            distance = ((npc.x - pos[0])**2 + (npc.y - pos[1])**2)**0.5
                            if distance <= 5:
                                nearby_npcs.append(f"{npc.name}(渇き:{npc.thirst:.0f})")
                    
                    nearby_str = f" [近く: {', '.join(nearby_npcs)}]" if nearby_npcs else ""
                    print(f"  {cave_id}: {info['water_amount']:.1f}L / {info['max_capacity']:.1f}L{nearby_str}")
            
            print("NPC状況:")
            for npc in roster.values():
                if npc.alive:
                    regular_water = npc_water_consumption[npc.name]["regular"]
                    cave_water = npc_water_consumption[npc.name]["cave"]
                    print(f"  {npc.name}: 渇き {npc.thirst:.1f} | 通常水源 {regular_water:.1f}L | 洞窟水 {cave_water:.1f}L")
    
    print(f"\n=== 最終統計 (T{ticks}) ===")
    print(f"天気統計: 晴れ {weather_stats['clear']} | 雨 {weather_stats['rain']} | 嵐 {weather_stats['storm']}")
    
    print("\n洞窟水利用統計:")
    total_cave_water = sum(data["cave"] for data in npc_water_consumption.values())
    total_regular_water = sum(data["regular"] for data in npc_water_consumption.values())
    
    for name, data in npc_water_consumption.items():
        cave_ratio = data["cave"] / (data["cave"] + data["regular"]) * 100 if data["cave"] + data["regular"] > 0 else 0
        print(f"  {name}: 洞窟水 {data['cave']:.1f}L | 通常水 {data['regular']:.1f}L | 洞窟水比率 {cave_ratio:.1f}%")
    
    print(f"\n全体比率: 洞窟水 {total_cave_water:.1f}L ({total_cave_water/(total_cave_water+total_regular_water)*100:.1f}%) | 通常水源 {total_regular_water:.1f}L")
    
    print("\n洞窟水変動:")
    for cave_id, history in cave_water_history.items():
        if history:
            max_water = max(history)
            min_water = min(history)
            final_water = history[-1]
            print(f"  {cave_id}: 最大 {max_water:.1f}L | 最小 {min_water:.1f}L | 最終 {final_water:.1f}L")
    
    # 雨水収集効果の検証
    print("\n雨水収集効果の検証:")
    rain_storm_ticks = weather_stats['rain'] + weather_stats['storm']
    if rain_storm_ticks > 0:
        print(f"雨/嵐の発生: {rain_storm_ticks}回")
        print("→ 洞窟への水の蓄積が観測されることを期待")
    
    clear_ticks = weather_stats['clear']
    if clear_ticks > 0:
        print(f"晴天の発生: {clear_ticks}回")
        print("→ 洞窟からの水の蒸発が観測されることを期待")

if __name__ == "__main__":
    print("洞窟雨水システムテストを開始...")
    simulate_cave_water_system(50)
    print("\nテスト完了!")