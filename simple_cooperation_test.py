#!/usr/bin/env python3
"""
簡易協力分析 - main.pyを複数回実行して結果を集計
"""

import subprocess
import re
import time

def analyze_cooperation():
    """協力行動の発生を分析"""
    
    results = []
    
    print("🤝 協力行動調査開始 - 10回連続実行")
    print("=" * 50)
    
    for run in range(1, 11):
        print(f"\n🔍 RUN {run}/10", end=" ")
        
        try:
            # main.pyを実行してログを取得
            result = subprocess.run(
                ['python', 'main.py'], 
                capture_output=True, 
                text=True, 
                timeout=120  # 2分でタイムアウト
            )
            
            output = result.stdout + result.stderr
            
            # パターン検索
            group_attempts = len(re.findall(r'GROUP HUNT ATTEMPT', output))
            group_formed = len(re.findall(r'GROUP HUNT FORMED', output))
            group_success = len(re.findall(r'GROUP HUNT SUCCESS', output))
            solo_attempts = len(re.findall(r'HUNT ATTEMPT.*solo hunt', output))
            solo_success = len(re.findall(r'SOLO HUNT SUCCESS', output))
            final_survivors = re.findall(r'T\d+.*👥(\d+) survivors', output)
            
            last_survivor_count = int(final_survivors[-1]) if final_survivors else 0
            
            run_result = {
                'run': run,
                'group_attempts': group_attempts,
                'group_formed': group_formed, 
                'group_success': group_success,
                'solo_attempts': solo_attempts,
                'solo_success': solo_success,
                'final_survivors': last_survivor_count
            }
            
            results.append(run_result)
            
            print(f"✅ 群れ:{group_attempts}回試行, 形成:{group_formed}回, 成功:{group_success}回, 単独:{solo_success}回成功, 生存者:{last_survivor_count}人")
            
        except subprocess.TimeoutExpired:
            print("⏰ タイムアウト")
        except Exception as e:
            print(f"❌ エラー: {e}")
        
        time.sleep(1)  # 1秒待機
    
    # 統計計算
    print("\n" + "=" * 60)
    print("🎯 協力行動分析結果")
    print("=" * 60)
    
    if results:
        total_group_attempts = sum(r['group_attempts'] for r in results)
        total_group_formed = sum(r['group_formed'] for r in results) 
        total_group_success = sum(r['group_success'] for r in results)
        total_solo_attempts = sum(r['solo_attempts'] for r in results)
        total_solo_success = sum(r['solo_success'] for r in results)
        avg_survivors = sum(r['final_survivors'] for r in results) / len(results)
        
        print(f"📊 実行回数: {len(results)}/10")
        print(f"📊 群れ狩り試行: {total_group_attempts}回")
        print(f"📊 群れ狩り形成: {total_group_formed}回")
        print(f"📊 群れ狩り成功: {total_group_success}回")
        print(f"📊 単独狩り試行: {total_solo_attempts}回")
        print(f"📊 単独狩り成功: {total_solo_success}回")
        print(f"📊 平均最終生存者: {avg_survivors:.1f}人")
        
        if total_group_attempts > 0:
            group_formation_rate = total_group_formed / total_group_attempts
            print(f"🎯 群れ形成率: {group_formation_rate:.1%}")
            
            if total_group_formed > 0:
                group_success_rate = total_group_success / total_group_formed
                print(f"🎯 群れ成功率: {group_success_rate:.1%}")
        else:
            print("⚠️  群れ狩りは一度も試行されませんでした")
        
        if total_solo_attempts > 0:
            solo_success_rate = total_solo_success / total_solo_attempts
            print(f"🏹 単独成功率: {solo_success_rate:.1%}")
        
        total_hunts = total_group_attempts + total_solo_attempts
        if total_hunts > 0:
            cooperation_ratio = total_group_attempts / total_hunts
            print(f"🤝 協力試行率: {cooperation_ratio:.1%}")
    
    return results

if __name__ == "__main__":
    analyze_cooperation()