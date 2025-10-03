"""
シミュレーション実行システム - SSD統合シミュレーションランナー

このモジュールは、各種シミュレーションの実行とSSD Core Engineとの統合を管理します。
"""

import random
from typing import List, Dict, Any, Optional
import time


class SimulationRunner:
    """シミュレーション実行システム"""
    
    def __init__(self):
        self.simulation_data = {}
        self.performance_metrics = {}

    def run_ssd_enhanced_simulation(self, env, npcs: List, steps: int = 50, 
                                  enable_hunting: bool = True, 
                                  enable_territories: bool = True,
                                  enable_exploration: bool = True) -> Dict[str, Any]:
        """SSD Core Engine統合シミュレーション実行"""
        
        print(f"\n=== SSD Enhanced Simulation (Steps: {steps}) ===")
        
        # シミュレーション統計の初期化
        stats = {
            "hunt_attempts": 0,
            "successful_hunts": 0,
            "territories_created": 0,
            "exploration_events": 0,
            "leap_decisions": 0,
            "total_decisions": 0,
            "ssd_predictions": 0,
            "environmental_changes": 0
        }
        
        try:
            from ssd_enhanced_npc import SSDEnhancedNPC
            from ssd_exploration_system import SSDExplorationSystem
            from ssd_territory_system import SSDTerritorySystem
            from ssd_hunting_system import SSDHuntingSystem
            
            # SSDEnhancedNPCでNPCをラップ
            enhanced_npcs = []
            for npc in npcs:
                try:
                    enhanced = SSDEnhancedNPC(npc)
                    enhanced_npcs.append(enhanced)
                except Exception as e:
                    print(f"Warning: Failed to enhance NPC {npc.name}: {e}")
                    continue
            
            print(f"Enhanced {len(enhanced_npcs)} NPCs with SSD Core Engine")
            
            # シミュレーションメインループ
            for step in range(steps):
                env.current_tick = step
                
                # 各NPCの行動処理
                for enhanced_npc in enhanced_npcs:
                    npc = enhanced_npc.npc
                    npc.current_tick = step
                    
                    try:
                        # SSDエンジンによる意思決定
                        decision_context = enhanced_npc.make_ssd_decision()
                        stats["total_decisions"] += 1
                        
                        if decision_context.get("prediction_used"):
                            stats["ssd_predictions"] += 1
                        
                        # 探索システムの処理
                        if enable_exploration:
                            exploration_system = SSDExplorationSystem(enhanced_npc)
                            exploration_pressure = exploration_system.calculate_exploration_pressure()
                            
                            if exploration_pressure > 0.7:
                                leap_decision = exploration_system.should_make_exploration_leap()
                                if leap_decision["should_leap"]:
                                    stats["leap_decisions"] += 1
                                    # 探索行動の実行（簡易版）
                                    new_x = npc.pos[0] + random.randint(-10, 10)
                                    new_y = npc.pos[1] + random.randint(-10, 10)
                                    npc.pos = (max(0, min(env.width-1, new_x)), 
                                              max(0, min(env.height-1, new_y)))
                                    stats["exploration_events"] += 1
                        
                        # 狩猟システムの処理
                        if enable_hunting and hasattr(npc, 'hunting_coherence'):
                            hunting_system = SSDHuntingSystem(enhanced_npc)
                            
                            # 狩猟機会の評価
                            if random.random() < npc.hunting_coherence:
                                stats["hunt_attempts"] += 1
                                
                                # 簡易的な獲物生成
                                target_prey = {
                                    "size": random.uniform(0.5, 2.0),
                                    "speed": random.uniform(0.3, 0.8),
                                    "defense": random.uniform(0.2, 0.6)
                                }
                                
                                # 狩猟グループの作成
                                hunt_group = hunting_system.create_hunt_group_v2(npc, target_prey)
                                
                                # 狩猟成功判定
                                hunt_result = hunting_system.calculate_hunt_success_v2(hunt_group, target_prey)
                                
                                if hunt_result["success"]:
                                    stats["successful_hunts"] += 1
                                
                                # 狩猟経験の処理
                                hunting_system.process_hunting_experience(
                                    "success" if hunt_result["success"] else "failure",
                                    target_prey["size"],
                                    len(hunt_group)
                                )
                        
                        # 縄張りシステムの処理
                        if enable_territories and step % 10 == 0:  # 10ステップごと
                            territory_system = SSDTerritorySystem(enhanced_npc)
                            
                            # 縄張り作成の判定（簡易版）
                            if random.random() < 0.1:  # 10%の確率
                                territory_id = territory_system.create_territory_v2(npc.pos, radius=8)
                                if territory_id and not territory_id.startswith("fallback"):
                                    stats["territories_created"] += 1
                        
                        # 通常のNPC行動処理
                        npc.act()
                        
                    except Exception as e:
                        print(f"Error processing NPC {npc.name} at step {step}: {e}")
                        continue
                
                # 環境の更新
                try:
                    env.update()
                    if step % 5 == 0:  # 環境変化の記録
                        stats["environmental_changes"] += 1
                except Exception as e:
                    print(f"Error updating environment at step {step}: {e}")
                
                # 進捗表示
                if step % 10 == 0:
                    hunt_success_rate = (stats["successful_hunts"] / max(1, stats["hunt_attempts"])) * 100
                    print(f"Step {step}: Hunts {stats['successful_hunts']}/{stats['hunt_attempts']} "
                          f"({hunt_success_rate:.1f}%), Territories: {stats['territories_created']}, "
                          f"Explorations: {stats['exploration_events']}")
            
            # 最終統計
            print(f"\n=== Simulation Complete ===")
            print(f"Total Hunt Success Rate: {(stats['successful_hunts'] / max(1, stats['hunt_attempts'])) * 100:.1f}%")
            print(f"Territories Created: {stats['territories_created']}")
            print(f"Exploration Events: {stats['exploration_events']}")
            print(f"SSD Predictions Used: {stats['ssd_predictions']}")
            print(f"Total Decisions Made: {stats['total_decisions']}")
            
            return stats
            
        except Exception as e:
            print(f"Simulation error: {e}")
            return {"error": str(e), **stats}

    def run_simulation(self, env, npcs: List, steps: int = 50, 
                      simulation_type: str = "standard") -> Dict[str, Any]:
        """標準シミュレーション実行"""
        
        print(f"\n=== Standard Simulation - {simulation_type} (Steps: {steps}) ===")
        
        stats = {
            "actions_taken": 0,
            "movements": 0,
            "resource_interactions": 0,
            "social_interactions": 0,
            "errors": 0
        }
        
        start_time = time.time()
        
        for step in range(steps):
            env.current_tick = step
            
            for npc in npcs:
                npc.current_tick = step
                
                try:
                    # NPC行動
                    old_pos = npc.pos
                    npc.act()
                    
                    stats["actions_taken"] += 1
                    
                    # 移動の検出
                    if npc.pos != old_pos:
                        stats["movements"] += 1
                    
                    # リソースとの相互作用検出
                    if hasattr(npc, 'food') or hasattr(npc, 'water'):
                        stats["resource_interactions"] += 1
                    
                except Exception as e:
                    stats["errors"] += 1
                    if stats["errors"] < 5:  # 最初の5つのエラーのみ表示
                        print(f"NPC {npc.name} error at step {step}: {e}")
            
            # 環境更新
            try:
                env.update()
            except Exception as e:
                print(f"Environment update error at step {step}: {e}")
            
            # 進捗表示
            if step % 20 == 0 and step > 0:
                elapsed = time.time() - start_time
                print(f"Step {step}: Actions {stats['actions_taken']}, "
                      f"Movements {stats['movements']}, Time {elapsed:.1f}s")
        
        end_time = time.time()
        stats["execution_time"] = end_time - start_time
        
        print(f"\n=== Standard Simulation Complete ===")
        print(f"Total Actions: {stats['actions_taken']}")
        print(f"Total Movements: {stats['movements']}")
        print(f"Execution Time: {stats['execution_time']:.2f}s")
        print(f"Errors: {stats['errors']}")
        
        return stats

    def run_performance_comparison(self, env, npcs: List, steps: int = 30) -> Dict[str, Any]:
        """パフォーマンス比較シミュレーション"""
        
        print(f"\n=== Performance Comparison (Steps: {steps}) ===")
        
        results = {}
        
        # 標準シミュレーション
        print("\n--- Running Standard Simulation ---")
        standard_stats = self.run_simulation(env, npcs, steps, "standard")
        results["standard"] = standard_stats
        
        # SSD統合シミュレーション
        print("\n--- Running SSD Enhanced Simulation ---")
        ssd_stats = self.run_ssd_enhanced_simulation(env, npcs, steps)
        results["ssd_enhanced"] = ssd_stats
        
        # 比較分析
        print(f"\n=== Performance Analysis ===")
        if "execution_time" in standard_stats and "error" not in ssd_stats:
            print(f"Standard Execution Time: {standard_stats['execution_time']:.2f}s")
            print(f"Standard Actions: {standard_stats['actions_taken']}")
            print(f"SSD Hunt Success: {ssd_stats['successful_hunts']}/{ssd_stats['hunt_attempts']}")
            print(f"SSD Territories: {ssd_stats['territories_created']}")
            print(f"SSD Predictions: {ssd_stats['ssd_predictions']}")
        
        return results

    def run_targeted_simulation(self, env, npcs: List, focus: str = "hunting", 
                              steps: int = 40) -> Dict[str, Any]:
        """特定システムに焦点を当てたシミュレーション"""
        
        print(f"\n=== Targeted Simulation - Focus: {focus} (Steps: {steps}) ===")
        
        if focus == "hunting":
            return self.run_ssd_enhanced_simulation(
                env, npcs, steps, 
                enable_hunting=True, 
                enable_territories=False, 
                enable_exploration=False
            )
        elif focus == "territory":
            return self.run_ssd_enhanced_simulation(
                env, npcs, steps,
                enable_hunting=False,
                enable_territories=True,
                enable_exploration=False
            )
        elif focus == "exploration":
            return self.run_ssd_enhanced_simulation(
                env, npcs, steps,
                enable_hunting=False,
                enable_territories=False,
                enable_exploration=True
            )
        else:
            return self.run_ssd_enhanced_simulation(env, npcs, steps)