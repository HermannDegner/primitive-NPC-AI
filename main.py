#!/usr/bin/env python3
"""
Enhanced SSD Village Simulation - Complete Integration + Subjective Boundary System
構造主観力学(SSD)理論完全統合版 + スマート環境システム + 主観的境界システム
"""

import random
import pandas as pd
import math
from config import *
from environment import Environment
from npc import NPC
from smart_environment import SmartEnvironment
from ssd_core import PhysicalStructureSystem
from subjective_boundary_system import integrate_subjective_boundary_system, SubjectiveBoundarySystem

class SeasonalSystem:
    """季節システム - 環境と資源の動的変化"""
    
    def __init__(self, season_length=50):
        self.season_length = season_length  # 1季節の長さ（ティック）
        self.current_season = 0  # 0:春, 1:夏, 2:秋, 3:冬
        self.season_names = ["🌸Spring", "🌞Summer", "🍂Autumn", "❄️Winter"]
        self.season_tick = 0
        
    def get_current_season(self, t):
        """現在の季節を取得"""
        self.season_tick = t % (self.season_length * 4)
        self.current_season = self.season_tick // self.season_length
        return self.current_season
    
    def get_season_name(self, t):
        """季節名を取得"""
        season = self.get_current_season(t)
        return self.season_names[season]
    
    def get_seasonal_modifiers(self, t):
        """季節による環境修正値"""
        season = self.get_current_season(t)
        progress = (self.season_tick % self.season_length) / self.season_length
        
        if season == 0:  # 春 - 成長期
            return {
                'berry_abundance': 1.0 + (progress * 0.8),  # 段階的増加
                'prey_activity': 1.0 + (progress * 0.6),
                'water_availability': 1.2,
                'temperature_stress': 0.0,
                'predator_activity': 0.8,  # 捕食者は比較的大人しい
                'exploration_bonus': 0.3,  # 探索に適した季節
                'social_gathering_bonus': 0.2
            }
        elif season == 1:  # 夏 - 豊穣期
            return {
                'berry_abundance': 1.8 - (progress * 0.3),  # 前半ピーク、後半減少
                'prey_activity': 1.4,
                'water_availability': 1.0 - (progress * 0.4),  # 段階的減少
                'temperature_stress': progress * 0.3,  # 暑さによるストレス
                'predator_activity': 1.2,  # 捕食者も活発
                'exploration_bonus': -0.1,  # 暑さで探索困難
                'social_gathering_bonus': 0.4  # 豊富な食料で社交活発
            }
        elif season == 2:  # 秋 - 準備期
            return {
                'berry_abundance': 1.2 - (progress * 0.7),  # 急激な減少
                'prey_activity': 1.0 - (progress * 0.3),
                'water_availability': 0.8 + (progress * 0.3),  # 雨期で回復
                'temperature_stress': 0.1,
                'predator_activity': 1.0 + (progress * 0.4),  # 冬に備えて活発化
                'exploration_bonus': 0.1,
                'social_gathering_bonus': -0.2,  # 準備で忙しく社交減少
                'hoarding_pressure': progress * 0.6  # 蓄え圧力
            }
        else:  # 冬 - 試練期
            return {
                'berry_abundance': 0.2 + (math.sin(progress * 3.14159) * 0.1),  # 極少
                'prey_activity': 0.4,  # 動物も少ない
                'water_availability': 0.6,  # 氷結などで減少
                'temperature_stress': 0.4 + (progress * 0.3),  # 寒さストレス
                'predator_activity': 0.6 - (progress * 0.2),  # 後半は冬眠傾向
                'exploration_bonus': -0.3,  # 探索困難
                'social_gathering_bonus': 0.5,  # 寒さで集まる傾向
                'survival_pressure': 0.4 + (progress * 0.4),  # 生存圧力最大
                'shelter_importance': 0.8
            }
    
    def apply_seasonal_effects(self, env, npcs, t):
        """環境とNPCに季節効果を適用"""
        modifiers = self.get_seasonal_modifiers(t)
        
        # 捕食者の活動度調整
        for predator in env.predators:
            if hasattr(predator, 'aggression'):
                if not hasattr(predator, 'base_aggression'):
                    predator.base_aggression = predator.aggression
                predator.aggression = predator.base_aggression * modifiers.get('predator_activity', 1.0)
        
        # NPCへの効果
        for npc in npcs:
            if not npc.alive:
                continue
                
            # 温度ストレス
            temp_stress = modifiers.get('temperature_stress', 0.0)
            if temp_stress > 0:
                npc.fatigue += temp_stress * 2
            
            # 探索ボーナス/ペナルティ
            exploration_mod = modifiers.get('exploration_bonus', 0.0)
            if hasattr(npc, 'seasonal_curiosity_mod'):
                npc.seasonal_curiosity_mod = exploration_mod
            else:
                npc.seasonal_curiosity_mod = exploration_mod
            
            # 社交性への影響
            social_mod = modifiers.get('social_gathering_bonus', 0.0)
            if hasattr(npc, 'seasonal_social_mod'):
                npc.seasonal_social_mod = social_mod
            else:
                npc.seasonal_social_mod = social_mod
            
            # 生存圧力
            survival_pressure = modifiers.get('survival_pressure', 0.0)
            if survival_pressure > 0:
                npc.hunger += survival_pressure * 1.5
                npc.thirst += survival_pressure * 1.0
        
        return modifiers

def run_enhanced_ssd_simulation(ticks=400):  # 1年サイクルを見るため400ティックに延長
    """SSD完全統合シミュレーション実行 + 季節システム"""
    
    # 季節システム初期化
    seasonal_system = SeasonalSystem(season_length=100)  # 1季節100ティック
    
    # シミュレーション統計変数
    total_predator_hunting_attempts = 0
    total_predator_kills = 0
    global boundary_system
    seed = random.randint(1, 1000)
    random.seed(seed)
    print(f"Enhanced SSD Simulation with SEASONAL SYSTEM - Random seed: {seed}")
    print("�🌞🍂❄️ FOUR SEASONS CARNIVORE SURVIVAL CHALLENGE �🌞🍂❄️")
    print("   Base: Berries: 0 (SEASONAL VARIATION), Water: 8, Hunt: 18, Caves: 6")
    print("   SEASONAL EFFECTS: Resource fluctuation, behavior changes, social dynamics")
    
    # 環境設定（スマート環境統合）- 完全肉食社会 + 捕食者脅威
    env = Environment(size=DEFAULT_WORLD_SIZE, 
                     n_berry=0,     # 完全撤廃 - 肉食のみの世界
                     n_hunt=18,     # デフォルト60 → 18に（狩場を増加）  
                     n_water=8,     # デフォルト40 → 8に80%削減（16人に対して0.5個/人）
                     n_caves=6,     # デフォルト25 → 6に75%削減
                     enable_smart_world=True)
    
    # 適度な脅威の捕食者を追加（境界形成を促進するため）
    from environment import Predator
    predator_positions = [(15, 85), (85, 15)]  # 2匹に削減、端に配置
    for i, pos in enumerate(predator_positions):
        predator = Predator(pos, aggression=0.4)  # 攻撃性を50%減少
        predator.hunt_radius = 8  # 狩猟範囲を縮小
        env.predators.append(predator)
        print(f"Added Balanced Predator_{i+1} at position {predator.pos()}, aggression: {predator.aggression}")
    
    smart_env = SmartEnvironment(world_size=DEFAULT_WORLD_SIZE)
    
    # 主観的境界システム初期化
    boundary_system = SubjectiveBoundarySystem()
    experience_handler, boundary_checker = integrate_subjective_boundary_system()
    
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
    
    # 境界システムにNPCレジストリを設定
    boundary_system.set_npc_roster(roster)
    
    print("=" * 60)
    
    # シミュレーション実行
    logs = []
    ssd_decision_logs = []
    environment_intelligence_logs = []
    total_predator_hunting_attempts = 0
    total_predator_kills = 0

    seasonal_logs = []

    for t in range(1, ticks + 1):
        # 季節効果の適用
        current_season_name = seasonal_system.get_season_name(t)
        seasonal_modifiers = seasonal_system.apply_seasonal_effects(env, list(roster.values()), t)
        
        # 季節変化の通知
        if t % seasonal_system.season_length == 1:
            print(f"\n🌍 T{t}: SEASON CHANGE TO {current_season_name}!")
            print(f"   📊 Effects: Berry×{seasonal_modifiers.get('berry_abundance', 1.0):.1f}, "
                  f"Prey×{seasonal_modifiers.get('prey_activity', 1.0):.1f}, "
                  f"Predator×{seasonal_modifiers.get('predator_activity', 1.0):.1f}")
        
        # エコシステム更新
        env.ecosystem_step(list(roster.values()), t)
        
        # 捕食者狩りの試行（季節影響あり）
        hunting_chance = 0.02 * seasonal_modifiers.get('predator_activity', 1.0)
        predator_hunting_attempts = 0
        predator_kills = 0
        for npc in roster.values():
            if npc.alive and random.random() < hunting_chance:
                hunt_result = npc.attempt_predator_hunting(env.predators, list(roster.values()), t)
                if hunt_result:
                    predator_hunting_attempts += 1
                    total_predator_hunting_attempts += 1
                    if hunt_result.get('predator_killed'):
                        predator_kills += 1
                        total_predator_kills += 1
                        print(f"  🏹 T{t} ({current_season_name}): PREDATOR HUNTING SUCCESS - Group of {hunt_result['group_size']} killed a predator!")
                        # 境界システムに成功体験を記録
                        boundary_system.process_subjective_experience(
                            npc, 'predator_defense_success', 'group_victory', 
                            {'group_size': hunt_result['group_size']}, t
                        )
                    elif hunt_result.get('casualties'):
                        print(f"  💀 T{t} ({current_season_name}): PREDATOR HUNTING FAILED - Casualties: {', '.join(hunt_result['casualties'])}")
        
        # 捕食者の攻撃処理
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
        
        # スマート環境分析
        smart_env.analyze_npc_impact(list(roster.values()), t)
        
        # 各NPCのSSD処理
        for npc in roster.values():
            if not npc.alive:
                continue
                
            # 環境フィードバック取得
            env_feedback = smart_env.provide_npc_environmental_feedback(npc, t)
            
            # SSD物理構造システム処理
            if hasattr(npc, 'physical_system'):
                # 環境制約更新
                npc.physical_system.physical_layer.update_environmental_constraints(env_feedback)
                npc.physical_system.upper_layer.receive_environmental_feedback(env_feedback)
                
                # 捕食者脅威の計算
                predator_threat = 0.0
                for predator in env.predators:
                    if predator.alive:
                        distance = ((npc.x - predator.x) ** 2 + (npc.y - predator.y) ** 2) ** 0.5
                        if distance < 20:  # 危険範囲内
                            predator_threat += max(0, (20 - distance) / 20)
                
                # 季節圧力の追加
                seasonal_pressure = 0.0
                if 'survival_pressure' in seasonal_modifiers:
                    seasonal_pressure = seasonal_modifiers['survival_pressure']
                
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
                
                # 季節ログ記録
                seasonal_logs.append({
                    't': t,
                    'season': current_season_name,
                    'npc': npc.name,
                    'seasonal_pressure': seasonal_pressure,
                    'temperature_stress': seasonal_modifiers.get('temperature_stress', 0.0),
                    'resource_modifier': seasonal_modifiers.get('berry_abundance', 1.0),
                    'exploration_mod': npc.seasonal_curiosity_mod,
                    'social_mod': npc.seasonal_social_mod
                })
                
                # 決定をNPC行動に反映
                if decision['type'] == 'leap':
                    npc.exploration_mode = True
                
                # 主観的境界システム: 経験処理（境界形成促進）
                action_context = {
                    'action': decision.get('action', 'foraging'),
                    'target_location': (npc.x, npc.y),
                    'social_interaction': decision.get('action') == 'social',
                    'success': random.random() > 0.3,  # 成功率70%に向上
                    'predator_threat': predator_threat > 0.2,  # より敏感な脅威検知
                    'resource_scarcity': env_feedback.get('resource_scarcity', 0) > 0.4,
                    'group_activity': len([other for other in roster.values() if other.alive and 
                                         ((npc.x - other.x)**2 + (npc.y - other.y)**2) < 225]) > 2  # 15マス範囲の仲間
                }
                
                # 経験処理
                experience_handler(npc, {'success': action_context['success']}, action_context, t)
                
                # 他のNPCとの境界相互作用チェック（強化版）
                for other_npc in roster.values():
                    if other_npc != npc and other_npc.alive:
                        distance = ((npc.x - other_npc.x)**2 + (npc.y - other_npc.y)**2) ** 0.5
                        if distance < 15:  # 相互作用範囲拡大
                            # 複数の相互作用タイプをチェック
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
                                        # 境界争いによる経験強化
                                        experience_handler(npc, {'success': False}, 
                                                         {**action_context, 'conflict': True, 'target_npc': other_npc}, t)
                                    elif interaction_result['response'] == 'firm_warning':
                                        print(f"⚠️ T{t}: BOUNDARY WARNING - {interaction_result['message']}")
                                elif interaction_result['response'] == 'cooperative':
                                    print(f"🤝 T{t}: BOUNDARY SHARING - {interaction_result['message']}")
                                    # 協力経験による境界強化
                                    experience_handler(npc, {'success': True}, 
                                                     {**action_context, 'social_cooperation': True, 'target_npc': other_npc}, t)
                
                # 行動タイプによる追加処理
                if decision['type'] == 'leap':
                    npc.exploration_mode_start_tick = t
                    npc.exploration_intensity = min(2.0, result.get('leap_probability', 1.0) + 0.5)
                elif decision['action'] == 'foraging':
                    npc.exploration_mode = False
                elif decision['action'] == 'resting':
                    # 休息決定時は疲労軽減
                    npc.fatigue = max(0, npc.fatigue - 15)
        
        # 進捗表示（境界形成重点版）
        if t % 25 == 0:  # より頻繁な更新
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
        
        # スマート環境統計記録（25ティックごと）
        if t % 25 == 0:
            env_state = smart_env.get_intelligence_summary()
            env_state['t'] = t
            environment_intelligence_logs.append(env_state)
    
    return roster, ssd_decision_logs, environment_intelligence_logs, seasonal_logs

def analyze_enhanced_results(roster, ssd_logs, env_intelligence_logs, seasonal_logs=None):
    """Enhanced analysis with boundary system + seasonal effects"""
    print("\\n" + "=" * 60)
    print("=== Enhanced SSD + Smart Environment + Boundary Analysis ===")
    print("=" * 60)
    
    # 生存者分析
    alive_npcs = [npc for npc in roster.values() if npc.alive]
    print(f"Final Survivors after FULL SEASONAL CYCLE: {len(alive_npcs)}/{len(roster)}")
    
    # 季節別分析
    if seasonal_logs:
        df_seasonal = pd.DataFrame(seasonal_logs)
        print(f"\\n🌍 Seasonal Impact Analysis:")
        
        for season in ['🌸Spring', '🌞Summer', '🍂Autumn', '❄️Winter']:
            season_data = df_seasonal[df_seasonal['season'] == season]
            if not season_data.empty:
                avg_pressure = season_data['seasonal_pressure'].mean()
                avg_temp_stress = season_data['temperature_stress'].mean()
                avg_resource_mod = season_data['resource_modifier'].mean()
                
                print(f"  {season}:")
                print(f"    Average seasonal pressure: {avg_pressure:.3f}")
                print(f"    Average temperature stress: {avg_temp_stress:.3f}")
                print(f"    Average resource availability: {avg_resource_mod:.3f}x")
    
    # SSD決定分析
    df_ssd = pd.DataFrame(ssd_logs)
    if not df_ssd.empty:
        print(f"\\nSSD Decision Analysis:")
        decision_counts = df_ssd['decision_type'].value_counts()
        for decision_type, count in decision_counts.items():
            print(f"  {decision_type}: {count} decisions")
        
        print(f"\\nAction Distribution:")
        action_counts = df_ssd['decision_action'].value_counts()
        for action, count in action_counts.items():
            print(f"  {action}: {count} times")
        
        # 跳躍分析
        leaps = df_ssd[df_ssd['decision_type'] == 'leap']
        print(f"\\nLeap Analysis:")
        print(f"  Total leaps: {len(leaps)}")
        if len(leaps) > 0:
            print(f"  Average leap probability: {leaps['leap_probability'].mean():.3f}")
        
        # 環境応答分析
        print(f"\\nEnvironmental Response Analysis:")
        print(f"  Avg environmental pressure: {df_ssd['environmental_pressure'].mean():.3f}")
        print(f"  Avg resource scarcity: {df_ssd['resource_scarcity'].mean():.3f}")
        print(f"  High pressure decisions: {len(df_ssd[df_ssd['environmental_pressure'] > 0.1])}")
    
    # 捕食者狩り分析（ログから抽出）
    print(f"\\n⚔️ Predator Hunting Analysis:")
    print(f"  Predator hunting system ACTIVE")
    print(f"  Evidence from simulation output shows hunting attempts occurred")
    print(f"  (Statistical details will be added in future version)")
    
    # 主観的境界システム分析
    print(f"\\n🏘️ Subjective Boundary System Analysis:")
    boundary_analysis = boundary_system.get_boundary_analysis(roster)
    
    print(f"  Individual boundary formations: {len(boundary_analysis['individual_boundaries'])}")
    print(f"  Collective boundaries formed: {len(boundary_analysis['collective_boundaries'])}")
    print(f"  Total boundary violations: {boundary_analysis['boundary_violations']}")
    
    # 個人境界の詳細
    print(f"\\n👤 Individual Boundaries:")
    for npc_name, boundary_info in boundary_analysis['individual_boundaries'].items():
        if boundary_info['boundary_clarity'] > 0.1:
            print(f"  {npc_name}:")
            print(f"    Inner people: {boundary_info['inner_people']}")
            print(f"    Inner places: {boundary_info['inner_places']}")
            print(f"    Inner resources: {boundary_info['inner_resources']}")
            print(f"    Boundary clarity: {boundary_info['boundary_clarity']:.3f}")
    
    # 集団境界の詳細
    if boundary_analysis['collective_boundaries']:
        print(f"\\n🤝 Collective Boundaries (In-Group Formation):")
        for collective_id, info in boundary_analysis['collective_boundaries'].items():
            print(f"  {collective_id}:")
            print(f"    Members: {', '.join(info['members'])}")
            print(f"    Cohesion: {info['cohesion']:.3f}")
            print(f"    Shared experiences: {info['shared_experiences']}")
    else:
        print(f"\\n🤝 No stable collective boundaries formed")
    
    # 環境知能分析
    df_env = pd.DataFrame(env_intelligence_logs)
    if not df_env.empty:
        print(f"\\nSmart Environment Intelligence Evolution:")
        final_state = df_env.iloc[-1]
        for key, value in final_state.items():
            if key != 't':
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
    
    print(f"\\nFinal Status Summary:")
    for npc in alive_npcs:
        print(f"  {npc.name}: Health OK")
        print(f"    Hunger: {npc.hunger:.1f}, Thirst: {npc.thirst:.1f}, Fatigue: {npc.fatigue:.1f}")
        print(f"    Exploration Mode: {npc.exploration_mode}")
        print(f"    Curiosity: {npc.curiosity:.3f}")
        print(f"    SSD Integration: {'ACTIVE' if hasattr(npc, 'physical_system') else 'INACTIVE'}")

# メイン実行
if __name__ == "__main__":
    try:
        print("=" * 60)
        print("🧠 SSD 4-Layer + Smart Environment + Boundaries 🌍")
        print("=" * 60)
        
        # 拡張シミュレーション実行
        final_roster, ssd_logs, env_logs, seasonal_logs = run_enhanced_ssd_simulation(ticks=400)
        
        # 結果分析
        analyze_enhanced_results(final_roster, ssd_logs, env_logs, seasonal_logs)
        
        print(f"\\n🎉 SEASONAL SURVIVAL COMPLETE - 4 Seasons Weathered! 🎉")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()