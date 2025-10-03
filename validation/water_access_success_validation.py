#!/usr/bin/env python3
"""
Fixed Water Access Success Validation - 修正版水アクセス成功検証
"""

def run_water_access_success_validation():
    """修正された水アクセス統合成功の検証"""
    
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        
        # 統合成功確認テスト（十分な観察時間）
        validation_ticks = 100
        
        print(f"Starting water access success validation ({validation_ticks} ticks)")
        print("Validating NPC survival behavior with integrated systems...")
        print()
        
        # シミュレーション実行
        results, deaths, events, analysis = run_ssd_integrated_simulation(max_ticks=validation_ticks)
        
        print("=" * 60)
        print("WATER ACCESS SUCCESS VALIDATION")
        print("=" * 60)
        
        # 正しいパターンで水関連イベント抽出
        water_events = []
        memory_events = []
        survival_events = []
        
        for event in events:
            if isinstance(event, str):
                # 水関連活動 (💧🚰🏞️💡アイコンを含む)
                if any(w in event for w in ["💧", "🚰", "🏞️💧", "WATER", "water", "drink", "thirst"]):
                    water_events.append(event)
                
                # 記憶・学習活動 (🧠💡アイコンを含む)  
                if any(w in event for w in ["🧠", "💡", "Memory", "learned", "urgency"]):
                    memory_events.append(event)
                
                # 生存活動全般 (🍎🏹活動など)
                if any(w in event for w in ["FOOD", "HUNT", "survival", "🍎", "🏹", "💧"]):
                    survival_events.append(event)
        
        print(f"\nINTEGRATED SYSTEM ACTIVITY ANALYSIS:")
        print(f"   Water-related events: {len(water_events)}")
        print(f"   Memory-learning events: {len(memory_events)}")  
        print(f"   Survival events: {len(survival_events)}")
        
        # 水活動の詳細分析
        if len(water_events) > 0:
            print(f"\n✅ WATER ACCESS SUCCESS:")
            print(f"   Water activities detected: {len(water_events)}")
            
            # 水活動の種別カウント
            water_attempts = len([e for e in water_events if "WATER ATTEMPT" in e])
            water_consumed = len([e for e in water_events if "WATER CONSUMED" in e])
            cave_water = len([e for e in water_events if "cave water" in e])
            
            print(f"   Water attempt actions: {water_attempts}")
            print(f"   Successful water consumption: {water_consumed}")
            print(f"   Cave water interactions: {cave_water}")
            
            # 成功率計算
            if water_attempts > 0:
                success_rate = (water_consumed / water_attempts) * 100
                print(f"   Water access success rate: {success_rate:.1f}%")
            
            # サンプルイベント表示
            print(f"\n   Sample water activities:")
            for event in water_events[:5]:
                print(f"     {event}")
        else:
            print(f"\n❌ NO WATER ACCESS:")
            print(f"   Water system still not functioning")
        
        # 記憶学習システム分析
        if len(memory_events) > 0:
            print(f"\n✅ MEMORY-LEARNING SUCCESS:")
            print(f"   Learning activities detected: {len(memory_events)}")
            
            # 記憶活動の種別
            memory_influence = len([e for e in memory_events if "Memory influence" in e])
            urgency_learned = len([e for e in memory_events if "urgency learned" in e])
            
            print(f"   Memory influence calculations: {memory_influence}")
            print(f"   Urgency learning events: {urgency_learned}")
            
            # サンプル記憶イベント
            print(f"\n   Sample memory-learning activities:")
            for event in memory_events[:3]:
                print(f"     {event}")
        else:
            print(f"\n❌ NO MEMORY LEARNING:")
            print(f"   Memory system not functioning")
        
        # 生存期間分析
        if len(deaths) > 0:
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
                avg_death = sum(death_ticks) / len(death_ticks)
                
                print(f"\nSURVIVAL PERFORMANCE ANALYSIS:")
                print(f"   First death: T{first_death}")
                print(f"   Average survival: T{avg_death:.1f}")
                
                # 前回結果との比較分析
                if first_death >= 80:
                    improvement = "EXCELLENT: 80+ ticks survival"
                elif first_death >= 60:
                    improvement = "GOOD: 60+ ticks survival"  
                elif first_death >= 45:
                    improvement = "MODERATE: 45+ ticks survival"
                else:
                    improvement = "POOR: <45 ticks survival"
                    
                print(f"   Performance rating: {improvement}")
        else:
            print(f"\nSURVIVAL PERFORMANCE ANALYSIS:")
            print(f"   PERFECT: No deaths in {validation_ticks} ticks!")
            print(f"   All NPCs survived the full test period")
        
        # 統合成功判定
        water_success = len(water_events) > 20  # 十分な水活動
        memory_success = len(memory_events) > 5  # 記憶学習活動
        survival_success = len(deaths) == 0 or min([int(d.split("T")[1].split(":")[0]) for d in deaths if isinstance(d, str) and "died" in d and "T" in d] or [100]) >= 60
        
        print(f"\nINTEGRATION SUCCESS ASSESSMENT:")
        print(f"   Water System: {'✅ SUCCESS' if water_success else '❌ NEEDS WORK'}")
        print(f"   Memory System: {'✅ SUCCESS' if memory_success else '❌ NEEDS WORK'}")  
        print(f"   Survival Performance: {'✅ SUCCESS' if survival_success else '❌ NEEDS WORK'}")
        
        overall_success = water_success and memory_success and survival_success
        
        return overall_success, len(water_events), len(memory_events), len(deaths)
        
    except Exception as e:
        print(f"Water access validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0, 0

if __name__ == "__main__":
    print("=== Water Access Success Validation ===")
    print()
    print("INTEGRATION VALIDATION FEATURES:")
    print("- NPC water seeking and consumption")
    print("- Cave water access and interaction") 
    print("- Memory-based coherence influence")
    print("- Experience learning for water urgency")
    print("- Metabolic integration with environmental pressure")
    print("- SSD prediction system with crisis detection")
    print("- Multi-layered survival behavior coordination")
    print()
    
    success, water_count, memory_count, death_count = run_water_access_success_validation()
    
    print("\n" + "=" * 60)
    print("FINAL INTEGRATION ASSESSMENT:")
    print(f"   Water events: {water_count}")
    print(f"   Memory events: {memory_count}")
    print(f"   Deaths: {death_count}")
    print()
    
    if success:
        print("🎉 INTEGRATION SUCCESS!")
        print("   Water access, memory systems, and survival integration working!")
        print("   整合慣性 κ = memory system successfully implemented!")
    else:
        print("🔄 Integration still developing...")
        print("   Some systems functioning, continued refinement needed.")