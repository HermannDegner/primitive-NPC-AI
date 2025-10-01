import random, math
from collections import defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

random.seed(42); np.random.seed(42)

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
# Predator (PATCH 2-1: Updated)
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
    # --- 水場・言語要素の追加 ---
    def __init__(self, size=40, n_berry=18, n_hunt=10, n_water=5):
        self.size = size
        self.berries = {}
        for _ in range(n_berry):
            x, y = random.randrange(size), random.randrange(size)
            self.berries[(x, y)] = {"abundance": random.uniform(0.3, 0.7), "regen": random.uniform(0.004, 0.015)}
        self.huntzones = {}
        for _ in range(n_hunt):
            x, y = random.randrange(size), random.randrange(size)
            self.huntzones[(x, y)] = {"base_success": random.uniform(0.20, 0.50), "danger": random.uniform(0.25, 0.65)}
        
        # --- 水場・言語要素の追加：水場を環境に追加 ---
        self.water_sources = {}
        for _ in range(n_water):
            x, y = random.randrange(size), random.randrange(size)
            self.water_sources[(x,y)] = {"quality": random.uniform(0.5, 1.0)}

        self.t = 0
        self.day_night = DayNightCycle(day_length=48)
        
    def step(self):
        for v in self.berries.values():
            v["abundance"] = min(1.0, v["abundance"] + v["regen"] * (1.0 - v["abundance"]))
        for v in self.huntzones.values():
            v["base_success"] = float(np.clip(v["base_success"] + np.random.normal(0, 0.01), 0.03, 0.8))
        self.t += 1
        self.day_night.step()
        
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
        success = random.random() < p
        if success:
            self.berries[node]["abundance"] = max(0.0, self.berries[node]["abundance"] - random.uniform(0.2, 0.4))
            food = random.uniform(14, 26) * (0.6 + abundance / 2)
        else:
            food = 0.0
        risk = 0.05
        return success, food, risk, p

# =========================
# Territory & Base NPC
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

class NPCWithTerritory:
    def __init__(self, name, preset, env, roster_ref, start_pos,
                 horizon=8, horizon_rally=6, rally_ttl=10):
        self.name = name; self.env = env; self.roster_ref = roster_ref
        self.x, self.y = start_pos
        
        # --- 水場・言語要素の追加：「渇き」と「水」の属性を追加 ---
        self.hunger = 50.0; self.thirst = 30.0; self.fatigue = 30.0; self.injury = 0.0
        self.water = 5.0 

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
        
        # --- 水場・言語要素の追加：「渇き」の閾値を追加 ---
        self.TH_H = 55.0; self.TH_T = 60.0 # Thirst threshold

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

        # --- 水場・言語要素の追加：知識（構造）として水場の場所を記憶 ---
        self.knowledge_water = set()
        # 初期知識として最も近い水場を１つ知っている
        initial_water = self.env.nearest_nodes(self.pos(), self.env.water_sources, k=1)
        if initial_water:
            self.knowledge_water.add(initial_water[0])


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
    def move_towards(self, target):
        tx, ty = target
        self.x += (1 if tx > self.x else -1 if tx < self.x else 0)
        self.y += (1 if ty > self.y else -1 if ty < self.y else 0)
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
                escape_x = self.territory.center[0] + (self.x - predator.x) * 2
                escape_y = self.territory.center[1] + (self.y - predator.y) * 2
                self.move_towards((max(0, min(self.env.size - 1, int(escape_x))), max(0, min(self.env.size - 1, int(escape_y)))))
                self.log.append({"t": t, "name": self.name, "action": "flee_from_predator"})
                return "fled"
            else:
                self.log.append({"t": t, "name": self.name, "action": "alert_predator"})
                return "alert"
        return None
    def help_utility(self, o):
        need = max(0,(o.hunger-55)/40)+max(0,(o.injury-15)/50)+max(0,(o.fatigue-70)/50)
        myneed = max(0,(self.hunger-55)/40)+max(0,(self.injury-15)/50)+max(0,(self.fatigue-70)/50)
        return (need * (0.35*self.empathy + 0.4*self.rel[o.name])) - 0.4*myneed
    def help_utility_territorial(self, o):
        u = self.help_utility(o)
        if self.territory.contains(o.pos()): u += 0.3 * self.group_loyalty
        if o.name in self.invited_guests: u += 0.2
        return u
    def help_utility_with_threat(self, o, predator):
        u = self.help_utility_territorial(o)
        if predator and predator.active and min(predator.distance_to(self), predator.distance_to(o)) < 10:
            u += 0.3 * (1 - min(predator.distance_to(self), predator.distance_to(o)) / 10)
            if self.territory.contains(o.pos()): u += 0.2
        return u
    def maybe_help_territorial(self, t, predator=None):
        allies = self.nearby_allies(radius=3)
        if not allies: return False
        best = max(allies, key=lambda o: self.help_utility_with_threat(o, predator) if predator else self.help_utility_territorial(o))
        bestu = self.help_utility_with_threat(best, predator) if predator else self.help_utility_territorial(best)
        if best and bestu > 0.05 and self.hunger < 85 and best.hunger > 75:
            delta = 25.0
            self.hunger = min(120.0, self.hunger + 6.0); best.hunger = max(0.0, best.hunger - delta)
            self.rel[best.name] += 0.08; best.rel[self.name] += 0.04
            self.update_kappa("help", True, delta * 0.5)
            if self.territory.contains(self.pos()): self.territory.memory["helped_here"] += 1
            self.log.append({"t": t, "name": self.name, "action": "share_food_territorial", "target": best.name})
            return True
        return False
    def forecast_hunger(self, t_now, horizon): return min(120.0, self.hunger + 1.8 * horizon)

    # --- 水場・言語要素の追加：水場情報共有のメソッド ---
    def share_water_knowledge(self, t):
        # 自分の知っている水場情報を近くの仲間に教える
        if not self.knowledge_water:
            return
        
        shared_info = False
        for ally in self.nearby_allies(radius=3):
            # 自分が知っていて、相手が知らない情報を探す
            new_info_for_ally = self.knowledge_water - ally.knowledge_water
            if new_info_for_ally:
                info_to_share = random.choice(list(new_info_for_ally))
                ally.knowledge_water.add(info_to_share)
                self.rel[ally.name] = min(1.0, self.rel[ally.name] + 0.05)
                ally.rel[self.name] = min(1.0, ally.rel[self.name] + 0.03)
                shared_info = True
                self.log.append({"t": t, "name": self.name, "action": "share_water_info", "target": ally.name, "info": info_to_share})
        
        if shared_info:
            self.update_kappa("social", True, 5.0)


class NPCPriority(NPCWithTerritory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.share_threshold = 50.0
        self.store_fraction  = 0.6
        self.rally_target = None

    def emit_rally_predator(self, t, node, min_k=3, ttl=12):
        self.rally_state = {"leader": self.name, "ttl": ttl, "node": node, "min_k": min_k, "kind": "predator"}
        self.log.append({"t": t, "name": self.name, "action": "rally_predator_hunt", "node": node})

    def attempt_predator_hunt(self, t, predator):
        rs = self.rally_state
        if not (rs and rs.get("leader")==self.name and rs.get("ttl",0)>0 and rs.get("kind")=="predator"): return False
        if not (predator and predator.is_camping()): return False

        node = rs["node"] or predator.camping_node
        party = [self] + [ally for ally in self.nearby_allies(radius=4) if getattr(ally, "rally_target", None) == self.name and ally.state == "rallying"]
        if len(party) < rs.get("min_k",3): return False

        for m in party: m.move_towards(node)

        k = len(party)
        cps = [m.combat_power(group_bonus=0.08*np.log1p(k-1) + 0.12*max(0.0, np.mean([m.rel.get(o.name,0.0) for o in party if o is not m]) if k>1 else 0.0)) for m in party]
        team_cp = np.sum(cps)
        predator_power = 4.0 * predator.strength * (1.0 + 0.05*(k-1))
        ratio = team_cp / predator_power
        p_slay = float(np.clip(0.25 + 0.15*np.tanh((ratio-1.0)*0.9), 0.10, 0.85))
        inj_prob = float(np.clip(0.45 * (1.0 - 0.45*np.tanh(ratio-1.0)) * (0.85 - 0.07*(k-3)), 0.15, 0.95))

        success = (random.random() < p_slay)
        if success:
            predator.despawn()
            total_food = 25.0 * (1.0 + 0.15*(k-1))
            shares = np.array([1.0]*k) / k * total_food
            for m, share in zip(party, shares):
                if random.random() < inj_prob: m.injury = min(120, m.injury + random.uniform(5, 18))
                before = m.hunger; m.hunger = max(0.0, m.hunger - share)
                rem = max(0.0, share - (before - m.hunger))
                if rem > 0: m.food_store = min(m.max_store, m.food_store + 0.6*rem)
                m.gain_combat_xp(6.0 + 3.0*predator.strength)
                m.update_kappa("hunt", True, 0.8*share)
                m.update_alignment_inertia("predator", 1.0, 0.9, True)
            for i in range(k):
                for j in range(i+1, k):
                    a,b = party[i], party[j]
                    a.rel[b.name] += 0.22; b.rel[a.name] += 0.22
            self.log.append({"t": t, "name": self.name, "action": "predator_slay_success", "party": [m.name for m in party]})
        else:
            for m in party:
                if random.random() < inj_prob: m.injury = min(120, m.injury + random.uniform(8, 25))
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
                meaning_p = max(0.0, (m.hunger - m.TH_H) / (100 - m.TH_H))
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

    def step(self, t, predator=None):
        if not self.alive: return
        
        # --- 状態更新フェーズ ---
        # 欲求の増加
        self.hunger += 1.0
        self.thirst += 1.5 # 渇きは空腹より速く進行
        self.fatigue += 1.0 * self.env.day_night.get_activity_cost_multiplier()
        self.sleep_debt += 0.8

        self.update_territory_center(); self.detect_intruders(t)
        if any(self.react_to_intruder(i, t) in ["chased", "retreated"] for i in self.detected_intruders): return
        
        # 死亡判定
        if self.hunger >= 120 or self.injury >= 120 or self.thirst >= 120:
            cause = "hunger" if self.hunger >= 120 else "injury" if self.injury >= 120 else "thirst"
            self.alive = False; self.log.append({"t": t, "name": self.name, "action": "death", "cause": cause})
            return

        # 睡眠中の処理
        if self.is_sleeping:
            self.sleep_duration += 1; self.total_sleep_time += 1
            recovery = 6.0 * (1.5 if self.env.day_night.is_night() else 1.0)
            self.fatigue = max(0, self.fatigue - recovery); self.injury = max(0, self.injury - 2.0)
            self.sleep_debt = max(0, self.sleep_debt - 4.0)
            if self.sleep_duration > 5: self.consolidate_memory()
            if self.fatigue < 30 and self.env.day_night.is_day(): self.wake_up(t, "natural")
            return
        
        # --- 意思決定フェーズ（優先度順） ---

        # L0: 危機回避
        if self.detect_predator(predator, t) == "fled": return

        # L1: 緊急の生理的欲求（Hard Guardrails）
        if self.thirst >= 95:
             # 水を飲むか、水場へ移動する
            if self.water > 0:
                self.water -= 1.0; self.thirst = max(0, self.thirst - 60)
                self.log.append({"t": t, "name": self.name, "action": "drink_carried_water"})
                return
            else:
                target_water = self.env.nearest_nodes(self.pos(), {k:v for k,v in self.env.water_sources.items() if k in self.knowledge_water}, k=1)
                if target_water:
                    target = target_water[0]
                    if self.pos() == target:
                        self.thirst = max(0, self.thirst - 80); self.water = 10.0
                        self.log.append({"t": t, "name": self.name, "action": "drink_at_source", "node": target})
                    else:
                        self.move_towards(target)
                        self.log.append({"t": t, "name": self.name, "action": "move_to_water", "node": target})
                    return
        if self.hunger >= 95:
            # 食料を探す（簡略化）
            nodes = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
            if nodes: self.move_towards(nodes[0]); self.env.forage(self.pos(), nodes[0]); return
        if self.injury >= 85 or self.fatigue >= 95 or self.should_sleep():
            self.move_towards(self.territory.center); self.enter_sleep(t); return

        # L2: 協調行動（Cooperative Context）
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

        # L3: 個人の欲求充足（Individual Needs）
        if self.thirst > self.TH_T:
            # L1と同様のロジックだが、より探索的
            if self.water > 0:
                self.water -= 1.0; self.thirst = max(0, self.thirst - 60)
                self.log.append({"t": t, "name": self.name, "action": "drink_carried_water"})
            else:
                # 知識ベースまたは探索
                known_sources = {k:v for k,v in self.env.water_sources.items() if k in self.knowledge_water}
                target_water = self.env.nearest_nodes(self.pos(), known_sources, k=1)
                if target_water:
                     target = target_water[0]
                     if self.pos() == target:
                         self.thirst = max(0, self.thirst - 80); self.water = 10.0
                         self.log.append({"t": t, "name": self.name, "action": "drink_at_source", "node": target})
                     else:
                         self.move_towards(target)
                         self.log.append({"t": t, "name": self.name, "action": "move_to_water", "node": target})
                else: # 知識がない場合、ランダムウォークで探索
                    self.x += random.choice([-1, 0, 1]); self.y += random.choice([-1, 0, 1])
                    self.log.append({"t": t, "name": self.name, "action": "explore_for_water"})
                    # 発見判定
                    found = self.env.nearest_nodes(self.pos(), self.env.water_sources, k=1)
                    if found and self.dist_to(found[0]) <= 1:
                        self.knowledge_water.add(found[0])
                        self.log.append({"t": t, "name": self.name, "action": "discover_water_source", "node": found[0]})

            return # 水関連の行動をしたらターン終了
        
        if self.hunger > self.TH_H:
            nodes = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
            if nodes:
                self.move_towards(nodes[0])
                success, food, _, _ = self.env.forage(self.pos(), nodes[0])
                if success: self.hunger -= food
                meaning_p = (self.hunger - self.TH_H) / 45.0; processed = food / 30.0 if success else 0
                self.update_alignment_inertia("forage", meaning_p, processed, success)
                return
        if self.maybe_help_territorial(t, predator): return

        # L4: 社会的行動と巡回（Social & Patrol）
        self.social_gravity_move(); self.copresence_tick(); self.apply_triadic_closure()
        self.share_water_knowledge(t) # <<< 言語による情報共有
        if random.random() < 0.5: self.move_towards(self.territory.center)
        self.decay_alignment_inertia()


# =========================
# NPC Presets
# =========================
FORAGER = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
SCAVENGER = {"risk_tolerance": 0.3, "curiosity": 0.6, "avoidance": 0.7, "stamina": 0.5, "empathy": 0.5}
NOMAD = {"risk_tolerance": 0.7, "curiosity": 0.8, "avoidance": 0.1, "stamina": 0.9, "empathy": 0.3}
MEDIATOR = {"risk_tolerance": 0.3, "curiosity": 0.5, "avoidance": 0.5, "stamina": 0.6, "empathy": 0.9}
HERMIT = {"risk_tolerance": 0.1, "curiosity": 0.2, "avoidance": 0.9, "stamina": 0.4, "empathy": 0.2}
AGGRESSOR = {"risk_tolerance": 0.9, "curiosity": 0.4, "avoidance": 0.1, "stamina": 0.8, "empathy": 0.3}
COLLECTOR = {"risk_tolerance": 0.4, "curiosity": 0.7, "avoidance": 0.6, "stamina": 0.7, "empathy": 0.6}

# =========================
# Main Execution
# =========================
def run_sim(TICKS=400, predator_spawn_interval=80):
    env = EnvForageBuff(size=40, n_berry=18, n_hunt=10, n_water=5)
    roster = {}
    npc_configs = [
        ("Forager_A", FORAGER, (15, 15)), ("Tracker_B", TRACKER, (25, 15)),
        ("Pioneer_C", PIONEER, (20, 25)), ("Guardian_D", GUARDIAN, (10, 20)),
        ("Scavenger_E", SCAVENGER, (30, 20)), ("Nomad_F", NOMAD, (5, 5)),
        ("Mediator_G", MEDIATOR, (20, 20)), ("Hermit_H", HERMIT, (35, 35)),
        ("Aggressor_I", AGGRESSOR, (10, 30)), ("Collector_J", COLLECTOR, (30, 10)),
        ("Forager_K", FORAGER, (15, 30)), ("Pioneer_L", PIONEER, (25, 25)),
    ]
    npcs = [NPCPriority(name, preset, env, roster, pos) for name, preset, pos in npc_configs]
    for npc in npcs: roster[npc.name] = npc
    predator = Predator(env, strength=3.0)
    
    logs = []
    for t in range(TICKS):
        if t > 0 and t % predator_spawn_interval == 0 and not predator.active:
            predator.spawn(t)
        predator.step()
        
        # --- 水場・言語要素の追加：ログ収集を改善 ---
        current_tick_logs = []
        for n in npcs:
            if n.alive:
                n.step(t, predator)
                if n.log:
                    current_tick_logs.extend(n.log)
                    n.log = [] # ログをクリア
        
        if current_tick_logs:
            logs.extend(current_tick_logs)
            
        env.step()
        
        # 生存者がいなくなったら終了
        if not any(n.alive for n in npcs):
            print(f"--- {t} tick: 全員が力尽きた ---")
            break

    return npcs, pd.DataFrame(logs)

if __name__ == "__main__":
    final_npcs, df_logs = run_sim()
    print("\n--- Simulation Finished ---")
    print(f"Survivors: {sum(1 for n in final_npcs if n.alive)} / {len(final_npcs)}")
    
    if not df_logs.empty:
        pred_hunts = df_logs[df_logs['action'].str.contains("predator_slay")]
        if not pred_hunts.empty:
            print(f"Predator Hunts: {len(pred_hunts)} ({len(pred_hunts[pred_hunts['action'] == 'predator_slay_success'])} success)")
        
        water_shares = df_logs[df_logs['action'] == 'share_water_info']
        if not water_shares.empty:
            print(f"Water source info shared {len(water_shares)} times.")