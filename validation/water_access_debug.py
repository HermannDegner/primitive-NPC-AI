#!/usr/bin/env python3
"""
Water Access Debug System - 水アクセスデバッグシステム  
"""

def run_water_access_debug():
    """水アクセス問題のデバッグ実行"""
    
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        
        # 短期集中デバッグ（NPCが渇きを感じ始める直前まで）
        debug_ticks = 130
        
        print(f"Starting water access debug ({debug_ticks} ticks)")
        print("Investigating water detection vs access capabilities...")
        print()
        
        # デバッグモードでシミュレーション実行
        results, deaths, events, analysis = run_ssd_integrated_simulation(max_ticks=debug_ticks)
        
        print("=" * 60)
        print("WATER ACCESS DEBUG ANALYSIS")
        print("=" * 60)
        
        # 水に関連するイベント抽出
        water_events = []
        movement_events = []
        survival_events = []
        
        for event in events:
            if isinstance(event, str):
                event_lower = event.lower()
                if any(w in event_lower for w in ["water", "drink", "thirst", "渇", "水"]):
                    water_events.append(event)
                elif any(w in event_lower for w in ["move", "移動", "position", "座標"]):
                    movement_events.append(event)
                elif any(w in event_lower for w in ["survival", "生存", "need", "必要"]):
                    survival_events.append(event)
        
        print(f"\nWATER-RELATED ACTIVITY ANALYSIS:")
        print(f"   Water events: {len(water_events)}")
        print(f"   Movement events: {len(movement_events)}")  
        print(f"   Survival events: {len(survival_events)}")
        
        # 水イベントの詳細表示
        if water_events:
            print(f"\n   Water event samples:")
            for event in water_events[:5]:
                print(f"     {event}")
        else:
            print(f"   ⚠️  NO WATER EVENTS FOUND - This is the problem!")
        
        # 死亡直前のステータス分析
        death_analysis = []
        for death in deaths:
            if isinstance(death, str) and "died" in death and "T:" in death:
                # 渇水レベル抽出
                try:
                    thirst_match = death.split("T:")
                    if len(thirst_match) > 1:
                        thirst_str = thirst_match[1].split(" ")[0]
                        thirst_value = float(thirst_str)
                        death_analysis.append(thirst_value)
                except:
                    pass
        
        if death_analysis:
            avg_death_thirst = sum(death_analysis) / len(death_analysis)
            min_death_thirst = min(death_analysis)
            max_death_thirst = max(death_analysis)
            
            print(f"\nDEATH THIRST LEVEL ANALYSIS:")
            print(f"   Average death thirst: {avg_death_thirst:.1f}")
            print(f"   Min death thirst: {min_death_thirst:.1f}")
            print(f"   Max death thirst: {max_death_thirst:.1f}")
            print(f"   Death threshold appears to be around 75-90+")
            
        # 水アクセス問題の診断
        print(f"\nWATER ACCESS DIAGNOSIS:")
        
        # 問題1: 水検知の問題
        if len(water_events) == 0:
            print(f"   ❌ WATER DETECTION FAILURE:")
            print(f"      NPCs are not detecting water sources")
            print(f"      Possible causes:")
            print(f"      - Water sources not in environment")
            print(f"      - Detection range too limited") 
            print(f"      - Water sensing disabled/broken")
        
        # 問題2: 移動の問題  
        if len(movement_events) < 50:  # 期待される移動量
            print(f"   ❌ MOVEMENT LIMITATION:")
            print(f"      Limited movement activity detected")
            print(f"      NPCs may be unable to reach water sources")
            print(f"      Possible causes:")
            print(f"      - Movement system disabled")
            print(f"      - Pathfinding to water broken")
            print(f"      - Physical barriers preventing access")
        
        # 問題3: 行動優先度の問題
        if len(survival_events) == 0:
            print(f"   ❌ SURVIVAL PRIORITY FAILURE:")
            print(f"      No survival-focused behavior detected") 
            print(f"      NPCs may not prioritize water seeking")
            print(f"      Possible causes:")
            print(f"      - Survival system not activated")
            print(f"      - Thirst not triggering water-seeking behavior")
            print(f"      - Other activities overriding survival needs")
        
        # 推奨される調査対象
        print(f"\nRECOMMENDED INVESTIGATION:")
        print(f"   1. Check environment.py for water source generation")
        print(f"   2. Examine NPC water detection range and mechanisms")  
        print(f"   3. Verify movement system can pathfind to water")
        print(f"   4. Confirm survival system prioritizes thirst relief")
        print(f"   5. Test if NPCs can interact with water when adjacent")
        
        return len(water_events) > 0, len(movement_events) > 0, len(survival_events) > 0
        
    except Exception as e:
        print(f"Water access debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False, False, False

if __name__ == "__main__":
    print("=== Water Access Debug System ===")
    print()
    print("INVESTIGATING:")
    print("- Water source detection by NPCs")
    print("- Movement to water sources")  
    print("- Survival behavior activation")
    print("- Physical water access mechanics")
    print("- Priority system for thirst relief")
    print()
    
    water_detect, can_move, survival_active = run_water_access_debug()
    
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY:")
    print(f"   Water Detection: {'✅' if water_detect else '❌'}")
    print(f"   Movement Capability: {'✅' if can_move else '❌'}")
    print(f"   Survival Activation: {'✅' if survival_active else '❌'}")
    print()
    
    if not any([water_detect, can_move, survival_active]):
        print("🚨 CRITICAL: Multiple water access systems failing!")
    elif water_detect and can_move and survival_active:
        print("🤔 PUZZLE: All systems appear functional but NPCs still dying")
    else:
        print("🎯 FOCUS AREA IDENTIFIED: Some systems need investigation")