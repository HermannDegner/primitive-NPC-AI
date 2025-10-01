"""
SSD Village Simulation - Environment System
構造主観力学(SSD)理論に基づく原始村落シミュレーション - 環境システム
"""

import random
import math


class Weather:
    """天候システム"""
    def __init__(self):
        self.condition = "clear"  # clear, rain, storm
        self.temperature = 20.0
        
    def step(self):
        """天気変化の1ステップ"""
        # シンプルな天気変化
        if random.random() < 0.1:
            self.condition = random.choice(["clear", "clear", "rain", "storm"])
        self.temperature = 15 + random.gauss(5, 3)


class DayNightCycle:
    """日夜サイクルシステム"""
    def __init__(self):
        self.time_of_day = 12  # 0-23時間
        self.tick_counter = 0
        
    def step(self):
        """時間経過の1ステップ"""
        self.tick_counter += 1
        self.time_of_day = (self.tick_counter // 2) % 24  # 2ティック = 1時間
        
    def is_night(self):
        """夜間かどうかを判定"""
        return self.time_of_day < 6 or self.time_of_day >= 18
        
    def get_night_danger_multiplier(self):
        """夜間の危険度倍率"""
        return 2.0 if self.is_night() else 1.0


class Prey:
    """獲物動物クラス"""
    def __init__(self, x, y, animal_type='deer'):
        self.x = x
        self.y = y
        self.type = animal_type
        self.alive = True
        self.fear_level = 0.0
        self.last_seen_predator = 0
        self.last_seen_human = 0
        
        # 動物タイプ別設定
        from config import PREY_ANIMALS
        self.config = PREY_ANIMALS[animal_type]
        self.meat_value = self.config['meat_value']
        self.hunting_difficulty = self.config['difficulty']
    
    def update_fear(self, predators, humans):
        """恐怖レベルの更新（捕食者・人間の近接で増加）"""
        self.fear_level *= 0.95  # 自然減衰
        
        # 捕食者・人間との距離で恐怖増加
        for predator in predators:
            distance = self.distance_to(predator)
            if distance < 20:
                self.fear_level = min(1.0, self.fear_level + 0.3)
                self.last_seen_predator = 0
        
        for human in humans:
            distance = self.distance_to(human)
            if distance < 15:
                self.fear_level = min(1.0, self.fear_level + 0.2)
                self.last_seen_human = 0
    
    def distance_to(self, other):
        if hasattr(other, 'x') and hasattr(other, 'y'):
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        elif hasattr(other, 'pos'):
            pos = other.pos()
            return math.sqrt((self.x - pos[0])**2 + (self.y - pos[1])**2)
        else:
            # タプル形式の座標の場合
            return math.sqrt((self.x - other[0])**2 + (self.y - other[1])**2)

class Predator:
    """捕食者システム：コミュニティ形成の外的圧力"""
    def __init__(self, pos, aggression=0.7):
        self.x, self.y = pos
        self.aggression = aggression
        self.hunt_radius = 8
        self.alive = True
        
        # SSD要素
        self.E = 4.0  # 意味圧（生存圧・狩猟圧）
        self.kappa = 1.0  # 整合慣性（学習した狩猟パターン）
        self.P = 2.0  # 未処理圧（ストレス・失敗）
        
        # 捕食者特有要素
        self.hunger_level = 0.8
        self.territory_center = pos
        self.territory_radius = 30
        self.human_threat_awareness = 0.0  # 人間への警戒度
        self.learned_patterns = {}
        self.last_successful_hunt = 0
        self.consecutive_failures = 0
        
        # 狩猟経験
        self.prey_hunting_success = 0
        self.human_encounter_experience = 0
        
    def pos(self):
        """現在位置を取得"""
        return (self.x, self.y)
        
    def distance_to(self, other):
        """指定位置までの距離を計算"""
        if hasattr(other, 'x') and hasattr(other, 'y'):
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        elif hasattr(other, 'pos'):
            pos = other.pos()
            return math.sqrt((self.x - pos[0])**2 + (self.y - pos[1])**2)
        else:
            # タプル形式の座標の場合
            return math.sqrt((self.x - other[0])**2 + (self.y - other[1])**2)
        
    def hunt_prey(self, prey_animals, current_tick):
        """動物（獲物）を狩る"""
        hunted_prey = []
        
        for prey in prey_animals:
            if not prey.alive:
                continue
                
            distance = self.distance_to(prey)
            if distance <= self.hunt_radius:
                # 狩猟成功判定
                base_success = 0.7  # 捕食者は動物狩りが得意
                fear_penalty = prey.fear_level * 0.3  # 警戒された獲物は逃げやすい
                
                success_rate = base_success - fear_penalty
                
                if random.random() < success_rate:
                    prey.alive = False
                    hunted_prey.append(prey)
                    self.hunger_level = max(0, self.hunger_level - 0.4)
                    self.prey_hunting_success += 1
                    self.last_successful_hunt = current_tick
                    self.consecutive_failures = 0
                    
                    # SSD学習: 成功パターンの強化
                    self.kappa += 0.05
                    self.P = max(0, self.P - 0.1)
                    
                else:
                    # 狩猟失敗
                    self.consecutive_failures += 1
                    self.P += 0.1
                    
                    # 連続失敗でストレス増加→人間襲撃確率上昇
                    if self.consecutive_failures > 3:
                        self.E += 0.2  # 生存圧増加
        
        return hunted_prey
    
    def assess_human_threat(self, humans):
        """人間の脅威レベルを評価"""
        threat_level = 0.0
        group_size = len([h for h in humans if h.alive and self.distance_to(h) < 30])
        
        # 集団の人間は脅威
        if group_size >= 3:
            threat_level += 0.4
        elif group_size >= 2:
            threat_level += 0.2
            
        # 経験豊富な人間は脅威
        experienced_humans = [h for h in humans if h.experience.get('predator_awareness', 0) > 0.3]
        threat_level += len(experienced_humans) * 0.1
        
        self.human_threat_awareness = min(1.0, threat_level)
        return threat_level
    
    def decide_hunt_target(self, humans, prey_animals):
        """狩猟対象の決定（人間 vs 動物）"""
        human_threat = self.assess_human_threat(humans)
        
        # 飢餓状態かつ人間の脅威が低い場合→人間を狙う
        if self.hunger_level > 0.7 and human_threat < 0.3:
            return 'human'
        
        # 獲物が豊富→動物を狙う
        available_prey = [p for p in prey_animals if p.alive]
        if len(available_prey) > 2:
            return 'prey'
            
        # ストレス状態→人間を狙う（危険だが報酬大）
        if self.P > self.E * 0.8:
            return 'human'
            
        return 'prey'
    
    def hunt_step(self, npcs, current_tick=0):
        """NPCを狩る行動（経験システム統合）"""
        if not self.alive:
            return None
            
        nearby_npcs = [npc for npc in npcs if npc.alive and self.distance_to(npc.pos()) <= self.hunt_radius]
        if not nearby_npcs:
            return None
        
        # 各NPCの遭遇回避をチェック
        potential_targets = []
        for npc in nearby_npcs:
            avoidance_chance = npc.get_predator_avoidance_chance()
            if random.random() >= avoidance_chance:  # 回避失敗
                potential_targets.append(npc)
                npc.predator_encounters += 1
            else:
                # 回避成功で少し経験獲得
                npc.gain_experience('predator_awareness', 0.02, current_tick)
        
        if not potential_targets:
            return None  # 全員回避成功
        
        target = min(potential_targets, key=lambda n: self.distance_to(n.pos()))
        nearby_defenders = len([npc for npc in potential_targets if self.distance_to(npc.pos()) <= 3])
        
        # 早期発見チェック
        detection_chance = target.get_predator_detection_chance()
        early_detection = random.random() < detection_chance
        
        if early_detection:
            # 早期発見時は仲間に警告
            alerted = target.alert_nearby_npcs_about_predator(npcs, self.pos())
            target.gain_experience('predator_awareness', 0.05, current_tick)
            # 早期発見時は逃走にボーナス
            escape_bonus = 0.2
        else:
            escape_bonus = 0.0
        
        # 逃走判定（経験考慮）
        escape_chance = target.get_predator_escape_chance() + escape_bonus
        
        if random.random() < escape_chance:
            # 逃走成功
            target.predator_escapes += 1
            target.gain_experience('predator_awareness', 0.08, current_tick)
            target.fatigue = min(100.0, target.fatigue + 20.0)  # 疲労増加
            return None
        
        # 攻撃成功
        # 集団防御の効果
        attack_success_rate = self.aggression - (nearby_defenders * 0.3)
        attack_success_rate = max(0.1, min(0.9, attack_success_rate))
        
        if random.random() < attack_success_rate:
            target.alive = False
            return {"victim": target.name, "defenders": nearby_defenders, "escape_failed": True}
        else:
            # 攻撃失敗（重傷だが生存）
            # NPCの体力システムに合わせて怪我を表現
            injury_damage = random.uniform(30, 60)
            target.fatigue = min(100.0, target.fatigue + injury_damage * 0.5)
            target.hunger = min(200.0, target.hunger + injury_damage * 0.3)  # 怪我により代謝亢進
            target.gain_experience('predator_awareness', 0.12, current_tick)  # 生存時は大きな経験
            return {"victim": None, "injured": target.name, "defenders": nearby_defenders}
        
        return None


class Environment:
    """環境とリソース管理（エコシステム対応）"""
    def __init__(self, size=90, n_berry=120, n_hunt=60, n_water=40, n_caves=25):
        self.size = size
        self.weather = Weather()
        self.day_night = DayNightCycle()
        self.predators = []
        self.prey_animals = []  # 獲物動物のリスト
        
        # リソース生成
        self.water_sources = {f"water_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                             for i in range(n_water)}
        self.berries = {f"berry_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                       for i in range(n_berry)}
        self.hunting_grounds = {f"hunt_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                               for i in range(n_hunt)}
        self.caves = {f"cave_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                     for i in range(n_caves)}
        
        # 獲物動物の初期生成
        self._spawn_initial_prey()
        
    def step(self):
        """環境の1ステップ更新"""
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
    
    def _spawn_initial_prey(self):
        """初期獲物動物の生成"""
        from config import PREY_ANIMALS
        for animal_type in PREY_ANIMALS.keys():
            count = PREY_ANIMALS[animal_type]['spawn_count']
            for _ in range(count):
                x = random.randint(5, self.size-5)
                y = random.randint(5, self.size-5)
                self.prey_animals.append(Prey(x, y, animal_type))
    
    def ecosystem_step(self, npcs, current_tick):
        """エコシステム全体の1ステップ更新"""
        # 既存の環境ステップ
        self.step()
        
        # 獲物動物の更新
        humans = [npc for npc in npcs if npc.alive]
        for prey in self.prey_animals:
            if prey.alive:
                prey.update_fear(self.predators, humans)
        
        # 捕食者の動物狩り
        for predator in self.predators:
            if predator.alive:
                hunted = predator.hunt_prey(self.prey_animals, current_tick)
                
        # 獲物動物の自然繁殖
        self._natural_prey_spawning()
        
        # 狩場競合の処理
        self._process_hunting_competition(humans, current_tick)
    
    def _natural_prey_spawning(self):
        """獲物動物の自然繁殖"""
        from config import PREY_ANIMALS
        for animal_type in PREY_ANIMALS.keys():
            current_count = len([p for p in self.prey_animals if p.alive and p.type == animal_type])
            max_count = PREY_ANIMALS[animal_type]['spawn_count']
            
            if current_count < max_count * 0.5:  # 半数以下になったら補充
                spawn_chance = 0.05 * (1 - current_count / max_count)
                if random.random() < spawn_chance:
                    x = random.randint(5, self.size-5)
                    y = random.randint(5, self.size-5)
                    self.prey_animals.append(Prey(x, y, animal_type))
    
    def _process_hunting_competition(self, humans, current_tick):
        """人間と捕食者の狩場競合処理"""
        from config import HUNTING_GROUND_COMPETITION
        
        for hunting_ground in self.hunting_grounds.values():
            # 狩場周辺の人間と捕食者
            nearby_humans = [h for h in humans if self._distance_to_point(h.pos(), hunting_ground) < HUNTING_GROUND_COMPETITION['competition_radius']]
            nearby_predators = [p for p in self.predators if p.alive and self._distance_to_point(p.pos(), hunting_ground) < HUNTING_GROUND_COMPETITION['competition_radius']]
            
            # 競合が発生した場合
            if nearby_humans and nearby_predators:
                # 人間が獲物を取れる確率が減少
                competition_penalty = len(nearby_predators) * HUNTING_GROUND_COMPETITION['human_penalty_per_predator']
                for human in nearby_humans:
                    # 狩猟ペナルティを何らかの形で適用（NPCクラスにメソッドがあれば）
                    if hasattr(human, 'apply_hunting_penalty'):
                        human.apply_hunting_penalty(competition_penalty)
    
    def _distance_to_point(self, pos1, pos2):
        """2点間の距離計算"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def get_available_prey_near(self, pos, radius=15):
        """指定位置周辺の利用可能な獲物を取得"""
        nearby_prey = []
        for prey in self.prey_animals:
            if prey.alive and self._distance_to_point(pos, (prey.x, prey.y)) <= radius:
                nearby_prey.append(prey)
        return nearby_prey
    
    def nearest_nodes(self, pos, nodes_dict, k=3):
        """指定位置から最も近いノードを取得"""
        if not nodes_dict:
            return []
        distances = [(node_pos, math.sqrt((pos[0]-node_pos[0])**2 + (pos[1]-node_pos[1])**2)) 
                    for node_pos in nodes_dict.values()]
        distances.sort(key=lambda x: x[1])
        return [pos for pos, _ in distances[:k]]