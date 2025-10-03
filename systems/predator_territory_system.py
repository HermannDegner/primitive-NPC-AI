#!/usr/bin/env python3
"""
Predator Territory System - 捕食者縄張りシステム
SSD理論に基づく捕食者の縄張り形成・防衛・拡張システム
"""

import math
import random
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class PredatorTerritoryInfo:
    """捕食者縄張り情報"""
    territory_id: str
    center: Tuple[float, float]
    radius: float
    owner_predator: str  # Predatorオブジェクトのid
    established_tick: int
    territorial_strength: float = 0.0
    hunt_success_count: int = 0
    last_intrusion_tick: int = 0
    prey_density: float = 0.0  # この縄張り内の獲物密度
    
    def contains(self, position: Tuple[float, float]) -> bool:
        """位置が縄張り内にあるかチェック"""
        x, y = position
        cx, cy = self.center
        return math.sqrt((x-cx)**2 + (y-cy)**2) <= self.radius
    
    def get_distance_from_center(self, position: Tuple[float, float]) -> float:
        """縄張り中心からの距離"""
        x, y = position
        cx, cy = self.center
        return math.sqrt((x-cx)**2 + (y-cy)**2)
    
    def get_intrusion_level(self, position: Tuple[float, float]) -> float:
        """侵入レベル（0.0=境界、1.0=中心）"""
        distance = self.get_distance_from_center(position)
        return max(0.0, 1.0 - (distance / self.radius))


class PredatorTerritorySystem:
    """捕食者縄張りシステム"""
    
    def __init__(self):
        # 縄張り管理
        self.territories: Dict[str, PredatorTerritoryInfo] = {}
        self.predator_territories: Dict[str, str] = {}  # {predator_id: territory_id}
        
        # 縄張り経験履歴
        self.territorial_experiences: Dict[str, List[Dict]] = defaultdict(list)
        
        # システム設定
        self.territory_establishment_threshold = 0.6  # 縄張り確立の閾値
        self.base_territory_radius = 25  # 基本縄張り半径
        self.max_territory_radius = 50   # 最大縄張り半径
        self.intrusion_aggression_multiplier = 2.0  # 侵入時の攻撃性倍率
        
    def process_predator_territorial_experience(self, predator, location: Tuple[float, float], 
                                              experience_type: str, success: bool, 
                                              current_tick: int) -> Dict[str, Any]:
        """捕食者の縄張り経験処理"""
        predator_id = f"predator_{id(predator)}"
        
        # 経験を記録
        experience = {
            'tick': current_tick,
            'location': location,
            'type': experience_type,  # 'hunt', 'patrol', 'intrusion_detected', 'territory_defense'
            'success': success,
            'aggression': predator.aggression
        }
        self.territorial_experiences[predator_id].append(experience)
        
        result = {
            'territorial_changes': [],
            'territory_established': False,
            'territory_expanded': False,
            'intrusion_detected': False
        }
        
        # 縄張り確立の評価
        if experience_type in ['hunt', 'patrol'] and success:
            territory_result = self._evaluate_territory_establishment(predator, location, current_tick)
            if territory_result:
                result['territorial_changes'].append(territory_result)
                result['territory_established'] = True
        
        # 既存縄張りの更新
        if predator_id in self.predator_territories:
            self._update_existing_territory(predator, experience, current_tick)
        
        return result
    
    def _evaluate_territory_establishment(self, predator, location: Tuple[float, float], 
                                        current_tick: int) -> Optional[Dict]:
        """縄張り確立の評価"""
        predator_id = f"predator_{id(predator)}"
        
        # 既に縄張りを持っている場合はスキップ
        if predator_id in self.predator_territories:
            return None
        
        # この場所での成功経験を計算
        recent_experiences = self.territorial_experiences[predator_id][-10:]  # 最近10回の経験
        local_successes = 0
        
        for exp in recent_experiences:
            exp_location = exp['location']
            distance = math.sqrt((location[0] - exp_location[0])**2 + (location[1] - exp_location[1])**2)
            if distance <= self.base_territory_radius and exp['success']:
                local_successes += 1
        
        # 縄張り確立の条件
        success_rate = local_successes / len(recent_experiences) if recent_experiences else 0
        establishment_score = success_rate * predator.aggression
        
        if establishment_score >= self.territory_establishment_threshold:
            # 縄張りを確立
            territory_id = f"predator_territory_{predator_id}_{current_tick}"
            
            # 半径は攻撃性と成功率によって決定
            radius = min(self.max_territory_radius, 
                        self.base_territory_radius + (establishment_score * 20))
            
            territory = PredatorTerritoryInfo(
                territory_id=territory_id,
                center=location,
                radius=radius,
                owner_predator=predator_id,
                established_tick=current_tick,
                territorial_strength=establishment_score
            )
            
            self.territories[territory_id] = territory
            self.predator_territories[predator_id] = territory_id
            
            # 捕食者の縄張り中心を更新
            predator.territory_center = location
            predator.territory_radius = radius
            
            return {
                'action': 'predator_territory_established',
                'predator_id': predator_id,
                'territory_id': territory_id,
                'location': location,
                'radius': radius,
                'establishment_score': establishment_score
            }
        
        return None
    
    def _update_existing_territory(self, predator, experience: Dict, current_tick: int):
        """既存縄張りの更新"""
        predator_id = f"predator_{id(predator)}"
        territory_id = self.predator_territories[predator_id]
        territory = self.territories[territory_id]
        
        # 狩猟成功時の縄張り強化
        if experience['type'] == 'hunt' and experience['success']:
            territory.hunt_success_count += 1
            territory.territorial_strength = min(1.0, territory.territorial_strength + 0.1)
            
            # 縄張り拡張の可能性
            if territory.hunt_success_count % 5 == 0:  # 5回成功毎に拡張チャンス
                new_radius = min(self.max_territory_radius, territory.radius + 5)
                if new_radius > territory.radius:
                    territory.radius = new_radius
                    predator.territory_radius = new_radius
    
    def check_territory_intrusion(self, intruder_pos: Tuple[float, float], 
                                 intruder_type: str) -> Dict[str, Any]:
        """縄張り侵入のチェック"""
        result = {
            'is_intrusion': False,
            'territory_owner': None,
            'intrusion_level': 0.0,
            'recommended_action': 'neutral'
        }
        
        for territory_id, territory in self.territories.items():
            if territory.contains(intruder_pos):
                intrusion_level = territory.get_intrusion_level(intruder_pos)
                
                result['is_intrusion'] = True
                result['territory_owner'] = territory.owner_predator
                result['intrusion_level'] = intrusion_level
                
                # 侵入者の種類による推奨行動
                if intruder_type == 'predator':
                    if intrusion_level > 0.7:
                        result['recommended_action'] = 'aggressive_chase'
                    elif intrusion_level > 0.3:
                        result['recommended_action'] = 'territorial_display'
                    else:
                        result['recommended_action'] = 'monitor'
                
                elif intruder_type == 'human':
                    if intrusion_level > 0.5:
                        result['recommended_action'] = 'hunt_opportunity'
                    else:
                        result['recommended_action'] = 'cautious_approach'
                
                elif intruder_type == 'prey':
                    result['recommended_action'] = 'hunt_immediately'
                
                break
        
        return result
    
    def get_territorial_behavior_modifier(self, predator, current_pos: Tuple[float, float]) -> Dict[str, float]:
        """縄張りに基づく行動修正値"""
        predator_id = f"predator_{id(predator)}"
        modifier = {
            'aggression_multiplier': 1.0,
            'hunt_success_bonus': 0.0,
            'movement_preference': 0.0,  # 正値=縄張り中心へ、負値=縄張り外へ
            'patrol_tendency': 0.0
        }
        
        if predator_id in self.predator_territories:
            territory_id = self.predator_territories[predator_id]
            territory = self.territories[territory_id]
            
            if territory.contains(current_pos):
                # 自分の縄張り内
                modifier['aggression_multiplier'] = 1.2  # 縄張り内では攻撃的
                modifier['hunt_success_bonus'] = 0.1     # 狩猟成功率ボーナス
                modifier['patrol_tendency'] = 0.3        # パトロール傾向
                
                # 中心に近いほど強いボーナス
                centrality = territory.get_intrusion_level(current_pos)
                modifier['hunt_success_bonus'] += centrality * 0.15
            
            else:
                # 縄張り外
                distance_to_territory = territory.get_distance_from_center(current_pos)
                if distance_to_territory < territory.radius * 1.5:
                    # 縄張り近辺 - 戻りたがる
                    modifier['movement_preference'] = 0.4
                else:
                    # 縄張りから遠い - 探索的になる
                    modifier['aggression_multiplier'] = 0.8
        
        return modifier
    
    def process_territory_defense(self, defender_predator, intruder_pos: Tuple[float, float], 
                                intruder_type: str, current_tick: int) -> Dict[str, Any]:
        """縄張り防衛行動の処理"""
        predator_id = f"predator_{id(defender_predator)}"
        
        if predator_id not in self.predator_territories:
            return {'defense_action': None}
        
        territory_id = self.predator_territories[predator_id]
        territory = self.territories[territory_id]
        
        if not territory.contains(intruder_pos):
            return {'defense_action': None}
        
        # 侵入レベルによる防衛行動
        intrusion_level = territory.get_intrusion_level(intruder_pos)
        territory.last_intrusion_tick = current_tick
        
        defense_result = {
            'defense_action': 'territorial_patrol',
            'aggression_boost': intrusion_level * self.intrusion_aggression_multiplier,
            'chase_priority': False
        }
        
        if intrusion_level > 0.8:  # 中心部への侵入
            defense_result['defense_action'] = 'aggressive_expulsion'
            defense_result['chase_priority'] = True
            
        elif intrusion_level > 0.5:  # 中程度の侵入
            defense_result['defense_action'] = 'threatening_approach'
            
        elif intrusion_level > 0.2:  # 境界近くの侵入
            defense_result['defense_action'] = 'monitoring_patrol'
        
        # 防衛経験を記録
        self.process_predator_territorial_experience(
            defender_predator, intruder_pos, 'territory_defense', 
            True, current_tick
        )
        
        return defense_result
    
    def get_territory_info(self, predator) -> Optional[Dict]:
        """捕食者の縄張り情報取得"""
        predator_id = f"predator_{id(predator)}"
        
        if predator_id not in self.predator_territories:
            return None
        
        territory_id = self.predator_territories[predator_id]
        territory = self.territories[territory_id]
        
        return {
            'territory_id': territory.territory_id,
            'center': territory.center,
            'radius': territory.radius,
            'established_tick': territory.established_tick,
            'territorial_strength': territory.territorial_strength,
            'hunt_success_count': territory.hunt_success_count,
            'prey_density': territory.prey_density,
            'last_intrusion_tick': territory.last_intrusion_tick
        }
    
    def update_prey_density(self, prey_animals: List):
        """各縄張りの獲物密度を更新"""
        for territory in self.territories.values():
            prey_count = 0
            for prey in prey_animals:
                if prey.alive and territory.contains((prey.x, prey.y)):
                    prey_count += 1
            
            # 縄張り面積で正規化
            area = math.pi * territory.radius ** 2
            territory.prey_density = prey_count / (area / 1000)  # 1000平方単位あたりの密度


# グローバルインスタンス
predator_territory_system = PredatorTerritorySystem()