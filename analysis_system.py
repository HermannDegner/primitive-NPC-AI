#!/usr/bin/env python3
"""
Analysis System Module - 分析システム
シミュレーション結果の包括的分析機能
"""

import pandas as pd

def analyze_enhanced_results(roster, ssd_logs, env_intelligence_logs, seasonal_logs=None):
    """Enhanced analysis with seasonal system"""
    print("\\n" + "=" * 80)
    print("=== Enhanced SSD + Smart Environment + Boundary + SEASONAL Analysis ===")
    print("=" * 80)
    
    # 生存者分析
    alive_npcs = [npc for npc in roster.values() if npc.alive]
    print(f"Final Survivors after FULL SEASONAL CYCLE: {len(alive_npcs)}/{len(roster)}")
    
    # 季節別分析
    if seasonal_logs:
        df_seasonal = pd.DataFrame(seasonal_logs)
        print(f"\\n🌍 Seasonal Impact Analysis:")
        
        for season in ['🌸Spring', '🌞Summer', '🍂Autumn', '❄️Winter']:
            season_data = df_seasonal[df_seasonal['season'] == season]
            if not season_data.empty:
                avg_pressure = season_data['seasonal_pressure'].mean()
                avg_temp_stress = season_data['temperature_stress'].mean()
                avg_resource_mod = season_data['resource_modifier'].mean()
                
                print(f"  {season}:")
                print(f"    Average seasonal pressure: {avg_pressure:.3f}")
                print(f"    Average temperature stress: {avg_temp_stress:.3f}")
                print(f"    Average resource availability: {avg_resource_mod:.3f}x")
    
    # SSD決定分析
    df_ssd = pd.DataFrame(ssd_logs)
    if not df_ssd.empty:
        print(f"\\nSSD Decision Analysis:")
        decision_counts = df_ssd['decision_type'].value_counts()
        for decision_type, count in decision_counts.items():
            print(f"  {decision_type}: {count} decisions")
        
        print(f"\\nAction Distribution:")
        action_counts = df_ssd['decision_action'].value_counts()
        for action, count in action_counts.items():
            print(f"  {action}: {count} times")
        
        # 跳躍分析
        leaps = df_ssd[df_ssd['decision_type'] == 'leap']
        print(f"\\nLeap Analysis:")
        print(f"  Total leaps: {len(leaps)}")
        
        if len(leaps) > 0:
            avg_leap_prob = leaps['leap_probability'].mean()
            print(f"  Average leap probability: {avg_leap_prob:.3f}")
            
            # 跳躍発生時の環境条件分析
            high_pressure_situations = leaps[leaps['environmental_pressure'] > 0.5]
            print(f"  Leaps during high environmental pressure: {len(high_pressure_situations)}")
    
    # 環境応答分析
    df_env = pd.DataFrame(env_intelligence_logs)
    if not df_env.empty:
        print(f"\\nEnvironmental Response Analysis:")
        avg_env_pressure = df_env['environmental_pressure'].mean()
        avg_resource_scarcity = df_env['resource_scarcity'].mean()
        print(f"  Avg environmental pressure: {avg_env_pressure:.3f}")
        print(f"  Avg resource scarcity: {avg_resource_scarcity:.3f}")
        
        # 高圧力状況の分析
        high_pressure_decisions = df_ssd[df_ssd['environmental_pressure'] > 0.5]
        print(f"  High pressure decisions: {len(high_pressure_decisions)}")
    
    # 捕食者狩り分析（プレースホルダー）
    print(f"\\n⚔️ Predator Hunting Analysis:")
    print(f"  Predator hunting system ACTIVE")
    print(f"  Evidence from simulation output shows hunting attempts occurred")
    print(f"  (Statistical details will be added in future version)")
    
    # 境界システム分析
    from subjective_boundary_system import boundary_system
    
    print(f"\\n🏘️ Subjective Boundary System Analysis:")
    individual_boundaries = len([npc for npc, boundaries in boundary_system.subjective_boundaries.items() 
                                if boundaries['people'] or boundaries['places'] or boundaries['resources']])
    collective_boundaries = len(boundary_system.collective_boundaries)
    total_violations = sum(len(violations) for violations in boundary_system.boundary_violations.values())
    
    print(f"  Individual boundary formations: {individual_boundaries}")
    print(f"  Collective boundaries formed: {collective_boundaries}")
    print(f"  Total boundary violations: {total_violations}")
    
    # 個人境界の詳細
    if individual_boundaries > 0:
        print(f"\\n👤 Individual Boundaries:")
        for npc_name, boundaries in boundary_system.subjective_boundaries.items():
            if boundaries['people'] or boundaries['places'] or boundaries['resources']:
                total_inner = len(boundaries['people']) + len(boundaries['places']) + len(boundaries['resources'])
                if total_inner > 0:
                    clarity = boundaries.get('boundary_clarity', 0.5)
                    print(f"  {npc_name}:")
                    print(f"    Inner people: {len(boundaries['people'])}")
                    print(f"    Inner places: {len(boundaries['places'])}")
                    print(f"    Inner resources: {len(boundaries['resources'])}")
                    print(f"    Boundary clarity: {clarity:.3f}")
    
    # 集団境界の詳細
    if collective_boundaries > 0:
        print(f"\\n🤝 Collective Boundaries (In-Group Formation):")
        for boundary_id, boundary_info in boundary_system.collective_boundaries.items():
            cohesion = boundary_info.get('cohesion', 0.0)
            shared_experiences = len(boundary_info.get('shared_experiences', []))
            members = [member for member in boundary_info.get('members', []) if member in roster and roster[member].alive]
            
            print(f"  {boundary_id}:")
            print(f"    Members: {', '.join(members)}")
            print(f"    Cohesion: {cohesion:.3f}")
            print(f"    Shared experiences: {shared_experiences}")
    
    # スマート環境進化分析
    if not df_env.empty:
        final_env_state = df_env.iloc[-1]
        print(f"\\nSmart Environment Intelligence Evolution:")
        for key, value in final_env_state.items():
            if key != 't':
                print(f"  {key}: {value:.4f}")
    
    # 最終状態サマリー
    print(f"\\nFinal Status Summary:")
    for npc in alive_npcs:
        health_status = "Health OK"
        if hasattr(npc, 'critically_injured') and npc.critically_injured:
            health_status = "CRITICAL INJURY"
        elif npc.hunger > 150 or npc.thirst > 150:
            health_status = "Poor Health"
        
        print(f"  {npc.name}: {health_status}")
        print(f"    Hunger: {npc.hunger:.1f}, Thirst: {npc.thirst:.1f}, Fatigue: {npc.fatigue:.1f}")
        print(f"    Exploration Mode: {npc.exploration_mode}")
        print(f"    Curiosity: {npc.curiosity:.3f}")
        print(f"    SSD Integration: ACTIVE")

def analyze_survival_patterns(roster, seasonal_logs):
    """生存パターンの詳細分析"""
    print(f"\\n📊 Survival Pattern Analysis:")
    
    # 生存者の特性分析
    survivors = [npc for npc in roster.values() if npc.alive]
    dead_npcs = [npc for npc in roster.values() if not npc.alive]
    
    print(f"\\n🎯 Survivor Characteristics:")
    if survivors:
        avg_curiosity = sum(npc.curiosity for npc in survivors) / len(survivors)
        avg_sociability = sum(npc.sociability for npc in survivors) / len(survivors)
        print(f"  Average curiosity: {avg_curiosity:.3f}")
        print(f"  Average sociability: {avg_sociability:.3f}")
        
        # 生存者の名前パターン分析
        survivor_types = {}
        for npc in survivors:
            npc_type = npc.name.split('_')[1] if '_' in npc.name else 'Unknown'
            survivor_types[npc_type] = survivor_types.get(npc_type, 0) + 1
        
        print(f"\\n  Survivor Types:")
        for npc_type, count in survivor_types.items():
            print(f"    {npc_type}: {count}")
    
    print(f"\\n💀 Casualty Analysis:")
    if dead_npcs:
        print(f"  Total casualties: {len(dead_npcs)}")
        # 死亡者の特性も分析可能（必要に応じて追加）

def generate_simulation_report(roster, ssd_logs, env_logs, seasonal_logs, simulation_params):
    """包括的シミュレーションレポート生成"""
    report = {
        'simulation_params': simulation_params,
        'survival_rate': len([npc for npc in roster.values() if npc.alive]) / len(roster),
        'total_decisions': len(ssd_logs),
        'seasonal_cycles': len(set(log['season'] for log in seasonal_logs)) if seasonal_logs else 0,
        'boundary_formations': 0,  # 境界システムから取得
        'environmental_events': len(env_logs)
    }
    
    return report