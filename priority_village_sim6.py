import random, math
from collections import defaultdict
import numpy as np
import pandas as pd

# スカウト復帰テスト用に異なるseedを使用
import time
seed_val = int(time.time()) % 1000
random.seed(seed_val); np.random.seed(seed_val)
print(f"Using random seed: {seed_val}")

# =========================
# Weather System
# =========================
class Weather:
    def __init__(self, change_interval=24):
        self.condition = "sunny"  # 'sunny' or 'rainy'
        self.intensity = 0.2      # 0.0 (calm) to 1.0 (intense)
        self.change_interval = change_interval
        self.ticks_since_change = 0

    def step(self):
        self.ticks_since_change += 1
        if self.ticks_since_change >= self.change_interval:
            self.ticks_since_change = 0
            if self.condition == "sunny":
                if random.random() < 0.3:
                    self.condition = "rainy"
                    self.intensity = random.uniform(0.3, 0.8)
                else:
                    self.intensity = random.uniform(0.1, 1.0)
            else: # rainy
                if random.random() < 0.4:
                    self.condition = "sunny"
                    self.intensity = random.uniform(0.1, 0.6)
                else:
                    self.intensity = random.uniform(0.2, 1.0)

# =========================
# Day/Night Cycle
# =========================
class DayNightCycle:
    def __init__(self, day_length=48, night_start=0.6, night_end=0.9):
        self.day_length = day_length
        self.night_start = night_start
        self.night_end = night_end
        self.current_tick = 0
        
    def step(self):
        self.current_tick += 1
        
    def get_time_of_day(self):
        return (self.current_tick % self.day_length) / self.day_length
        
    def is_night(self):
        time = self.get_time_of_day()
        return time >= self.night_start or time < 0.1
        
    def get_light_level(self):
        time = self.get_time_of_day()
        if self.is_night():
            return 0.1
        # Smooth daylight curve
        daylight_factor = (time - 0.1) / (self.night_start - 0.1)
        return (math.sin((daylight_factor - 0.5) * math.pi) + 1) / 2

# =========================
# Environment & Supporting Classes
# =========================
class EnvForageBuff:
    def __init__(self, size=80, n_berry=40, n_hunt=20, n_water=16, n_caves=10):
        self.size = size
        self.berries = {}
        for _ in range(n_berry):
            x, y = random.randrange(size), random.randrange(size)
            # ベリーの豊富さと再生率をさらに向上（生存率改善用）
            self.berries[(x, y)] = {"abundance": random.uniform(0.8, 1.0), "regen": random.uniform(0.015, 0.035)}
        
        self.huntzones = {}
        for _ in range(n_hunt):
            x, y = random.randrange(size), random.randrange(size)
            # 狩場の豊富さを向上し、枯渇率を低下
            self.huntzones[(x, y)] = {"richness": random.uniform(0.6, 0.9), "depletion": random.uniform(0.001, 0.005)}
        
        self.water_sources = {(random.randrange(size), random.randrange(size)): {"quality": random.uniform(0.5, 1.0)} for _ in range(n_water)}
        self.caves = {(random.randrange(size), random.randrange(size)): {"safety_bonus": random.uniform(0.7, 0.9)} for _ in range(n_caves)}
        
        self.t = 0
        self.day_night = DayNightCycle()
        self.weather = Weather()
        
        # 捕食者システム
        self.predators = []  # アクティブな捕食者のリスト
        self.predator_spawn_probability = 0.003  # 毎ティック0.3%の捕食者出現確率
        self.predator_activity_modifier = {'sunny': 0.7, 'rainy': 1.3}  # 天候による活動度変化
    
    def forage(self, pos, node):
        """ベリーの採集を試みる"""
        if node not in self.berries:
            return False, 0.0, 0.0, 0.0
        
        abundance = self.berries[node]["abundance"]
        # 採集成功率をさらに向上（スカウト復帰テスト用）
        p = 0.9 * abundance  # 0.8から0.9に向上
        if self.weather.condition == "rainy":
            p *= (1.0 - 0.2 * self.weather.intensity)  # 雨の影響をさらに緩和
        
        success = random.random() < p
        if success:
            self.berries[node]["abundance"] = max(0.0, self.berries[node]["abundance"] - random.uniform(0.05, 0.2))  # 消耗をさらに減少
            food = random.uniform(25, 45) * (0.8 + abundance / 2)  # 食料量をさらに増加
        else:
            food = 0.0
        risk = 0.05
        return success, food, risk, p

    def step(self, npcs=None):
        for v in self.berries.values(): 
            v["abundance"] = min(1.0, v["abundance"] + v["regen"] * (1.0 - v["abundance"]))
        
        # 捕食者システムの更新
        if npcs:
            self.update_predators(npcs)
        
        self.t += 1
        self.day_night.step()
        self.weather.step()
    
    def update_predators(self, npcs):
        """捕食者システムの更新"""
        # 新しい捕食者の出現判定
        weather_modifier = self.predator_activity_modifier.get(self.weather.condition, 1.0)
        spawn_chance = self.predator_spawn_probability * weather_modifier
        
        if self.day_night.is_night():  # 夜間は捕食者活動増加
            spawn_chance *= 2.0
        
        if random.random() < spawn_chance and len(self.predators) < 3:  # 最大3匹まで
            spawn_x = random.randint(0, self.size - 1)
            spawn_y = random.randint(0, self.size - 1)
            new_predator = Predator((spawn_x, spawn_y), self)
            self.predators.append(new_predator)
        
        # 既存捕食者の行動
        predator_attacks = []
        for predator in self.predators[:]:
            if predator.alive:
                attack_result = predator.step(npcs, self.t)
                if attack_result:
                    predator_attacks.append(attack_result)
            else:
                self.predators.remove(predator)
        
        return predator_attacks if predator_attacks else []
        
    def nearest_nodes(self, pos, node_dict, k=4):
        nodes = list(node_dict.keys())
        if not nodes: return []
        nodes.sort(key=lambda p: abs(p[0] - pos[0]) + abs(p[1] - pos[1]))
        return nodes[:k]

# =========================
# Territory & NPC Class
# =========================
class Predator:
    def __init__(self, spawn_pos, env):
        self.x, self.y = spawn_pos
        self.env = env
        self.hunger = 100.0  # 捕食者の空腹度
        self.aggression = random.uniform(0.6, 1.0)  # 攻撃性
        self.hunt_radius = 8  # 狩猟範囲
        self.alive = True
        self.age = 0  # 生存時間
        self.max_age = random.randint(100, 300)  # 最大生存時間
        
    def pos(self):
        return (self.x, self.y)
        
    def move_towards_target(self, target_pos):
        """ターゲットに向かって移動"""
        tx, ty = target_pos
        if abs(self.x - tx) > 0:
            self.x += (1 if tx > self.x else -1)
        elif abs(self.y - ty) > 0:
            self.y += (1 if ty > self.y else -1)
        
        # 環境境界内に制限
        self.x = max(0, min(self.env.size - 1, self.x))
        self.y = max(0, min(self.env.size - 1, self.y))
    
    def find_prey(self, npcs):
        """獲物となるNPCを探す"""
        potential_prey = []
        for npc in npcs:
            if npc.alive:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                if distance <= self.hunt_radius:
                    # 孤立したNPCほど狙いやすい
                    nearby_allies = len([other for other in npcs 
                                       if other != npc and other.alive and 
                                       abs(other.x - npc.x) + abs(other.y - npc.y) < 3])
                    vulnerability = 1.0 - (nearby_allies * 0.2)  # 仲間が多いほど安全
                    potential_prey.append((npc, distance, vulnerability))
        
        if potential_prey:
            # 最も脆弱なターゲットを選択
            return max(potential_prey, key=lambda x: x[2] - x[1] * 0.1)[0]
        return None
    
    def attack_prey(self, target_npc, t):
        """獲物を攻撃"""
        if abs(self.x - target_npc.x) + abs(self.y - target_npc.y) <= 1:
            # 攻撃成功の判定
            nearby_defenders = len([npc for npc in target_npc.roster_ref.values()
                                  if npc != target_npc and npc.alive and
                                  abs(npc.x - target_npc.x) + abs(npc.y - target_npc.y) < 2])
            
            defense_bonus = nearby_defenders * 0.3  # 仲間による防御ボーナス
            attack_success_rate = self.aggression - defense_bonus
            
            if random.random() < attack_success_rate:
                # 攻撃成功 - NPCが重傷または死亡
                damage = random.uniform(30, 60)
                target_npc.fatigue = min(100, target_npc.fatigue + damage)
                
                attack_result = {
                    "t": t, "predator_pos": self.pos(), "victim": target_npc.name,
                    "victim_pos": target_npc.pos(), "damage": damage,
                    "defenders": nearby_defenders, "success": True
                }
                
                if target_npc.fatigue >= 100:  # 致命傷
                    target_npc.alive = False
                    attack_result["fatal"] = True
                
                self.hunger = max(0, self.hunger - 50)  # 捕食者の満腹度回復
                return attack_result
            else:
                # 攻撃失敗 - 集団防御成功
                return {
                    "t": t, "predator_pos": self.pos(), "victim": target_npc.name,
                    "defenders": nearby_defenders, "success": False,
                    "defense_successful": True
                }
        return None
    
    def step(self, npcs, t):
        """捕食者の行動ステップ"""
        self.age += 1
        self.hunger += 2  # 時間経過で空腹度増加
        
        # 寿命チェック
        if self.age > self.max_age or self.hunger > 200:
            self.alive = False
            return None
        
        # 獲物を探して攻撃
        prey = self.find_prey(npcs)
        if prey:
            if abs(self.x - prey.x) + abs(self.y - prey.y) > 1:
                self.move_towards_target(prey.pos())
            else:
                return self.attack_prey(prey, t)
        else:
            # 獲物がいない場合はランダム移動
            self.x += random.choice([-1, 0, 1])
            self.y += random.choice([-1, 0, 1])
            self.x = max(0, min(self.env.size - 1, self.x))
            self.y = max(0, min(self.env.size - 1, self.y))
        
        return None

class Territory:
    def __init__(self, owner, center, radius):
        self.owner = owner
        self.center = center
        self.radius = radius
        
        # オキシトシン的縄張り - 人も含む社会的領域
        self.social_members = set([owner])  # 縄張りの社会的メンバー
        self.bonding_strength = {owner: 1.0}  # メンバーとの結束強度
        self.shared_activities = []  # 共有活動の履歴
        self.collective_safety_memory = 0.0  # 集団安全体験の記憶
        
    def get_community_size(self):
        """コミュニティの実質的なサイズを取得"""
        return len(self.social_members)
    
    def get_active_members(self, roster_ref):
        """現在アクティブなメンバーのリストを取得"""
        active_members = []
        for member_name in self.social_members:
            if member_name in roster_ref and roster_ref[member_name].alive:
                active_members.append(roster_ref[member_name])
        return active_members
    
    def get_community_cohesion(self):
        """コミュニティの結束度を計算"""
        if len(self.bonding_strength) <= 1:
            return 1.0  # 単独の場合は最大結束
        
        total_bonding = sum(self.bonding_strength.values())
        max_possible = len(self.bonding_strength) * 1.0
        return total_bonding / max_possible if max_possible > 0 else 0.0
    
    def add_member(self, member_name, bonding_strength=0.5):
        """新しいメンバーを追加"""
        self.social_members.add(member_name)
        self.bonding_strength[member_name] = bonding_strength
    
    def remove_member(self, member_name):
        """メンバーを除外"""
        self.social_members.discard(member_name)
        self.bonding_strength.pop(member_name, None)

# =========================
# NPC Class (16人拡張版)
# =========================
class NPCPriority:
    def __init__(self, name, preset, env, roster_ref, start_pos):
        self.name = name
        self.env = env
        self.roster_ref = roster_ref
        self.x, self.y = start_pos
        self.hunger = 20.0  # 初期空腹度をさらに低く（スカウト復帰テスト用）
        self.thirst = 10.0  # 初期渇きをさらに低く
        self.fatigue = 20.0  # 初期疲労をさらに低く
        self.alive = True
        self.log = []
        
        # SSD パラメータ
        self.kappa = defaultdict(lambda: 0.1)
        self.E = 0.0
        self.T0 = 0.3
        self.T = self.T0

        # 性格プリセット
        self.curiosity = preset["curiosity"]
        self.risk_tolerance = preset["risk_tolerance"]
        self.empathy = preset.get("empathy", 0.6)

        # 関係性の初期化
        self.rel = defaultdict(float)

        # 行動モード関連（跳躍的変化システム）
        self.role = "generalist"  # 基本役割は保持
        self.exploration_mode = False  # 探索モードの状態
        self.exploration_mode_start_tick = 0  # 探索モード開始時刻
        self.exploration_intensity = 1.0  # 探索の強度倍率
        # 定住整合慣性システム（SSD理論）
        self.settlement_experiences = {'resource_stability': [], 'social_stability': [], 'exploration_satisfaction': []}
        

        
        # 基本パラメータ
        self.age = random.randint(20, 40)  # 初期年齢
        self.experience_points = 0.0       # 経験値累積
        self.lifetime_discoveries = 0      # 生涯発見数
        self.last_discovery_tick = 0
        
        # 縄張りシステム（整合慣性ベース）
        self.territory = None              # 所有する縄張り
        self.territory_claim_strength = 0.0  # 縄張り主張の強さ
        self.territorial_aggression = random.uniform(0.1, 0.7)  # 縄張り意識
        self.home_cave = None              # ホーム洞窟
        self.territory_violations = 0      # 侵入被害回数
        
        # 安全性整合慣性（SSD理論）
        self.cave_safety_experiences = {}  # 洞窟ごとの安全性体験
        self.territory_claim_threshold = 0.25  # 縄張り主張の安全感閾値（社会的要素を重視）
        self.safety_coherence_threshold = 0.2  # 縄張り主張の整合闾值（低めに設定）
        
        # 知識管理を拡張：各種リソースの発見状況を管理
        self.knowledge_caves = set()
        self.knowledge_water = set()
        self.knowledge_berries = set()  # ベリー採取場所の知識
        self.knowledge_huntzones = set()  # 狩場の知識
        
        # 初期知識を最小限に：最低限のリソースのみ知っている状態
        initial_cave = self.env.nearest_nodes(self.pos(), self.env.caves, k=1)
        if initial_cave: self.knowledge_caves.add(initial_cave[0])
        
        # 水源知識を大幅増加（水不足を防ぐ）
        initial_waters = self.env.nearest_nodes(self.pos(), self.env.water_sources, k=4)
        for water in initial_waters:
            self.knowledge_water.add(water)
            
        initial_berries = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
        for berry in initial_berries:
            self.knowledge_berries.add(berry)

    def pos(self):
        return (self.x, self.y)
        
    def dist_to(self, o):
        return abs(self.x - o.x) + abs(self.y - o.y)
        
    def dist_to_pos(self, pos):
        return abs(self.x - pos[0]) + abs(self.y - pos[1])  # タプル座標との距離計算
        
    def move_towards(self, target):
        tx, ty = target
        self.x += (1 if tx > self.x else -1 if tx < self.x else 0)
        self.y += (1 if ty > self.y else -1 if ty < self.y else 0)
        self.x = max(0, min(self.env.size - 1, self.x))
        self.y = max(0, min(self.env.size - 1, self.y))
        
    def nearby_allies(self, radius=3):
        return [o for on, o in self.roster_ref.items() if on != self.name and o.alive and self.dist_to(o) <= radius]

    # 拡張された探索圧力計算
    def calculate_life_crisis_pressure(self):
        """命の危機という意味圧を計算（SSD理論）"""
        crisis_pressure = 0.0
        
        # 1. 脂水症の危機（未来予測的判断）
        if self.thirst > 140:  # 180で死亡なので140から危機意識
            dehydration_crisis = (self.thirst - 140) / 40.0  # 0-1.0の範囲
            crisis_pressure += dehydration_crisis * 2.0  # 脂水症は最優先
        
        # 2. 餓死の危機
        if self.hunger > 160:  # 200で死亡なので160から危機意識
            starvation_crisis = (self.hunger - 160) / 40.0
            crisis_pressure += starvation_crisis * 1.5
        
        # 3. 疲労による判断力低下の危機
        if self.fatigue > 80:
            fatigue_crisis = (self.fatigue - 80) / 20.0
            crisis_pressure += fatigue_crisis * 1.0
        
        # 4. 組み合わせリスク（複数の問題が同時発生）
        risk_factors = 0
        if self.thirst > 120: risk_factors += 1
        if self.hunger > 120: risk_factors += 1  
        if self.fatigue > 70: risk_factors += 1
        
        if risk_factors >= 2:
            crisis_pressure += risk_factors * 0.5  # 複合リスクの加算
        
        return min(4.0, crisis_pressure)  # 最大値制限
    
    def calculate_exploration_pressure(self):
        pressure = 0.0
        ticks_since_discovery = self.env.t - self.last_discovery_tick
        boredom = min(1.0, ticks_since_discovery / 150.0)
        pressure += boredom * 0.6
        
        # 全リソースタイプの未発見状況を考慮した探索圧力
        total_unknown_pressure = 0.0
        
        if len(self.knowledge_caves) < len(self.env.caves):
            cave_ratio = 1.0 - len(self.knowledge_caves) / len(self.env.caves)
            total_unknown_pressure += cave_ratio * 0.25
            
        if len(self.knowledge_water) < len(self.env.water_sources):
            water_ratio = 1.0 - len(self.knowledge_water) / len(self.env.water_sources)
            total_unknown_pressure += water_ratio * 0.25
            
        if len(self.knowledge_berries) < len(self.env.berries):
            berry_ratio = 1.0 - len(self.knowledge_berries) / len(self.env.berries)
            total_unknown_pressure += berry_ratio * 0.3  # 食料は重要なので重み大
            
        if len(self.knowledge_huntzones) < len(self.env.huntzones):
            hunt_ratio = 1.0 - len(self.knowledge_huntzones) / len(self.env.huntzones)
            total_unknown_pressure += hunt_ratio * 0.2
            
        pressure += total_unknown_pressure
        
        # 探索モード中は他者の情報不足がさらなる探索圧力を生む
        if self.exploration_mode:
            allies_needing_info = 0
            for ally in self.nearby_allies(radius=100):
                if (len(ally.knowledge_caves) < len(self.knowledge_caves) or
                    len(ally.knowledge_berries) < len(self.knowledge_berries) or
                    len(ally.knowledge_huntzones) < len(self.knowledge_huntzones)):
                    allies_needing_info += 1
            if allies_needing_info > 0: pressure += 0.3 * self.exploration_intensity
            
        return min(2.5, pressure)
    
    def calculate_leadership_influence(self):
        """リーダーシップ影響力の計算"""
        influence = 0.0
        
        # 1. 情報優位性（知識の豊富さ）
        total_knowledge = (len(self.knowledge_caves) + len(self.knowledge_water) + 
                          len(self.knowledge_berries) + len(self.knowledge_huntzones))
        max_possible_knowledge = (len(self.env.caves) + len(self.env.water_sources) + 
                                 len(self.env.berries) + len(self.env.huntzones))
        
        if max_possible_knowledge > 0:
            knowledge_advantage = total_knowledge / max_possible_knowledge
            influence += knowledge_advantage * 0.4
        
        # 2. 社会的整合慣性（協力経験）
        social_experience = self.kappa.get("social", 0.1)
        influence += social_experience * 0.3
        
        # 3. 関係性ネットワークの幅と深さ
        relationship_strength = sum(self.rel.values()) / max(1, len(self.rel))
        relationship_breadth = len([r for r in self.rel.values() if r > 0.3]) / max(1, len(self.roster_ref) - 1)
        influence += (relationship_strength * 0.15 + relationship_breadth * 0.15)
        
        # 4. 性格的適性（リーダーシップ素質）
        leadership_traits = (self.empathy * 0.4 + (1.0 - self.risk_tolerance * 0.3) + 
                           self.curiosity * 0.3)
        influence += leadership_traits * 0.2
        
        return min(1.0, influence)
    
    def calculate_decision_pressure(self):
        """集団意思決定の必要性を計算"""
        pressure = 0.0
        nearby_allies = self.nearby_allies(radius=10)
        
        if len(nearby_allies) < 3:  # 小さすぎる集団はリーツー不要
            return 0.0
        
        # 1. 情報の散乱度（異なる知識を持つ人数）
        knowledge_disparity = 0.0
        my_total_knowledge = len(self.knowledge_caves) + len(self.knowledge_berries)
        
        for ally in nearby_allies:
            ally_knowledge = len(ally.knowledge_caves) + len(ally.knowledge_berries)
            if abs(my_total_knowledge - ally_knowledge) > 5:
                knowledge_disparity += 0.1
        
        pressure += min(0.4, knowledge_disparity)
        
        # 2. 探索モードの非同期性（判断が割れている）
        exploration_modes = sum(1 for ally in nearby_allies if ally.exploration_mode)
        if 0 < exploration_modes < len(nearby_allies):
            pressure += 0.3  # 一部だけが探索モードの場合
        
        # 3. リソース競争の必要性
        resource_competition = self.calculate_exploration_pressure() * 0.2
        pressure += min(0.3, resource_competition)
        
        return min(1.0, pressure)

    def experience_discovery_pleasure(self, t, resource_type, node):
        meaning_pressure = self.calculate_exploration_pressure()
        
        # リソースタイプに応じた発見価値の設定
        resource_values = {
            "cave": 0.9,           # 安全な避難場所として高価値
            "water": 0.8,          # 生存に必須
            "berry_patch": 1.0,    # 食料確保で最高価値
            "hunting_ground": 0.85  # タンパク質源として高価値
        }
        
        value = resource_values.get(resource_type, 0.7)
        # 探索モード中は発見報酬が増加
        mode_multiplier = self.exploration_intensity if self.exploration_mode else 1.0
        pleasure = meaning_pressure * value * 1.0 * mode_multiplier
        
        self.kappa["exploration"] = min(1.0, self.kappa.get("exploration", 0.1) + 0.15)
        self.E = min(5.0, self.E + pleasure * 0.5)
        self.T = max(self.T0, self.T - 0.3)
        self.last_discovery_tick = t
        
        # 引退システム：経験値と発見回数の累積
        self.experience_points += pleasure * 0.3
        self.lifetime_discoveries += 1
        
        self.log.append({"t": t, "name": self.name, "action": f"discovery_pleasure_{resource_type}", "pleasure": pleasure})
        return pleasure

    def consider_exploration_mode_shift(self, t):
        """意味圧に応じた探索モードの跳躍的変化と復帰判定"""
        # 命の危機意味圧を優先評価
        life_crisis = self.calculate_life_crisis_pressure()
        
        if self.exploration_mode:
            # 命の危機が高い場合は即座に探索モードを終了
            if life_crisis > 1.5:  # 重大な命の危機
                self.exploration_mode = False
                self.mode_stability_counter = 0
                self.log.append({"t": t, "name": self.name, "action": "emergency_exploration_exit", 
                               "life_crisis": life_crisis, "thirst": self.thirst, "hunger": self.hunger,
                               "fatigue": self.fatigue, "reason": "life_crisis_override"})
                return True
            
            # 通常の探索モードからの復帰判定
            exploration_pressure = self.calculate_exploration_pressure()
            return self.consider_mode_reversion(t, exploration_pressure)
        else:
            # 命の危機がある場合は探索モードへの突入を抑制
            if life_crisis > 1.0:
                return False  # 探索よりも生存を優先
            
            # 通常の探索モードへの跳躍判定
            exploration_pressure = self.calculate_exploration_pressure()
            return self.consider_exploration_leap(t, exploration_pressure)
    
    def consider_exploration_leap(self, t, exploration_pressure):
        """探索モードへの跳躍的移行判定（SSD理論：未処理圧統合版）"""
        # 基本意味圧閾値（好奇心による調整）
        base_threshold = 0.8 + (1.0 - self.curiosity) * 0.3
        
        # SSD理論：未処理圧(E)による跳躍閾値の動的調整
        # Eが高いほど跳躍しやすくなる（蓄積された未解決の意味圧）
        leap_threshold = base_threshold - (self.E * 0.2)
        leap_threshold = max(0.3, leap_threshold)  # 最小閾値を維持
        
        # 整合慣性と意味圧による跳躍判定
        exploration_experience = self.kappa.get("exploration", 0.1)
        # 未処理圧も跳躍確率に影響
        leap_probability = min(0.9, (exploration_pressure + self.E * 0.3) / 2.0) * (0.5 + exploration_experience)
        
        if exploration_pressure > leap_threshold and random.random() < leap_probability:
            # 探索モードへの跳躍的変化
            self.exploration_mode = True
            self.exploration_mode_start_tick = t
            self.exploration_intensity = 1.0 + exploration_pressure * 0.5  # 圧力に応じた強度
            self.mode_stability_counter = 0
            
            self.log.append({"t": t, "name": self.name, "action": "exploration_mode_leap", 
                           "pressure": exploration_pressure, "intensity": self.exploration_intensity})
            return True
            
        return False

    def consider_mode_reversion(self, t, exploration_pressure):
        """探索モードから通常モードへの復帰判定"""
        # 定住整合慣性の評価（SSD理論）
        resource_stability = self.evaluate_resource_stability()
        settlement_coherence = self.calculate_settlement_coherence(exploration_pressure, resource_stability)
        
        mode_duration = t - self.exploration_mode_start_tick
        
        # SSD理論：柔軟な復帰条件（重み付き総合判定）
        coherence_threshold = 0.7 - (self.curiosity * 0.2)  # 好奇心が高いほど定住しにくい
        
        # 復帰要因の重み付き評価
        coherence_factor = min(1.0, settlement_coherence / coherence_threshold)  # 定住整合性
        duration_factor = min(1.0, mode_duration / 15.0)  # 十分な探索期間
        pressure_factor = max(0.0, (0.6 - exploration_pressure) / 0.6)  # 探索圧力の低下
        
        # 未処理圧(E)の影響：Eが低いほど復帰しやすい
        energy_factor = max(0.0, (3.0 - self.E) / 3.0)
        
        # 総合復帰スコア（SSD理論：複合的要因による自然な相転移）
        reversion_score = (coherence_factor * 0.4 + duration_factor * 0.2 + 
                          pressure_factor * 0.3 + energy_factor * 0.1)
        
        # デバッグ情報（必要時）
        if mode_duration > 30 and t % 30 == 0:
            self.log.append({"t": t, "name": self.name, "action": "mode_reversion_check", 
                           "settlement_coherence": settlement_coherence, "duration": mode_duration, 
                           "exploration_pressure": exploration_pressure, "E": self.E,
                           "reversion_score": reversion_score, "factors": {
                               "coherence": coherence_factor, "duration": duration_factor,
                               "pressure": pressure_factor, "energy": energy_factor}})
        
        # 柔軟な復帰判定：スコア閾値 OR 強い単一要因
        if (reversion_score > 0.6 or  # 総合的な復帰条件
            (settlement_coherence >= coherence_threshold * 1.2) or  # 非常に強い定住感
            (exploration_pressure < 0.2 and mode_duration > 8)):  # 探索意欲の大幅低下
            
            # 探索モード終了時の体験記録（定住整合慣性への影響）
            self.record_settlement_experience(exploration_pressure, resource_stability, mode_duration)
            
            # 通常モードへの復帰
            self.exploration_mode = False
            self.exploration_intensity = 1.0
            
            # 探索経験を少し減衰（忘却効果）
            self.kappa["exploration"] = max(0.05, self.kappa.get("exploration", 0.1) * 0.9)
            
            self.log.append({"t": t, "name": self.name, "action": "exploration_mode_reversion", 
                           "duration": mode_duration, "stability": resource_stability,
                           "settlement_coherence": settlement_coherence})
            return True
        
        return False
    
    # def consider_leadership_emergence(self, t):
    #     """リーダーシップの初期発現判定"""
    #     if self.leadership_mode or self.leader_target:
    #         return False  # 既にリーダーかフォロワー
    #     
    #     # 影響力と意思決定圧力を計算
    #     influence = self.calculate_leadership_influence()
    #     decision_pressure = self.calculate_decision_pressure()
    #     
    #     # リーダーシップ発現の闾値
    #     leadership_threshold = 0.6 - (decision_pressure * 0.3)  # 圧力が高いほど低い闾値
    #     
    #     # 跳躍的リーダーシップ発現
    #     if influence > leadership_threshold and decision_pressure > 0.3:
    #         nearby_allies = self.nearby_allies(radius=10)
    #         
    #         # 他に強いリーダーがいないことを確認
    #         competing_leaders = [ally for ally in nearby_allies if ally.leadership_mode]
    #         if len(competing_leaders) == 0:
    #             
    #             self.leadership_mode = True
    #             self.leadership_start_tick = t
    #             self.influence_score = influence
    #             
    #             # 初期フォロワーの募集
    #             for ally in nearby_allies:
    #                 if self.rel.get(ally.name, 0) > 0.4:  # 関係性が良い人を優先
    #                     if random.random() < 0.6:  # 60%の確率でフォロー
    #                         ally.leader_target = self
    #                         self.followers.add(ally.name)
    #             
    #             self.log.append({"t": t, "name": self.name, "action": "leadership_emergence", 
    #                            "influence": influence, "pressure": decision_pressure, 
    #                            "initial_followers": len(self.followers)})
    #             return True
    #     
    #     return False
    
    # def consider_following_leader(self, t):
    #     """リーダーへのフォロー判定"""
    #     if self.leadership_mode or self.leader_target:
    #         return False  # 既にリーダーかフォロワー
    #     
    #     nearby_allies = self.nearby_allies(radius=10)
    #     potential_leaders = [ally for ally in nearby_allies if ally.leadership_mode]
    #     
    #     if not potential_leaders:
    #         return False
    #     
    #     # 最も適切なリーダーを選択
    #     best_leader = None
    #     best_score = 0.0
    #     
    #     for leader in potential_leaders:
    #         # リーダーの魅力度を計算
    #         relationship_bonus = self.rel.get(leader.name, 0) * 0.4
    #         knowledge_advantage = (len(leader.knowledge_caves) + len(leader.knowledge_berries) - 
    #                              len(self.knowledge_caves) - len(self.knowledge_berries)) * 0.02
    #         influence_bonus = leader.influence_score * 0.4
    #         
    #         total_score = relationship_bonus + max(0, knowledge_advantage) + influence_bonus
    #         
    #         if total_score > best_score:
    #             best_score = total_score
    #             best_leader = leader
    #     
    #     # フォローするかの判定
    #     follow_threshold = 0.5 - (self.calculate_decision_pressure() * 0.2)
    #     if best_score > follow_threshold:
    #         self.leader_target = best_leader
    #         best_leader.followers.add(self.name)
    #         
    #         # 関係性の向上
    #         self.rel[best_leader.name] = min(1.0, self.rel.get(best_leader.name, 0) + 0.2)
    #         best_leader.rel[self.name] = min(1.0, best_leader.rel.get(self.name, 0) + 0.1)
    #         
    #         self.log.append({"t": t, "name": self.name, "action": "follow_leader", 
    #                        "leader": best_leader.name, "score": best_score})
    #         return True
    #     
    #     return False
    
    def calculate_cave_safety_feeling(self, cave_pos):
        """洞窟への安全感を計算（安全と感じる場所＝縄張り）"""
        if cave_pos not in self.cave_safety_experiences:
            # 初回訪問時は本質的安全性のみ
            return self.env.caves[cave_pos]["safety_bonus"] * 0.4
        
        experiences = self.cave_safety_experiences[cave_pos]
        
        # 1. 安全体験の直接的影響（安全だった回数）
        safety_events = (
            experiences.get('positive_rest', 0) +           # 安全な休息体験
            experiences.get('weather_shelter', 0) * 1.2 +  # 天候からの避難体験（より強い安全感）
            experiences.get('social_bonus', 0) * 0.8       # 社交的安全体験
        )
        
        # 2. 本質的安全性（洞窟の物理的特性）
        intrinsic_safety = self.env.caves[cave_pos]["safety_bonus"]
        
        # 3. 体験に基づく主観的安全感（ここは安全だ、という感覚）
        experiential_safety = min(1.0, safety_events / 3.0)  # 3回の安全体験で最大安全感
        
        # 4. 社会的安全感（仒間がいることによる安心感）
        social_safety = self.calculate_social_safety_at_location(cave_pos)
        
        # 4.5. オキシトシン的縄張り効果（場所＋人の統合的安全感）
        oxytocin_effect = self.calculate_oxytocin_territory_effect(cave_pos)
        
        # 5. 総合安全感（体験、物理、社会、オキシトシンの4要素）
        total_safety_feeling = (intrinsic_safety * 0.15 + 
                               experiential_safety * 0.4 + 
                               social_safety * 0.25 +
                               oxytocin_effect * 0.2)  # オキシトシン効果を追加
        
        # 5. 安全感から縄張り意識への直接変換（安全だと感じるほど自分の場所だと思う）
        territory_instinct = total_safety_feeling
        
        # 7. 縄張り意識の強化（体験と社会的結束による）
        if safety_events > 2:  # 安全体験による強化
            territory_instinct *= (1.0 + (safety_events - 2) * 0.15)
        
        if social_safety > 0.4:  # 仒間がいることによる強化
            territory_instinct *= (1.0 + social_safety * 0.3)  # 社会的結束が強いほど縄張り意識強化
            
        return min(1.0, territory_instinct)  # 最大値を制限
    
    def calculate_settlement_coherence(self, exploration_pressure, resource_stability):
        """定住整合慣性を計算（SSD理論）"""
        # 1. 基本的な定住傾向（リソース安定性と探索圧力の逆相関）
        base_settlement_tendency = resource_stability * (1.0 - min(1.0, exploration_pressure))
        
        # 2. 体験による定住慣性の蓄積
        resource_experiences = getattr(self, 'settlement_experiences', {}).get('resource_stability', [])
        social_experiences = getattr(self, 'settlement_experiences', {}).get('social_stability', [])
        satisfaction_experiences = getattr(self, 'settlement_experiences', {}).get('exploration_satisfaction', [])
        
        # 最近の体験を重視（最新10個の体験）
        recent_resource_stability = sum(resource_experiences[-10:]) / max(1, len(resource_experiences[-10:]))
        recent_social_stability = sum(social_experiences[-10:]) / max(1, len(social_experiences[-10:]))
        recent_satisfaction = sum(satisfaction_experiences[-10:]) / max(1, len(satisfaction_experiences[-10:]))
        
        # 3. 整合慣性の統合計算
        experience_weight = 0.0
        if resource_experiences:
            stability_coherence = (recent_resource_stability * 0.4 + 
                                 recent_social_stability * 0.3 + 
                                 recent_satisfaction * 0.3)
            experience_weight = min(1.0, len(resource_experiences) / 15.0) * stability_coherence
        
        # 4. 最終的な定住整合慣性
        settlement_coherence = base_settlement_tendency * 0.4 + experience_weight * 0.6
        
        return settlement_coherence
    
    def calculate_social_safety_at_location(self, location):
        """指定した場所での社会的安全感を計算（仲間の存在による安心感）"""
        if location not in self.env.caves:
            return 0.0
            
        social_safety = 0.0
        
        # 1. 現在その場所にいる仲間の数
        companions_present = 0
        for npc in self.roster_ref.values():
            if npc != self and npc.alive and npc.pos() == location:
                companions_present += 1
        
        # 2. 同じ場所で過去に一緒に過ごした経験
        shared_experiences = 0
        cave_experiences = self.cave_safety_experiences.get(location, {})
        if 'social_bonus' in cave_experiences:
            shared_experiences = cave_experiences['social_bonus']
        
        # 3. 仲間の縄張り意識（その場所を安全だと思っている仲間の数）
        allies_claiming_territory = 0
        for npc in self.roster_ref.values():
            if npc != self and npc.alive and hasattr(npc, 'territory') and npc.territory == location:
                allies_claiming_territory += 1
        
        # 4. 社会的安全感の計算
        # 現在の仲間の存在（即座の安心感）
        immediate_social_safety = min(0.6, companions_present * 0.2)  # 最大3人で0.6
        
        # 過去の共有体験（この場所は仲間と安全に過ごした場所）
        experiential_social_safety = min(0.4, shared_experiences * 0.1)  # 最大4回で0.4
        
        # 集団の縄張り意識（みんなが安全だと思っている場所）
        collective_territory_safety = min(0.3, allies_claiming_territory * 0.15)  # 最大2人で0.3
        
        social_safety = immediate_social_safety + experiential_social_safety + collective_territory_safety
        
        return min(1.0, social_safety)  # 最大1.0に制限
    
    def calculate_oxytocin_territory_effect(self, location):
        """オキシトシン的縄張り効果 - 場所と人の統合的安全感"""
        if location not in self.env.caves:
            return 0.0
            
        oxytocin_effect = 0.0
        
        # 1. 縄張りメンバーシップ効果（この場所の「仲間」としての帰属感）
        territory_members = set()
        for npc in self.roster_ref.values():
            if (npc.alive and hasattr(npc, 'territory') and 
                npc.territory and npc.territory.center == location):
                territory_members.add(npc.name)
                if hasattr(npc.territory, 'social_members'):
                    territory_members.update(npc.territory.social_members)
        
        if self.name in territory_members:
            membership_bonus = 0.4  # 「ここは自分たちの場所」感覚
            oxytocin_effect += membership_bonus
        
        # 2. 共同活動による結束（一緒に過ごした時間の価値）
        location_key = f"{location[0]}_{location[1]}"
        shared_experiences = getattr(self, 'location_social_memories', {}).get(location_key, [])
        
        # 最近の共同体験（オキシトシン分泌促進）
        recent_bonding = sum(1 for exp in shared_experiences if exp.get('recent', False))
        bonding_effect = min(0.3, recent_bonding * 0.1)  # 最大0.3
        oxytocin_effect += bonding_effect
        
        # 3. 保護本能効果（仲間を守る場所としての意識）
        protection_instinct = 0.0
        for npc in self.roster_ref.values():
            if (npc != self and npc.alive and npc.pos() == location):
                relationship = self.rel.get(npc.name, 0)
                if relationship > 0.5:  # 強い絆がある仲間
                    protection_instinct += 0.15  # 「この人を守る場所」意識
        
        oxytocin_effect += min(0.4, protection_instinct)  # 最大0.4
        
        # 4. 安心感の相互強化（基本的な縄張り一致による信頼感で循環参照を回避）
        collective_confidence = 0.0
        for npc in self.roster_ref.values():
            if (npc != self and npc.alive and hasattr(npc, 'territory') and 
                npc.territory and npc.territory.center == location):
                # 単純な縄張り共有による信頼感（循環参照回避）
                collective_confidence += 0.1
        
        oxytocin_effect += min(0.3, collective_confidence)
        
        return min(1.2, oxytocin_effect)  # オキシトシン効果は通常の安全感を超える可能性
    
    def update_social_territory_bonding(self, t, location, companion_names):
        """社会的縄張りの結束を更新"""
        if not hasattr(self, 'location_social_memories'):
            self.location_social_memories = {}
            
        location_key = f"{location[0]}_{location[1]}"
        if location_key not in self.location_social_memories:
            self.location_social_memories[location_key] = []
        
        # 共同体験を記録（オキシトシン分泌のトリガー）
        bonding_event = {
            'tick': t,
            'companions': companion_names,
            'activity_type': 'territorial_bonding',
            'recent': True,  # 最近の体験フラグ
            'oxytocin_strength': len(companion_names) * 0.2
        }
        
        self.location_social_memories[location_key].append(bonding_event)
        
        # 古い記憶の「recent」フラグを更新
        for memory in self.location_social_memories[location_key]:
            if t - memory['tick'] > 50:  # 50ティック以上古い記憶は「recent」でなくなる
                memory['recent'] = False
        
        # メンバーとの結束強化
        for companion_name in companion_names:
            self.rel[companion_name] = min(1.0, self.rel.get(companion_name, 0) + 0.05)
            
        # コミュニティサイズの更新
        territory_at_location = None
        if hasattr(self, 'territory') and self.territory and self.territory.center == location:
            territory_at_location = self.territory
            
        community_size = territory_at_location.get_community_size() if territory_at_location else 1
        
        self.log.append({
            "t": t, "name": self.name, "action": "oxytocin_bonding",
            "location": location, "companions": companion_names,
            "bonding_strength": len(companion_names) * 0.2,
            "community_size_after": community_size
        })
    
    def emergency_survival_action(self, t, life_crisis):
        """命の危機時の緊急生存行動（探索よりも優先）"""
        # 1. 脂水症の緊急対処（最優先）
        if self.thirst > 140:
            known_water = {k: v for k, v in self.env.water_sources.items() if k in self.knowledge_water}
            if known_water:
                nearest_water = self.env.nearest_nodes(self.pos(), known_water, k=1)
                if nearest_water:
                    target = nearest_water[0]
                    if self.pos() == target:
                        self.thirst = max(0, self.thirst - 30)  # 大量水分補給
                        self.log.append({"t": t, "name": self.name, "action": "emergency_hydration", 
                                       "life_crisis": life_crisis, "thirst_before": self.thirst + 30})
                        return True
                    else:
                        self.move_towards(target)
                        self.log.append({"t": t, "name": self.name, "action": "emergency_seek_water", 
                                       "target": target, "life_crisis": life_crisis})
                        return True
        
        # 2. 餓死の緊急対処
        if self.hunger > 160:
            known_berries = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
            if known_berries:
                nearest_berries = self.env.nearest_nodes(self.pos(), known_berries, k=1)
                if nearest_berries:
                    target = nearest_berries[0]
                    success, food, _, _ = self.env.forage(self.pos(), target)
                    if success:
                        self.hunger = max(0, self.hunger - food * 1.5)  # 緊急時は効率アップ
                        self.log.append({"t": t, "name": self.name, "action": "emergency_foraging", 
                                       "life_crisis": life_crisis, "food_gained": food * 1.5})
                        return True
                    else:
                        self.move_towards(target)
                        return True
        
        # 3. 疲労回復の緊急対処
        if self.fatigue > 80:
            known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
            if known_caves:
                nearest_cave = self.env.nearest_nodes(self.pos(), known_caves, k=1)
                if nearest_cave:
                    target = nearest_cave[0]
                    if self.pos() == target:
                        recovery = 20  # 緊急時の大幅回復
                        self.fatigue = max(0, self.fatigue - recovery)
                        self.log.append({"t": t, "name": self.name, "action": "emergency_rest", 
                                       "life_crisis": life_crisis, "recovery": recovery})
                        return True
                    else:
                        self.move_towards(target)
                        return True
        
        return False
    
    def try_invite_companions_to_territory(self, t):
        """縄張りを持つNPCが仲間を招待する（社会的磁力）"""
        if self.territory is None:
            return False
            
        # 近くにいる仲間を探す
        nearby_npcs = []
        for npc in self.roster_ref.values():
            if (npc != self and npc.alive and 
                abs(npc.x - self.x) <= 15 and abs(npc.y - self.y) <= 15):
                
                # 関係性が良好で、疲労している、または夜間の場合に招待対象とする
                relationship = self.rel.get(npc.name, 0)
                is_tired = npc.fatigue > 60
                is_night_approaching = self.env.day_night.is_night() or self.env.day_night.get_time_of_day() > 0.5
                needs_shelter = not hasattr(npc, 'territory') or npc.territory is None
                
                if (relationship > 0.3 and (is_tired or is_night_approaching) and needs_shelter):
                    nearby_npcs.append(npc)
        
        if not nearby_npcs:
            return False
            
        # 招待する仲間を選択
        invited_companion = random.choice(nearby_npcs)
        
        # 招待の魅力度を計算（縄張りの安全感 + 関係性）
        territory_safety = self.calculate_cave_safety_feeling(self.territory)
        relationship_bonus = self.rel.get(invited_companion.name, 0) * 0.5
        invitation_appeal = territory_safety + relationship_bonus
        
        # 招待の受諾判定（コミュニティ形成促進のため大幅緩和）
        base_threshold = 0.2  # 0.4から下げて受け入れやすく
        empathy_bonus = invited_companion.empathy * 0.3  # 共感性ボーナスを増強
        loneliness_factor = 0.1 if not hasattr(invited_companion, 'territory') or invited_companion.territory is None else 0.0
        companion_acceptance_threshold = base_threshold - empathy_bonus - loneliness_factor
        
        if invitation_appeal > companion_acceptance_threshold:
            # 招待受諾 - 仲間が縄張りに向かう
            invited_companion.move_towards(self.territory.center)
            
            # オキシトシン的結束 - 縄張りの社会的メンバーに追加
            if hasattr(self.territory, 'social_members'):
                self.territory.add_member(invited_companion.name, invitation_appeal)
            
            # 相互コミュニティ参加 - 招待される側も自分のコミュニティに招待者を追加
            if hasattr(invited_companion, 'territory') and invited_companion.territory:
                # 相互メンバーシップ
                invited_companion.territory.add_member(self.name, invitation_appeal * 0.8)
                
            # 社会的縄張り結束を更新
            self.update_social_territory_bonding(t, self.territory.center, [invited_companion.name])
            invited_companion.update_social_territory_bonding(t, self.territory.center, [self.name])
            
            # 両者の関係性向上（オキシトシン効果による強化）
            bonding_boost = 0.12  # 通常より強い結束
            self.rel[invited_companion.name] = min(1.0, self.rel.get(invited_companion.name, 0) + bonding_boost)
            invited_companion.rel[self.name] = min(1.0, invited_companion.rel.get(self.name, 0) + bonding_boost)
            
            # 社交的経験の向上（両者とも）
            self.kappa["social"] = min(1.0, self.kappa.get("social", 0) + 0.03)
            invited_companion.kappa["social"] = min(1.0, invited_companion.kappa.get("social", 0) + 0.03)
            
            # グループ招待の連鎖効果 - 招待された人が自分の友人も連れてくる可能性
            if random.random() < 0.7 and len(nearby_npcs) > 1:  # 70%の確率でグループ招待
                secondary_invitees = [npc for npc in nearby_npcs 
                                    if npc != invited_companion 
                                    and invited_companion.rel.get(npc.name, 0) > 0.4]
                
                if secondary_invitees:
                    secondary_companion = random.choice(secondary_invitees)
                    secondary_appeal = invitation_appeal * 0.7  # 間接招待は魅力度低下
                    
                    if secondary_appeal > companion_acceptance_threshold:
                        self.territory.add_member(secondary_companion.name, secondary_appeal)
                        secondary_companion.move_towards(self.territory.center)
                        
                        # 三者間の結束強化
                        bonding_boost_secondary = 0.08
                        self.rel[secondary_companion.name] = min(1.0, self.rel.get(secondary_companion.name, 0) + bonding_boost_secondary)
                        secondary_companion.rel[self.name] = min(1.0, secondary_companion.rel.get(self.name, 0) + bonding_boost_secondary)
                        
                        self.log.append({"t": t, "name": self.name, "action": "group_territory_invitation",
                                       "primary_invitee": invited_companion.name,
                                       "secondary_invitee": secondary_companion.name,
                                       "community_size": self.territory.get_community_size()})
            
            self.log.append({"t": t, "name": self.name, "action": "territory_invitation", 
                           "invitee": invited_companion.name, "territory": self.territory.center,
                           "invitation_appeal": invitation_appeal, "relationship": relationship_bonus,
                           "community_size_after": self.territory.get_community_size()})
            
            return True
        
        return False
    
    def assess_predator_threat(self):
        """捕食者の脅威を評価"""
        nearby_predators = []
        for predator in self.env.predators:
            if predator.alive:
                distance = abs(self.x - predator.x) + abs(self.y - predator.y)
                if distance <= 10:  # 10マス以内の捕食者
                    nearby_predators.append((predator, distance))
        
        if not nearby_predators:
            return 0.0, None
        
        # 最も近い捕食者の脅威度を計算
        closest_predator, min_distance = min(nearby_predators, key=lambda x: x[1])
        threat_level = (11 - min_distance) / 10.0 * closest_predator.aggression
        
        return threat_level, closest_predator
    
    def seek_group_protection(self, t, threat_level):
        """集団保護を求める行動"""
        if threat_level < 0.3:
            return False
        
        # 近くの仲間を探す
        nearby_allies = []
        for npc in self.roster_ref.values():
            if npc != self and npc.alive:
                distance = abs(self.x - npc.x) + abs(self.y - npc.y)
                if distance <= 8:
                    relationship = self.rel.get(npc.name, 0)
                    nearby_allies.append((npc, distance, relationship))
        
        if not nearby_allies:
            return False
        
        # 最も信頼できる仲間に向かう
        target_ally = max(nearby_allies, key=lambda x: x[2] - x[1] * 0.1)[0]
        
        if abs(self.x - target_ally.x) + abs(self.y - target_ally.y) > 2:
            self.move_towards(target_ally.pos())
            self.log.append({
                "t": t, "name": self.name, "action": "seek_group_protection",
                "target_ally": target_ally.name, "threat_level": threat_level
            })
            return True
        
        return False
    
    def calculate_night_danger(self):
        """夜間野宿の危険度を評価"""
        dangers = {
            'weather_exposure': 0.0,
            'predator_risk': 0.0, 
            'isolation_stress': 0.0,
            'total_danger': 0.0
        }
        
        # 1. 天候による危険（雨の場合は危険度上昇）
        if self.env.weather.condition == "rainy":
            dangers['weather_exposure'] = 0.4 + (self.env.weather.intensity * 0.4)
        else:
            dangers['weather_exposure'] = 0.2  # 基本的な夜の寒さと露出リスク
            
        # 2. 捕食者リスク（孤立度に依存）
        nearby_allies = len([npc for npc in self.roster_ref.values() 
                           if npc != self and npc.alive and self.dist_to(npc) < 5])
        if nearby_allies == 0:
            dangers['predator_risk'] = 0.4  # 完全孤立は危険
        elif nearby_allies < 2:
            dangers['predator_risk'] = 0.2  # 少人数も危険
        else:
            dangers['predator_risk'] = 0.05  # 集団なら安全
            
        # 3. 心理的ストレス（疲労度に依存）
        fatigue_stress = min(0.3, self.fatigue / 200.0)
        dangers['isolation_stress'] = fatigue_stress
        
        # 4. 総合危険度
        dangers['total_danger'] = (dangers['weather_exposure'] * 0.4 + 
                                 dangers['predator_risk'] * 0.4 + 
                                 dangers['isolation_stress'] * 0.2)
        
        return dangers
    
    def handle_outdoor_camping(self, t, night_danger_assessment):
        """夜間野宿の処理"""
        self.camping_outdoors = True
        total_danger = night_danger_assessment['total_danger']
        
        # 危険度に応じたダメージ
        if total_danger > 0.7:
            # 高危険：体力と疲労に大きな影響
            self.fatigue += 15 + random.randint(0, 10)
            self.hunger += 8
            self.thirst += 6
            danger_level = "severe"
        elif total_danger > 0.4:
            # 中危険：中程度の影響
            self.fatigue += 8 + random.randint(0, 5)
            self.hunger += 4
            self.thirst += 3
            danger_level = "moderate"
        else:
            # 低危険：軽微な影響
            self.fatigue += 3 + random.randint(0, 2)
            self.hunger += 2
            self.thirst += 1
            danger_level = "mild"
        
        # 危険イベント（低確率）
        event_occurred = False
        if random.random() < total_danger * 0.3:
            if random.random() < 0.6:
                # 悪天候による追加ダメージ
                self.fatigue += 10
                event_occurred = "weather_damage"
            else:
                # 不安による睡眠不足
                self.fatigue += 15
                event_occurred = "sleep_deprivation"
        
        self.log.append({"t": t, "name": self.name, "action": "outdoor_camping", 
                       "danger_level": danger_level, "total_danger": total_danger,
                       "fatigue_penalty": self.fatigue, "event": event_occurred,
                       "weather": self.env.weather.condition})
    
    def record_settlement_experience(self, exploration_pressure, resource_stability, duration):
        """定住体験を記録して整合慣性を蓄積"""
        if not hasattr(self, 'settlement_experiences'):
            self.settlement_experiences = {'resource_stability': [], 'social_stability': [], 'exploration_satisfaction': []}
        
        # リソース安定性の体験
        self.settlement_experiences['resource_stability'].append(resource_stability)
        
        # 社会的安定性の体験（近隣の関係性から算出）
        nearby_relationships = len([r for r in self.rel.values() if r > 0.3])
        social_stability = min(1.0, nearby_relationships / 5.0)  # 最大5人との関係で正規化
        self.settlement_experiences['social_stability'].append(social_stability)
        
        # 探索満足度（長期間探索したほど満足度が高い）
        exploration_satisfaction = min(1.0, duration / 100.0) * (1.0 - exploration_pressure)
        self.settlement_experiences['exploration_satisfaction'].append(exploration_satisfaction)
        
        # 古い体験は除去（最新20個まで保持）
        for key in self.settlement_experiences:
            if len(self.settlement_experiences[key]) > 20:
                self.settlement_experiences[key] = self.settlement_experiences[key][-20:]
    
    def claim_cave_territory(self, cave_pos, t):
        """整合慣性ベースの縄張り主張"""
        if self.territory is not None:
            return False  # 既に縄張りを持っている
        
        # この洞窟への安全感を計算
        safety_feeling = self.calculate_cave_safety_feeling(cave_pos)
        
        # 安全だと感じるレベルに達していない場合は縄張り主張しない
        if safety_feeling < self.territory_claim_threshold:
            return False
        
        # 洞窟の安全性ボーナスに基づいて縄張りの価値を決定
        safety_bonus = self.env.caves[cave_pos]["safety_bonus"]
        territory_radius = 8 + int(safety_feeling * 8)  # 安全感による可変半径
        
        # 他のNPCの縄張りと重複しないかチェック
        for other_npc in self.roster_ref.values():
            if other_npc != self and other_npc.territory is not None:
                distance = abs(cave_pos[0] - other_npc.territory.center[0]) + abs(cave_pos[1] - other_npc.territory.center[1])
                if distance < territory_radius + other_npc.territory.radius - 3:  # 3マスのバッファー
                    # 縄張り競合の判定 - コミュニティ結合も考慮
                    relationship = self.rel.get(other_npc.name, 0)
                    if relationship > 0.6:  # 強い関係性がある場合は結合を優先
                        # コミュニティ結合 - 両者が同じ縄張りを共有
                        other_npc.territory.add_member(self.name, relationship)
                        self.territory = other_npc.territory  # 同じ縄張りを共有
                        self.home_cave = other_npc.home_cave
                        self.log.append({"t": t, "name": self.name, "action": "community_merge",
                                       "partner": other_npc.name, "shared_territory": cave_pos,
                                       "relationship": relationship})
                        return True
                    elif self.territorial_aggression > other_npc.territorial_aggression:
                        # 通常の縄張り奪取
                        other_npc.lose_territory(t, self.name)
                    else:
                        return False  # 主張失敗
        
        # 縄張りを確立（オキシトシン的社会縄張りとして）
        self.territory = Territory(self.name, cave_pos, territory_radius)
        self.territory.social_members = set([self.name])  # 初期メンバーは自分のみ
        self.territory.bonding_strength[self.name] = 1.0  # 自分との結束は最大
        self.home_cave = cave_pos
        self.territory_claim_strength = safety_bonus * self.territorial_aggression
        
        self.log.append({"t": t, "name": self.name, "action": "claim_territory", 
                       "center": cave_pos, "radius": territory_radius, 
                       "strength": self.territory_claim_strength, "safety_bonus": safety_bonus,
                       "safety_feeling_score": safety_feeling})
        return True
    
    def lose_territory(self, t, aggressor_name):
        """縄張りを失う"""
        if self.territory is None:
            return
        
        old_center = self.territory.center
        self.log.append({"t": t, "name": self.name, "action": "lose_territory", 
                       "old_center": old_center, "aggressor": aggressor_name})
        
        self.territory = None
        self.home_cave = None
        self.territory_claim_strength = 0.0
        # 縄張り喪失体験として記録（整合慣性への影響）
        if not hasattr(self, 'territory_loss_experiences'):
            self.territory_loss_experiences = []
        self.territory_loss_experiences.append({'tick': t, 'aggressor': aggressor_name})
    
    def check_territory_intrusion(self, t):
        """縄張り侵入のチェックと対処"""
        if self.territory is None:
            return
        
        # 自分の縄張り内の侵入者を探す
        intruders = []
        for other_npc in self.roster_ref.values():
            if other_npc != self and other_npc.alive:
                distance = abs(other_npc.x - self.territory.center[0]) + abs(other_npc.y - self.territory.center[1])
                if distance <= self.territory.radius:
                    # 同盟関係や強い友人関係は例外
                    relationship = self.rel.get(other_npc.name, 0)
                    if relationship < 0.6:  # 友人関係が薄い場合は侵入者扱い
                        intruders.append(other_npc)
        
        # 侵入者への対処
        for intruder in intruders:
            if random.random() < self.territorial_aggression * 0.8:
                # 縄張り主張で関係悪化
                self.rel[intruder.name] = max(-0.5, self.rel.get(intruder.name, 0) - 0.2)
                intruder.rel[self.name] = max(-0.5, intruder.rel.get(self.name, 0) - 0.15)
                
                self.log.append({"t": t, "name": self.name, "action": "territorial_warning", 
                               "intruder": intruder.name, "territory_center": self.territory.center})
    
    def consider_exploration_leap(self, t, exploration_pressure):
        """探索モードへの跳躍的入り判定"""
        # 意味圧が闾値を超えた時の跳躍条件
        pressure_threshold = 0.8 + (1.0 - self.curiosity) * 0.3  # 好奇心が低いほど高い闾値
        
        # 整合慣性と意味圧による跳躍判定
        exploration_experience = self.kappa.get("exploration", 0.1)
        leap_probability = min(0.8, exploration_pressure / 2.0) * (0.5 + exploration_experience)
        
        if exploration_pressure > pressure_threshold and random.random() < leap_probability:
            # 探索モードへの跳躍的変化
            self.exploration_mode = True
            self.exploration_mode_start_tick = t
            self.exploration_intensity = 1.0 + exploration_pressure * 0.5  # 圧力に応じた強度
            self.mode_stability_counter = 0
            
            self.log.append({"t": t, "name": self.name, "action": "exploration_mode_leap", 
                           "pressure": exploration_pressure, "intensity": self.exploration_intensity})
            return True
            
        return False

    def consider_scout_reversion(self, t):
        """スカウトから元の役割への復帰判定"""
        exploration_pressure = self.calculate_exploration_pressure()
        
        # リソース安定性の評価
        resource_stability = self.evaluate_resource_stability()
        
        # 探索圧力が低く、リソースが安定している場合
        if exploration_pressure < 0.15 and resource_stability > 0.7:
            self.resource_stability_counter += 1
        else:
            self.resource_stability_counter = max(0, self.resource_stability_counter - 1)
        
        # 十分な期間（20tick）リソースが安定していた場合に復帰を検討（条件を緩和）
        scout_duration = t - self.scout_start_tick
        reversion_threshold = 20 + (self.curiosity * 15)  # 好奇心が高いほど長くスカウトを続ける（緩和）
        
        # デバッグ用：復帰検討の詳細をログ出力

        
        if (self.resource_stability_counter >= 20 and 
            scout_duration > reversion_threshold and
            exploration_pressure < 0.2):  # 探索圧力の閾値を緩和
            
            # 元の役割に復帰
            old_role = self.role
            self.role = self.original_role
            self.discovery_reward_multiplier = 1.0  # 通常の発見報酬に戻る
            self.resource_stability_counter = 0
            
            # 復帰時に探索経験を少し減衰（忘却効果）
            self.kappa["exploration"] = max(0.05, self.kappa.get("exploration", 0.1) * 0.8)
            
            self.log.append({"t": t, "name": self.name, "action": "scout_reversion", 
                           "from_role": old_role, "to_role": self.role, 
                           "duration": scout_duration, "stability": resource_stability})
            return True
        
        return False
    
    def evaluate_resource_stability(self):
        """現在のリソース安定性を評価"""
        stability_score = 0.0
        
        # 基本生理ニーズの充足度
        hunger_stability = max(0, (70 - self.hunger) / 70)  # 空腹度が低いほど安定
        thirst_stability = max(0, (70 - self.thirst) / 70)  # 渇きが少ないほど安定
        fatigue_stability = max(0, (70 - self.fatigue) / 70)  # 疲労が少ないほど安定
        
        basic_needs = (hunger_stability + thirst_stability + fatigue_stability) / 3
        stability_score += basic_needs * 0.6
        
        # 知識の豊富さ（発見済みリソースの割合）
        total_resources = (len(self.env.caves) + len(self.env.water_sources) + 
                          len(self.env.berries) + len(self.env.huntzones))
        known_resources = (len(self.knowledge_caves) + len(self.knowledge_water) + 
                          len(self.knowledge_berries) + len(self.knowledge_huntzones))
        
        if total_resources > 0:
            knowledge_ratio = known_resources / total_resources
            stability_score += knowledge_ratio * 0.4
        
        return min(1.0, stability_score)

    def consider_retirement(self, t):
        """引退を検討する"""
        if self.retired or self.age < 45:
            return False
            
        # 引退条件の計算
        age_pressure = max(0, (self.age - 45) / 20.0)  # 45歳から引退圧力
        fatigue_pressure = max(0, (self.fatigue - 70) / 30.0)  # 疲労蓄積
        experience_readiness = min(1.0, self.experience_points / 15.0)  # 十分な経験
        
        # 引退準備度の更新
        self.retirement_readiness += (age_pressure * 0.02 + 
                                    fatigue_pressure * 0.01 + 
                                    experience_readiness * 0.01)
        
        # 引退判定（確率的）
        retirement_threshold = 0.3 + (0.1 if self.role == "scout" else 0.0)
        if (self.retirement_readiness > retirement_threshold and 
            random.random() < 0.15):  # 15%の確率で引退
            return self.execute_retirement(t)
        
        return False
    
    def execute_retirement(self, t):
        """引退を実行し、知識を伝承する"""
        self.retired = True
        self.role = "elder"  # 長老として位置づけ
        
        # 指導対象を選定（若い同じグループのNPC）
        potential_mentees = []
        for ally in self.nearby_allies(radius=15):
            if not ally.retired and ally.age < self.age - 10:
                potential_mentees.append(ally)
        
        if potential_mentees:
            self.mentor_target = random.choice(potential_mentees)
            self.transfer_knowledge(t, self.mentor_target)
        
        self.log.append({"t": t, "name": self.name, "action": "retirement", 
                        "age": self.age, "experience": self.experience_points,
                        "mentor_target": self.mentor_target.name if self.mentor_target else None})
        return True
    
    def transfer_knowledge(self, t, mentee):
        """後継者に知識を伝承する"""
        if not mentee or self.retired != True:
            return
        
        # 知識の伝承
        knowledge_transfer_bonus = 0.5  # 伝承ボーナス
        
        # リソース知識の伝承
        for cave in self.knowledge_caves:
            if cave not in mentee.knowledge_caves:
                mentee.knowledge_caves.add(cave)
        for water in self.knowledge_water:
            if water not in mentee.knowledge_water:
                mentee.knowledge_water.add(water)
        for berry in self.knowledge_berries:
            if berry not in mentee.knowledge_berries:
                mentee.knowledge_berries.add(berry)
        for hunt in self.knowledge_huntzones:
            if hunt not in mentee.knowledge_huntzones:
                mentee.knowledge_huntzones.add(hunt)
        
        # 経験値の一部伝承
        transferred_exp = self.experience_points * 0.3
        mentee.experience_points += transferred_exp
        mentee.kappa["exploration"] = min(1.0, mentee.kappa["exploration"] + 0.1)
        mentee.kappa["social"] = min(1.0, mentee.kappa["social"] + 0.05)
        
        # 関係性の向上
        mentee.rel[self.name] = min(1.0, mentee.rel.get(self.name, 0) + 0.8)
        self.rel[mentee.name] = min(1.0, self.rel.get(mentee.name, 0) + 0.6)
        
        # ログ記録
        self.knowledge_legacy.append({
            "t": t, "mentee": mentee.name, "transferred_exp": transferred_exp,
            "caves": len(self.knowledge_caves), "berries": len(self.knowledge_berries)
        })
        
        self.log.append({"t": t, "name": self.name, "action": "knowledge_transfer", 
                        "mentee": mentee.name, "transferred_exp": transferred_exp})

    def elder_activities(self, t):
        """引退者の活動：指導と休息"""
        # 疲労回復が早い
        self.fatigue = max(0, self.fatigue - 2.0)
        
        # 継続的な指導活動
        if self.mentor_target and not self.mentor_target.retired:
            # 定期的に追加指導を実施
            if t % 30 == 0 and random.random() < 0.4:
                self.provide_ongoing_mentorship(t, self.mentor_target)
        
        # 新しい指導対象を探す（前の対象が引退した場合）
        elif t % 40 == 0:  # 定期的に新しい弟子を探す
            potential_mentees = []
            for ally in self.nearby_allies(radius=20):
                if not ally.retired and ally.age < self.age - 10:
                    potential_mentees.append(ally)
            
            if potential_mentees:
                self.mentor_target = random.choice(potential_mentees)
                self.log.append({"t": t, "name": self.name, "action": "new_mentee_selected", 
                               "mentee": self.mentor_target.name})
    
    def provide_ongoing_mentorship(self, t, mentee):
        """継続的な指導を提供"""
        # 小さな経験値ボーナス
        mentee.experience_points += 0.2
        mentee.kappa["social"] = min(1.0, mentee.kappa["social"] + 0.02)
        
        # 関係性の維持・強化
        mentee.rel[self.name] = min(1.0, mentee.rel.get(self.name, 0) + 0.1)
        
        self.log.append({"t": t, "name": self.name, "action": "ongoing_mentorship", 
                        "mentee": mentee.name})

    def share_discovery_with_pleasure(self, t, node, resource_type):
        shared_count = 0
        total_approval = 0.0
        for ally in self.nearby_allies(radius=8):
            relationship = self.rel.get(ally.name, 0)
            sharing_probability = 0.3 + 0.7 * relationship
            if random.random() > sharing_probability: continue
            
            # リソースタイプに応じて適切な知識セットを選択
            if resource_type == "cave":
                target_knowledge = ally.knowledge_caves
            elif resource_type == "water":
                target_knowledge = ally.knowledge_water
            elif resource_type == "berry_patch":
                target_knowledge = ally.knowledge_berries
            elif resource_type == "hunting_ground":
                target_knowledge = ally.knowledge_huntzones
            else:
                continue
                
            if node not in target_knowledge:
                target_knowledge.add(node)
                # 新しいリソース情報は特に価値が高いので関係性ボーナスを増加
                relationship_bonus = 0.4 if resource_type in ["berry_patch", "hunting_ground"] else 0.3
                ally.rel[self.name] = min(1.0, ally.rel.get(self.name, 0) + relationship_bonus)
                self.rel[ally.name] = min(1.0, self.rel.get(ally.name, 0) + 0.1)
                
                total_approval += ally.rel[self.name]
                shared_count += 1
                self.log.append({"t": t, "name": self.name, "action": f"share_{resource_type}_info", "target": ally.name})
        
        if shared_count > 0:
            base_pleasure = 0.3 * shared_count
            approval_multiplier = 1.0 + (total_approval / shared_count) * 0.5
            cooperation_bonus = 1.2 if shared_count >= 2 else 1.0
            total_pleasure = base_pleasure * approval_multiplier * cooperation_bonus
            self.kappa["social"] = min(1.0, self.kappa.get("social", 0.1) + 0.05 * shared_count)
            
            # 引退システム：共有経験の蓄積
            self.experience_points += total_pleasure * 0.2
            self.lifetime_shares += shared_count
            
            self.log.append({"t": t, "name": self.name, "action": "approval_pleasure", "pleasure": total_pleasure})

    def exploration_mode_action(self, t):
        """探索モード中の積極的な探索行動"""
        exploration_pressure = self.calculate_exploration_pressure()
        if exploration_pressure < 0.2: return False  # 基本閾値
        
        # 探索モードの強度に応じた行動
        action_intensity = "intensive" if self.exploration_intensity > 1.3 else "moderate"
        self.log.append({"t": t, "name": self.name, "action": f"exploration_mode_active", "intensity": action_intensity})
        
        # 強度に応じた移動範囲
        movement_range = 2 if self.exploration_intensity > 1.3 else 1
        dx = random.choice(list(range(-movement_range, movement_range + 1)))
        dy = random.choice(list(range(-movement_range, movement_range + 1)))
        
        # 移動実行
        new_x = self.x + dx
        new_y = self.y + dy
        self.x = max(0, min(self.env.size - 1, new_x))
        self.y = max(0, min(self.env.size - 1, new_y))

        # 探索モード中は発見範囲が拡大
        detection_range = 3 if self.exploration_intensity > 1.3 else 2
        
        # 全てのリソースタイプで新しい発見をチェック
        resource_types = [
            ("cave", self.env.caves, self.knowledge_caves),
            ("water", self.env.water_sources, self.knowledge_water),
            ("berry_patch", self.env.berries, self.knowledge_berries),
            ("hunting_ground", self.env.huntzones, self.knowledge_huntzones)
        ]
        
        for res_type, res_dict, knowledge in resource_types:
            nearest = self.env.nearest_nodes(self.pos(), res_dict, k=1)
            if nearest:
                distance = self.dist_to_pos(nearest[0])
                already_known = nearest[0] in knowledge
                
                if distance <= detection_range and not already_known:
                    knowledge.add(nearest[0])
                    # 探索モード中は発見報酬が増加
                    self.experience_discovery_pleasure(t, res_type, nearest[0])
                    
                    # 洞窟発見時の特別ボーナス
                    if res_type == "cave":
                        safety_bonus = self.env.caves[nearest[0]]["safety_bonus"]
                        # 安全性の高い洞窟ほど大きな発見喜び
                        extra_pleasure = safety_bonus * 5
                        self.kappa["exploration"] = min(1.0, self.kappa.get("exploration", 0.1) + extra_pleasure * 0.1)
                        self.log.append({"t": t, "name": self.name, "action": "discover_valuable_cave", 
                                       "location": nearest[0], "safety_bonus": safety_bonus, 
                                       "extra_pleasure": extra_pleasure})
                    
                    self.share_discovery_with_pleasure(t, nearest[0], res_type)
                    self.log.append({"t": t, "name": self.name, "action": f"discover_{res_type}_exploration_mode", 
                                   "location": nearest[0], "intensity": self.exploration_intensity})
        return True
    
    # def leader_group_action(self, t):
    #     """リーダーの集団指揮行動"""
    #     if not self.leadership_mode or len(self.followers) == 0:
    #         return False
    #     
    #     # フォロワーの現在状態をチェック
    #     active_followers = []
    #     for follower_name in list(self.followers):
    #         follower_npc = self.roster_ref.get(follower_name)
    #         if follower_npc and follower_npc.alive and follower_npc.leader_target == self:
    #             active_followers.append(follower_npc)
    #         else:
    #             self.followers.discard(follower_name)  # 非アクティブなフォロワーを削除
    #     
    #     if len(active_followers) == 0:
    #         return False
    #     
    #     # 集団探索の指示（探索圧力が高い時）
    #     if self.calculate_exploration_pressure() > 1.0:
    #         target_location = None
    #         
    #         # 未知のリソースを探して探索目標を設定
    #         unknown_resources = []
    #         for pos in self.env.berries.keys():
    #             if pos not in self.knowledge_berries:
    #                 unknown_resources.append(pos)
    #         
    #         if unknown_resources:
    #             target_location = random.choice(unknown_resources)
    #             
    #             # フォロワーに探索指示を送る
    #             for follower in active_followers:
    #                 if random.random() < 0.7:  # 70%の確率で指示に従う
    #                     follower.move_towards(target_location)
    #             
    #             self.log.append({"t": t, "name": self.name, "action": "group_exploration_command", 
    #                            "followers": len(active_followers), "target": target_location})
    #             return True
    #     
    #     # 知識と情報の集団共有（定期的）
    #     if t % 10 == 0:  # 10tick毎
    #         knowledge_shared = 0
    #         for follower in active_followers:
    #             # リーダーの知識をフォロワーに共有
    #             for cave in self.knowledge_caves:
    #                 if cave not in follower.knowledge_caves:
    #                     follower.knowledge_caves.add(cave)
    #                     knowledge_shared += 1
    #                     
    #             for berry in self.knowledge_berries:
    #                 if berry not in follower.knowledge_berries:
    #                     follower.knowledge_berries.add(berry)
    #                     knowledge_shared += 1
    #             
    #             # 相互関係の強化
    #             follower.rel[self.name] = min(1.0, follower.rel.get(self.name, 0) + 0.05)
    #             self.rel[follower.name] = min(1.0, self.rel.get(follower.name, 0) + 0.03)
    #         
    #         if knowledge_shared > 0:
    #             self.log.append({"t": t, "name": self.name, "action": "leadership_knowledge_sharing", 
    #                            "knowledge_shared": knowledge_shared, "followers": len(active_followers)})
    #             return True
    #     
    #     return False

    def step(self, t):
        if not self.alive: return

        self.hunger += 0.5  # 空腹度の増加を大幅緩和
        self.thirst += 0.8  # 渇きの増加を大幅緩和
        self.fatigue += 0.6  # 疲労の増加を大幅緩和
        # 死亡判定を大幅緩和（縄張りシステムテスト用）
        if self.hunger >= 200 or self.thirst >= 180:
            # 死因の記録
            death_cause = "starvation" if self.hunger >= 200 else "dehydration"
            exploration_duration = getattr(self, 'exploration_start_tick', 0)
            exploration_mode_duration = t - exploration_duration if hasattr(self, 'exploration_start_tick') else 0
            
            self.log.append({"t": t, "name": self.name, "action": "death", 
                           "cause": death_cause, "hunger": self.hunger, "thirst": self.thirst,
                           "fatigue": self.fatigue, "exploration_mode": self.exploration_mode,
                           "exploration_duration": exploration_mode_duration,
                           "territories_claimed": 1 if self.territory else 0})
            self.alive = False
            return

        # 引退システム：年齢更新と引退判定（無効化中）
        # if t % 50 == 0:  # 50tick毎に年齢更新
        #     self.age += 1
            
        # SSD理論：意味圧に応じた探索モードの跳躍的変化
        self.consider_exploration_mode_shift(t)
        
        # 縄張り侵入のチェック（5tick毎）
        if t % 5 == 0:
            self.check_territory_intrusion(t)

        # リーダーの集団指揮行動（無効化中）
        # if self.leadership_mode:
        #     if self.leader_group_action(t): return
        
        # 疲労による強制休憩（探索モードよりも優先）
        if self.fatigue > 60:  # 疲労度60%超えで強制休憩（条件緩和）
            known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
            if known_caves:
                cave_nodes = self.env.nearest_nodes(self.pos(), known_caves, k=1)
                if cave_nodes:
                    target = cave_nodes[0]
                    if self.pos() == target:
                        # 疲労回復のための休憩
                        safety_bonus = self.env.caves[target]["safety_bonus"]
                        recovery = 15 + (safety_bonus * 10)  # 大きな回復量
                        self.fatigue = max(0, self.fatigue - recovery)
                        
                        # 休憩体験の蓄積
                        if target not in self.cave_safety_experiences:
                            self.cave_safety_experiences[target] = {'positive_rest': 0, 'weather_shelter': 0, 'social_bonus': 0}
                        self.cave_safety_experiences[target]['positive_rest'] += 1
                        
                        # 疲労時の社交活動（高確率で発生）
                        nearby_npcs = [npc for npc in self.roster_ref.values() 
                                     if npc != self and npc.alive and self.dist_to(npc) < 3]
                        if nearby_npcs and random.random() < 0.8:  # 80%の確率で社交
                            social_partner = random.choice(nearby_npcs)
                            if self.knowledge_caves:
                                shared_cave = random.choice(list(self.knowledge_caves))
                                social_partner.knowledge_caves.add(shared_cave)
                            self.rel[social_partner.name] = min(1.0, self.rel.get(social_partner.name, 0) + 0.1)
                            social_partner.rel[self.name] = min(1.0, social_partner.rel.get(self.name, 0) + 0.1)
                            self.cave_safety_experiences[target]['social_bonus'] += 1
                        
                        # 縄張り主張判定
                        if self.territory is None:
                            safety_feeling = self.calculate_cave_safety_feeling(target)
                            if safety_feeling > 0.15:
                                self.log.append({"t": t, "name": self.name, "action": "fatigue_rest_safety_check", 
                                               "location": target, "safety_feeling": safety_feeling, 
                                               "threshold": self.territory_claim_threshold, 
                                               "close_to_claiming": safety_feeling >= self.territory_claim_threshold * 0.8})
                            if safety_feeling >= self.territory_claim_threshold:
                                self.claim_cave_territory(target, t)
                        
                        self.log.append({"t": t, "name": self.name, "action": "fatigue_rest", 
                                       "location": target, "recovery": recovery, 
                                       "safety_feeling": self.calculate_cave_safety_feeling(target),
                                       "social_interactions": len(nearby_npcs)})
                        return
                    else:
                        self.move_towards(target)
                        return
        
        # 捕食者脅威の優先評価
        threat_level, predator = self.assess_predator_threat()
        if threat_level > 0.2:  # 捕食者脅威がある場合は集団保護行動
            if self.seek_group_protection(t, threat_level):
                return
        
        # 命の危機を優先的に処理（探索よりも生存を優先）
        life_crisis = self.calculate_life_crisis_pressure()
        
        if life_crisis > 1.0:  # 命の危機がある場合は緊急生存行動
            if self.emergency_survival_action(t, life_crisis): 
                return
        
        # 探索モード中の積極的行動または高い探索圧力時（命の危機がない場合のみ）
        if (self.exploration_mode or self.calculate_exploration_pressure() > 1.5) and life_crisis <= 1.0:
            if self.exploration_mode_action(t): return
        
        # 基本的な生存行動
        # 悪天候時の洞窟避難（雨の強度が高い場合）
        if self.env.weather.condition == "rainy" and self.env.weather.intensity > 0.6:
            known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
            if known_caves:
                cave_nodes = self.env.nearest_nodes(self.pos(), known_caves, k=1)
                if cave_nodes:
                    target = cave_nodes[0]
                    if self.pos() == target:
                        # 洞窟で雨宿り：天候待ち + 軽い疲労回復
                        safety_bonus = self.env.caves[target]["safety_bonus"]
                        weather_recovery = 5 + (safety_bonus * 3)  # 5-8の回復
                        self.fatigue = max(0, self.fatigue - weather_recovery)
                        
                        # 天候避難体験の蓄積
                        if target not in self.cave_safety_experiences:
                            self.cave_safety_experiences[target] = {'positive_rest': 0, 'weather_shelter': 0, 'social_bonus': 0}
                        self.cave_safety_experiences[target]['weather_shelter'] += 1
                        
                        # 天候避難時の社交活動（雨宿り仲間との交流）
                        nearby_npcs = [npc for npc in self.roster_ref.values() 
                                     if npc != self and npc.alive and self.dist_to(npc) < 3]
                        if nearby_npcs and random.random() < 0.7:  # 70%の確率で雨宿り社交
                            social_partner = random.choice(nearby_npcs)
                            # 雨宿り中の洞窟情報共有
                            if self.knowledge_caves:
                                shared_cave = random.choice(list(self.knowledge_caves))
                                social_partner.knowledge_caves.add(shared_cave)
                            # 関係性の向上
                            self.rel[social_partner.name] = min(1.0, self.rel.get(social_partner.name, 0) + 0.06)
                            social_partner.rel[self.name] = min(1.0, social_partner.rel.get(self.name, 0) + 0.06)
                            # 雨宿り社交ボーナス体験を記録
                            self.cave_safety_experiences[target]['social_bonus'] += 1
                        
                        self.log.append({"t": t, "name": self.name, "action": "weather_shelter", 
                                       "location": target, "recovery": weather_recovery,
                                       "weather_intensity": self.env.weather.intensity,
                                       "social_interactions": len(nearby_npcs)})
                    else:
                        self.move_towards(target)
                    return
                    
        # 夜間野宿の危険性評価と洞窟避難判定
        if self.env.day_night.is_night():
            night_danger_assessment = self.calculate_night_danger()
            
            # 危険度が閾値を超えるか、既に野宿中の場合は洞窟を探す
            should_seek_shelter = (night_danger_assessment['total_danger'] > 0.25 or 
                                 getattr(self, 'camping_outdoors', False))
            
            if should_seek_shelter:
                known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
                if known_caves:
                    # ホーム洞窟があればそこに、なければ最も近い洞窟に
                    if self.home_cave and self.home_cave in known_caves:
                        target = self.home_cave
                    else:
                        cave_nodes = self.env.nearest_nodes(self.pos(), known_caves, k=1)
                        if cave_nodes:
                            target = cave_nodes[0]
                        else:
                            target = None
                    
                    if target:
                        if self.pos() == target:
                            # 夜間の洞窟での休憩：危険回避による安全確保
                            safety_bonus = self.env.caves[target]["safety_bonus"]
                            night_recovery = 8 + (safety_bonus * 6)  # 8-14の回復
                            
                            # ホーム洞窟での休憩ならボーナス
                            if self.home_cave == target:
                                night_recovery += 5
                            
                            self.fatigue = max(0, self.fatigue - night_recovery)
                            
                            # 夜間休憩体験の蓄積
                            if target not in self.cave_safety_experiences:
                                self.cave_safety_experiences[target] = {'positive_rest': 0, 'weather_shelter': 0, 'social_bonus': 0}
                            self.cave_safety_experiences[target]['positive_rest'] += 1
                            
                            # 夜間の社交活動（洞窟での他NPCとの遭遇）
                            nearby_npcs = [npc for npc in self.roster_ref.values() 
                                         if npc != self and npc.alive and self.dist_to(npc) < 3]
                            if nearby_npcs and random.random() < 0.6:  # 60%の確率で社交（社会的安全感重視）
                                social_partner = random.choice(nearby_npcs)
                                # 簡単な知識共有：洞窟情報を共有
                                if self.knowledge_caves:
                                    shared_cave = random.choice(list(self.knowledge_caves))
                                    social_partner.knowledge_caves.add(shared_cave)
                                # 関係性の向上
                                self.rel[social_partner.name] = min(1.0, self.rel.get(social_partner.name, 0) + 0.05)
                                social_partner.rel[self.name] = min(1.0, social_partner.rel.get(self.name, 0) + 0.05)
                                # 社交ボーナス体験を記録
                                self.cave_safety_experiences[target]['social_bonus'] += 1
                            
                            # 安全感ベースの縄張り主張判定（ここは安全だ、と感じたら縄張りに）
                            if self.territory is None:
                                safety_feeling = self.calculate_cave_safety_feeling(target)
                                # デバッグ用ログ出力
                                if safety_feeling > 0.15:  # 一定以上の安全感がある場合にログ出力
                                    self.log.append({"t": t, "name": self.name, "action": "safety_feeling_check", 
                                                   "location": target, "safety_feeling": safety_feeling, 
                                                   "threshold": self.territory_claim_threshold, 
                                                   "close_to_claiming": safety_feeling >= self.territory_claim_threshold * 0.8})
                                if safety_feeling >= self.territory_claim_threshold:
                                    self.claim_cave_territory(target, t)
                            
                            self.log.append({"t": t, "name": self.name, "action": "night_shelter", 
                                           "location": target, "recovery": night_recovery, 
                                           "safety_bonus": safety_bonus, "social_interactions": len(nearby_npcs),
                                           "danger_avoided": night_danger_assessment['total_danger'],
                                           "safety_feeling": self.calculate_cave_safety_feeling(target)})
                            # 安全な夜を過ごした状態
                            self.camping_outdoors = False
                        else:
                            self.move_towards(target)
                            self.log.append({"t": t, "name": self.name, "action": "seeking_night_shelter", 
                                           "target": target, "danger_level": night_danger_assessment['total_danger']})
                        return
                    else:
                        # 洞窟が見つからない場合は仕方なく野宿
                        self.handle_outdoor_camping(t, night_danger_assessment)
                        return
                else:
                    # 洞窟の知識がない場合も仕方なく野宿  
                    self.handle_outdoor_camping(t, night_danger_assessment)
                    return
            else:
                # 危険性が低い、または既に洞窟にいる場合は通常の行動を継続
                pass
                    
        # 高疲労時の洞窟での休憩（闾値を下げて促進）
        if self.fatigue > 60:
            known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
            if known_caves:
                cave_nodes = self.env.nearest_nodes(self.pos(), known_caves, k=1)
                if cave_nodes:
                    target = cave_nodes[0]
                    if self.pos() == target:
                        # 洞窟で休憩：安全性ボーナスに応じた回復
                        safety_bonus = self.env.caves[target]["safety_bonus"]
                        fatigue_recovery = 15 + (safety_bonus * 10)  # 15-25の回復
                        
                        # 自分のホーム洞窟ならさらに回復ボーナス
                        if self.home_cave == target:
                            fatigue_recovery += 5  # ホームボーナス
                        
                        self.fatigue = max(0, self.fatigue - fatigue_recovery)
                        
                        # 安全性体験の蓄積（SSD整合慣性）
                        if target not in self.cave_safety_experiences:
                            self.cave_safety_experiences[target] = {'positive_rest': 0, 'weather_shelter': 0, 'social_bonus': 0}
                        
                        self.cave_safety_experiences[target]['positive_rest'] += 1
                        
                        # 洞窟での社交活動：近くにいる他のNPCと情報共有
                        nearby_npcs = [npc for npc in self.roster_ref.values() 
                                     if npc != self and npc.alive and self.dist_to(npc) < 3]
                        if nearby_npcs and random.random() < 0.4:  # 40%の確率で社交
                            social_partner = random.choice(nearby_npcs)
                            # 簡単な知識共有：洞窟情報を共有
                            if self.knowledge_caves:
                                shared_cave = random.choice(list(self.knowledge_caves))
                                social_partner.knowledge_caves.add(shared_cave)
                            # 関係性の向上
                            self.rel[social_partner.name] = min(1.0, self.rel.get(social_partner.name, 0) + 0.1)
                            social_partner.rel[self.name] = min(1.0, social_partner.rel.get(self.name, 0) + 0.1)
                            # 社交ボーナス体験を記録
                            self.cave_safety_experiences[target]['social_bonus'] += 1
                        
                        # 安全感ベースの縄張り主張判定（休んで安全だと感じたら縄張りに）
                        if self.territory is None:
                            safety_feeling = self.calculate_cave_safety_feeling(target)
                            # デバッグ用ログ出力
                            if safety_feeling > 0.15:  # 一定以上の安全感がある場合にログ出力
                                self.log.append({"t": t, "name": self.name, "action": "daytime_safety_check", 
                                               "location": target, "safety_feeling": safety_feeling, 
                                               "threshold": self.territory_claim_threshold, 
                                               "close_to_claiming": safety_feeling >= self.territory_claim_threshold * 0.8})
                            if safety_feeling >= self.territory_claim_threshold:
                                self.claim_cave_territory(target, t)
                        
                        self.log.append({"t": t, "name": self.name, "action": "rest_in_cave", 
                                       "location": target, "recovery": fatigue_recovery, 
                                       "safety_bonus": safety_bonus, "social_interactions": len(nearby_npcs),
                                       "safety_feeling": self.calculate_cave_safety_feeling(target)})
                    else:
                        self.move_towards(target)
                    return
                    
        # 水分補給（命の危機に応じて闾値調整）
        water_threshold = 90 - (life_crisis * 30)  # 危機時は早めに水分補給
        if self.thirst > max(60, water_threshold):  # 最低60で水分補給
            known_water = self.env.nearest_nodes(self.pos(), {k:v for k,v in self.env.water_sources.items() if k in self.knowledge_water}, k=1)
            if known_water:
                target = known_water[0]
                if self.pos() == target:
                    self.thirst = 0
                    self.fatigue = max(0, self.fatigue - 5)  # 水分補給時に休憩効果も付与
                    if life_crisis > 1.0:
                        self.log.append({"t": t, "name": self.name, "action": "crisis_hydration", 
                                       "life_crisis": life_crisis, "threshold_used": water_threshold})
                else:
                    self.move_towards(target)
                return
        
        if self.hunger > 100:  # 食事の闾値を緩和
            # 既知のベリー採取場所を優先的に探す
            known_berries = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
            if known_berries:
                nodes = self.env.nearest_nodes(self.pos(), known_berries, k=1)
            else:
                # 既知の場所がない場合は近くを探索
                nodes = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
                # 新しい場所を発見した場合は知識に追加
                if nodes and nodes[0] not in self.knowledge_berries:
                    self.knowledge_berries.add(nodes[0])
                    self.log.append({"t": t, "name": self.name, "action": "discover_berry_patch", "location": nodes[0]})
                    
            if nodes:
                self.move_towards(nodes[0])
                success, food, _, _ = self.env.forage(self.pos(), nodes[0])
                if success:
                    self.hunger -= food
                    self.fatigue = max(0, self.fatigue - 2)  # 成功した採集で少し疲労回復
                return

        # 社会的磁力：縄張りを持っている場合、仲間を招待することがある
        if self.territory is not None and random.random() < 0.5:  # 50%の確率で招待行動（大幅増加）
            if self.try_invite_companions_to_territory(t):
                return
        
        # ランダム移動
        self.move_towards((self.x + random.choice([-1,1]), self.y + random.choice([-1,1])))

# =========================
# NPC Presets (16人用拡張)
# =========================
FORAGER = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
ADVENTURER = {"risk_tolerance": 0.8, "curiosity": 0.8, "avoidance": 0.1, "stamina": 0.8, "empathy": 0.4}
DIPLOMAT = {"risk_tolerance": 0.3, "curiosity": 0.6, "avoidance": 0.4, "stamina": 0.5, "empathy": 0.9}
LONER = {"risk_tolerance": 0.4, "curiosity": 0.7, "avoidance": 0.9, "stamina": 0.7, "empathy": 0.2}
LEADER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.3, "stamina": 0.8, "empathy": 0.7}
# 16人構成用の追加性格タイプ
SCHOLAR = {"risk_tolerance": 0.2, "curiosity": 0.9, "avoidance": 0.7, "stamina": 0.4, "empathy": 0.6}
WARRIOR = {"risk_tolerance": 0.9, "curiosity": 0.3, "avoidance": 0.1, "stamina": 0.9, "empathy": 0.3}
HEALER = {"risk_tolerance": 0.2, "curiosity": 0.5, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.9}
NOMAD = {"risk_tolerance": 0.7, "curiosity": 0.8, "avoidance": 0.2, "stamina": 0.9, "empathy": 0.4}

# =========================
# Main Execution (16人版)
# =========================
def run_sim(TICKS=500):  # デバッグ用に短期シミュレーション
    # 16人の生存を確実にした超豊富なリソース環境（スカウト復帰システム実証用）
    env = EnvForageBuff(size=90, n_berry=120, n_hunt=60, n_water=40, n_caves=25)
    roster = {}
    
    # NPCの人数を16人に大幅増加（4つのグループに分散配置）
    npc_configs = [
        # 北西グループ（探索・冒険重視）
        ("Pioneer_Alpha", PIONEER, (20, 20)),
        ("Adventurer_Beta", ADVENTURER, (21, 19)),
        ("Tracker_Gamma", TRACKER, (19, 21)),
        ("Scholar_Delta", SCHOLAR, (18, 18)),
        
        # 北東グループ（戦闘・守備重視）
        ("Warrior_Echo", WARRIOR, (60, 20)),
        ("Guardian_Foxtrot", GUARDIAN, (61, 19)),
        ("Loner_Golf", LONER, (59, 21)),
        ("Nomad_Hotel", NOMAD, (58, 18)),
        
        # 南西グループ（協力・治療重視）
        ("Healer_India", HEALER, (20, 60)),
        ("Diplomat_Juliet", DIPLOMAT, (21, 59)),
        ("Forager_Kilo", FORAGER, (19, 61)),
        ("Leader_Lima", LEADER, (18, 58)),
        
        # 南東グループ（バランス型）
        ("Guardian_Mike", GUARDIAN, (60, 60)),
        ("Tracker_November", TRACKER, (61, 59)),
        ("Adventurer_Oscar", ADVENTURER, (59, 61)),
        ("Pioneer_Papa", PIONEER, (58, 58)),
    ]
    
    # NPCを生成
    npcs = [NPCPriority(name, preset, env, roster, pos) for name, preset, pos in npc_configs]
    for npc in npcs:
        roster[npc.name] = npc
    
    # 全NPCが生成された後に初期関係性を設定
    for npc in npcs:
        for other in npcs:
            if npc.name != other.name:
                initial_distance = npc.dist_to(other)
                if initial_distance < 5:
                    npc.rel[other.name] = 0.3

    logs = []
    weather_log = []
    for t in range(TICKS):
        current_tick_logs = []
        for n in npcs:
            if n.alive:
                n.step(t)
                if n.log:
                    current_tick_logs.extend(n.log)
                    n.log = []
        
        if current_tick_logs:
            logs.extend(current_tick_logs)
            
        env.step()
        weather_log.append({"t": t, "condition": env.weather.condition, "intensity": env.weather.intensity})

        if not any(n.alive for n in npcs):
            print(f"--- {t} tick: 全員が力尽きた ---")
            break

    return npcs, pd.DataFrame(logs), pd.DataFrame(weather_log)

if __name__ == "__main__":
    final_npcs, df_logs, df_weather = run_sim(TICKS=500)  # デバッグ用短期実行
    print("\n--- 16-Person Village Simulation Finished ---")
    print(f"Survivors: {sum(1 for n in final_npcs if n.alive)} / {len(final_npcs)}")
    
    # デバッグ：探索死と生存分析
    if not df_logs.empty:
        print("\n--- Exploration Death Analysis ---")
        
        # 死亡分析
        deaths = df_logs[df_logs['action'] == 'death']
        if not deaths.empty:
            print(f"Total deaths: {len(deaths)}")
            starvation_deaths = deaths[deaths['cause'] == 'starvation']
            dehydration_deaths = deaths[deaths['cause'] == 'dehydration']
            print(f"Starvation deaths: {len(starvation_deaths)}")
            print(f"Dehydration deaths: {len(dehydration_deaths)}")
            
            exploration_deaths = deaths[deaths['exploration_mode'] == True]
            print(f"Deaths while in exploration mode: {len(exploration_deaths)}")
            
            if not exploration_deaths.empty:
                avg_exploration_duration = exploration_deaths['exploration_duration'].mean()
                max_exploration_duration = exploration_deaths['exploration_duration'].max()
                min_exploration_duration = exploration_deaths['exploration_duration'].min()
                print(f"Average exploration mode duration before death: {avg_exploration_duration:.1f} ticks")
                print(f"Max exploration duration before death: {max_exploration_duration:.1f} ticks")
                print(f"Min exploration duration before death: {min_exploration_duration:.1f} ticks")
                
                # 生存期間と探索期間の比率
                avg_death_tick = exploration_deaths['t'].mean()
                exploration_ratio = (exploration_deaths['exploration_duration'] / exploration_deaths['t'] * 100).mean()
                print(f"Average death tick: {avg_death_tick:.1f}")
                print(f"Average % of life spent in exploration mode: {exploration_ratio:.1f}%")
            
            territory_holders_died = deaths[deaths['territories_claimed'] > 0]
            print(f"Territory holders who died: {len(territory_holders_died)}")
            
            # 探索モードから抜け出せなかった分析
            exploration_leaps = df_logs[df_logs['action'] == 'exploration_mode_leap']
            exploration_reversions = df_logs[df_logs['action'] == 'exploration_reversion']
            print(f"\nExploration mode leaps: {len(exploration_leaps)}")
            print(f"Exploration mode reversions: {len(exploration_reversions)}")
            print(f"Stuck in exploration ratio: {(len(exploration_leaps) - len(exploration_reversions))/len(exploration_leaps)*100:.1f}%" if len(exploration_leaps) > 0 else "No exploration leaps")
            
            print("\nSample death details:")
            for _, death in deaths.head(5).iterrows():
                exploration_pct = (death['exploration_duration'] / death['t'] * 100) if death['t'] > 0 else 0
                print(f"  {death['name']}: {death['cause']} at tick {death['t']}, exploration_mode={death['exploration_mode']}, duration={death['exploration_duration']} ({exploration_pct:.1f}% of life)")
        
        print("\n--- Fatigue & Cave Activity Analysis ---")
        
        # 疲労関連の活動
        fatigue_events = df_logs[df_logs['action'] == 'fatigue_rest']
        fatigue_checks = df_logs[df_logs['action'] == 'fatigue_rest_safety_check']
        print(f"Fatigue rest events: {len(fatigue_events)}")
        print(f"Fatigue rest safety checks: {len(fatigue_checks)}")
        
        # 洞窟での活動全般
        cave_actions = df_logs[df_logs['action'].isin(['night_shelter', 'rest_in_cave', 'weather_shelter', 'fatigue_rest'])]
        print(f"Total cave activities: {len(cave_actions)}")
        
        if len(cave_actions) > 0:
            print(f"Night shelters: {len(df_logs[df_logs['action'] == 'night_shelter'])}")
            print(f"Day rests: {len(df_logs[df_logs['action'] == 'rest_in_cave'])}")
            print(f"Weather shelters: {len(df_logs[df_logs['action'] == 'weather_shelter'])}")
        
        # 安全感チェック
        safety_checks = df_logs[df_logs['action'].isin(['safety_feeling_check', 'daytime_safety_check'])]
        print(f"Safety feeling checks: {len(safety_checks)}")
        
        if not safety_checks.empty:
            high_safety = safety_checks[safety_checks['safety_feeling'] > 0.15]
            if not high_safety.empty:
                print(f"High safety feelings (>0.15): {len(high_safety)}")
                print(f"Max safety feeling achieved: {high_safety['safety_feeling'].max():.3f}")
                print(f"Average threshold: {high_safety['threshold'].mean():.3f}")
                
        # 夜間洞窟行動の詳細
        if len(cave_actions) > 0:
            sample_cave = cave_actions.head(10)
            print("\nSample cave activities:")
            for _, row in sample_cave.iterrows():
                if 'safety_feeling' in row:
                    print(f"  {row['name']} {row['action']} at tick {row['t']}: safety={row.get('safety_feeling', 'N/A'):.3f}")
                else:
                    print(f"  {row['name']} {row['action']} at tick {row['t']}: (no safety data)")
    
    if not df_logs.empty:
        for npc in final_npcs:
            if not npc.alive:
                death_log = df_logs[(df_logs['name'] == npc.name)]
                if not death_log.empty:
                    print(f"- {npc.name}: Died around tick {df_logs[df_logs['name'] == npc.name]['t'].max()}")

        # 新しいリソース発見のサマリー
        print("\n--- Resource Discovery Summary ---")
        cave_discoveries = df_logs[df_logs['action'].str.contains('discover.*cave', na=False)]
        water_discoveries = df_logs[df_logs['action'].str.contains('discover.*water', na=False)]
        berry_discoveries = df_logs[df_logs['action'].str.contains('discover.*berry', na=False)]
        hunt_discoveries = df_logs[df_logs['action'].str.contains('discover.*hunting', na=False)]
        
        print(f"Caves discovered: {len(cave_discoveries)}")
        print(f"Water sources discovered: {len(water_discoveries)}")
        print(f"Berry patches discovered: {len(berry_discoveries)}")
        print(f"Hunting grounds discovered: {len(hunt_discoveries)}")
        
        # 発見の詳細
        if len(cave_discoveries) > 0:
            print(f"  - Notable cave discoveries:")
            valuable_caves = df_logs[df_logs['action'] == 'discover_valuable_cave']
            for _, cave in valuable_caves.head(3).iterrows():
                print(f"    {cave['name']} found cave at {cave.get('location')} (safety: {cave.get('safety_bonus', 0):.2f})")

        # 意味圧による探索モードの跳躍的変化サマリー
        print("\n--- Exploration Mode Leap Summary ---")
        exploration_leaps = df_logs[df_logs['action'] == 'exploration_mode_leap']
        mode_reversions = df_logs[df_logs['action'] == 'exploration_mode_reversion']
        
        if not exploration_leaps.empty:
            for _, leap in exploration_leaps.iterrows():
                npc_name = leap['name']
                pressure = leap.get('pressure', 0)
                intensity = leap.get('intensity', 0)
                print(f"'{npc_name}' leaped into exploration mode at tick {leap['t']} "
                      f"(pressure: {pressure:.2f}, intensity: {intensity:.2f})")

            print("\n--- Exploration Mode Activity ---")
            explorers = exploration_leaps['name'].unique()
            for explorer_name in explorers:
                explorer_logs = df_logs[df_logs['name'] == explorer_name]
                
                exploration_actions = explorer_logs[explorer_logs['action'] == 'exploration_mode_active']
                discovery_actions = explorer_logs[explorer_logs['action'].str.contains('discover_.*_exploration_mode')]
                
                print(f"{explorer_name}: {len(exploration_actions)} exploration mode actions, {len(discovery_actions)} discoveries")
        else:
            print("No one entered exploration mode in this simulation.")
        
        # 探索モード復帰のサマリー
        if not mode_reversions.empty:
            print("\n--- Exploration Mode Reversion Summary ---")
            for _, reversion in mode_reversions.iterrows():
                npc_name = reversion['name']
                duration = reversion.get('duration', 0)
                stability = reversion.get('stability', 0)
                print(f"'{npc_name}' returned to normal mode at tick {reversion['t']} "
                      f"(exploration duration: {duration} ticks, stability: {stability:.2f})")
        else:
            print("No exploration mode reversions occurred in this simulation.")
            
            # モード復帰検討の詳細情報を表示
            reversion_checks = df_logs[df_logs['action'] == 'mode_reversion_check']
            if not reversion_checks.empty:
                print("\n--- Exploration Mode Reversion Check Details ---")
                for _, check in reversion_checks.iterrows():
                    name = check['name']
                    duration = check.get('duration', 0)
                    stability_counter = check.get('stability_counter', 0)
                    threshold = check.get('threshold', 0)
                    pressure = check.get('exploration_pressure', 0)
                    stability = check.get('stability', 0)
                    print(f"{name} at tick {check['t']}: duration={duration}, threshold={threshold}, "
                          f"stability_counter={stability_counter}, pressure={pressure:.3f}, stability={stability:.3f}")
            else:
                print("No mode reversion checks were logged.")
        
        # リーダーシップの初期発現サマリー（無効化中）
        # print("\n--- Leadership Emergence Summary ---")
        # leadership_emergences = df_logs[df_logs['action'] == 'leadership_emergence']
        # follow_actions = df_logs[df_logs['action'] == 'follow_leader']
        # 
        # if not leadership_emergences.empty:
        #     print(f"Total leaders emerged: {len(leadership_emergences)}")
        #     for _, emergence in leadership_emergences.iterrows():
        #         leader_name = emergence['name']
        #         influence = emergence.get('influence', 0)
        #         pressure = emergence.get('pressure', 0)
        #         followers = emergence.get('initial_followers', 0)
        #         print(f"'{leader_name}' emerged as leader at tick {emergence['t']} "
        #               f"(influence: {influence:.3f}, pressure: {pressure:.3f}, initial followers: {followers})")
        # else:
        #     print("No leadership emergences occurred in this simulation.")
        #     
        # if not follow_actions.empty:
        #     print(f"\nFollower relationships formed: {len(follow_actions)}")
        #     leaders_followers = {}
        #     for _, follow in follow_actions.iterrows():
        #         follower = follow['name']
        #         leader = follow.get('leader', 'Unknown')
        #         score = follow.get('score', 0)
        #         if leader not in leaders_followers:
        #             leaders_followers[leader] = []
        #         leaders_followers[leader].append(f"{follower}(score:{score:.2f})")
        #     
        #     for leader, follower_list in leaders_followers.items():
        #         print(f"Leader {leader}: {', '.join(follower_list)}")
        # else:
        #     print("No follower relationships were formed.")
        # 
        # # 最終的なリーダーシップ状態
        # final_leaders = [npc for npc in final_npcs if npc.alive and npc.leadership_mode]
        # if final_leaders:
        #     print(f"\nFinal leadership status:")
        #     for leader in final_leaders:
        #         active_followers = [f for f in leader.followers if f in [n.name for n in final_npcs if n.alive and n.leader_target == leader]]
        #         print(f"- Leader {leader.name}: {len(active_followers)} active followers, influence: {leader.influence_score:.3f}")
        # else:
        #     print("\nNo active leaders at simulation end.")

        # 社会関係性サマリー
        print("\n--- Social Relationships Summary ---")
        # 情報共有活動のサマリー
        sharing_actions = df_logs[df_logs['action'].str.contains('share_.*_info', na=False)]
        if not sharing_actions.empty:
            print(f"Total information sharing events: {len(sharing_actions)}")
            
            # シェアしたリソースタイプ別の統計
            resource_sharing = {}
            for _, action in sharing_actions.iterrows():
                action_type = action['action']
                if 'berry_patch' in action_type:
                    resource_sharing['berry'] = resource_sharing.get('berry', 0) + 1
                elif 'cave' in action_type:
                    resource_sharing['cave'] = resource_sharing.get('cave', 0) + 1
                elif 'water' in action_type:
                    resource_sharing['water'] = resource_sharing.get('water', 0) + 1
                elif 'hunting_ground' in action_type:
                    resource_sharing['hunting'] = resource_sharing.get('hunting', 0) + 1
            
            for resource, count in resource_sharing.items():
                print(f"- {resource} information shared: {count} times")
        else:
            print("No information sharing occurred.")
        
        # 最終的な関係性ネットワーク
        if final_npcs:
            print("\nFinal relationship network:")
            strong_relationships = 0
            total_relationships = 0
            
            for npc in final_npcs:
                if npc.alive:
                    for other_name, rel_strength in npc.rel.items():
                        if rel_strength > 0.1:  # 意味のある関係
                            total_relationships += 1
                            if rel_strength > 0.6:  # 強い関係
                                strong_relationships += 1
            
            print(f"- Total meaningful relationships: {total_relationships}")
            print(f"- Strong relationships (>0.6): {strong_relationships}")
            
            # 最も社交的なNPCを特定
            most_social = None
            max_social_score = 0
            for npc in final_npcs:
                if npc.alive:
                    social_score = sum(npc.rel.values()) + npc.kappa.get("social", 0) * 5
                    if social_score > max_social_score:
                        max_social_score = social_score
                        most_social = npc
            
            if most_social:
                print(f"- Most social NPC: {most_social.name} (social score: {max_social_score:.2f})")

        # 縄張りシステムのサマリー
        print("\n--- Territory System Summary ---")
        territory_claims = df_logs[df_logs['action'] == 'claim_territory']
        territory_losses = df_logs[df_logs['action'] == 'lose_territory']
        territorial_warnings = df_logs[df_logs['action'] == 'territorial_warning']
        community_merges = df_logs[df_logs['action'] == 'community_merge']
        group_invitations = df_logs[df_logs['action'] == 'group_territory_invitation']
        
        if not territory_claims.empty:
            print(f"Total territory claims: {len(territory_claims)}")
            for _, claim in territory_claims.iterrows():
                npc_name = claim['name']
                center = claim.get('center', 'Unknown')
                radius = claim.get('radius', 0)
                strength = claim.get('strength', 0)
                coherence = claim.get('coherence_score', 0)
                print(f"- {npc_name} claimed territory at {center} (radius: {radius}, coherence: {coherence:.3f}, strength: {strength:.2f})")
        else:
            print("No territories were claimed in this simulation.")
            
        # コミュニティサイズ分析
        if final_npcs:
            print("\n--- Community Size Analysis ---")
            active_territories = [npc for npc in final_npcs if npc.alive and npc.territory is not None]
            
            if active_territories:
                community_sizes = []
                max_community = None
                max_size = 0
                
                for npc in active_territories:
                    territory = npc.territory
                    community_size = territory.get_community_size()
                    cohesion = territory.get_community_cohesion()
                    active_members = territory.get_active_members(npc.roster_ref)
                    
                    community_sizes.append(community_size)
                    
                    if community_size > max_size:
                        max_size = community_size
                        max_community = npc
                    
                    member_names = [member.name for member in active_members]
                    print(f"- {npc.name}'s community at {territory.center}: {community_size} members, cohesion: {cohesion:.3f}")
                    print(f"  Members: {', '.join(member_names) if member_names else 'None active'}")
                
                if max_community:
                    print(f"\nLargest community: {max_community.name} with {max_size} members")
                    print(f"Average community size: {sum(community_sizes)/len(community_sizes):.2f}")
                    print(f"Total unique community members: {sum(community_sizes)}")
                    
                    # コミュニティサイズ分布を表示
                    size_distribution = {}
                    for size in community_sizes:
                        size_distribution[size] = size_distribution.get(size, 0) + 1
                    print(f"Community size distribution: {size_distribution}")
                    
                    # コミュニティサイズと生存率の相関分析
                    if len(community_sizes) > 1:
                        isolated_npcs = [npc for npc in final_npcs if npc.alive and (not hasattr(npc, 'territory') or npc.territory is None)]
                        community_members = [npc for npc in final_npcs if npc.alive and hasattr(npc, 'territory') and npc.territory is not None]
                        
                        print(f"\nSurvival analysis:")
                        print(f"Isolated survivors: {len(isolated_npcs)}")
                        print(f"Community survivors: {len(community_members)}")
                        if len(community_members) > len(isolated_npcs):
                            print("-> Community formation improves survival against predators!")
            else:
                print("No active communities found.")
                
        # コミュニティ形成活動の統計
        print("\n--- Community Formation Statistics ---")
        territory_invitations = df_logs[df_logs['action'] == 'territory_invitation']
        oxytocin_bonding = df_logs[df_logs['action'] == 'oxytocin_bonding']
        
        print(f"Territory invitations sent: {len(territory_invitations)}")
        print(f"Group invitations (friends bringing friends): {len(group_invitations)}")
        print(f"Community merges (territorial cooperation): {len(community_merges)}")
        print(f"Oxytocin bonding events: {len(oxytocin_bonding)}")
        
        if not community_merges.empty:
            print("\\nSuccessful community merges:")
            for _, merge in community_merges.iterrows():
                print(f"- {merge['name']} merged with {merge['partner']} (relationship: {merge['relationship']:.3f})")
            
        if not territory_losses.empty:
            print(f"\nTerritory conflicts: {len(territory_losses)}")
            for _, loss in territory_losses.iterrows():
                loser = loss['name']
                aggressor = loss.get('aggressor', 'Unknown')
                print(f"- {loser} lost territory to {aggressor}")
                
        if not territorial_warnings.empty:
            print(f"\nTerritorial warnings issued: {len(territorial_warnings)}")
            
        # 最終的な縄張り状況
        if final_npcs:
            current_territories = [npc for npc in final_npcs if npc.alive and npc.territory is not None]
            if current_territories:
                print(f"\nFinal territory holdings:")
                for npc in current_territories:
                    print(f"- {npc.name}: Territory at {npc.territory.center}, radius {npc.territory.radius}")
            else:
                print("\nNo active territories at simulation end.")

        # 引退システムのサマリー（無効化中）
        # print("\n--- Retirement System Summary ---")
        # retirements = df_logs[df_logs['action'] == 'retirement']
        # knowledge_transfers = df_logs[df_logs['action'] == 'knowledge_transfer']
        # mentorships = df_logs[df_logs['action'] == 'ongoing_mentorship']
        
        # if not retirements.empty:
        #     print(f"Total retirements: {len(retirements)}")
        #     for _, retirement in retirements.iterrows():
        #         elder_name = retirement['name']
        #         age = retirement.get('age', 'Unknown')
        #         experience = retirement.get('experience', 0)
        #         mentee = retirement.get('mentor_target', 'None')
        #         print(f"- {elder_name}: Retired at age {age}, experience {experience:.1f}, mentoring {mentee}")
        
        #     print(f"Knowledge transfers: {len(knowledge_transfers)}")
        #     print(f"Ongoing mentorship sessions: {len(mentorships)}")
        
        #     # 引退者の最終状態
        #     print(f"\nFinal retirement status:")
        #     for npc in final_npcs:
        #         if npc.retired:
        #             print(f"- Elder {npc.name}: Age {npc.age}, Experience {npc.experience_points:.1f}, "
        #                   f"Discoveries {npc.lifetime_discoveries}, Shares {npc.lifetime_shares}")
        # else:
        #     print("No retirements occurred in this simulation.")

    print("\n--- Weather Summary ---")
    print(df_weather['condition'].value_counts())