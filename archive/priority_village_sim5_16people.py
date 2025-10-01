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

    def step(self):
        for v in self.berries.values(): 
            v["abundance"] = min(1.0, v["abundance"] + v["regen"] * (1.0 - v["abundance"]))
        self.t += 1
        self.day_night.step()
        self.weather.step()
        
    def nearest_nodes(self, pos, node_dict, k=4):
        nodes = list(node_dict.keys())
        if not nodes: return []
        nodes.sort(key=lambda p: abs(p[0] - pos[0]) + abs(p[1] - pos[1]))
        return nodes[:k]

# =========================
# Territory & NPC Class
# =========================
class Territory:
    def __init__(self, owner, center, radius):
        self.owner = owner
        self.center = center
        self.radius = radius

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
        self.mode_stability_counter = 0  # モード安定性カウンター
        
        # 引退システム関連（無効化中）
        self.age = random.randint(20, 40)  # 初期年齢
        self.experience_points = 0.0       # 経験値累積
        self.lifetime_discoveries = 0      # 生涯発見数
        self.lifetime_shares = 0           # 生涯共有数
        self.retirement_readiness = 0.0    # 引退準備度
        self.retired = False               # 引退状態
        self.mentor_target = None          # 指導対象
        self.knowledge_legacy = []         # 知識遺産ログ
        self.last_discovery_tick = 0
        
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
        """意味圧に応じた探索モードへの跳躍的変化"""
        exploration_pressure = self.calculate_exploration_pressure()
        
        if self.exploration_mode:
            # 探索モード中の場合、復帰を検討
            return self.consider_mode_reversion(t, exploration_pressure)
        else:
            # 通常モードから探索モードへの跳躍を検討
            return self.consider_exploration_leap(t, exploration_pressure)
    
    def consider_exploration_leap(self, t, exploration_pressure):
        """探索モードへの跳躍的移行判定"""
        # 意味圧が閾値を超えた時の跳躍条件
        pressure_threshold = 0.8 + (1.0 - self.curiosity) * 0.3  # 好奇心が低いほど高い閾値
        
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

    def consider_mode_reversion(self, t, exploration_pressure):
        """探索モードから通常モードへの復帰判定"""
        # モード安定性の評価
        resource_stability = self.evaluate_resource_stability()
        
        # 意味圧が低く、リソースが安定している場合
        if exploration_pressure < 0.3 and resource_stability > 0.6:
            self.mode_stability_counter += 1
        else:
            self.mode_stability_counter = max(0, self.mode_stability_counter - 1)
        
        mode_duration = t - self.exploration_mode_start_tick
        
        # 復帰条件：意味圧の減少と安定性の確保
        reversion_threshold = 15 + (self.curiosity * 10)  # 好奇心が高いほど長く続ける
        
        # デバッグ情報（必要時）
        if mode_duration > 30 and t % 30 == 0:
            self.log.append({"t": t, "name": self.name, "action": "mode_reversion_check", 
                           "stability_counter": self.mode_stability_counter, 
                           "duration": mode_duration, "threshold": reversion_threshold,
                           "exploration_pressure": exploration_pressure, "stability": resource_stability})
        
        if (self.mode_stability_counter >= reversion_threshold and 
            mode_duration > 10 and
            exploration_pressure < 0.4):
            
            # 通常モードへの復帰
            self.exploration_mode = False
            self.exploration_intensity = 1.0
            self.mode_stability_counter = 0
            
            # 探索経験を少し減衰（忘却効果）
            self.kappa["exploration"] = max(0.05, self.kappa.get("exploration", 0.1) * 0.9)
            
            self.log.append({"t": t, "name": self.name, "action": "exploration_mode_reversion", 
                           "duration": mode_duration, "stability": resource_stability})
            return True
        
        return False
    
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
        if scout_duration > 50 and t % 50 == 0:  # 50tickごとに状況をログ
            self.log.append({"t": t, "name": self.name, "action": "scout_reversion_check", 
                           "stability_counter": self.resource_stability_counter, 
                           "duration": scout_duration, "threshold": reversion_threshold,
                           "exploration_pressure": exploration_pressure, "stability": resource_stability})
        
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
                    self.share_discovery_with_pleasure(t, nearest[0], res_type)
                    self.log.append({"t": t, "name": self.name, "action": f"discover_{res_type}_exploration_mode", 
                                   "location": nearest[0], "intensity": self.exploration_intensity})
        return True



    def step(self, t):
        if not self.alive: return

        self.hunger += 0.8  # 空腹度の増加を緩和
        self.thirst += 1.2  # 渇きの増加を緩和
        self.fatigue += 0.9  # 疲労の増加を緩和
        # 死亡判定をより緩和（スカウト復帰システムテスト用）
        if self.hunger >= 120 or self.thirst >= 120:
            self.alive = False
            return

        # 引退システム：年齢更新と引退判定（無効化中）
        # if t % 50 == 0:  # 50tick毎に年齢更新
        #     self.age += 1
            
        # # 引退判定（引退済みでない場合のみ）
        # if not self.retired:
        #     if self.consider_retirement(t):
        #         return  # 引退した場合は他の行動をスキップ

        # # 引退者は限定的な行動のみ
        # if self.retired:
        #     self.elder_activities(t)
        #     return

        # 意味圧に応じた探索モードの跳躍的変化
        self.consider_exploration_mode_shift(t)

        # 探索モード中の積極的行動または高い探索圧力時
        if self.exploration_mode or self.calculate_exploration_pressure() > 1.5:
            if self.exploration_mode_action(t): return

        # 基本的な生存行動
        if self.thirst > 70:
            known_water = self.env.nearest_nodes(self.pos(), {k:v for k,v in self.env.water_sources.items() if k in self.knowledge_water}, k=1)
            if known_water:
                target = known_water[0]
                if self.pos() == target:
                    self.thirst = 0
                    self.fatigue = max(0, self.fatigue - 5)  # 水分補給時に休憩効果も付与
                else:
                    self.move_towards(target)
                return
        
        if self.hunger > 70:
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
def run_sim(TICKS=1500):  # より長期間のシミュレーション
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
    final_npcs, df_logs, df_weather = run_sim(TICKS=1200)
    print("\n--- 16-Person Village Simulation Finished ---")
    print(f"Survivors: {sum(1 for n in final_npcs if n.alive)} / {len(final_npcs)}")
    
    if not df_logs.empty:
        for npc in final_npcs:
            if not npc.alive:
                death_log = df_logs[(df_logs['name'] == npc.name)]
                if not death_log.empty:
                    print(f"- {npc.name}: Died around tick {df_logs[df_logs['name'] == npc.name]['t'].max()}")

        # 新しいリソース発見のサマリー
        print("\n--- Resource Discovery Summary ---")
        cave_discoveries = df_logs[df_logs['action'] == 'discover_cave']
        water_discoveries = df_logs[df_logs['action'] == 'discover_water']
        berry_discoveries = df_logs[df_logs['action'] == 'discover_berry_patch']
        hunt_discoveries = df_logs[df_logs['action'] == 'discover_hunting_ground']
        
        print(f"Caves discovered: {len(cave_discoveries)}")
        print(f"Water sources discovered: {len(water_discoveries)}")
        print(f"Berry patches discovered: {len(berry_discoveries)}")
        print(f"Hunting grounds discovered: {len(hunt_discoveries)}")

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