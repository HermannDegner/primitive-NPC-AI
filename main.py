#!/usr/bin/env python3
"""
Enhanced SS        # Generate detailed report
        report = generate_simulation_report(roster, ssd_logs, env_logs, seasonal_logs)
        print(f"\nDetailed Report: {len(report)} analysis items completed")heory Primitive NPC AI Simulation - Main Entry Point
Complete Integration: SSD (4-Layer Structure) + Subjective Boundary System + Smart Environment + Seasonal Systems

Integration Environment: Enhanced SSD + Seasonal + Boundary + Smart World
Created: 2024
Version: v3.1 - Modularized
"""

try:
    from enhanced_simulation import run_enhanced_ssd_simulation
    from analysis_system import (
        analyze_enhanced_results, 
        analyze_survival_patterns,
        generate_simulation_report
    )
except ImportError as e:
    print(f"Warning - Module Import Error: {e}")
    print("Dependencies not found. Cannot run simulation.")
    exit(1)

def main():
    """Main Entry Point - Enhanced SSD Seasonal Simulation"""
    
    print("Enhanced SSD Theory Simulation - Seasonal Carnivore Survival")
    print("Complete Integration: SSD + Boundary + Smart Environment + Seasonal Systems")
    print("=" * 60)
    
    try:
        # Run simulation (200 ticks for cooperation test)
        roster, ssd_logs, env_logs, seasonal_logs = run_enhanced_ssd_simulation(ticks=200)
        
        # Result analysis
        print("\nAnalyzing simulation results...")
        analyze_enhanced_results(roster, ssd_logs, env_logs, seasonal_logs)
        
        # Survival pattern analysis
        analyze_survival_patterns(roster, seasonal_logs)
        
        # 詳細レポート生成
        report = generate_simulation_report(roster, ssd_logs, env_logs, seasonal_logs)
        print(f"\n� 詳細レポート: {len(report)} 項目の分析完了")
        
    except Exception as e:
        print(f"Simulation Execution Error: {e}")
        import traceback
        traceback.print_exc()

# Main execution
if __name__ == "__main__":
    main()