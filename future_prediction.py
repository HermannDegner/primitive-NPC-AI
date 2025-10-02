#!/usr/bin/env python3
"""
Enhanced SSD Theory: 未来予測エンジン (Future Prediction Engine)
全ての行動判断の基盤となる未来状態予測システム
"""

import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum

class ActionType(Enum):
    """行動タイプの定義"""
    HUNT = "hunt"
    FORAGE = "forage" 
    DRINK = "drink"
    REST = "rest"
    EXPLORE = "explore"
    COOPERATE = "cooperate"
    SOCIALIZE = "socialize"
    MOVE = "move"
    TERRITORY = "territory"

@dataclass
class PredictedAction:
    """予測される行動"""
    action_type: ActionType
    duration: int  # 実行に要するティック数
    cost: Dict[str, float]  # 各リソースへの影響 {"fatigue": +20, "hunger": -30}
    benefit: Dict[str, float]  # 期待される利益
    probability: float  # 実行確率
    urgency: float  # 緊急度 (0-1)
    prerequisites: List[str]  # 前提条件
    
class FuturePredictionEngine:
    """未来予測エンジン"""
    
    def __init__(self, npc):
        self.npc = npc
        self.prediction_horizon = 20  # 20ティック先まで予測
        self.action_costs = self._initialize_action_costs()
        self.state_thresholds = self._initialize_thresholds()
        
    def _initialize_action_costs(self) -> Dict[ActionType, Dict[str, float]]:
        """行動コストの初期化"""
        return {
            ActionType.HUNT: {
                "fatigue": 25, "time": 3, "hunger_benefit": -40, 
                "success_rate": 0.4, "cooperation_bonus": 0.6
            },
            ActionType.FORAGE: {
                "fatigue": 15, "time": 2, "hunger_benefit": -25,
                "success_rate": 0.7
            },
            ActionType.DRINK: {
                "fatigue": 8, "time": 1, "thirst_benefit": -35,
                "success_rate": 0.9
            },
            ActionType.REST: {
                "fatigue": -30, "time": 1, "min_recovery": -20,
                "safety_bonus": 15
            },
            ActionType.EXPLORE: {
                "fatigue": 12, "time": 1, "discovery_chance": 0.3,
                "knowledge_gain": 0.8
            },
            ActionType.COOPERATE: {
                "fatigue": 20, "time": 4, "efficiency_bonus": 1.5,
                "social_benefit": 0.9
            },
            ActionType.MOVE: {
                "fatigue": 2, "time": 1, "per_distance": True
            }
        }
    
    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """状態閾値の初期化"""
        return {
            "fatigue": {
                "safe": 40, "caution": 70, "danger": 100, "critical": 130
            },
            "hunger": {
                "satisfied": 20, "mild": 40, "serious": 60, "critical": 80
            },
            "thirst": {
                "satisfied": 15, "mild": 30, "serious": 50, "critical": 70
            }
        }
    
    def predict_future_state(self, action_sequence: List[PredictedAction]) -> Dict[str, float]:
        """行動シーケンスに基づく未来状態の予測"""
        current_state = {
            "fatigue": self.npc.fatigue,
            "hunger": self.npc.hunger, 
            "thirst": self.npc.thirst,
            "time": 0
        }
        
        for action in action_sequence:
            # 行動実行による状態変化
            if action.action_type in self.action_costs:
                costs = self.action_costs[action.action_type]
                
                # 疲労変化
                if "fatigue" in costs:
                    current_state["fatigue"] += costs["fatigue"] * action.probability
                
                # 空腹変化 
                if "hunger_benefit" in costs:
                    success_rate = costs.get("success_rate", 1.0)
                    current_state["hunger"] += costs["hunger_benefit"] * success_rate * action.probability
                
                # 喉の渇き変化
                if "thirst_benefit" in costs:
                    success_rate = costs.get("success_rate", 1.0)
                    current_state["thirst"] += costs["thirst_benefit"] * success_rate * action.probability
                
                # 時間経過
                current_state["time"] += costs.get("time", 1)
            
            # 自然劣化（時間経過による）
            time_passed = costs.get("time", 1) if action.action_type in self.action_costs else 1
            current_state["fatigue"] += time_passed * 1.5  # 基礎疲労
            current_state["hunger"] += time_passed * 1.2   # 基礎空腹
            current_state["thirst"] += time_passed * 0.8   # 基礎渇き
        
        # 上限・下限の適用
        current_state["fatigue"] = max(0, min(150, current_state["fatigue"]))
        current_state["hunger"] = max(0, min(100, current_state["hunger"]))
        current_state["thirst"] = max(0, min(100, current_state["thirst"]))
        
        return current_state
    
    def generate_action_options(self) -> List[PredictedAction]:
        """現在状況に基づく行動選択肢の生成 - 昭夜サイクル + 季節予測対応"""
        options = []
        
        # 昭夜サイクル情報を取得
        is_night = self.npc.env.day_night.is_night()
        time_of_day = self.npc.env.day_night.time_of_day
        night_danger = self.npc.env.day_night.get_night_danger_multiplier()
        
        # 季節予測情報を取得
        current_seasonal_info = self._get_seasonal_prediction_context()
        seasonal_urgency_mod = current_seasonal_info.get('urgency_modifier', 1.0)
        resource_availability = current_seasonal_info.get('resource_availability', 1.0)
        
        # 協力可能性を事前に評価
        cooperation_possible = self._assess_cooperation_potential()
        
        # 基本的な生存行動（昭夜サイクル + 季節予測考慮）
        if self.npc.hunger > 25:
            # 狩猟オプション - 夜間リスク + 季節要素
            base_hunt_urgency = min(1.0, self.npc.hunger / 80)
            night_risk_penalty = 0.3 if is_night else 0.0  # 夜間リスク
            seasonal_boost = (seasonal_urgency_mod - 1.0) * 0.5  # 季節緊急度追加
            hunt_urgency = max(0.1, base_hunt_urgency - night_risk_penalty + seasonal_boost)
            
            # 季節による成功率調整
            seasonal_hunt_prob = 0.4 * resource_availability
            
            options.append(PredictedAction(
                action_type=ActionType.HUNT,
                duration=3,
                cost={"fatigue": 25},
                benefit={"hunger": -40 * resource_availability},
                probability=seasonal_hunt_prob + (0.2 if cooperation_possible else 0),
                urgency=min(1.0, hunt_urgency),
                prerequisites=["fatigue < 120"]
            ))
            
            # 採集オプション（季節統合版ベリー対応）
            # 季節によるベリー利用可能性を考慮
            berry_availability = resource_availability * 0.8  # ベリーは狩猟より季節影響大
            forage_benefit = -20 * berry_availability  # 季節に応じて採集効率変動
            
            options.append(PredictedAction(
                action_type=ActionType.FORAGE,
                duration=2, 
                cost={"fatigue": 15},
                benefit={"hunger": forage_benefit},
                probability=0.8 * berry_availability,  # 季節に応じて成功率変動
                urgency=hunt_urgency * 0.8,  # 狩猟より安全で手軽
                prerequisites=["fatigue < 100"]
            ))
        
        if self.npc.thirst > 20:
            # 水飲みオプション（季節統合版）
            base_thirst_urgency = min(1.0, self.npc.thirst / 60)  # より早期の反応
            seasonal_thirst_mod = seasonal_urgency_mod * 0.3  # 季節による渇き緊急度
            thirst_urgency = min(1.0, base_thirst_urgency + seasonal_thirst_mod)
            options.append(PredictedAction(
                action_type=ActionType.DRINK,
                duration=1,
                cost={"fatigue": 8},
                benefit={"thirst": -35},
                probability=0.9,
                urgency=thirst_urgency,
                prerequisites=[]  # 水源不明でも探索する
            ))
        
        # 休憩オプション - 常に検討
        rest_urgency = min(1.0, max(0, self.npc.fatigue - 40) / 80)
        options.append(PredictedAction(
            action_type=ActionType.REST,
            duration=1,
            cost={"fatigue": -30},
            benefit={"fatigue": -30},
            probability=1.0 if self._has_safe_shelter() else 0.7,
            urgency=rest_urgency,
            prerequisites=[]
        ))
        
        # 探索オプション - 昭夜サイクル + 季節予測に応じて調整
        if self.npc.exploration_mode or self.npc.curiosity > 0.5:
            base_explore_urgency = 0.3 + (self.npc.curiosity * 0.4)
            
            # 季節による探索緊急度調整
            upcoming_risk = current_seasonal_info.get('upcoming_season_risk', 0.0)
            if upcoming_risk > 0.2:  # 季節変化が近い場合、資源探索が重要
                base_explore_urgency += upcoming_risk * 0.5
            
            # 夜間は探索を制限、朝早い時間は奨励
            if is_night:
                time_modifier = -0.5  # 夜間は探索を避ける
                explore_probability = 0.1
            elif 6 <= time_of_day <= 10:  # 朝の探索タイム
                time_modifier = 0.3
                explore_probability = 0.5
            else:
                time_modifier = 0.0
                explore_probability = 0.3
                
            explore_urgency = max(0.05, base_explore_urgency + time_modifier)
            
            options.append(PredictedAction(
                action_type=ActionType.EXPLORE,
                duration=1,
                cost={"fatigue": 12, "danger_risk": 5 * night_danger},
                benefit={"knowledge": 0.8, "discovery_chance": 0.3 + (0.2 if not is_night else -0.1)},
                probability=explore_probability,
                urgency=explore_urgency,
                prerequisites=["fatigue < 100"] + (["daylight_preferred"] if is_night else [])
            ))
        
        # 協力オプション - 夜間は安全性向上
        if cooperation_possible:
            base_coop_urgency = 0.6 if self.npc.hunger > 40 else 0.3
            
            # 夜間は集団の安全性が重要
            night_safety_bonus = 0.3 if is_night else 0.0
            # 朝早い時間は狩猟に最適
            morning_hunt_bonus = 0.2 if 6 <= time_of_day <= 10 else 0.0
            
            coop_urgency = min(1.0, base_coop_urgency + night_safety_bonus + morning_hunt_bonus)
            
            # 夜間は協力率が向上（安全のため）
            cooperation_probability = 0.9 if is_night else 0.8
            
            options.append(PredictedAction(
                action_type=ActionType.COOPERATE,
                duration=4,
                cost={"fatigue": 20, "danger_risk": 2 * night_danger},
                benefit={
                    "hunt_success": 1.5 + morning_hunt_bonus,
                    "social": 0.9,
                    "safety": 15 if is_night else 5
                },
                probability=cooperation_probability,
                urgency=coop_urgency,
                prerequisites=["nearby_npcs", "fatigue < 120"]
            ))
        
        return options
    
    def evaluate_action_sequence(self, actions: List[PredictedAction]) -> float:
        """行動シーケンスの評価スコア計算"""
        future_state = self.predict_future_state(actions)
        
        # 生存リスク評価
        survival_risk = 0
        survival_risk += max(0, (future_state["fatigue"] - 100) / 50) * 10  # 疲労リスク
        survival_risk += max(0, (future_state["hunger"] - 70) / 30) * 8    # 飢餓リスク  
        survival_risk += max(0, (future_state["thirst"] - 60) / 40) * 6    # 脱水リスク
        
        # 効率性評価
        efficiency_score = 0
        total_duration = sum(action.duration for action in actions)
        if total_duration > 0:
            benefit_per_time = sum(
                sum(action.benefit.values()) * action.probability 
                for action in actions
            ) / total_duration
            efficiency_score = benefit_per_time
        
        # 緊急度考慮
        urgency_score = sum(action.urgency * action.probability for action in actions)
        
        # 総合評価（生存リスクを最優先）
        total_score = efficiency_score + urgency_score * 2 - survival_risk * 5
        
        return total_score
    
    def find_optimal_action_sequence(self, max_depth: int = 5) -> List[PredictedAction]:
        """最適な行動シーケンスの探索"""
        best_sequence = []
        best_score = float('-inf')
        
        # 再帰的に行動シーケンスを探索
        def explore_sequences(current_sequence: List[PredictedAction], depth: int):
            nonlocal best_sequence, best_score
            
            if depth >= max_depth:
                score = self.evaluate_action_sequence(current_sequence)
                if score > best_score:
                    best_score = score
                    best_sequence = current_sequence.copy()
                return
            
            # 次の行動選択肢を生成
            options = self.generate_action_options()
            
            for action in options:
                # 前提条件チェック
                if self._check_prerequisites(action, current_sequence):
                    new_sequence = current_sequence + [action]
                    explore_sequences(new_sequence, depth + 1)
        
        explore_sequences([], 0)
        return best_sequence
    
    def get_immediate_action_recommendation(self) -> Optional[PredictedAction]:
        """即座に実行すべき行動の推奨"""
        optimal_sequence = self.find_optimal_action_sequence(max_depth=3)
        
        if optimal_sequence:
            return optimal_sequence[0]
        
        # フォールバック: 緊急度最高の行動
        options = self.generate_action_options()
        if options:
            return max(options, key=lambda x: x.urgency * x.probability)
        
        return None
    
    def _assess_cooperation_potential(self) -> bool:
        """協力の可能性評価"""
        if not hasattr(self.npc, 'roster'):
            return False
            
        nearby_npcs = [
            npc for npc in self.npc.roster.values()
            if (npc.alive and npc != self.npc and 
                self.npc.distance_to(npc.pos()) <= 60 and
                npc.fatigue < 120)
        ]
        return len(nearby_npcs) >= 1
    
    def _has_safe_shelter(self) -> bool:
        """安全な避難所を持っているか"""
        return (hasattr(self.npc, 'knowledge_caves') and 
                len(self.npc.knowledge_caves) > 0)
    
    def _check_prerequisites(self, action: PredictedAction, current_sequence: List[PredictedAction]) -> bool:
        """行動の前提条件チェック"""
        future_state = self.predict_future_state(current_sequence)
        
        for prereq in action.prerequisites:
            if prereq == "fatigue < 120" and future_state["fatigue"] >= 120:
                return False
            elif prereq == "fatigue < 100" and future_state["fatigue"] >= 100:
                return False  
            elif prereq == "water_source_known" and not hasattr(self.npc, 'knowledge_water'):
                return False
            elif prereq == "nearby_npcs" and not self._assess_cooperation_potential():
                return False
                
        return True
    
    def get_prediction_summary(self) -> Dict:
        """予測システムの状況サマリー - 昭夜情報含む"""
        recommended_action = self.get_immediate_action_recommendation()
        optimal_sequence = self.find_optimal_action_sequence(max_depth=3)
        future_state = self.predict_future_state(optimal_sequence[:3])
        
        # 昭夜サイクル + 季節情報
        is_night = self.npc.env.day_night.is_night()
        time_of_day = self.npc.env.day_night.time_of_day
        seasonal_context = self._get_seasonal_prediction_context()
        
        return {
            "current_state": {
                "fatigue": self.npc.fatigue,
                "hunger": self.npc.hunger, 
                "thirst": self.npc.thirst
            },
            "time_context": {
                "time_of_day": time_of_day,
                "is_night": is_night,
                "phase": self._get_time_phase(time_of_day),
                "danger_level": self.npc.env.day_night.get_night_danger_multiplier()
            },
            "seasonal_context": {
                "urgency_modifier": seasonal_context['urgency_modifier'],
                "resource_availability": seasonal_context['resource_availability'], 
                "temperature_stress": seasonal_context['temperature_stress'],
                "upcoming_season_risk": seasonal_context['upcoming_season_risk']
            },
            "recommended_action": {
                "action": recommended_action.action_type.value if recommended_action else None,
                "urgency": recommended_action.urgency if recommended_action else 0,
                "rationale": self._get_action_rationale(recommended_action)
            },
            "future_state_3_steps": future_state,
            "survival_risk_level": self._calculate_survival_risk(future_state)
        }
    
    def _get_time_phase(self, hour: int) -> str:
        """時間帯のフェーズを取得"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _get_action_rationale(self, action: Optional[PredictedAction]) -> str:
        """行動の理由説明 - 昭夜情報含む"""
        if not action:
            return "no_viable_options"
        
        is_night = self.npc.env.day_night.is_night()
        time_of_day = self.npc.env.day_night.time_of_day
        
        # 季節+時間帯情報を含む理由説明
        seasonal_info = self._get_seasonal_prediction_context()
        
        time_prefix = "night_" if is_night else "day_"
        
        # 季節プレフィックスの追加
        if seasonal_info['urgency_modifier'] > 1.2:
            time_prefix = f"season_urgent_{time_prefix}"
        elif seasonal_info['upcoming_season_risk'] > 0.2:
            time_prefix = f"season_prep_{time_prefix}"
        elif seasonal_info['resource_availability'] < 0.8:
            time_prefix = f"season_scarce_{time_prefix}"
        
        if 6 <= time_of_day <= 10 and action.action_type.value in ["hunt", "cooperate"]:
            time_prefix = "morning_optimal_"
        elif 18 <= time_of_day <= 22 and action.action_type.value == "rest":
            time_prefix = "evening_rest_"
            
        if action.urgency > 0.8:
            return f"{time_prefix}critical_{action.action_type.value}"
        elif action.urgency > 0.6:
            return f"{time_prefix}urgent_{action.action_type.value}"
        elif action.probability > 0.8:
            return f"{time_prefix}reliable_{action.action_type.value}"
        else:
            return f"{time_prefix}strategic_{action.action_type.value}"
    
    def _calculate_survival_risk(self, state: Dict[str, float]) -> str:
        """生存リスクレベルの判定"""
        risk_factors = 0
        
        if state["fatigue"] > 120:
            risk_factors += 2
        elif state["fatigue"] > 100:
            risk_factors += 1
            
        if state["hunger"] > 70:
            risk_factors += 2
        elif state["hunger"] > 50:
            risk_factors += 1
            
        if state["thirst"] > 60:
            risk_factors += 2
        elif state["thirst"] > 40:
            risk_factors += 1
        
        if risk_factors >= 4:
            return "critical"
        elif risk_factors >= 2:
            return "high"
        elif risk_factors >= 1:
            return "moderate"
        else:
            return "low"
    
    def _get_seasonal_prediction_context(self) -> Dict[str, float]:
        """季節予測コンテキストの取得"""
        try:
            # 環境から季節修正係数を取得
            seasonal_modifier = getattr(self.npc.env, 'seasonal_modifier', {})
            
            # 季節による緊急度修正
            urgency_mod = 1.0
            resource_availability = seasonal_modifier.get('prey_activity', 1.0)
            
            # 冬や厳しい季節での緊急度上昇
            temperature_stress = seasonal_modifier.get('temperature_stress', 0.0)
            if temperature_stress > 0.2:
                urgency_mod += temperature_stress * 0.5
                
            # 資源不足時の緊急度上昇
            if resource_availability < 0.8:
                urgency_mod += (1.0 - resource_availability) * 0.4
                
            return {
                'urgency_modifier': urgency_mod,
                'resource_availability': resource_availability,
                'temperature_stress': temperature_stress,
                'season_pressure': seasonal_modifier.get('seasonal_pressure', 0.0),
                'upcoming_season_risk': self._predict_upcoming_season_risk()
            }
        except Exception:
            # フォールバック
            return {
                'urgency_modifier': 1.0,
                'resource_availability': 1.0,
                'temperature_stress': 0.0,
                'season_pressure': 0.0,
                'upcoming_season_risk': 0.0
            }
    
    def _predict_upcoming_season_risk(self) -> float:
        """次の季節のリスク予測"""
        try:
            # 簡単な季節サイクル予測（100ティック周期と仮定）
            current_tick = getattr(self.npc.env, 'tick', 0)
            season_progress = (current_tick % 100) / 100.0
            
            # 季節変化が近い場合のリスク上昇
            if season_progress > 0.8:  # 季節終了が近い
                return 0.3
            elif season_progress > 0.6:  # 季節中期
                return 0.1
            else:
                return 0.0
        except Exception:
            return 0.0