#!/usr/bin/env python3
"""
SSD Prediction Enhancement Test - SSD予測強化テスト
"""

def run_prediction_enhancement_test():
    """SSD予測強化テスト実行"""
    
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        
        # 予測効果確認テスト（150ティック）
        test_ticks = 150
        
        print(f"Starting SSD prediction enhancement test ({test_ticks} ticks)")
        print("Testing proactive survival behavior with SSD crisis detection...")
        print()
        
        # シミュレーション実行
        results, deaths, events, analysis = run_ssd_integrated_simulation(max_ticks=test_ticks)
        
        print("=" * 60)
        print("SSD PREDICTION ENHANCEMENT TEST COMPLETED")
        print("=" * 60)
        
        # 結果分析
        print("\nPREDICTION EFFECTIVENESS:")
        print(f"   Test Duration: {test_ticks} ticks")
        print(f"   Total Deaths: {len(deaths)}")
        
        # 生存率計算
        if results and 'roster' in results:
            initial_count = len(results['roster'])
            survivor_count = sum(1 for npc in results['roster'].values() if npc.get('is_alive', True))
            survival_rate = (survivor_count / initial_count) * 100
            print(f"   Survival Rate: {survivor_count}/{initial_count} ({survival_rate:.1f}%)")
            
            # 予測効果評価
            if survival_rate == 100:
                prediction_effect = "PERFECT PREDICTION"
            elif survival_rate >= 75:
                prediction_effect = "EXCELLENT PREDICTION"
            elif survival_rate >= 50:
                prediction_effect = "GOOD PREDICTION"
            elif survival_rate >= 25:
                prediction_effect = "MODERATE PREDICTION"
            else:
                prediction_effect = "PREDICTION NEEDS IMPROVEMENT"
                
            print(f"   SSD Prediction Effect: {prediction_effect}")
        
        # 死亡分析
        if len(deaths) > 0:
            print(f"\nDEATH ANALYSIS:")
            
            # 最初の死亡時期
            first_death_tick = None
            dehydration_deaths = 0
            starvation_deaths = 0
            
            for death in deaths:
                if isinstance(death, str) and "died" in death:
                    # 死因分析
                    if "脱水" in death:
                        dehydration_deaths += 1
                    if "飢餓" in death:
                        starvation_deaths += 1
                    
                    # 最初の死亡時期
                    if first_death_tick is None and "T" in death:
                        try:
                            tick_part = death.split("T")[1].split(":")[0]
                            first_death_tick = int(tick_part)
                        except:
                            pass
            
            print(f"   First death at: Tick {first_death_tick if first_death_tick else 'N/A'}")
            print(f"   Dehydration deaths: {dehydration_deaths}")
            print(f"   Starvation deaths: {starvation_deaths}")
            
            # 前回結果との比較（T51が基準）
            if first_death_tick and first_death_tick > 51:
                improvement = (first_death_tick - 51) / 51 * 100
                print(f"   Survival improvement: +{improvement:.1f}%")
            elif first_death_tick:
                print(f"   Still dying too early at T{first_death_tick}")
        else:
            print(f"\nDEATH ANALYSIS:")
            print(f"   PERFECT: No deaths in {test_ticks} ticks!")
            print(f"   SSD prediction: FULLY EFFECTIVE")
        
        return len(deaths) == 0  # Perfect if no deaths
        
    except Exception as e:
        print(f"Prediction enhancement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== SSD Prediction Enhancement Test ===")
    print()
    print("SSD PREDICTION ENHANCEMENTS:")
    print("- Proactive crisis detection: thirst > 50")
    print("- Early water seeking: thirst > 60")  
    print("- SSD prediction frequency: every 10 ticks")
    print("- Crisis response: immediate seek_water()")
    print("- Metabolism rates: further reduced 50%+")
    print("- Prediction debug: enabled every 50 ticks")
    print()
    
    success = run_prediction_enhancement_test()
    if success:
        print("\n🎉 SSD PREDICTION SYSTEM PERFECTED!")
    else:
        print("\n⚠️ Prediction system needs more tuning.")