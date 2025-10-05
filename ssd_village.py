#!/usr/bin/env python3
"""
SSD Village Simulation - Clean Version
構造主観力学(SSD)理論に基づく原始村落シミュレーション
https://github.com/HermannDegner/Structural-Subjectivity-Dynamics

主要機能:
- SSD理論統合（未処理圧E、跳躍メカニズム、柔軟復帰条件）
- 捕食者システムによる生存圧力とコミュニティ形成
- 縄張りとオキシトシン効果による社会的結束
- 意味のあるコミュニティ形成システム
"""

import random
import math
from collections import defaultdict, deque
import pandas as pd

# SSD理論：性格プリセット
PIONEER = {"curiosity": 0.9, "sociability": 0.4, "risk_tolerance": 0.8, "empathy": 0.5}
ADVENTURER = {"curiosity": 0.8, "sociability": 0.6, "risk_tolerance": 0.9, "empathy": 0.4}
TRACKER = {"curiosity": 0.6, "sociability": 0.5, "risk_tolerance": 0.6, "empathy": 0.7}
SCHOLAR = {"curiosity": 0.95, "sociability": 0.3, "risk_tolerance": 0.4, "empathy": 0.8}
WARRIOR = {"curiosity": 0.4, "sociability": 0.6, "risk_tolerance": 0.9, "empathy": 0.5}
GUARDIAN = {"curiosity": 0.3, "sociability": 0.8, "risk_tolerance": 0.7, "empathy": 0.9}
HEALER = {"curiosity": 0.5, "sociability": 0.9, "risk_tolerance": 0.3, "empathy": 0.95}
DIPLOMAT = {"curiosity": 0.6, "sociability": 0.95, "risk_tolerance": 0.4, "empathy": 0.8}
FORAGER = {"curiosity": 0.7, "sociability": 0.7, "risk_tolerance": 0.5, "empathy": 0.6}
LEADER = {"curiosity": 0.5, "sociability": 0.9, "risk_tolerance": 0.7, "empathy": 0.7}
LONER = {"curiosity": 0.8, "sociability": 0.2, "risk_tolerance": 0.6, "empathy": 0.3}
NOMAD = {"curiosity": 0.85, "sociability": 0.4, "risk_tolerance": 0.8, "empathy": 0.4}

class Weather:
    def __init__(self):
        self.condition = "clear"  # clear, rain, storm
        self.temperature = 20.0
        
    def step(self):
        # シンプルな天気変化
        if random.random() < 0.1:
            self.condition = random.choice(["clear", "clear", "rain", "storm"])
        self.temperature = 15 + random.gauss(5, 3)

class DayNightCycle:
    def __init__(self):
        self.time_of_day = 12  # 0-23時間
        self.tick_counter = 0
        
    def step(self):
        self.tick_counter += 1
        self.time_of_day = (self.tick_counter // 2) % 24  # 2ティック = 1時間
        
    def is_night(self):
        return self.time_of_day < 6 or self.time_of_day >= 18
        
    def get_night_danger_multiplier(self):
        return 2.0 if self.is_night() else 1.0

class Predator:
    """捕食者システム：コミュニティ形成の外的圧力"""
    def __init__(self, pos, aggression=0.7):
        self.x, self.y = pos
        self.aggression = aggression
        self.hunt_radius = 8
        self.alive = True
        
    def pos(self):
        return (self.x, self.y)
        
    def distance_to(self, pos):
        return math.sqrt((self.x - pos[0])**2 + (self.y - pos[1])**2)
        
    def hunt_step(self, npcs):
        """NPCを狩る行動"""
        if not self.alive:
            return None
            
        nearby_npcs = [npc for npc in npcs if npc.alive and self.distance_to(npc.pos()) <= self.hunt_radius]
        if not nearby_npcs:
            return None
            
        target = min(nearby_npcs, key=lambda n: self.distance_to(n.pos()))
        nearby_defenders = len([npc for npc in nearby_npcs if self.distance_to(npc.pos()) <= 3])
        
        # 集団防御の効果
        attack_success_rate = self.aggression - (nearby_defenders * 0.3)
        attack_success_rate = max(0.1, min(0.9, attack_success_rate))
        
        if random.random() < attack_success_rate:
            target.alive = False
            return {"victim": target.name, "defenders": nearby_defenders}
        return None

class Territory:
    """縄張りシステム"""
    def __init__(self, center, radius=5, owner=None):
        self.center = center
        self.radius = radius
        self.owner = owner
        self.members = set()
        if owner:
            self.members.add(owner)
        self.established_tick = 0
        
    def contains(self, pos):
        x, y = pos
        cx, cy = self.center
        return math.sqrt((x-cx)**2 + (y-cy)**2) <= self.radius
        
    def add_member(self, npc_name):
        self.members.add(npc_name)
        
    def remove_member(self, npc_name):
        self.members.discard(npc_name)

class Environment:
    def __init__(self, size=90, n_berry=120, n_hunt=60, n_water=40, n_caves=25):
        self.size = size
        self.weather = Weather()
        self.day_night = DayNightCycle()
        self.predators = []
        
        # リソース生成
        self.water_sources = {f"water_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                             for i in range(n_water)}
        self.berries = {f"berry_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                       for i in range(n_berry)}
        self.hunting_grounds = {f"hunt_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                               for i in range(n_hunt)}
        self.caves = {f"cave_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                     for i in range(n_caves)}
        
    def step(self):
        self.weather.step()
        self.day_night.step()
        
        # 捕食者の行動
        for predator in self.predators:
            if predator.alive:
                # 移動（シンプルなランダムウォーク）
                predator.x += random.randint(-2, 2)
                predator.y += random.randint(-2, 2)
                predator.x = max(0, min(self.size-1, predator.x))
                predator.y = max(0, min(self.size-1, predator.y))
        
        # 捕食者の生成
        spawn_rate = 0.003  # 基本0.3%
        if self.day_night.is_night():
            spawn_rate *= 2.0  # 夜間は2倍
        if self.weather.condition == "rain":
            spawn_rate *= 1.3  # 雨天時は1.3倍
            
        if random.random() < spawn_rate:
            pos = (random.randint(5, self.size-5), random.randint(5, self.size-5))
            self.predators.append(Predator(pos))
    
    def nearest_nodes(self, pos, nodes_dict, k=3):
        if not nodes_dict:
            return []
        distances = [(node_pos, math.sqrt((pos[0]-node_pos[0])**2 + (pos[1]-node_pos[1])**2)) 
                    for node_pos in nodes_dict.values()]
        distances.sort(key=lambda x: x[1])
        return [pos for pos, _ in distances[:k]]

class NPC:
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
        self.kappa = defaultdict(lambda: 0.1)  # 整合慣性
        self.E = 0.0  # 未処理圧
        self.T = 1.0  # 温度パラメータ
        self.T0 = 1.0
        
        # 探索モード（SSD理論の跳躍メカニズム）
        self.exploration_mode = False
        self.exploration_mode_start_tick = 0
        self.exploration_intensity = 1.0
        
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
        return (self.x, self.y)
    
    def distance_to(self, pos):
        return math.sqrt((self.x - pos[0])**2 + (self.y - pos[1])**2)
    
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
    
    def calculate_life_crisis_pressure(self):
        """SSD理論：命の危機意味圧"""
        dehydration_crisis = max(0, (self.thirst - 140) / 60)
        starvation_crisis = max(0, (self.hunger - 160) / 80)
        fatigue_crisis = max(0, (self.fatigue - 80) / 40)
        
        return dehydration_crisis + starvation_crisis + fatigue_crisis
    
    def calculate_exploration_pressure(self):
        """SSD理論：探索意味圧の計算"""
        # 基本探索圧力
        boredom = min(1.0, (100 - len(self.knowledge_caves) * 10 - 
                           len(self.knowledge_water) * 15 - 
                           len(self.knowledge_berries) * 5) / 100)
        
        curiosity_drive = self.curiosity * 0.8
        risk_seeking = self.risk_tolerance * 0.6
        
        # 社会的要因
        isolation_pressure = (1.0 - self.sociability * 0.5) if not self.territory else 0.0
        
        total_pressure = boredom + curiosity_drive + risk_seeking + isolation_pressure
        return min(2.0, total_pressure)
    
    def consider_exploration_mode_shift(self, t):
        """SSD理論：意味圧に応じた探索モードの跳躍的変化と復帰判定"""
        life_crisis = self.calculate_life_crisis_pressure()
        
        if self.exploration_mode:
            # 命の危機時は即座に探索モードを終了
            if life_crisis > 1.5:
                self.exploration_mode = False
                self.log.append({"t": t, "name": self.name, "action": "emergency_exploration_exit", 
                               "life_crisis": life_crisis, "reason": "life_crisis_override"})
                return True
            
            # 通常の復帰判定
            exploration_pressure = self.calculate_exploration_pressure()
            return self.consider_mode_reversion(t, exploration_pressure)
        else:
            # 命の危機時は探索モードへの突入を抑制
            if life_crisis > 1.0:
                return False
            
            # 通常の跳躍判定
            exploration_pressure = self.calculate_exploration_pressure()
            return self.consider_exploration_leap(t, exploration_pressure)
    
    def consider_exploration_leap(self, t, exploration_pressure):
        """SSD理論：探索モードへの跳躍的移行判定（未処理圧統合版）"""
        # 基本意味圧閾値（好奇心による調整）
        base_threshold = 0.8 + (1.0 - self.curiosity) * 0.3
        
        # SSD理論：未処理圧(E)による跳躍閾値の動的調整
        leap_threshold = base_threshold - (self.E * 0.2)
        leap_threshold = max(0.3, leap_threshold)
        
        # 整合慣性と意味圧による跳躍判定
        exploration_experience = self.kappa.get("exploration", 0.1)
        leap_probability = min(0.9, (exploration_pressure + self.E * 0.3) / 2.0) * (0.5 + exploration_experience)
        
        if exploration_pressure > leap_threshold and random.random() < leap_probability:
            # 探索モードへの跳躍的変化
            self.exploration_mode = True
            self.exploration_mode_start_tick = t
            self.exploration_intensity = 1.0 + exploration_pressure * 0.5
            
            # SSD理論：跳躍によって未処理圧の一部が解消される
            self.E = max(0.0, self.E - (exploration_pressure * 0.3))
            
            self.log.append({"t": t, "name": self.name, "action": "exploration_mode_leap", 
                           "pressure": exploration_pressure, "E_before": self.E + (exploration_pressure * 0.3),
                           "E_after": self.E, "threshold": leap_threshold, "intensity": self.exploration_intensity})
            return True
        
        return False
    
    def consider_mode_reversion(self, t, exploration_pressure):
        """SSD理論：探索モードから通常モードへの柔軟な復帰判定"""
        resource_stability = self.evaluate_resource_stability()
        settlement_coherence = self.calculate_settlement_coherence(exploration_pressure, resource_stability)
        mode_duration = t - self.exploration_mode_start_tick
        
        # SSD理論：柔軟な復帰条件（重み付き総合判定）
        coherence_threshold = 0.7 - (self.curiosity * 0.2)
        
        # 復帰要因の重み付き評価
        coherence_factor = min(1.0, settlement_coherence / coherence_threshold)
        duration_factor = min(1.0, mode_duration / 15.0)
        pressure_factor = max(0.0, (0.6 - exploration_pressure) / 0.6)
        energy_factor = max(0.0, (3.0 - self.E) / 3.0)  # 未処理圧が低いほど復帰しやすい
        
        # 総合復帰スコア
        reversion_score = (coherence_factor * 0.4 + duration_factor * 0.2 + 
                          pressure_factor * 0.3 + energy_factor * 0.1)
        
        # 柔軟な復帰判定：スコア閾値 OR 強い単一要因
        if (reversion_score > 0.6 or
            (settlement_coherence >= coherence_threshold * 1.2) or
            (exploration_pressure < 0.2 and mode_duration > 8)):
            
            self.exploration_mode = False
            self.exploration_intensity = 1.0
            self.kappa["exploration"] = max(0.05, self.kappa.get("exploration", 0.1) * 0.9)
            
            self.log.append({"t": t, "name": self.name, "action": "exploration_mode_reversion", 
                           "duration": mode_duration, "reversion_score": reversion_score})
            return True
        
        return False
    
    def evaluate_resource_stability(self):
        """リソース安定性の評価"""
        water_stability = min(1.0, len(self.knowledge_water) / 3.0)
        food_stability = min(1.0, (len(self.knowledge_berries) + len(self.knowledge_hunting)) / 4.0)
        shelter_stability = min(1.0, len(self.knowledge_caves) / 2.0)
        
        return (water_stability + food_stability + shelter_stability) / 3.0
    
    def calculate_settlement_coherence(self, exploration_pressure, resource_stability):
        """定住整合慣性の計算"""
        # 基本的な定住要因
        resource_factor = resource_stability * 0.4
        pressure_factor = max(0.0, (1.0 - exploration_pressure)) * 0.3
        
        # 社会的要因
        social_factor = 0.0
        if self.territory and self.territory.members:
            social_factor = min(0.3, len(self.territory.members) * 0.1)
        
        return resource_factor + pressure_factor + social_factor
    
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
                
                self.log.append({"t": t, "name": self.name, "action": "group_protection", 
                               "threat_level": threat_level, "ally": closest_ally.name})
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
            self.territory = Territory(cave_pos, radius=8, owner=self.name)
            self.territory.established_tick = t
            
            # 近くの仲間を招待
            self.invite_nearby_to_territory(t)
            
            self.log.append({"t": t, "name": self.name, "action": "establish_territory", 
                           "location": cave_pos, "radius": 8})
    
    def invite_nearby_to_territory(self, t):
        """縄張りへの招待"""
        if not self.territory:
            return
            
        nearby_npcs = [npc for npc in self.roster.values() 
                      if npc != self and npc.alive and npc.territory is None and 
                      self.distance_to(npc.pos()) <= 12]
        
        for npc in nearby_npcs:
            if random.random() < 0.7:  # 70%の確率で招待
                if random.random() < 0.2:  # 20%の確率で受諾
                    npc.territory = self.territory
                    self.territory.add_member(npc.name)
                    
                    self.log.append({"t": t, "name": self.name, "action": "invite_to_territory", 
                                   "invitee": npc.name, "accepted": True})
    
    def emergency_survival_action(self, t, life_crisis):
        """命の危機時の緊急行動"""
        if self.thirst > 140:
            known_water = {k: v for k, v in self.env.water_sources.items() if k in self.knowledge_water}
            if known_water:
                nearest_water = self.env.nearest_nodes(self.pos(), known_water, k=1)
                if nearest_water:
                    target = nearest_water[0]
                    if self.pos() == target:
                        self.thirst = max(0, self.thirst - 45)
                        self.log.append({"t": t, "name": self.name, "action": "emergency_drink", 
                                       "recovery": 45, "life_crisis": life_crisis})
                    else:
                        self.move_towards(target)
                    return True
        
        if self.hunger > 160:
            # 緊急食料探索
            known_food = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
            if known_food:
                nearest_berries = self.env.nearest_nodes(self.pos(), known_food, k=1)
                if nearest_berries:
                    target = nearest_berries[0]
                    if self.pos() == target:
                        self.hunger = max(0, self.hunger - 50)
                        self.log.append({"t": t, "name": self.name, "action": "emergency_eat", 
                                       "recovery": 50, "life_crisis": life_crisis})
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
            self.log.append({"t": t, "name": self.name, "action": "death", "cause": cause})
            return
        
        # SSD理論：意味圧による探索モードシフト
        self.consider_exploration_mode_shift(t)
        
        # 命の危機対応
        life_crisis = self.calculate_life_crisis_pressure()
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
                    self.log.append({"t": t, "name": self.name, "action": "drink", "recovery": 35})
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
                    if random.random() < success_rate:
                        self.hunger = max(0, self.hunger - 40)
                        self.log.append({"t": t, "name": self.name, "action": "forage", "recovery": 40})
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
                    
                    self.log.append({"t": t, "name": self.name, "action": "rest_in_cave", 
                                   "recovery": total_recovery, "safety_feeling": safety_feeling})
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
        
        if random.random() < discovery_chance:
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
        self.kappa["exploration"] = min(1.0, self.kappa.get("exploration", 0.1) + 0.15)
        self.E = min(5.0, self.E + pleasure * 0.5)  # 未処理圧の蓄積
        self.T = max(self.T0, self.T - 0.3)
        
        self.experience_points += pleasure * 0.3
        self.lifetime_discoveries += 1
        
        self.log.append({"t": t, "name": self.name, "action": f"discovery_{resource_type}", 
                        "pleasure": pleasure, "E": self.E})
    
    def explore_or_socialize(self, t):
        """探索または社会化行動"""
        if self.exploration_mode or random.random() < self.curiosity:
            self.explore_for_resource(t, "any")
        else:
            # 社会的行動
            nearby_npcs = [npc for npc in self.roster.values() 
                          if npc != self and npc.alive and self.distance_to(npc.pos()) <= 8]
            
            if nearby_npcs and random.random() < self.sociability:
                closest_npc = min(nearby_npcs, key=lambda n: self.distance_to(n.pos()))
                self.move_towards(closest_npc.pos())
                self.log.append({"t": t, "name": self.name, "action": "socialize", 
                               "target": closest_npc.name})

def run_simulation(ticks=500):
    """シミュレーション実行"""
    seed = random.randint(1, 1000)
    random.seed(seed)
    print(f"Using random seed: {seed}")
    
    # 環境設定
    env = Environment(size=90, n_berry=120, n_hunt=60, n_water=40, n_caves=25)
    roster = {}
    
    # NPCの作成（16人）
    npc_configs = [
        ("Pioneer_Alpha", PIONEER, (20, 20)),
        ("Adventurer_Beta", ADVENTURER, (21, 19)), 
        ("Tracker_Gamma", TRACKER, (19, 21)),
        ("Scholar_Delta", SCHOLAR, (18, 18)),
        ("Warrior_Echo", WARRIOR, (60, 20)),
        ("Guardian_Foxtrot", GUARDIAN, (61, 19)),
        ("Loner_Golf", LONER, (59, 21)),
        ("Nomad_Hotel", NOMAD, (58, 18)),
        ("Healer_India", HEALER, (20, 60)),
        ("Diplomat_Juliet", DIPLOMAT, (21, 59)),
        ("Forager_Kilo", FORAGER, (19, 61)),
        ("Leader_Lima", LEADER, (18, 58)),
        ("Guardian_Mike", GUARDIAN, (60, 60)),
        ("Tracker_November", TRACKER, (61, 59)),
        ("Adventurer_Oscar", ADVENTURER, (59, 61)),
        ("Pioneer_Papa", PIONEER, (58, 58))
    ]
    
    for name, preset, start_pos in npc_configs:
        npc = NPC(name, preset, env, roster, start_pos)
        roster[name] = npc
    
    # シミュレーション実行
    logs = []
    weather_logs = []
    
    for t in range(1, ticks + 1):
        env.step()
        
        # 捕食者の攻撃処理
        for predator in env.predators:
            if predator.alive:
                attack_result = predator.hunt_step(list(roster.values()))
                if attack_result:
                    print(f"T{t}: Predator attack! {attack_result['victim']} killed (defenders: {attack_result['defenders']})")
        
        # NPC行動
        for npc in roster.values():
            npc.step(t)
            logs.extend(npc.log[-10:])  # 最新10個のログのみ保持
        
        # 天気ログ
        weather_logs.append({
            "t": t,
            "condition": env.weather.condition,
            "temperature": env.weather.temperature,
            "time_of_day": env.day_night.time_of_day,
            "predators": len([p for p in env.predators if p.alive])
        })
        
        # 進捗表示
        if t % 100 == 0:
            survivors = sum(1 for npc in roster.values() if npc.alive)
            exploration_mode_count = sum(1 for npc in roster.values() if npc.alive and npc.exploration_mode)
            territories = len(set(id(npc.territory) for npc in roster.values() 
                                if npc.alive and npc.territory is not None))
            
            print(f"T{t}: Survivors={survivors}/16, Exploring={exploration_mode_count}, "
                  f"Territories={territories}, Predators={len([p for p in env.predators if p.alive])}")
    
    return list(roster.values()), pd.DataFrame(logs), pd.DataFrame(weather_logs)

if __name__ == "__main__":
    final_npcs, df_logs, df_weather = run_simulation(ticks=500)
    
    # 結果分析
    survivors = [npc for npc in final_npcs if npc.alive]
    print(f"\n=== SSD Village Simulation Results ===")
    print(f"Survivors: {len(survivors)}/16")
    
    # SSD理論関連分析
    if not df_logs.empty:
        mode_changes = df_logs[df_logs['action'].isin(['exploration_mode_leap', 'exploration_mode_reversion'])]
        print(f"SSD Mode Changes:")
        print(f"  - Exploration leaps: {len(mode_changes[mode_changes['action'] == 'exploration_mode_leap'])}")
        print(f"  - Mode reversions: {len(mode_changes[mode_changes['action'] == 'exploration_mode_reversion'])}")
        
        # コミュニティ形成分析
        territories = {}
        for npc in survivors:
            if npc.territory is not None:
                territory_id = id(npc.territory)
                if territory_id not in territories:
                    territories[territory_id] = []
                territories[territory_id].append(npc.name)
        
        if territories:
            print(f"\nCommunity Formation:")
            for i, (territory_id, members) in enumerate(territories.items()):
                print(f"  - Community {i+1}: {len(members)} members ({', '.join(members)})")
            
            max_community_size = max(len(members) for members in territories.values())
            avg_community_size = sum(len(members) for members in territories.values()) / len(territories)
            print(f"  - Maximum community size: {max_community_size}")
            print(f"  - Average community size: {avg_community_size:.1f}")
        
        # 捕食者分析
        predator_events = df_logs[df_logs['action'].isin(['group_protection'])]
        print(f"\nPredator Defense:")
        print(f"  - Group protection events: {len(predator_events)}")
    
    print(f"\n=== Simulation Complete ===")