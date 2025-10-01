"""
SSD Village Simulation - SSD Core Theory
構造主観力学(SSD)理論に基づく原始村落シミュレーション - SSD理論コア
https://github.com/HermannDegner/Structural-Subjectivity-Dynamics

SSD理論の核心概念：
- 意味圧（Meaning Pressure）: 構造に変化を促す力
- 整合（Alignment）: 構造が意味圧に対して安定を保つ過程
- 跳躍（Leap）: 整合の限界を超えた時の非連続的変化
- 整合慣性（κ）: 過去の経験に基づく行動パターンの反復傾向
"""

import random
from collections import defaultdict


class SSDCore:
    """SSD理論の核心メカニズムを提供するクラス"""
    
    @staticmethod
    def calculate_meaning_pressure(factors):
        """意味圧の計算"""
        total_pressure = 0.0
        for factor_name, value in factors.items():
            total_pressure += value
        return min(3.0, max(0.0, total_pressure))
    
    @staticmethod
    def calculate_alignment_inertia(experience_dict, action_type, base_value=0.1):
        """整合慣性(κ)の計算"""
        return experience_dict.get(action_type, base_value)
    
    @staticmethod
    def should_leap(pressure, threshold, probability_factor=1.0):
        """跳躍判定"""
        if pressure <= threshold:
            return False
        
        leap_probability = min(0.9, (pressure - threshold) * probability_factor)
        return random.random() < leap_probability
    
    @staticmethod
    def update_alignment_inertia(kappa_dict, action_type, success=True, learning_rate=0.1):
        """整合慣性の更新"""
        current_kappa = kappa_dict.get(action_type, 0.1)
        
        if success:
            # 成功時は慣性を強化
            new_kappa = min(1.0, current_kappa + learning_rate * 0.1)
        else:
            # 失敗時は慣性を弱化
            new_kappa = max(0.05, current_kappa - learning_rate * 0.05)
            
        kappa_dict[action_type] = new_kappa
        return new_kappa
    
    @staticmethod
    def calculate_temperature_effect(base_temperature, stress_level):
        """温度パラメータの動的調整"""
        # ストレスが高いほど温度が上昇（より予測困難な行動）
        return base_temperature * (1.0 + stress_level * 0.5)


class ExplorationModeManager:
    """探索モードの管理"""
    
    def __init__(self, npc):
        self.npc = npc
        
    def calculate_life_crisis_pressure(self):
        """生命危機意味圧の計算"""
        dehydration_crisis = max(0, (self.npc.thirst - 140) / 60)
        starvation_crisis = max(0, (self.npc.hunger - 160) / 80)
        fatigue_crisis = max(0, (self.npc.fatigue - 80) / 40)
        
        return dehydration_crisis + starvation_crisis + fatigue_crisis
    
    def calculate_exploration_pressure(self):
        """探索意味圧の計算"""
        # 基本探索圧力
        knowledge_saturation = (len(self.npc.knowledge_caves) * 10 + 
                               len(self.npc.knowledge_water) * 15 + 
                               len(self.npc.knowledge_berries) * 5)
        boredom = min(1.0, (100 - knowledge_saturation) / 100)
        
        curiosity_drive = self.npc.curiosity * 0.8
        risk_seeking = self.npc.risk_tolerance * 0.6
        
        # 社会的要因
        isolation_pressure = (1.0 - self.npc.sociability * 0.5) if not self.npc.territory else 0.0
        
        total_pressure = boredom + curiosity_drive + risk_seeking + isolation_pressure
        return min(2.0, total_pressure)
    
    def consider_exploration_leap(self, t, exploration_pressure):
        """探索モードへの跳躍判定"""
        # 基本意味圧閾値（好奇心による調整）
        base_threshold = 0.8 + (1.0 - self.npc.curiosity) * 0.3
        
        # SSD理論：未処理圧(E)による跳躍閾値の動的調整
        leap_threshold = base_threshold - (self.npc.E * 0.2)
        leap_threshold = max(0.3, leap_threshold)
        
        # 整合慣性と意味圧による跳躍判定
        exploration_experience = self.npc.kappa.get("exploration", 0.1)
        leap_probability = min(0.9, (exploration_pressure + self.npc.E * 0.3) / 2.0) * (0.5 + exploration_experience)
        
        if exploration_pressure > leap_threshold and random.random() < leap_probability:
            # 探索モードへの跳躍的変化
            self.npc.exploration_mode = True
            self.npc.exploration_mode_start_tick = t
            self.npc.exploration_intensity = 1.0 + exploration_pressure * 0.5
            
            # SSD理論：跳躍によって未処理圧の一部が解消される
            self.npc.E = max(0.0, self.npc.E - (exploration_pressure * 0.3))
            
            self.npc.log.append({
                "t": t, 
                "name": self.npc.name, 
                "action": "exploration_mode_leap", 
                "pressure": exploration_pressure, 
                "E_before": self.npc.E + (exploration_pressure * 0.3),
                "E_after": self.npc.E, 
                "threshold": leap_threshold, 
                "intensity": self.npc.exploration_intensity
            })
            return True
        
        return False
    
    def consider_mode_reversion(self, t, exploration_pressure):
        """探索モードから通常モードへの復帰判定"""
        resource_stability = self._evaluate_resource_stability()
        settlement_coherence = self._calculate_settlement_coherence(exploration_pressure, resource_stability)
        mode_duration = t - self.npc.exploration_mode_start_tick
        
        # SSD理論：柔軟な復帰条件（重み付き総合判定）
        coherence_threshold = 0.7 - (self.npc.curiosity * 0.2)
        
        # 復帰要因の重み付き評価
        coherence_factor = min(1.0, settlement_coherence / coherence_threshold)
        duration_factor = min(1.0, mode_duration / 15.0)
        pressure_factor = max(0.0, (0.6 - exploration_pressure) / 0.6)
        energy_factor = max(0.0, (3.0 - self.npc.E) / 3.0)
        
        # 総合復帰スコア
        reversion_score = (coherence_factor * 0.4 + duration_factor * 0.2 + 
                          pressure_factor * 0.3 + energy_factor * 0.1)
        
        # 柔軟な復帰判定：スコア閾値 OR 強い単一要因
        if (reversion_score > 0.6 or
            (settlement_coherence >= coherence_threshold * 1.2) or
            (exploration_pressure < 0.2 and mode_duration > 8)):
            
            self.npc.exploration_mode = False
            self.npc.exploration_intensity = 1.0
            self.npc.kappa["exploration"] = max(0.05, self.npc.kappa.get("exploration", 0.1) * 0.9)
            
            self.npc.log.append({
                "t": t, 
                "name": self.npc.name, 
                "action": "exploration_mode_reversion", 
                "duration": mode_duration, 
                "reversion_score": reversion_score
            })
            return True
        
        return False
    
    def _evaluate_resource_stability(self):
        """リソース安定性の評価"""
        water_stability = min(1.0, len(self.npc.knowledge_water) / 3.0)
        food_stability = min(1.0, (len(self.npc.knowledge_berries) + len(self.npc.knowledge_hunting)) / 4.0)
        shelter_stability = min(1.0, len(self.npc.knowledge_caves) / 2.0)
        
        return (water_stability + food_stability + shelter_stability) / 3.0
    
    def _calculate_settlement_coherence(self, exploration_pressure, resource_stability):
        """定住整合慣性の計算"""
        # 基本的な定住要因
        resource_factor = resource_stability * 0.4
        pressure_factor = max(0.0, (1.0 - exploration_pressure)) * 0.3
        
        # 社会的要因
        social_factor = 0.0
        if self.npc.territory and self.npc.territory.members:
            social_factor = min(0.3, len(self.npc.territory.members) * 0.1)
        
        return resource_factor + pressure_factor + social_factor