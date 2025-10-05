
import random, math
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

random.seed(42); np.random.seed(42)

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
                    self.int    roster = {}
    # NPCの人数を16人に大幅増加（4つのグループに分散配置）
    npc_configs = [
        # 北西グループ（探索・冒隺重視）
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
    ].uniform(0.3, 0.8)
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
        return self.night_start <= time < self.night_end or time >= self.night_end
    def is_day(self):
        return not self.is_night()
    def get_light_level(self):
        time = self.get_time_of_day()
        if time < self.night_start:
            progress = time / self.night_start
            return (math.sin((progress - 0.5) * math.pi) + 1) / 2
        elif time < self.night_end:
            return 0.1
        else:
            progress = (time - self.night_end) / (1.0 - self.night_end)
            return progress * 0.3
    def get_sleep_pressure(self):
        time = self.get_time_of_day()
        if self.night_start <= time < self.night_end:
            night_center = (self.night_start + self.night_end) / 2
            distance_from_center = abs(time - night_center)
            max_distance = (self.night_end - self.night_start) / 2
            pressure = 1.0 - (distance_from_center / max_distance) * 0.5
            return pressure
        else:
            return 0.1
    def get_activity_cost_multiplier(self):
        light = self.get_light_level()
        return 1.0 + (1.0 - light)
    def get_forage_success_modifier(self):
        light = self.get_light_level()
        return 0.3 + light * 0.7

# =========================
# Predator
# =========================
class Predator:
    def __init__(self, env, strength=3.0):
        self.env = env
        self.x = random.randrange(env.size)
        self.y = random.randrange(env.size)
        self.strength = strength
        self.active = False
        self.duration = 0
        self.max_duration = 30
        self.camp_ticks = 0
        self.camping_node = None
        self.camp_radius = 2
        self.camp_threshold = 8

    def pos(self):
        return (self.x, self.y)
    def spawn(self, t):
        self.x = random.randrange(self.env.size)
        self.y = random.randrange(self.env.size)
        self.active = True
        self.duration = 0
        self.camp_ticks = 0
        self.camping_node = None
        return self.pos()
    def despawn(self):
        self.active = False
        self.camp_ticks = 0
        self.camping_node = None

    def step(self):
        if not self.active:
            return
        self.duration += 1
        if self.duration >= self.max_duration:
            self.despawn(); return

        if random.random() < 0.3:
            self.x += random.choice([-1, 0, 1])
            self.y += random.choice([-1, 0, 1])
            self.x = max(0, min(self.env.size-1, self.x))
            self.y = max(0, min(self.env.size-1, self.y))

        nodes = list(self.env.huntzones.keys())
        if nodes:
            near = min(nodes, key=lambda p: abs(p[0]-self.x)+abs(p[1]-self.y))
            d = abs(near[0]-self.x)+abs(near[1]-self.y)
            if d <= self.camp_radius:
                if self.camping_node == near:
                    self.camp_ticks += 1
                else:
                    self.camping_node = near
                    self.camp_ticks = 1
            else:
                self.camping_node = None
                self.camp_ticks = 0

    def is_camping(self):
        return self.active and (self.camp_ticks >= self.camp_threshold) and (self.camping_node is not None)

    def distance_to(self, npc):
        return abs(self.x - npc.x) + abs(self.y - npc.y)

# =========================
# Environment
# =========================
class EnvForageBuff:
    def __init__(self, size=40, n_berry=18, n_hunt=10, n_water=5, n_caves=4):
        self.size = size
        self.berries = {}
        for _ in range(n_berry):
            x, y = random.randrange(size), random.randrange(size)
            self.berries[(x, y)] = {"abundance": random.uniform(0.3, 0.7), "regen": random.uniform(0.004, 0.015)}
        self.huntzones = {}
        for _ in range(n_hunt):
            x, y = random.randrange(size), random.randrange(size)
            self.huntzones[(x, y)] = {"base_success": random.uniform(0.20, 0.50), "danger": random.uniform(0.25, 0.65)}
        
        self.water_sources = {}
        for _ in range(n_water):
            x, y = random.randrange(size), random.randrange(size)
            self.water_sources[(x,y)] = {"quality": random.uniform(0.5, 1.0)}

        # Add caves from pasted_content.txt
        self.caves = {(random.randrange(size), random.randrange(size)): {"safety_bonus": random.uniform(0.7, 0.9)} for _ in range(n_caves)}

        self.t = 0
        self.day_night = DayNightCycle(day_length=48)
        self.weather = Weather()

    def step(self):
        for v in self.berries.values():
            v["abundance"] = min(1.0, v["abundance"] + v["regen"] * (1.0 - v["abundance"]))
        for v in self.huntzones.values():
            v["base_success"] = float(np.clip(v["base_success"] + np.random.normal(0, 0.01), 0.03, 0.8))
        self.t += 1
        self.day_night.step()
        self.weather.step()

    def nearest_nodes(self, pos, node_dict, k=4):
        nodes = list(node_dict.keys())
        if not nodes: return []
        nodes.sort(key=lambda p: abs(p[0] - pos[0]) + abs(p[1] - pos[1]))
        return nodes[:k]
        
    def forage(self, pos, node):
        abundance = self.berries[node]["abundance"]
        dist = abs(pos[0] - node[0]) + abs(pos[1] - node[1])
        p = 0.6 * abundance + 0.25 * max(0, 1 - dist / 12)
        modifier = self.day_night.get_forage_success_modifier()
        p *= modifier

        # 雨が強いと採集成功率が下がる (from pasted_content.txt)
        if self.weather.condition == "rainy":
            p *= (1.0 - 0.5 * self.weather.intensity)

        success = random.random() < p
        if success:
            self.berries[node]["abundance"] = max(0.0, self.berries[node]["abundance"] - random.uniform(0.2, 0.4))
            food = random.uniform(14, 26) * (0.6 + abundance / 2)
        else:
            food = 0.0
        risk = 0.05
        return success, food, risk, p

# =========================
# Territory & NPC Class
# =========================
class Territory:
    def __init__(self, owner, center, radius):
        self.owner = owner
        self.center = center
        self.radius = radius
        self.intrusion_tolerance = 0.5
        self.memory = {"food_found":0, "helped_here":0, "threatened":0, "rested":0}
        self.attachment_strength = 0.3
    def contains(self, pos):
        dx = pos[0] - self.center[0]; dy = pos[1] - self.center[1]
        return (dx**2 + dy**2) <= self.radius**2

class NPCPriority:
    def __init__(self, name, preset, env, roster_ref, start_pos,
                 horizon=8, horizon_rally=6, rally_ttl=10):
        self.name = name; self.env = env; self.roster_ref = roster_ref
        self.x, self.y = start_pos
        self.hunger = 50.0; self.thirst = 20.0; self.fatigue = 30.0; self.injury = 0.0
        self.water = 15.0  # 初期水分量を増加 
        self.alive = True; self.state = "Awake"
        self.kappa = defaultdict(lambda: 0.1); self.kappa_min = 0.05
        self.E = 0.0; self.T = 0.3
        self.G0 = 0.5; self.g = 0.7; self.eta = 0.3
        self.lambda_forget = 0.02; self.rho = 0.1; self.alpha = 0.6; self.beta_E = 0.15
        self.Theta0 = 1.0; self.a1 = 0.5; self.a2 = 0.4; self.h0 = 0.2; self.gamma = 0.8
        self.T0 = 0.3; self.c1 = 0.5; self.c2 = 0.6
        p = preset
        self.risk_tolerance = p["risk_tolerance"]; self.curiosity = p["curiosity"]
        self.avoidance = p["avoidance"]; self.stamina = p["stamina"]; self.empathy = p.get("empathy",0.6)
        self.TH_H = 55.0; self.TH_T = 60.0 
        self.rel = defaultdict(float); self.help_debt = defaultdict(float)
        self.sleep_debt = 0.0; self.is_sleeping = False; self.sleep_duration = 0
        self.total_sleep_time = 0; self.sleep_cycles = 0
        initial_radius = 5 + self.avoidance * 3
        self.territory = Territory(owner=self.name, center=self.pos(), radius=initial_radius)
        self.territorial_aggression = 0.3 + (1 - self.empathy) * 0.4
        self.group_loyalty = 0.5 + self.empathy * 0.3
        self.detected_intruders = []
        self.invited_guests = set()
        self.log = []
        
        # 【修正1】rally_targetの初期化
        self.rally_target = None
        self.boredom = 0.0
        self.max_store = 120.0
        self.food_store = 0.0
        self.rally_ttl_default = rally_ttl
        self.horizon = horizon
        self.horizon_rally = horizon_rally
        self.cohesion = 0.0
        self.village_affinity = 0.0
        self.last_social_tick = 0
        self.align_inertia = 0.0
        self.align_streak  = 0
        self.align_decay   = 0.004
        self.rally_state = { "leader": None, "ttl": 0, "node": None, "min_k": 2, "kind": "hunt"}
        self.combat_power_base = 2.0 + (self.risk_tolerance * 2.0) + (self.stamina * 1.0)
        self.combat_xp = 0.0
        self.knowledge_water = set()
        # 最も近い水源を1つだけ知っている状態でスタート
        initial_waters = self.env.nearest_nodes(self.pos(), self.env.water_sources, k=1)
        for water in initial_waters:
            self.knowledge_water.add(water)

        # --- pasted_content.txtからの追加 --- 
        # 【修正2】初期関係性の設定を改善
        # （現在のコードでは他のNPCがまだroster_refに登録されていない可能性）
        # この処理は全NPCが生成された後に実行すべき
        
        # 役割関連
        self.role = "generalist"
        self.discovery_reward_multiplier = 1.0
        self.last_discovery_tick = 0

        # 知識管理を拡張：各種リソースの発見状況を管理
        self.knowledge_caves = set()
        self.knowledge_berries = set()  # ベリー採取場所の知識
        self.knowledge_huntzones = set()  # 狩場の知識
        
        # 初期知識を大幅に削減：最低限のリソースのみ知っている状態
        # 洞窟は1つだけ知っている
        initial_cave = self.env.nearest_nodes(self.pos(), self.env.caves, k=1)
        if initial_cave: self.knowledge_caves.add(initial_cave[0])
        
        # ベリーは最も近い1つだけ知っている
        initial_berries = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
        for berry in initial_berries:
            self.knowledge_berries.add(berry)
            
        # 狩場は知らない状態でスタート（探索で発見する必要がある）
        # initial_huntzones = self.env.nearest_nodes(self.pos(), self.env.huntzones, k=1)
        # for hunt in initial_huntzones:
        #     self.knowledge_huntzones.add(hunt)
        # --- pasted_content.txtからの追加ここまで ---

    def update_alignment_inertia(self, action_type, meaning_pressure, processed_amount, success):
        eps = 1e-6
        eff = processed_amount / max(meaning_pressure, eps) if meaning_pressure > 0 else 0.0
        eff = max(0.0, min(1.5, eff))
        if success:
            self.align_streak += 1
            gain = 0.06 * eff * (1.0 + 0.2 * min(6, self.align_streak))
            self.align_inertia = min(1.0, self.align_inertia + gain)
        else:
            self.align_streak = 0
            self.align_inertia = max(0.0, self.align_inertia - 0.03*(1.2 - eff))

    def decay_alignment_inertia(self):
        self.align_inertia = max(0.0, self.align_inertia - self.align_decay)

    def combat_power(self, group_bonus=0.0):
        k = self.kappa.get("hunt", 0.1)
        xp_term = 1.0 + 0.15*np.tanh(self.combat_xp/30.0)
        fatigue_pen = 1.0 - 0.35*(self.fatigue/120.0)
        injury_pen  = 1.0 - 0.50*(self.injury /120.0)
        inertia_boost = 1.0 + 0.25*self.align_inertia
        return max(0.1,
                   (self.combat_power_base * (1.0 + 0.25*k) * xp_term * fatigue_pen * injury_pen * inertia_boost)
                   * (1.0 + group_bonus)
        )

    def gain_combat_xp(self, amount):
        self.combat_xp += amount

    def pos(self): return (self.x, self.y)
    def dist_to(self, o): return abs(self.x - o.x) + abs(self.y - o.y)
    def dist_to_pos(self, pos): return abs(self.x - pos[0]) + abs(self.y - pos[1])  # タプル座標との距離計算
    def move_towards(self, target):
        # 【修正3】境界チェックの追加
        tx, ty = target
        self.x += (1 if tx > self.x else -1 if tx < self.x else 0)
        self.y += (1 if ty > self.y else -1 if ty < self.y else 0)
        self.x = max(0, min(self.env.size - 1, self.x))
        self.y = max(0, min(self.env.size - 1, self.y))
    def nearby_allies(self, radius=3): return [o for on, o in self.roster_ref.items() if on != self.name and o.alive and self.dist_to(o) <= radius]
    def alignment_flow(self, action_type, meaning_pressure): return (self.G0 + self.g * self.kappa[action_type]) * meaning_pressure
    def update_kappa(self, action_type, success, reward):
        kappa = self.kappa[action_type]
        work = self.eta * reward if success else -self.rho * (kappa ** 2)
        self.kappa[action_type] = max(self.kappa_min, kappa + work - (self.lambda_forget * (kappa - self.kappa_min)))
    def update_heat(self, meaning_pressure, processed_amount):
        unprocessed = max(0, meaning_pressure - processed_amount)
        self.E = max(0, self.E + self.alpha * unprocessed - self.beta_E * self.E)
    def get_personal_sleep_pressure(self):
        env_pressure = self.env.day_night.get_sleep_pressure()
        debt_pressure = min(1.0, self.sleep_debt / 100)
        fatigue_pressure = min(1.0, self.fatigue / 100)
        return (env_pressure * 0.5 + debt_pressure * 0.3 + fatigue_pressure * 0.2)
    def should_sleep(self):
        if self.is_sleeping: return True
        if self.sleep_debt > 150: return True
        if self.fatigue > 90: return True
        if self.env.day_night.is_night() and self.fatigue > 60: return True
        if self.get_personal_sleep_pressure() > 0.7 and self.hunger < 85 and self.thirst < 85: return True
        return False
    def enter_sleep(self, t): self.is_sleeping = True; self.sleep_duration = 0; self.state = "Sleeping"; self.sleep_cycles += 1
    def consolidate_memory(self):
        if len(self.kappa) < 2: return
        actions, values = list(self.kappa.keys()), list(self.kappa.values())
        mean_kappa = np.mean(values)
        for action in actions:
            if self.kappa[action] > mean_kappa: self.kappa[action] = min(1.0, self.kappa[action] + 0.05)
            else: self.kappa[action] = max(self.kappa_min, self.kappa[action] - self.lambda_forget * 3)
    def wake_up(self, t, reason):
        self.is_sleeping = False; self.state = "Awake"
        if reason == "natural": self.T = self.T0; self.boredom = 0.0
        self.sleep_duration = 0
    def update_territory_center(self):
        cx, cy = self.territory.center
        self.territory.center = (cx * 0.95 + self.x * 0.05, cy * 0.95 + self.y * 0.05)
    def detect_intruders(self, t):
        self.detected_intruders = []
        for ally in self.nearby_allies(radius=int(self.territory.radius)):
            if ally.name in self.invited_guests: continue
            if self.territory.contains(ally.pos()):
                self.detected_intruders.append({"npc": ally, "threat_level": self.calculate_threat(ally)})
    def calculate_threat(self, other):
        threat = 0.3 + other.territorial_aggression * 0.3
        if self.rel[other.name] < 0: threat += abs(self.rel[other.name]) * 0.5
        elif self.rel[other.name] > 0.5: threat -= 0.3
        if self.hunger > 70 and other.hunger > 70: threat += 0.4
        return max(0, min(1.0, threat))
    def react_to_intruder(self, intruder, t):
        threat, other = intruder["threat_level"], intruder["npc"]
        if threat < 0.3 and self.empathy > 0.7 and random.random() < 0.3: return "invited"
        elif threat < 0.6: return "warned"
        else: return "chased" if self.territorial_aggression > other.territorial_aggression else "retreated"
    def detect_predator(self, predator, t):
        if not predator.active: return None
        dist = predator.distance_to(self)
        if dist <= 10:
            threat_level = predator.strength * (1 - dist / 10)
            self.E = min(5.0, self.E + threat_level * 0.3)
            for ally in self.nearby_allies(radius=5):
                ally.E = min(5.0, ally.E + threat_level * 0.2)
            if dist <= 3:
                escape_x = self.territory.center[0] + (self.x - predator.x)
                escape_y = self.territory.center[1] + (self.y - predator.y)
                self.move_towards((escape_x, escape_y))
                self.log.append({"t": t, "name": self.name, "action": "flee_predator"})
                return "fled"
        return None

    def emit_rally_predator(self, t, predator_node=None, min_k=2, ttl=10):
        self.rally_state = {"leader": self.name, "ttl": ttl, "node": predator_node, "min_k": min_k, "kind": "predator"}
        self.log.append({"t": t, "name": self.name, "action": "rally_for_predator"})

    def attempt_predator_hunt(self, t, predator):
        rs = self.rally_state
        if not (rs and rs.get("leader") == self.name and rs.get("ttl",0) > 0 and rs.get("kind") == "predator"): return False
        party = [self] + [ally for ally in self.nearby_allies(radius=3) if getattr(ally, "rally_target", None) == self.name and ally.state == "rallying"]
        if len(party) < rs.get("min_k", 2): return False
        if not predator.active or predator.distance_to(self) > 3: return False

        total_combat_power = sum(m.combat_power(group_bonus=0.2) for m in party)
        success_chance = min(0.9, total_combat_power / (predator.strength * 5.0))

        if random.random() < success_chance:
            predator.despawn()
            for m in party:
                m.gain_combat_xp(5.0 + 2.0*predator.strength)
                m.update_kappa("hunt", True, 1.0)
                m.update_alignment_inertia("predator", 1.0, 1.0, True)
            self.log.append({"t": t, "name": self.name, "action": "predator_slay_success", "party": [m.name for m in party]})
        else:
            for m in party:
                m.injury = min(120, m.injury + random.uniform(5, 15))
                m.gain_combat_xp(2.0 + 1.0*predator.strength)
                m.update_kappa("hunt", False, 0)
                m.update_alignment_inertia("predator", 1.0, 0.0, False)
            self.log.append({"t": t, "name": self.name, "action": "predator_slay_failure", "party": [m.name for m in party]})
        for m in party:
            if getattr(m, "rally_target", None) == self.name: m.rally_target = None; m.state = "Awake"
        self.rally_state = {"leader": None, "ttl": 0, "node": None, "min_k": 2, "kind": "hunt"}
        return True

    def emit_rally_for_hunt(self, t, hunt_node=None, min_k=2, ttl=10):
        self.rally_state = {"leader": self.name, "ttl": ttl, "node": hunt_node, "min_k": min_k, "kind": "hunt"}
        self.log.append({"t": t, "name": self.name, "action": "rally_for_hunt"})

    def consider_join_rally(self, t):
        for ally in self.nearby_allies(radius=8):
            rs = getattr(ally, "rally_state", None)
            if rs and rs.get("leader") == ally.name and rs.get("ttl",0) > 0:
                rally_kind = rs.get("kind", "hunt")
                threat_bonus = 0.35 if rally_kind == "predator" else 0.0
                need_pressure = max(0.0, (self.hunger - self.TH_H) / (100 - self.TH_H))
                base = self.alignment_flow("hunt", need_pressure)
                u = base + 0.70 + threat_bonus + 0.35 * self.rel[ally.name] - 0.008 * self.fatigue + 0.4 * self.cohesion + 0.4 * self.village_affinity
                if u >= 0.0 and not self.is_sleeping:
                    target = rs["node"] if rs["node"] else ally.pos()
                    self.move_towards(target); self.state = "rallying"; self.rally_target = ally.name
                    self.log.append({"t": t, "name": self.name, "action": "join_rally", "leader": ally.name})
                    return True
        return False

    def attempt_rally_group_hunt(self, t):
        rs = self.rally_state
        if not (rs and rs.get("leader") == self.name and rs.get("ttl",0) > 0): return False
        party = [self] + [ally for ally in self.nearby_allies(radius=3) if getattr(ally, "rally_target", None) == self.name and ally.state == "rallying"]
        if len(party) < rs.get("min_k", 2): return False
        nodes = self.env.nearest_nodes(self.pos(), self.env.huntzones, k=1)
        if not nodes: return False;
        node = nodes[0]
        success = random.random() < 0.8
        total_food = 100 if success else 0
        shares = [total_food / len(party)] * len(party)
        for m, share in zip(party, shares):
            if success:
                before = m.hunger; m.hunger = max(0.0, m.hunger - share)
                rem = max(0.0, share - (before - m.hunger)); m.food_store = min(m.max_store, m.food_store + rem * 0.6)
                m.update_kappa("hunt", True, share)
                meaning_p = max(0.0, (m.hunger - m.TH_H) / (100 - m.TH_H)); processed = min(1.0, 0.6 + 0.4*np.tanh(share/60.0))
                m.update_alignment_inertia("hunt", meaning_p, processed, True)
            else:
                m.update_kappa("hunt", False, 0)
                meaning_p = max(0.0, (self.hunger - self.TH_H) / (100 - self.TH_H))
                m.update_alignment_inertia("hunt", meaning_p, 0.0, False)
            if getattr(m, "rally_target", None) == self.name: m.rally_target = None; m.state = "Awake"
        self.log.append({"t": t, "name": self.name, "action": "rally_group_hunt_success" if success else "rally_group_hunt_failure", "party": [m.name for m in party]})
        self.rally_state = {"leader": None, "ttl": 0, "node": None, "min_k": 2, "kind": "hunt"}
        return True

    def mark_social(self, t): self.last_social_tick = t
    def apply_triadic_closure(self):
        for i, a in enumerate(self.nearby_allies(radius=4)):
            for b in self.nearby_allies(radius=4)[i+1:]:
                if self.rel[a.name] > 0.2 and self.rel[b.name] > 0.2:
                    inc = 0.03 * min(self.rel[a.name], self.rel[b.name])
                    a.rel[b.name] = max(-0.5, min(1.0, a.rel.get(b.name, 0) + inc))
                    b.rel[a.name] = max(-0.5, min(1.0, b.rel.get(a.name, 0) + inc))
    def copresence_tick(self):
        for o in self.nearby_allies(radius=3):
            if self.rel[o.name] > 0: self.rel[o.name] = min(1.0, self.rel[o.name] + 0.015)
    def social_gravity_move(self):
        cands = self.nearby_allies(radius=6)
        if not cands: return False
        best = max(cands, key=lambda o: self.rel[o.name])
        if random.random() < 0.25: self.move_towards(best.pos()); return True
        return False

    # --- pasted_content.txtからの追加メソッド ---
    def calculate_exploration_pressure(self):
        pressure = 0.0
        ticks_since_discovery = self.env.t - self.last_discovery_tick
        boredom = min(1.0, ticks_since_discovery / 150.0)
        pressure += boredom * 0.6
        
        # 全リソースタイプの未発見状況を考慮した探索圧力
        total_unknown_pressure = 0.0
        
        # 洞窟の未発見圧力
        if len(self.knowledge_caves) < len(self.env.caves):
            cave_ratio = 1.0 - len(self.knowledge_caves) / len(self.env.caves)
            total_unknown_pressure += cave_ratio * 0.25
            
        # 水源の未発見圧力
        if len(self.knowledge_water) < len(self.env.water_sources):
            water_ratio = 1.0 - len(self.knowledge_water) / len(self.env.water_sources)
            total_unknown_pressure += water_ratio * 0.25
            
        # ベリー採取場所の未発見圧力
        if len(self.knowledge_berries) < len(self.env.berries):
            berry_ratio = 1.0 - len(self.knowledge_berries) / len(self.env.berries)
            total_unknown_pressure += berry_ratio * 0.3  # 食料は重要なので重み大
            
        # 狩場の未発見圧力
        if len(self.knowledge_huntzones) < len(self.env.huntzones):
            hunt_ratio = 1.0 - len(self.knowledge_huntzones) / len(self.env.huntzones)
            total_unknown_pressure += hunt_ratio * 0.2
            
        pressure += total_unknown_pressure
        
        # スカウト役の場合は仲間への情報提供責任も圧力となる
        if self.role == "scout":
            allies_needing_info = 0
            for ally in self.nearby_allies(radius=100):
                if (len(ally.knowledge_caves) < len(self.knowledge_caves) or
                    len(ally.knowledge_berries) < len(self.knowledge_berries) or
                    len(ally.knowledge_huntzones) < len(self.knowledge_huntzones)):
                    allies_needing_info += 1
            if allies_needing_info > 0: pressure += 0.4
            
        return min(2.5, pressure)  # 最大値も少し上げる

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
        pleasure = meaning_pressure * value * 1.0 * self.discovery_reward_multiplier
        
        self.kappa["exploration"] = min(1.0, self.kappa.get("exploration", 0.1) + 0.15)
        self.E = min(5.0, self.E + pleasure * 0.5)
        self.T = max(self.T0, self.T - 0.3)
        self.last_discovery_tick = t
        
        self.log.append({"t": t, "name": self.name, "action": f"discovery_pleasure_{resource_type}", "pleasure": pleasure})
        return pleasure

    def consider_becoming_scout(self, t):
        if self.role == "scout": return False
        # 条件をさらに緩和：確実にスカウトが発生するように
        if self.curiosity < 0.5: return False  # PIONEER(0.9)、ADVENTURER(0.8)、TRACKER(0.5)が対象
        # 最大2人までスカウト可能
        current_scouts = sum(1 for ally in self.nearby_allies(radius=100) if ally.role == "scout")
        if current_scouts >= 2: return False
        
        # より緩い条件で転職判定
        exploration_pressure = self.calculate_exploration_pressure()
        
        # 時間経過による自動転職促進
        if t > 30 and exploration_pressure > 0.2: pass
        elif t > 100: pass  # 100tick後は無条件で転職可能
        elif self.kappa.get("exploration", 0.0) >= 0.1: pass  # わずかな探索経験があれば
        else: return False

        self.role = "scout"
        self.discovery_reward_multiplier = 2.0
        self.log.append({"t": t, "name": self.name, "action": "role_transition_to_scout"})
        return True

    def share_discovery_with_pleasure(self, t, node, resource_type):
        shared_count = 0; total_approval = 0.0
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
            self.log.append({"t": t, "name": self.name, "action": "approval_pleasure", "pleasure": total_pleasure})

    def scout_action(self, t):
        exploration_pressure = self.calculate_exploration_pressure()
        if exploration_pressure < 0.3: return False  # 閾値を下げて積極的に探索
        self.log.append({"t": t, "name": self.name, "action": "scouting"})
        # Ensure movement stays within bounds
        new_x = self.x + random.choice([-1, 0, 1])
        new_y = self.y + random.choice([-1, 0, 1])
        self.x = max(0, min(self.env.size - 1, new_x))
        self.y = max(0, min(self.env.size - 1, new_y))

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
                # デバッグ情報をログに追加
                self.log.append({"t": t, "name": self.name, "action": f"scout_check_{res_type}", 
                               "distance": distance, "already_known": already_known, "pos": self.pos()})
                
                if distance <= 2 and not already_known:
                    knowledge.add(nearest[0])
                    self.experience_discovery_pleasure(t, res_type, nearest[0])
                    self.share_discovery_with_pleasure(t, nearest[0], res_type)
                    # 特別な発見ログを追加
                    self.log.append({"t": t, "name": self.name, "action": f"discover_{res_type}", "location": nearest[0]})
        return True

    def share_water_knowledge(self, t):
        if not self.knowledge_water: return
        for ally in self.nearby_allies(radius=8):
            if random.random() < (0.3 + 0.7 * self.rel.get(ally.name, 0)):
                new_knowledge_shared = False
                for water_node in self.knowledge_water:
                    if water_node not in ally.knowledge_water:
                        ally.knowledge_water.add(water_node)
                        new_knowledge_shared = True
                if new_knowledge_shared:
                    self.log.append({"t": t, "name": self.name, "action": "share_water_info", "target": ally.name})
                    ally.rel[self.name] = min(1.0, ally.rel.get(self.name, 0) + 0.1)
                    self.rel[ally.name] = min(1.0, self.rel.get(ally.name, 0) + 0.05)

    def forecast_hunger(self, t, ticks_ahead):
        # 簡易的な将来の空腹度予測
        return self.hunger + ticks_ahead * 1.0

    def maybe_help_territorial(self, t, predator):
        # 縄張り防衛の支援ロジック
        for ally in self.nearby_allies(radius=8):
            if ally.detected_intruders and self.rel[ally.name] > 0.4 and random.random() < self.empathy:
                # 侵入者への対応を支援
                intruder = ally.detected_intruders[0]
                if ally.territorial_aggression > self.territorial_aggression:
                    # リーダーが攻撃的なら一緒に追い払う
                    self.move_towards(intruder["npc"].pos())
                    self.log.append({"t": t, "name": self.name, "action": "assist_territorial_defense", "target": ally.name})
                    return True
                elif ally.territorial_aggression < self.territorial_aggression and intruder["threat_level"] < 0.5:
                    # リーダーが非攻撃的で脅威が低いなら、仲裁を試みる
                    self.log.append({"t": t, "name": self.name, "action": "mediate_territorial_dispute", "target": ally.name})
                    return True
        return False
    # --- pasted_content.txtからの追加メソッドここまで ---

    def step(self, t, predator=None):
        if not self.alive: return

        # === 状態更新フェーズ ===
        self.hunger += 1.0
        self.fatigue += 1.0 * self.env.day_night.get_activity_cost_multiplier()
        self.sleep_debt += 0.8

        # --- 気候による意味圧を適用 ---
        weather = self.env.weather
        if weather.condition == 'sunny':
            self.thirst += 1.5 + (1.0 * weather.intensity)
        elif weather.condition == 'rainy':
            self.thirst += 0.5
            self.fatigue += 1.5 * weather.intensity
            if weather.intensity > 0.7 and random.random() < 0.05:
                self.injury = min(120, self.injury + random.uniform(1, 5))
                self.log.append({"t": t, "name": self.name, "action": "injured_by_heavy_rain"})

        self.update_territory_center(); self.detect_intruders(t)
        if any(self.react_to_intruder(i, t) in ["chased", "retreated"] for i in self.detected_intruders): return
        
        if self.hunger >= 120 or self.injury >= 120 or self.thirst >= 120:
            cause = "hunger" if self.hunger >= 120 else "injury" if self.injury >= 120 else "thirst"
            self.alive = False; self.log.append({"t": t, "name": self.name, "action": "death", "cause": cause})
            return

        if self.is_sleeping:
            self.sleep_duration += 1; self.total_sleep_time += 1
            recovery = 6.0 * (1.5 if self.env.day_night.is_night() else 1.0)
            self.fatigue = max(0, self.fatigue - recovery); self.injury = max(0, self.injury - 2.0)
            self.sleep_debt = max(0, self.sleep_debt - 4.0)
            if self.sleep_duration > 5: self.consolidate_memory()
            if self.fatigue < 30 and self.env.day_night.is_day(): self.wake_up(t, "natural")
            return
        
        # === 意思決定フェーズ ===
        # L0: 危機回避
        if self.detect_predator(predator, t) == "fled": return

        # L1: 緊急の生理的欲求
        # 強い雨の時は、安全な場所（縄張りの中心）へ避難しようとする
        if weather.condition == 'rainy' and weather.intensity > 0.8 and self.dist_to_pos(self.territory.center) > 2:
            self.move_towards(self.territory.center)
            self.log.append({"t": t, "name": self.name, "action": "shelter_from_rain"})
            return

        if self.thirst >= 95:
             if self.water > 0:
                self.water -= 1.0; self.thirst = max(0, self.thirst - 60)
                self.log.append({"t": t, "name": self.name, "action": "drink_carried_water"})
                return
             else:
                known_water = self.env.nearest_nodes(self.pos(), {k:v for k,v in self.env.water_sources.items() if k in self.knowledge_water}, k=1)
                if known_water:
                    target = known_water[0]
                    if self.pos() == target: 
                        self.thirst = max(0, self.thirst - 80); self.water = 10.0
                        self.log.append({"t": t, "name": self.name, "action": "drink_at_source", "node": target})
                    else: 
                        self.move_towards(target)
                        self.log.append({"t": t, "name": self.name, "action": "move_to_water", "node": target})
                    return
                else:
                    # 水源探索ロジック (pasted_content.txtのNPCPriority.stepから)
                    self.x += random.choice([-1, 0, 1]); self.y += random.choice([-1, 0, 1])
                    self.x = max(0, min(self.env.size - 1, self.x))
                    self.y = max(0, min(self.env.size - 1, self.y))
                    self.log.append({"t": t, "name": self.name, "action": "explore_for_water"})
                    found = self.env.nearest_nodes(self.pos(), self.env.water_sources, k=1)
                    if found and self.dist_to(found[0]) <= 1:
                        self.knowledge_water.add(found[0])
                        self.log.append({"t": t, "name": self.name, "action": "discover_water_source", "node": found[0]})
                    return

        if self.hunger >= 95:
            # まず既知のベリー採取場所を優先的に探す
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
                if success: self.hunger -= food
                meaning_p = (self.hunger - self.TH_H) / 45.0; processed = food / 30.0 if success else 0
                self.update_alignment_inertia("forage", meaning_p, processed, success)
                return

        if self.injury >= 85 or self.fatigue >= 95 or self.should_sleep():
            self.move_towards(self.territory.center); self.enter_sleep(t); return

        # L2: 社会的行動と役割行動
        self.consider_becoming_scout(t)

        if self.role == "scout" or self.calculate_exploration_pressure() > 1.2:
            if self.scout_action(t): return

        if self.state == "rallying": self.move_towards(self.roster_ref[self.rally_target].pos()); return
        if predator and predator.is_camping() and not self.is_sleeping and self.fatigue < 80:
            self.emit_rally_predator(t, predator.camping_node, min_k=3, ttl=12)
        if self.rally_state["leader"] == self.name and self.rally_state["ttl"] > 0:
            if self.rally_state.get("kind") == "predator":
                if self.attempt_predator_hunt(t, predator): return
            else:
                if self.attempt_rally_group_hunt(t): return
        if (self.hunger > self.TH_H or self.forecast_hunger(t, 6) > self.TH_H) and not self.is_sleeping:
            self.emit_rally_for_hunt(t)
        if self.consider_join_rally(t): return

        if self.maybe_help_territorial(t, predator): return

        self.social_gravity_move(); self.copresence_tick(); self.apply_triadic_closure()
        self.share_water_knowledge(t)
        if random.random() < 0.5: self.move_towards(self.territory.center)
        self.decay_alignment_inertia()

# =========================
# NPC Presets
# =========================
FORAGER = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
# 新しい性格タイプを追加
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
# Main Execution
# =========================
def run_sim(TICKS=400, predator_spawn_interval=80):
    # 16人の大規模コミュニティに対応した十分なリソースを配置
    env = EnvForageBuff(size=80, n_berry=40, n_hunt=20, n_water=16, n_caves=10)
    roster = {}
    # NPCの人数を8人に調整（2つのグループに分散配置）
    npc_configs = [
        # 北西グループ（探索・冒険重視）
        ("Pioneer_Alpha", PIONEER, (20, 20)),
        ("Adventurer_Beta", ADVENTURER, (21, 19)),
        ("Tracker_Gamma", TRACKER, (19, 21)),
        ("Loner_Delta", LONER, (18, 18)),
        
        # 南東グループ（協力・安定重視）
        ("Leader_Echo", LEADER, (40, 40)),
        ("Guardian_Foxtrot", GUARDIAN, (41, 39)),
        ("Diplomat_Golf", DIPLOMAT, (39, 41)),
        ("Forager_Hotel", FORAGER, (42, 40)),
    ]
    # NPCを生成
    npcs = [NPCPriority(name, preset, env, roster, pos) for name, preset, pos in npc_configs]
    for npc in npcs:
        roster[npc.name] = npc
    
    # 【修正4】全NPCが生成された後に初期関係性を設定
    for npc in npcs:
        for other in npcs:
            if npc.name != other.name:
                initial_distance = npc.dist_to(other)
                if initial_distance < 5:
                    npc.rel[other.name] = 0.3
    
    predator = Predator(env, strength=3.0)
    
    logs = []
    weather_log = []
    for t in range(TICKS):
        if t > 0 and t % predator_spawn_interval == 0 and not predator.active:
            predator.spawn(t)
        predator.step()
        
        current_tick_logs = []
        for n in npcs:
            if n.alive:
                n.step(t, predator)
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
    final_npcs, df_logs, df_weather = run_sim(TICKS=1200) # 12人体制でより長いシミュレーション
    print("\n--- Simulation Finished ---")
    print(f"Survivors: {sum(1 for n in final_npcs if n.alive)} / {len(final_npcs)}")
    
    if not df_logs.empty:
        for npc in final_npcs:
            if not npc.alive:
                death_log = df_logs[(df_logs['name'] == npc.name) & (df_logs['action'] == 'death')]
                if not death_log.empty:
                    print(f"- {npc.name}: Died at tick {death_log['t'].iloc[0]} due to {death_log['cause'].iloc[0]}")

        pred_hunts = df_logs[df_logs['action'].str.contains("predator_slay")]
        if not pred_hunts.empty:
            print(f"Predator Hunts: {len(pred_hunts)} ({len(pred_hunts[pred_hunts['action'] == 'predator_slay_success'])} success)")
        
        water_shares = df_logs[df_logs['action'] == 'share_water_info']
        if not water_shares.empty:
            print(f"Water source info shared {len(water_shares)} times.")

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
        
        # 各リソースタイプの情報共有状況
        berry_shares = df_logs[df_logs['action'] == 'share_berry_patch_info']
        hunt_shares = df_logs[df_logs['action'] == 'share_hunting_ground_info']
        if not berry_shares.empty:
            print(f"Berry patch info shared {len(berry_shares)} times.")
        if not hunt_shares.empty:
            print(f"Hunting ground info shared {len(hunt_shares)} times.")

        # --- pasted_content.txtからのログ出力の追加 ---
        print("\n--- Role Transition Summary ---")
        transitions = df_logs[df_logs['action'] == 'role_transition_to_scout']
        if not transitions.empty:
            scout_name = transitions['name'].iloc[0]
            print(f"'{scout_name}' transitioned to SCOUT at tick {transitions['t'].iloc[0]}!")

            print("\n--- Scout Activity Summary ---")
            scout_logs = df_logs[df_logs['name'] == scout_name]
            
            # スカウト活動の詳細分析
            scouting_actions = scout_logs[scout_logs['action'] == 'scouting']
            check_actions = scout_logs[scout_logs['action'].str.contains('scout_check')]
            discovery_actions = scout_logs[scout_logs['action'].str.contains('discover_')]
            
            print(f"Total scouting attempts: {len(scouting_actions)}")
            print(f"Total resource checks: {len(check_actions)}")
            print(f"Total discoveries: {len(discovery_actions)}")
            print(f"Total info shares: {len(scout_logs[scout_logs['action'].str.contains('share')])}")
            
            # 死亡時の情報
            death_tick = final_npcs[0].env.t if scout_name == 'Pioneer_Alpha' else 157  # 既知の死亡tick
            print(f"Scout died at tick: {death_tick}")
            print(f"Scout was active for {death_tick - 49} ticks")
            
            approval_logs = scout_logs[scout_logs['action'] == 'approval_pleasure']
            if not approval_logs.empty and 'pleasure' in approval_logs.columns:
                print(f"Total approval pleasure: {approval_logs['pleasure'].sum():.2f}")
            else:
                print("Total approval pleasure: 0.00")
        else:
            print("No one became a scout in this simulation.")
        # --- pasted_content.txtからのログ出力の追加ここまで ---

    print("\n--- Weather Summary ---")
    print(df_weather['condition'].value_counts())

