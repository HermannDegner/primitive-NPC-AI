"""
SSD Village Simulation - NPC Agent
構造主観力学(SSD)理論に基づく原始村落シミュレーション - NPCエージェント
"""

import random
import math
from collections import defaultdict

from config import *
from social import Territory
from ssd_core import ExplorationModeManager
from utils import distance_between, find_nearest_position, probability_check, log_event


class NPC:
    """SSD理論に基づくNPCエージェント"""
    
    def __init__(self, name, preset, env, roster, start_pos):
        self.name = name
        self.env = env
        self.roster = roster
        self.x, self.y = start_pos
        
        # 基本状態
        self.hunger = 20.0
        self.thirst = 10.0
        self.fatigue = 20.0
        self.alive = True
        self.log = []
        
        # 性格特性（SSD理論）
        self.curiosity = preset.get("curiosity", 0.5)
        self.sociability = preset.get("sociability", 0.5)
        self.risk_tolerance = preset.get("risk_tolerance", 0.5)
        self.empathy = preset.get("empathy", 0.6)
        
        # SSD理論パラメータ
        self.kappa = defaultdict(lambda: DEFAULT_KAPPA)  # 整合慣性
        self.E = 0.0  # 未処理圧
        self.T = DEFAULT_TEMPERATURE  # 温度パラメータ
        self.T0 = DEFAULT_TEMPERATURE
        
        # 探索モード（SSD理論の跳躍メカニズム）
        self.exploration_mode = False
        self.exploration_mode_start_tick = 0
        self.exploration_intensity = 1.0
        self.exploration_manager = ExplorationModeManager(self)
        
        # 知識と記憶
        self.knowledge_caves = set()
        self.knowledge_water = set()
        self.knowledge_berries = set()
        self.knowledge_hunting = set()
        
        # 縄張りとコミュニティ
        self.territory = None
        self.territory_claim_threshold = 0.8
        
        # 基本パラメータ
        self.age = random.randint(20, 40)
        self.experience_points = 0.0
        self.lifetime_discoveries = 0
        
        # 初期知識の設定
        self._initialize_knowledge()
    
    def _initialize_knowledge(self):
        """初期知識の設定"""
        # 近くのリソースを初期知識として追加
        initial_cave = self.env.nearest_nodes(self.pos(), self.env.caves, k=1)
        if initial_cave:
            cave_name = next(k for k, v in self.env.caves.items() if v == initial_cave[0])
            self.knowledge_caves.add(cave_name)
            
        initial_waters = self.env.nearest_nodes(self.pos(), self.env.water_sources, k=2)
        for water_pos in initial_waters:
            water_name = next(k for k, v in self.env.water_sources.items() if v == water_pos)
            self.knowledge_water.add(water_name)
    
    def pos(self):
        """現在位置を取得"""
        return (self.x, self.y)
    
    def distance_to(self, pos):
        """指定位置までの距離を計算"""
        return distance_between(self.pos(), pos)
    
    def move_towards(self, target):
        """目標に向かって移動"""
        tx, ty = target
        dx = tx - self.x
        dy = ty - self.y
        
        if dx == 0 and dy == 0:
            return
            
        # 移動距離を正規化
        distance = math.sqrt(dx**2 + dy**2)
        move_distance = min(2, distance)
        
        if distance > 0:
            self.x += int(dx / distance * move_distance)
            self.y += int(dy / distance * move_distance)
            
        self.x = max(0, min(self.env.size-1, self.x))
        self.y = max(0, min(self.env.size-1, self.y))
    
    def consider_exploration_mode_shift(self, t):
        """SSD理論：意味圧に応じた探索モードの跳躍的変化と復帰判定"""
        life_crisis = self.exploration_manager.calculate_life_crisis_pressure()
        
        if self.exploration_mode:
            # 命の危機時は即座に探索モードを終了
            if life_crisis > 1.5:
                self.exploration_mode = False
                log_event(self.log, {
                    "t": t, "name": self.name, "action": "emergency_exploration_exit", 
                    "life_crisis": life_crisis, "reason": "life_crisis_override"
                })
                return True
            
            # 通常の復帰判定
            exploration_pressure = self.exploration_manager.calculate_exploration_pressure()
            return self.exploration_manager.consider_mode_reversion(t, exploration_pressure)
        else:
            # 命の危機時は探索モードへの突入を抑制
            if life_crisis > 1.0:
                return False
            
            # 通常の跳躍判定
            exploration_pressure = self.exploration_manager.calculate_exploration_pressure()
            return self.exploration_manager.consider_exploration_leap(t, exploration_pressure)
    
    def assess_predator_threat(self):
        """捕食者脅威の評価"""
        threat_level = 0.0
        nearby_predators = []
        
        for predator in self.env.predators:
            if predator.alive and self.distance_to(predator.pos()) <= 10:
                distance = self.distance_to(predator.pos())
                threat = (10 - distance) / 10 * predator.aggression
                threat_level += threat
                nearby_predators.append(predator)
        
        return threat_level, nearby_predators
    
    def seek_group_protection(self, t):
        """集団防御の追求"""
        threat_level, nearby_predators = self.assess_predator_threat()
        
        if threat_level > 0.3:
            # 近くの仲間を探す
            nearby_npcs = [npc for npc in self.roster.values() 
                          if npc != self and npc.alive and self.distance_to(npc.pos()) <= 15]
            
            if nearby_npcs:
                # 最も近い仲間のところに向かう
                closest_ally = min(nearby_npcs, key=lambda n: self.distance_to(n.pos()))
                self.move_towards(closest_ally.pos())
                
                log_event(self.log, {
                    "t": t, "name": self.name, "action": "group_protection", 
                    "threat_level": threat_level, "ally": closest_ally.name
                })
                return True
        
        return False
    
    def calculate_cave_safety_feeling(self, cave_pos):
        """洞窟への安全感計算"""
        # 1. 物理的安全感
        intrinsic_safety = 0.7  # 洞窟の基本安全性
        
        # 2. 体験に基づく安全感
        cave_name = next((k for k, v in self.env.caves.items() if v == cave_pos), None)
        safety_events = 0
        if cave_name:
            for log_entry in self.log:
                if (log_entry.get("location") == cave_pos and 
                    log_entry.get("action") in ["rest_in_cave", "safe_shelter"]):
                    safety_events += 1
        
        experiential_safety = min(1.0, safety_events / 3.0)
        
        # 3. 社会的安全感
        social_safety = self.calculate_social_safety_at_location(cave_pos)
        
        # 4. オキシトシン的縄張り効果
        oxytocin_effect = self.calculate_oxytocin_territory_effect(cave_pos)
        
        # 総合安全感
        total_safety_feeling = (intrinsic_safety * 0.15 + 
                               experiential_safety * 0.4 + 
                               social_safety * 0.25 + 
                               oxytocin_effect * 0.2)
        
        return min(1.0, total_safety_feeling)
    
    def calculate_social_safety_at_location(self, location):
        """特定場所での社会的安全感"""
        nearby_npcs = [npc for npc in self.roster.values() 
                      if npc != self and npc.alive and npc.distance_to(location) <= 5]
        
        if not nearby_npcs:
            return 0.0
        
        # 仲間の数による安心感
        group_safety = min(0.8, len(nearby_npcs) * 0.2)
        
        return group_safety * self.sociability
    
    def calculate_oxytocin_territory_effect(self, location):
        """オキシトシン的縄張り効果（場所＋人の統合的安全感）"""
        oxytocin_effect = 0.0
        
        # 1. 縄張りメンバーシップによる安心感
        if self.territory and self.territory.contains(location):
            oxytocin_effect += 0.3
        
        # 2. 仲間の結束による安心感
        territory_members = 0
        for npc in self.roster.values():
            if (npc != self and npc.alive and 
                hasattr(npc, 'territory') and npc.territory and 
                npc.territory.contains(location)):
                territory_members += 1
        
        bonding_effect = min(0.4, territory_members * 0.15)
        oxytocin_effect += bonding_effect
        
        # 3. 保護本能による安心感強化
        protection_instinct = self.empathy * 0.5
        oxytocin_effect += min(0.4, protection_instinct)
        
        # 4. 安心感の相互強化（基本的な縄張り一致による信頼感）
        collective_confidence = 0.0
        for npc in self.roster.values():
            if (npc != self and npc.alive and hasattr(npc, 'territory') and 
                npc.territory and npc.territory.center == location):
                collective_confidence += 0.1
        
        oxytocin_effect += min(0.3, collective_confidence)
        
        return min(1.0, oxytocin_effect)
    
    def claim_cave_territory(self, cave_pos, t):
        """洞窟縄張りの設定"""
        if self.territory is None:
            self.territory = Territory(cave_pos, radius=TERRITORY_RADIUS, owner=self.name)
            self.territory.established_tick = t
            
            # 近くの仲間を招待
            self.invite_nearby_to_territory(t)
            
            log_event(self.log, {
                "t": t, "name": self.name, "action": "establish_territory", 
                "location": cave_pos, "radius": TERRITORY_RADIUS
            })
    
    def invite_nearby_to_territory(self, t):
        """縄張りへの招待"""
        if not self.territory:
            return
            
        nearby_npcs = [npc for npc in self.roster.values() 
                      if npc != self and npc.alive and npc.territory is None and 
                      self.distance_to(npc.pos()) <= 12]
        
        for npc in nearby_npcs:
            if probability_check(0.7):  # 70%の確率で招待
                if probability_check(0.2):  # 20%の確率で受諾
                    npc.territory = self.territory
                    self.territory.add_member(npc.name)
                    
                    log_event(self.log, {
                        "t": t, "name": self.name, "action": "invite_to_territory", 
                        "invitee": npc.name, "accepted": True
                    })
    
    def emergency_survival_action(self, t, life_crisis):
        """命の危機時の緊急行動"""
        if self.thirst > THIRST_DANGER_THRESHOLD:
            known_water = {k: v for k, v in self.env.water_sources.items() if k in self.knowledge_water}
            if known_water:
                nearest_water = self.env.nearest_nodes(self.pos(), known_water, k=1)
                if nearest_water:
                    target = nearest_water[0]
                    if self.pos() == target:
                        self.thirst = max(0, self.thirst - 45)
                        log_event(self.log, {
                            "t": t, "name": self.name, "action": "emergency_drink", 
                            "recovery": 45, "life_crisis": life_crisis
                        })
                    else:
                        self.move_towards(target)
                    return True
        
        if self.hunger > HUNGER_DANGER_THRESHOLD:
            # 緊急食料探索
            known_food = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
            if known_food:
                nearest_berries = self.env.nearest_nodes(self.pos(), known_food, k=1)
                if nearest_berries:
                    target = nearest_berries[0]
                    if self.pos() == target:
                        self.hunger = max(0, self.hunger - 50)
                        log_event(self.log, {
                            "t": t, "name": self.name, "action": "emergency_eat", 
                            "recovery": 50, "life_crisis": life_crisis
                        })
                    else:
                        self.move_towards(target)
                    return True
        
        return False
    
    def step(self, t):
        """メインの行動ステップ"""
        if not self.alive:
            return
        
        # 基本的な劣化
        self.hunger += 1.5
        self.thirst += 2.0
        self.fatigue += 1.0
        
        # 生存チェック
        if self.thirst > 200 or self.hunger > 240:
            self.alive = False
            cause = "dehydration" if self.thirst > 200 else "starvation"
            log_event(self.log, {"t": t, "name": self.name, "action": "death", "cause": cause})
            return
        
        # SSD理論：意味圧による探索モードシフト
        self.consider_exploration_mode_shift(t)
        
        # 命の危機対応
        life_crisis = self.exploration_manager.calculate_life_crisis_pressure()
        if life_crisis > 1.0:
            if self.emergency_survival_action(t, life_crisis):
                return
        
        # 捕食者脅威への対応
        if self.seek_group_protection(t):
            return
        
        # 通常行動の優先順位付け
        if self.thirst > 80:
            self.seek_water(t)
        elif self.hunger > 100:
            self.seek_food(t)
        elif self.fatigue > 60:
            self.seek_rest(t)
        else:
            self.explore_or_socialize(t)
    
    def seek_water(self, t):
        """水分補給行動"""
        known_water = {k: v for k, v in self.env.water_sources.items() if k in self.knowledge_water}
        if known_water:
            nearest_water = self.env.nearest_nodes(self.pos(), known_water, k=1)
            if nearest_water:
                target = nearest_water[0]
                if self.pos() == target:
                    self.thirst = max(0, self.thirst - 35)
                    log_event(self.log, {"t": t, "name": self.name, "action": "drink", "recovery": 35})
                else:
                    self.move_towards(target)
        else:
            self.explore_for_resource(t, "water")
    
    def seek_food(self, t):
        """食料探索行動"""
        known_berries = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
        if known_berries:
            nearest_berries = self.env.nearest_nodes(self.pos(), known_berries, k=1)
            if nearest_berries:
                target = nearest_berries[0]
                if self.pos() == target:
                    success_rate = 0.8
                    if probability_check(success_rate):
                        self.hunger = max(0, self.hunger - 40)
                        log_event(self.log, {"t": t, "name": self.name, "action": "forage", "recovery": 40})
                else:
                    self.move_towards(target)
        else:
            self.explore_for_resource(t, "food")
    
    def seek_rest(self, t):
        """休息行動"""
        known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
        if known_caves:
            # 安全感に基づく洞窟選択
            cave_safety = {}
            for cave_name, cave_pos in known_caves.items():
                safety_feeling = self.calculate_cave_safety_feeling(cave_pos)
                cave_safety[cave_pos] = safety_feeling
            
            if cave_safety:
                best_cave = max(cave_safety.keys(), key=lambda pos: cave_safety[pos])
                safety_feeling = cave_safety[best_cave]
                
                if self.pos() == best_cave:
                    # 洞窟での休息
                    base_recovery = 25
                    safety_bonus = safety_feeling * 15
                    total_recovery = base_recovery + safety_bonus
                    
                    self.fatigue = max(0, self.fatigue - total_recovery)
                    
                    # 縄張り設定の検討
                    if safety_feeling >= self.territory_claim_threshold and not self.territory:
                        self.claim_cave_territory(best_cave, t)
                    
                    log_event(self.log, {
                        "t": t, "name": self.name, "action": "rest_in_cave", 
                        "recovery": total_recovery, "safety_feeling": safety_feeling
                    })
                else:
                    self.move_towards(best_cave)
        else:
            self.explore_for_resource(t, "shelter")
    
    def explore_for_resource(self, t, resource_type):
        """リソース探索"""
        # 探索移動
        explore_distance = 3 if self.exploration_mode else 2
        dx = random.randint(-explore_distance, explore_distance)
        dy = random.randint(-explore_distance, explore_distance)
        
        new_x = max(0, min(self.env.size-1, self.x + dx))
        new_y = max(0, min(self.env.size-1, self.y + dy))
        self.x, self.y = new_x, new_y
        
        # リソース発見判定
        discovery_chance = 0.3
        if self.exploration_mode:
            discovery_chance *= self.exploration_intensity
        
        if probability_check(discovery_chance):
            self.discover_nearby_resources(t, resource_type)
    
    def discover_nearby_resources(self, t, target_type):
        """近くのリソースを発見"""
        discovery_radius = 5
        discovered = False
        
        # 水源の発見
        if target_type in ["water", "any"]:
            for water_name, water_pos in self.env.water_sources.items():
                if (water_name not in self.knowledge_water and 
                    self.distance_to(water_pos) <= discovery_radius):
                    self.knowledge_water.add(water_name)
                    self.record_discovery_experience(t, "water", 0.8)
                    discovered = True
        
        # ベリーの発見
        if target_type in ["food", "any"]:
            for berry_name, berry_pos in self.env.berries.items():
                if (berry_name not in self.knowledge_berries and 
                    self.distance_to(berry_pos) <= discovery_radius):
                    self.knowledge_berries.add(berry_name)
                    self.record_discovery_experience(t, "berries", 0.7)
                    discovered = True
        
        # 洞窟の発見
        if target_type in ["shelter", "any"]:
            for cave_name, cave_pos in self.env.caves.items():
                if (cave_name not in self.knowledge_caves and 
                    self.distance_to(cave_pos) <= discovery_radius):
                    self.knowledge_caves.add(cave_name)
                    self.record_discovery_experience(t, "cave", 0.9)
                    discovered = True
        
        return discovered
    
    def record_discovery_experience(self, t, resource_type, meaning_pressure):
        """SSD理論：発見体験の記録"""
        resource_values = {
            "water": 0.9,
            "berries": 0.7, 
            "cave": 0.85,
            "hunting_ground": 0.8
        }
        
        value = resource_values.get(resource_type, 0.7)
        mode_multiplier = self.exploration_intensity if self.exploration_mode else 1.0
        pleasure = meaning_pressure * value * mode_multiplier
        
        # SSD理論パラメータの更新
        self.kappa["exploration"] = min(1.0, self.kappa.get("exploration", DEFAULT_KAPPA) + 0.15)
        self.E = min(5.0, self.E + pleasure * 0.5)  # 未処理圧の蓄積
        self.T = max(self.T0, self.T - 0.3)
        
        self.experience_points += pleasure * 0.3
        self.lifetime_discoveries += 1
        
        log_event(self.log, {
            "t": t, "name": self.name, "action": f"discovery_{resource_type}", 
            "pleasure": pleasure, "E": self.E
        })
    
    def explore_or_socialize(self, t):
        """探索または社会化行動"""
        if self.exploration_mode or probability_check(self.curiosity):
            self.explore_for_resource(t, "any")
        else:
            # 社会的行動
            nearby_npcs = [npc for npc in self.roster.values() 
                          if npc != self and npc.alive and self.distance_to(npc.pos()) <= 8]
            
            if nearby_npcs and probability_check(self.sociability):
                closest_npc = min(nearby_npcs, key=lambda n: self.distance_to(n.pos()))
                self.move_towards(closest_npc.pos())
                log_event(self.log, {
                    "t": t, "name": self.name, "action": "socialize", 
                    "target": closest_npc.name
                })