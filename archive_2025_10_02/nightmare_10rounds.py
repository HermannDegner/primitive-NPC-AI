#!/usr/bin/env python3
"""
Enhanced SSD Village Simulation - 10 Round Nightmare Challenge
構造主観力学(SSD)理論完全統合版 - 10回連続ナイトメアチャレンジ
"""

import random
import pandas as pd
from config import *
from environment import Environment, Predator
from npc import NPC
from smart_environment import SmartEnvironment
from ssd_core import PhysicalStructureSystem

def attempt_predator_hunt(leader_npc, predators, roster, current_tick, nearby_allies):
    """捕食者討伐システム"""
    import random
    
    # 最も近い捕食者を選択
    closest_predator = None
    min_distance = float('inf')
    
    for predator in predators:
        if predator.alive:
            distance = ((leader_npc.x - predator.x) ** 2 + (leader_npc.y - predator.y) ** 2) ** 0.5
            if distance < min_distance and distance < 20:  # 討伐可能範囲
                min_distance = distance
                closest_predator = predator
    
    if not closest_predator:
        return None
    
    # グループメンバーを集結
    hunting_group = [leader_npc]
    for ally in roster.values():
        if ally.alive and ally != leader_npc and len(hunting_group) < 6:  # 最大6人グループ
            ally_distance = ((leader_npc.x - ally.x) ** 2 + (leader_npc.y - ally.y) ** 2) ** 0.5
            if ally_distance < 15 and random.random() < (ally.risk_tolerance + 0.2):
                hunting_group.append(ally)
    
    group_size = len(hunting_group)
    
    # 戦闘力計算
    total_combat_power = 0
    for hunter in hunting_group:
        combat_power = hunter.risk_tolerance + hunter.experience.get('hunting', 0)
        
        # 職業ボーナス
        if 'Warrior' in hunter.name:
            combat_power += 0.4
        elif 'Guardian' in hunter.name:
            combat_power += 0.3
        elif 'Tracker' in hunter.name:
            combat_power += 0.2
        elif 'Scholar' in hunter.name:
            combat_power -= 0.1
        
        total_combat_power += combat_power
    
    # グループサイズボーナス
    group_bonus = min(0.5, (group_size - 1) * 0.1)
    total_combat_power += group_bonus
    
    # 強化された捕食者の戦闘力（基本1.2-2.0）
    base_power = 1.2 + (closest_predator.aggression * 0.8)
    experience_bonus = min(0.4, current_tick * 0.002)
    isolation_bonus = 0.3 if group_size < 4 else 0.0
    desperation_bonus = 0.5 if getattr(closest_predator, 'injured', False) else 0.0
    predator_power = base_power + experience_bonus + isolation_bonus + desperation_bonus + random.uniform(-0.1, 0.1)
    
    # 戦闘結果判定
    success_chance = min(0.95, total_combat_power / (predator_power + 1.0))
    hunt_success = random.random() < success_chance
    
    # 結果処理
    result = {
        'group_size': group_size,
        'success': hunt_success,
        'combat_power': total_combat_power,
        'predator_power': predator_power,
        'success_chance': success_chance
    }
    
    if hunt_success:
        closest_predator.alive = False
        result['predator_killed'] = True
        
        # 経験値獲得
        for hunter in hunting_group:
            hunter.experience['hunting'] = hunter.experience.get('hunting', 0) + 0.15
            hunter.experience['predator_awareness'] = hunter.experience.get('predator_awareness', 0) + 0.1
        
        # 死亡時反撃
        casualties = []
        death_throes_damage = random.random() < min(0.6, 0.2 + closest_predator.aggression * 0.4)
        
        if death_throes_damage:
            casualty_count = min(2, max(1, int(group_size * 0.3)))
            for _ in range(casualty_count):
                injured = random.choice(hunting_group)
                if injured.name not in casualties:
                    injured.fatigue = min(100, injured.fatigue + 35)
                    injured.hunger = min(200, injured.hunger + 10)
                    casualties.append(injured.name)
        
        result['casualties'] = casualties
    else:
        # 討伐失敗 - 強化された捕食者の反撃
        casualties = []
        deaths = []
        
        for hunter in hunting_group:
            damage_roll = random.random()
            
            if damage_roll < 0.15:  # 15%の死亡確率
                hunter.alive = False
                deaths.append(hunter.name)
            elif damage_roll < 0.5:  # 35%の重傷確率
                hunter.fatigue = min(100, hunter.fatigue + 40)
                hunter.hunger = min(200, hunter.hunger + 25)
                casualties.append(hunter.name)
            
            if hunter.alive:
                hunter.experience['predator_awareness'] = hunter.experience.get('predator_awareness', 0) + 0.03
        
        if random.random() < 0.3:
            closest_predator.injured = True
        
        result['casualties'] = casualties
        result['deaths'] = deaths
    
    return result

def run_single_nightmare_round(round_num, ticks=200):
    """1回のナイトメアラウンド実行"""
    seed = random.randint(1, 10000)
    random.seed(seed)
    
    print(f"\n{'='*20} ROUND {round_num} {'='*20}")
    print(f"Seed: {seed}")
    
    # 環境設定
    env = Environment(size=DEFAULT_WORLD_SIZE, 
                     n_berry=24, n_hunt=12, n_water=8, n_caves=6,
                     enable_smart_world=True)
    
    # 強化された捕食者を追加
    predator_configs = [
        ((10, 10), 1.2), ((80, 10), 0.9), ((45, 80), 1.0),
        ((20, 80), 1.1), ((70, 70), 0.8)
    ]
    
    for i, (pos, aggression) in enumerate(predator_configs):
        predator = Predator(pos, aggression)
        predator.hunt_radius = 12
        predator.E = 6.0 + (i * 0.5)
        predator.kappa = 1.5
        predator.P = 3.0
        env.predators.append(predator)
    
    smart_env = SmartEnvironment(world_size=DEFAULT_WORLD_SIZE)
    roster = {}
    
    # NPCの作成
    npc_configs = [
        ("SSD_Pioneer_Alpha", PIONEER, (20, 20)),
        ("SSD_Adventurer_Beta", ADVENTURER, (25, 25)), 
        ("SSD_Scholar_Gamma", SCHOLAR, (30, 30)),
        ("SSD_Warrior_Delta", WARRIOR, (35, 35)),
        ("SSD_Healer_Echo", HEALER, (40, 40)),
        ("SSD_Diplomat_Zeta", DIPLOMAT, (45, 45)),
        ("SSD_Guardian_Eta", GUARDIAN, (50, 20)),
        ("SSD_Tracker_Theta", TRACKER, (55, 25)),
        ("SSD_Loner_Iota", LONER, (60, 30)),
        ("SSD_Nomad_Kappa", NOMAD, (65, 35)),
        ("SSD_Forager_Lambda", FORAGER, (20, 50)),
        ("SSD_Leader_Mu", LEADER, (25, 55)),
        ("SSD_Pioneer_Nu", PIONEER, (30, 60)),
        ("SSD_Adventurer_Xi", ADVENTURER, (35, 65)),
        ("SSD_Scholar_Omicron", SCHOLAR, (60, 50)),
        ("SSD_Warrior_Pi", WARRIOR, (65, 55))
    ]
    
    for name, preset, start_pos in npc_configs:
        npc = NPC(name, preset, env, roster, start_pos)
        npc.physical_system = PhysicalStructureSystem(npc)
        roster[name] = npc
    
    # 戦闘記録
    battle_events = []
    final_stats = {'round': round_num, 'seed': seed}
    
    # シミュレーション実行
    for t in range(1, ticks + 1):
        env.ecosystem_step(list(roster.values()), t)
        
        # 捕食者の攻撃
        for predator in env.predators:
            if predator.alive:
                attack_result = predator.hunt_step(list(roster.values()), t)
                if attack_result and attack_result.get('victim'):
                    battle_events.append({
                        't': t, 'type': 'predator_kill', 'victim': attack_result['victim']
                    })
        
        smart_env.analyze_npc_impact(list(roster.values()), t)
        
        # NPCのSSD処理
        for npc in roster.values():
            if not npc.alive:
                continue
                
            env_feedback = smart_env.provide_npc_environmental_feedback(npc, t)
            
            if hasattr(npc, 'physical_system'):
                npc.physical_system.physical_layer.update_environmental_constraints(env_feedback)
                npc.physical_system.upper_layer.receive_environmental_feedback(env_feedback)
                
                # 捕食者脅威計算
                predator_threat = 0.0
                hunting_opportunity = 0.0
                nearby_allies = 0
                
                for predator in env.predators:
                    if predator.alive:
                        distance = ((npc.x - predator.x) ** 2 + (npc.y - predator.y) ** 2) ** 0.5
                        if distance < 20:
                            predator_threat += max(0, (20 - distance) / 20)
                
                if predator_threat > 0:
                    for ally in roster.values():
                        if ally.alive and ally != npc:
                            ally_distance = ((npc.x - ally.x) ** 2 + (npc.y - ally.y) ** 2) ** 0.5
                            if ally_distance < 15:
                                nearby_allies += 1
                    
                    combat_skill = npc.risk_tolerance + (npc.experience.get('hunting', 0) * 0.5)
                    if 'Warrior' in npc.name or 'Guardian' in npc.name:
                        combat_skill += 0.3
                    elif 'Scholar' in npc.name or 'Healer' in npc.name:
                        combat_skill -= 0.2
                    
                    if nearby_allies >= 2:
                        hunting_opportunity = min(1.0, combat_skill + (nearby_allies * 0.2))
                
                external_stimuli = {
                    'exploration_pressure': 0.3 + (npc.curiosity * 0.4),
                    'environmental_pressure': env_feedback.get('environmental_pressure', 0.0),
                    'resource_pressure': env_feedback.get('resource_scarcity', 0.0),
                    'social_pressure': 0.1 + (npc.sociability * 0.2),
                    'survival_pressure': max(0, (npc.hunger + npc.thirst - 100) / 200),
                    'predator_threat': predator_threat,
                    'hunting_opportunity': hunting_opportunity,
                    'group_strength': nearby_allies
                }
                
                result = npc.physical_system.process_structural_dynamics(external_stimuli)
                decision = result['final_decision']
                
                # 戦闘決定強化
                if hunting_opportunity > 0.7 and nearby_allies >= 2:
                    if decision['action'] == 'foraging' and random.random() < 0.3:
                        decision['action'] = 'hunting'
                        decision['combat_target'] = 'predator'
                
                # 討伐実行
                if decision['action'] == 'hunting' and hunting_opportunity > 0.5:
                    hunt_result = attempt_predator_hunt(npc, env.predators, roster, t, nearby_allies)
                    if hunt_result:
                        battle_events.append({
                            't': t, 'type': 'hunt_attempt', 'leader': npc.name,
                            'success': hunt_result['success'],
                            'group_size': hunt_result['group_size'],
                            'casualties': hunt_result.get('casualties', []),
                            'deaths': hunt_result.get('deaths', [])
                        })
    
    # 最終統計
    alive_count = sum(1 for npc in roster.values() if npc.alive)
    dead_npcs = [npc.name for npc in roster.values() if not npc.alive]
    predators_killed = len([e for e in battle_events if e['type'] == 'hunt_attempt' and e['success']])
    npc_deaths_by_predator = len([e for e in battle_events if e['type'] == 'predator_kill'])
    hunt_attempts = len([e for e in battle_events if e['type'] == 'hunt_attempt'])
    successful_hunts = len([e for e in battle_events if e['type'] == 'hunt_attempt' and e['success']])
    
    final_stats.update({
        'survivors': alive_count,
        'survival_rate': alive_count / 16 * 100,
        'deaths': 16 - alive_count,
        'dead_npcs': dead_npcs,
        'predators_killed': predators_killed,
        'npc_deaths_by_predator': npc_deaths_by_predator,
        'hunt_attempts': hunt_attempts,
        'successful_hunts': successful_hunts,
        'hunt_success_rate': successful_hunts / hunt_attempts * 100 if hunt_attempts > 0 else 0
    })
    
    print(f"Round {round_num} Result: {alive_count}/16 survivors ({alive_count/16*100:.1f}%)")
    print(f"  Predators killed: {predators_killed}/5")
    print(f"  Hunt success rate: {final_stats['hunt_success_rate']:.1f}%")
    if dead_npcs:
        print(f"  Casualties: {', '.join(dead_npcs)}")
    
    return final_stats, battle_events

def run_10_round_nightmare_challenge():
    """10回連続ナイトメアチャレンジ実行"""
    print("=" * 60)
    print("🔥💀 10-ROUND NIGHTMARE CHALLENGE 💀🔥")
    print("=" * 60)
    print("Enhanced Predators vs SSD 4-Layer NPCs")
    print("Resources: 80% reduced, 5 Enhanced Predators each round")
    print("=" * 60)
    
    all_results = []
    all_events = []
    
    for round_num in range(1, 11):
        round_stats, round_events = run_single_nightmare_round(round_num)
        all_results.append(round_stats)
        all_events.extend(round_events)
    
    # 総合分析
    print("\n" + "=" * 60)
    print("🏆 10-ROUND CHALLENGE COMPLETE ANALYSIS 🏆")
    print("=" * 60)
    
    df_results = pd.DataFrame(all_results)
    
    # 基本統計
    total_survivors = df_results['survivors'].sum()
    total_possible = 16 * 10
    overall_survival_rate = total_survivors / total_possible * 100
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total Survivors: {total_survivors}/{total_possible} ({overall_survival_rate:.1f}%)")
    print(f"  Average Survivors per Round: {df_results['survivors'].mean():.1f}")
    print(f"  Best Round: {df_results['survivors'].max()}/16 survivors")
    print(f"  Worst Round: {df_results['survivors'].min()}/16 survivors")
    print(f"  Standard Deviation: {df_results['survivors'].std():.2f}")
    
    # 戦闘統計
    total_predators_killed = df_results['predators_killed'].sum()
    total_hunt_attempts = df_results['hunt_attempts'].sum()
    total_successful_hunts = df_results['successful_hunts'].sum()
    overall_hunt_success = total_successful_hunts / total_hunt_attempts * 100 if total_hunt_attempts > 0 else 0
    
    print(f"\n⚔️ BATTLE STATISTICS:")
    print(f"  Total Predators Killed: {total_predators_killed}/50")
    print(f"  Total Hunt Attempts: {total_hunt_attempts}")
    print(f"  Overall Hunt Success Rate: {overall_hunt_success:.1f}%")
    print(f"  Average Predators Killed per Round: {df_results['predators_killed'].mean():.1f}")
    
    # ラウンド別詳細
    print(f"\n📋 ROUND-BY-ROUND BREAKDOWN:")
    for i, result in enumerate(all_results):
        status = "🏆" if result['survivors'] == 16 else "⚔️" if result['survivors'] >= 14 else "💀"
        print(f"  Round {i+1}: {status} {result['survivors']}/16 survivors, "
              f"{result['predators_killed']}/5 predators killed")
    
    # パフォーマンス評価
    perfect_rounds = len(df_results[df_results['survivors'] == 16])
    good_rounds = len(df_results[df_results['survivors'] >= 14])
    
    print(f"\n🎯 PERFORMANCE EVALUATION:")
    print(f"  Perfect Rounds (16/16): {perfect_rounds}/10")
    print(f"  Good Rounds (14-16/16): {good_rounds}/10")
    print(f"  Consistency Rating: {(good_rounds/10)*100:.0f}%")
    
    # 最終判定
    if overall_survival_rate >= 95:
        rating = "LEGENDARY DOMINANCE"
        emoji = "👑"
    elif overall_survival_rate >= 90:
        rating = "OUTSTANDING VICTORY"
        emoji = "🏆"
    elif overall_survival_rate >= 85:
        rating = "STRONG PERFORMANCE"
        emoji = "⚔️"
    elif overall_survival_rate >= 75:
        rating = "DECENT SURVIVAL"
        emoji = "🛡️"
    else:
        rating = "CHALLENGING STRUGGLE"
        emoji = "💀"
    
    print(f"\n{emoji} FINAL VERDICT: {rating} {emoji}")
    print(f"SSD 4-Layer System achieved {overall_survival_rate:.1f}% survival rate!")
    print("=" * 60)
    
    return all_results, all_events

# メイン実行
if __name__ == "__main__":
    try:
        results, events = run_10_round_nightmare_challenge()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()