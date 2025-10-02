#!/usr/bin/env python3
"""
簡単な10回連続実行スクリプト
"""

import os
import subprocess
import json
from datetime import datetime

def run_10_simulations():
    """main.pyを10回実行して結果を記録"""
    
    print("🔬 10回連続実行による集団死分析開始")
    print("=" * 60)
    
    results = []
    
    for i in range(1, 11):
        print(f"\n🧪 実行 {i}/10 開始...")
        
        try:
            # main.pyを実行
            result = subprocess.run(['python', 'main.py'], 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8')
            
            output = result.stdout
            
            # 出力から生存者数を抽出
            survivors = 0
            total_npcs = 16  # デフォルト
            
            lines = output.split('\n')
            for line in lines:
                if 'survivors' in line.lower() and 'exploring' in line.lower():
                    # 例: "👥2 survivors, 🔍0 exploring" の形式を解析
                    parts = line.split('👥')
                    if len(parts) > 1:
                        survivor_part = parts[1].split(' ')[0]
                        try:
                            survivors = int(survivor_part)
                        except:
                            pass
                elif 'Final Survivors' in line:
                    # 例: "Final Survivors after FULL SEASONAL CYCLE: 2/2"
                    parts = line.split(': ')
                    if len(parts) > 1:
                        survivor_info = parts[1].split('/')
                        if len(survivor_info) >= 2:
                            try:
                                survivors = int(survivor_info[0])
                                total_npcs = int(survivor_info[1])
                            except:
                                pass
            
            # 死因分析（簡易版）
            dehydration_deaths = output.count('dehydration')
            starvation_deaths = output.count('starvation')
            
            # 結果記録
            run_result = {
                'run_id': i,
                'survivors': survivors,
                'total_npcs': total_npcs,
                'deaths': total_npcs - survivors,
                'survival_rate': survivors / total_npcs if total_npcs > 0 else 0,
                'dehydration_deaths': dehydration_deaths,
                'starvation_deaths': starvation_deaths,
                'output_length': len(output),
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(run_result)
            
            print(f"✅ 実行 {i} 完了 - 生存者: {survivors}/{total_npcs} ({survivors/total_npcs*100:.1f}%)")
            print(f"   脱水死: {dehydration_deaths}, 餓死: {starvation_deaths}")
            
        except Exception as e:
            print(f"❌ 実行 {i} でエラー: {e}")
            continue
    
    # 統計分析
    print("\n" + "=" * 60)
    print("📊 集団死パターン分析結果")
    print("=" * 60)
    
    if not results:
        print("❌ 分析対象データなし")
        return
    
    # 基本統計
    survival_rates = [r['survival_rate'] for r in results]
    survivors_counts = [r['survivors'] for r in results]
    deaths_counts = [r['deaths'] for r in results]
    
    print(f"\n🎯 基本統計 (n={len(results)}):")
    print(f"   平均生存率: {sum(survival_rates)/len(survival_rates)*100:.1f}%")
    print(f"   最高生存率: {max(survival_rates)*100:.1f}%")
    print(f"   最低生存率: {min(survival_rates)*100:.1f}%")
    print(f"   平均生存者数: {sum(survivors_counts)/len(survivors_counts):.1f}人")
    
    # 死因統計
    total_dehydration = sum(r['dehydration_deaths'] for r in results)
    total_starvation = sum(r['starvation_deaths'] for r in results)
    
    print(f"\n💀 死因統計:")
    print(f"   脱水死: 合計{total_dehydration}回検出")
    print(f"   餓死: 合計{total_starvation}回検出")
    
    # 生存パターン
    complete_extinctions = len([r for r in results if r['survivors'] == 0])
    high_survival = len([r for r in results if r['survival_rate'] > 0.5])
    perfect_survival = len([r for r in results if r['survival_rate'] == 1.0])
    
    print(f"\n🔍 生存パターン:")
    print(f"   完全絶滅: {complete_extinctions}/{len(results)}回 ({complete_extinctions/len(results)*100:.1f}%)")
    print(f"   高生存率(>50%): {high_survival}/{len(results)}回 ({high_survival/len(results)*100:.1f}%)")
    print(f"   完全生存: {perfect_survival}/{len(results)}回 ({perfect_survival/len(results)*100:.1f}%)")
    
    # 詳細結果表示
    print(f"\n📋 各実行の詳細:")
    for result in results:
        print(f"   実行{result['run_id']:2d}: {result['survivors']:2d}/{result['total_npcs']}人生存 "
              f"({result['survival_rate']*100:5.1f}%) - "
              f"脱水:{result['dehydration_deaths']:2d}, 餓死:{result['starvation_deaths']:2d}")
    
    # 結果保存
    with open('simulation_results_10runs.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細結果を simulation_results_10runs.json に保存しました")
    print("=" * 60)

if __name__ == "__main__":
    run_10_simulations()