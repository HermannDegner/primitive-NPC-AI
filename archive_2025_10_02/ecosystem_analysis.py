#!/usr/bin/env python3
"""
エコシステム分析：10回シミュレーション実行
捕食者狩り、動物エコシステム、狩場競合の効果を分析
"""

import pandas as pd
from simulation import run_simulation, analyze_results

def run_ecosystem_analysis(runs=10, ticks=500):
    """エコシステム機能の10回分析"""
    print("=== エコシステム分析：10回シミュレーション ===")
    print("新機能: 捕食者狩り、動物エコシステム、狩場競合")
    print()
    
    all_results = []
    
    for run in range(1, runs + 1):
        print(f"--- Run {run}/10 ---")
        
        try:
            # シミュレーション実行
            final_npcs, df_logs, df_weather, df_ecosystem = run_simulation(ticks)
            
            # 生存者分析
            survivors = [npc for npc in final_npcs if npc.alive]
            survivor_count = len(survivors)
            
            # 死亡者分析
            deaths = [npc for npc in final_npcs if not npc.alive]
            death_analysis = {}
            
            for npc in deaths:
                personality = npc.name.split('_')[0]
                if personality not in death_analysis:
                    death_analysis[personality] = []
                death_analysis[personality].append(npc.name)
            
            # 捕食者狩り分析
            predator_hunts = df_ecosystem[df_ecosystem['event'] == 'predator_hunting'] if not df_ecosystem.empty else pd.DataFrame()
            total_predator_hunts = len(predator_hunts)
            successful_predator_hunts = len(predator_hunts[predator_hunts['success'] == True]) if not predator_hunts.empty else 0
            predator_hunt_casualties = predator_hunts['casualties'].sum() if not predator_hunts.empty else 0
            predator_hunt_injured = predator_hunts['injured'].sum() if not predator_hunts.empty else 0
            
            # 捕食者による動物狩り分析
            predator_prey_hunts = df_ecosystem[df_ecosystem['event'] == 'predator_hunts_prey'] if not df_ecosystem.empty else pd.DataFrame()
            total_predator_prey_hunts = len(predator_prey_hunts)
            total_prey_killed = predator_prey_hunts['prey_count'].sum() if not predator_prey_hunts.empty else 0
            
            # 捕食者警戒経験分析
            predator_awareness_stats = {}
            for npc in final_npcs:
                if npc.alive:
                    awareness_exp = npc.experience.get('predator_awareness', 0.0)
                    predator_awareness_stats[npc.name] = {
                        'awareness_experience': awareness_exp,
                        'predator_encounters': getattr(npc, 'predator_encounters', 0),
                        'predator_escapes': getattr(npc, 'predator_escapes', 0),
                        'escape_rate': getattr(npc, 'predator_escapes', 0) / max(1, getattr(npc, 'predator_encounters', 1))
                    }
            
            # 最終環境状態
            final_predators = df_weather.iloc[-1]['predators'] if not df_weather.empty else 0
            final_prey = df_weather.iloc[-1]['prey_animals'] if not df_weather.empty else 0
            
            run_result = {
                'run': run,
                'survivors': survivor_count,
                'deaths': len(deaths),
                'death_breakdown': death_analysis,
                'predator_hunts_attempted': total_predator_hunts,
                'predator_hunts_successful': successful_predator_hunts,
                'predator_hunt_success_rate': successful_predator_hunts / max(1, total_predator_hunts),
                'predator_hunt_casualties': predator_hunt_casualties,
                'predator_hunt_injured': predator_hunt_injured,
                'predator_prey_hunts': total_predator_prey_hunts,
                'total_prey_killed_by_predators': total_prey_killed,
                'final_predators': final_predators,
                'final_prey': final_prey,
                'predator_awareness_stats': predator_awareness_stats
            }
            
            all_results.append(run_result)
            
            # 実行結果サマリー
            print(f"  生存者: {survivor_count}/16")
            print(f"  捕食者狩り: {total_predator_hunts}回試行, {successful_predator_hunts}回成功")
            if total_predator_hunts > 0:
                print(f"  成功率: {successful_predator_hunts/total_predator_hunts*100:.1f}%")
                print(f"  犠牲者: {predator_hunt_casualties}人, 負傷者: {predator_hunt_injured}人")
            print(f"  捕食者による動物狩り: {total_predator_prey_hunts}回, {total_prey_killed}匹捕獲")
            print()
            
        except Exception as e:
            print(f"  Run {run} でエラー発生: {e}")
            continue
    
    # 総合分析
    print("\n=== 総合分析結果 ===")
    
    if all_results:
        # 生存率分析
        avg_survivors = sum(r['survivors'] for r in all_results) / len(all_results)
        print(f"平均生存者数: {avg_survivors:.1f}/16 ({avg_survivors/16*100:.1f}%)")
        
        # 捕食者狩り統計
        total_hunt_attempts = sum(r['predator_hunts_attempted'] for r in all_results)
        total_hunt_successes = sum(r['predator_hunts_successful'] for r in all_results)
        total_hunt_casualties = sum(r['predator_hunt_casualties'] for r in all_results)
        total_hunt_injured = sum(r['predator_hunt_injured'] for r in all_results)
        
        if total_hunt_attempts > 0:
            print(f"\n捕食者狩り統計:")
            print(f"  総試行回数: {total_hunt_attempts}")
            print(f"  総成功回数: {total_hunt_successes}")
            print(f"  平均成功率: {total_hunt_successes/total_hunt_attempts*100:.1f}%")
            print(f"  総犠牲者: {total_hunt_casualties}人")
            print(f"  総負傷者: {total_hunt_injured}人")
            print(f"  危険度: {(total_hunt_casualties + total_hunt_injured)/total_hunt_attempts*100:.1f}%")
        
        # エコシステム統計
        total_predator_prey_hunts = sum(r['predator_prey_hunts'] for r in all_results)
        total_prey_killed = sum(r['total_prey_killed_by_predators'] for r in all_results)
        
        print(f"\nエコシステム統計:")
        print(f"  捕食者による動物狩り: {total_predator_prey_hunts}回")
        print(f"  捕獲された動物: {total_prey_killed}匹")
        
        # 性格別死亡率分析
        death_by_personality = {}
        for result in all_results:
            for personality, deaths in result['death_breakdown'].items():
                if personality not in death_by_personality:
                    death_by_personality[personality] = 0
                death_by_personality[personality] += len(deaths)
        
        print(f"\n性格別死亡率:")
        for personality, death_count in sorted(death_by_personality.items()):
            death_rate = death_count / (len(all_results) * 2) * 100  # 各性格2人ずつ
            print(f"  {personality}: {death_count}/{len(all_results)*2} ({death_rate:.1f}%)")
        
        # 捕食者警戒経験の効果
        print(f"\n捕食者警戒経験の効果:")
        all_awareness_stats = []
        for result in all_results:
            all_awareness_stats.extend(result['predator_awareness_stats'].values())
        
        if all_awareness_stats:
            avg_awareness = sum(s['awareness_experience'] for s in all_awareness_stats) / len(all_awareness_stats)
            avg_encounters = sum(s['predator_encounters'] for s in all_awareness_stats) / len(all_awareness_stats)
            avg_escapes = sum(s['predator_escapes'] for s in all_awareness_stats) / len(all_awareness_stats)
            avg_escape_rate = sum(s['escape_rate'] for s in all_awareness_stats) / len(all_awareness_stats)
            
            print(f"  平均警戒経験: {avg_awareness:.3f}")
            print(f"  平均遭遇回数: {avg_encounters:.1f}")
            print(f"  平均逃走回数: {avg_escapes:.1f}")
            print(f"  平均逃走成功率: {avg_escape_rate*100:.1f}%")
    
    return all_results

if __name__ == "__main__":
    results = run_ecosystem_analysis(10, 500)