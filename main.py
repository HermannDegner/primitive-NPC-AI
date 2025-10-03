#!/usr/bin/env python3
"""Main entrypoint for the SSD Core Engine Enhanced Primitive NPC AI Simulation.

This module uses the modular SSD Core Engine for more sophisticated 
structural subjective dynamics simulation.
"""

from typing import Optional, Tuple, List, Dict, Any
import sys
import os
import random

# SSD Core Engine のインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ssd_core_engine'))
from ssd_engine import create_ssd_engine, setup_basic_structure
from ssd_types import LayerType, ObjectInfo
from ssd_utils import create_survival_scenario_objects, SystemMonitor

# 縄張りシステムの安全インポート
try:
    from ssd_territory import TerritoryProcessor
    TERRITORY_SYSTEM_AVAILABLE = True
except ImportError:
    print("Warning: Territory system not available")
    TERRITORY_SYSTEM_AVAILABLE = False

# ローカルシステムとの連携
# from analysis_system import (  # 未使用のため無効化
#     analyze_enhanced_results,
#     analyze_survival_patterns,
#     generate_simulation_report,
# )
from config import *
from environment import Environment
from npc import NPC
from seasonal_system import SeasonalSystem


class SSDEnhancedNPC:
    """SSD Core Engine統合NPC"""
    
    def __init__(self, npc: NPC):
        self.npc = npc
        self.engine = create_ssd_engine(f"ssd_npc_{npc.name}")
        setup_basic_structure(self.engine)
        self.monitor = SystemMonitor()
        
        # 縄張りシステムの初期化
        if TERRITORY_SYSTEM_AVAILABLE:
            self.territory_processor = TerritoryProcessor()
            self.territory_processor.initialize_npc_boundaries(npc.name)
        else:
            self.territory_processor = None
        
        # NPCの基本情報をSSDエンジンに登録
        self._register_npc_state()
    
    def _register_npc_state(self):
        """NPCの状態をSSDエンジンに登録"""
        # 物理層：基本的な生存ニーズ
        self.engine.add_structural_element(
            LayerType.PHYSICAL, 
            "survival_needs",
            {"hunger": self.npc.hunger, "thirst": self.npc.thirst, "fatigue": self.npc.fatigue}
        )
        
        # 基層：本能的行動パターンと縄張り意識
        base_data = {
            "curiosity": self.npc.curiosity, 
            "sociability": self.npc.sociability, 
            "risk_tolerance": self.npc.risk_tolerance
        }
        
        # 縄張りシステムが利用可能な場合は縄張り意識を追加
        if self.territory_processor:
            territorial_state = self.territory_processor.get_territorial_state(self.npc.name)
            base_data.update({
                "territorial_awareness": 0.5,
                "has_territory": territorial_state['has_territory'],
                "inner_objects_count": territorial_state['inner_objects_count']
            })
        
        self.engine.add_structural_element(LayerType.BASE, "instincts", base_data)
        
        # 中核層：学習した行動パターン
        self.engine.add_structural_element(
            LayerType.CORE,
            "learned_behaviors",
            {"hunting_experience": getattr(self.npc, 'hunting_experience', 0), "kappa": dict(self.npc.kappa)}
        )
        
        # 上層：戦略的思考
        strategic_data = {"exploration_mode": getattr(self.npc, 'exploration_mode', False)}
        
        # 縄張り関連の戦略的思考を追加
        if self.territory_processor:
            territorial_state = self.territory_processor.get_territorial_state(self.npc.name)
            strategic_data.update({
                "collective_memberships": len(territorial_state['collective_memberships']),
                "territory_strategy": "cooperative" if territorial_state['has_territory'] else "nomadic"
            })
        
        self.engine.add_structural_element(LayerType.UPPER, "strategic_planning", strategic_data)
    
    def perceive_environment(self, environment: Environment) -> List[ObjectInfo]:
        """環境をSSD ObjectInfoとして知覚"""
        objects = []
        
        # 水源の知覚 (洞窟の水)
        for cave_id, cave_pos in environment.caves.items():
            if cave_id in environment.cave_water_storage:
                water_data = environment.cave_water_storage[cave_id]
                if water_data["water_amount"] > 0:
                    water_obj = ObjectInfo(
                        id=f"water_{cave_id}",
                        type="water",
                        current_value=water_data["water_amount"],
                        survival_relevance=0.9,  # 高い生存関連性
                        properties={
                            "position": cave_pos,
                            "threat_level": 0.1,
                            "resource_potential": water_data["water_amount"] / 100.0
                        }
                    )
                    objects.append(water_obj)
        
        # 食料源の知覚 (ベリー)
        for berry_id, berry_pos in environment.berries.items():
            food_obj = ObjectInfo(
                id=f"food_{berry_id}",
                type="food",
                current_value=1.0,  # ベリーの存在
                survival_relevance=0.8,
                properties={
                    "position": berry_pos,
                    "threat_level": 0.0,
                    "resource_potential": 0.8
                }
            )
            objects.append(food_obj)
        
        # 狩猟場の知覚
        for hunt_id, hunt_pos in environment.hunting_grounds.items():
            hunt_obj = ObjectInfo(
                id=f"hunting_{hunt_id}",
                type="hunting",
                current_value=1.0,  # 狩猟可能性
                survival_relevance=0.7,
                properties={
                    "position": hunt_pos,
                    "threat_level": 0.3,  # 狩猟にはリスクが伴う
                    "resource_potential": 0.5
                }
            )
            objects.append(hunt_obj)
        
        return objects[:8]  # 認知限界として最大8つまで
    
    def make_decision(self, perceived_objects: List[ObjectInfo], available_actions: List[str]) -> Dict[str, Any]:
        """SSD Core Engineによる意思決定"""
        # NPCの現在状態を更新
        self._update_npc_state()
        
        # 縄張り的相互作用の評価
        territorial_context = {}
        if self.territory_processor:
            current_pos = (self.npc.x, self.npc.y)
            territorial_context = self.territory_processor.check_territorial_interaction(
                self.npc.name, current_pos
            )
        
        # SSDエンジンでステップ実行
        result = self.engine.step(
            perceived_objects=perceived_objects,
            available_actions=available_actions
        )
        
        # 縄張り情報を結果に追加
        if territorial_context:
            result['territorial_context'] = territorial_context
        
        return result
    
    def _update_npc_state(self):
        """NPCの状態をSSDエンジンに反映"""
        try:
            # 物理層の更新（存在する場合のみ）
            if hasattr(self.engine, 'update_structural_element'):
                self.engine.update_structural_element(
                    LayerType.PHYSICAL,
                    "survival_needs",
                    {"hunger": self.npc.hunger, "thirst": self.npc.thirst, "fatigue": self.npc.fatigue}
                )
        except Exception as e:
            # 更新メソッドが存在しない場合は無視
            pass
    
    def process_territorial_experience(self, experience_type: str, experience_valence: float, 
                                     other_npcs: List[str] = None, tick: int = 0) -> Dict[str, Any]:
        """縄張り経験の処理"""
        if not self.territory_processor:
            return {}
        
        current_pos = (self.npc.x, self.npc.y)
        return self.territory_processor.process_territorial_experience(
            npc_id=self.npc.name,
            location=current_pos,
            experience_type=experience_type,
            experience_valence=experience_valence,
            other_npcs=other_npcs,
            tick=tick
        )
    
    # === SSD Core Engine による探索機能代替実装 ===
    
    def calculate_life_crisis_pressure_v2(self) -> float:
        """ssd_core_engine版: 生命危機意味圧の計算"""
        # 生存関連のオブジェクト情報を作成
        survival_objects = []
        
        # 脱水危機
        if self.npc.thirst > 140:
            dehydration_obj = ObjectInfo(
                id="dehydration_crisis",
                type="survival_threat", 
                current_value=(self.npc.thirst - 140) / 60.0,
                survival_relevance=0.95,
                properties={"threat_type": "dehydration", "urgency": min(1.0, (self.npc.thirst - 140) / 60.0)}
            )
            survival_objects.append(dehydration_obj)
        
        # 飢餓危機
        if self.npc.hunger > 140:
            starvation_obj = ObjectInfo(
                id="starvation_crisis",
                type="survival_threat",
                current_value=(self.npc.hunger - 140) / 60.0, 
                survival_relevance=0.90,
                properties={"threat_type": "starvation", "urgency": min(1.0, (self.npc.hunger - 140) / 60.0)}
            )
            survival_objects.append(starvation_obj)
        
        # 疲労危機
        if self.npc.fatigue > 170:
            fatigue_obj = ObjectInfo(
                id="fatigue_crisis",
                type="survival_threat",
                current_value=(self.npc.fatigue - 170) / 30.0,
                survival_relevance=0.70,
                properties={"threat_type": "exhaustion", "urgency": min(1.0, (self.npc.fatigue - 170) / 30.0)}
            )
            survival_objects.append(fatigue_obj)
        
        if not survival_objects:
            return 0.0
        
        # SSD Core Engine で意味圧計算
        try:
            result = self.engine.step(
                perceived_objects=survival_objects,
                available_actions=["assess_crisis"]
            )
            return result.get('total_meaning_pressure', 0.0)
        except Exception as e:
            # フォールバック: 単純計算
            return sum(obj.current_value * obj.survival_relevance for obj in survival_objects) / len(survival_objects)
    
    def calculate_exploration_pressure_v2(self) -> float:
        """ssd_core_engine版: 探索圧の計算"""
        # 探索動機となるオブジェクト情報を作成
        exploration_objects = []
        
        # リソース不足圧
        resource_scarcity = max(0, (self.npc.hunger + self.npc.thirst - 120) / 80.0)
        if resource_scarcity > 0:
            resource_obj = ObjectInfo(
                id="resource_scarcity",
                type="exploration_trigger",
                current_value=resource_scarcity,
                survival_relevance=0.85,
                properties={"motivation": "resource_seeking", "intensity": resource_scarcity}
            )
            exploration_objects.append(resource_obj)
        
        # 環境制約圧（仮想的な領域制約）
        territory_pressure = 0.3  # 基本的な探索動機
        territory_obj = ObjectInfo(
            id="territory_constraint",
            type="exploration_trigger", 
            current_value=territory_pressure,
            survival_relevance=0.60,
            properties={"motivation": "territory_expansion", "base_pressure": territory_pressure}
        )
        exploration_objects.append(territory_obj)
        
        if not exploration_objects:
            return 0.0
        
        # SSD Core Engine で探索圧計算
        try:
            result = self.engine.step(
                perceived_objects=exploration_objects,
                available_actions=["evaluate_exploration"]
            )
            return result.get('total_meaning_pressure', 0.0)
        except Exception as e:
            # フォールバック: 単純計算
            return sum(obj.current_value * obj.survival_relevance for obj in exploration_objects) / len(exploration_objects)
    
    def consider_exploration_leap_v2(self, t: int, exploration_pressure: float) -> bool:
        """ssd_core_engine版: 探索モード跳躍判定"""
        # 跳躍判定のためのオブジェクト情報
        leap_objects = []
        
        # 探索圧オブジェクト
        pressure_obj = ObjectInfo(
            id="exploration_pressure",
            type="mode_decision",
            current_value=exploration_pressure,
            survival_relevance=0.80,
            properties={"decision_type": "exploration_leap", "pressure_level": exploration_pressure, "tick": t}
        )
        leap_objects.append(pressure_obj)
        
        # 現在状態の安定性
        stability = 1.0 - min(1.0, (self.npc.hunger + self.npc.thirst + self.npc.fatigue) / 300.0)
        stability_obj = ObjectInfo(
            id="current_stability", 
            type="mode_decision",
            current_value=1.0 - stability,  # 不安定さとして表現
            survival_relevance=0.75,
            properties={"decision_type": "stability_assessment", "stability_level": stability}
        )
        leap_objects.append(stability_obj)
        
        try:
            # SSD Core Engine で跳躍判定
            result = self.engine.step(
                perceived_objects=leap_objects,
                available_actions=["exploration_leap", "stay_settled"]
            )
            
            # 最適行動が探索跳躍かどうかで判定
            best_action = result.get('best_action', 'stay_settled')
            total_pressure = result.get('total_meaning_pressure', 0.0)
            
            # 閾値判定: 高圧力 + 探索行動選択
            return best_action == 'exploration_leap' or total_pressure > 0.7
            
        except Exception as e:
            # フォールバック: 従来ロジック
            return exploration_pressure > 0.6 + random.random() * 0.3
    
    def consider_mode_reversion_v2(self, t: int, exploration_pressure: float) -> bool:
        """ssd_core_engine版: 探索モード復帰判定"""
        # 復帰判定のためのオブジェクト情報
        reversion_objects = []
        
        # 現在の探索圧（低いほど復帰動機）
        low_pressure_obj = ObjectInfo(
            id="low_exploration_pressure",
            type="mode_decision",
            current_value=1.0 - exploration_pressure,  # 逆転: 低圧力 = 復帰動機
            survival_relevance=0.85,
            properties={"decision_type": "mode_reversion", "pressure_reduction": 1.0 - exploration_pressure}
        )
        reversion_objects.append(low_pressure_obj)
        
        # リソース安定性 
        resource_stability = 1.0 - min(1.0, (self.npc.hunger + self.npc.thirst) / 200.0)
        stability_obj = ObjectInfo(
            id="resource_stability",
            type="mode_decision",
            current_value=resource_stability,
            survival_relevance=0.70,
            properties={"decision_type": "stability_check", "resource_level": resource_stability}
        )
        reversion_objects.append(stability_obj)
        
        try:
            # SSD Core Engine で復帰判定
            result = self.engine.step(
                perceived_objects=reversion_objects,
                available_actions=["revert_to_settled", "continue_exploration"]
            )
            
            best_action = result.get('best_action', 'continue_exploration')
            total_stability = result.get('total_meaning_pressure', 0.0)
            
            # 復帰条件: 安定性が高く、復帰行動が選択された場合
            return best_action == 'revert_to_settled' or total_stability > 0.6
            
        except Exception as e:
            # フォールバック: 従来ロジック
            return exploration_pressure < 0.3 and resource_stability > 0.6
    
    # === SSD Core Engine による社会システム代替実装 ===
    
    def create_territory_v2(self, center: Tuple[int, int], radius: int = 5, owner: str = None) -> str:
        """SSD Core Engine版: 縄張り作成"""
        territory_id = f"territory_{center[0]}_{center[1]}_{owner or 'unknown'}"
        
        territory_obj = ObjectInfo(
            id=territory_id,
            type="social_territory",
            current_value=1.0,  # 初期状態では1人
            survival_relevance=0.7,
            properties={
                "center": center,
                "radius": radius, 
                "owner": owner,
                "members": {owner} if owner else set(),
                "established_tick": 0
            }
        )
        
        # SSD Engine の社会層に追加
        try:
            self.engine.add_structural_element(LayerType.SOCIAL, territory_id, territory_obj)
        except:
            # フォールバック: プロパティとして保存
            if not hasattr(self, '_territories'):
                self._territories = {}
            self._territories[territory_id] = territory_obj
            
        return territory_id
    
    def check_territory_contains_v2(self, territory_id: str, pos: Tuple[int, int]) -> bool:
        """SSD Core Engine版: 位置が縄張り内かチェック"""
        try:
            territory_data = self.engine.get_structural_element(LayerType.SOCIAL, territory_id)
            center = territory_data.properties["center"]
            radius = territory_data.properties["radius"]
            
            x, y = pos
            cx, cy = center
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            return distance <= radius
        except:
            # フォールバック
            if hasattr(self, '_territories') and territory_id in self._territories:
                territory_data = self._territories[territory_id]
                center = territory_data.properties["center"]
                radius = territory_data.properties["radius"]
                x, y = pos
                cx, cy = center
                return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= radius
            return False
    
    def create_hunt_group_v2(self, leader: str, target_prey_type: str = "medium_game") -> str:
        """SSD Core Engine版: 狩りグループ作成"""
        hunt_group_id = f"hunt_group_{leader}_{target_prey_type}"
        
        hunt_group_obj = ObjectInfo(
            id=hunt_group_id,
            type="social_cooperation",
            current_value=0.5,  # 初期成功率
            survival_relevance=0.8,
            properties={
                "leader": leader,
                "members": [leader],
                "target_prey_type": target_prey_type,
                "formation_tick": 0,
                "status": "forming",
                "hunt_location": None,
                "success": False,
                "meat_acquired": 0.0
            }
        )
        
        # SSD Engine の協力層に追加
        try:
            self.engine.add_structural_element(LayerType.SOCIAL, hunt_group_id, hunt_group_obj)
        except:
            # フォールバック
            if not hasattr(self, '_hunt_groups'):
                self._hunt_groups = {}
            self._hunt_groups[hunt_group_id] = hunt_group_obj
            
        return hunt_group_id
    
    def add_hunt_group_member_v2(self, hunt_group_id: str, member: str) -> bool:
        """SSD Core Engine版: 狩りグループにメンバー追加"""
        try:
            hunt_data = self.engine.get_structural_element(LayerType.SOCIAL, hunt_group_id)
            members = hunt_data.properties["members"]
            if member not in members:
                members.append(member)
                hunt_data.current_value = self._calculate_hunt_success_rate_v2(len(members), hunt_data.properties["target_prey_type"])
                self.engine.update_structural_element(LayerType.SOCIAL, hunt_group_id, hunt_data)
                return True
        except:
            # フォールバック
            if hasattr(self, '_hunt_groups') and hunt_group_id in self._hunt_groups:
                hunt_data = self._hunt_groups[hunt_group_id]
                members = hunt_data.properties["members"]
                if member not in members:
                    members.append(member)
                    hunt_data.current_value = self._calculate_hunt_success_rate_v2(len(members), hunt_data.properties["target_prey_type"])
                    return True
        return False
    
    def _calculate_hunt_success_rate_v2(self, member_count: int, target_prey_type: str) -> float:
        """狩りの成功率を計算（SSD版）"""
        # 簡単な計算（実際のconfigを使わない）
        base_rate = 0.3
        member_bonus = member_count * 0.15
        max_bonus = 0.4
        
        prey_difficulty = {"small_game": 0.0, "medium_game": 0.2, "large_game": 0.4}.get(target_prey_type, 0.2)
        
        success_rate = base_rate + min(member_bonus, max_bonus) - prey_difficulty
        return max(0.1, min(0.9, success_rate))
    
    def create_meat_resource_v2(self, amount: float, owner: str = None, hunt_group_id: str = None) -> str:
        """SSD Core Engine版: 肉リソース作成"""
        meat_id = f"meat_{owner or 'unknown'}_{hunt_group_id or 'solo'}"
        
        meat_obj = ObjectInfo(
            id=meat_id,
            type="resource_food",
            current_value=amount,  # 現在の栄養価
            survival_relevance=0.9,
            properties={
                "amount": amount,
                "freshness": 1.0,
                "owner": owner,
                "hunt_group_id": hunt_group_id,
                "creation_tick": 0,
                "shared_with": set()
            }
        )
        
        # SSD Engine のリソース層に追加
        try:
            self.engine.add_structural_element(LayerType.UPPER, meat_id, meat_obj)
        except:
            # フォールバック
            if not hasattr(self, '_meat_resources'):
                self._meat_resources = {}
            self._meat_resources[meat_id] = meat_obj
            
        return meat_id
    
    def decay_meat_v2(self, meat_id: str, ticks: int = 1) -> bool:
        """SSD Core Engine版: 肉の腐敗処理"""
        try:
            meat_data = self.engine.get_structural_element(LayerType.UPPER, meat_id)
            
            decay_rate = 0.05  # 5%/tick の腐敗率
            for _ in range(ticks):
                meat_data.properties["freshness"] *= (1.0 - decay_rate)
            
            # 効果的栄養価を更新
            effective_nutrition = meat_data.properties["amount"] * meat_data.properties["freshness"]
            meat_data.current_value = effective_nutrition
            
            # 完全に腐った場合
            if meat_data.properties["freshness"] < 0.1:
                meat_data.properties["amount"] = 0.0
                meat_data.current_value = 0.0
                self.engine.update_structural_element(LayerType.UPPER, meat_id, meat_data)
                return True  # 腐敗完了
            
            self.engine.update_structural_element(LayerType.UPPER, meat_id, meat_data)
            return False
            
        except:
            # フォールバック
            if hasattr(self, '_meat_resources') and meat_id in self._meat_resources:
                meat_data = self._meat_resources[meat_id]
                decay_rate = 0.05
                for _ in range(ticks):
                    meat_data.properties["freshness"] *= (1.0 - decay_rate)
                
                effective_nutrition = meat_data.properties["amount"] * meat_data.properties["freshness"]
                meat_data.current_value = effective_nutrition
                
                if meat_data.properties["freshness"] < 0.1:
                    meat_data.properties["amount"] = 0.0
                    meat_data.current_value = 0.0
                    return True
                return False
            return True  # 見つからない場合は腐敗とみなす


def run_ssd_enhanced_simulation(ticks: int = 200) -> Tuple[Dict, List, List, List]:
    """SSD Core Engine強化シミュレーション"""
    
    print("🚀 SSD Core Engine Enhanced Simulation with Territory System")
    print("Complete Integration: Modular SSD + Territory + Environment + Seasonal Systems")
    print("=" * 75)
    
    # 環境とシステムの初期化
    environment = Environment(
        size=DEFAULT_WORLD_SIZE,
        n_berry=48,
        n_hunt=50,
        n_water=35,
        n_caves=20,
        enable_smart_world=True,
    )
    
    seasonal_system = SeasonalSystem(season_length=50)  # より短い季節サイクル
    
    # NPCの作成とSSD強化
    npcs = []
    ssd_npcs = []
    roster = {}  # NPCクラスで必要
    
    personalities = [PIONEER, ADVENTURER, SCHOLAR, WARRIOR, HEALER, DIPLOMAT, GUARDIAN, TRACKER, 
                    LONER, NOMAD, FORAGER, LEADER, PIONEER, ADVENTURER, SCHOLAR, WARRIOR]
    personality_names = ["Pioneer", "Adventurer", "Scholar", "Warrior", "Healer", "Diplomat", 
                        "Guardian", "Tracker", "Loner", "Nomad", "Forager", "Leader", 
                        "Pioneer", "Adventurer", "Scholar", "Warrior"]
    greek_letters = ["Alpha", "Beta", "Gamma", "Delta", "Echo", "Zeta", "Eta", "Theta", 
                    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi"]
    
    for i in range(16):  # 旧システムと同じ16体に変更
        personality_idx = i % len(personalities)
        name = f"SSD_{personality_names[personality_idx]}_{greek_letters[i]}"
        start_pos = (random.randint(0, DEFAULT_WORLD_SIZE), random.randint(0, DEFAULT_WORLD_SIZE))
        
        npc = NPC(
            name=name,
            preset=personalities[personality_idx],
            env=environment,
            roster=roster,
            start_pos=start_pos
        )
        npcs.append(npc)
        roster[name] = npc
        
        # SSD Enhanced NPC作成と相互参照設定
        ssd_enhanced_npc = SSDEnhancedNPC(npc)
        ssd_npcs.append(ssd_enhanced_npc)
        
        # NPCからSSD Enhanced版へのアクセス設定
        npc.ssd_enhanced_ref = ssd_enhanced_npc
    
    # ログ記録
    ssd_logs = []
    env_logs = []
    seasonal_logs = []
    
    # 利用可能な行動
    available_actions = [
        'rest', 'explore', 'forage', 'hunt', 'seek_water', 
        'seek_shelter', 'investigate', 'avoid'
    ]
    
    print(f"📊 初期状態: NPCs={len(npcs)}, Environment=Ready, SSD=Enhanced")
    
    # メインシミュレーションループ
    for tick in range(ticks):
        # 季節更新
        current_season = seasonal_system.get_current_season(tick)
        seasonal_modifiers = seasonal_system.get_seasonal_modifiers(current_season)
        
        # 四半期ごとにプログレス表示
        if ticks > 4 and tick % (ticks // 4) == 0:
            season_name = seasonal_system.get_season_name(current_season)
            print(f"\n🔄 Tick {tick}/{ticks} - {season_name} - NPCs: {len([n for n in npcs if n.alive])}")
        
        tick_ssd_data = []
        
        # 各NPCの行動
        for ssd_npc in ssd_npcs:
            if not ssd_npc.npc.alive:
                continue
            
            # 環境知覚
            perceived_objects = ssd_npc.perceive_environment(environment)
            
            # SSD意思決定
            ssd_result = ssd_npc.make_decision(perceived_objects, available_actions)
            
            # 従来のNPCシステムで行動実行と縄張り経験処理
            territorial_result = {}
            if 'decision' in ssd_result and 'chosen_action' in ssd_result['decision']:
                chosen_action = ssd_result['decision']['chosen_action']
                
                # 行動の実行（簡略化）
                action_success = False
                if chosen_action == 'seek_water':
                    if hasattr(ssd_npc.npc, 'seek_water'):
                        action_success = True
                        ssd_npc.npc.seek_water(environment)
                        # 縄張り経験：水へのアクセス
                        territorial_result = ssd_npc.process_territorial_experience(
                            'water_access', 0.6, tick=tick
                        )
                elif chosen_action == 'forage':
                    if hasattr(ssd_npc.npc, 'forage'):
                        action_success = True
                        ssd_npc.npc.forage(environment)
                        # 縄張り経験：採食成功
                        territorial_result = ssd_npc.process_territorial_experience(
                            'successful_forage', 0.7, tick=tick
                        )
                elif chosen_action == 'hunt':
                    if hasattr(ssd_npc.npc, 'hunt'):
                        action_success = True
                        ssd_npc.npc.hunt(environment)
                        # 縄張り経験：狩猟活動
                        territorial_result = ssd_npc.process_territorial_experience(
                            'hunting_activity', 0.4, tick=tick
                        )
                elif chosen_action == 'rest':
                    if hasattr(ssd_npc.npc, 'rest'):
                        action_success = True
                        ssd_npc.npc.rest()
                    else:
                        # 休息の代替実装
                        action_success = True
                        ssd_npc.npc.fatigue = max(0, ssd_npc.npc.fatigue - 5)
                    
                    # 縄張り経験：安全な休息
                    territorial_result = ssd_npc.process_territorial_experience(
                        'safe_rest', 0.8, tick=tick
                    )
                elif chosen_action == 'explore':
                    # 探索の代替実装
                    action_success = True
                    ssd_npc.npc.x += random.randint(-3, 3)
                    ssd_npc.npc.y += random.randint(-3, 3)
                    ssd_npc.npc.fatigue += 2
                    # 縄張り経験：探索発見
                    territorial_result = ssd_npc.process_territorial_experience(
                        'exploration_discovery', 0.3, tick=tick
                    )
            
            # SSDデータの記録
            tick_data = {
                'npc': ssd_npc.npc.name,
                'decision': ssd_result.get('decision', {}),
                'system_state': ssd_result.get('system_state', {}),
                'thermal_dynamics': ssd_result.get('thermal_dynamics', {}),
                'predictions': ssd_result.get('predictions', []),
                'territorial_context': ssd_result.get('territorial_context', {}),
                'territorial_result': territorial_result
            }
            tick_ssd_data.append(tick_data)
            
            # 基本的な生存チェック
            ssd_npc.npc.hunger += 1
            ssd_npc.npc.thirst += 2
            ssd_npc.npc.fatigue += 1
            
            # 死亡判定（公平な比較のため閾値100で統一）
            if ssd_npc.npc.hunger > 100 or ssd_npc.npc.thirst > 100:
                ssd_npc.npc.alive = False
                print(f"💀 T{tick}: {ssd_npc.npc.name} died from starvation/dehydration! (Hunger: {ssd_npc.npc.hunger}, Thirst: {ssd_npc.npc.thirst})")
        
        # 縄張りシステムの境界減衰処理（10ティックごと）
        if TERRITORY_SYSTEM_AVAILABLE and tick % 10 == 0:
            for ssd_npc in ssd_npcs:
                if ssd_npc.territory_processor:
                    ssd_npc.territory_processor.decay_boundaries()
        
        # ログ記録
        ssd_logs.append(tick_ssd_data)
        env_logs.append({
            'tick': tick,
            'season': current_season,
            'survivors': len([n for n in npcs if n.alive])
        })
        seasonal_logs.append({
            'tick': tick,
            'season': current_season,
            'modifiers': seasonal_modifiers
        })
        
        # 環境更新（簡略化）
        environment.step()  # 環境の基本更新
        if hasattr(environment, 'ecosystem_step'):
            environment.ecosystem_step(npcs, tick)
    
    # 最終縄張り統計
    final_survivors = [n for n in npcs if n.alive]
    total_territories = 0
    total_collective_groups = 0
    
    if TERRITORY_SYSTEM_AVAILABLE:
        for ssd_npc in ssd_npcs:
            if ssd_npc.npc.alive and ssd_npc.territory_processor:
                territorial_state = ssd_npc.territory_processor.get_territorial_state(ssd_npc.npc.name)
                if territorial_state['has_territory']:
                    total_territories += 1
                total_collective_groups += len(territorial_state['collective_memberships'])
    
    print(f"\n✅ SSD縄張りシミュレーション完了!")
    print(f"📊 最終生存者: {len(final_survivors)}/{len(npcs)}")
    if TERRITORY_SYSTEM_AVAILABLE:
        print(f"🏘️ 確立された縄張り: {total_territories}")
        print(f"🤝 集団境界形成: {total_collective_groups}")
    
    return roster, ssd_logs, env_logs, seasonal_logs


def run_simulation(ticks: int = 200, analyze: bool = True) -> Tuple[dict, list, list, list]:
    """Programmatically run the SSD Core Engine enhanced simulation."""
    
    print("SSD Core Engine Enhanced Simulation - Advanced Structural Dynamics with Territory System")
    print("Complete Integration: SSD Modular Engine + Territory System + Environment + Seasonal Systems")
    if TERRITORY_SYSTEM_AVAILABLE:
        print("🏘️ Territory System: ENABLED - SSD理論準拠縄張りシステム")
    else:
        print("⚠️ Territory System: DISABLED - 基本SSD Engineのみ")
    print("=" * 90)
    
    try:
        # SSD強化シミュレーション実行
        roster, ssd_logs, env_logs, seasonal_logs = run_ssd_enhanced_simulation(ticks=ticks)
        
        if analyze:
            try:
                print("\n🔍 Basic analysis (detailed analysis temporarily disabled)")
                print("✅ Simulation completed successfully.")
            except Exception as e:
                print(f"⚠️ Analysis Error: {e}")
        
        return roster, ssd_logs, env_logs, seasonal_logs
        
    except Exception as e:
        print(f"❌ Simulation Error: {e}")
        import traceback
        traceback.print_exc()
        # Return empty results in case of error
        return {}, [], [], []


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the SSD Core Engine Enhanced NPC Simulation")
    parser.add_argument("--ticks", type=int, default=200, help="Number of ticks to simulate")
    parser.add_argument(
        "--no-analyze", action="store_true", help="Skip post-simulation analysis and report"
    )
    
    args = parser.parse_args()
    
    try:
        run_simulation(ticks=args.ticks, analyze=not args.no_analyze)
    except Exception as exc:
        print(f"💥 Simulation Execution Error: {exc}")
        import traceback
        traceback.print_exc()
