"""
SSD Enhanced NPC - SSD Core Engineと統合されたNPCクラス

このモジュールは、Structural System Dynamics (SSD) Core Engineを使用して
高度な意思決定と予測機能を持つNPCの実装を提供します。
"""

import sys
import os
from typing import Dict, List, Any, Tuple

# SSD Core Engine のインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ssd_core_engine'))
from ssd_core_engine.ssd_engine import create_ssd_engine, setup_basic_structure
from ssd_core_engine.ssd_types import LayerType, ObjectInfo

# ローカルインポート
from npc import NPC
from environment import Environment

try:
    from territory_system import TerritoryProcessor
    TERRITORY_SYSTEM_AVAILABLE = True
except ImportError:
    TERRITORY_SYSTEM_AVAILABLE = False
    TerritoryProcessor = None

from system_monitor import SystemMonitor


class SSDEnhancedNPC:
    """SSD Core Engine統合NPC"""

    def __init__(self, npc: NPC):
        self.npc = npc
        self.engine = create_ssd_engine(f"ssd_npc_{npc.name}")
        setup_basic_structure(self.engine)
        
        # システム監視
        self.monitor = SystemMonitor()

        # 縄張りシステムの初期化
        if TERRITORY_SYSTEM_AVAILABLE:
            self.territory_processor = TerritoryProcessor()
            self.territory_processor.initialize_npc_boundaries(npc.name)
        else:
            self.territory_processor = None

        # NPCの基本情報をSSDエンジンに登録
        self._register_npc_state()
        
        # 環境リソース情報をSSD予測システムに登録
        self._register_environment_resources()
        
        # NPCにSSDへの参照を設定
        self.npc.ssd_enhanced_ref = self

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
            "personality": getattr(self.npc, 'personality', 'Unknown'),
            "hunting_skill": getattr(self.npc, 'hunting_skill', 0.5),
            "cooperation_tendency": getattr(self.npc, 'cooperation_tendency', 0.5),
            "territorial_instinct": 0.7
        }
        self.engine.add_structural_element(LayerType.BASE, "instincts", base_data)

        # 認知層：知識と記憶
        cognitive_data = {
            "known_caves": len(getattr(self.npc, 'knowledge_caves', set())),
            "known_berries": len(getattr(self.npc, 'knowledge_berries', set())),
            "known_water": len(getattr(self.npc, 'knowledge_water', set())),
            "exploration_experience": getattr(self.npc, 'exploration_count', 0)
        }
        self.engine.add_structural_element(LayerType.COGNITIVE, "knowledge", cognitive_data)

        # 社会層：他NPCとの関係と協力状態
        social_data = {
            "current_group": getattr(self.npc, 'current_group', None),
            "reputation": 0.5,
            "leadership_tendency": getattr(self.npc, 'leadership', 0.3)
        }
        self.engine.add_structural_element(LayerType.SOCIAL, "relationships", social_data)

    def perceive_environment(self, environment: Environment) -> List[ObjectInfo]:
        """環境を知覚してSSDエンジン用のオブジェクト情報に変換"""
        objects = []
        
        # 洞窟の知覚
        for cave in environment.caves:
            if self._is_perceivable(cave.x, cave.y):
                cave_obj = ObjectInfo(
                    id=f"cave_{cave.x}_{cave.y}",
                    type="shelter",
                    current_value=cave.water_amount + cave.food_amount,
                    survival_relevance=0.8,
                    properties={
                        "position": (cave.x, cave.y),
                        "water": cave.water_amount,
                        "food": cave.food_amount,
                        "safety": 0.9
                    }
                )
                objects.append(cave_obj)

        # ベリーパッチの知覚
        npc_pos = (self.npc.x, self.npc.y)
        for patch_type, patches in environment.berry_patches.items():
            for patch_pos in patches:
                if self._is_perceivable(patch_pos[0], patch_pos[1]):
                    food_obj = ObjectInfo(
                        id=f"berries_{patch_pos[0]}_{patch_pos[1]}",
                        type="food",
                        current_value=environment.berry_nutrition.get(patch_type, 5),
                        survival_relevance=0.6,
                        properties={
                            "position": patch_pos,
                            "nutrition": environment.berry_nutrition.get(patch_type, 5),
                            "type": patch_type,
                            "renewable": True
                        }
                    )
                    objects.append(food_obj)

        # 認知限界
        return objects[:8]  # 認知限界として最大8つまで

    def make_decision(self, perceived_objects: List[ObjectInfo], available_actions: List[str]) -> Dict[str, Any]:
        """SSD Core Engineによる意思決定"""
        # NPCの現在状態を更新
        self._update_npc_state()

        # 縄張り的相互作用の評価
        territorial_context = {}
        if self.territory_processor:
            current_pos = (self.npc.x, self.npc.y)
            # 縄張り情報の取得と意思決定への反映は個別実装

        # SSD Engineによる意思決定
        result = self.engine.make_decision(
            perceived_objects=perceived_objects,
            available_actions=available_actions,
            context={"territorial": territorial_context}
        )

        # 縄張りコンテキストの追加
        if territorial_context:
            result['territorial_context'] = territorial_context

        return result

    def _register_environment_resources(self):
        """環境リソース情報をSSD予測システムに登録"""
        try:
            # 環境から食料リソースの総計を計算
            total_berries = 0
            total_cave_food = 0
            
            if hasattr(self.npc.env, 'berry_patches'):
                for patch_list in self.npc.env.berry_patches.values():
                    total_berries += len(patch_list)
            
            if hasattr(self.npc.env, 'caves'):
                for cave in self.npc.env.caves:
                    if hasattr(cave, 'food_amount'):
                        total_cave_food += cave.food_amount
            
            # 食料密度の計算
            area = getattr(self.npc.env, 'world_size', 100) ** 2
            food_density = (total_berries + total_cave_food) / area if area > 0 else 0.001
            
            # SSD Engineに環境食料状態を登録
            self.engine.add_perceived_object(ObjectInfo(
                id="food_resources",
                type="resource_environment",
                current_value=food_density,
                survival_relevance=0.95,
                properties={
                    "total_berries": total_berries,
                    "total_cave_food": total_cave_food,
                    "food_density": food_density,
                    "area": area,
                    "scarcity_level": "high" if food_density < 0.002 else "medium" if food_density < 0.005 else "low"
                }
            ))
            
        except Exception as e:
            # 環境リソース登録に失敗した場合は静かに続行
            pass

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
            # 更新に失敗した場合は静かに続行
            pass

    def _is_perceivable(self, x: int, y: int) -> bool:
        """位置が知覚範囲内かどうか判定"""
        distance = ((self.npc.x - x) ** 2 + (self.npc.y - y) ** 2) ** 0.5
        return distance <= 10  # 知覚範囲

    # === 縄張り防衛システム ===
    
    def check_territorial_threats(self, nearby_entities: List[Any], current_tick: int) -> Dict[str, Any]:
        """縄張りに対する脅威をチェックし、防衛行動を決定"""
        threat_response = {
            'threats_detected': [],
            'defense_actions': [],
            'cooperation_requests': [],
            'behavioral_changes': {}
        }
        
        if not self.territory_processor:
            return threat_response
            
        current_pos = (self.npc.x, self.npc.y)
        
        for entity in nearby_entities:
            threat_type = 'unknown'
            entity_pos = None
            
            # エンティティタイプの判定
            if hasattr(entity, 'aggression'):  # 捕食者
                threat_type = 'predator'
                entity_pos = (entity.x, entity.y)
            elif hasattr(entity, 'name') and entity != self.npc:  # 他のNPC
                threat_type = 'unknown_human'
                entity_pos = (entity.x, entity.y)
                
                # 既知の敵対関係チェック
                boundary = self.territory_processor.subjective_boundaries.get(self.npc.name)
                if boundary and boundary.is_outer(entity.name):
                    threat_type = 'hostile_human'
            
            if entity_pos:
                # 脅威侵入チェック
                intrusion_result = self.territory_processor.check_threat_intrusion(
                    self.npc.name, entity_pos, threat_type
                )
                
                if intrusion_result['is_threat_to_territory']:
                    threat_response['threats_detected'].append({
                        'entity': entity,
                        'type': threat_type,
                        'position': entity_pos,
                        'threat_level': intrusion_result['threat_level'],
                        'urgency': intrusion_result['defensive_urgency']
                    })
                    
                    # 防衛行動の処理
                    defense_result = self.territory_processor.process_territorial_defense(
                        self.npc.name, entity_pos, threat_type, current_tick
                    )
                    
                    threat_response['defense_actions'].append(defense_result)
                    
                    # 行動変更の適用
                    if defense_result['cooperation_boost'] > 0:
                        threat_response['behavioral_changes']['cooperation_tendency'] = \
                            threat_response['behavioral_changes'].get('cooperation_tendency', 0) + \
                            defense_result['cooperation_boost']
                    
                    if defense_result['fear_response'] > 0:
                        threat_response['behavioral_changes']['fear_level'] = \
                            max(threat_response['behavioral_changes'].get('fear_level', 0), 
                                defense_result['fear_response'])
                    
                    # 集団動員が必要な場合
                    if defense_result.get('group_mobilization'):
                        threat_response['cooperation_requests'].append({
                            'action': 'group_defense',
                            'target': entity_pos,
                            'urgency': 'high'
                        })
        
        return threat_response
    
    def process_territorial_experience(self, experience_type: str, location: Tuple[int, int], 
                                     valence: float, other_npcs: List[str] = None, 
                                     current_tick: int = 0) -> Dict[str, Any]:
        """縄張り経験を処理し、境界を更新"""
        if not self.territory_processor:
            return {}
            
        result = self.territory_processor.process_territorial_experience(
            self.npc.name, location, experience_type, valence, other_npcs, current_tick
        )
        
        # 縄張り変化をSSDエンジンに反映
        if result.get('territorial_changes'):
            for change in result['territorial_changes']:
                if change['action'] == 'territory_claimed':
                    # 縄張り確立の成功体験として記録
                    self.engine.add_perceived_object(ObjectInfo(
                        id=f"territory_{change['territory_id']}",
                        type="owned_territory",
                        current_value=change['safety_feeling'],
                        survival_relevance=0.8,
                        properties={
                            "center": change['location'],
                            "radius": change['radius'],
                            "established_tick": change['tick']
                        }
                    ))
        
        return result

    # === SSD統合意思決定メソッド ===
    
    def evaluate_hunt_opportunity_ssd(self, target_prey: Dict[str, Any]) -> float:
        """SSD統合狩猟機会評価"""
        try:
            # SSDレイヤー統合評価
            physical_suitability = self._evaluate_physical_hunting_capacity(target_prey)
            strategic_advantage = self._evaluate_strategic_hunting_advantage(target_prey)
            future_impact = self._evaluate_hunting_future_impact(target_prey)
            
            # SSD統合スコア
            ssd_score = (
                physical_suitability * 0.4 +
                strategic_advantage * 0.35 +
                future_impact * 0.25
            )
            
            return max(0.0, min(1.0, ssd_score))
            
        except Exception as e:
            return 0.3  # セーフティフォールバック
    
    def can_form_hunt_group_ssd(self) -> bool:
        """SSD統合狩猟グループ形成判定"""
        try:
            # SSDレイヤー統合判定
            physical_readiness = (self.npc.alive and 
                                self.npc.hunger < 80 and 
                                self.npc.fatigue < 85)
            
            strategic_value = (getattr(self.npc, 'hunting_skill', 0.5) > 0.2 and
                             self.npc.sociability > 0.3)
            
            future_benefit = self._assess_group_hunting_future_benefit()
            
            return physical_readiness and strategic_value and future_benefit > 0.4
            
        except Exception as e:
            return False
    
    def assess_territory_value_ssd(self, center_pos: Tuple[int, int], radius: int = 5) -> float:
        """SSD統合縄張り価値評価"""
        try:
            # SSDレイヤー統合評価
            resource_value = self._evaluate_territory_resources(center_pos, radius)
            strategic_value = self._evaluate_territory_strategic_position(center_pos, radius)
            future_potential = self._evaluate_territory_future_potential(center_pos, radius)
            
            # SSD統合スコア
            ssd_value = (
                resource_value * 0.5 +
                strategic_value * 0.3 +
                future_potential * 0.2
            )
            
            return max(0.0, min(1.0, ssd_value))
            
        except Exception as e:
            return 0.3
    
    def calculate_exploration_motivation_ssd(self) -> float:
        """SSD統合探索動機計算"""
        try:
            # SSDレイヤー統合計算
            survival_pressure = self._calculate_ssd_survival_pressure()
            curiosity_factor = self._calculate_ssd_curiosity_drive()
            strategic_exploration = self._calculate_ssd_strategic_exploration_need()
            
            # SSD統合動機
            ssd_motivation = (
                survival_pressure * 0.4 +
                curiosity_factor * 0.35 +
                strategic_exploration * 0.25
            )
            
            return max(0.0, min(1.0, ssd_motivation))
            
        except Exception as e:
            return 0.4
    
    # === SSDレイヤー統合評価ヘルパーメソッド ===
    
    def _evaluate_physical_hunting_capacity(self, target_prey: Dict[str, Any]) -> float:
        """物理層：狩猟体力評価"""
        prey_size = target_prey.get('size', 1.0)
        own_strength = getattr(self.npc, 'hunting_skill', 0.5)
        health_factor = (100 - self.npc.hunger) / 100.0
        stamina_factor = (100 - self.npc.fatigue) / 100.0
        
        strength_ratio = own_strength / max(0.1, prey_size)
        return min(1.0, strength_ratio * 0.7 * health_factor * stamina_factor)
    
    def _evaluate_strategic_hunting_advantage(self, target_prey: Dict[str, Any]) -> float:
        """中核層：戦略的狩猟優位性評価"""
        hunting_experience = getattr(self.npc, 'hunting_experience', 0.0)
        experience_factor = min(1.0, hunting_experience * 0.1)
        
        # 環境的優位性
        environmental_advantage = 0.5  # 基本値
        if hasattr(self.npc, 'env'):
            # 洞窟や障害物の近さによる戦術的優位性
            for cave_name in self.npc.knowledge_caves:
                if hasattr(self.npc.env, 'caves') and cave_name in self.npc.env.caves:
                    cave_pos = self.npc.env.caves[cave_name]
                    distance = self.npc.distance_to(cave_pos)
                    if distance <= 10:  # 近くに逃げ場がある
                        environmental_advantage += 0.2
                        break
        
        return (experience_factor * 0.6 + environmental_advantage * 0.4)
    
    def _evaluate_hunting_future_impact(self, target_prey: Dict[str, Any]) -> float:
        """上層：狩猟の未来影響評価"""
        prey_size = target_prey.get('size', 1.0)
        
        # 将来の食料確保への影響
        food_security_impact = min(1.0, prey_size * 0.4)
        
        # 狩猟スキル向上への影響
        skill_development_impact = min(0.3, prey_size * 0.2)
        
        # 社会的地位向上への影響
        social_status_impact = min(0.2, prey_size * 0.1) if self.npc.sociability > 0.5 else 0.0
        
        return food_security_impact + skill_development_impact + social_status_impact
    
    def _assess_group_hunting_future_benefit(self) -> float:
        """グループ狩猟の将来利益評価"""
        # 協力による成功率向上
        cooperation_benefit = self.npc.sociability * 0.6
        
        # 学習機会としての価値
        learning_benefit = (1.0 - getattr(self.npc, 'hunting_experience', 0.0) * 0.1) * 0.3
        
        # 社会的絆強化への影響
        social_benefit = self.npc.sociability * 0.4
        
        return cooperation_benefit + learning_benefit + social_benefit
    
    def _calculate_ssd_survival_pressure(self) -> float:
        """SSD生存圧力計算"""
        hunger_pressure = self.npc.hunger / 100.0
        thirst_pressure = self.npc.thirst / 100.0
        fatigue_pressure = self.npc.fatigue / 100.0
        
        # 非線形な圧力関数
        total_pressure = (hunger_pressure ** 1.2 + thirst_pressure ** 1.5 + fatigue_pressure ** 1.1) / 3.0
        return min(1.0, total_pressure)
    
    def _calculate_ssd_curiosity_drive(self) -> float:
        """SSD好奇心駆動計算"""
        base_curiosity = self.npc.curiosity
        
        # 知識の不足による好奇心増大
        knowledge_gap = max(0, 1.0 - (len(self.npc.knowledge_caves) + 
                                    len(self.npc.knowledge_water) + 
                                    len(self.npc.knowledge_berries)) * 0.05)
        
        # 探索モードによる増幅
        exploration_amplifier = 1.5 if getattr(self.npc, 'exploration_mode', False) else 1.0
        
        return min(1.0, base_curiosity * (1.0 + knowledge_gap * 0.5) * exploration_amplifier)
    
    def _calculate_ssd_strategic_exploration_need(self) -> float:
        """SSD戦略的探索必要性計算"""
        # 現在のリソース状況の不安定性
        resource_instability = 0.0
        if len(self.npc.knowledge_water) < 2:
            resource_instability += 0.3
        if len(self.npc.knowledge_caves) < 1:
            resource_instability += 0.2
        if len(self.npc.knowledge_berries) < 3:
            resource_instability += 0.1
        
        # 領土の持続可能性
        territory_sustainability = 0.7  # 基本値
        if hasattr(self.npc, 'territory') and self.npc.territory:
            territory_sustainability = 0.9  # 縄張り保有者は安定
        
        return min(1.0, resource_instability + (1.0 - territory_sustainability) * 0.5)
    
    def should_explore_leap_ssd(self) -> bool:
        """SSD統合探索跳躍判定"""
        try:
            exploration_motivation = self.calculate_exploration_motivation_ssd()
            current_crisis = getattr(self.npc, 'life_crisis', 0.0)
            
            # SSD層統合による跳躍判定
            physical_readiness = (self.npc.fatigue < 70 and self.npc.hunger < 90)
            strategic_necessity = exploration_motivation > 0.6
            future_opportunity_cost = self._evaluate_exploration_opportunity_cost()
            
            # SSD統合判定
            ssd_leap_score = (
                (1.0 if physical_readiness else 0.0) * 0.3 +
                exploration_motivation * 0.5 +
                (1.0 - future_opportunity_cost) * 0.2
            )
            
            leap_threshold = 0.65 - current_crisis * 0.15
            return ssd_leap_score > leap_threshold
            
        except Exception as e:
            return False
    
    def should_defend_territory_ssd(self, intruder_npc) -> bool:
        """SSD統合縄張り防衛判定"""
        try:
            if not self.npc.territory:
                return False
            
            # SSD層統合による防衛判定
            physical_capacity = (self.npc.alive and self.npc.fatigue < 80)
            
            # 社会的関係の評価
            trust_level = self.npc.trust_levels.get(intruder_npc.name, 0.5)
            social_threat = trust_level < 0.6
            
            # 戦略的価値の評価
            territory_value = self._evaluate_current_territory_strategic_value()
            strategic_importance = territory_value > 0.7
            
            # 未来影響の評価
            defense_consequences = self._evaluate_defense_consequences(intruder_npc)
            future_benefit = defense_consequences > 0.5
            
            # SSD統合判定
            return (physical_capacity and 
                   (social_threat or strategic_importance) and 
                   future_benefit)
            
        except Exception as e:
            return False
    
    def _evaluate_exploration_opportunity_cost(self) -> float:
        """探索の機会費用評価"""
        # 現在地での活動価値
        current_location_value = 0.5
        
        # 近くのリソース利用可能性
        nearby_resources = 0
        for cave_name in self.npc.knowledge_caves:
            if hasattr(self.npc.env, 'caves') and cave_name in self.npc.env.caves:
                cave_pos = self.npc.env.caves[cave_name]
                if self.npc.distance_to(cave_pos) <= 15:
                    nearby_resources += 1
        
        resource_accessibility = min(1.0, nearby_resources * 0.3)
        
        # 社会的機会の損失
        social_opportunity = self.npc.sociability * 0.4
        
        return (current_location_value * 0.4 + resource_accessibility * 0.4 + social_opportunity * 0.2)
    
    def _evaluate_current_territory_strategic_value(self) -> float:
        """現在縄張りの戦略的価値評価"""
        if not hasattr(self.npc, 'territory') or not self.npc.territory:
            return 0.0
        
        # 縄張り内のリソース密度
        territory_resources = 0
        territory_center = getattr(self.npc.territory, 'center', self.npc.pos)
        territory_radius = getattr(self.npc.territory, 'radius', 10)
        
        for cave_name in self.npc.knowledge_caves:
            if hasattr(self.npc.env, 'caves') and cave_name in self.npc.env.caves:
                cave_pos = self.npc.env.caves[cave_name]
                distance = ((territory_center[0] - cave_pos[0]) ** 2 + (territory_center[1] - cave_pos[1]) ** 2) ** 0.5
                if distance <= territory_radius:
                    territory_resources += 0.3
        
        return min(1.0, territory_resources)
    
    def _evaluate_defense_consequences(self, intruder_npc) -> float:
        """防衛行動の結果評価"""
        # 防衛成功の見込み
        own_strength = getattr(self.npc, 'hunting_skill', 0.5)
        intruder_strength = getattr(intruder_npc, 'hunting_skill', 0.5)
        success_probability = own_strength / (own_strength + intruder_strength)
        
        # 社会的影響
        social_standing_impact = 0.6 if self.npc.sociability > 0.5 else 0.3
        
        # 長期的縄張り安定性への影響
        territorial_stability_impact = 0.7
        
        return (success_probability * 0.5 + social_standing_impact * 0.3 + territorial_stability_impact * 0.2)
    
    def make_unified_decision_ssd(self) -> Dict[str, Any]:
        """SSD統一意思決定エンジン - NPCの全行動を統合制御"""
        try:
            # SSDレイヤー統合による状況評価
            situation_assessment = self._assess_current_situation()
            
            # 行動選択肢の評価
            action_options = self._evaluate_action_options(situation_assessment)
            
            # 最適行動の選択
            selected_action = self._select_optimal_action(action_options)
            
            # 決定の記録
            decision_record = {
                "decision_type": "unified_ssd",
                "selected_action": selected_action,
                "situation": situation_assessment,
                "alternatives": action_options,
                "timestamp": getattr(self.npc, 'current_tick', 0)
            }
            
            self.monitor.record_event("unified_decision", decision_record)
            
            return selected_action
            
        except Exception as e:
            # フォールバック決定
            return {
                "action": "survival_basic",
                "priority": 0.5,
                "confidence": 0.3,
                "error": str(e)
            }
    
    def _assess_current_situation(self) -> Dict[str, Any]:
        """現在状況のSSD統合評価"""
        # 物理層：生存状況
        survival_status = {
            "hunger_level": self.npc.hunger / 100.0,
            "thirst_level": self.npc.thirst / 100.0,
            "fatigue_level": self.npc.fatigue / 100.0,
            "survival_pressure": self._calculate_ssd_survival_pressure()
        }
        
        # 基層：本能的ニーズ
        instinctive_drives = {
            "exploration_drive": self._calculate_ssd_curiosity_drive(),
            "territorial_instinct": 0.6 if hasattr(self.npc, 'territory') and self.npc.territory else 0.3,
            "social_need": self.npc.sociability * (1.0 - len(self.npc.trust_levels) * 0.1)
        }
        
        # 中核層：学習された行動パターン
        learned_patterns = {
            "hunting_competence": getattr(self.npc, 'hunting_experience', 0.0),
            "exploration_experience": len(self.npc.knowledge_caves + self.npc.knowledge_water) * 0.1,
            "social_experience": len(self.npc.trust_levels) * 0.15
        }
        
        # 上層：戦略的機会
        strategic_opportunities = {
            "resource_opportunities": self._assess_nearby_resources(),
            "social_opportunities": self._assess_social_opportunities(),
            "territorial_opportunities": self._assess_territorial_opportunities()
        }
        
        return {
            "physical": survival_status,
            "instinctive": instinctive_drives, 
            "learned": learned_patterns,
            "strategic": strategic_opportunities
        }
    
    def _evaluate_action_options(self, situation: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """行動選択肢のSSD評価"""
        options = {}
        
        # 生存行動の評価
        options["survival"] = {
            "urgency": situation["physical"]["survival_pressure"],
            "success_probability": 0.8,
            "future_benefit": 0.6,
            "resource_cost": 0.3
        }
        
        # 探索行動の評価
        exploration_motivation = self.calculate_exploration_motivation_ssd()
        options["exploration"] = {
            "urgency": exploration_motivation,
            "success_probability": 0.6,
            "future_benefit": 0.9,
            "resource_cost": 0.5
        }
        
        # 狩猟行動の評価（仮想的な獲物を想定）
        average_prey = {"size": 1.2, "speed": 0.5, "defense": 0.3}
        hunt_opportunity = self.evaluate_hunt_opportunity_ssd(average_prey)
        options["hunting"] = {
            "urgency": hunt_opportunity * 0.8,
            "success_probability": hunt_opportunity,
            "future_benefit": 0.8,
            "resource_cost": 0.7
        }
        
        # 社会的行動の評価
        social_value = situation["instinctive"]["social_need"]
        options["social"] = {
            "urgency": social_value,
            "success_probability": self.npc.sociability,
            "future_benefit": 0.7,
            "resource_cost": 0.2
        }
        
        # 縄張り行動の評価
        territorial_value = situation["instinctive"]["territorial_instinct"]
        options["territorial"] = {
            "urgency": territorial_value,
            "success_probability": 0.7,
            "future_benefit": 0.8,
            "resource_cost": 0.4
        }
        
        return options
    
    def _select_optimal_action(self, options: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """SSD統合最適行動選択"""
        best_action = None
        best_score = -1.0
        
        for action_name, metrics in options.items():
            # SSD統合スコア計算
            ssd_score = (
                metrics["urgency"] * 0.35 +
                metrics["success_probability"] * 0.25 +
                metrics["future_benefit"] * 0.25 +
                (1.0 - metrics["resource_cost"]) * 0.15
            )
            
            if ssd_score > best_score:
                best_score = ssd_score
                best_action = action_name
        
        return {
            "action": best_action or "survival",
            "priority": best_score,
            "confidence": min(1.0, best_score + 0.2),
            "metrics": options.get(best_action, {})
        }
    
    def _assess_nearby_resources(self) -> float:
        """近隣リソースの評価"""
        resource_score = 0.0
        
        # 知っているリソースとの距離
        for cave_name in self.npc.knowledge_caves:
            if hasattr(self.npc.env, 'caves') and cave_name in self.npc.env.caves:
                cave_pos = self.npc.env.caves[cave_name]
                distance = self.npc.distance_to(cave_pos)
                if distance <= 20:
                    resource_score += max(0, 0.3 - distance * 0.01)
        
        for water_pos in self.npc.knowledge_water:
            distance = self.npc.distance_to(water_pos)
            if distance <= 15:
                resource_score += max(0, 0.2 - distance * 0.01)
        
        return min(1.0, resource_score)
    
    def _assess_social_opportunities(self) -> float:
        """社会的機会の評価"""
        if not hasattr(self.npc, 'env'):
            return 0.3
        
        nearby_npcs = 0
        for other_npc in getattr(self.npc.env, 'npcs', []):
            if other_npc != self.npc:
                distance = self.npc.distance_to(other_npc.pos)
                if distance <= 20:
                    nearby_npcs += 1
        
        return min(1.0, nearby_npcs * 0.2 * self.npc.sociability)
    
    def _assess_territorial_opportunities(self) -> float:
        """縄張り機会の評価"""
        if hasattr(self.npc, 'territory') and self.npc.territory:
            return 0.3  # 既に縄張りがある場合は低い
        
        # 現在地の縄張り価値
        current_territory_value = self.assess_territory_value_ssd(self.npc.pos, 8)
        
        return current_territory_value
    
    def _evaluate_territory_resources(self, center_pos: Tuple[int, int], radius: int) -> float:
        """縄張りリソース価値評価"""
        value_score = 0.0
        
        # 知っているリソースとの距離
        for cave_name in self.npc.knowledge_caves:
            if hasattr(self.npc.env, 'caves') and cave_name in self.npc.env.caves:
                cave_pos = self.npc.env.caves[cave_name]
                distance = ((center_pos[0] - cave_pos[0]) ** 2 + (center_pos[1] - cave_pos[1]) ** 2) ** 0.5
                if distance <= radius:
                    value_score += 0.3
        
        for water_pos in self.npc.knowledge_water:
            distance = ((center_pos[0] - water_pos[0]) ** 2 + (center_pos[1] - water_pos[1]) ** 2) ** 0.5
            if distance <= radius:
                value_score += 0.2
        
        for berry_pos in self.npc.knowledge_berries:
            distance = ((center_pos[0] - berry_pos[0]) ** 2 + (center_pos[1] - berry_pos[1]) ** 2) ** 0.5
            if distance <= radius:
                value_score += 0.1
        
        return min(1.0, value_score)
    
    def _evaluate_territory_strategic_position(self, center_pos: Tuple[int, int], radius: int) -> float:
        """縄張りの戦略的位置評価"""
        # 中央性評価（環境の中心に近いかどうか）
        if hasattr(self.npc, 'env'):
            env_center_x = getattr(self.npc.env, 'width', 100) // 2
            env_center_y = getattr(self.npc.env, 'height', 100) // 2
            distance_to_center = ((center_pos[0] - env_center_x) ** 2 + (center_pos[1] - env_center_y) ** 2) ** 0.5
            max_distance = ((env_center_x) ** 2 + (env_center_y) ** 2) ** 0.5
            centrality = 1.0 - (distance_to_center / max_distance)
        else:
            centrality = 0.5
        
        # 防御可能性（障害物や境界の近さ）
        defensibility = 0.5  # 基本値
        
        return (centrality * 0.6 + defensibility * 0.4)
    
    def _evaluate_territory_future_potential(self, center_pos: Tuple[int, int], radius: int) -> float:
        """縄張りの将来ポテンシャル評価"""
        # リソース再生可能性
        regeneration_potential = 0.7  # ベリーなどの再生
        
        # 拡張可能性
        expansion_potential = 0.6  # 周辺地域への拡張
        
        # 長期安定性
        stability_potential = 0.8  # 捕食者リスクの低さなど
        
        return (regeneration_potential * 0.4 + expansion_potential * 0.3 + stability_potential * 0.3)