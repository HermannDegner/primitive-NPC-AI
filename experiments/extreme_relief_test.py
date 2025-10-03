#!/usr/bin/env python3
"""
Extreme Environment Relief Test - 極限環境圧緩和テスト
"""

def run_extreme_relief_test():
    """極限環境圧緩和テスト実行"""
    
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        
        # 短期テスト（100ティック）で効果確認
        test_ticks = 100
        
        print(f"Starting EXTREME environment relief test ({test_ticks} ticks)")
        print("Testing drastically improved survival conditions...")
        print()
        
        # シミュレーション実行
        results, deaths, events, analysis = run_ssd_integrated_simulation(max_ticks=test_ticks)
        
        print("=" * 60)
        print("EXTREME ENVIRONMENT RELIEF TEST COMPLETED")
        print("=" * 60)
        
        # 結果分析
        print("\nEXTREME RELIEF EFFECTIVENESS:")
        print(f"   Test Duration: {test_ticks} ticks")
        print(f"   Total Deaths: {len(deaths)}")
        
        # 生存率計算
        if results and 'roster' in results:
            initial_count = len(results['roster'])
            survivor_count = sum(1 for npc in results['roster'].values() if npc.get('is_alive', True))
            survival_rate = (survivor_count / initial_count) * 100
            print(f"   Survival Rate: {survivor_count}/{initial_count} ({survival_rate:.1f}%)")
            
            # 改善度評価
            if survival_rate == 100:
                improvement = "PERFECT - NO DEATHS!"
            elif survival_rate >= 90:
                improvement = "EXCELLENT RELIEF"
            elif survival_rate >= 75:
                improvement = "GOOD RELIEF"
            else:
                improvement = "NEEDS MORE ADJUSTMENT"
                
            print(f"   Relief Effectiveness: {improvement}")
        
        # 死亡時期分析
        if len(deaths) > 0:
            print(f"\nDEATH ANALYSIS:")
            death_ticks = []
            for death in deaths:
                if isinstance(death, str) and "T" in death and "died" in death:
                    try:
                        tick_part = death.split("T")[1].split(":")[0]
                        death_ticks.append(int(tick_part))
                    except:
                        pass
            
            if death_ticks:
                first_death = min(death_ticks)
                print(f"   First death at: Tick {first_death}")
                
                # 前回は51ティックで最初の死亡
                if first_death > 51:
                    improvement_factor = first_death / 51
                    print(f"   First death delayed by: {improvement_factor:.1f}x")
                else:
                    print(f"   First death still too early")
            
            # 死因分析
            dehydration_count = sum(1 for d in deaths if isinstance(d, str) and "脱水" in d)
            starvation_count = sum(1 for d in deaths if isinstance(d, str) and "飢餓" in d)
            print(f"   Dehydration deaths: {dehydration_count}")
            print(f"   Starvation deaths: {starvation_count}")
        else:
            print(f"\nDEATH ANALYSIS:")
            print(f"   PERFECT RESULT: No deaths in {test_ticks} ticks!")
            print(f"   Environment relief: EXTREMELY EFFECTIVE")
        
        return len(deaths) == 0  # Perfect if no deaths
        
    except Exception as e:
        print(f"Extreme relief test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== EXTREME Environmental Pressure Relief Test ===")
    print()
    print("ADDITIONAL EXTREME RELIEF MEASURES:")
    print("- Water recovery: +71% (35->60 per drink)")
    print("- Death threshold: thirst 220->300 (+36%)")  
    print("- Early water seeking: thirst 120->70 (-42%)")
    print("- Season temp stress: 5->2 reduction (-60%)")
    print("- Recovery floor: 20->50 (+150%)")
    print()
    
    success = run_extreme_relief_test()
    if success:
        print("\n🎉 PERFECT ENVIRONMENT ACHIEVED!")
    else:
        print("\n⚠️ Still needs more adjustment.")