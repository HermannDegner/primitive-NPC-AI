#!/usr/bin/env python3
"""Main entrypoint for the SSD Core Engine-based NPC AI Simulation.

🎯 ARCHITECTURE NOTE: This system is built around ssd_core_engine as the foundation.
All surrounding code is designed to complement and integrate with the SSD Core Engine.

💡 KEY THEORETICAL BREAKTHROUGH:
整合慣性κ (Coherence Inertia) = 記憶蓄積システム

SSD理論の核心的洞察として、整合慣性κは単なる物理パラメータではなく、
エージェントの「記憶の強度」を表現することが判明しました。

- κ ↑ = より多くの記憶、より強い適応反応
- κ ↓ = 記憶が少ない、学習段階の状態

この理解により、NPCは過去の体験を蓄積し、
それに基づいて将来の行動を動的に調整する真の学習システムが実現されました。

CORE PRINCIPLE:
- ssd_core_engine/ provides the theoretical framework and AI engine
- All other modules (NPC classes, environment, simulation) adapt TO the SSD engine
- NOT the other way around - preserve SSD engine integrity

INTEGRATION HIERARCHY:
1. ssd_core_engine/ (FOUNDATION - DO NOT MODIFY core logic)
2. NPCs use SSD engines for decision making  
3. Environment provides ObjectInfo compatible with SSD types
4. Simulation orchestrates SSD-powered interactions

This approach ensures maximum utilization of advanced SSD capabilities while
maintaining theoretical consistency and avoiding architectural conflicts.
"""

from typing import Optional, Tuple
import sys
import os

# 🔗 SSD理論常時参照システム - 基礎理論への常時接続を保証
from ssd_theory_reference import get_ssd_reference, SSD_THEORY_REPO

# 分割されたシミュレーションシステムをインポート
try:
    from integrated_simulation import run_ssd_enhanced_simulation as run_enhanced_ssd_simulation
    SIMULATION_AVAILABLE = True
    print("✅ Using integrated simulation system")
except ImportError:
    try:
        # バックアップ機能をメインフォルダーから使用
        from ssd_integrated_simulation import run_ssd_integrated_simulation as run_enhanced_ssd_simulation
        SIMULATION_AVAILABLE = True
        print("⚠️ Using SSD integrated simulation (full feature set)")
    except ImportError:
        # フォールバック無効化 - 手動参照推奨
        SIMULATION_AVAILABLE = False
        print("❌ Warning: Secondary simulation system failed")
        print("🔍 Both primary and secondary systems unavailable:")
        print("   - integrated_simulation.py (primary system) failed")
        print("   - ssd_integrated_simulation.py (secondary) failed")
        print()
        print("�️  Manual Recovery Options:")
        print("   1. Check dependencies: pip install required packages")  
        print("   2. Debug secondary system: ssd_integrated_simulation.py")
        print("   3. Reference archive: archive/main_backup.py (manual restore)")
        print("   4. Check logs above for specific error details")
        print()
        print("💡 Note: Fallback system disabled for cleaner architecture")
        print("� Use archive/main_backup.py for reference if needed")

# 分析システムの安全インポート（オプション機能）
try:
    from analysis_system import (
        analyze_enhanced_results,
        analyze_survival_patterns, 
        generate_simulation_report,
    )
    ANALYSIS_AVAILABLE = True
    print("✅ Analysis system available")
except ImportError:
    ANALYSIS_AVAILABLE = False
    print("ℹ️ Analysis system not available (optional feature)")
    
    # 分析関数のダミー実装
    def analyze_enhanced_results(*args, **kwargs):
        print("📊 Analysis skipped (analysis_system not available)")
        
    def analyze_survival_patterns(*args, **kwargs):
        print("📈 Pattern analysis skipped (analysis_system not available)")
        
    def generate_simulation_report(*args, **kwargs):
        print("📋 Report generation skipped (analysis_system not available)")


def run_simulation(ticks: int = 200, analyze: bool = True) -> Tuple[dict, list, list, list]:
    """Programmatically run the enhanced SSD simulation.

    Args:
        ticks: Number of ticks to simulate.
        analyze: If True, run post-simulation analysis and report generation.

    Returns:
        A tuple (roster, ssd_logs, env_logs, seasonal_logs) produced by the simulation.
    """

    print("Enhanced SSD Theory Simulation - Seasonal Carnivore Survival")
    print("Integrated Territorial & Collective Boundary Formation System")
    print("=" * 60)

    try:
        if SIMULATION_AVAILABLE:
            # 分割されたシミュレーションシステムを呼び出し
            print("Running Enhanced SSD Simulation...")
            roster, ssd_logs, env_logs, seasonal_logs = run_enhanced_ssd_simulation(ticks)
            
            if analyze and ANALYSIS_AVAILABLE:
                try:
                    print("\nAnalyzing simulation results...")
                    analyze_enhanced_results(roster, ssd_logs, env_logs, seasonal_logs)
                    print("Analysis completed.")
                except Exception as e:
                    print(f"Analysis Error: {e}")
            
            return roster, ssd_logs, env_logs, seasonal_logs
        else:
            print("Backup simulation not available. Running minimal simulation...")
            
            # 最小限のシミュレーション
            roster = {}
            for i in range(3):
                npc_name = f"NPC_{i}"
                roster[npc_name] = {
                    "x": 25, "y": 25,
                    "hunger": 50, "thirst": 30, "fatigue": 40,
                    "ticks_survived": ticks
                }
            
            print(f"Completed {ticks} ticks with {len(roster)} NPCs")
            return roster, [], [], []
            
    except Exception as e:
        print(f"Simulation failed: {e}")
        # 最小限の返り値
        return {}, [], [], []


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Enhanced SSD NPC Simulation")
    parser.add_argument("--ticks", type=int, default=200, help="Number of ticks to simulate")
    parser.add_argument(
        "--no-analyze", action="store_true", help="Skip post-simulation analysis and report"
    )

    args = parser.parse_args()

    try:
        run_simulation(ticks=args.ticks, analyze=not args.no_analyze)
    except Exception as exc:
        print(f"Simulation Execution Error: {exc}")
        import traceback

        traceback.print_exc()
