"""
SSD Village Simulation - Main Simulation Runner
構造主観力学(SSD)理論に基づく原始村落シミュレーション - メインシミュレーション
"""

import random
import pandas as pd

from config import *
from environment import Environment
from npc import NPC


def run_simulation(ticks=500):
    """シミュレーション実行"""
    seed = random.randint(1, 1000)
    random.seed(seed)
    print(f"Using random seed: {seed}")
    
    # 環境設定
    env = Environment(size=DEFAULT_WORLD_SIZE, 
                     n_berry=DEFAULT_BERRY_COUNT, 
                     n_hunt=DEFAULT_HUNTING_GROUND_COUNT, 
                     n_water=DEFAULT_WATER_SOURCE_COUNT, 
                     n_caves=DEFAULT_CAVE_COUNT)
    roster = {}
    
    # NPCの作成（16人）
    npc_configs = [
        ("Pioneer_Alpha", PIONEER, (20, 20)),
        ("Adventurer_Beta", ADVENTURER, (21, 19)), 
        ("Tracker_Gamma", TRACKER, (19, 21)),
        ("Scholar_Delta", SCHOLAR, (18, 18)),
        ("Warrior_Echo", WARRIOR, (60, 20)),
        ("Guardian_Foxtrot", GUARDIAN, (61, 19)),
        ("Loner_Golf", LONER, (59, 21)),
        ("Nomad_Hotel", NOMAD, (58, 18)),
        ("Healer_India", HEALER, (20, 60)),
        ("Diplomat_Juliet", DIPLOMAT, (21, 59)),
        ("Forager_Kilo", FORAGER, (19, 61)),
        ("Leader_Lima", LEADER, (18, 58)),
        ("Guardian_Mike", GUARDIAN, (60, 60)),
        ("Tracker_November", TRACKER, (61, 59)),
        ("Adventurer_Oscar", ADVENTURER, (59, 61)),
        ("Pioneer_Papa", PIONEER, (58, 58))
    ]
    
    for name, preset, start_pos in npc_configs:
        npc = NPC(name, preset, env, roster, start_pos)
        roster[name] = npc
    
    # シミュレーション実行
    logs = []
    weather_logs = []
    
    for t in range(1, ticks + 1):
        env.step()
        
        # 捕食者の攻撃処理
        for predator in env.predators:
            if predator.alive:
                attack_result = predator.hunt_step(list(roster.values()))
                if attack_result:
                    print(f"T{t}: Predator attack! {attack_result['victim']} killed (defenders: {attack_result['defenders']})")
        
        # NPC行動
        for npc in roster.values():
            npc.step(t)
            logs.extend(npc.log[-10:])  # 最新10個のログのみ保持
        
        # 天気ログ
        weather_logs.append({
            "t": t,
            "condition": env.weather.condition,
            "temperature": env.weather.temperature,
            "time_of_day": env.day_night.time_of_day,
            "predators": len([p for p in env.predators if p.alive])
        })
        
        # 進捗表示
        if t % 100 == 0:
            survivors = sum(1 for npc in roster.values() if npc.alive)
            exploration_mode_count = sum(1 for npc in roster.values() if npc.alive and npc.exploration_mode)
            territories = len(set(id(npc.territory) for npc in roster.values() 
                                if npc.alive and npc.territory is not None))
            
            print(f"T{t}: Survivors={survivors}/16, Exploring={exploration_mode_count}, "
                  f"Territories={territories}, Predators={len([p for p in env.predators if p.alive])}")
    
    return list(roster.values()), pd.DataFrame(logs), pd.DataFrame(weather_logs)


def analyze_results(final_npcs, df_logs, df_weather):
    """結果分析"""
    survivors = [npc for npc in final_npcs if npc.alive]
    print(f"\n=== SSD Village Simulation Results ===")
    print(f"Survivors: {len(survivors)}/16")
    
    # SSD理論関連分析
    if not df_logs.empty:
        mode_changes = df_logs[df_logs['action'].isin(['exploration_mode_leap', 'exploration_mode_reversion'])]
        print(f"SSD Mode Changes:")
        print(f"  - Exploration leaps: {len(mode_changes[mode_changes['action'] == 'exploration_mode_leap'])}")
        print(f"  - Mode reversions: {len(mode_changes[mode_changes['action'] == 'exploration_mode_reversion'])}")
        
        # コミュニティ形成分析
        territories = {}
        for npc in survivors:
            if npc.territory is not None:
                territory_id = id(npc.territory)
                if territory_id not in territories:
                    territories[territory_id] = []
                territories[territory_id].append(npc.name)
        
        if territories:
            print(f"\nCommunity Formation:")
            for i, (territory_id, members) in enumerate(territories.items()):
                print(f"  - Community {i+1}: {len(members)} members ({', '.join(members)})")
            
            max_community_size = max(len(members) for members in territories.values())
            avg_community_size = sum(len(members) for members in territories.values()) / len(territories)
            print(f"  - Maximum community size: {max_community_size}")
            print(f"  - Average community size: {avg_community_size:.1f}")
        
        # 捕食者分析
        predator_events = df_logs[df_logs['action'].isin(['group_protection'])]
        print(f"\nPredator Defense:")
        print(f"  - Group protection events: {len(predator_events)}")
    
    print(f"\n=== Simulation Complete ===")


if __name__ == "__main__":
    final_npcs, df_logs, df_weather = run_simulation(ticks=500)
    analyze_results(final_npcs, df_logs, df_weather)