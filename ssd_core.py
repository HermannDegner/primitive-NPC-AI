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


class PhysicalStructureSystem:
    """SSD理論4層物理構造の実装"""
    
    def __init__(self, npc):
        self.npc = npc
        # 4層物理構造の初期化
        self.physical_layer = PhysicalLayer(npc)      # 物理構造
        self.foundation_layer = FoundationLayer(npc)  # 基層構造
        self.core_layer = CoreLayer(npc)              # 中核構造
        self.upper_layer = UpperLayer(npc)            # 上層構造
    
    def process_structural_dynamics(self, external_stimuli):
        """構造動力学の4層処理"""
        # 1. 物理構造：物理的制約と基本ニーズ
        physical_constraints = self.physical_layer.process_physical_constraints(external_stimuli)
        
        # 2. 基層構造：生存メカニズムと本能的反応
        survival_mechanisms = self.foundation_layer.process_survival_mechanisms(physical_constraints)
        
        # 3. 中核構造：行動選択と意思決定
        behavioral_decisions = self.core_layer.process_behavioral_decisions(survival_mechanisms)
        
        # 4. 上層構造：適応と学習
        adaptive_outputs = self.upper_layer.process_adaptive_learning(behavioral_decisions)
        
        return adaptive_outputs


class PhysicalLayer:
    """物理構造：生体システムの物理的制約と基本的な生理現象"""
    
    def __init__(self, npc):
        self.npc = npc
        self.physical_constants = {
            'metabolic_rate': 1.0,
            'energy_efficiency': 0.8,
            'physical_limits': {
                'max_hunger': 200,
                'max_thirst': 180,
                'max_fatigue': 120
            }
        }
    
    def process_physical_constraints(self, stimuli):
        """物理的制約の処理"""
        constraints = {}
        
        # 生理的制約の計算
        constraints['hunger_constraint'] = self._calculate_hunger_constraint()
        constraints['thirst_constraint'] = self._calculate_thirst_constraint()
        constraints['fatigue_constraint'] = self._calculate_fatigue_constraint()
        constraints['physical_capacity'] = self._calculate_physical_capacity()
        
        # 環境制約
        constraints['environmental_limits'] = self._assess_environmental_limits(stimuli)
        
        return constraints
    
    def _calculate_hunger_constraint(self):
        """飢餓制約の計算"""
        hunger_ratio = self.npc.hunger / self.physical_constants['physical_limits']['max_hunger']
        return min(2.0, hunger_ratio ** 2)
    
    def _calculate_thirst_constraint(self):
        """渇き制約の計算"""
        thirst_ratio = self.npc.thirst / self.physical_constants['physical_limits']['max_thirst']
        return min(3.0, (thirst_ratio ** 1.5) * 1.2)
    
    def _calculate_fatigue_constraint(self):
        """疲労制約の計算"""
        fatigue_ratio = self.npc.fatigue / self.physical_constants['physical_limits']['max_fatigue']
        return min(1.5, fatigue_ratio * 1.0)
    
    def _calculate_physical_capacity(self):
        """物理的行動能力の計算"""
        total_burden = (self.npc.hunger + self.npc.thirst + self.npc.fatigue) / 3.0
        return max(0.1, 1.0 - (total_burden / 150.0))
    
    def _assess_environmental_limits(self, stimuli):
        """環境制約の評価"""
        return stimuli.get('environmental_pressure', 0.0)
    
    def update_environmental_constraints(self, environmental_feedback):
        """スマート環境システムからの制約更新"""
        if not hasattr(self, 'environmental_constraints'):
            self.environmental_constraints = {}
        
        # 環境フィードバックを物理制約として統合
        self.environmental_constraints.update(environmental_feedback)
        
        # 物理制約への動的反映
        if 'resource_scarcity' in environmental_feedback:
            scarcity = environmental_feedback['resource_scarcity']
            # 資源不足による代謝効率の低下
            self.physical_constants['energy_efficiency'] *= (1.0 - scarcity * 0.2)
            self.physical_constants['energy_efficiency'] = max(0.5, self.physical_constants['energy_efficiency'])
        
        if 'climate_stress' in environmental_feedback:
            climate_stress = environmental_feedback['climate_stress']
            # 気候ストレスによる物理的負荷増加
            self.physical_constants['metabolic_rate'] *= (1.0 + climate_stress * 0.3)
            self.physical_constants['metabolic_rate'] = min(2.0, self.physical_constants['metabolic_rate'])


class FoundationLayer:
    """基層構造：生存本能、基本的な動機システム"""
    
    def __init__(self, npc):
        self.npc = npc
        self.survival_thresholds = {
            'critical_hunger': 160,
            'critical_thirst': 140,
            'critical_fatigue': 100
        }
    
    def process_survival_mechanisms(self, physical_constraints):
        """生存メカニズムの処理"""
        mechanisms = {}
        
        # 基本生存圧力
        mechanisms['survival_pressure'] = self._calculate_survival_pressure(physical_constraints)
        mechanisms['danger_response'] = self._assess_danger_response(physical_constraints)
        mechanisms['resource_urgency'] = self._calculate_resource_urgency(physical_constraints)
        
        # 本能的行動傾向
        mechanisms['instinctive_priorities'] = self._determine_instinctive_priorities(mechanisms)
        
        return mechanisms
    
    def _calculate_survival_pressure(self, constraints):
        """基本生存圧力の計算"""
        hunger_pressure = constraints['hunger_constraint']
        thirst_pressure = constraints['thirst_constraint']
        fatigue_pressure = constraints['fatigue_constraint']
        
        # 非線形結合：最も高い圧力が支配的
        max_pressure = max(hunger_pressure, thirst_pressure, fatigue_pressure)
        total_pressure = (hunger_pressure + thirst_pressure + fatigue_pressure) / 3.0
        
        return max_pressure * 0.7 + total_pressure * 0.3
    
    def _assess_danger_response(self, constraints):
        """危険反応の評価"""
        capacity = constraints['physical_capacity']
        danger_amplification = 2.0 - capacity
        return min(2.0, danger_amplification)
    
    def _calculate_resource_urgency(self, constraints):
        """資源緊急度の計算"""
        urgencies = {
            'water': constraints['thirst_constraint'],
            'food': constraints['hunger_constraint'],
            'rest': constraints['fatigue_constraint']
        }
        return urgencies
    
    def _determine_instinctive_priorities(self, mechanisms):
        """本能的優先順位の決定"""
        urgencies = mechanisms['resource_urgency']
        
        # 最も緊急な需要を特定
        max_urgency = max(urgencies.values())
        priority_resource = max(urgencies.keys(), key=lambda k: urgencies[k])
        
        return {
            'primary_need': priority_resource,
            'urgency_level': max_urgency,
            'focus_intensity': min(2.0, max_urgency * 0.8)
        }


class CoreLayer:
    """中核構造：意思決定、行動選択、意味圧の統合"""
    
    def __init__(self, npc):
        self.npc = npc
        self.decision_weights = {
            'survival_weight': 1.0,
            'exploration_weight': 0.3,
            'social_weight': 0.2,
            'efficiency_weight': 0.4
        }
    
    def process_behavioral_decisions(self, survival_mechanisms):
        """行動決定の処理"""
        decisions = {}
        
        # 意味圧の統合計算
        decisions['integrated_pressure'] = self._integrate_meaning_pressures(survival_mechanisms)
        
        # 行動選択の重み付け
        decisions['action_weights'] = self._calculate_action_weights(survival_mechanisms)
        
        # 跳躍条件の評価
        decisions['leap_conditions'] = self._evaluate_leap_conditions(decisions['integrated_pressure'])
        
        # 整合慣性の適用
        decisions['inertia_modulation'] = self._apply_alignment_inertia(decisions)
        
        return decisions
    
    def _integrate_meaning_pressures(self, mechanisms):
        """複数の意味圧の統合"""
        survival_pressure = mechanisms['survival_pressure']
        danger_pressure = mechanisms['danger_response']
        
        # 探索圧力（既存システムから）
        exploration_pressure = self._calculate_exploration_pressure()
        
        # 社会的圧力
        social_pressure = self._calculate_social_pressure()
        
        # 重み付き統合
        integrated = {
            'survival': survival_pressure * self.decision_weights['survival_weight'],
            'exploration': exploration_pressure * self.decision_weights['exploration_weight'],
            'social': social_pressure * self.decision_weights['social_weight'],
            'total': 0
        }
        
        integrated['total'] = sum(integrated[k] for k in ['survival', 'exploration', 'social'])
        
        return integrated
    
    def _calculate_exploration_pressure(self):
        """探索圧力の計算"""
        knowledge_saturation = (len(self.npc.knowledge_caves) * 10 + 
                               len(self.npc.knowledge_water) * 15 + 
                               len(self.npc.knowledge_berries) * 5)
        boredom = min(1.0, (100 - knowledge_saturation) / 100)
        curiosity_drive = self.npc.curiosity * 0.8
        
        return boredom + curiosity_drive
    
    def _calculate_social_pressure(self):
        """社会的圧力の計算"""
        if not self.npc.territory:
            return self.npc.sociability * 0.5
        
        group_size = len(self.npc.territory.members)
        optimal_size = 3 + self.npc.sociability * 2
        
        size_deviation = abs(group_size - optimal_size) / optimal_size
        return size_deviation * self.npc.sociability
    
    def _calculate_action_weights(self, mechanisms):
        """行動選択の重み計算"""
        priorities = mechanisms['instinctive_priorities']
        
        weights = {
            'foraging': 0.3,
            'exploration': 0.2,
            'resting': 0.2,
            'social': 0.1,
            'territory': 0.2
        }
        
        # 本能的優先度による調整
        if priorities['primary_need'] == 'food':
            weights['foraging'] *= (1.0 + priorities['urgency_level'])
        elif priorities['primary_need'] == 'water':
            weights['exploration'] *= (1.0 + priorities['urgency_level'])
        elif priorities['primary_need'] == 'rest':
            weights['resting'] *= (1.0 + priorities['urgency_level'])
        
        return weights
    
    def _evaluate_leap_conditions(self, integrated_pressure):
        """跳躍条件の評価"""
        total_pressure = integrated_pressure['total']
        current_E = self.npc.E
        
        # 動的閾値計算
        base_threshold = 1.2
        adjusted_threshold = base_threshold - (current_E * 0.15)
        
        leap_probability = 0.0
        if total_pressure > adjusted_threshold:
            leap_probability = min(0.9, (total_pressure - adjusted_threshold) * 0.8)
        
        return {
            'threshold': adjusted_threshold,
            'pressure': total_pressure,
            'probability': leap_probability,
            'ready': leap_probability > 0.3
        }
    
    def _apply_alignment_inertia(self, decisions):
        """整合慣性の適用"""
        action_weights = decisions['action_weights']
        modulated_weights = {}
        
        for action, weight in action_weights.items():
            kappa = self.npc.kappa.get(action, 0.1)
            # 慣性による重み調整
            modulated_weights[action] = weight * (0.5 + kappa * 1.0)
        
        return modulated_weights


class UpperLayer:
    """上層構造：学習、適応、長期戦略"""
    
    def __init__(self, npc):
        self.npc = npc
        self.learning_rates = {
            'success_rate': 0.1,
            'failure_rate': 0.05,
            'adaptation_rate': 0.08
        }
    
    def process_adaptive_learning(self, behavioral_decisions):
        """適応学習の処理"""
        adaptations = {}
        
        # 学習による適応
        adaptations['learning_updates'] = self._process_learning_updates(behavioral_decisions)
        
        # 長期戦略の調整
        adaptations['strategy_adaptation'] = self._adapt_long_term_strategy(behavioral_decisions)
        
        # 環境適応
        adaptations['environmental_adaptation'] = self._process_environmental_adaptation()
        
        # 最終的な行動決定
        adaptations['final_decision'] = self._make_final_decision(behavioral_decisions, adaptations)
        
        return adaptations
    
    def _process_learning_updates(self, decisions):
        """学習による更新処理"""
        updates = {}
        
        # 整合慣性の動的調整
        for action, weight in decisions['inertia_modulation'].items():
            current_kappa = self.npc.kappa.get(action, 0.1)
            
            # 使用頻度による慣性強化
            usage_boost = min(0.02, weight * 0.01)
            new_kappa = min(1.0, current_kappa + usage_boost)
            
            updates[action] = new_kappa
            self.npc.kappa[action] = new_kappa
        
        return updates
    
    def _adapt_long_term_strategy(self, decisions):
        """長期戦略の適応"""
        strategy = {}
        
        # 生存効率の評価
        survival_efficiency = self._evaluate_survival_efficiency()
        
        # 探索戦略の調整
        exploration_success_rate = self._calculate_exploration_success_rate()
        
        strategy['risk_tolerance_adjustment'] = self._adjust_risk_tolerance(survival_efficiency)
        strategy['exploration_strategy'] = self._adjust_exploration_strategy(exploration_success_rate)
        
        return strategy
    
    def _evaluate_survival_efficiency(self):
        """生存効率の評価"""
        recent_actions = self.npc.log[-10:] if len(self.npc.log) >= 10 else self.npc.log
        
        if not recent_actions:
            return 0.5
        
        successful_actions = [a for a in recent_actions if a.get('success', False)]
        return len(successful_actions) / len(recent_actions)
    
    def _calculate_exploration_success_rate(self):
        """探索成功率の計算"""
        exploration_actions = [a for a in self.npc.log if 'exploration' in a.get('action', '')]
        
        if not exploration_actions:
            return 0.5
        
        successful_explorations = [a for a in exploration_actions if a.get('discovery', False)]
        return len(successful_explorations) / len(exploration_actions) if exploration_actions else 0.5
    
    def _adjust_risk_tolerance(self, efficiency):
        """リスク許容度の調整"""
        if efficiency > 0.7:
            adjustment = min(0.05, (efficiency - 0.7) * 0.2)
            self.npc.risk_tolerance = min(1.0, self.npc.risk_tolerance + adjustment)
        elif efficiency < 0.3:
            adjustment = min(0.05, (0.3 - efficiency) * 0.2)
            self.npc.risk_tolerance = max(0.0, self.npc.risk_tolerance - adjustment)
        
        return self.npc.risk_tolerance
    
    def _adjust_exploration_strategy(self, success_rate):
        """探索戦略の調整"""
        if success_rate > 0.6:
            self.npc.curiosity = min(1.0, self.npc.curiosity + 0.02)
        elif success_rate < 0.3:
            self.npc.curiosity = max(0.1, self.npc.curiosity - 0.02)
        
        return self.npc.curiosity
    
    def _process_environmental_adaptation(self):
        """環境適応の処理"""
        adaptation = {}
        
        # 季節適応
        adaptation['seasonal'] = self._adapt_to_season()
        
        # 資源状況適応
        adaptation['resource'] = self._adapt_to_resource_availability()
        
        return adaptation
    
    def _adapt_to_season(self):
        """季節適応（将来実装用）"""
        return {'adaptation_level': 0.5}
    
    def receive_environmental_feedback(self, environmental_feedback):
        """スマート環境システムからのフィードバック受信"""
        if not hasattr(self, 'environmental_adaptation_data'):
            self.environmental_adaptation_data = {}
        
        # 環境フィードバックを適応データとして保存
        self.environmental_adaptation_data.update(environmental_feedback)
        
        # 適応機会に基づく学習率調整
        if 'adaptation_opportunity' in environmental_feedback:
            opportunity = environmental_feedback['adaptation_opportunity']
            
            # 適応機会が高い場合、学習率を向上
            if opportunity > 0.7:
                for key in self.learning_rates:
                    self.learning_rates[key] *= 1.1
                    self.learning_rates[key] = min(0.2, self.learning_rates[key])
            
            # 適応機会が低い場合、保守的な学習
            elif opportunity < 0.3:
                for key in self.learning_rates:
                    self.learning_rates[key] *= 0.9
                    self.learning_rates[key] = max(0.01, self.learning_rates[key])
        
        # 環境健康度による戦略調整
        if 'biodiversity_health' in environmental_feedback:
            biodiversity = environmental_feedback['biodiversity_health']
            
            # 生物多様性が高い環境では探索戦略を強化
            if biodiversity > 0.8 and hasattr(self.npc, 'curiosity'):
                self.npc.curiosity = min(1.0, self.npc.curiosity + 0.01)
            
            # 生物多様性が低い環境では慎重戦略を採用
            elif biodiversity < 0.4 and hasattr(self.npc, 'risk_tolerance'):
                self.npc.risk_tolerance = max(0.0, self.npc.risk_tolerance - 0.01)
    
    def _adapt_to_resource_availability(self):
        """資源可用性への適応"""
        water_knowledge = len(self.npc.knowledge_water)
        food_knowledge = len(self.npc.knowledge_berries) + len(getattr(self.npc, 'knowledge_hunting', []))
        
        if water_knowledge < 2:
            return {'priority': 'water_exploration', 'urgency': 0.8}
        elif food_knowledge < 3:
            return {'priority': 'food_exploration', 'urgency': 0.6}
        else:
            return {'priority': 'territory_consolidation', 'urgency': 0.3}
    
    def _make_final_decision(self, behavioral_decisions, adaptations):
        """最終的な行動決定"""
        leap_conditions = behavioral_decisions['leap_conditions']
        modulated_weights = behavioral_decisions['inertia_modulation']
        
        # 跳躍条件をチェック
        if leap_conditions['ready'] and random.random() < leap_conditions['probability']:
            decision_type = 'leap'
            # 未処理圧の部分解消
            self.npc.E = max(0.0, self.npc.E - (leap_conditions['pressure'] * 0.2))
        else:
            decision_type = 'normal'
        
        # 最も重みの高い行動を選択
        chosen_action = max(modulated_weights.keys(), key=lambda k: modulated_weights[k])
        
        return {
            'type': decision_type,
            'action': chosen_action,
            'weights': modulated_weights,
            'pressure_resolved': leap_conditions['pressure'] * 0.2 if decision_type == 'leap' else 0
        }


class SSDCore:
    """SSD理論の核心メカニズムを提供するクラス（4層物理構造統合版）"""
    
    def __init__(self, npc=None):
        self.physical_system = PhysicalStructureSystem(npc) if npc else None
    
    @staticmethod
    def calculate_meaning_pressure(factors, physical_system=None):
        """意味圧の計算（4層物理構造対応）"""
        if physical_system:
            # 4層物理構造を通じた処理
            processed_result = physical_system.process_structural_dynamics(factors)
            return processed_result['final_decision']['pressure_resolved']
        else:
            # 従来の直接計算
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
    """探索モードの管理（4層物理構造統合版）"""
    
    def __init__(self, npc):
        self.npc = npc
        # 4層物理構造システムの初期化
        self.physical_system = PhysicalStructureSystem(npc)
        
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