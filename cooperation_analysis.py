#!/usr/bin/env python3
"""
協力行動調査用の軽量シミュレーション
群れ狩りの発生パターンを分析
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def run_cooperation_analysis():
    """協力行動の分析用短縮シミュレーション"""
    from enhanced_simulation import EnhancedSSSimulation
    import random
    
    cooperation_stats = {
        'group_hunt_attempts': 0,
        'group_hunt_successes': 0,
        'solo_hunt_attempts': 0,
        'solo_hunt_successes': 0,
        'runs_completed': 0
    }
    
    print("🤝 協力行動調査開始 - 10回連続実行")
    print("=" * 50)
    
    for run in range(1, 11):
        print(f"\n🔍 RUN {run}/10")
        
        try:
            # シード変更
            random.seed(run * 42)
            
            # 短時間シミュレーション (200ターンまで)
            sim = EnhancedSSSimulation(
                n_agents=16, 
                grid_size=90, 
                max_ticks=200,  # 短縮
                n_berry=0,
                n_hunt=12, 
                n_water=20,
                n_caves=6
            )
            
            # 群れ狩りカウンター追加
            group_hunts_this_run = 0
            solo_hunts_this_run = 0
            
            # デバッグ出力をカウントに変換
            original_print = print
            
            def counting_print(*args, **kwargs):
                nonlocal group_hunts_this_run, solo_hunts_this_run
                msg = ' '.join(str(arg) for arg in args)
                if "GROUP HUNT ATTEMPT" in msg:
                    cooperation_stats['group_hunt_attempts'] += 1
                    group_hunts_this_run += 1
                elif "GROUP HUNT SUCCESS" in msg:
                    cooperation_stats['group_hunt_successes'] += 1
                elif "SOLO HUNT SUCCESS" in msg:
                    cooperation_stats['solo_hunt_successes'] += 1
                    solo_hunts_this_run += 1
                elif "HUNT ATTEMPT" in msg and "solo hunt" in msg:
                    cooperation_stats['solo_hunt_attempts'] += 1
                # 重要なメッセージのみ出力
                if any(key in msg for key in ["GROUP HUNT", "survivors", "DEATH"]):
                    original_print(*args, **kwargs)
            
            print = counting_print
            
            # シミュレーション実行
            from enhanced_simulation import run_enhanced_ssd_simulation
            run_enhanced_ssd_simulation(ticks=200)
            
            print = original_print  # 復元
            
            print(f"  👥 群れ狩り試行: {group_hunts_this_run}")
            print(f"  🏹 単独狩り: {solo_hunts_this_run}")
            
            cooperation_stats['runs_completed'] += 1
            
        except Exception as e:
            print(f"  ❌ Run {run} エラー: {e}")
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("🎯 協力行動分析結果")
    print("=" * 50)
    print(f"完了したRun数: {cooperation_stats['runs_completed']}/10")
    print(f"群れ狩り試行総数: {cooperation_stats['group_hunt_attempts']}")
    print(f"群れ狩り成功数: {cooperation_stats['group_hunt_successes']}")
    print(f"単独狩り試行総数: {cooperation_stats['solo_hunt_attempts']}")
    print(f"単独狩り成功数: {cooperation_stats['solo_hunt_successes']}")
    
    if cooperation_stats['group_hunt_attempts'] > 0:
        group_success_rate = cooperation_stats['group_hunt_successes'] / cooperation_stats['group_hunt_attempts']
        print(f"群れ狩り成功率: {group_success_rate:.1%}")
    else:
        print("群れ狩りは発生しませんでした")
    
    if cooperation_stats['solo_hunt_attempts'] > 0:
        solo_success_rate = cooperation_stats['solo_hunt_successes'] / cooperation_stats['solo_hunt_attempts']
        print(f"単独狩り成功率: {solo_success_rate:.1%}")
    
    total_hunts = cooperation_stats['group_hunt_attempts'] + cooperation_stats['solo_hunt_attempts']
    if total_hunts > 0:
        cooperation_ratio = cooperation_stats['group_hunt_attempts'] / total_hunts
        print(f"協力率: {cooperation_ratio:.1%} ({cooperation_stats['group_hunt_attempts']}/{total_hunts})")
    
    return cooperation_stats

if __name__ == "__main__":
    run_cooperation_analysis()