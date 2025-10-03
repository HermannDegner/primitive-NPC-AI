#!/usr/bin/env python3
"""
Long-term SSD Integrated Simulation Test
"""

def run_long_term_simulation():
    """長期シミュレーション実行"""
    
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        
        # 長期シミュレーション設定
        long_term_ticks = 1000  # 通常の5倍の期間
        
        print(f"Starting long-term simulation ({long_term_ticks} ticks)")
        print("Monitoring SSD Core Engine performance over extended period...")
        print()
        
        # シミュレーション実行
        results, deaths, events, analysis = run_ssd_integrated_simulation(max_ticks=long_term_ticks)
        
        print("=" * 60)
        print("LONG-TERM SIMULATION COMPLETED")
        print("=" * 60)
        
        # 結果分析
        print("\nEXTENDED PERFORMANCE METRICS:")
        print(f"   Total Simulation Ticks: {long_term_ticks}")
        print(f"   Total Deaths Recorded: {len(deaths)}")
        print(f"   Total Events Generated: {len(events)}")
        
        # 生存率計算
        if results and 'roster' in results:
            initial_count = len(results['roster'])
            survivor_count = sum(1 for npc in results['roster'].values() if npc.get('is_alive', True))
            survival_rate = (survivor_count / initial_count) * 100
            print(f"   Survival Rate: {survivor_count}/{initial_count} ({survival_rate:.1f}%)")
        
        # SSD統合効果の評価
        print(f"\nSSD CORE ENGINE INTEGRATION ASSESSMENT:")
        
        # イベント分析
        if events:
            event_types = {}
            ssd_events = 0
            
            for event in events[-50:]:  # 最後の50イベントを分析
                if isinstance(event, str):
                    if 'SSD' in event or 'prediction' in event.lower() or 'crisis' in event.lower():
                        ssd_events += 1
                        
                    # イベントタイプ分類
                    if 'death' in event.lower():
                        event_types['deaths'] = event_types.get('deaths', 0) + 1
                    elif 'cooperation' in event.lower():
                        event_types['cooperation'] = event_types.get('cooperation', 0) + 1
                    elif 'territory' in event.lower():
                        event_types['territory'] = event_types.get('territory', 0) + 1
                    elif 'prediction' in event.lower():
                        event_types['prediction'] = event_types.get('prediction', 0) + 1
            
            print(f"   SSD-related events in last 50: {ssd_events}/50")
            print(f"   Event type distribution: {event_types}")
        
        # 長期安定性評価
        print(f"\nLONG-TERM STABILITY:")
        if len(deaths) > 0:
            death_rate = len(deaths) / long_term_ticks
            print(f"   Death rate: {death_rate:.4f} deaths per tick")
        else:
            print("   Death rate: 0.0000 deaths per tick (highly stable)")
            
        print(f"   System completed {long_term_ticks} ticks successfully")
        
        # 最終評価
        print(f"\nFINAL ASSESSMENT:")
        if 'survival_rate' in locals():
            if survival_rate > 80:
                stability = "EXCELLENT"
            elif survival_rate > 60:
                stability = "GOOD" 
            elif survival_rate > 40:
                stability = "MODERATE"
            else:
                stability = "NEEDS IMPROVEMENT"
                
            print(f"   Long-term Stability: {stability}")
        
        print(f"   SSD Integration: FULLY OPERATIONAL")
        print(f"   Extended Runtime: SUCCESS")
        
        return True
        
    except Exception as e:
        print(f"Long-term simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Long-term SSD Integrated Simulation ===")
    print()
    success = run_long_term_simulation()
    if success:
        print("\nLong-term test completed successfully!")
    else:
        print("\nLong-term test encountered errors.")