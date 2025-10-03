"""
NPC Prediction Module - 予測システムと将来計画
"""

import sys
import os

# 親ディレクトリをパスに追加
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from systems.utils import log_event
except ImportError:
    # フォールバック実装
    def log_event(log_dict, event_data):
        print(f"LOG: {event_data}")


class NPCPredictionMixin:
    """NPC予測機能のミックスイン"""
    
    def execute_predicted_action(self, action, t):
        """予測されたアクションの実行"""
        action_type = action.action_type

        # 新しい予測システムと古い予測システム両方に対応
        survival_risk = 0.5
        rationale = "No prediction system"
        
        if hasattr(self, 'prediction_system') and self.prediction_system:
            # 新しいssd_core_engine予測システム使用
            perceived_objects = self._build_perceived_objects()
            crisis_info = self.prediction_system.detect_crisis_conditions(perceived_objects, t)
            survival_risk = crisis_info.get('cooperation_urgency', 0.5)
            rationale = f"SSD Prediction: {crisis_info.get('crisis_level', 'none')} crisis"
            
        elif hasattr(self, 'future_engine') and self.future_engine:
            # 古い予測システム（後方互換性）
            prediction_summary = self.future_engine.get_prediction_summary()
            survival_risk = prediction_summary.get("survival_risk_level", 0.5)
            rationale = prediction_summary.get("recommended_action", {}).get("rationale", "Legacy prediction")

        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": "future_prediction_decision",
                "recommended_action": action_type.value if hasattr(action_type, 'value') else str(action_type),
                "urgency": getattr(action, 'urgency', 0.5),
                "rationale": rationale,
                "survival_risk": survival_risk,
            },
        )

        # アクション実行
        action_str = action_type.value if hasattr(action_type, 'value') else str(action_type)
        
        if action_str == "hunt":
            self.execute_predictive_hunt(t)
        elif action_str == "forage":
            self.execute_predictive_forage(t)
        elif action_str == "drink":
            self.execute_predictive_drink(t)
        elif action_str == "rest":
            self.execute_predictive_rest(t)
        elif action_str == "explore":
            self.execute_predictive_explore(t)
        elif action_str == "cooperate":
            self.execute_predictive_cooperation(t)
        else:
            # 未対応のアクションはフォールバック
            if hasattr(self, 'explore_or_socialize'):
                self.explore_or_socialize(t)

    def execute_predictive_hunt(self, t):
        """予測的狩猟実行 - SSD Core Engine統合版"""
        cooperation_potential = False
        
        if hasattr(self, 'ssd_engine') and self.ssd_engine:
            # 完全なSSD Core Engine統合
            perceived_objects = self._build_ssd_objects()
            
            # SSD Core Engineによる意思決定
            step_result = self.ssd_engine.step(
                perceived_objects=perceived_objects,
                available_actions=["hunt", "group_hunt", "forage"]
            )
            
            # 協力判断
            if 'decision' in step_result:
                chosen_action = step_result['decision']['chosen_action']
                cooperation_potential = chosen_action == "group_hunt"
            
            # 危機検出による協力判断
            crisis_info = self.ssd_engine.detect_crisis_conditions()
            cooperation_urgency = crisis_info.get('cooperation_urgency', 0.0)
            cooperation_potential = cooperation_potential or cooperation_urgency > 0.3
            
        elif hasattr(self, 'prediction_system') and self.prediction_system:
            # 旧ssd_core_engine予測システム使用
            perceived_objects = self._build_perceived_objects()
            crisis_info = self.prediction_system.detect_crisis_conditions(perceived_objects, t)
            cooperation_urgency = crisis_info.get('cooperation_urgency', 0.0)
            cooperation_potential = cooperation_urgency > 0.3
            
        elif hasattr(self, 'future_engine') and self.future_engine:
            # レガシーシステム（後方互換性）
            cooperation_potential = self.future_engine._assess_cooperation_potential()

        if cooperation_potential and hasattr(self, 'organize_predictive_group_hunt'):
            if self.organize_predictive_group_hunt(t):
                log_event(
                    self.log, {"t": t, "name": self.name, "action": "predictive_group_hunt_organized"}
                )
                return

        # ソロ狩猟
        if hasattr(self, "attempt_solo_hunt"):
            self.attempt_solo_hunt(t)
        elif hasattr(self, "seek_food"):
            self.seek_food(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_solo_hunt"})

    def execute_predictive_forage(self, t):
        """予測的採集実行"""
        if hasattr(self, "seek_food"):
            self.seek_food(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_forage"})

    def execute_predictive_drink(self, t):
        """予測的水分補給実行"""
        if hasattr(self, "seek_water"):
            self.seek_water(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_drink"})

    def execute_predictive_rest(self, t):
        """予測的休憩実行"""
        if hasattr(self, "seek_rest"):
            self.seek_rest(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_rest"})

    def execute_predictive_explore(self, t):
        """予測的探索実行"""
        if hasattr(self, 'explore_for_resource'):
            self.explore_for_resource(t, "any")
        elif hasattr(self, 'explore_or_socialize'):
            self.explore_or_socialize(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_explore"})

    def predict_next_activities(self):
        """次の活動の予測"""
        predictions = {}
        
        # 基本的な生存需要予測
        # 1. 空腹度予測
        hunger_trend = self._predict_hunger_trend()
        predictions['hunger'] = {
            'current': getattr(self, 'hunger', 0),
            'predicted_6h': hunger_trend['6h'],
            'predicted_12h': hunger_trend['12h'],
            'urgency': hunger_trend['urgency']
        }
        
        # 2. 疲労度予測
        fatigue_trend = self._predict_fatigue_trend()
        predictions['fatigue'] = {
            'current': getattr(self, 'fatigue', 0),
            'predicted_6h': fatigue_trend['6h'], 
            'predicted_12h': fatigue_trend['12h'],
            'urgency': fatigue_trend['urgency']
        }
        
        # 3. 渇き予測
        thirst_trend = self._predict_thirst_trend()
        predictions['thirst'] = {
            'current': getattr(self, 'thirst', 0),
            'predicted_6h': thirst_trend['6h'],
            'predicted_12h': thirst_trend['12h'],
            'urgency': thirst_trend['urgency']
        }
        
        # 4. 推奨アクション
        predictions['recommended_action'] = self._get_recommended_action(predictions)
        
        return predictions

    def _build_perceived_objects(self):
        """SSD予測システム用のオブジェクト形式を構築"""
        from ssd_core_engine.ssd_types import ObjectInfo
        
        perceived_objects = {}
        
        # 健康状態
        perceived_objects["health"] = ObjectInfo(
            id=f"{self.name}_health",
            type="health",
            current_value=self.health,
            decline_rate=max(0.5, self.fatigue * 0.1),  # 疲労度に基づく減少率
            volatility=0.2
        )
        
        # 水分
        perceived_objects["water"] = ObjectInfo(
            id=f"{self.name}_water",
            type="water", 
            current_value=self.thirst,
            decline_rate=1.5,  # 基本減少率
            volatility=0.1
        )
        
        # 食料
        perceived_objects["food"] = ObjectInfo(
            id=f"{self.name}_food",
            type="food",
            current_value=self.hunger, 
            decline_rate=1.2,  # 基本減少率
            volatility=0.15
        )
        
        # エネルギー（疲労度の逆）
        perceived_objects["energy"] = ObjectInfo(
            id=f"{self.name}_energy",
            type="energy",
            current_value=100 - self.fatigue,
            decline_rate=0.8,
            volatility=0.25
        )
        
        return perceived_objects

    def _build_ssd_objects(self):
        """SSD Core Engine用のオブジェクトリストを構築"""
        from ssd_core_engine.ssd_types import ObjectInfo
        
        return [
            ObjectInfo(
                id=f"{self.name}_health",
                type="health",
                current_value=self.health,
                decline_rate=max(0.5, self.fatigue * 0.1),
                volatility=0.2,
                survival_relevance=1.0  # 生存に直結
            ),
            ObjectInfo(
                id=f"{self.name}_water", 
                type="water",
                current_value=self.thirst,
                decline_rate=1.5,
                volatility=0.1,
                survival_relevance=0.9
            ),
            ObjectInfo(
                id=f"{self.name}_food",
                type="food", 
                current_value=self.hunger,
                decline_rate=1.2,
                volatility=0.15,
                survival_relevance=0.8
            ),
            ObjectInfo(
                id=f"{self.name}_energy",
                type="energy",
                current_value=100 - self.fatigue,
                decline_rate=0.8,
                volatility=0.25,
                survival_relevance=0.7
            )
        ]

    def _predict_hunger_trend(self):
        """空腹度変化の予測"""
        current_hunger = getattr(self, 'hunger', 0)
        
        # 活動レベルによる消費予測
        activity_factor = 1.0
        if hasattr(self, 'current_activity'):
            if self.current_activity in ['hunting', 'exploration']:
                activity_factor = 1.5  # 高活動時は消費増加
            elif self.current_activity == 'resting':
                activity_factor = 0.7   # 休憩時は消費減少
        
        # 基本消費率（時間あたり）
        base_consumption = 2.0
        hourly_consumption = base_consumption * activity_factor
        
        # 予測値計算
        predicted_6h = min(150, current_hunger + (hourly_consumption * 6))
        predicted_12h = min(150, current_hunger + (hourly_consumption * 12))
        
        # 緊急度評価
        urgency = 0.0
        if predicted_6h > 100:
            urgency = 0.7
        elif predicted_12h > 100:
            urgency = 0.4
            
        return {
            '6h': predicted_6h,
            '12h': predicted_12h,
            'urgency': urgency
        }

    def _predict_fatigue_trend(self):
        """疲労度変化の予測"""
        current_fatigue = getattr(self, 'fatigue', 0)
        
        # 休憩状態なら回復、活動中なら蓄積
        if hasattr(self, 'current_activity') and self.current_activity == 'resting':
            # 休憩時は回復
            recovery_rate = 8.0  # 時間あたり回復量
            predicted_6h = max(0, current_fatigue - (recovery_rate * 6))
            predicted_12h = max(0, current_fatigue - (recovery_rate * 12))
            urgency = 0.0
        else:
            # 活動時は蓄積
            accumulation_rate = 3.0
            predicted_6h = min(150, current_fatigue + (accumulation_rate * 6))
            predicted_12h = min(150, current_fatigue + (accumulation_rate * 12))
            
            # 緊急度評価
            urgency = 0.0
            if predicted_6h > 120:
                urgency = 0.8
            elif predicted_12h > 100:
                urgency = 0.5
                
        return {
            '6h': predicted_6h,
            '12h': predicted_12h,
            'urgency': urgency
        }

    def _predict_thirst_trend(self):
        """渇き変化の予測"""
        current_thirst = getattr(self, 'thirst', 0)
        
        # 基本的な脱水率
        dehydration_rate = 3.0  # 時間あたり
        
        # 予測値計算
        predicted_6h = min(150, current_thirst + (dehydration_rate * 6))
        predicted_12h = min(150, current_thirst + (dehydration_rate * 12))
        
        # 緊急度評価
        urgency = 0.0
        if predicted_6h > 80:
            urgency = 0.6
        elif predicted_12h > 80:
            urgency = 0.3
            
        return {
            '6h': predicted_6h,
            '12h': predicted_12h,
            'urgency': urgency
        }

    def _get_recommended_action(self, predictions):
        """予測に基づく推奨アクション"""
        urgencies = {
            'hunt': predictions['hunger']['urgency'],
            'drink': predictions['thirst']['urgency'], 
            'rest': predictions['fatigue']['urgency'],
            'explore': 0.2  # ベースライン
        }
        
        # 最も緊急度の高いアクション
        recommended = max(urgencies.items(), key=lambda x: x[1])
        
        return {
            'action': recommended[0],
            'urgency': recommended[1],
            'rationale': f"Predicted {recommended[0]} urgency: {recommended[1]:.2f}"
        }

    def consider_predictive_rest(self, t):
        """予測的休憩の検討"""
        # 現在の疲労状況
        current_fatigue = getattr(self, 'fatigue', 0)
        
        # 将来の疲労予測
        future_fatigue = self._predict_fatigue_trend()
        
        # 予測的休憩の必要性評価
        predictive_rest_score = 0.0
        
        # 現在の疲労レベル
        if current_fatigue > 80:
            predictive_rest_score += 0.4
            
        # 将来の疲労予測
        if future_fatigue['6h'] > 120:
            predictive_rest_score += 0.5
            
        # 社会的要因（ケア対象がいる場合は休憩を優先）
        if hasattr(self, 'care_target') and self.care_target:
            predictive_rest_score += 0.3
            
        return predictive_rest_score > 0.6

    def assess_future_survival_risk(self, time_horizon=12):
        """将来の生存リスク評価"""
        predictions = self.predict_next_activities()
        
        risk_factors = []
        total_risk = 0.0
        
        # 各予測要素のリスク評価
        for need, data in predictions.items():
            if need in ['hunger', 'thirst', 'fatigue']:
                if data['urgency'] > 0.7:
                    risk_factors.append(f"Critical {need}")
                    total_risk += 0.4
                elif data['urgency'] > 0.4:
                    risk_factors.append(f"Moderate {need}")
                    total_risk += 0.2
        
        # 環境リスク要因
        if hasattr(self, 'env') and hasattr(self.env, 'seasonal_modifier'):
            seasonal_risk = 1.0 - self.env.seasonal_modifier.get('resource_availability', 1.0)
            total_risk += seasonal_risk * 0.3
            if seasonal_risk > 0.3:
                risk_factors.append("Environmental stress")
        
        return {
            'total_risk': min(1.0, total_risk),
            'risk_factors': risk_factors,
            'time_horizon': time_horizon,
            'survival_probability': 1.0 - min(1.0, total_risk)
        }