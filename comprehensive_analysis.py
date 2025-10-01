#!/usr/bin/env python3
"""
SSD Village Simulation - 包括的分析
10回のシミュレーション実行で死亡、コミュニティ形成、捕食者警戒を総合分析
"""

import sys
import os
from collections import defaultdict, Counter
import statistics
import random

# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from simulation import run_simulation
    from config import PERSONALITY_PRESETS
except ImportError as e:
    print(f"インポートエラー: {e}")
    sys.exit(1)

def comprehensive_analysis(runs=10):
    """10回のシミュレーション実行で総合分析"""
    
    print("=" * 80)
    print("SSD Village Simulation - 包括的分析")
    print("死亡パターン・コミュニティ形成・捕食者警戒システム")
    print("=" * 80)
    print(f"{runs}回のシミュレーションを実行中...")
    print()
    
    # 分析データの初期化
    all_run_data = []
    death_data = []
    community_data = []
    predator_data = []
    personality_stats = defaultdict(lambda: {
        'total': 0, 'deaths': 0, 'predator_deaths': 0, 'other_deaths': 0,
        'avg_awareness_exp': 0.0, 'max_awareness_exp': 0.0,
        'survival_times': [], 'community_participation': 0
    })
    
    for run_num in range(1, runs + 1):
        print(f"--- Run {run_num}/{runs} ---")
        
        try:
            # 異なるシード値で実行
            random.seed(run_num * 1337)
            
            # シミュレーション実行
            final_npcs, df_logs, df_weather = run_simulation(ticks=500)
            
            # 基本統計
            survivors = [npc for npc in final_npcs if npc.alive]
            initial_count = len(final_npcs)
            
            # 死亡分析
            deaths_this_run = []
            predator_deaths = 0
            other_deaths = 0
            
            # NPCのalive状態から死亡を判定
            dead_npcs = [npc for npc in final_npcs if not npc.alive]
            
            # ログから捕食者攻撃による死亡を特定
            predator_kills = []
            for _, log in df_logs.iterrows():
                event = log.get('event', '')
                if 'predator attack!' in event.lower() and 'killed' in event.lower():
                    # "Predator attack! Warrior_Echo killed" 形式から名前を抽出
                    parts = event.split('!')
                    if len(parts) > 1:
                        kill_part = parts[1].strip()
                        if 'killed' in kill_part:
                            victim_name = kill_part.split(' killed')[0].strip()
                            predator_kills.append(victim_name)
            
            # 各死亡NPCの死因を判定
            for npc in dead_npcs:
                # 性格推定
                personality = 'unknown'
                personality_names = ['PIONEER', 'ADVENTURER', 'TRACKER', 'SCHOLAR', 'WARRIOR', 'GUARDIAN',
                                   'HEALER', 'DIPLOMAT', 'FORAGER', 'LEADER', 'LONER', 'NOMAD']
                for preset_name in personality_names:
                    if preset_name.lower() in npc.name.lower():
                        personality = preset_name
                        break
                
                # 死因判定
                if npc.name in predator_kills:
                    cause = 'predator_attack'
                    predator_deaths += 1
                    survival_time = 500  # 推定生存時間
                elif hasattr(npc, 'thirst') and npc.thirst > 200:
                    cause = 'dehydration'
                    other_deaths += 1
                    survival_time = 500
                elif hasattr(npc, 'hunger') and npc.hunger > 200:
                    cause = 'starvation'
                    other_deaths += 1
                    survival_time = 500
                elif hasattr(npc, 'fatigue') and npc.fatigue > 100:
                    cause = 'exhaustion'
                    other_deaths += 1
                    survival_time = 500
                else:
                    cause = 'other'
                    other_deaths += 1
                    survival_time = 500
                
                death_info = {
                    'run': run_num,
                    'npc_name': npc.name,
                    'personality': personality,
                    'cause': cause,
                    'survival_time': survival_time,
                    'event_text': f"{cause} death"
                }
                
                deaths_this_run.append(death_info)
                death_data.append(death_info)
                
                # 性格別統計更新
                personality_stats[personality]['deaths'] += 1
                if cause == 'predator_attack':
                    personality_stats[personality]['predator_deaths'] += 1
                else:
                    personality_stats[personality]['other_deaths'] += 1
                personality_stats[personality]['survival_times'].append(survival_time)
            
            # 生存者分析
            community_indicators = {
                'care_relationships': 0,
                'hunting_groups': 0,
                'meat_sharing': 0,
                'trust_relationships': 0,
                'high_awareness_survivors': 0,
                'total_awareness_exp': 0,
                'avg_awareness_exp': 0,
                'community_formation_level': 0
            }
            
            predator_indicators = {
                'encounters': 0,
                'escapes': 0,
                'avoidances': 0,
                'early_detections': 0,
                'group_alerts': 0,
                'total_defensive_actions': 0
            }
            
            # 生存者の経験と社会的指標を分析
            total_awareness_exp = 0
            high_awareness_count = 0
            
            for npc in survivors:
                # 性格推定
                personality = 'unknown'
                personality_names = ['PIONEER', 'ADVENTURER', 'TRACKER', 'SCHOLAR', 'WARRIOR', 'GUARDIAN',
                                   'HEALER', 'DIPLOMAT', 'FORAGER', 'LEADER', 'LONER', 'NOMAD']
                for preset_name in personality_names:
                    if preset_name.lower() in npc.name.lower():
                        personality = preset_name
                        break
                
                personality_stats[personality]['total'] += 1
                
                # 経験値分析
                if hasattr(npc, 'experience'):
                    awareness_exp = npc.experience.get('predator_awareness', 0.0)
                    total_awareness_exp += awareness_exp
                    
                    if awareness_exp > 0.5:
                        high_awareness_count += 1
                    
                    # 性格別経験統計
                    current_avg = personality_stats[personality]['avg_awareness_exp']
                    current_max = personality_stats[personality]['max_awareness_exp']
                    personality_stats[personality]['avg_awareness_exp'] = max(current_avg, awareness_exp)
                    personality_stats[personality]['max_awareness_exp'] = max(current_max, awareness_exp)
                
                # コミュニティ参加度
                if hasattr(npc, 'trust_levels') and len(npc.trust_levels) > 3:
                    personality_stats[personality]['community_participation'] += 1
            
            # ログからコミュニティ・捕食者イベントを抽出
            for _, log in df_logs.iterrows():
                event = log.get('event', '').lower()
                action = log.get('action', '').lower()
                
                # コミュニティ形成指標
                if any(keyword in event for keyword in ['care', 'help', 'share']):
                    community_indicators['care_relationships'] += 1
                elif any(keyword in event for keyword in ['hunt', 'group']):
                    community_indicators['hunting_groups'] += 1
                elif any(keyword in event for keyword in ['meat', 'food']):
                    community_indicators['meat_sharing'] += 1
                elif any(keyword in event for keyword in ['trust', 'bond']):
                    community_indicators['trust_relationships'] += 1
                
                # 捕食者対策指標
                if 'predator' in event:
                    if 'encounter' in event:
                        predator_indicators['encounters'] += 1
                    elif 'escape' in event:
                        predator_indicators['escapes'] += 1
                    elif 'avoid' in event:
                        predator_indicators['avoidances'] += 1
                    elif 'detect' in event:
                        predator_indicators['early_detections'] += 1
                    elif 'alert' in event:
                        predator_indicators['group_alerts'] += 1
            
            # 統合指標計算
            community_indicators['high_awareness_survivors'] = high_awareness_count
            community_indicators['total_awareness_exp'] = total_awareness_exp
            community_indicators['avg_awareness_exp'] = total_awareness_exp / len(survivors) if survivors else 0
            
            # コミュニティ形成レベル（0-100）
            community_score = min(100, 
                community_indicators['care_relationships'] * 2 +
                community_indicators['hunting_groups'] * 3 +
                community_indicators['meat_sharing'] * 1 +
                community_indicators['trust_relationships'] * 4 +
                high_awareness_count * 5
            )
            community_indicators['community_formation_level'] = community_score
            
            predator_indicators['total_defensive_actions'] = (
                predator_indicators['escapes'] + 
                predator_indicators['avoidances'] + 
                predator_indicators['early_detections']
            )
            
            # この回のデータを記録
            run_data = {
                'run': run_num,
                'initial_count': initial_count,
                'survivors': len(survivors),
                'deaths': len(deaths_this_run),
                'predator_deaths': predator_deaths,
                'other_deaths': other_deaths,
                'survival_rate': len(survivors) / initial_count if initial_count > 0 else 0,
                'community_indicators': community_indicators,
                'predator_indicators': predator_indicators
            }
            
            all_run_data.append(run_data)
            community_data.append(community_indicators)
            predator_data.append(predator_indicators)
            
            # 実行結果表示
            print(f"  初期: {initial_count}人, 生存: {len(survivors)}人, 死亡: {len(deaths_this_run)}人")
            print(f"  捕食者死亡: {predator_deaths}人, その他死亡: {other_deaths}人")
            print(f"  生存率: {run_data['survival_rate']*100:.1f}%, コミュニティ形成度: {community_score}")
            
        except Exception as e:
            print(f"  Run {run_num} でエラー: {e}")
            continue
    
    # 結果分析開始
    print("\n" + "=" * 80)
    print("包括的分析結果")
    print("=" * 80)
    
    # 1. 基本統計
    if all_run_data:
        total_initial = sum(d['initial_count'] for d in all_run_data)
        total_survivors = sum(d['survivors'] for d in all_run_data)
        total_deaths = sum(d['deaths'] for d in all_run_data)
        total_predator_deaths = sum(d['predator_deaths'] for d in all_run_data)
        total_other_deaths = sum(d['other_deaths'] for d in all_run_data)
        
        print(f"📊 基本統計:")
        print(f"  総人口: {total_initial}人")
        print(f"  総生存者: {total_survivors}人")
        print(f"  総死亡者: {total_deaths}人")
        if total_deaths > 0:
            print(f"    ├─ 捕食者による死亡: {total_predator_deaths}人 ({total_predator_deaths/total_deaths*100:.1f}%)")
            print(f"    └─ その他の死亡: {total_other_deaths}人 ({total_other_deaths/total_deaths*100:.1f}%)")
        else:
            print(f"    ├─ 捕食者による死亡: {total_predator_deaths}人")
            print(f"    └─ その他の死亡: {total_other_deaths}人")
        print(f"  全体生存率: {total_survivors/total_initial*100:.1f}%")
        
        avg_survival_rate = statistics.mean([d['survival_rate'] for d in all_run_data])
        print(f"  平均生存率: {avg_survival_rate*100:.1f}%")
        print()
    
    # 2. 死因別分析
    if death_data:
        print(f"⚰️ 死因別分析:")
        cause_counts = Counter([d['cause'] for d in death_data])
        for cause, count in cause_counts.most_common():
            percentage = count / len(death_data) * 100
            print(f"  {cause}: {count}件 ({percentage:.1f}%)")
        
        # 生存時間分析
        survival_times = [d['survival_time'] for d in death_data]
        if survival_times:
            print(f"\n  生存時間分析:")
            print(f"    平均生存時間: {statistics.mean(survival_times):.1f}ティック")
            print(f"    最短: {min(survival_times)}ティック")
            print(f"    最長: {max(survival_times)}ティック")
            print(f"    中央値: {statistics.median(survival_times):.1f}ティック")
        print()
    
    # 3. 性格別分析
    print(f"🎭 性格別生存分析:")
    personality_survival_rates = {}
    for personality, stats in personality_stats.items():
        if stats['total'] > 0:
            survival_rate = (stats['total'] - stats['deaths']) / stats['total']
            predator_death_rate = stats['predator_deaths'] / stats['deaths'] if stats['deaths'] > 0 else 0
            
            personality_survival_rates[personality] = survival_rate
            
            print(f"  {personality}:")
            print(f"    生存率: {survival_rate*100:.1f}% ({stats['total']-stats['deaths']}/{stats['total']}人)")
            print(f"    捕食者死亡: {stats['predator_deaths']}人")
            print(f"    その他死亡: {stats['other_deaths']}人")
            print(f"    警戒経験: 平均{stats['avg_awareness_exp']:.3f}, 最大{stats['max_awareness_exp']:.3f}")
            if stats['survival_times']:
                avg_survival_time = statistics.mean(stats['survival_times'])
                print(f"    平均生存時間: {avg_survival_time:.1f}ティック")
    
    # 生存率ランキング
    sorted_personalities = sorted(personality_survival_rates.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  生存率ランキング:")
    for i, (personality, rate) in enumerate(sorted_personalities, 1):
        print(f"    {i}. {personality}: {rate*100:.1f}%")
    print()
    
    # 4. コミュニティ形成分析
    if community_data:
        print(f"🏘️ コミュニティ形成分析:")
        
        avg_care = statistics.mean([d['care_relationships'] for d in community_data])
        avg_hunting = statistics.mean([d['hunting_groups'] for d in community_data])
        avg_sharing = statistics.mean([d['meat_sharing'] for d in community_data])
        avg_trust = statistics.mean([d['trust_relationships'] for d in community_data])
        avg_community_level = statistics.mean([d['community_formation_level'] for d in community_data])
        
        print(f"  平均コミュニティ指標:")
        print(f"    ケア関係: {avg_care:.1f}件/回")
        print(f"    狩り集団: {avg_hunting:.1f}件/回")
        print(f"    食料分配: {avg_sharing:.1f}件/回")
        print(f"    信頼関係: {avg_trust:.1f}件/回")
        print(f"    総合形成度: {avg_community_level:.1f}/100")
        
        # 最高コミュニティ形成度の回
        best_community_run = max(all_run_data, key=lambda x: x['community_indicators']['community_formation_level'])
        print(f"\n  最高コミュニティ形成:")
        print(f"    Run {best_community_run['run']}: 形成度{best_community_run['community_indicators']['community_formation_level']}")
        print(f"    生存率: {best_community_run['survival_rate']*100:.1f}%")
        print()
    
    # 5. 捕食者対策分析
    if predator_data:
        print(f"🛡️ 捕食者対策システム分析:")
        
        total_encounters = sum([d['encounters'] for d in predator_data])
        total_escapes = sum([d['escapes'] for d in predator_data])
        total_avoidances = sum([d['avoidances'] for d in predator_data])
        total_detections = sum([d['early_detections'] for d in predator_data])
        total_alerts = sum([d['group_alerts'] for d in predator_data])
        total_defensive = sum([d['total_defensive_actions'] for d in predator_data])
        
        print(f"  総合防御統計:")
        print(f"    遭遇: {total_encounters}回")
        print(f"    逃走成功: {total_escapes}回")
        print(f"    遭遇回避: {total_avoidances}回")
        print(f"    早期発見: {total_detections}回")
        print(f"    集団警戒: {total_alerts}回")
        print(f"    総防御行動: {total_defensive}回")
        
        if total_encounters > 0:
            escape_success_rate = total_escapes / total_encounters * 100
            print(f"    逃走成功率: {escape_success_rate:.1f}%")
        
        # 防御効果と生存率の相関
        defense_survival_correlation = []
        for run_data in all_run_data:
            defense_score = run_data['predator_indicators']['total_defensive_actions']
            survival_rate = run_data['survival_rate']
            defense_survival_correlation.append((defense_score, survival_rate))
        
        print()
    
    # 6. 各回詳細
    print(f"📋 各回詳細結果:")
    for data in all_run_data:
        print(f"  Run {data['run']}: "
              f"生存率{data['survival_rate']*100:.1f}% "
              f"({data['survivors']}/{data['initial_count']}人), "
              f"コミュニティ度{data['community_indicators']['community_formation_level']}, "
              f"捕食者死亡{data['predator_deaths']}人")
    
    print("\n" + "=" * 80)
    print("包括的分析完了")
    print("=" * 80)
    
    return all_run_data, personality_survival_rates, community_data, predator_data

if __name__ == "__main__":
    comprehensive_analysis(runs=10)