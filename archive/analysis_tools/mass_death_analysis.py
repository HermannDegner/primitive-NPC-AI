#!/usr/bin/env python3
"""
集団死分析スクリプト - 10回連続実行による死亡パターン分析
Enhanced SSD Theory + Seasonal System の統計的検証
"""

import json
import statistics
from enhanced_simulation import run_enhanced_ssd_simulation
import time

def analyze_mass_death_patterns():
    """10回連続実行による集団死パターンの分析"""
    
    print("🔬 集団死分析開始 - 10回連続実行による統計的検証")
    print("=" * 80)
    
    results = []
    
    for run_id in range(1, 11):
        print(f"\n🧪 実行 {run_id}/10 開始...")
        start_time = time.time()
        
        try:
            # シミュレーション実行
            roster, ssd_logs, env_logs, seasonal_logs = run_enhanced_ssd_simulation(ticks=200)
            
            # 生存者分析
            survivors = [npc for npc in roster.values() if npc.alive]
            deaths = [npc for npc in roster.values() if not npc.alive]
            
            # 死亡原因分析
            death_causes = {}
            death_times = []
            death_locations = []
            
            for npc in deaths:
                # 死亡時の状態記録
                cause = "unknown"
                if hasattr(npc, 'death_cause'):
                    cause = npc.death_cause
                elif npc.thirst >= 180:
                    cause = "dehydration"
                elif npc.hunger >= 200:
                    cause = "starvation"
                else:
                    cause = "other"
                
                if cause not in death_causes:
                    death_causes[cause] = 0
                death_causes[cause] += 1
                
                if hasattr(npc, 'death_time'):
                    death_times.append(npc.death_time)
                death_locations.append(npc.pos())
            
            # 生存者特性分析
            survivor_types = {}
            survivor_health = {
                'hunger': [],
                'thirst': [], 
                'fatigue': [],
                'curiosity': [],
                'sociability': []
            }
            
            for survivor in survivors:
                # タイプ分析
                npc_type = survivor.preset_name if hasattr(survivor, 'preset_name') else "unknown"
                if npc_type not in survivor_types:
                    survivor_types[npc_type] = 0
                survivor_types[npc_type] += 1
                
                # 健康状態分析
                survivor_health['hunger'].append(survivor.hunger)
                survivor_health['thirst'].append(survivor.thirst)
                survivor_health['fatigue'].append(survivor.fatigue)
                survivor_health['curiosity'].append(survivor.curiosity)
                survivor_health['sociability'].append(survivor.sociability)
            
            # SSD決定分析
            ssd_stats = {
                'normal_decisions': 0,
                'leap_decisions': 0,
                'total_decisions': 0
            }
            
            for log in ssd_logs:
                ssd_stats['total_decisions'] += 1
                if log.get('decision_type') == 'leap':
                    ssd_stats['leap_decisions'] += 1
                else:
                    ssd_stats['normal_decisions'] += 1
            
            # 実行時間計測
            execution_time = time.time() - start_time
            
            # 結果記録
            run_result = {
                'run_id': run_id,
                'execution_time': execution_time,
                'total_npcs': len(roster),
                'survivors': len(survivors),
                'deaths': len(deaths),
                'survival_rate': len(survivors) / len(roster),
                'death_causes': death_causes,
                'death_times': death_times,
                'death_locations': death_locations,
                'survivor_types': survivor_types,
                'survivor_health': survivor_health,
                'ssd_stats': ssd_stats
            }
            
            results.append(run_result)
            
            print(f"✅ 実行 {run_id} 完了 - 生存者: {len(survivors)}/{len(roster)} ({len(survivors)/len(roster)*100:.1f}%)")
            print(f"   主な死因: {death_causes}")
            print(f"   実行時間: {execution_time:.1f}秒")
            
        except Exception as e:
            print(f"❌ 実行 {run_id} でエラー: {e}")
            continue
    
    # 統計分析
    print("\n" + "=" * 80)
    print("📊 集団死パターン統計分析結果")
    print("=" * 80)
    
    if not results:
        print("❌ 分析対象データなし")
        return
    
    # 基本統計
    survival_rates = [r['survival_rate'] for r in results]
    total_survivors = [r['survivors'] for r in results]
    total_deaths = [r['deaths'] for r in results]
    
    print(f"\n🎯 基本統計 (n={len(results)}):")
    print(f"   平均生存率: {statistics.mean(survival_rates)*100:.1f}% (±{statistics.stdev(survival_rates)*100:.1f}%)")
    print(f"   最高生存率: {max(survival_rates)*100:.1f}%")
    print(f"   最低生存率: {min(survival_rates)*100:.1f}%")
    print(f"   平均生存者数: {statistics.mean(total_survivors):.1f}人")
    print(f"   平均死亡者数: {statistics.mean(total_deaths):.1f}人")
    
    # 死因統計
    all_death_causes = {}
    for result in results:
        for cause, count in result['death_causes'].items():
            if cause not in all_death_causes:
                all_death_causes[cause] = []
            all_death_causes[cause].append(count)
    
    print(f"\n💀 死因統計:")
    for cause, counts in all_death_causes.items():
        avg_deaths = statistics.mean(counts) if counts else 0
        total_occurrences = len([r for r in results if cause in r['death_causes']])
        print(f"   {cause}: 平均{avg_deaths:.1f}人/回, {total_occurrences}/{len(results)}回で発生")
    
    # 生存者タイプ統計
    all_survivor_types = {}
    for result in results:
        for npc_type, count in result['survivor_types'].items():
            if npc_type not in all_survivor_types:
                all_survivor_types[npc_type] = []
            all_survivor_types[npc_type].append(count)
    
    print(f"\n🏆 生存者タイプ統計:")
    for npc_type, counts in all_survivor_types.items():
        avg_survivors = statistics.mean(counts) if counts else 0
        survival_frequency = len([r for r in results if npc_type in r['survivor_types']])
        print(f"   {npc_type}: 平均{avg_survivors:.1f}人/回, {survival_frequency}/{len(results)}回で生存")
    
    # 健康状態統計
    print(f"\n💪 生存者健康状態統計:")
    health_metrics = ['hunger', 'thirst', 'fatigue', 'curiosity', 'sociability']
    
    for metric in health_metrics:
        all_values = []
        for result in results:
            all_values.extend(result['survivor_health'][metric])
        
        if all_values:
            avg_value = statistics.mean(all_values)
            std_value = statistics.stdev(all_values) if len(all_values) > 1 else 0
            print(f"   {metric}: {avg_value:.1f} (±{std_value:.1f})")
    
    # SSD決定統計
    print(f"\n🧠 SSD決定統計:")
    total_normal = sum(r['ssd_stats']['normal_decisions'] for r in results)
    total_leap = sum(r['ssd_stats']['leap_decisions'] for r in results)
    total_decisions = sum(r['ssd_stats']['total_decisions'] for r in results)
    
    if total_decisions > 0:
        print(f"   通常決定: {total_normal} ({total_normal/total_decisions*100:.1f}%)")
        print(f"   跳躍決定: {total_leap} ({total_leap/total_decisions*100:.1f}%)")
        print(f"   総決定数: {total_decisions}")
    
    # 実行時間統計
    execution_times = [r['execution_time'] for r in results]
    print(f"\n⏱️  実行時間統計:")
    print(f"   平均実行時間: {statistics.mean(execution_times):.1f}秒")
    print(f"   最速実行時間: {min(execution_times):.1f}秒")
    print(f"   最遅実行時間: {max(execution_times):.1f}秒")
    
    # 集団死パターンの特徴
    print(f"\n🔍 集団死パターンの特徴:")
    
    # 完全絶滅の回数
    complete_extinctions = len([r for r in results if r['survivors'] == 0])
    print(f"   完全絶滅: {complete_extinctions}/{len(results)}回 ({complete_extinctions/len(results)*100:.1f}%)")
    
    # 高生存率の回数
    high_survival = len([r for r in results if r['survival_rate'] > 0.5])
    print(f"   高生存率(>50%): {high_survival}/{len(results)}回 ({high_survival/len(results)*100:.1f}%)")
    
    # 結果保存
    with open('mass_death_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細結果を mass_death_analysis_results.json に保存しました")
    print("=" * 80)

if __name__ == "__main__":
    analyze_mass_death_patterns()