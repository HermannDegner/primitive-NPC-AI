#!/usr/bin/env python3
"""
Enhanced SSD Village Simulation - Ultimate Survival Challenge
構造主観力学(SSD)理論完全統合版 + スマート環境システム + 捕食者脅威
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
    
    # 捕食者の経験値ボーナス（時間経過で強くなる）
    experience_bonus = min(0.4, current_tick * 0.002)
    
    # 孤立した人間に対する捕食者ボーナス
    isolation_bonus = 0.3 if group_size < 4 else 0.0
    
    # 傷ついた捕食者は より危険に（絶望的攻撃）
    desperation_bonus = 0.5 if getattr(closest_predator, 'injured', False) else 0.0
    
    predator_power = base_power + experience_bonus + isolation_bonus + desperation_bonus + random.uniform(-0.1, 0.1)
    
    print(f"    Predator combat power: {predator_power:.2f} (base:{base_power:.2f}, exp:{experience_bonus:.2f}, isolation:{isolation_bonus:.2f})")
    
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
        # 捕食者を討伐
        closest_predator.alive = False
        result['predator_killed'] = True
        
        # 経験値獲得
        for hunter in hunting_group:
            hunter.experience['hunting'] = hunter.experience.get('hunting', 0) + 0.15
            hunter.experience['predator_awareness'] = hunter.experience.get('predator_awareness', 0) + 0.1
        
        # 強化された捕食者は死ぬ前に反撃（高確率負傷）
        casualties = []
        death_throes_damage = random.random() < min(0.6, 0.2 + closest_predator.aggression * 0.4)
        
        if death_throes_damage:
            # 最も前線に立った者が負傷
            casualty_count = min(2, max(1, int(group_size * 0.3)))
            for _ in range(casualty_count):
                injured = random.choice(hunting_group)
                if injured.name not in casualties:
                    injured.fatigue = min(100, injured.fatigue + 35)
                    injured.hunger = min(200, injured.hunger + 10)
                    casualties.append(injured.name)
                    print(f"      {injured.name} injured in final predator assault!")
        
        result['casualties'] = casualties
    else:
        # 討伐失敗 - 強化された捕食者の反撃
        casualties = []
        deaths = []
        
        # 失敗時の死亡確率（強化された捕食者は致命的）
        for hunter in hunting_group:
            damage_roll = random.random()
            
            if damage_roll < 0.15:  # 15%の死亡確率
                hunter.alive = False
                deaths.append(hunter.name)
                print(f"      {hunter.name} KILLED in failed hunt!")
            elif damage_roll < 0.5:  # 35%の重傷確率
                hunter.fatigue = min(100, hunter.fatigue + 40)
                hunter.hunger = min(200, hunter.hunger + 25)
                casualties.append(hunter.name)
                print(f"      {hunter.name} severely wounded!")
            
            # 経験値は獲得（生存者のみ）
            if hunter.alive:
                hunter.experience['predator_awareness'] = hunter.experience.get('predator_awareness', 0) + 0.03
        
        # 捕食者も負傷する可能性
        if random.random() < 0.3:
            closest_predator.injured = True
            print(f"      Predator wounded but survived!")
        
        result['casualties'] = casualties
        result['deaths'] = deaths
    
    return result

def run_ultimate_survival_simulation(ticks=200):
    """究極生存チャレンジシミュレーション実行"""
    seed = random.randint(1, 1000)
    random.seed(seed)
    print(f"Enhanced SSD Simulation (NIGHTMARE MODE) - Random seed: {seed}")
    print("NIGHTMARE SURVIVAL CHALLENGE: Resources 80% reduced + ENHANCED PREDATORS!")
    print("   Berries: 24 (1.5/person), Water: 8 (0.5/person), Hunt: 12, Caves: 6")
    print("   PLUS: 5 ENHANCED Predators with increased aggression & abilities!")
    print("   WARNING: Predators grow stronger over time and fight back when dying!")
    
    # 環境設定（スマート環境統合）- 極限の資源不足 + 捕食者脅威
    env = Environment(size=DEFAULT_WORLD_SIZE, 
                     n_berry=24,    # デフォルト120 → 24に80%削減（16人に対して1.5個/人）
                     n_hunt=12,     # デフォルト60 → 12に80%削減  
                     n_water=8,     # デフォルト40 → 8に80%削減（16人に対して0.5個/人）
                     n_caves=6,     # デフォルト25 → 6に75%削減
                     enable_smart_world=True)
    
    # 強化された捕食者を追加
    predator_configs = [
        ((10, 10), 1.2),   # アルファ捕食者（超攻撃的）
        ((80, 10), 0.9),   # ベータ捕食者（標準）
        ((45, 80), 1.0),   # ガンマ捕食者（標準+）
        ((20, 80), 1.1),   # デルタ捕食者（追加の脅威）
        ((70, 70), 0.8)    # イプシロン捕食者（狡猾）
    ]
    
    for i, (pos, aggression) in enumerate(predator_configs):
        predator = Predator(pos, aggression)
        # 捕食者を強化
        predator.hunt_radius = 12  # より大きな狩猟範囲
        predator.E = 6.0 + (i * 0.5)  # より高い意味圧
        predator.kappa = 1.5  # より強い整合慣性
        predator.P = 3.0  # より高い未処理圧
        env.predators.append(predator)
        print(f"Added ENHANCED Predator_{i+1} at {predator.pos()} (aggression: {aggression})")
    
    smart_env = SmartEnvironment(world_size=DEFAULT_WORLD_SIZE)
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
        roster[name] = npc
        print(f"Created {name} with SSD 4-Layer System")
    
    print(f"\nTotal NPCs with SSD Integration: {len(roster)}")
    print(f"Total ENHANCED Predators: {len(env.predators)}")
    print("WARNING: This is a NIGHTMARE difficulty challenge!")
    print("=" * 60)
    
    # シミュレーション実行
    logs = []
    ssd_decision_logs = []
    environment_intelligence_logs = []
    predator_events = []

    for t in range(1, ticks + 1):
        # エコシステム更新
        env.ecosystem_step(list(roster.values()), t)
        
        # 捕食者の攻撃処理
        predator_attacks = 0
        for predator in env.predators:
            if predator.alive:
                attack_result = predator.hunt_step(list(roster.values()), t)
                if attack_result:
                    predator_attacks += 1
                    if attack_result.get('victim'):
                        print(f"  T{t}: PREDATOR KILL - {attack_result['victim']} killed!")
                        predator_events.append({
                            't': t,
                            'event': 'predator_kill',
                            'victim': attack_result['victim']
                        })
        
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
                
                # 捕食者討伐機会の評価
                hunting_opportunity = 0.0
                nearby_allies = 0
                if predator_threat > 0:
                    # 近くの味方をカウント
                    for ally in roster.values():
                        if ally.alive and ally != npc:
                            ally_distance = ((npc.x - ally.x) ** 2 + (npc.y - ally.y) ** 2) ** 0.5
                            if ally_distance < 15:  # 協力可能距離
                                nearby_allies += 1
                    
                    # 戦闘能力評価（戦士系は高く、学者系は低く）
                    combat_skill = npc.risk_tolerance + (npc.experience.get('hunting', 0) * 0.5)
                    if 'Warrior' in npc.name or 'Guardian' in npc.name:
                        combat_skill += 0.3
                    elif 'Scholar' in npc.name or 'Healer' in npc.name:
                        combat_skill -= 0.2
                    
                    # グループ戦闘での討伐機会
                    if nearby_allies >= 2:  # 3人以上のグループ
                        hunting_opportunity = min(1.0, combat_skill + (nearby_allies * 0.2))
                
                # 外部刺激作成（捕食者脅威 + 討伐機会追加）
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
                
                # SSD構造力学処理
                result = npc.physical_system.process_structural_dynamics(external_stimuli)
                decision = result['final_decision']
                
                # 戦闘決定の強化判定
                if hunting_opportunity > 0.7 and nearby_allies >= 2:
                    # 高い討伐機会があれば戦闘を決定に追加
                    if decision['action'] == 'foraging' and random.random() < 0.3:
                        decision['action'] = 'hunting'
                        decision['combat_target'] = 'predator'
                
                # ログ記録
                ssd_decision_logs.append({
                    't': t,
                    'npc': npc.name,
                    'decision_action': decision['action'],
                    'decision_type': decision['type'],
                    'environmental_pressure': env_feedback.get('environmental_pressure', 0),
                    'resource_scarcity': env_feedback.get('resource_scarcity', 0),
                    'predator_threat': predator_threat,
                    'hunting_opportunity': hunting_opportunity,
                    'nearby_allies': nearby_allies,
                    'meaning_pressure': result.get('meaning_pressure', 0),
                    'leap_probability': result.get('leap_probability', 0),
                    'curiosity': npc.curiosity,
                    'exploration_mode': npc.exploration_mode
                })
                
                # 決定をNPC行動に反映
                if decision['type'] == 'leap':
                    npc.exploration_mode = True
                    npc.exploration_mode_start_tick = t
                    npc.exploration_intensity = min(2.0, result.get('leap_probability', 1.0) + 0.5)
                elif decision['action'] == 'foraging':
                    npc.exploration_mode = False
                elif decision['action'] == 'resting':
                    # 休息決定時は疲労軽減
                    npc.fatigue = max(0, npc.fatigue - 15)
                elif decision['action'] == 'hunting' and hunting_opportunity > 0.5:
                    # 捕食者討伐の実行
                    predator_hunt_result = attempt_predator_hunt(npc, env.predators, roster, t, nearby_allies)
                    if predator_hunt_result:
                        predator_events.append({
                            't': t,
                            'event': 'predator_hunt_attempt',
                            'leader': npc.name,
                            'group_size': predator_hunt_result['group_size'],
                            'success': predator_hunt_result['success'],
                            'casualties': predator_hunt_result.get('casualties', []),
                            'predator_killed': predator_hunt_result.get('predator_killed', False)
                        })
                        if predator_hunt_result['success']:
                            print(f"  T{t}: ENHANCED PREDATOR DEFEATED! {npc.name} led group hunt (size: {predator_hunt_result['group_size']})")
                            if predator_hunt_result.get('casualties'):
                                print(f"       But with casualties: {', '.join(predator_hunt_result['casualties'])}")
                        else:
                            print(f"  T{t}: HUNT FAILED - {npc.name}'s group unsuccessful against enhanced predator!")
                            if predator_hunt_result.get('deaths'):
                                print(f"       DEATHS: {', '.join(predator_hunt_result['deaths'])}")
                            if predator_hunt_result.get('casualties'):
                                print(f"       WOUNDED: {', '.join(predator_hunt_result['casualties'])}")
        
        # 進捗表示（詳細版）
        if t % 50 == 0:
            alive_count = sum(1 for npc in roster.values() if npc.alive)
            exploring_count = sum(1 for npc in roster.values() if npc.alive and npc.exploration_mode)
            alive_predators = sum(1 for p in env.predators if p.alive)
            intelligence = smart_env.get_intelligence_summary()
            
            # 資源状況分析
            avg_hunger = sum(npc.hunger for npc in roster.values() if npc.alive) / alive_count if alive_count > 0 else 0
            avg_thirst = sum(npc.thirst for npc in roster.values() if npc.alive) / alive_count if alive_count > 0 else 0
            
            print(f"T{t}: Alive={alive_count}/{len(roster)}, "
                  f"Exploring={exploring_count}, "
                  f"Predators={alive_predators}, "
                  f"Env_Stress={intelligence['environmental_stress']:.3f}, "
                  f"Avg_Hunger={avg_hunger:.1f}, "
                  f"Avg_Thirst={avg_thirst:.1f}")
        
        # 環境知能ログ
        if t % 25 == 0:
            intelligence = smart_env.get_intelligence_summary()
            environment_intelligence_logs.append({
                't': t,
                **intelligence
            })
    
    return roster, ssd_decision_logs, environment_intelligence_logs, predator_events

def analyze_ultimate_results(roster, ssd_logs, env_intelligence_logs, predator_events):
    """究極生存チャレンジ結果分析"""
    print("\n" + "=" * 60)
    print("=== ULTIMATE SURVIVAL CHALLENGE ANALYSIS ===")
    print("=" * 60)
    
    # 生存者分析
    alive_npcs = [npc for npc in roster.values() if npc.alive]
    dead_npcs = [npc for npc in roster.values() if not npc.alive]
    
    print(f"FINAL SURVIVORS: {len(alive_npcs)}/{len(roster)} ({len(alive_npcs)/len(roster)*100:.1f}%)")
    if dead_npcs:
        print(f"CASUALTIES: {len(dead_npcs)} NPCs died")
        for npc in dead_npcs:
            print(f"  - {npc.name}")
    
    # 捕食者脅威分析
    print(f"\nPREDATOR THREAT ANALYSIS:")
    print(f"  Total predator events: {len(predator_events)}")
    
    kills = [e for e in predator_events if e['event'] == 'predator_kill']
    hunts = [e for e in predator_events if e['event'] == 'predator_hunt_attempt']
    successful_hunts = [e for e in hunts if e.get('success', False)]
    
    print(f"  Predator kills on NPCs: {len(kills)}")
    print(f"  NPC hunt attempts: {len(hunts)}")
    print(f"  Successful NPC hunts: {len(successful_hunts)}")
    
    if kills:
        print(f"  NPC casualties:")
        for kill in kills:
            print(f"    - T{kill['t']}: {kill['victim']} killed by predator")
    
    if successful_hunts:
        print(f"  Predator defeats:")
        for hunt in successful_hunts:
            print(f"    - T{hunt['t']}: {hunt['leader']} led successful hunt (group: {hunt['group_size']})")
    
    # 最終捕食者状況 - environment.predatorsから取得
    # この関数では環境オブジェクトにアクセスできないため、イベントログから推測
    predators_killed = len(successful_hunts)
    print(f"  Predators killed by NPCs: {predators_killed}")
    
    # SSD決定分析
    df_ssd = pd.DataFrame(ssd_logs)
    if not df_ssd.empty:
        print(f"\nSSD DECISION ANALYSIS:")
        decision_counts = df_ssd['decision_type'].value_counts()
        for decision_type, count in decision_counts.items():
            print(f"  {decision_type}: {count} decisions")
        
        # 捕食者脅威への応答
        high_threat_decisions = df_ssd[df_ssd['predator_threat'] > 0.5]
        print(f"\nHIGH PREDATOR THREAT RESPONSES:")
        print(f"  High threat situations: {len(high_threat_decisions)}")
        if len(high_threat_decisions) > 0:
            print(f"  Average threat level: {high_threat_decisions['predator_threat'].mean():.3f}")
    
    # 環境知能最終状態
    df_env = pd.DataFrame(env_intelligence_logs)
    if not df_env.empty:
        print(f"\nSMART ENVIRONMENT FINAL STATE:")
        final_state = df_env.iloc[-1]
        for key, value in final_state.items():
            if key != 't':
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
    
    # 生存者詳細
    print(f"\nSURVIVOR DETAILS:")
    for npc in alive_npcs:
        print(f"  {npc.name}:")
        print(f"    Position: ({npc.x}, {npc.y})")
        print(f"    Exploration Mode: {npc.exploration_mode}")
        print(f"    SSD Integration: ACTIVE")

# メイン実行
if __name__ == "__main__":
    try:
        print("=" * 60)
        print("NIGHTMARE SURVIVAL CHALLENGE")
        print("SSD 4-Layer + Smart Environment + ENHANCED Predator Threats")
        print("=" * 60)
        
        # 究極生存チャレンジ実行
        final_roster, ssd_logs, env_logs, predator_events = run_ultimate_survival_simulation(ticks=200)
        
        # 結果分析
        analyze_ultimate_results(final_roster, ssd_logs, env_logs, predator_events)
        
        print("\n" + "=" * 60)
        print("ULTIMATE SURVIVAL CHALLENGE COMPLETE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()