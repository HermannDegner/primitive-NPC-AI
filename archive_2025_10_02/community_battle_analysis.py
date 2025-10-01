#!/usr/bin/env python3
"""
Enhanced SSD Village Simulation - Community Formation Analysis
構造主観力学(SSD)理論 + コミュニティ形成システム分析
"""

import random
import pandas as pd
from config import *
from environment import Environment, Predator
from npc import NPC
from smart_environment import SmartEnvironment
from ssd_core import PhysicalStructureSystem
from social import Territory

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
    
    # 強化された捕食者の戦闘力
    base_power = 1.2 + (closest_predator.aggression * 0.8)
    experience_bonus = min(0.4, current_tick * 0.002)
    isolation_bonus = 0.3 if group_size < 4 else 0.0
    desperation_bonus = 0.5 if getattr(closest_predator, 'injured', False) else 0.0
    predator_power = base_power + experience_bonus + isolation_bonus + desperation_bonus + random.uniform(-0.1, 0.1)
    
    # 戦闘結果判定
    success_chance = min(0.95, total_combat_power / (predator_power + 1.0))
    hunt_success = random.random() < success_chance
    
    result = {
        'group_size': group_size,
        'success': hunt_success,
        'combat_power': total_combat_power,
        'predator_power': predator_power,
        'success_chance': success_chance,
        'group_members': [h.name for h in hunting_group]
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

def establish_battle_communities(roster, current_tick):
    """戦闘状況でのコミュニティ形成"""
    communities_formed = 0
    
    for npc in roster.values():
        if not npc.alive or npc.territory:
            continue
            
        # 近くの味方を探す
        nearby_npcs = []
        for other in roster.values():
            if other.alive and other != npc:
                distance = ((npc.x - other.x) ** 2 + (npc.y - other.y) ** 2) ** 0.5
                if distance < 20:  # コミュニティ形成範囲
                    nearby_npcs.append(other)
        
        # コミュニティ形成条件（3人以上の集団）
        if len(nearby_npcs) >= 2:
            # リーダー適性チェック
            leadership_score = (npc.sociability + npc.risk_tolerance) / 2
            if 'Leader' in npc.name or 'Guardian' in npc.name:
                leadership_score += 0.3
                
            # コミュニティ形成確率
            if random.random() < leadership_score * 0.3:  # 30%基準確率
                # 新しいコミュニティを設立
                territory = Territory((npc.x, npc.y), radius=15, owner=npc.name)
                territory.established_tick = current_tick
                
                npc.territory = territory
                territory.add_member(npc.name)
                
                # 近くのNPCを勧誘
                for candidate in nearby_npcs[:3]:  # 最大3人まで勧誘
                    if not candidate.territory and random.random() < candidate.sociability:
                        candidate.territory = territory
                        territory.add_member(candidate.name)
                
                communities_formed += 1
                
    return communities_formed

def run_community_analysis_simulation(ticks=200):
    """コミュニティ形成分析付きシミュレーション"""
    seed = random.randint(1, 10000)
    random.seed(seed)
    
    print(f"Community Formation Analysis - Seed: {seed}")
    print("Enhanced Predators + Community Formation System")
    
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
    
    # 分析用データ
    community_data = []
    battle_events = []
    
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
        
        # コミュニティ形成チェック
        if t % 10 == 0:  # 10ティックごとにコミュニティ形成をチェック
            communities_formed = establish_battle_communities(roster, t)
            if communities_formed > 0:
                print(f"  T{t}: {communities_formed} new communities formed")
        
        smart_env.analyze_npc_impact(list(roster.values()), t)
        
        # NPCのSSD処理（変更なし）
        for npc in roster.values():
            if not npc.alive:
                continue
                
            env_feedback = smart_env.provide_npc_environmental_feedback(npc, t)
            
            if hasattr(npc, 'physical_system'):
                npc.physical_system.physical_layer.update_environmental_constraints(env_feedback)
                npc.physical_system.upper_layer.receive_environmental_feedback(env_feedback)
                
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
                
                if hunting_opportunity > 0.7 and nearby_allies >= 2:
                    if decision['action'] == 'foraging' and random.random() < 0.3:
                        decision['action'] = 'hunting'
                        decision['combat_target'] = 'predator'
                
                if decision['action'] == 'hunting' and hunting_opportunity > 0.5:
                    hunt_result = attempt_predator_hunt(npc, env.predators, roster, t, nearby_allies)
                    if hunt_result:
                        battle_events.append({
                            't': t, 'type': 'hunt_attempt', 'leader': npc.name,
                            'success': hunt_result['success'],
                            'group_size': hunt_result['group_size'],
                            'group_members': hunt_result['group_members'],
                            'casualties': hunt_result.get('casualties', []),
                            'deaths': hunt_result.get('deaths', [])
                        })
        
        # コミュニティ状況記録（25ティックごと）
        if t % 25 == 0:
            territories = {}
            for npc in roster.values():
                if npc.alive and npc.territory is not None:
                    territory_id = id(npc.territory)
                    if territory_id not in territories:
                        territories[territory_id] = {
                            'members': [],
                            'center': npc.territory.center,
                            'established': npc.territory.established_tick
                        }
                    territories[territory_id]['members'].append(npc.name)
            
            community_data.append({
                't': t,
                'num_communities': len(territories),
                'total_members': sum(len(data['members']) for data in territories.values()),
                'communities': territories
            })
    
    # 最終分析
    analyze_community_formation(roster, community_data, battle_events)
    
    return roster, community_data, battle_events

def analyze_community_formation(roster, community_data, battle_events):
    """コミュニティ形成の詳細分析"""
    print("\n" + "=" * 60)
    print("🏘️ COMMUNITY FORMATION ANALYSIS 🏘️")
    print("=" * 60)
    
    # 最終コミュニティ状況
    territories = {}
    for npc in roster.values():
        if npc.alive and npc.territory is not None:
            territory_id = id(npc.territory)
            if territory_id not in territories:
                territories[territory_id] = []
            territories[territory_id].append(npc.name)
    
    alive_count = sum(1 for npc in roster.values() if npc.alive)
    
    print(f"\n📊 FINAL COMMUNITY STATUS:")
    print(f"  Survivors: {alive_count}/16")
    print(f"  Communities formed: {len(territories)}")
    
    if territories:
        total_community_members = sum(len(members) for members in territories.values())
        community_rate = total_community_members / alive_count * 100
        
        print(f"  NPCs in communities: {total_community_members}/{alive_count} ({community_rate:.1f}%)")
        
        max_community_size = max(len(members) for members in territories.values())
        avg_community_size = total_community_members / len(territories)
        
        print(f"  Largest community: {max_community_size} members")
        print(f"  Average community size: {avg_community_size:.1f} members")
        
        print(f"\n🏘️ COMMUNITY DETAILS:")
        for i, (territory_id, members) in enumerate(territories.items()):
            print(f"  Community {i+1}: {len(members)} members")
            print(f"    Members: {', '.join(members)}")
    else:
        print(f"  No communities formed - all NPCs remain independent")
    
    # コミュニティと戦闘効率の関係分析
    hunt_events = [e for e in battle_events if e['type'] == 'hunt_attempt']
    if hunt_events:
        print(f"\n⚔️ COMMUNITY vs BATTLE EFFICIENCY:")
        
        community_hunts = 0
        individual_hunts = 0
        
        for hunt in hunt_events:
            # グループメンバーが同じコミュニティに属しているかチェック
            # (簡易版：グループサイズで判定)
            if hunt['group_size'] >= 3:
                community_hunts += 1
            else:
                individual_hunts += 1
        
        total_hunts = len(hunt_events)
        successful_hunts = len([h for h in hunt_events if h['success']])
        
        print(f"  Total hunt attempts: {total_hunts}")
        print(f"  Group hunts (3+): {community_hunts}")
        print(f"  Small hunts (1-2): {individual_hunts}")
        print(f"  Overall success rate: {successful_hunts/total_hunts*100:.1f}%")
    
    # 時系列でのコミュニティ発達
    if community_data:
        print(f"\n📈 COMMUNITY DEVELOPMENT OVER TIME:")
        for data in community_data[::2]:  # 2つおきに表示
            print(f"  T{data['t']}: {data['num_communities']} communities, {data['total_members']} members")
    
    print("=" * 60)

# メイン実行
if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🏘️⚔️ COMMUNITY FORMATION + BATTLE ANALYSIS ⚔️🏘️")
        print("=" * 60)
        
        roster, community_data, battle_events = run_community_analysis_simulation(ticks=200)
        
        print("\nSimulation complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()