"""
SSD狩猟システム - 狩猟行動と集団管理

このモジュールは、NPCの狩猟行動、集団狩猟、狩猟成功判定に関する機能を提供します。
"""

from typing import Tuple, Dict, Any, List
import random
import math


class SSDHuntingSystem:
    """SSD Core Engine版狩猟システム"""
    
    def __init__(self, ssd_enhanced_npc):
        self.enhanced_npc = ssd_enhanced_npc
        self.npc = ssd_enhanced_npc.npc
        self.engine = ssd_enhanced_npc.engine

    def process_hunting_experience(self, hunt_result: str, prey_size: float, 
                                 group_size: int = 1, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """狩猟経験の処理（SSD版 - NPCの基本評価を拡張）"""
        try:
            # NPCの基本評価を活用
            base_opportunity = self.npc.evaluate_hunt_opportunity({"size": prey_size})
            
            # 狩猟結果の評価値計算（基本評価を考慮）
            if hunt_result == "success":
                # 基本評価が低いのに成功した場合はボーナス
                surprise_bonus = max(0, 0.2 - base_opportunity)
                experience_valence = min(1.0, prey_size * 0.3 + (group_size - 1) * 0.1 + surprise_bonus)
            elif hunt_result == "failure":
                # 基本評価が高かったのに失敗した場合はペナルティ軽減
                expectation_buffer = base_opportunity * 0.2
                experience_valence = -0.3 - (prey_size * 0.1) + expectation_buffer
            else:
                experience_valence = 0.0
            
            # 経験の構造化
            experience_data = {
                "type": "hunting",
                "subtype": hunt_result,
                "valence": experience_valence,
                "timestamp": getattr(self.npc, 'current_tick', 0),
                "context": {
                    "prey_size": prey_size,
                    "group_size": group_size,
                    "coordination": context.get("coordination", 0.5) if context else 0.5,
                    "base_opportunity": base_opportunity,  # NPCレベル評価を記録
                    **(context or {})
                }
            }
            
            # SSD Engineに経験を登録
            if hasattr(self.engine, 'process_experience'):
                return self.engine.process_experience(experience_data)
            else:
                return {"status": "processed", "experience": experience_data}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_hunt_group_v2(self, leader, target_prey, max_group_size: int = 4) -> List:
        """SSD Core Engine版: 狩猟グループ作成（NPCの基本判定を活用）"""
        try:
            # NPCの基本判定を活用
            if not leader.can_form_hunt_group():
                return [leader]
            
            hunt_group = [leader]
            
            # リーダーの近隣にいるNPCを探索
            nearby_npcs = []
            if hasattr(leader, 'env'):
                for other_npc in getattr(leader.env, 'npcs', []):
                    if (other_npc != leader and 
                        other_npc.can_form_hunt_group() and  # NPCレベル判定
                        self._calculate_distance(leader.pos, other_npc.pos) <= 15):
                        nearby_npcs.append(other_npc)
            
            # 狩猟適性の評価とグループ組成（NPCレベル協調性を活用）
            candidates = []
            for npc in nearby_npcs:
                # NPCレベルの協調性評価を基盤として使用
                base_coordination = leader.get_hunting_coordination_with(npc)
                ssd_enhancement = self._evaluate_ssd_hunting_enhancement(npc, target_prey, leader)
                
                total_suitability = base_coordination * 0.7 + ssd_enhancement * 0.3
                
                if total_suitability > 0.3:  # 最低適性閾値
                    candidates.append((npc, total_suitability))
            
            # 適性順でソートしてグループに追加
            candidates.sort(key=lambda x: x[1], reverse=True)
            for npc, _ in candidates[:max_group_size - 1]:
                hunt_group.append(npc)
            
            # SSD Engine に狩猟グループを社会構造として登録
            group_id = f"hunt_group_{id(leader)}_{getattr(leader, 'current_tick', 0)}"
            group_data = {
                "leader": leader.name,
                "members": [npc.name for npc in hunt_group],
                "target_prey": target_prey,
                "formation_tick": getattr(leader, 'current_tick', 0),
                "coordination_level": self._calculate_group_coordination(hunt_group)
            }
            
            if hasattr(self.engine, 'add_structural_element'):
                self.engine.add_structural_element('SOCIAL', group_id, group_data)
            
            return hunt_group
            
        except Exception as e:
            return [leader]  # フォールバック: リーダーのみ

    def calculate_hunt_success_v2(self, hunt_group: List, target_prey: Dict[str, Any]) -> Dict[str, Any]:
        """SSD Core Engine版: 狩猟成功判定"""
        try:
            # 基本パラメータの取得
            group_size = len(hunt_group)
            prey_size = target_prey.get('size', 1.0)
            prey_speed = target_prey.get('speed', 0.5)
            prey_defense = target_prey.get('defense', 0.3)
            
            # 集団の総合能力計算
            total_strength = 0
            total_coordination = 0
            for npc in hunt_group:
                npc_strength = getattr(npc, 'strength', 1.0)
                npc_agility = getattr(npc, 'agility', 1.0)
                total_strength += npc_strength + npc_agility * 0.5
                
                # 協調性の評価（簡易版）
                coordination_factor = self._assess_individual_coordination(npc, hunt_group[0])
                total_coordination += coordination_factor
            
            avg_coordination = total_coordination / group_size
            
            # 成功確率の計算
            # 基本成功率: 集団の強さ vs 獲物のサイズ
            strength_ratio = total_strength / (prey_size * 2.0)
            base_success = min(0.9, strength_ratio * 0.6)
            
            # 協調ボーナス
            coordination_bonus = avg_coordination * 0.2 * (group_size - 1)
            
            # 敏捷性ペナルティ
            agility_penalty = prey_speed * 0.3
            
            # 防御ペナルティ
            defense_penalty = prey_defense * 0.25
            
            # 最終成功確率
            success_probability = max(0.05, 
                base_success + coordination_bonus - agility_penalty - defense_penalty)
            
            # ランダム判定
            success = random.random() < success_probability
            
            # 結果の詳細
            result = {
                "success": success,
                "probability": success_probability,
                "group_size": group_size,
                "prey_data": target_prey,
                "factors": {
                    "strength_ratio": strength_ratio,
                    "coordination": avg_coordination,
                    "prey_advantages": prey_speed + prey_defense
                }
            }
            
            # SSD Engine に狩猟結果を記録
            if hasattr(self.engine, 'record_event'):
                self.engine.record_event('hunting_attempt', result)
            
            return result
            
        except Exception as e:
            # フォールバック判定
            return {
                "success": random.random() < 0.4,
                "probability": 0.4,
                "group_size": len(hunt_group),
                "error": str(e)
            }

    def _calculate_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """2点間の距離計算"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def _evaluate_ssd_hunting_enhancement(self, npc, target_prey: Dict[str, Any], leader) -> float:
        """SSDレベルの狩猟拡張評価（NPCの基本能力は既に考慮済み）"""
        try:
            # SSDエンジンによる将来予測評価
            future_success_probability = 0.5  # デフォルト
            if hasattr(self.engine, 'predict_outcome'):
                try:
                    prediction_context = {
                        "action": "hunt_collaboration",
                        "participants": [npc.name, leader.name],
                        "target": target_prey
                    }
                    future_prediction = self.engine.predict_outcome(prediction_context)
                    future_success_probability = future_prediction.get('success_probability', 0.5)
                except Exception:
                    pass
            
            # SSDレベルの環境的要因
            environmental_factor = 0.5
            if hasattr(npc, 'env'):
                # 現在の環境リスク
                predator_risk = getattr(npc.env, 'predator_risk_level', 0.3)
                weather_factor = getattr(npc.env, 'weather_hunting_modifier', 1.0)
                environmental_factor = (1.0 - predator_risk) * weather_factor * 0.8
            
            # SSD統合評価
            ssd_enhancement = (
                future_success_probability * 0.6 +
                environmental_factor * 0.4
            )
            
            return max(0.0, min(1.0, ssd_enhancement))
            
        except Exception as e:
            return 0.5  # デフォルト拡張評価

    def _calculate_group_coordination(self, hunt_group: List) -> float:
        """狩猟グループの協調レベル計算"""
        if len(hunt_group) <= 1:
            return 1.0
        
        try:
            total_coordination = 0
            pair_count = 0
            
            for i, npc1 in enumerate(hunt_group):
                for npc2 in hunt_group[i+1:]:
                    # 能力の類似性による協調性
                    strength_diff = abs(getattr(npc1, 'strength', 1.0) - getattr(npc2, 'strength', 1.0))
                    agility_diff = abs(getattr(npc1, 'agility', 1.0) - getattr(npc2, 'agility', 1.0))
                    
                    similarity = 1.0 - (strength_diff + agility_diff) * 0.25
                    total_coordination += max(0.3, similarity)
                    pair_count += 1
            
            return total_coordination / pair_count if pair_count > 0 else 0.8
            
        except Exception as e:
            return 0.6  # デフォルト協調性

    def _assess_individual_coordination(self, npc, leader) -> float:
        """個別NPCのリーダーとの協調性評価"""
        try:
            # 能力差による協調性
            strength_diff = abs(getattr(npc, 'strength', 1.0) - getattr(leader, 'strength', 1.0))
            agility_diff = abs(getattr(npc, 'agility', 1.0) - getattr(leader, 'agility', 1.0))
            
            ability_coordination = 1.0 - (strength_diff + agility_diff) * 0.2
            
            # 距離による協調性（近いほど良い）
            distance = self._calculate_distance(npc.pos, leader.pos)
            distance_coordination = max(0.3, 1.0 - distance * 0.05)
            
            return (ability_coordination + distance_coordination) / 2.0
            
        except Exception as e:
            return 0.6  # デフォルト値