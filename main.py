#!/usr/bin/env python3
"""Main entrypoint for the Enhanced SSD Primitive NPC AI Simulation.

This module exposes a callable `run_simulation` function so other tools/tests
can import and run the simulation programmatically. It also provides a small
CLI wrapper for convenience.

Behaviors preserved from the previous `main.py`:
- Run `run_enhanced_ssd_simulation` and (optionally) run analysis functions.
"""

from typing import Optional, Tuple

try:
    from enhanced_simulation import run_enhanced_ssd_simulation
    from analysis_system import (
        analyze_enhanced_results,
        analyze_survival_patterns,
        generate_simulation_report,
    )
except ImportError as e:
    print(f"Warning - Module Import Error: {e}")
    print("Dependencies not found. Cannot run simulation.")
    raise


def run_simulation(ticks: int = 200, analyze: bool = True) -> Tuple[dict, list, list, list]:
    """Programmatically run the enhanced SSD simulation.

    Args:
        ticks: Number of ticks to simulate.
        analyze: If True, run post-simulation analysis and report generation.

    Returns:
        A tuple (roster, ssd_logs, env_logs, seasonal_logs) produced by the simulation.
    """

    print("Enhanced SSD Theory Simulation - Seasonal Carnivore Survival")
    print("Complete Integration: SSD + Boundary + Smart Environment + Seasonal Systems")
    print("=" * 60)

    # Run the core simulation
    roster, ssd_logs, env_logs, seasonal_logs = run_enhanced_ssd_simulation(ticks=ticks)

    if analyze:
        try:
            print("\nAnalyzing simulation results...")
            analyze_enhanced_results(roster, ssd_logs, env_logs, seasonal_logs)
            analyze_survival_patterns(roster, seasonal_logs)
            report = generate_simulation_report(roster, ssd_logs, env_logs, seasonal_logs)
            print(f"\nDetailed Report: {len(report)} analysis items completed")
        except Exception as e:
            print(f"Analysis Error: {e}")

    return roster, ssd_logs, env_logs, seasonal_logs


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
