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
    ecosystem_logs = []

    for t in range(1, ticks + 1):
        # エコシステム全体の更新
        env.ecosystem_step(list(roster.values()), t)
        
        # 捕食者狩りの試行（低確率）
        predator_hunting_attempts = 0
        for npc in roster.values():
            if npc.alive and random.random() < 0.005:  # 0.5%の確率
                hunt_result = npc.attempt_predator_hunting(env.predators, list(roster.values()), t)
                if hunt_result:
                    predator_hunting_attempts += 1
                    ecosystem_logs.append({
                        't': t,
                        'event': 'predator_hunting',
                        'hunter': npc.name,
                        'success': hunt_result['success'],
                        'group_size': hunt_result['group_size'],
                        'casualties': len(hunt_result['casualties']),
                        'injured': len(hunt_result['injured'])
                    })
        
        # 捕食者の攻撃処理
        for predator in env.predators:
            if predator.alive:
                # 狩猟対象の決定
                hunt_target = predator.decide_hunt_target(list(roster.values()), env.prey_animals)
                
                if hunt_target == 'prey':
                    # 動物を狩る
                    hunted = predator.hunt_prey(env.prey_animals, t)
                    if hunted:
                        ecosystem_logs.append({
                            't': t,
                            'event': 'predator_hunts_prey',
                            'predator_id': id(predator),
                            'prey_count': len(hunted)
                        })
                else:
                    # 人間を攻撃
                    attack_result = predator.hunt_step(list(roster.values()), t)
                    if attack_result:
                        if attack_result.get('victim'):
                            print(f"T{t}: Predator attack! {attack_result['victim']} killed (defenders: {attack_result['defenders']})")
                        elif attack_result.get('injured'):
                            print(f"T{t}: Predator attack! {attack_result['injured']} injured (defenders: {attack_result['defenders']})")
        
        # NPC行動
        for npc in roster.values():
            npc.step(t)
            logs.extend(npc.log[-10:])  # 最新10個のログのみ保持        # 天気ログ
        weather_logs.append({
            "t": t,
            "condition": env.weather.condition,
            "temperature": env.weather.temperature,
            "time_of_day": env.day_night.time_of_day,
            "predators": len([p for p in env.predators if p.alive]),
            "prey_animals": len([p for p in env.prey_animals if p.alive])
        })
        
        # 進捗表示
        if t % 100 == 0:
            survivors = sum(1 for npc in roster.values() if npc.alive)
            exploration_mode_count = sum(1 for npc in roster.values() if npc.alive and npc.exploration_mode)
            territories = len(set(id(npc.territory) for npc in roster.values() 
                                if npc.alive and npc.territory is not None))
            
            print(f"T{t}: Survivors={survivors}/16, Exploring={exploration_mode_count}, "
                  f"Territories={territories}, Predators={len([p for p in env.predators if p.alive])}")
    
    return list(roster.values()), pd.DataFrame(logs), pd.DataFrame(weather_logs), pd.DataFrame(ecosystem_logs)


def analyze_results(final_npcs, df_logs, df_weather, df_ecosystem=None):
    """結果分析（エコシステム対応）"""
    survivors = [npc for npc in final_npcs if npc.alive]
    print(f"\n=== SSD Village Simulation Results ===")
    print(f"Survivors: {len(survivors)}/16")
    
    # SSD理論関連分析
    if not df_logs.empty:
        mode_changes = df_logs[df_logs['action'].isin(['exploration_mode_leap', 'exploration_mode_reversion'])]
        print(f"SSD Mode Changes:")
        print(f"  - Exploration leaps: {len(mode_changes[mode_changes['action'] == 'exploration_mode_leap'])}")
        print(f"  - Mode reversions: {len(mode_changes[mode_changes['action'] == 'exploration_mode_reversion'])}")
        
        # コミュニティ形成分析（縄張りベース）
        territories = {}
        for npc in survivors:
            if npc.territory is not None:
                territory_id = id(npc.territory)
                if territory_id not in territories:
                    territories[territory_id] = []
                territories[territory_id].append(npc.name)
        
        # 社会的結束分析（看護関係・肉分配・狩り協力ベース）
        care_pairs = set()
        hunt_groups = set()
        meat_sharing_pairs = set()
        
        if not df_logs.empty:
            # 看護関係
            care_logs = df_logs[df_logs['action'] == 'start_caring']
            for _, log in care_logs.iterrows():
                if 'patient' in log:
                    care_pairs.add((log['name'], log['patient']))
            
            # 狩りグループ
            group_hunt_logs = df_logs[df_logs['action'].str.contains('group_hunt', na=False)]
            for _, log in group_hunt_logs.iterrows():
                if 'members' in log and log['members']:
                    members = tuple(sorted(log['members']))
                    hunt_groups.add(members)
            
            # 肉分配
            share_logs = df_logs[df_logs['action'] == 'share_meat']
            for _, log in share_logs.iterrows():
                if 'recipient' in log:
                    meat_sharing_pairs.add((log['name'], log['recipient']))
        
        print(f"\nCommunity Formation Analysis:")
        
        # 縄張りベースのコミュニティ
        if territories:
            print(f"  Territory-based Communities: {len(territories)}")
            for i, (territory_id, members) in enumerate(territories.items()):
                print(f"    - Territory {i+1}: {len(members)} members ({', '.join(members)})")
            
            max_community_size = max(len(members) for members in territories.values())
            avg_community_size = sum(len(members) for members in territories.values()) / len(territories)
            print(f"    - Maximum community size: {max_community_size}")
            print(f"    - Average community size: {avg_community_size:.1f}")
        else:
            print(f"  Territory-based Communities: 0 (no established territories)")
        
        # 社会的結束の指標
        print(f"\n  Social Bonding Indicators:")
        print(f"    - Care relationships: {len(care_pairs)} unique pairs")
        print(f"    - Hunting groups formed: {len(hunt_groups)}")
        print(f"    - Meat sharing relationships: {len(meat_sharing_pairs)} unique pairs")
        
        # 社会的ネットワーク密度
        total_possible_pairs = len(survivors) * (len(survivors) - 1) // 2 if len(survivors) > 1 else 0
        if total_possible_pairs > 0:
            social_connections = len(care_pairs) + len(meat_sharing_pairs)
            social_density = social_connections / total_possible_pairs
            print(f"    - Social network density: {social_density:.3f} ({social_connections}/{total_possible_pairs})")
        
        # 重症システムの影響
        witness_events = df_logs[df_logs['action'] == 'witness_critical_injury']
        if len(witness_events) > 0:
            print(f"    - Community empathy events: {len(witness_events)}")
            unique_witnesses = len(witness_events['name'].unique()) if 'name' in witness_events.columns else 0
            print(f"    - NPCs affected by witnessing: {unique_witnesses}/{len(survivors)}")
        
        # 信頼関係システムの分析
        trust_events = df_logs[df_logs['action'] == 'trust_update']
        if len(trust_events) > 0:
            print(f"\n  Trust Relationship System:")
            print(f"    - Trust updates recorded: {len(trust_events)}")
            
            # 各生存者の信頼ネットワーク
            high_trust_relationships = 0
            total_trust_relationships = 0
            
            for survivor in survivors:
                if hasattr(survivor, 'trust_levels'):
                    for target, trust_level in survivor.trust_levels.items():
                        if target in [s.name for s in survivors]:  # 相手も生存している場合のみ
                            total_trust_relationships += 1
                            if trust_level >= 0.7:  # 高信頼関係
                                high_trust_relationships += 1
            
            print(f"    - Active trust relationships: {total_trust_relationships}")
            print(f"    - High-trust bonds (>0.7): {high_trust_relationships}")
            
            if total_trust_relationships > 0:
                trust_ratio = high_trust_relationships / total_trust_relationships
                print(f"    - High-trust ratio: {trust_ratio:.3f}")
            
            # 最も信頼されているNPCを特定
            trust_received = {}
            for survivor in survivors:
                if hasattr(survivor, 'trust_levels'):
                    for target, trust_level in survivor.trust_levels.items():
                        if target in [s.name for s in survivors]:
                            if target not in trust_received:
                                trust_received[target] = []
                            trust_received[target].append(trust_level)
            
            if trust_received:
                avg_trust_received = {name: sum(trusts)/len(trusts) 
                                    for name, trusts in trust_received.items()}
                most_trusted = max(avg_trust_received.items(), key=lambda x: x[1])
                print(f"    - Most trusted NPC: {most_trusted[0]} (avg: {most_trusted[1]:.3f})")
        
        # 経験システムの分析
        if hasattr(survivors[0], 'experience'):
            print(f"\n  Experience System Analysis:")
            
            exp_totals = {'hunting': [], 'exploration': [], 'survival': [], 'care': [], 'social': [], 'predator_awareness': []}
            for survivor in survivors:
                for exp_type, exp_value in survivor.experience.items():
                    if exp_type in exp_totals:
                        exp_totals[exp_type].append(exp_value)
            
            for exp_type, values in exp_totals.items():
                if values:
                    avg_exp = sum(values) / len(values)
                    max_exp = max(values)
                    print(f"    - {exp_type.capitalize()} experience: avg {avg_exp:.2f}, max {max_exp:.2f}")
            
            # 最も経験豊富なNPCを特定
            total_exp_by_npc = {}
            for survivor in survivors:
                total_exp = sum(survivor.experience.values())
                total_exp_by_npc[survivor.name] = total_exp
            
            if total_exp_by_npc:
                most_experienced = max(total_exp_by_npc.items(), key=lambda x: x[1])
                print(f"    - Most experienced NPC: {most_experienced[0]} (total: {most_experienced[1]:.2f})")
            
            # SSD理論の意味圧との関係
            meaning_pressure_vs_exp = []
            for survivor in survivors:
                total_exp = sum(survivor.experience.values())
                meaning_pressure = survivor.E  # Eは意味圧のfloat値
                meaning_pressure_vs_exp.append((meaning_pressure, total_exp))
            
            if meaning_pressure_vs_exp:
                avg_meaning_pressure = sum(mp for mp, _ in meaning_pressure_vs_exp) / len(meaning_pressure_vs_exp)
                avg_total_exp = sum(exp for _, exp in meaning_pressure_vs_exp) / len(meaning_pressure_vs_exp)
                print(f"    - Average meaning pressure (E): {avg_meaning_pressure:.2f}")
                print(f"    - Average total experience: {avg_total_exp:.2f}")
                
                # 意味圧の95%制限に対する経験値の比率
                exp_ratios = []
                for survivor in survivors:
                    total_exp = sum(survivor.experience.values())
                    meaning_pressure = survivor.E
                    max_allowed_exp = meaning_pressure * 0.95  # SSD理論の制限
                    if max_allowed_exp > 0:
                        ratio = total_exp / max_allowed_exp
                        exp_ratios.append(ratio)
                
                if exp_ratios:
                    avg_ratio = sum(exp_ratios) / len(exp_ratios)
                    max_ratio = max(exp_ratios)
                    print(f"    - Experience saturation: avg {avg_ratio:.1%}, max {max_ratio:.1%} of meaning pressure limit")
        
        # 捕食者対策効果分析
        # ログデータの構造に応じて適切な列名を使用
        if 'action' in df_logs.columns:
            predator_encounters = len(df_logs[df_logs['action'].str.contains('predator.*encounter', na=False, case=False)])
            predator_escapes = len(df_logs[df_logs['action'].str.contains('predator.*escape', na=False, case=False)])
            predator_deaths = len(df_logs[df_logs['action'].str.contains('predator.*death', na=False, case=False)])
            predator_avoidances = len(df_logs[df_logs['action'].str.contains('predator.*avoid', na=False, case=False)])
        else:
            # デフォルト値を設定
            predator_encounters = 0
            predator_escapes = 0
            predator_deaths = 0
            predator_avoidances = 0
        
        print(f"\nPredator Defense Analysis:")
        if predator_encounters > 0 or predator_escapes > 0 or predator_deaths > 0:
            total_encounters = predator_encounters + predator_escapes + predator_deaths
            escape_rate = (predator_escapes / total_encounters * 100) if total_encounters > 0 else 0
            death_rate = (predator_deaths / total_encounters * 100) if total_encounters > 0 else 0
            print(f"  - Total predator encounters: {total_encounters}")
            print(f"  - Successful escapes: {predator_escapes} ({escape_rate:.1f}%)")
            print(f"  - Deaths from predators: {predator_deaths} ({death_rate:.1f}%)")
            print(f"  - Encounters avoided: {predator_avoidances}")
            
            # 経験豊富なNPCの生存分析
            if survivors:
                high_awareness_npcs = [npc for npc in survivors 
                                     if npc.alive and npc.experience.get('predator_awareness', 0) > 0.5]
                if high_awareness_npcs:
                    print(f"  - High awareness survivors: {len(high_awareness_npcs)} (experience>0.5)")
                
                # 捕食者遭遇経験の統計
                encounter_stats = [(npc.name, 
                                  getattr(npc, 'predator_encounters', 0), 
                                  getattr(npc, 'predator_escapes', 0), 
                                  npc.experience.get('predator_awareness', 0)) for npc in survivors if npc.alive]
                if encounter_stats:
                    avg_encounters = sum(stat[1] for stat in encounter_stats) / len(encounter_stats)
                    avg_escapes = sum(stat[2] for stat in encounter_stats) / len(encounter_stats)
                    avg_awareness = sum(stat[3] for stat in encounter_stats) / len(encounter_stats)
                    print(f"  - Avg encounters per survivor: {avg_encounters:.1f}")
                    print(f"  - Avg escapes per survivor: {avg_escapes:.1f}")
                    print(f"  - Avg awareness experience: {avg_awareness:.2f}")
        else:
            print(f"  - No predator encounters recorded")
        
        # 狩り分析
        hunting_events = df_logs[df_logs['action'].str.contains('hunt', na=False)]
        if len(hunting_events) > 0:
            print(f"\nHunting Activities:")
            print(f"  - Total hunting events: {len(hunting_events)}")
            success_hunts = hunting_events[hunting_events['action'].str.contains('success', na=False)]
            print(f"  - Successful hunts: {len(success_hunts)}")
            group_hunts = hunting_events[hunting_events['action'].str.contains('group', na=False)]
            solo_hunts = hunting_events[hunting_events['action'].str.contains('solo', na=False)]
            print(f"  - Group hunts: {len(group_hunts)}")
            print(f"  - Solo hunts: {len(solo_hunts)}")
            
            # 怪我分析
            injury_events = hunting_events[hunting_events['action'] == 'hunt_injury']
            if len(injury_events) > 0:
                total_damage = injury_events['damage'].sum() if 'damage' in injury_events.columns else 0
                avg_damage = injury_events['damage'].mean() if 'damage' in injury_events.columns else 0
                print(f"  - Hunt injuries: {len(injury_events)} (avg damage: {avg_damage:.1f})")
                
                # 重症分析
                critical_events = df_logs[df_logs['action'] == 'critical_injury']
                if len(critical_events) > 0:
                    print(f"  - Critical injuries: {len(critical_events)}")
                    
        # 重症・看護システム分析
        care_events = df_logs[df_logs['action'].str.contains('care', na=False)]
        critical_events = df_logs[df_logs['action'].str.contains('critical|injury_recovery', na=False)]
        
        if len(critical_events) > 0 or len(care_events) > 0:
            print(f"\nCritical Injury & Care System:")
            if len(critical_events) > 0:
                critical_injuries = df_logs[df_logs['action'] == 'critical_injury']
                recoveries = df_logs[df_logs['action'] == 'injury_recovery']
                print(f"  - Critical injuries: {len(critical_injuries)}")
                print(f"  - Full recoveries: {len(recoveries)}")
            
            if len(care_events) > 0:
                care_starts = df_logs[df_logs['action'] == 'start_caring']
                care_feeds = df_logs[df_logs['action'] == 'care_feed']
                witness_events = df_logs[df_logs['action'] == 'witness_critical_injury']
                print(f"  - Care relationships: {len(care_starts)}")
                print(f"  - Food sharing to injured: {len(care_feeds)}")
                if len(witness_events) > 0:
                    avg_empathy_boost = witness_events['empathy_increase'].mean() if 'empathy_increase' in witness_events.columns else 0
                    print(f"  - Injury witness events: {len(witness_events)} (avg empathy boost: {avg_empathy_boost:.3f})")
            
        meat_events = df_logs[df_logs['action'].str.contains('meat', na=False)]
        if len(meat_events) > 0:
            print(f"\nMeat Management:")
            print(f"  - Total meat events: {len(meat_events)}")
            shared_meat = meat_events[meat_events['action'].str.contains('share', na=False)]
            spoiled_meat = meat_events[meat_events['action'].str.contains('spoiled', na=False)]
            print(f"  - Meat sharing events: {len(shared_meat)}")
            print(f"  - Meat spoiled: {len(spoiled_meat)}")
    
    print(f"\n=== Simulation Complete ===")


if __name__ == "__main__":
    final_npcs, df_logs, df_weather = run_simulation(ticks=500)
    analyze_results(final_npcs, df_logs, df_weather)