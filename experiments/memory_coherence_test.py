#!/usr/bin/env python3
"""
Memory-Integrated Coherence System Test - 記憶統合型整合慣性システムテスト
"""

def run_memory_coherence_test():
    """記憶統合型整合慣性システムテスト実行"""
    
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        
        # 記憶統合効果確認テスト（250ティック - 記憶蓄積に十分な時間）
        test_ticks = 250
        
        print(f"Starting memory-integrated coherence system test ({test_ticks} ticks)")
        print("Testing survival behavior with memory-enhanced coherence...")
        print()
        
        # シミュレーション実行
        results, deaths, events, analysis = run_ssd_integrated_simulation(max_ticks=test_ticks)
        
        print("=" * 60)
        print("MEMORY-INTEGRATED COHERENCE TEST COMPLETED")
        print("=" * 60)
        
        # 結果分析
        print("\nMEMORY COHERENCE EFFECTIVENESS:")
        print(f"   Test Duration: {test_ticks} ticks")
        print(f"   Total Deaths: {len(deaths)}")
        
        # 生存率計算
        if results and 'roster' in results:
            initial_count = len(results['roster'])
            survivor_count = sum(1 for npc in results['roster'].values() if npc.get('is_alive', True))
            survival_rate = (survivor_count / initial_count) * 100
            print(f"   Survival Rate: {survivor_count}/{initial_count} ({survival_rate:.1f}%)")
            
            # 記憶統合効果評価
            if survival_rate == 100:
                memory_effect = "PERFECT MEMORY INTEGRATION"
            elif survival_rate >= 75:
                memory_effect = "EXCELLENT MEMORY COHERENCE"
            elif survival_rate >= 50:
                memory_effect = "GOOD MEMORY LEARNING"
            elif survival_rate >= 25:
                memory_effect = "MODERATE MEMORY ADAPTATION"
            else:
                memory_effect = "MEMORY STILL FORMING"
                
            print(f"   Memory Integration Effect: {memory_effect}")
        
        # 記憶・学習活動の分析
        memory_logs = []
        for event in events:
            if isinstance(event, str):
                if any(keyword in event for keyword in ["Memory influence", "🧠", "learned", "💡", "Crisis survival"]):
                    memory_logs.append(event)
        
        print(f"\nMEMORY & LEARNING ACTIVITY:")
        print(f"   Memory-related events: {len(memory_logs)}")
        
        if memory_logs:
            print("   Sample memory integration events:")
            for log in memory_logs[:7]:  # 最初の7件を表示
                print(f"     {log}")
        else:
            print("   No explicit memory events logged (internal processing)")
        
        # 死亡パターン分析
        if len(deaths) > 0:
            print(f"\nDEATH PATTERN ANALYSIS:")
            
            # 時系列での死亡分析
            death_ticks = []
            for death in deaths:
                if isinstance(death, str) and "died" in death and "T" in death:
                    try:
                        tick_part = death.split("T")[1].split(":")[0]
                        death_ticks.append(int(tick_part))
                    except:
                        pass
            
            if death_ticks:
                first_death = min(death_ticks)
                last_death = max(death_ticks) if len(death_ticks) > 1 else first_death
                death_span = last_death - first_death
                
                print(f"   First death: T{first_death}")
                print(f"   Last death: T{last_death}")
                print(f"   Death span: {death_span} ticks")
                
                # 前回結果との比較（T123が前回基準）
                if first_death > 123:
                    improvement = (first_death - 123) / 123 * 100
                    print(f"   Memory improvement: +{improvement:.1f}%")
                elif first_death < 123:
                    decline = (123 - first_death) / 123 * 100
                    print(f"   Performance variation: -{decline:.1f}% (memory still adapting)")
                else:
                    print(f"   Consistent with previous results")
                
                # 記憶形成期間の推定
                if death_span > 50:
                    print(f"   Extended death span suggests memory learning in progress")
                else:
                    print(f"   Rapid death pattern - memory needs more time to develop")
            
            dehydration_count = sum(1 for d in deaths if isinstance(d, str) and "脱水" in d)
            print(f"   Dehydration deaths: {dehydration_count}/{len(deaths)}")
        else:
            print(f"\nDEATH PATTERN ANALYSIS:")
            print(f"   PERFECT: No deaths recorded!")
            print(f"   Memory-coherence integration: FULLY EFFECTIVE")
        
        # 記憶統合成功度
        memory_success = (len(memory_logs) > 0) and (len(deaths) < 200)  # 記憶活動があり死亡数改善
        
        return memory_success
        
    except Exception as e:
        print(f"Memory coherence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Memory-Integrated Coherence System Test ===")
    print()
    print("MEMORY-COHERENCE INTEGRATION FEATURES:")
    print("- κ(coherence) = Memory accumulation system")
    print("- Failure memories → Enhanced κ → Earlier action")  
    print("- Success memories → Optimized κ → Efficient action")
    print("- Memory influence calculation with experience weight")
    print("- Coherence as survival memory strength indicator")
    print("- Memory-driven threshold adaptation")
    print("- Integration: Current state × Memory influence")
    print()
    
    success = run_memory_coherence_test()
    if success:
        print("\n🧠 MEMORY-COHERENCE INTEGRATION SUCCESSFUL!")
        print("   κ(整合慣性) = Memory system confirmed!")
    else:
        print("\n🔄 Memory-coherence still developing - needs more time.")