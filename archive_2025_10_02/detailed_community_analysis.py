#!/usr/bin/env python3
"""
Enhanced Community Analysis - Detailed Community Formation Study
詳細なコミュニティ形成分析 + 職業別傾向調査
"""

import random
import pandas as pd
from config import *
from environment import Environment, Predator
from npc import NPC
from smart_environment import SmartEnvironment
from ssd_core import PhysicalStructureSystem
from social import Territory

def get_role_from_name(name):
    """名前から職業を取得"""
    roles = ['Pioneer', 'Adventurer', 'Scholar', 'Warrior', 'Healer', 
             'Diplomat', 'Guardian', 'Tracker', 'Loner', 'Nomad', 
             'Forager', 'Leader']
    
    for role in roles:
        if role in name:
            return role
    return 'Unknown'

def analyze_community_compatibility(roster):
    """コミュニティの職業構成分析"""
    territories = {}
    
    for npc in roster.values():
        if npc.alive and npc.territory is not None:
            territory_id = id(npc.territory)
            if territory_id not in territories:
                territories[territory_id] = {
                    'members': [],
                    'roles': [],
                    'center': npc.territory.center,
                    'established': getattr(npc.territory, 'established_tick', 0)
                }
            territories[territory_id]['members'].append(npc.name)
            territories[territory_id]['roles'].append(get_role_from_name(npc.name))
    
    print(f"\n🎭 ROLE-BASED COMMUNITY ANALYSIS:")
    
    for i, (territory_id, data) in enumerate(territories.items()):
        members = data['members']
        roles = data['roles']
        
        print(f"\n  Community {i+1} ({len(members)} members):")
        print(f"    Members: {', '.join(members)}")
        print(f"    Roles: {', '.join(roles)}")
        
        # 役割バランス分析
        combat_roles = sum(1 for role in roles if role in ['Warrior', 'Guardian', 'Tracker'])
        support_roles = sum(1 for role in roles if role in ['Healer', 'Scholar', 'Diplomat'])
        exploration_roles = sum(1 for role in roles if role in ['Pioneer', 'Adventurer', 'Nomad'])
        resource_roles = sum(1 for role in roles if role in ['Forager'])
        leadership_roles = sum(1 for role in roles if role in ['Leader'])
        
        balance_score = 0
        if combat_roles > 0:
            balance_score += 2  # 戦闘力は重要
        if support_roles > 0:
            balance_score += 1  # サポート役
        if exploration_roles > 0:
            balance_score += 1  # 探索役
        if resource_roles > 0:
            balance_score += 1  # 資源役
        if leadership_roles > 0:
            balance_score += 2  # リーダーシップ
        
        print(f"    Combat roles: {combat_roles}, Support: {support_roles}, Exploration: {exploration_roles}")
        print(f"    Balance score: {balance_score}/7 ({'Excellent' if balance_score >= 5 else 'Good' if balance_score >= 3 else 'Basic'})")
    
    return territories

def analyze_survival_by_community_status(roster):
    """コミュニティ所属と生存率の関係分析"""
    community_survivors = 0
    independent_survivors = 0
    community_deaths = 0
    independent_deaths = 0
    
    for npc in roster.values():
        if npc.territory is not None:  # コミュニティ所属
            if npc.alive:
                community_survivors += 1
            else:
                community_deaths += 1
        else:  # 独立
            if npc.alive:
                independent_survivors += 1
            else:
                independent_deaths += 1
    
    total_community = community_survivors + community_deaths
    total_independent = independent_survivors + independent_deaths
    
    print(f"\n🎯 SURVIVAL RATE BY COMMUNITY STATUS:")
    
    if total_community > 0:
        community_survival_rate = community_survivors / total_community * 100
        print(f"  Community members: {community_survivors}/{total_community} survived ({community_survival_rate:.1f}%)")
    else:
        print(f"  Community members: No communities formed")
    
    if total_independent > 0:
        independent_survival_rate = independent_survivors / total_independent * 100
        print(f"  Independent NPCs: {independent_survivors}/{total_independent} survived ({independent_survival_rate:.1f}%)")
    else:
        print(f"  Independent NPCs: No independents")
    
    if total_community > 0 and total_independent > 0:
        advantage = community_survival_rate - independent_survival_rate
        print(f"  Community advantage: {advantage:+.1f}% survival rate")

def run_detailed_community_analysis(rounds=3):
    """複数ラウンドでの詳細コミュニティ分析"""
    
    print("=" * 80)
    print("🏘️📊 DETAILED COMMUNITY FORMATION ANALYSIS 📊🏘️")
    print("=" * 80)
    
    all_results = []
    
    for round_num in range(1, rounds + 1):
        print(f"\n{'='*20} ROUND {round_num} {'='*20}")
        
        seed = random.randint(1, 10000)
        random.seed(seed)
        
        # 環境設定
        env = Environment(size=DEFAULT_WORLD_SIZE, 
                         n_berry=24, n_hunt=12, n_water=8, n_caves=6,
                         enable_smart_world=True)
        
        # 強化された捕食者を追加
        predator_configs = [
            ((15, 15), 1.2), ((75, 15), 0.9), ((45, 75), 1.0),
            ((25, 75), 1.1), ((65, 65), 0.8)
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
        
        # シミュレーション実行（150ティック）
        communities_formed_timeline = []
        
        for t in range(1, 151):
            env.ecosystem_step(list(roster.values()), t)
            
            # 捕食者の攻撃
            for predator in env.predators:
                if predator.alive:
                    predator.hunt_step(list(roster.values()), t)
            
            # コミュニティ形成チェック（10ティックごと）
            if t % 10 == 0:
                communities_formed = 0
                
                for npc in roster.values():
                    if not npc.alive or npc.territory:
                        continue
                        
                    # 近くの味方を探す
                    nearby_npcs = []
                    for other in roster.values():
                        if other.alive and other != npc:
                            distance = ((npc.x - other.x) ** 2 + (npc.y - other.y) ** 2) ** 0.5
                            if distance < 20:
                                nearby_npcs.append(other)
                    
                    # コミュニティ形成条件
                    if len(nearby_npcs) >= 2:
                        leadership_score = (npc.sociability + npc.risk_tolerance) / 2
                        if 'Leader' in npc.name or 'Guardian' in npc.name:
                            leadership_score += 0.3
                            
                        if random.random() < leadership_score * 0.3:
                            territory = Territory((npc.x, npc.y), radius=15, owner=npc.name)
                            territory.established_tick = t
                            
                            npc.territory = territory
                            territory.add_member(npc.name)
                            
                            for candidate in nearby_npcs[:3]:
                                if not candidate.territory and random.random() < candidate.sociability:
                                    candidate.territory = territory
                                    territory.add_member(candidate.name)
                            
                            communities_formed += 1
                
                if communities_formed > 0:
                    communities_formed_timeline.append((t, communities_formed))
            
            smart_env.analyze_npc_impact(list(roster.values()), t)
            
            # NPC SSD処理（簡略化）
            for npc in roster.values():
                if not npc.alive:
                    continue
                
                env_feedback = smart_env.provide_npc_environmental_feedback(npc, t)
                
                if hasattr(npc, 'physical_system'):
                    npc.physical_system.physical_layer.update_environmental_constraints(env_feedback)
        
        # ラウンド結果の分析
        alive_count = sum(1 for npc in roster.values() if npc.alive)
        
        territories = analyze_community_compatibility(roster)
        analyze_survival_by_community_status(roster)
        
        result = {
            'round': round_num,
            'seed': seed,
            'survivors': alive_count,
            'total_communities': len(territories),
            'community_timeline': communities_formed_timeline
        }
        
        all_results.append(result)
        
        print(f"\n  Round {round_num} Summary: {alive_count}/16 survivors, {len(territories)} communities")
    
    # 総合分析
    print(f"\n{'='*30} OVERALL ANALYSIS {'='*30}")
    
    avg_survivors = sum(r['survivors'] for r in all_results) / len(all_results)
    avg_communities = sum(r['total_communities'] for r in all_results) / len(all_results)
    
    print(f"\n📈 MULTI-ROUND SUMMARY:")
    print(f"  Average survivors: {avg_survivors:.1f}/16 ({avg_survivors/16*100:.1f}%)")
    print(f"  Average communities formed: {avg_communities:.1f}")
    
    # コミュニティ形成タイミング分析
    all_formation_times = []
    for result in all_results:
        for t, count in result['community_timeline']:
            all_formation_times.extend([t] * count)
    
    if all_formation_times:
        avg_formation_time = sum(all_formation_times) / len(all_formation_times)
        print(f"  Average community formation time: T{avg_formation_time:.0f}")
        print(f"  Total communities formed across all rounds: {len(all_formation_times)}")

if __name__ == "__main__":
    try:
        run_detailed_community_analysis(rounds=3)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()