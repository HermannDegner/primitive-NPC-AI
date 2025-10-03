#!/usr/bin/env python3
"""
Experience Learning System Test - 経験学習システムテスト
"""

def run_experience_learning_test():
    """経験学習システムテスト実行"""
    
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        
        # 学習効果確認テスト（200ティック）
        test_ticks = 200
        
        print(f"Starting experience learning system test ({test_ticks} ticks)")
        print("Testing adaptive survival behavior with learning...")
        print()
        
        # シミュレーション実行
        results, deaths, events, analysis = run_ssd_integrated_simulation(max_ticks=test_ticks)
        
        print("=" * 60)
        print("EXPERIENCE LEARNING TEST COMPLETED")
        print("=" * 60)
        
        # 結果分析
        print("\nLEARNING EFFECTIVENESS:")
        print(f"   Test Duration: {test_ticks} ticks")
        print(f"   Total Deaths: {len(deaths)}")
        
        # 生存率計算
        if results and 'roster' in results:
            initial_count = len(results['roster'])
            survivor_count = sum(1 for npc in results['roster'].values() if npc.get('is_alive', True))
            survival_rate = (survivor_count / initial_count) * 100
            print(f"   Survival Rate: {survivor_count}/{initial_count} ({survival_rate:.1f}%)")
            
            # 学習効果評価
            if survival_rate == 100:
                learning_effect = "PERFECT LEARNING"
            elif survival_rate >= 75:
                learning_effect = "EXCELLENT LEARNING"
            elif survival_rate >= 50:
                learning_effect = "GOOD LEARNING"
            elif survival_rate >= 25:
                learning_effect = "MODERATE LEARNING"
            else:
                learning_effect = "LEARNING NEEDS MORE TIME"
                
            print(f"   Learning Effect: {learning_effect}")
        
        # 学習進歩の分析（ログから推測）
        learning_logs = [event for event in events if isinstance(event, str) and 
                        ("learned" in event.lower() or "Learning" in event or "💡" in event)]
        
        print(f"\nLEARNING ACTIVITY:")
        print(f"   Learning events detected: {len(learning_logs)}")
        
        if learning_logs:
            print("   Sample learning events:")
            for log in learning_logs[:5]:
                print(f"     {log}")
        
        # 死亡分析
        if len(deaths) > 0:
            print(f"\nDEATH ANALYSIS:")
            
            first_death_tick = None
            for death in deaths:
                if isinstance(death, str) and "died" in death and "T" in death:
                    try:
                        tick_part = death.split("T")[1].split(":")[0]
                        first_death_tick = int(tick_part)
                        break
                    except:
                        pass
            
            print(f"   First death at: Tick {first_death_tick if first_death_tick else 'N/A'}")
            
            # 前回結果との比較（T121が基準）
            if first_death_tick and first_death_tick > 121:
                improvement = (first_death_tick - 121) / 121 * 100
                print(f"   Learning improvement: +{improvement:.1f}%")
            elif first_death_tick:
                decline = (121 - first_death_tick) / 121 * 100
                print(f"   Performance decline: -{decline:.1f}% (learning still adapting)")
            
            dehydration_deaths = sum(1 for d in deaths if isinstance(d, str) and "脱水" in d)
            print(f"   Dehydration deaths: {dehydration_deaths}")
        else:
            print(f"\nDEATH ANALYSIS:")
            print(f"   PERFECT: No deaths - learning system highly effective!")
        
        return len(deaths) == 0  # Perfect if no deaths
        
    except Exception as e:
        print(f"Experience learning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Experience Learning System Test ===")
    print()
    print("LEARNING FEATURES IMPLEMENTED:")
    print("- Adaptive water urgency thresholds")
    print("- Adaptive food urgency thresholds")  
    print("- Success/failure experience recording")
    print("- Crisis survival experience logging")
    print("- Dynamic threshold adjustment (±5-20)")
    print("- Learning-based early warning system")
    print("- SSD+Learning hybrid prediction")
    print()
    
    success = run_experience_learning_test()
    if success:
        print("\n🎓 EXPERIENCE LEARNING SYSTEM PERFECTED!")
    else:
        print("\n📚 Learning system still adapting - needs more experience.")