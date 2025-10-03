"""
SSD探索システム - 探索圧と跳躍判定を管理

このモジュールは、NPCの探索行動に関する計算と判定を提供します。
"""

from typing import Tuple


class SSDExplorationSystem:
    """SSD Core Engineによる探索機能"""
    
    def __init__(self, ssd_enhanced_npc):
        self.enhanced_npc = ssd_enhanced_npc
        self.npc = ssd_enhanced_npc.npc
        self.engine = ssd_enhanced_npc.engine

    def calculate_life_crisis_pressure_v2(self) -> float:
        """ssd_core_engine版: 生命危機意味圧の計算"""
        try:
            # 基本生命危機レベル
            hunger_crisis = max(0, (self.npc.hunger - 40) / 60.0)
            thirst_crisis = max(0, (self.npc.thirst - 30) / 70.0)
            fatigue_crisis = max(0, (self.npc.fatigue - 50) / 50.0)
            
            base_crisis = max(hunger_crisis, thirst_crisis, fatigue_crisis)
            
            # 最近の失敗経験による圧力増加
            recent_failures = getattr(self.npc, 'recent_exploration_failures', 0)
            failure_pressure = min(0.3, recent_failures * 0.1)
            
            # 知識不足による圧力
            known_resources = (
                len(getattr(self.npc, 'knowledge_caves', set())) + 
                len(getattr(self.npc, 'knowledge_berries', set()))
            )
            knowledge_pressure = max(0, (5 - known_resources) / 10.0)
            
            # SSD Core Engine で意味圧計算
            try:
                crisis_info = self.engine.detect_crisis_conditions()
                if crisis_info and 'survival_threat' in crisis_info.get('detected_crises', []):
                    ssd_amplification = 1.5
                else:
                    ssd_amplification = 1.0
            except:
                ssd_amplification = 1.0
            
            total_pressure = (base_crisis + failure_pressure + knowledge_pressure) * ssd_amplification
            return min(1.0, total_pressure)
        
        except Exception as e:
            return base_crisis if 'base_crisis' in locals() else 0.5

    def calculate_exploration_pressure_v2(self) -> float:
        """ssd_core_engine版: 探索圧の計算"""
        try:
            # 基本探索圧計算
            base_exploration_urge = getattr(self.npc, 'curiosity', 0.5)
            
            # 停滞感による圧力増加
            if hasattr(self.npc, 'last_significant_discovery'):
                ticks_since_discovery = getattr(self.npc, 'current_tick', 0) - self.npc.last_significant_discovery
                stagnation_pressure = min(0.4, ticks_since_discovery / 50.0)
            else:
                stagnation_pressure = 0.2
            
            # 未知領域への好奇心
            unexplored_areas = max(0, 1.0 - (getattr(self.npc, 'exploration_count', 0) / 20.0))
            
            # 社会的探索圧（他NPCからの影響）
            social_pressure = 0.0
            if hasattr(self.npc, 'roster'):
                active_explorers = sum(1 for other_npc in self.npc.roster.values() 
                                     if other_npc != self.npc and getattr(other_npc, 'is_exploring', False))
                social_pressure = min(0.3, active_explorers * 0.1)
            
            # SSD Core Engine で探索圧計算
            try:
                prediction = self.engine.predict_future_state('exploration_value', steps_ahead=5)
                if hasattr(prediction, 'expected_value') and prediction.expected_value > 0.6:
                    ssd_enhancement = 1.3
                else:
                    ssd_enhancement = 1.0
            except:
                ssd_enhancement = 1.0
            
            total_pressure = (base_exploration_urge + stagnation_pressure + unexplored_areas + social_pressure) * ssd_enhancement
            return min(1.0, total_pressure)
        
        except Exception as e:
            return base_exploration_urge if 'base_exploration_urge' in locals() else 0.5

    def consider_exploration_leap_v2(self, t: int, exploration_pressure: float) -> bool:
        """ssd_core_engine版: 探索モード跳躍判定"""
        try:
            # 基本跳躍閾値
            base_threshold = 0.65
            
            # 個人特性による調整
            curiosity_modifier = (getattr(self.npc, 'curiosity', 0.5) - 0.5) * 0.2
            risk_taking = getattr(self.npc, 'risk_tolerance', 0.5)
            risk_modifier = (risk_taking - 0.5) * 0.15
            
            # 最近の成功/失敗による調整
            recent_successes = getattr(self.npc, 'recent_exploration_successes', 0)
            recent_failures = getattr(self.npc, 'recent_exploration_failures', 0)
            
            if recent_successes > recent_failures:
                confidence_modifier = min(0.2, (recent_successes - recent_failures) * 0.1)
            else:
                confidence_modifier = max(-0.2, (recent_successes - recent_failures) * 0.1)
            
            adjusted_threshold = base_threshold + curiosity_modifier + risk_modifier - confidence_modifier
            adjusted_threshold = max(0.3, min(0.9, adjusted_threshold))
            
            # SSD Core Engine で跳躍判定
            try:
                decision_result = self.engine.make_decision(
                    perceived_objects=[],
                    available_actions=['explore', 'stay'],
                    context={'exploration_pressure': exploration_pressure, 'threshold': adjusted_threshold}
                )
                
                if decision_result.get('recommended_action') == 'explore':
                    ssd_bonus = 0.1
                else:
                    ssd_bonus = 0.0
            except:
                ssd_bonus = 0.0
            
            final_pressure = exploration_pressure + ssd_bonus
            
            return final_pressure >= adjusted_threshold
        
        except Exception as e:
            return exploration_pressure >= 0.7

    def consider_mode_reversion_v2(self, t: int, exploration_pressure: float) -> bool:
        """ssd_core_engine版: 探索モード復帰判定"""
        try:
            # 基本復帰条件
            if not getattr(self.npc, 'is_exploring', False):
                return False
            
            # 生存ニーズによる強制復帰
            critical_hunger = self.npc.hunger > 80
            critical_thirst = self.npc.thirst > 70
            critical_fatigue = self.npc.fatigue > 90
            
            if critical_hunger or critical_thirst or critical_fatigue:
                return True
            
            # 探索目標達成による自然復帰
            exploration_duration = getattr(self.npc, 'exploration_duration', 0)
            max_duration = 15 + int(getattr(self.npc, 'curiosity', 0.5) * 10)
            
            if exploration_duration >= max_duration:
                return True
            
            # 満足度による復帰判定
            recent_discoveries = getattr(self.npc, 'recent_discoveries', 0)
            satisfaction_threshold = 2 + int(getattr(self.npc, 'curiosity', 0.5) * 2)
            
            # SSD Core Engine で復帰判定
            try:
                crisis_info = self.engine.detect_crisis_conditions()
                if crisis_info and len(crisis_info.get('detected_crises', [])) > 1:
                    ssd_urgency = True
                else:
                    ssd_urgency = False
            except:
                ssd_urgency = False
            
            if recent_discoveries >= satisfaction_threshold or ssd_urgency:
                return True
            
            # 探索圧の低下による復帰
            return exploration_pressure < 0.3
        
        except Exception as e:
            return True  # エラー時は安全側に倒して復帰