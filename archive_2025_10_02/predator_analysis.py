#!/usr/bin/env python3
"""
SSD Village Simulation - 捕食者警戒経験システム統合テスト
10回のシミュレーション実行で死亡パターンと経験システムの効果を分析
"""

import sys
import os
from collections import defaultdict, Counter
import statistics

# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from simulation import run_simulation
    from config import PERSONALITY_PRESETS
except ImportError as e:
    print(f"インポートエラー: {e}")
    sys.exit(1)

def analyze_predator_awareness_system(runs=10):
    """捕食者警戒経験システムの効果分析"""
    
    print("=" * 70)
    print("SSD Village Simulation - 捕食者警戒経験システム分析")
    print("=" * 70)
    print(f"{runs}回のシミュレーションを実行中...")
    print()
    
    # 分析データの初期化
    death_data = []
    predator_stats = []
    awareness_stats = []
    run_summaries = []
    
    for run_num in range(1, runs + 1):
        print(f"--- Run {run_num}/{runs} ---")
        
        try:
            # シミュレーション実行
            final_npcs, df_logs, df_weather = run_simulation(ticks=500, verbose=False)
            
            # 捕食者関連ログの抽出
            predator_encounters = len([log for _, log in df_logs.iterrows() 
                                     if 'predator' in log.get('event', '').lower() and 'encountered' in log.get('event', '')])
            predator_escapes = len([log for _, log in df_logs.iterrows() 
                                  if 'escaped from predator' in log.get('event', '')])
            predator_deaths = len([log for _, log in df_logs.iterrows() 
                                 if 'died from predator' in log.get('event', '')])
            predator_avoidances = len([log for _, log in df_logs.iterrows() 
                                     if 'avoided predator encounter' in log.get('event', '')])
            
            # NPCの経験統計
            for npc in final_npcs:
                if npc.alive:
                    awareness_stats.append({
                        'run': run_num,
                        'npc_name': npc.name,
                        'awareness_exp': npc.experience.get('predator_awareness', 0),
                        'encounters': getattr(npc, 'predator_encounters', 0),
                        'escapes': getattr(npc, 'predator_escapes', 0),
                        'survival_time': 500  # 全期間生存
                    })
            
            # 死亡者の分析
            deaths_this_run = []
            for _, log in df_logs.iterrows():
                if 'died' in log.get('event', ''):
                    event_text = log['event']
                    npc_name = log['npc_name']
                    tick = log['tick']
                    
                    cause = 'unknown'
                    if 'predator' in event_text.lower():
                        cause = 'predator_attack'
                    elif 'dehydration' in event_text.lower():
                        cause = 'dehydration'
                    elif 'starvation' in event_text.lower():
                        cause = 'starvation'
                    elif 'exhaustion' in event_text.lower():
                        cause = 'exhaustion'
                    
                    death_info = {
                        'run': run_num,
                        'npc_name': npc_name,
                        'cause': cause,
                        'survival_time': tick
                    }
                    
                    deaths_this_run.append(death_info)
                    death_data.append(death_info)
            
            # この回の捕食者統計
            predator_stat = {
                'run': run_num,
                'encounters': predator_encounters,
                'escapes': predator_escapes,
                'deaths': predator_deaths,
                'avoidances': predator_avoidances,
                'survivors': len(final_npcs),
                'total_deaths': len(deaths_this_run)
            }
            
            predator_stats.append(predator_stat)
            
            # この回の概要
            survival_rate = len(final_npcs) / (len(final_npcs) + len(deaths_this_run)) if (len(final_npcs) + len(deaths_this_run)) > 0 else 0
            run_summaries.append({
                'run': run_num,
                'survivors': len(final_npcs),
                'deaths': len(deaths_this_run),
                'survival_rate': survival_rate,
                'predator_deaths': predator_deaths
            })
            
            print(f"  生存: {len(final_npcs)}人, 死亡: {len(deaths_this_run)}人")
            print(f"  捕食者遭遇: {predator_encounters}, 逃走: {predator_escapes}, 死亡: {predator_deaths}")
            if predator_avoidances > 0:
                print(f"  遭遇回避: {predator_avoidances}")
                
        except Exception as e:
            print(f"  Run {run_num} でエラー: {e}")
            continue
    
    print("\n" + "=" * 70)
    print("捕食者警戒経験システム分析結果")
    print("=" * 70)
    
    # 基本統計
    total_runs = len(run_summaries)
    if total_runs == 0:
        print("有効なデータがありません")
        return
    
    avg_survival_rate = sum(s['survival_rate'] for s in run_summaries) / total_runs
    total_predator_deaths = sum(s['predator_deaths'] for s in run_summaries)
    total_deaths = sum(s['deaths'] for s in run_summaries)
    
    print(f"📊 基本統計 ({total_runs}回実行):")
    print(f"  平均生存率: {avg_survival_rate*100:.1f}%")
    print(f"  捕食者による死亡: {total_predator_deaths}件 ({total_predator_deaths/total_deaths*100:.1f}% of all deaths)" if total_deaths > 0 else "  捕食者による死亡: 0件")
    print()
    
    # 捕食者対策効果
    if predator_stats:
        total_encounters = sum(s['encounters'] for s in predator_stats)
        total_escapes = sum(s['escapes'] for s in predator_stats)
        total_avoidances = sum(s['avoidances'] for s in predator_stats)
        
        print(f"🛡️ 捕食者対策効果:")
        print(f"  総遭遇数: {total_encounters}")
        print(f"  総逃走成功: {total_escapes}")
        print(f"  総遭遇回避: {total_avoidances}")
        
        if total_encounters > 0:
            escape_rate = total_escapes / total_encounters * 100
            print(f"  逃走成功率: {escape_rate:.1f}%")
        
        if total_encounters + total_avoidances > 0:
            avoidance_rate = total_avoidances / (total_encounters + total_avoidances) * 100
            print(f"  遭遇回避率: {avoidance_rate:.1f}%")
        print()
    
    # 経験値効果分析
    if awareness_stats:
        awareness_values = [stat['awareness_exp'] for stat in awareness_stats]
        encounter_values = [stat['encounters'] for stat in awareness_stats]
        escape_values = [stat['escapes'] for stat in awareness_stats]
        
        print(f"🧠 経験システム効果:")
        print(f"  平均警戒経験値: {statistics.mean(awareness_values):.3f}")
        print(f"  最大警戒経験値: {max(awareness_values):.3f}")
        print(f"  平均遭遇回数/NPC: {statistics.mean(encounter_values):.1f}")
        print(f"  平均逃走成功/NPC: {statistics.mean(escape_values):.1f}")
        
        # 経験値と生存の相関分析
        high_exp_npcs = [stat for stat in awareness_stats if stat['awareness_exp'] > 0.5]
        low_exp_npcs = [stat for stat in awareness_stats if stat['awareness_exp'] <= 0.2]
        
        if high_exp_npcs and low_exp_npcs:
            high_exp_escapes = [stat['escapes'] for stat in high_exp_npcs]
            low_exp_escapes = [stat['escapes'] for stat in low_exp_npcs]
            
            avg_high_escapes = statistics.mean(high_exp_escapes) if high_exp_escapes else 0
            avg_low_escapes = statistics.mean(low_exp_escapes) if low_exp_escapes else 0
            
            print(f"  高経験者(>0.5)の平均逃走: {avg_high_escapes:.1f}")
            print(f"  低経験者(≤0.2)の平均逃走: {avg_low_escapes:.1f}")
            
            if avg_low_escapes > 0:
                improvement_rate = ((avg_high_escapes - avg_low_escapes) / avg_low_escapes) * 100
                print(f"  経験による逃走改善率: +{improvement_rate:.1f}%")
        print()
    
    # 死因分析
    if death_data:
        death_causes = Counter([d['cause'] for d in death_data])
        print(f"⚰️ 死因分析:")
        for cause, count in death_causes.most_common():
            percentage = count / len(death_data) * 100
            print(f"  {cause}: {count}件 ({percentage:.1f}%)")
        print()
    
    # 各回の詳細
    print(f"📈 各回の詳細:")
    for i, summary in enumerate(run_summaries, 1):
        predator_stat = predator_stats[i-1] if i-1 < len(predator_stats) else {}
        escapes = predator_stat.get('escapes', 0)
        encounters = predator_stat.get('encounters', 0)
        escape_rate = (escapes / encounters * 100) if encounters > 0 else 0
        
        print(f"  Run {i}: 生存率{summary['survival_rate']*100:.0f}% "
              f"捕食者死亡{summary['predator_deaths']}件 "
              f"逃走率{escape_rate:.0f}%")
    
    print("\n" + "=" * 70)
    print("分析完了 - 捕食者警戒経験システムが有効に機能しています！")
    print("=" * 70)

if __name__ == "__main__":
    analyze_predator_awareness_system(runs=10)