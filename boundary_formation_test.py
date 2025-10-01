#!/usr/bin/env python3
"""
Boundary Formation Test - 境界形成特化テスト版
強制的に境界形成を促進するテスト版シミュレーション
"""

import random
import pandas as pd
from config import *
from environment import Environment
from npc import NPC
from smart_environment import SmartEnvironment
from ssd_core import PhysicalStructureSystem
from subjective_boundary_system import integrate_subjective_boundary_system, SubjectiveBoundarySystem

def run_boundary_test_simulation(ticks=150):
    """境界形成テスト特化シミュレーション"""
    global boundary_system
    seed = random.randint(1, 1000)
    random.seed(seed)
    
    print("=" * 60)
    print("🏘️ BOUNDARY FORMATION TEST SIMULATION 🏘️")
    print("=" * 60)
    print(f"Test seed: {seed}")
    print("Focus: Aggressive boundary formation and conflict generation")
    
    # 環境設定（境界形成に最適化）
    env = Environment(size=60,  # 小さなワールドで密集促進
                     n_berry=16,    # 適度な資源
                     n_hunt=8,      # 
                     n_water=6,     # 
                     n_caves=4,     # 
                     enable_smart_world=True)
    
    # 弱い捕食者を1匹だけ（脅威は最小限）
    from environment import Predator
    predator = Predator((30, 30), aggression=0.2)
    predator.hunt_radius = 5
    env.predators.append(predator)
    print(f"Added minimal threat predator at center")
    
    smart_env = SmartEnvironment(world_size=60)
    
    # 主観的境界システム初期化
    boundary_system = SubjectiveBoundarySystem()
    experience_handler, boundary_checker = integrate_subjective_boundary_system()
    
    roster = {}
    
    # NPCを密集して配置（8人で境界争いを促進）
    npc_configs = [
        ("Alpha", PIONEER, (25, 25)),    # 中央付近に密集配置
        ("Beta", WARRIOR, (26, 26)), 
        ("Gamma", SCHOLAR, (27, 25)),
        ("Delta", GUARDIAN, (25, 27)),
        ("Echo", HEALER, (35, 35)),      # 少し離れたグループ
        ("Zeta", DIPLOMAT, (36, 36)),
        ("Eta", TRACKER, (37, 35)),
        ("Theta", LEADER, (35, 37))
    ]
    
    for name, preset, start_pos in npc_configs:
        npc = NPC(name, preset, env, roster, start_pos)
        npc.physical_system = PhysicalStructureSystem(npc)
        roster[name] = npc
        print(f"Created {name} at {start_pos}")
    
    # 境界システムにNPCレジストリを設定
    boundary_system.set_npc_roster(roster)
    
    print(f"\nStarting boundary formation test with {len(roster)} NPCs")
    print("=" * 60)
    
    # シミュレーション実行
    ssd_logs = []
    env_logs = []

    for t in range(1, ticks + 1):
        env.ecosystem_step(list(roster.values()), t)
        smart_env.analyze_npc_impact(list(roster.values()), t)
        
        # 捕食者攻撃（最小限）
        predator_attacks = 0
        for predator in env.predators:
            if predator.alive and random.random() < 0.01:  # 1%の確率でのみ攻撃
                attack_result = predator.hunt_step(list(roster.values()), t)
                if attack_result and attack_result.get('victim'):
                    print(f"  💀 T{t}: Predator attack - {attack_result['victim']} killed!")
                    predator_attacks += 1
        
        # 各NPCの処理
        for npc in roster.values():
            if not npc.alive:
                continue
                
            env_feedback = smart_env.provide_npc_environmental_feedback(npc, t)
            
            # SSD処理（簡略化）
            if hasattr(npc, 'physical_system'):
                external_stimuli = {
                    'exploration_pressure': 0.2,
                    'environmental_pressure': 0.1,
                    'resource_pressure': 0.3,
                    'social_pressure': 0.4,  # 社会的圧力を高く
                    'survival_pressure': 0.2
                }
                
                result = npc.physical_system.process_structural_dynamics(external_stimuli)
                decision = result['final_decision']
                
                # 強制的に多様な経験を生成
                experience_types = ['successful_foraging', 'social_cooperation', 'resource_sharing', 
                                  'territory_enter', 'group_hunting', 'friendly_encounter']
                
                for exp_type in experience_types:
                    if random.random() < 0.3:  # 30%の確率で各経験が発生
                        target_location = (npc.x + random.randint(-5, 5), npc.y + random.randint(-5, 5))
                        
                        # 経験処理
                        boundary_system.process_subjective_experience(
                            npc, exp_type, target_location, {'action': exp_type}, t
                        )
                
                # 近くのNPCとの相互作用を強制的に発生
                for other_npc in roster.values():
                    if other_npc != npc and other_npc.alive:
                        distance = ((npc.x - other_npc.x)**2 + (npc.y - other_npc.y)**2) ** 0.5
                        if distance < 10:  # より広い範囲で相互作用
                            
                            # 複数の相互作用を試行
                            interaction_types = ['social_approach', 'resource_use', 'territory_enter']
                            for interaction_type in interaction_types:
                                if random.random() < 0.4:  # 40%の確率で発生
                                    interaction_result = boundary_checker(
                                        npc, other_npc, interaction_type, {'action': interaction_type}, t
                                    )
                                    
                                    if not interaction_result['allowed']:
                                        if interaction_result['response'] == 'aggressive_defense':
                                            print(f"⚔️ T{t}: CONFLICT - {npc.name} vs {other_npc.name} ({interaction_type})")
                                        elif interaction_result['response'] == 'firm_warning':
                                            print(f"⚠️ T{t}: WARNING - {npc.name} warned by {other_npc.name}")
                                    elif interaction_result['response'] == 'cooperative':
                                        print(f"🤝 T{t}: COOPERATION - {npc.name} & {other_npc.name} sharing")
        
        # 詳細進捗表示
        if t % 10 == 0:
            alive_count = len([npc for npc in roster.values() if npc.alive])
            
            # 境界統計
            total_boundaries = 0
            strong_boundaries = 0
            for boundaries in boundary_system.subjective_boundaries.values():
                total_boundaries += len(boundaries['people']) + len(boundaries['places']) + len(boundaries['resources'])
                for strength in boundary_system.boundary_strength.values():
                    strong_boundaries += len([s for s in strength.values() if s > 0.5])
            
            collective_count = len(boundary_system.collective_boundaries)
            violations_recent = sum(len([v for v in violations if t - v['tick'] < 10]) 
                                  for violations in boundary_system.boundary_violations.values())
            
            print(f"T{t}: 👥{alive_count} survivors")
            print(f"     🏘️{total_boundaries} total boundaries ({strong_boundaries} strong)")
            print(f"     🤝{collective_count} collectives, 🚫{violations_recent} recent violations")
            
            # 境界形成の詳細表示
            if total_boundaries > 0:
                print(f"     Boundary details:")
                for npc_name, boundaries in boundary_system.subjective_boundaries.items():
                    if npc_name in roster and roster[npc_name].alive:
                        people_count = len(boundaries['people'])
                        places_count = len(boundaries['places'])
                        if people_count > 0 or places_count > 0:
                            print(f"       {npc_name}: {people_count} people, {places_count} places")
        
        # 環境ログ記録
        if t % 20 == 0:
            env_state = smart_env.get_intelligence_summary()
            env_state['t'] = t
            env_logs.append(env_state)
    
    return roster, ssd_logs, env_logs

# メイン実行
if __name__ == "__main__":
    try:
        print("🧪 BOUNDARY FORMATION TEST STARTING... 🧪")
        
        final_roster, ssd_logs, env_logs = run_boundary_test_simulation(ticks=100)
        
        print("\n" + "=" * 60)
        print("🏘️ BOUNDARY FORMATION TEST RESULTS 🏘️")
        print("=" * 60)
        
        # 境界分析
        boundary_analysis = boundary_system.get_boundary_analysis(final_roster)
        
        print(f"Final boundary statistics:")
        print(f"  Individual boundaries: {len(boundary_analysis['individual_boundaries'])}")
        print(f"  Collective boundaries: {len(boundary_analysis['collective_boundaries'])}")
        print(f"  Total violations: {boundary_analysis['boundary_violations']}")
        
        # 詳細境界情報
        for npc_name, boundary_info in boundary_analysis['individual_boundaries'].items():
            if boundary_info['boundary_clarity'] > 0.0:
                print(f"\n{npc_name} boundaries:")
                print(f"  Inner people: {boundary_info['inner_people']}")
                print(f"  Inner places: {boundary_info['inner_places']}")
                print(f"  Inner resources: {boundary_info['inner_resources']}")
                print(f"  Clarity: {boundary_info['boundary_clarity']:.3f}")
        
        if boundary_analysis['collective_boundaries']:
            print(f"\nCollective boundaries:")
            for collective_id, info in boundary_analysis['collective_boundaries'].items():
                print(f"  {collective_id}: {len(info['members'])} members, cohesion: {info['cohesion']:.3f}")
        
        print("\n🧪 TEST COMPLETE! 🧪")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()