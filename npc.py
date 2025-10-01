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
        
        # 狩りシステム
        self.hunting_skill = preset.get("risk_tolerance", 0.5) * 0.7 + random.random() * 0.3
        self.hunting_experience = 0.0
        self.hunt_group = None  # 参加している狩りグループ
        self.meat_inventory = []  # 所有している肉リソース
        self.last_hunt_attempt = 0
        self.hunt_success_count = 0
        self.hunt_failure_count = 0
        
        # 重症システム関連属性
        self.critically_injured = False
        self.injury_recovery_time = 0
        self.injury_start_tick = 0
        self.caregiver = None           # 看護してくれる仲間
        self.care_target = None         # 看護している相手
        self.temporary_empathy_boost = 0.0  # 重症者目撃による一時的共感増加
        self.witnessed_injuries = set()      # 目撃した重症者のリスト（重複防止）
        
        # 信頼関係システム
        self.trust_levels = {}              # 他のNPCに対する信頼度 {npc_name: trust_value}
        self.trust_history = {}             # 信頼関係の履歴 {npc_name: [events...]}
        self.last_interaction = {}          # 最後の直接インタラクション {npc_name: tick}
        
        # SSD理論統合型経験システム（整合慣性κとして機能）
        self.experience = {
            'hunting': 0.1,                 # 狩り経験（初期値）
            'exploration': 0.1,             # 探索経験
            'survival': 0.1,                # 野宿・生存経験
            'care': 0.1,                    # 看護・治療経験
            'social': 0.1,                  # 社交・協力経験
            'predator_awareness': 0.1,      # 捕食者警戒経験
        }
        self.last_experience_update = 0     # 最後の経験値更新時刻
        
        # 捕食者警戒状態
        self.predator_alert_time = 0        # 警戒状態の残り時間
        self.known_predator_location = None # 既知の捕食者位置
        self.predator_encounters = 0        # 捕食者遭遇回数
        self.predator_escapes = 0           # 捕食者からの逃走成功回数
        
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
        
        # 重症回復チェック
        self.check_injury_recovery(t)
        
        # 記憶の鮮明さ減衰（信頼度は維持）
        self.decay_memory_over_time(t)
        
        # 経験値の減衰処理（使わないと錆びる）
        self.decay_unused_experience(t)
        
        # 肉の在庫管理（腐敗チェック）
        self.manage_meat_inventory(t)
        
        # 肉の分配検討
        self.consider_meat_sharing(t)
        
        # 重症者目撃による共感の変化
        self.witness_critical_injuries(t)
        
        # 重症者支援システム
        if self.seek_help_for_injured(t):
            return  # 支援活動を優先
        
        # 命の危機対応
        life_crisis = self.exploration_manager.calculate_life_crisis_pressure()
        if life_crisis > 1.0:
            if self.emergency_survival_action(t, life_crisis):
                return
        
        # 捕食者脅威への対応
        if self.seek_group_protection(t):
            return
        
        # 重症者は行動制限
        if self.critically_injured:
            # 重症者は基本的に待機（看護を受ける）
            if self.caregiver:
                log_event(self.log, {
                    "t": t, "name": self.name, "action": "being_cared",
                    "caregiver": self.caregiver.name
                })
            return
        
        # 看護中は看護を優先
        if self.care_target and self.care_target.critically_injured:
            self.provide_care(t)
            return
        
        # 通常行動の優先順位付け
        if self.thirst > 80:
            self.seek_water(t)
        elif self.hunger > 80:  # より低い閾値
            # 狩りも食料獲得手段として検討
            if self.consider_hunting(t):
                # 集団狩りを優先的に試行
                if not self.organize_group_hunt(t):
                    # 集団狩りが組織できない場合は単独狩り
                    if not self.attempt_solo_hunt(t):
                        # 狩りに失敗した場合は従来の食料探索
                        self.seek_food(t)
            else:
                self.seek_food(t)
        elif self.hunt_group and self.hunt_group.status == 'forming':
            # 狩りグループの実行
            self.execute_group_hunt(t)
        elif self.fatigue > 70:  # より高い閾値で休息優先度調整
            self.seek_rest(t)
        else:
            # 狩りの機会検討（低優先度）
            if self.consider_hunting(t) and self.hunger > 50:  # より低い閾値
                if not self.organize_group_hunt(t):
                    pass  # 通常行動に移行
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
                    
                    # SSD理論：野宿・生存経験の獲得
                    survival_quality = safety_feeling * (total_recovery / 40)  # 回復効率に基づく
                    self.gain_experience('survival', 
                                       EXPERIENCE_SYSTEM_SETTINGS['survival_exp_rate'] * survival_quality, t)
                    
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
        
        # SSD理論：探索経験の獲得
        exploration_intensity = self.exploration_intensity if self.exploration_mode else 0.5
        self.gain_experience('exploration', 
                           EXPERIENCE_SYSTEM_SETTINGS['exploration_exp_rate'] * exploration_intensity, t)
        
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
        self.kappa["exploration"] = min(1.0, self.kappa.get("exploration", 0.1) + 0.15)
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
    
    # === 狩りシステム ===
    
    def consider_hunting(self, t):
        """狩りの検討"""
        
        # 狩りクールダウンチェック
        hunt_cooldown = max(3, 8 - int(self.experience['hunting'] * 2))  # 経験で短縮
        if t - self.last_hunt_attempt < hunt_cooldown:
            return False
            
        # 狩りを行う条件
        hunting_desire = 0.0
        
        # 飢餓レベルによる狩り欲求
        if self.hunger > 60:  # より低い閾値
            hunting_desire += (self.hunger - 60) / 140
            
        # 性格による狩り傾向
        hunting_desire += self.risk_tolerance * 0.4
        
        # 肉の不足による欲求
        if not self.meat_inventory:
            hunting_desire += 0.5
            
        # 狩り経験による自信
        success_rate = self.calculate_hunting_confidence()
        hunting_desire += success_rate * 0.4
        

        
        return hunting_desire > 0.3  # 適正な狩り閾値
    
    def calculate_hunting_confidence(self):
        """狩りの自信レベルを計算（経験値統合）"""
        base_confidence = self.hunting_skill
        
        # SSD理論：経験による効率向上
        experience_boost = self.get_experience_efficiency('hunting') - 1.0
        base_confidence += experience_boost * 0.4
        
        # 従来の成功率による修正
        total_attempts = self.hunt_success_count + self.hunt_failure_count
        if total_attempts > 0:
            success_ratio = self.hunt_success_count / total_attempts
            base_confidence += (success_ratio - 0.5) * 0.3
            
        return max(0.1, min(0.9, base_confidence))
    
    def attempt_solo_hunt(self, t):
        """単独狩りの試行"""
        from config import HUNTING_SETTINGS, PREY_TYPES
        from social import MeatResource
        
        self.last_hunt_attempt = t
        
        # 疲労コスト
        hunt_cost = HUNTING_SETTINGS['hunt_fatigue_cost']
        self.fatigue += hunt_cost
        
        # 成功判定
        confidence = self.calculate_hunting_confidence()
        base_rate = HUNTING_SETTINGS['solo_success_rate']
        success_rate = base_rate + confidence * 0.2
        
        hunt_successful = probability_check(success_rate)
        
        if hunt_successful:
            # 狩り成功
            prey_type = 'small_game'  # 単独では小動物のみ
            meat_amount = PREY_TYPES[prey_type]['meat_amount']
            
            # 肉リソース獲得
            meat = MeatResource(meat_amount, owner=self.name)
            meat.creation_tick = t
            self.meat_inventory.append(meat)
            
            # 経験値更新
            self.hunt_success_count += 1
            self.hunting_experience += 0.2
            
            # SSD理論：狩り経験の獲得
            self.gain_experience('hunting', EXPERIENCE_SYSTEM_SETTINGS['hunting_exp_rate'], t)
            
            # SSD理論：成功による快感（跳躍的報酬）
            success_pleasure = meat_amount * 0.5 + confidence * 0.3
            self.E = max(0.0, self.E - success_pleasure * 0.4)  # 未処理圧の軽減
        else:
            # 狩り失敗
            self.hunt_failure_count += 1
            
            # SSD理論：失敗による未処理圧の蓄積
            failure_pressure = confidence * 0.3 + 0.2
            self.E = min(5.0, self.E + failure_pressure)
        
        # 成功・失敗に関わらず怪我リスクあり（成功時は確率減少）
        injury_rate = HUNTING_SETTINGS['danger_rate']
        if hunt_successful:
            injury_rate *= 0.6  # 成功時は怪我確率40%減
        
        injured = False
        critical_injury = False
        if probability_check(injury_rate):
            injury_damage = random.randint(5, 15) if not hunt_successful else random.randint(3, 12)
            self.fatigue += injury_damage
            injured = True
            
            # 重症判定
            if probability_check(HUNTING_SETTINGS['critical_injury_rate']):
                self.become_critically_injured(t)
                critical_injury = True
            
            log_event(self.log, {
                "t": t, "name": self.name, "action": "hunt_injury",
                "damage": injury_damage, "hunt_success": hunt_successful,
                "critical_injury": critical_injury
            })
        
        # 結果ログ
        if hunt_successful:
            log_event(self.log, {
                "t": t, "name": self.name, "action": "solo_hunt_success",
                "prey_type": prey_type, "meat_amount": meat_amount,
                "pleasure": success_pleasure, "injured": injured
            })
        else:
            log_event(self.log, {
                "t": t, "name": self.name, "action": "solo_hunt_failure",
                "pressure_increase": failure_pressure, "injured": injured
            })
        
        return hunt_successful
    
    def organize_group_hunt(self, t):
        """集団狩りの組織化"""
        from social import HuntGroup
        from config import HUNTING_SETTINGS
        
        # 既にグループに参加している場合はスキップ
        if self.hunt_group:
            return False
            
        # 近くの仲間を探す
        potential_members = [
            npc for npc in self.roster.values()
            if npc != self and npc.alive and npc.hunt_group is None
            and self.distance_to(npc.pos()) <= 15
            and npc.fatigue < 60  # 疲労していない
        ]
        
        if len(potential_members) >= 2:  # 最低3人（自分含む）で組織
            # 狩りグループ作成
            hunt_group = HuntGroup(leader=self, target_prey_type='medium_game')
            hunt_group.formation_tick = t
            
            # メンバー募集
            recruited = 0
            for npc in potential_members[:4]:  # 最大5人まで
                # 参加意欲の計算（信頼関係考慮）
                trust_level = npc.get_trust_level(self.name)
                trust_bonus = trust_level * 0.3  # 信頼できるリーダーなら参加しやすい
                
                join_probability = (npc.risk_tolerance * 0.4 + 
                                  npc.sociability * 0.3 + 
                                  (npc.hunger / 200) * 0.2 + 
                                  trust_bonus)
                
                if probability_check(join_probability):
                    hunt_group.add_member(npc)
                    npc.hunt_group = hunt_group
                    recruited += 1
            
            if hunt_group.can_start_hunt():
                self.hunt_group = hunt_group
                
                log_event(self.log, {
                    "t": t, "name": self.name, "action": "organize_hunt_group",
                    "members": [m.name for m in hunt_group.members],
                    "target_prey": hunt_group.target_prey_type
                })
                
                return True
        
        return False
    
    def execute_group_hunt(self, t):
        """集団狩りの実行"""
        from config import HUNTING_SETTINGS, PREY_TYPES
        from social import MeatResource
        
        if not self.hunt_group or self.hunt_group.status != 'forming':
            return False
        
        hunt_group = self.hunt_group
        hunt_group.status = 'hunting'
        
        # 全メンバーの疲労コスト
        hunt_cost = HUNTING_SETTINGS['hunt_fatigue_cost']
        for member in hunt_group.members:
            member.fatigue += hunt_cost
            member.last_hunt_attempt = t
        
        # 成功判定
        success_rate = hunt_group.get_success_rate()
        
        hunt_successful = probability_check(success_rate)
        
        if hunt_successful:
            # 狩り成功
            prey_type = hunt_group.target_prey_type
            meat_amount = PREY_TYPES[prey_type]['meat_amount']
            
            # 肉リソース作成（グループ共有）
            meat = MeatResource(meat_amount, owner=self.name, hunt_group=hunt_group)
            meat.creation_tick = t
            
            # リーダーが肉を管理
            self.meat_inventory.append(meat)
            hunt_group.success = True
            hunt_group.meat_acquired = meat_amount
            
            # 全メンバーの経験値更新
            for member in hunt_group.members:
                member.hunt_success_count += 1
                member.hunting_experience += 0.3
                
                # SSD理論：集団狩りでの経験獲得（協力学習）
                base_exp = EXPERIENCE_SYSTEM_SETTINGS['hunting_exp_rate'] * 1.2  # 集団ボーナス
                member.gain_experience('hunting', base_exp, t)
                member.gain_experience('social', EXPERIENCE_SYSTEM_SETTINGS['social_exp_rate'], t)
                
                # SSD理論：集団成功による快感と社会的結束
                success_pleasure = (meat_amount / len(hunt_group.members)) * 0.6
                social_bonding = len(hunt_group.members) * 0.1
                total_pleasure = success_pleasure + social_bonding
                
                member.E = max(0.0, member.E - total_pleasure * 0.5)
                member.kappa['group_hunting'] = min(1.0, 
                    member.kappa.get('group_hunting', 0.1) + 0.25)
                
                # 信頼度更新：共に危険を乗り越えた結束
                for other_member in hunt_group.members:
                    if other_member != member:
                        # 成功した狩りでの信頼関係
                        emotional_context = {
                            'shared_danger': True,
                            'life_threatening': False  # 成功したので危険は過ぎた
                        }
                        member.update_trust(other_member.name, 
                                          'hunt_together_success', t, emotional_context)
        else:
            # 狩り失敗
            for member in hunt_group.members:
                member.hunt_failure_count += 1
            
            # SSD理論：集団失敗による未処理圧
            for member in hunt_group.members:
                failure_pressure = 0.4 / len(hunt_group.members)  # 集団では圧力分散
                member.E = min(5.0, member.E + failure_pressure)
        
        # 成功・失敗に関わらず全メンバーに怪我リスク
        injured_members = []
        for member in hunt_group.members:
            # 集団では危険分散、成功時はさらに減少
            base_danger_rate = HUNTING_SETTINGS['danger_rate'] / len(hunt_group.members)
            if hunt_successful:
                injury_rate = base_danger_rate * 0.5  # 成功時は怪我確率50%減
            else:
                injury_rate = base_danger_rate
            
            if probability_check(injury_rate):
                injury_damage = random.randint(2, 8) if hunt_successful else random.randint(3, 10)
                member.fatigue += injury_damage
                critical_injury = False
                
                # 重症判定（集団では確率低下）
                critical_rate = HUNTING_SETTINGS['critical_injury_rate'] * 0.5
                if probability_check(critical_rate):
                    member.become_critically_injured(t)
                    critical_injury = True
                
                injured_members.append({
                    "name": member.name, 
                    "damage": injury_damage, 
                    "critical": critical_injury
                })
                
                log_event(member.log, {
                    "t": t, "name": member.name, "action": "hunt_injury",
                    "damage": injury_damage, "hunt_success": hunt_successful, 
                    "group_hunt": True, "critical_injury": critical_injury
                })
        
        # 結果ログ
        if hunt_successful:
            log_event(self.log, {
                "t": t, "name": self.name, "action": "group_hunt_success",
                "members": [m.name for m in hunt_group.members],
                "prey_type": prey_type, "meat_amount": meat_amount,
                "injured_members": injured_members
            })
        else:
            log_event(self.log, {
                "t": t, "name": self.name, "action": "group_hunt_failure",
                "members": [m.name for m in hunt_group.members],
                "injured_members": injured_members
            })
        
        # 狩りグループ解散
        for member in hunt_group.members:
            member.hunt_group = None
        hunt_group.status = 'disbanded'
        
        return success_rate > 0.5  # 成功したかどうかを返す
    
    def manage_meat_inventory(self, t):
        """肉の在庫管理（腐敗処理）"""
        if not self.meat_inventory:
            return
        
        # 腐敗処理
        spoiled_meat = []
        for meat in self.meat_inventory:
            if meat.decay():
                spoiled_meat.append(meat)
        
        # 腐った肉を削除
        for meat in spoiled_meat:
            self.meat_inventory.remove(meat)
            log_event(self.log, {
                "t": t, "name": self.name, "action": "meat_spoiled",
                "amount": meat.amount
            })
    
    def consider_meat_sharing(self, t):
        """肉の分配検討"""
        if not self.meat_inventory:
            return
        
        for meat in self.meat_inventory:
            sharing_pressure = meat.get_sharing_pressure()
            
            # 分配圧力が高い場合
            if sharing_pressure > 0.7:
                # 近くの仲間に分配
                nearby_npcs = [
                    npc for npc in self.roster.values()
                    if npc != self and npc.alive and npc.hunger > 60
                    and self.distance_to(npc.pos()) <= 10
                ]
                
                if nearby_npcs:
                    # 最も飢えている仲間に分配
                    hungriest = max(nearby_npcs, key=lambda n: n.hunger)
                    share_amount = min(meat.amount * 0.3, meat.amount)
                    
                    if share_amount > 0:
                        shared = meat.share_with(hungriest.name, share_amount)
                        hungriest.receive_meat_gift(shared, self, t)
                        
                        # SSD理論：分配による社会的報酬（一時的共感ブースト込み）
                        effective_empathy = self.get_effective_empathy()
                        social_reward = shared * effective_empathy * 0.4
                        self.E = max(0.0, self.E - social_reward)
                        
                        log_event(self.log, {
                            "t": t, "name": self.name, "action": "share_meat",
                            "recipient": hungriest.name, "amount": shared,
                            "social_reward": social_reward
                        })
    
    def receive_meat_gift(self, amount, giver, t):
        """肉の贈り物を受け取る"""
        # 直接栄養として摂取
        nutrition = amount * 0.8  # 肉の栄養価
        self.hunger = max(0, self.hunger - nutrition)
        
        # 社会的絆の強化
        if hasattr(self, 'social_bonds'):
            if not hasattr(self, 'social_bonds'):
                self.social_bonds = {}
            self.social_bonds[giver.name] = self.social_bonds.get(giver.name, 0.0) + 0.3
        
        # 信頼度更新：飢饿程度によって情動的熟量が変化
        if self.hunger > 150:
            event_type = 'food_in_hunger' if self.hunger > 180 else 'meat_share_starving'
            emotional_context = {'desperate_situation': self.hunger > 200}
        else:
            event_type = 'casual_food_share'
            emotional_context = {'desperate_situation': False}
            
        self.update_trust(giver.name, event_type, t, emotional_context)
        
        log_event(self.log, {
            "t": t, "name": self.name, "action": "receive_meat_gift",
            "giver": giver.name, "amount": amount, "nutrition": nutrition
        })
    
    # === 重症システム ===
    
    def become_critically_injured(self, t):
        """重症状態になる"""
        self.critically_injured = True
        self.injury_start_tick = t
        self.injury_recovery_time = random.randint(
            CRITICAL_INJURY_SETTINGS['duration_min'],
            CRITICAL_INJURY_SETTINGS['duration_max']
        )
        
        log_event(self.log, {
            "t": t, "name": self.name, "action": "critical_injury",
            "recovery_time": self.injury_recovery_time
        })
    
    def check_injury_recovery(self, t):
        """重症の回復チェック"""
        if not self.critically_injured:
            return
        
        elapsed_time = t - self.injury_start_tick
        recovery_progress = elapsed_time / self.injury_recovery_time
        
        # 看護による回復加速
        if self.caregiver:
            recovery_progress *= (1 + CRITICAL_INJURY_SETTINGS['care_effectiveness'])
        
        if recovery_progress >= 1.0:
            self.critically_injured = False
            self.caregiver = None
            
            # 回復時に看護してくれた人への特別な信頼
            if self.caregiver:
                emotional_context = {
                    'life_threatening': True,
                    'desperate_situation': True
                }
                self.update_trust(self.caregiver.name, 
                                'life_saved_critical', t, emotional_context)
            
            log_event(self.log, {
                "t": t, "name": self.name, "action": "injury_recovery",
                "duration": elapsed_time, "caregiver": self.caregiver.name if self.caregiver else None
            })
    
    def seek_help_for_injured(self, t):
        """重症者への支援を探す・提供する"""
        if self.critically_injured:
            # 重症者：助けを求める
            if not self.caregiver:
                nearby_npcs = [
                    npc for npc in self.roster.values()
                    if npc != self and npc.alive and not npc.critically_injured
                    and self.distance_to(npc.pos()) <= 8
                    and npc.care_target is None
                ]
                
                if nearby_npcs:
                    # 最も共感的な仲間を選ぶ
                    potential_caregiver = max(nearby_npcs, key=lambda n: n.empathy)
                    
                    # 看護意欲の判定（一時的共感ブースト、信頼関係込み）
                    effective_empathy = potential_caregiver.get_effective_empathy()
                    trust_level = potential_caregiver.get_trust_level(self.name)
                    care_willingness = effective_empathy * 0.6 + trust_level * 0.4 + 0.1
                    if probability_check(care_willingness):
                        self.caregiver = potential_caregiver
                        potential_caregiver.care_target = self
                        
                        # 信頼度更新：重症時の看護は高い情動的熟量
                        emotional_context = {
                            'life_threatening': True,
                            'desperate_situation': self.critically_injured
                        }
                        self.update_trust(potential_caregiver.name, 
                                        'care_during_injury', t, emotional_context)
                        
                        log_event(self.log, {
                            "t": t, "name": self.name, "action": "receive_care",
                            "caregiver": potential_caregiver.name
                        })
                        
                        return True
        else:
            # 健康者：重症者を探して支援
            if not self.care_target:
                nearby_injured = [
                    npc for npc in self.roster.values()
                    if npc != self and npc.alive and npc.critically_injured
                    and self.distance_to(npc.pos()) <= 10
                    and npc.caregiver is None
                ]
                
                if nearby_injured:
                    injured_npc = nearby_injured[0]  # 最初の重症者を支援
                    effective_empathy = self.get_effective_empathy()
                    care_willingness = effective_empathy * 0.9 + 0.1
                    
                    if probability_check(care_willingness):
                        self.care_target = injured_npc
                        injured_npc.caregiver = self
                        
                        log_event(self.log, {
                            "t": t, "name": self.name, "action": "start_caring",
                            "patient": injured_npc.name
                        })
                        
                        return True
        return False
    
    def provide_care(self, t):
        """看護行動"""
        if not self.care_target or not self.care_target.critically_injured:
            self.care_target = None
            return
        
        patient = self.care_target
        
        # 患者の近くに移動
        if self.distance_to(patient.pos()) > 1:
            self.move_towards(patient.pos())
            return
        
        # 食料分配
        if self.hunger < 80 and patient.hunger > 100:
            food_to_share = min(30, self.hunger * CRITICAL_INJURY_SETTINGS['food_sharing_rate'])
            if food_to_share > 0:
                self.hunger += food_to_share * 0.3  # 看護者も少し消費
                patient.hunger = max(0, patient.hunger - food_to_share)
                
                log_event(self.log, {
                    "t": t, "name": self.name, "action": "care_feed",
                    "patient": patient.name, "amount": food_to_share
                })
        
        # 肉の分配
        if self.meat_inventory and patient.hunger > 80:
            meat = self.meat_inventory[0]
            share_amount = min(meat.amount * 0.4, meat.amount)
            if share_amount > 0:
                shared = meat.share_with(patient.name, share_amount)
                patient.receive_meat_gift(shared, self, t)
                
                log_event(self.log, {
                    "t": t, "name": self.name, "action": "care_meat_share",
                    "patient": patient.name, "amount": shared
                })
        
        # 洞窟への搬送
        if hasattr(self, 'knowledge_caves') and self.knowledge_caves:
            known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
            if known_caves and patient.pos() not in known_caves.values():
                # 最寄りの安全な洞窟を探す
                nearest_cave = min(known_caves.values(), 
                                 key=lambda cave: self.distance_to(cave))
                
                # 患者を洞窟に連れて行く
                if patient.pos() != nearest_cave:
                    # 患者を洞窟方向に移動させる
                    dx = 1 if nearest_cave[0] > patient.x else -1 if nearest_cave[0] < patient.x else 0
                    dy = 1 if nearest_cave[1] > patient.y else -1 if nearest_cave[1] < patient.y else 0
                    
                    if dx != 0 or dy != 0:
                        patient.x = max(0, min(self.env.size-1, patient.x + dx))
                        patient.y = max(0, min(self.env.size-1, patient.y + dy))
                        
                        log_event(self.log, {
                            "t": t, "name": self.name, "action": "transport_patient",
                            "patient": patient.name, "destination": nearest_cave
                        })
        
        # SSD理論：看護による社会的結束（一時的共感ブースト込み）
        effective_empathy = self.get_effective_empathy()
        social_bonding = effective_empathy * 0.25
        self.E = max(0.0, self.E - social_bonding)
        
        # 看護疲労
        self.fatigue += 2
        
        # SSD理論：看護経験の獲得
        self.gain_experience('care', EXPERIENCE_SYSTEM_SETTINGS['care_exp_rate'], t)
    
    # === 信頼関係システム ===
    
    def update_trust(self, other_npc_name, event_type, t, emotional_context=None):
        """情動的熟量を考慮した信頼度更新"""
        if other_npc_name == self.name:
            return  # 自分自身とは信頼関係なし
        
        # 情動的状態を評価（「熟」の大きさ）
        emotional_heat = self.calculate_emotional_heat(t, emotional_context)
        
        # イベントに基づく信頼度確定
        if event_type in TRUST_EVENTS:
            event_data = TRUST_EVENTS[event_type]
            base_trust = event_data['base_trust']
            event_heat = event_data['emotional_heat']
            
            # 情動的熟量が高いほど、信頼度の確定が強くなる
            heat_multiplier = 0.5 + (emotional_heat * event_heat * 0.5)
            final_trust = base_trust * heat_multiplier
            
            # 現在の信頼度との重み付き平均（新しい経験が強い影響）
            current_trust = self.trust_levels.get(other_npc_name, TRUST_SYSTEM_SETTINGS['neutral_trust'])
            weight_new = 0.7 + (emotional_heat * 0.3)  # 熟が高いほど新しい経験を重視
            
            new_trust = (final_trust * weight_new) + (current_trust * (1 - weight_new))
        else:
            # 未定義イベントは小さな変化
            current_trust = self.trust_levels.get(other_npc_name, TRUST_SYSTEM_SETTINGS['neutral_trust'])
            change = 0.05 * emotional_heat  # 小さな変化
            new_trust = current_trust + change
        
        # 信頼度の範囲制限
        new_trust = max(TRUST_SYSTEM_SETTINGS['min_trust_level'],
                       min(TRUST_SYSTEM_SETTINGS['max_trust_level'], new_trust))
        
        self.trust_levels[other_npc_name] = new_trust
        self.last_interaction[other_npc_name] = t
        
        # 履歴記録（情動的熟量も含む）
        if other_npc_name not in self.trust_history:
            self.trust_history[other_npc_name] = []
        
        self.trust_history[other_npc_name].append({
            'tick': t,
            'event': event_type,
            'emotional_heat': emotional_heat,
            'trust_level': new_trust,
            'memory_strength': 1.0  # 初期は鮮明
        })
        
        # 履歴の上限（最新15件まで保持）
        if len(self.trust_history[other_npc_name]) > 15:
            self.trust_history[other_npc_name] = self.trust_history[other_npc_name][-15:]
        
        log_event(self.log, {
            "t": t, "name": self.name, "action": "trust_established",
            "target": other_npc_name, "event_type": event_type,
            "emotional_heat": emotional_heat, "trust_level": new_trust
        })
    
    def calculate_emotional_heat(self, t, context=None):
        """情動的熟量（「熟」の大きさ）を計算"""
        heat = 0.3  # ベースライン
        
        # 生存危機による熟量
        if self.critically_injured:
            heat += 0.7  # 重症時は情動が高まる
        elif self.hunger > 150:
            heat += 0.4  # 飢饿時
        elif self.thirst > 150:
            heat += 0.4  # 渇き時
        elif self.fatigue > 80:
            heat += 0.2  # 疲労時
        
        # 最近の危険経験による熟量
        recent_injury = any(log.get('action') == 'hunt_injury' and t - log.get('t', 0) < 20 
                          for log in self.log[-10:] if isinstance(log, dict))
        if recent_injury:
            heat += 0.3
        
        # コンテキストによる調整
        if context:
            if context.get('life_threatening', False):
                heat += 0.5
            if context.get('desperate_situation', False):
                heat += 0.4
            if context.get('shared_danger', False):
                heat += 0.3
        
        return min(1.0, heat)  # 最大0～1.0
    
    def get_trust_level(self, other_npc_name):
        """記憶に基づいた総合的な信頼度を取得"""
        if other_npc_name == self.name:
            return 1.0  # 自分自身は完全に信頼
        
        # 直接的な信頼度がある場合
        if other_npc_name in self.trust_levels:
            return self.trust_levels[other_npc_name]
        
        # 記憶から信頼度を推定
        if other_npc_name in self.trust_history and self.trust_history[other_npc_name]:
            memories = self.trust_history[other_npc_name]
            
            # 記憶の重み付き平均（鮮明な記憶ほど強い影響）
            weighted_trust = 0
            total_weight = 0
            
            for memory in memories:
                weight = memory.get('memory_strength', 0.5) * memory.get('emotional_heat', 0.3)
                weighted_trust += memory.get('trust_level', 0.5) * weight
                total_weight += weight
            
            if total_weight > 0:
                return weighted_trust / total_weight
        
        return TRUST_SYSTEM_SETTINGS['neutral_trust']  # 未知は中立
    
    def get_trusted_npcs(self, threshold=None):
        """信頼できるNPCのリストを取得"""
        if threshold is None:
            threshold = TRUST_SYSTEM_SETTINGS['high_trust_threshold']
        
        return [npc_name for npc_name, trust in self.trust_levels.items()
                if trust >= threshold and npc_name in self.roster
                and self.roster[npc_name].alive]
    
    def decay_memory_over_time(self, t):
        """記憶の鮮明さの減衰（信頼度は維持）"""
        decay_rate = TRUST_SYSTEM_SETTINGS['memory_decay_rate']
        min_strength = TRUST_SYSTEM_SETTINGS['min_memory_strength']
        
        # 各人の記憶履歴の鮮明さを減衰
        for npc_name in self.trust_history:
            for memory in self.trust_history[npc_name]:
                # 記憶の鮮明さのみ減衰（情動的熟量が高いほど減衰しにくい）
                emotional_protection = memory.get('emotional_heat', 0.3)
                effective_decay = decay_rate + (emotional_protection * 0.003)  # 熟が高いほど減衰しにくい
                
                memory['memory_strength'] = max(min_strength, 
                                               memory.get('memory_strength', 1.0) * effective_decay)
        
        # 非常に古い記憶は削除（完全に忘れることはない）
        for npc_name in list(self.trust_history.keys()):
            self.trust_history[npc_name] = [
                memory for memory in self.trust_history[npc_name]
                if memory.get('memory_strength', 0) > 0.01 or 
                   t - memory.get('tick', 0) < 200  # 200ティック以内は保持
            ]
    
    def is_trusted_ally(self, other_npc_name):
        """指定したNPCが信頼できる仲間かどうか"""
        return self.get_trust_level(other_npc_name) >= TRUST_SYSTEM_SETTINGS['high_trust_threshold']
    
    # === SSD理論統合型経験システム ===
    
    def gain_experience(self, experience_type, base_amount, t):
        """SSD理論に基づく経験値獲得（整合慣性κとして機能）"""
        if experience_type not in self.experience:
            return
        
        # 現在の意味圧(E)を計算
        current_meaning_pressure = self.E
        
        # 経験値の上限は意味圧の95%まで（SSD理論の制約）
        max_experience = current_meaning_pressure * EXPERIENCE_SYSTEM_SETTINGS['kappa_growth_limit']
        current_exp = self.experience[experience_type]
        
        # 意味圧を超える経験知は獲得不可
        if current_exp >= max_experience:
            return  # これ以上の成長はない
        
        # 学習効率は現在の経験値と意味圧の差に依存
        learning_efficiency = (max_experience - current_exp) / max_experience
        learning_rate = EXPERIENCE_SYSTEM_SETTINGS['base_learning_rate'] * learning_efficiency
        
        # 経験値獲得
        exp_gain = base_amount * learning_rate
        new_experience = min(max_experience, current_exp + exp_gain)
        
        self.experience[experience_type] = new_experience
        self.last_experience_update = t
        
        # 整合慣性κの更新（経験がκ値として機能）
        kappa_key = f"exp_{experience_type}"
        self.kappa[kappa_key] = min(1.0, new_experience / 5.0)  # 正規化
        
        log_event(self.log, {
            "t": t, "name": self.name, "action": "experience_gain",
            "type": experience_type, "gain": exp_gain, "new_exp": new_experience,
            "meaning_pressure": current_meaning_pressure, "max_possible": max_experience
        })
    
    def get_experience_efficiency(self, experience_type):
        """経験に基づく行動効率の計算"""
        if experience_type not in self.experience:
            return 1.0
        
        exp_value = self.experience[experience_type]
        threshold = EXPERIENCE_SYSTEM_SETTINGS['experience_threshold']
        max_boost = EXPERIENCE_SYSTEM_SETTINGS['max_efficiency_boost']
        
        # 経験による効率向上（漸近的成長）
        if exp_value < threshold:
            efficiency = 1.0 + (exp_value / threshold) * (max_boost * 0.3)
        else:
            remaining = exp_value - threshold
            efficiency = 1.0 + max_boost * 0.3 + (remaining / (remaining + 2)) * (max_boost * 0.7)
        
        return min(1.0 + max_boost, efficiency)
    
    def decay_unused_experience(self, t):
        """使わない経験は微細に減衰（錆びる）"""
        if t - self.last_experience_update < 20:  # 最近更新されていれば減衰しない
            return
        
        decay_rate = EXPERIENCE_SYSTEM_SETTINGS['experience_decay']
        min_exp = EXPERIENCE_SYSTEM_SETTINGS['min_experience']
        
        for exp_type in self.experience:
            old_exp = self.experience[exp_type]
            self.experience[exp_type] = max(min_exp, old_exp * decay_rate)
        
        self.last_experience_update = t
    
    def witness_critical_injuries(self, t):
        """重症者の目撃による共感増加"""
        if self.critically_injured:
            return  # 自分が重症の場合はスキップ
        
        # 一時的共感ブーストの自然減衰
        self.temporary_empathy_boost *= CRITICAL_INJURY_SETTINGS['empathy_decay_rate']
        
        # 周囲の重症者をチェック
        witness_range = CRITICAL_INJURY_SETTINGS['witness_range']
        nearby_injured = [
            npc for npc in self.roster.values()
            if npc != self and npc.alive and npc.critically_injured
            and self.distance_to(npc.pos()) <= witness_range
            and npc.name not in self.witnessed_injuries
        ]
        
        for injured_npc in nearby_injured:
            # 新しい重症者を目撃
            self.witnessed_injuries.add(injured_npc.name)
            
            # 共感の増加
            empathy_increase = CRITICAL_INJURY_SETTINGS['witness_empathy_boost']
            
            # 距離による影響（近いほど強い衝撃）
            distance_factor = max(0.3, 1.0 - (self.distance_to(injured_npc.pos()) / witness_range))
            empathy_increase *= distance_factor
            
            # 既存の共感度による影響（共感的な人ほど強く反応）
            base_empathy_factor = 0.5 + (self.empathy * 0.5)
            empathy_increase *= base_empathy_factor
            
            # 一時的共感ブーストに追加（上限あり）
            max_boost = CRITICAL_INJURY_SETTINGS['max_empathy_boost']
            self.temporary_empathy_boost = min(max_boost, 
                                             self.temporary_empathy_boost + empathy_increase)
            
            log_event(self.log, {
                "t": t, "name": self.name, "action": "witness_critical_injury",
                "injured_npc": injured_npc.name, 
                "empathy_increase": empathy_increase,
                "total_boost": self.temporary_empathy_boost
            })
        
        # 回復した人を目撃リストから削除
        recovered_npcs = {
            npc.name for npc in self.roster.values()
            if npc.name in self.witnessed_injuries and not npc.critically_injured
        }
        self.witnessed_injuries -= recovered_npcs
    
    def get_effective_empathy(self):
        """一時的ブーストを含む実効共感度"""
        return min(1.0, self.empathy + self.temporary_empathy_boost)
    
    def get_predator_escape_chance(self):
        """捕食者からの逃走成功率を計算（経験考慮）"""
        from config import PREDATOR_AWARENESS_SETTINGS
        
        # 基本逃走率（体力状態に基づく）
        base_escape_rate = PREDATOR_AWARENESS_SETTINGS['base_escape_rate']
        
        # 疲労ペナルティ（0-100の範囲を0-1に正規化）
        fatigue_penalty = (self.fatigue / 100.0) * 0.3
        
        # 飢えや渇きによる体力低下を考慮
        hunger_penalty = max(0, (self.hunger - 100) / 200.0) * 0.2
        thirst_penalty = max(0, (self.thirst - 100) / 200.0) * 0.2
        
        adjusted_base = base_escape_rate - fatigue_penalty - hunger_penalty - thirst_penalty
        
        # 警戒経験によるボーナス
        awareness_exp = self.experience.get('predator_awareness', 0.0)
        experience_bonus = awareness_exp * PREDATOR_AWARENESS_SETTINGS['escape_bonus']
        
        # 最終逃走成功率
        final_escape_rate = min(PREDATOR_AWARENESS_SETTINGS['max_escape_rate'], 
                               max(0.05, adjusted_base + experience_bonus))
        
        return final_escape_rate
    
    def get_predator_detection_chance(self):
        """捕食者の早期発見確率を計算（経験考慮）"""
        from config import PREDATOR_AWARENESS_SETTINGS
        
        # 基本発見率
        base_detection = PREDATOR_AWARENESS_SETTINGS['base_detection_rate']
        
        # 警戒経験によるボーナス
        awareness_exp = self.experience.get('predator_awareness', 0.0)
        experience_bonus = awareness_exp * PREDATOR_AWARENESS_SETTINGS['detection_bonus']
        
        # 疲労による影響
        fatigue_penalty = self.fatigue * 0.2
        
        # 最終発見確率
        final_detection = min(PREDATOR_AWARENESS_SETTINGS['max_detection_rate'],
                             max(0.01, base_detection + experience_bonus - fatigue_penalty))
        
        return final_detection
    
    def get_predator_avoidance_chance(self):
        """捕食者との遭遇回避確率を計算（経験考慮）"""
        from config import PREDATOR_AWARENESS_SETTINGS
        
        # 基本回避率
        base_avoidance = PREDATOR_AWARENESS_SETTINGS['base_avoidance_rate']
        
        # 警戒経験によるボーナス
        awareness_exp = self.experience.get('predator_awareness', 0.0)
        experience_bonus = awareness_exp * PREDATOR_AWARENESS_SETTINGS['avoidance_bonus']
        
        # 最終回避確率
        final_avoidance = min(PREDATOR_AWARENESS_SETTINGS['max_avoidance_rate'],
                             base_avoidance + experience_bonus)
        
        return final_avoidance
    
    def alert_nearby_npcs_about_predator(self, all_npcs, predator_location):
        """近くのNPCに捕食者の存在を警告（経験による効果向上）"""
        from config import PREDATOR_AWARENESS_SETTINGS
        from utils import distance_between
        
        awareness_exp = self.experience.get('predator_awareness', 0.0)
        alert_effectiveness = 0.5 + (awareness_exp * PREDATOR_AWARENESS_SETTINGS['group_alert_bonus'])
        
        alerted_count = 0
        alert_range = (PREDATOR_AWARENESS_SETTINGS['alert_range_base'] + 
                      awareness_exp * PREDATOR_AWARENESS_SETTINGS['alert_range_bonus'])
        
        for other_npc in all_npcs:
            if other_npc != self and other_npc.health > 0:
                distance = distance_between((self.x, self.y), (other_npc.x, other_npc.y))
                
                if distance <= alert_range and random.random() < alert_effectiveness:
                    # 他のNPCに警戒状態を付与
                    other_npc.predator_alert_time = 20  # 20ティック間警戒
                    other_npc.known_predator_location = predator_location
                    alerted_count += 1
        
        if alerted_count > 0:
            self.add_ssd_observation('group_alert', alerted_count)
        
        return alerted_count
    
    def add_ssd_observation(self, observation_type, value):
        """SSD観察データの追加（簡易実装）"""
        # 将来のSSD理論拡張のためのプレースホルダー
        pass
    
    def attempt_predator_hunting(self, predators, all_npcs, current_tick):
        """捕食者狩りの試行（超ハイリスク）"""
        from config import PREDATOR_HUNTING
        
        if not predators:
            return None
        
        # 近くの捕食者を探す
        nearby_predators = []
        for predator in predators:
            if predator.alive:
                distance = distance_between(self.pos(), predator.pos())
                if distance <= PREDATOR_HUNTING['detection_range']:
                    nearby_predators.append((predator, distance))
        
        if not nearby_predators:
            return None
        
        # 最も近い捕食者を選択
        target_predator, distance = min(nearby_predators, key=lambda x: x[1])
        
        # 狩猟グループの形成
        hunting_group = [self]
        for npc in all_npcs:
            if (npc != self and npc.alive and 
                distance_between(self.pos(), npc.pos()) <= PREDATOR_HUNTING['group_formation_range'] and
                len(hunting_group) < PREDATOR_HUNTING['max_group_size']):
                # グループ参加意思決定
                participation_chance = (npc.risk_tolerance * 0.3 + 
                                      npc.experience.get('predator_awareness', 0) * 0.4 + 0.3)
                if random.random() < participation_chance:
                    hunting_group.append(npc)
        
        # 狩猟実行
        return self.execute_predator_hunt(target_predator, hunting_group, current_tick)
    
    def execute_predator_hunt(self, predator, hunting_group, current_tick):
        """捕食者狩りの実行"""
        from config import PREDATOR_HUNTING
        
        group_size = len(hunting_group)
        
        # 成功率計算
        base_success_rate = PREDATOR_HUNTING['success_rate_base']
        group_bonus = (group_size - 1) * PREDATOR_HUNTING['group_size_bonus']
        experience_bonus = sum(npc.experience.get('predator_awareness', 0) for npc in hunting_group) * PREDATOR_HUNTING['experience_bonus']
        
        total_success_rate = min(0.4, base_success_rate + group_bonus + experience_bonus)
        
        # 狩猟結果判定
        if random.random() < total_success_rate:
            return self.predator_hunt_success(predator, hunting_group, current_tick)
        else:
            return self.predator_hunt_failure(predator, hunting_group, current_tick)
    
    def predator_hunt_success(self, predator, hunting_group, current_tick):
        """捕食者狩り成功"""
        from config import PREDATOR_HUNTING
        
        # 捕食者を除去
        predator.alive = False
        
        results = {
            'success': True,
            'predator_killed': True,
            'group_size': len(hunting_group),
            'casualties': [],
            'injured': [],
            'meat_gained': PREDATOR_HUNTING['meat_reward']
        }
        
        # 各参加者への報酬と経験
        for npc in hunting_group:
            # 肉の分配
            npc.hunger = max(0, npc.hunger - PREDATOR_HUNTING['meat_reward'] / len(hunting_group))
            
            # 経験獲得
            npc.gain_experience('predator_awareness', 0.15, current_tick)
            npc.gain_experience('combat', 0.1, current_tick)
            
            # SSD学習: 成功体験
            npc.add_ssd_observation('predator_hunt_success', 1.0)
            
            # 成功時でも疲労
            npc.fatigue = min(100.0, npc.fatigue + 30.0)
        
        return results
    
    def predator_hunt_failure(self, predator, hunting_group, current_tick):
        """捕食者狩り失敗"""
        from config import PREDATOR_HUNTING
        
        results = {
            'success': False,
            'predator_killed': False,
            'group_size': len(hunting_group),
            'casualties': [],
            'injured': [],
            'meat_gained': 0
        }
        
        # 各参加者の被害判定
        for npc in hunting_group:
            injury_roll = random.random()
            
            if injury_roll < PREDATOR_HUNTING['death_rate_on_failure']:
                # 死亡
                npc.alive = False
                results['casualties'].append(npc.name)
            elif injury_roll < PREDATOR_HUNTING['injury_rate']:
                # 重傷
                npc.fatigue = min(100.0, npc.fatigue + 50.0)
                npc.hunger = min(200.0, npc.hunger + 30.0)  # 代謝亢進
                results['injured'].append(npc.name)
                
                # 重傷でも経験は得る
                npc.gain_experience('predator_awareness', 0.08, current_tick)
            
            # 失敗による疲労とストレス
            npc.fatigue = min(100.0, npc.fatigue + 40.0)
            
            # SSD学習: 失敗体験
            npc.add_ssd_observation('predator_hunt_failure', 1.0)
        
        return results