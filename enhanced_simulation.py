#!/usr/bin/env python3
"""
Enhanced Simulation Module - 統合シミュレーション実行エンジン
SSD + 境界 + スマート環境 + 季節システムの完全統合実行
"""

import random
import pandas as pd
from config import *
from environment import Environment, Predator
from npc import NPC
from smart_environment import SmartEnvironment
from ssd_core import PhysicalStructureSystem
from subjective_boundary_system import integrate_subjective_boundary_system, SubjectiveBoundarySystem
from seasonal_system import SeasonalSystem

# グローバル境界システム
boundary_system = None

def run_enhanced_ssd_simulation(ticks=400):
    """SSD完全統合シミュレーション実行 + 季節システム"""
    
    # 季節システム初期化
    seasonal_system = SeasonalSystem(season_length=100)  # 1季節100ティック
    
    # シミュレーション統計変数
    total_predator_hunting_attempts = 0
    total_predator_kills = 0
    global boundary_system
    
    # ランダムシード設定
    seed = random.randint(1, 1000)
    random.seed(seed)
    
    # シミュレーション開始メッセージ
    print(f"Enhanced SSD Simulation with SEASONAL SYSTEM - Random seed: {seed}")
    print("🌸🌞🍂❄️ FOUR SEASONS CARNIVORE SURVIVAL CHALLENGE 🌸🌞🍂❄️")
    print("   Base: Berries: 0 (SEASONAL VARIATION), Water: 8, Hunt: 18, Caves: 6")
    print("   SEASONAL EFFECTS: Resource fluctuation, behavior changes, social dynamics")
    
    # 環境設定（スマート環境統合）- 完全肉食社会 + 捕食者脅威
    env = Environment(size=DEFAULT_WORLD_SIZE, 
                     n_berry=0,     # 完全撤廃 - 肉食のみの世界
                     n_hunt=18,     # デフォルト60 → 18に（狩場を増加）  
                     n_water=8,     # デフォルト40 → 8に80%削減（16人に対して0.5個/人）
                     n_caves=6,     # デフォルト25 → 6に75%削減
                     enable_smart_world=True)
    
    # 捕食者追加
    predator_positions = [(15, 85), (85, 15)]
    for i, pos in enumerate(predator_positions):
        predator = Predator(pos, aggression=0.4)
        predator.hunt_radius = 8
        env.predators.append(predator)
        print(f"Added Balanced Predator_{i+1} at position {predator.pos()}")
    
    # スマート環境とバウンダリシステム初期化
    smart_env = SmartEnvironment(world_size=DEFAULT_WORLD_SIZE)
    boundary_system = SubjectiveBoundarySystem()
    experience_handler, boundary_checker = integrate_subjective_boundary_system()
    
    # NPCロスター作成
    roster = create_npc_roster(env)
    boundary_system.set_npc_roster(roster)
    
    print("=" * 60)
    
    # メインシミュレーションループ
    logs, ssd_decision_logs, environment_intelligence_logs, seasonal_logs = run_simulation_loop(
        seasonal_system, env, smart_env, roster, experience_handler, boundary_checker, ticks
    )
    
    return roster, ssd_decision_logs, environment_intelligence_logs, seasonal_logs

def create_npc_roster(env):
    """NPCロスターの作成"""
    roster = {}
    
    # NPCの作成（SSD物理構造システム統合）- 16人バージョン
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
        # SSD物理構造システムを追加
        npc.physical_system = PhysicalStructureSystem(npc)
        # 季節関連属性初期化
        npc.seasonal_curiosity_mod = 0.0
        npc.seasonal_social_mod = 0.0
        roster[name] = npc
        print(f"Created {name} with SSD 4-Layer System + Seasonal Adaptation")
    
    print(f"\\nTotal NPCs with SSD Integration: {len(roster)}")
    return roster

def run_simulation_loop(seasonal_system, env, smart_env, roster, experience_handler, boundary_checker, ticks):
    """メインシミュレーションループ"""
    
    # ログ初期化
    logs = []
    ssd_decision_logs = []
    environment_intelligence_logs = []
    seasonal_logs = []
    
    for t in range(1, ticks + 1):
        # 季節効果の適用
        current_season_name = seasonal_system.get_season_name(t)
        seasonal_modifiers = seasonal_system.apply_seasonal_effects(env, list(roster.values()), t)
        
        # 季節変化の通知
        if t % seasonal_system.season_length == 1:
            print(f"\\n🌍 T{t}: SEASON CHANGE TO {current_season_name}!")
            print(f"   📊 Effects: Berry×{seasonal_modifiers.get('berry_abundance', 1.0):.1f}, "
                  f"Prey×{seasonal_modifiers.get('prey_activity', 1.0):.1f}, "
                  f"Predator×{seasonal_modifiers.get('predator_activity', 1.0):.1f}")
        
        # エコシステム更新
        env.ecosystem_step(list(roster.values()), t)
        
        # 捕食者狩り処理
        process_predator_hunting(env, roster, seasonal_modifiers, current_season_name, t)
        
        # 捕食者攻撃処理
        predator_attacks = process_predator_attacks(env, roster, current_season_name, t)
        
        # スマート環境分析
        smart_env.analyze_npc_impact(list(roster.values()), t)
        
        # NPC個別処理
        process_npc_decisions(roster, env, smart_env, seasonal_modifiers, 
                            experience_handler, boundary_checker, 
                            ssd_decision_logs, seasonal_logs, current_season_name, t)
        
        # 進捗表示
        display_progress(roster, seasonal_modifiers, current_season_name, predator_attacks, t)
        
        # 環境情報記録
        if t % 25 == 0:
            env_state = smart_env.get_intelligence_summary()
            env_state['t'] = t
            environment_intelligence_logs.append(env_state)
    
    return logs, ssd_decision_logs, environment_intelligence_logs, seasonal_logs

def process_predator_hunting(env, roster, seasonal_modifiers, current_season_name, t):
    """捕食者狩り処理"""
    hunting_chance = 0.02 * seasonal_modifiers.get('predator_activity', 1.0)
    
    for npc in roster.values():
        if npc.alive and random.random() < hunting_chance:
            hunt_result = npc.attempt_predator_hunting(env.predators, list(roster.values()), t)
            if hunt_result:
                if hunt_result.get('predator_killed'):
                    print(f"  🏹 T{t} ({current_season_name}): PREDATOR HUNTING SUCCESS - Group of {hunt_result['group_size']} killed a predator!")
                    # 境界システムに成功体験を記録
                    boundary_system.process_subjective_experience(
                        npc, 'predator_defense_success', 'group_victory', 
                        {'group_size': hunt_result['group_size']}, t
                    )
                elif hunt_result.get('casualties'):
                    print(f"  💀 T{t} ({current_season_name}): PREDATOR HUNTING FAILED - Casualties: {', '.join(hunt_result['casualties'])}")

def process_predator_attacks(env, roster, current_season_name, t):
    """捕食者攻撃処理"""
    predator_attacks = 0
    for predator in env.predators:
        if predator.alive:
            attack_result = predator.hunt_step(list(roster.values()), t)
            if attack_result:
                predator_attacks += 1
                if attack_result.get('victim'):
                    print(f"  💀 T{t} ({current_season_name}): PREDATOR KILL - {attack_result['victim']} killed!")
                    # 境界システムに脅威体験を記録
                    for npc in roster.values():
                        if npc.alive and npc.distance_to((predator.x, predator.y)) < 15:
                            boundary_system.process_subjective_experience(
                                npc, 'predator_threat_witness', 'external_danger', 
                                {'victim': attack_result['victim']}, t
                            )
    return predator_attacks

def process_npc_decisions(roster, env, smart_env, seasonal_modifiers, 
                        experience_handler, boundary_checker, 
                        ssd_decision_logs, seasonal_logs, current_season_name, t):
    """NPC個別決定処理"""
    
    for npc in roster.values():
        if not npc.alive:
            continue
        
        env_feedback = smart_env.provide_npc_environmental_feedback(npc, t)
        
        if hasattr(npc, 'physical_system'):
            # 捕食者脅威計算
            predator_threat = 0.0
            for predator in env.predators:
                if predator.alive:
                    distance = ((npc.x - predator.x) ** 2 + (npc.y - predator.y) ** 2) ** 0.5
                    if distance < 20:
                        predator_threat += max(0, (20 - distance) / 20)
            
            # 季節圧力の追加
            seasonal_pressure = seasonal_modifiers.get('survival_pressure', 0.0)
            
            # 外部刺激作成（季節統合版）
            exploration_base = 0.3 + (npc.curiosity * 0.4)
            exploration_seasonal = exploration_base + npc.seasonal_curiosity_mod
            
            external_stimuli = {
                'exploration_pressure': max(0, exploration_seasonal),
                'environmental_pressure': env_feedback.get('environmental_pressure', 0.0) + seasonal_pressure,
                'resource_pressure': env_feedback.get('resource_scarcity', 0.0) * seasonal_modifiers.get('berry_abundance', 1.0),
                'social_pressure': 0.1 + (npc.sociability * 0.2) + npc.seasonal_social_mod,
                'survival_pressure': max(0, (npc.hunger + npc.thirst - 100) / 200) + seasonal_pressure,
                'predator_threat': predator_threat,
                'seasonal_stress': seasonal_modifiers.get('temperature_stress', 0.0)
            }
            
            # SSD構造力学処理
            result = npc.physical_system.process_structural_dynamics(external_stimuli)
            decision = result['final_decision']
            
            # ログ記録
            log_npc_decision(npc, decision, result, env_feedback, seasonal_modifiers, 
                           current_season_name, ssd_decision_logs, seasonal_logs, t)
            
            # 境界システム処理
            process_boundary_interactions(npc, decision, roster, experience_handler, boundary_checker, t)

def log_npc_decision(npc, decision, result, env_feedback, seasonal_modifiers, 
                   current_season_name, ssd_decision_logs, seasonal_logs, t):
    """NPCの決定をログに記録"""
    
    # SSD決定ログ
    ssd_decision_logs.append({
        't': t,
        'npc': npc.name,
        'decision_action': decision['action'],
        'decision_type': decision['type'],
        'environmental_pressure': env_feedback.get('environmental_pressure', 0),
        'resource_scarcity': env_feedback.get('resource_scarcity', 0),
        'meaning_pressure': result.get('meaning_pressure', 0),
        'leap_probability': result.get('leap_probability', 0),
        'curiosity': npc.curiosity,
        'exploration_mode': npc.exploration_mode
    })
    
    # 季節ログ
    seasonal_logs.append({
        't': t,
        'season': current_season_name,
        'npc': npc.name,
        'seasonal_pressure': seasonal_modifiers.get('survival_pressure', 0.0),
        'temperature_stress': seasonal_modifiers.get('temperature_stress', 0.0),
        'resource_modifier': seasonal_modifiers.get('berry_abundance', 1.0),
        'exploration_mod': npc.seasonal_curiosity_mod,
        'social_mod': npc.seasonal_social_mod
    })

def process_boundary_interactions(npc, decision, roster, experience_handler, boundary_checker, t):
    """境界システムの相互作用処理"""
    
    # 決定をNPC行動に反映
    if decision['type'] == 'leap':
        npc.exploration_mode = True
    
    # 主観的境界システム: 経験処理
    action_context = {
        'action': decision.get('action', 'foraging'),
        'target_location': (npc.x, npc.y),
        'decision_type': decision['type']
    }
    
    # 成功/失敗をランダムに決定（より詳細な実装が可能）
    success = random.random() < 0.7
    experience_result = {'success': success}
    experience_handler(npc, experience_result, action_context, t)
    
    # 他NPCとの相互作用チェック
    for other_npc in roster.values():
        if other_npc.alive and other_npc != npc:
            distance = npc.distance_to((other_npc.x, other_npc.y))
            if distance < 12:
                interaction_types = ['social_approach']
                if action_context['action'] == 'foraging':
                    interaction_types.append('resource_use')
                if distance < 8:
                    interaction_types.append('territory_enter')
                
                for interaction_type in interaction_types:
                    interaction_result = boundary_checker(
                        npc, other_npc, interaction_type, action_context, t
                    )
                    
                    if not interaction_result['allowed']:
                        if interaction_result['response'] == 'aggressive_defense':
                            print(f"⚔️ T{t}: BOUNDARY CONFLICT - {interaction_result['message']}")
                        elif interaction_result['response'] == 'firm_warning':
                            print(f"⚠️ T{t}: BOUNDARY WARNING - {interaction_result['message']}")
                    elif interaction_result['response'] == 'cooperative':
                        print(f"🤝 T{t}: BOUNDARY SHARING - {interaction_result['message']}")

def display_progress(roster, seasonal_modifiers, current_season_name, predator_attacks, t):
    """進捗表示"""
    if t % 25 == 0:
        alive_count = len([npc for npc in roster.values() if npc.alive])
        exploration_count = len([npc for npc in roster.values() if npc.alive and npc.exploration_mode])
        
        # 境界形成状況をチェック
        total_boundaries = sum(len(boundaries['people']) + len(boundaries['places']) + len(boundaries['resources']) 
                             for boundaries in boundary_system.subjective_boundaries.values())
        collective_count = len(boundary_system.collective_boundaries)
        violations_today = sum(len([v for v in violations if t - v['tick'] < 25]) 
                             for violations in boundary_system.boundary_violations.values())
        
        print(f"T{t} ({current_season_name}): 👥{alive_count} survivors, 🔍{exploration_count} exploring")
        if total_boundaries > 0 or collective_count > 0 or violations_today > 0:
            print(f"      🏘️{total_boundaries} boundaries, 🤝{collective_count} collectives, 🚫{violations_today} violations")
        
        # 季節サマリー
        berry_mod = seasonal_modifiers.get('berry_abundance', 1.0)
        temp_stress = seasonal_modifiers.get('temperature_stress', 0.0)
        print(f"      🌍 Resources: {berry_mod:.1f}x, Temperature stress: {temp_stress:.1f}")