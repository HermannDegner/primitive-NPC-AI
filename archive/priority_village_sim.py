import random, math
from collections import defaultdict
import numpy as np
import pandas as pd

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
    def pos(self):
        return (self.x, self.y)
    def spawn(self, t):
        self.x = random.randrange(self.env.size)
        self.y = random.randrange(self.env.size)
        self.active = True
        self.duration = 0
        return self.pos()
    def despawn(self):
        self.active = False
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
    def distance_to(self, npc):
        return abs(self.x - npc.x) + abs(self.y - npc.y)

# =========================
# Environment (with slightly buffed forage)
# =========================
class EnvForageBuff:
    def __init__(self, size=40, n_berry=18, n_hunt=10):
        self.size = size
        self.berries = {}
        for _ in range(n_berry):
            x, y = random.randrange(size), random.randrange(size)
            self.berries[(x, y)] = {
                "abundance": random.uniform(0.3, 0.7),
                "regen": random.uniform(0.004, 0.015)
            }
        self.huntzones = {}
        for _ in range(n_hunt):
            x, y = random.randrange(size), random.randrange(size)
            self.huntzones[(x, y)] = {
                "base_success": random.uniform(0.20, 0.50),
                "danger": random.uniform(0.25, 0.65)
            }
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
# Base NPC with territory, pantry, social
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
        self.hunger = 50.0; self.fatigue = 30.0; self.injury = 0.0
        self.alive = True; self.state = "Awake"
        # Alignment / heat
        self.kappa = defaultdict(lambda: 0.1); self.kappa_min = 0.05
        self.E = 0.0; self.T = 0.3
        self.G0 = 0.5; self.g = 0.7; self.eta = 0.3
        self.lambda_forget = 0.02; self.rho = 0.1; self.alpha = 0.6; self.beta_E = 0.15
        # leap params
        self.Theta0 = 1.0; self.a1 = 0.5; self.a2 = 0.4; self.h0 = 0.2; self.gamma = 0.8
        self.T0 = 0.3; self.c1 = 0.5; self.c2 = 0.6
        # traits
        p = preset
        self.risk_tolerance = p["risk_tolerance"]; self.curiosity = p["curiosity"]
        self.avoidance = p["avoidance"]; self.stamina = p["stamina"]; self.empathy = p.get("empathy",0.6)
        self.TH_H = 55.0
        self.rel = defaultdict(float); self.help_debt = defaultdict(float)
        # sleep
        self.sleep_debt = 0.0; self.is_sleeping = False; self.sleep_duration = 0
        self.total_sleep_time = 0; self.sleep_cycles = 0
        # territory
        initial_radius = 5 + self.avoidance * 3
        self.territory = Territory(owner=self.name, center=self.pos(), radius=initial_radius)
        self.territorial_aggression = 0.3 + (1 - self.empathy) * 0.4
        self.group_loyalty = 0.5 + self.empathy * 0.3
        self.detected_intruders = []
        self.invited_guests = set()
        self.log = []
        self.boredom = 0.0
        # pantry
        self.max_store = 120.0
        self.food_store = 0.0
        # rally
        self.rally_state = {"leader": None, "ttl": 0, "node": None, "min_k": 2}
        self.rally_ttl_default = rally_ttl
        self.horizon = horizon
        self.horizon_rally = horizon_rally
        # social extras
        self.cohesion = 0.0
        self.village_affinity = 0.0
        self.last_social_tick = 0

    # --- utils ---
    def pos(self):
        return (self.x, self.y)
    def dist_to(self, o):
        return abs(self.x - o.x) + abs(self.y - o.y)
    def move_towards(self, target):
        tx, ty = target
        self.x += (1 if tx > self.x else -1 if tx < self.x else 0)
        self.y += (1 if ty > self.y else -1 if ty < self.y else 0)
    def nearby_allies(self, radius=3):
        return [o for on, o in self.roster_ref.items() if on != self.name and o.alive and self.dist_to(o) <= radius]

    # --- alignment/heat ---
    def alignment_flow(self, action_type, meaning_pressure):
        kappa = self.kappa[action_type]
        j = (self.G0 + self.g * kappa) * meaning_pressure
        return j
    def update_kappa(self, action_type, success, reward):
        kappa = self.kappa[action_type]
        if success:
            work = self.eta * reward
        else:
            work = -self.rho * (kappa ** 2)
        decay = self.lambda_forget * (kappa - self.kappa_min)
        self.kappa[action_type] = max(self.kappa_min, kappa + work - decay)
    def update_heat(self, meaning_pressure, processed_amount):
        unprocessed = max(0, meaning_pressure - processed_amount)
        self.E += self.alpha * unprocessed - self.beta_E * self.E
        self.E = max(0, self.E)

    # --- sleep ---
    def get_personal_sleep_pressure(self):
        env_pressure = self.env.day_night.get_sleep_pressure()
        debt_pressure = min(1.0, self.sleep_debt / 100)
        fatigue_pressure = min(1.0, self.fatigue / 100)
        total = (env_pressure * 0.5 + debt_pressure * 0.3 + fatigue_pressure * 0.2)
        return total
    def should_sleep(self):
        if self.is_sleeping: return True
        pressure = self.get_personal_sleep_pressure()
        if self.sleep_debt > 150: return True
        if self.fatigue > 90: return True
        if self.env.day_night.is_night() and self.fatigue > 60: return True
        if pressure > 0.7 and self.hunger < 85: return True
        return False
    def enter_sleep(self, t):
        self.is_sleeping = True
        self.sleep_duration = 0
        self.state = "Sleeping"
        self.sleep_cycles += 1
    def consolidate_memory(self):
        if len(self.kappa) < 2: return
        actions = list(self.kappa.keys()); values = list(self.kappa.values())
        mean_kappa = np.mean(values)
        for action in actions:
            if self.kappa[action] > mean_kappa:
                self.kappa[action] = min(1.0, self.kappa[action] + 0.05)
            else:
                self.kappa[action] = max(self.kappa_min, self.kappa[action] - self.lambda_forget * 3)
    def wake_up(self, t, reason):
        self.is_sleeping = False
        self.state = "Awake"
        if reason == "natural":
            self.T = self.T0; self.boredom = 0.0
        self.sleep_duration = 0

    # --- territory / intruders ---
    def update_territory_center(self):
        current_pos = self.pos(); cx, cy = self.territory.center
        new_cx = cx * 0.95 + current_pos[0] * 0.05
        new_cy = cy * 0.95 + current_pos[1] * 0.05
        self.territory.center = (new_cx, new_cy)
    def detect_intruders(self, t):
        self.detected_intruders = []
        allies = self.nearby_allies(radius=int(self.territory.radius))
        for ally in allies:
            if ally.name in self.invited_guests: continue
            if self.territory.contains(ally.pos()):
                threat = self.calculate_threat(ally)
                self.detected_intruders.append({"name": ally.name, "npc": ally, "detected_at": t, "threat_level": threat})
    def calculate_threat(self, other_npc):
        base_threat = 0.3
        relation = self.rel[other_npc.name]
        if relation < 0: base_threat += abs(relation) * 0.5
        elif relation > 0.5: base_threat -= 0.3
        base_threat += other_npc.territorial_aggression * 0.3
        if self.hunger > 70 and other_npc.hunger > 70: base_threat += 0.4
        return max(0, min(1.0, base_threat))
    def react_to_intruder(self, intruder_data, t):
        threat = intruder_data["threat_level"]; other_npc = intruder_data["npc"]
        if threat < 0.3:
            if self.empathy > 0.7 and random.random() < 0.3:
                self.invited_guests.add(other_npc.name)
                self.rel[other_npc.name] += 0.1; other_npc.rel[self.name] += 0.1
                self.log.append({"t": t, "name": self.name, "action": "invite_to_territory", "target": other_npc.name, "threat_level": round(threat, 2)})
                return "invited"
        elif threat < 0.6:
            edge_x = self.territory.center[0] + self.territory.radius * 0.8
            edge_y = self.territory.center[1]
            self.move_towards((int(edge_x), int(edge_y)))
            self.rel[other_npc.name] -= 0.05
            self.log.append({"t": t, "name": self.name, "action": "warning_distance", "target": other_npc.name, "threat_level": round(threat, 2)})
            return "warned"
        else:
            if self.territorial_aggression > other_npc.territorial_aggression:
                other_npc.E = min(5.0, other_npc.E + 0.5)
                other_npc.rel[self.name] -= 0.15; self.rel[other_npc.name] -= 0.1
                self.log.append({"t": t, "name": self.name, "action": "chase_away", "target": other_npc.name, "threat_level": round(threat, 2)})
                return "chased"
            else:
                escape_x = self.territory.center[0] - (other_npc.x - self.territory.center[0])
                escape_y = self.territory.center[1] - (other_npc.y - self.territory.center[1])
                self.move_towards((max(0, min(self.env.size-1, int(escape_x))), max(0, min(self.env.size-1, int(escape_y)))))
                self.E = min(5.0, self.E + 0.3)
                self.log.append({"t": t, "name": self.name, "action": "retreat_from_territory", "target": other_npc.name, "threat_level": round(threat, 2)})
                return "retreated"
        return "ignored"

    # --- predator awareness ---
    def detect_predator(self, predator, t):
        if not predator.active: return None
        dist = predator.distance_to(self)
        if dist <= 10:
            threat_level = predator.strength * (1 - dist/10)
            self.E = min(5.0, self.E + threat_level * 0.3)
            allies = self.nearby_allies(radius=5); warned_count = 0
            for ally in allies:
                self.rel[ally.name] += 0.05; ally.rel[self.name] += 0.05
                ally.E = min(5.0, ally.E + threat_level * 0.2); warned_count += 1
            if dist <= 3:
                escape_x = self.territory.center[0] + (self.x - predator.x) * 2
                escape_y = self.territory.center[1] + (self.y - predator.y) * 2
                self.move_towards((max(0, min(self.env.size-1, int(escape_x))), max(0, min(self.env.size-1, int(escape_y)))))
                self.log.append({"t": t, "name": self.name, "action": "flee_from_predator", "distance": dist, "at_home": self.territory.contains(self.pos())})
                return "fled"
            else:
                self.log.append({"t": t, "name": self.name, "action": "alert_predator", "distance": dist, "warned_allies": warned_count})
                return "alert"
        return None

    # --- help utilities / sharing ---
    def help_utility(self, o):
        need = max(0, (o.hunger - 55) / 40) + max(0, (o.injury - 15) / 50) + max(0, (o.fatigue - 70) / 50)
        base = 0.35 * self.empathy + 0.4 * self.rel[o.name] + 0.35 * self.help_debt[o.name]
        myneed = max(0, (self.hunger - 55) / 40) + max(0, (self.injury - 15) / 50) + max(0, (self.fatigue - 70) / 50)
        return need * base - 0.4 * myneed
    def help_utility_territorial(self, o):
        base_utility = self.help_utility(o)
        if self.territory.contains(o.pos()): base_utility += 0.3 * self.group_loyalty
        if o.name in self.invited_guests: base_utility += 0.2
        return base_utility
    def help_utility_with_threat(self, o, predator):
        base_utility = self.help_utility_territorial(o)
        if predator and predator.active:
            threat_distance = min(predator.distance_to(self), predator.distance_to(o))
            if threat_distance < 10:
                base_utility += 0.3 * (1 - threat_distance/10)
                if self.territory.contains(o.pos()): base_utility += 0.2
        return base_utility
    def maybe_help_territorial(self, t, predator=None):
        allies = self.nearby_allies(radius=3)
        if not allies: return False
        best = None; bestu = 0.0
        for o in allies:
            u = self.help_utility_with_threat(o, predator) if predator else self.help_utility_territorial(o)
            if u > bestu: bestu = u; best = o
        if best and bestu > 0.05:
            if self.hunger < 85 and best.hunger > 75:
                delta = 25.0
                self.hunger = min(120.0, self.hunger + 6.0)
                best.hunger = max(0.0, best.hunger - delta)
                self.rel[best.name] += 0.08; best.rel[self.name] += 0.04
                best.help_debt[self.name] += 0.2
                self.update_kappa("help", True, delta * 0.5)
                if self.territory.contains(self.pos()):
                    self.territory.memory["helped_here"] += 1
                self.log.append({"t": t, "name": self.name, "action": "share_food_territorial", "target": best.name})
                return True
        return False

    # --- forecast hunger (simple) ---
    def forecast_hunger(self, t_now, horizon):
        return min(120.0, self.hunger + 1.8 * horizon)

# =========================
# Rally hunting (big rewards + cohesion effects)
# =========================
RALLY_BONUS = 0.70
JOIN_RADIUS = 8
JOIN_NEAR   = 3

class NPCRallyHunt(NPCWithTerritory):
    def emit_rally_for_hunt(self, t, hunt_node=None, min_k=2, ttl=10):
        self.rally_state = {"leader": self.name, "ttl": ttl, "node": hunt_node, "min_k": min_k}
        self.log.append({"t": t, "name": self.name, "action": "rally_for_hunt", "node": hunt_node, "ttl": ttl})
    def consider_join_rally(self, t):
        joined = False
        for ally in self.nearby_allies(radius=JOIN_RADIUS):
            rs = getattr(ally, "rally_state", None)
            if not rs: continue
            if rs.get("leader") == ally.name and rs.get("ttl",0) > 0:
                need_pressure = max(0.0, (self.hunger - self.TH_H) / (100 - self.TH_H))
                base = self.alignment_flow("hunt", need_pressure)
                u = base + RALLY_BONUS + 0.35 * self.rel[ally.name] - 0.008 * self.fatigue + 0.4 * self.cohesion + 0.4 * self.village_affinity
                if u >= 0.0 and not self.is_sleeping:
                    target = rs["node"] if rs["node"] else ally.pos()
                    self.move_towards(target)
                    self.state = "rallying"; self.rally_target = ally.name
                    self.log.append({"t": t, "name": self.name, "action": "join_rally", "leader": ally.name, "u": float(u)})
                    joined = True
                    break
        return joined
    def attempt_rally_group_hunt(self, t):
        rs = self.rally_state
        if not rs or rs.get("leader") != self.name or rs.get("ttl",0) <= 0:
            return False
        party = [self]
        for ally in self.nearby_allies(radius=JOIN_NEAR):
            if getattr(ally, "rally_target", None) == self.name and ally.state == "rallying" and ally.alive and not ally.is_sleeping:
                party.append(ally)
        if len(party) < rs.get("min_k", 2):
            return False
        # choose node
        if rs["node"] is None:
            nodes = self.env.nearest_nodes(self.pos(), self.env.huntzones, k=1)
            if not nodes: return False
            node = nodes[0]
        else:
            node = rs["node"]
        # probabilities
        hz = self.env.huntzones[node]
        light = self.env.day_night.get_light_level()
        tw = 1 - abs(light - 0.4)/0.6
        light_mod = 0.35 + 0.65 * max(0.0, tw)
        dist = abs(self.x - node[0]) + abs(self.y - node[1])
        dist_term = 0.25 * max(0, 1 - dist/16)
        p_solo = float(np.clip(hz["base_success"]*light_mod + dist_term, 0.03, 0.95))
        k = len(party); alpha = 0.70
        p_group = 1 - (1 - p_solo)**(1 + alpha*(k-1))
        p_group = float(np.clip(p_group, 0.10, 0.99))
        for m in party: m.move_towards(node)
        base_inj_prob = 0.15 + 0.7 * hz["danger"]
        size_discount = 0.55 - 0.08 * (k-2)
        inj_prob = max(0.20, min(0.95, base_inj_prob * max(0.35, size_discount)))
        success = random.random() < p_group
        if success:
            base_food = random.uniform(45, 85) * (0.85 + hz["base_success"])  # big game
            total_food = base_food * (1 + 0.75*(k-1))
        else:
            total_food = 0.0
        needs = np.array([max(1.0, m.hunger) for m in party])
        shares = (needs / needs.sum()) * total_food if total_food > 0 else np.zeros(k)
        injuries = []
        for m, share in zip(party, shares):
            inj = 0.0
            if random.random() < inj_prob:
                base_injury = random.uniform(2, 10) * (0.6 + 0.8*hz["danger"])
                if not success: base_injury *= 1.15
                inj = 0.65 * base_injury
                m.injury = min(120, m.injury + inj)
            if success and share > 0:
                before = m.hunger
                m.hunger = max(0.0, m.hunger - share)
                eaten = before - m.hunger
                rem = max(0.0, share - eaten)
                if rem > 0:
                    m.food_store = min(m.max_store, m.food_store + rem*0.6)
                m.fatigue = min(120, max(0, m.fatigue - share * 0.16))
                m.update_kappa("hunt", True, share * 1.3)
            else:
                m.update_kappa("hunt", False, 0)
            injuries.append(inj)
        # cooperative joy / cohesion
        if success:
            for i in range(k):
                for j in range(i+1, k):
                    a, b = party[i], party[j]
                    delta = 0.18
                    a.rel[b.name] += delta; b.rel[a.name] += delta
            for m in party:
                m.E = max(0.0, m.E - 0.6)
                m.group_loyalty = min(1.0, m.group_loyalty + 0.06)
                m.cohesion = min(1.0, m.cohesion + 0.22)
                m.territory.attachment_strength = min(1.0, m.territory.attachment_strength + 0.02)
        else:
            for i in range(k):
                for j in range(i+1, k):
                    a, b = party[i], party[j]
                    delta = 0.05
                    a.rel[b.name] += delta; b.rel[a.name] += delta
            for m in party:
                m.cohesion = min(1.0, m.cohesion + 0.05)
        # zone adaptation
        self.env.huntzones[node]["base_success"] = float(np.clip(hz["base_success"] + (-0.045 if success else 0.012), 0.03, 0.8))
        # leader reward
        if success:
            self.food_store = min(self.max_store, getattr(self, "food_store", 0) + 4.0)
            for ally in party[1:]: ally.rel[self.name] += 0.06
        # cleanup
        for m in party:
            if getattr(m, "rally_target", None) == self.name:
                m.rally_target = None; m.state = "Awake"
        self.rally_state = {"leader": None, "ttl": 0, "node": None, "min_k": 2}
        # log
        self.log.append({
            "t": t, "name": self.name,
            "action": "rally_group_hunt_success" if success else "rally_group_hunt_failure",
            "party": [m.name for m in party], "k": k, "total_food": total_food,
            "p_group": p_group, "inj_prob": inj_prob, "injuries": injuries
        })
        return True
    def step(self, t, predator=None):
        # decay cohesion slightly
        self.cohesion = max(0.0, self.cohesion - 0.001)
        # TTL tick
        if self.rally_state["ttl"] > 0:
            self.rally_state["ttl"] -= 1
            if self.rally_state["ttl"] == 0:
                self.rally_state["leader"] = None; self.rally_state["node"] = None
        super().step(t, predator)

# =========================
# Community extensions (triadic closure, FoF, gossip, grace-period decay)
# =========================
TRIAD_GAIN      = 0.030
COPRESENCE_GAIN = 0.015
GOSSIP_GAIN     = 0.020
NEG_SPILLOVER   = 0.006
REL_DECAY       = 0.0003
REL_MIN, REL_MAX = -0.5, 1.0
REL_TH = 0.2
LAMB = 0.9
DECAY_GRACE = 40

class NPCRallyHuntCommunity(NPCRallyHunt):
    def mark_social(self, t):
        self.last_social_tick = t
    def fof_score(self, j_name):
        total, w = 0.0, 0.0
        for k_name, rik in self.rel.items():
            if k_name == j_name: continue
            if k_name not in self.roster_ref: continue
            rkj = self.roster_ref[k_name].rel.get(j_name, 0.0)
            if rik > 0 and rkj > 0:
                total += rik * rkj; w += 1.0
        return (total / w) if w > 0 else 0.0
    def apply_triadic_closure(self):
        allies = [o for o in self.nearby_allies(radius=4)]
        did=False
        for i in range(len(allies)):
            for j in range(i+1, len(allies)):
                a, b = allies[i], allies[j]
                if self.rel[a.name] > REL_TH and self.rel[b.name] > REL_TH:
                    inc = TRIAD_GAIN * min(self.rel[a.name], self.rel[b.name])
                    a.rel[b.name] = max(REL_MIN, min(REL_MAX, a.rel[b.name] + inc))
                    b.rel[a.name] = max(REL_MIN, min(REL_MAX, b.rel[a.name] + inc)); did=True
        if did: self.mark_social(self.env.t)
    def copresence_tick(self):
        mates = [o for o in self.nearby_allies(radius=3)]
        any_friend = False
        for o in mates:
            if self.rel[o.name] > 0:
                self.rel[o.name] = min(REL_MAX, self.rel[o.name] + COPRESENCE_GAIN)
                any_friend = True
        if any_friend: self.mark_social(self.env.t)
    def prosocial_gossip(self, party_names):
        for a in party_names:
            if a not in self.roster_ref: continue
            for b in party_names:
                if a == b: continue
                for k_name, rik in self.roster_ref[a].rel.items():
                    if k_name in party_names: continue
                    if rik > REL_TH and k_name in self.roster_ref:
                        target = self.roster_ref[k_name]
                        target.rel[b] = min(REL_MAX, target.rel.get(b, 0.0) + GOSSIP_GAIN * rik)
        self.mark_social(self.env.t)
    def antisocial_spill(self, thief_name):
        witnesses = [o for o in self.nearby_allies(radius=4) if o.name != thief_name]
        for w in witnesses:
            w.rel[thief_name] = max(REL_MIN, w.rel.get(thief_name, 0.0) - NEG_SPILLOVER)
    def relax_rel(self):
        idle = self.env.t - self.last_social_tick
        if idle <= DECAY_GRACE: return
        for name, r in list(self.rel.items()):
            if abs(r) < 0.1:
                if r > 0: self.rel[name] = max(0.0, r - REL_DECAY)
                elif r < 0: self.rel[name] = min(0.0, r + REL_DECAY)
            else:
                d = REL_DECAY * (0.2 * (1 - min(1.0, abs(r))))
                if r > 0: self.rel[name] = max(0.0, r - d)
                elif r < 0: self.rel[name] = min(0.0, r + d)
    def social_gravity_move(self):
        cands = self.nearby_allies(radius=6)
        if not cands: return False
        def score(o):
            return self.rel[o.name] + LAMB * self.fof_score(o.name) + 0.2*self.village_affinity
        best = max(cands, key=score)
        fof = self.fof_score(best.name)
        p = min(0.85, 0.12 + 0.25*max(0, self.rel[best.name]) + 0.18*fof + 0.15*self.village_affinity)
        if random.random() < p:
            self.move_towards(best.pos()); return True
        return False
    def attempt_rally_group_hunt(self, t):
        ok = super().attempt_rally_group_hunt(t)
        if ok:
            last = self.log[-1] if len(self.log) > 0 else None
            if last and "party" in last:
                self.prosocial_gossip(last["party"])  # spread good reputation
            self.mark_social(self.env.t)
        return ok
    def step(self, t, predator=None):
        # decay village affinity slowly
        self.village_affinity = max(0.0, self.village_affinity - 0.0005)
        super().step(t, predator)
        # tail social updates
        self.social_gravity_move()
        self.copresence_tick(); self.apply_triadic_closure(); self.relax_rel()
        friends = [o for o in self.nearby_allies(radius=3) if self.rel[o.name] > 0.2]
        if friends: self.village_affinity = min(1.0, self.village_affinity + 0.015)

# =========================
# Priority-layered agent with explicit death-cause logging
# =========================
HARD_HUNGER  = 95.0
HARD_INJURY  = 85.0
HARD_FATIGUE = 95.0
JOIN_NEAR_PRIORITY = 4

class NPCPriority(NPCRallyHuntCommunity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.share_threshold = 50.0
        self.store_fraction  = 0.6
    def in_communal_context(self):
        peers = [o for o in self.nearby_allies(radius=3) if self.rel[o.name] > 0.3]
        return len(peers) >= 2
    def _need_food_near_term(self):
        return self.hunger >= 70
    def _try_pantry_pull_or_share_request(self, t):
        if getattr(self, "food_store", 0.0) > 5.0:
            take = min(self.food_store, max(8.0, (self.hunger - 60)))
            self.food_store -= take
            before = self.hunger
            self.hunger = max(0.0, self.hunger - take)
            self.log.append({"t": t, "name": self.name, "action": "pantry_pull", "got": take, "h_before": before, "h_after": self.hunger})
            return True
        allies = sorted(self.nearby_allies(radius=3), key=lambda o: o.rel[self.name], reverse=True)
        for ally in allies:
            if ally.food_store > 12.0 and (ally.rel[self.name] > 0.1 or self.in_communal_context()):
                give = min(ally.food_store - 6.0, 12.0)
                if give > 0:
                    ally.food_store -= give
                    before = self.hunger
                    self.hunger = max(0.0, self.hunger - give)
                    self.rel[ally.name] += 0.05; ally.rel[self.name] += 0.03
                    self.log.append({"t": t, "name": self.name, "action": "help_received", "from": ally.name, "got": give})
                    return True
        return False
    def _try_quick_forage_home_pref(self, t):
        nodes = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
        if not nodes: return False
        node = nodes[0]
        self.move_towards(node)
        success, food, risk, p = self.env.forage(self.pos(), node)
        if success:
            before = self.hunger
            self.hunger = max(0.0, self.hunger - food)
            rem = max(0.0, food - (before - self.hunger))
            if rem > 0: self.food_store = min(self.max_store, getattr(self, "food_store", 0.0) + self.store_fraction*rem)
            self.update_kappa("forage", True, food)
            self.log.append({"t": t, "name": self.name, "action": "eat_success_quick", "food": food})
        else:
            self.update_kappa("forage", False, 0)
            self.log.append({"t": t, "name": self.name, "action": "eat_failure_quick"})
        return True
    def _seek_safe_rest(self, t):
        cx, cy = self.territory.center
        self.move_towards((int(cx), int(cy)))
        if self.fatigue >= 70 or self.env.day_night.is_night():
            self.enter_sleep(t); return True
        return True
    def _enter_sleep_now(self, t):
        self.enter_sleep(t); return True
    def _continue_rally_move(self, t):
        leader = None
        for o in self.nearby_allies(radius=JOIN_NEAR_PRIORITY+3):
            if getattr(o, "rally_state", {}).get("leader", None) == o.name and o.rally_state.get("ttl",0) > 0:
                leader = o; break
        if leader is None: return False
        target = leader.rally_state["node"] if leader.rally_state["node"] else leader.pos()
        self.move_towards(target); return True
    def _should_emit_or_refresh_rally(self, t):
        return (self.hunger > self.TH_H or self.forecast_hunger(self.env.t, self.horizon_rally) > self.TH_H) and not self.is_sleeping
    def _emit_or_refresh_rally(self, t):
        nodes = self.env.nearest_nodes(self.pos(), self.env.huntzones, k=1)
        target_node = nodes[0] if nodes else None
        if self.rally_state["leader"] is None:
            self.emit_rally_for_hunt(t, hunt_node=target_node, min_k=2, ttl=10)
        else:
            if self.rally_state["leader"] == self.name:
                self.rally_state["ttl"] = min(12, self.rally_state["ttl"] + 2)
    def _try_join_rally(self, t):
        return self.consider_join_rally(t)
    def _leader_can_launch_group_hunt_now(self, t):
        return self.rally_state["leader"] == self.name and self.rally_state["ttl"] > 0
    def _forage_is_good_now(self):
        return self.env.day_night.get_light_level() > 0.3 and self.hunger > (self.TH_H - 10)
    def _do_forage_step(self, t):
        nodes = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
        if not nodes: return False
        node = nodes[0]
        self.move_towards(node)
        success, food, risk, p = self.env.forage(self.pos(), node)
        if success:
            before = self.hunger
            self.hunger = max(0.0, self.hunger - food)
            rem = max(0.0, food - (before - self.hunger))
            if rem > 0: self.food_store = min(self.max_store, getattr(self, "food_store", 0.0) + self.store_fraction*rem)
            self.update_kappa("forage", True, food)
            self.log.append({"t": t, "name": self.name, "action": "eat_success", "food": food})
        else:
            self.update_kappa("forage", False, 0)
            self.log.append({"t": t, "name": self.name, "action": "eat_failure"})
        return True
    def _should_help_neighbor_now(self):
        allies = self.nearby_allies(radius=3)
        return any(o.hunger > 85 for o in allies)
    def _do_solo_hunt_step(self, t):
        nodes = self.env.nearest_nodes(self.pos(), self.env.huntzones, k=1)
        if not nodes: return False
        node = nodes[0]
        self.move_towards(node)
        hz = self.env.huntzones[node]
        light = self.env.day_night.get_light_level()
        tw = 1 - abs(light - 0.4)/0.6
        light_mod = 0.35 + 0.65 * max(0.0, tw)
        dist = abs(self.x - node[0]) + abs(self.y - node[1])
        dist_term = 0.25 * max(0, 1 - dist/16)
        p_solo = float(np.clip(hz["base_success"]*light_mod + dist_term, 0.03, 0.95))
        success = random.random() < p_solo
        if success:
            base_food = random.uniform(20, 40) * (0.8 + hz["base_success"]) ; food = base_food
            before = self.hunger
            self.hunger = max(0.0, self.hunger - food)
            rem = max(0.0, food - (before - self.hunger))
            if rem > 0: self.food_store = min(self.max_store, getattr(self, "food_store", 0.0) + self.store_fraction*rem)
            self.update_kappa("hunt", True, food*0.8)
            self.log.append({"t": t, "name": self.name, "action": "solo_hunt_success", "food": food})
        else:
            inj_prob = 0.15 + 0.7 * hz["danger"]
            if random.random() < inj_prob: self.injury = min(120, self.injury + random.uniform(2, 8))
            self.update_kappa("hunt", False, 0)
            self.log.append({"t": t, "name": self.name, "action": "solo_hunt_failure"})
        return True
    def step(self, t, predator=None):
        if not self.alive: return
        # pre
        self.update_territory_center(); self.detect_intruders(t)
        for intruder in self.detected_intruders:
            reaction = self.react_to_intruder(intruder, t)
            if reaction in ["chased", "retreated"]: return
        # death check w/ cause
        if self.hunger >= 100 or self.injury >= 100:
            cause = "hunger" if self.hunger >= 100 else "injury"
            self.alive = False
            self.log.append({"t": t, "name": self.name, "action": "death", "cause": cause, "at_home": self.territory.contains(self.pos()),
                             "hunger": round(self.hunger,1), "injury": round(self.injury,1), "fatigue": round(self.fatigue,1)})
            return
        # sleep branch
        if self.is_sleeping:
            # replicate parent's sleep handling (short form)
            self.sleep_duration += 1; self.total_sleep_time += 1
            time_bonus = 1.5 if self.env.day_night.is_night() else 1.0
            recovery = 6.0 * time_bonus * (1 + 0.2 * self.stamina)
            self.fatigue = max(0, self.fatigue - recovery)
            self.injury = max(0, self.injury - 2.0 * time_bonus)
            self.hunger = min(120, self.hunger + 0.5)
            self.E = max(0, self.E - (0.3 * time_bonus))
            self.sleep_debt = max(0, self.sleep_debt - 4.0 * time_bonus)
            if self.env.day_night.get_time_of_day() > 0.7 and self.sleep_duration > 5:
                self.consolidate_memory()
            should_wake = False; wake_reason = None
            if self.env.day_night.is_day() and self.fatigue < 30 and self.sleep_debt < 40:
                should_wake = True; wake_reason = "natural"
            if self.hunger > 95: should_wake = True; wake_reason = "hunger_emergency"
            if self.sleep_duration < 5: should_wake = False
            if should_wake: self.wake_up(t, wake_reason)
            return
        # L1 hard guard
        if self.hunger >= HARD_HUNGER:
            if self._try_pantry_pull_or_share_request(t): return
            if self._try_quick_forage_home_pref(t): return
        if self.injury >= HARD_INJURY:
            if self._seek_safe_rest(t): return
        if self.fatigue >= HARD_FATIGUE:
            if self._enter_sleep_now(t): return
        # L2 cooperative context
        if getattr(self, "state", "") == "rallying":
            if self._continue_rally_move(t): return
        if self._should_emit_or_refresh_rally(t):
            self._emit_or_refresh_rally(t)
            if self._try_join_rally(t): return
        if self._leader_can_launch_group_hunt_now(t):
            if self.attempt_rally_group_hunt(t): return
        # L3 night modulation
        if self.env.day_night.is_night() and self.avoidance > 0.4 and random.random() < 0.5:
            pass
        # L4 supply order
        if self._need_food_near_term():
            if self._try_pantry_pull_or_share_request(t): return
        if self._should_help_neighbor_now():
            if self.maybe_help_territorial(t, predator): return
        if self._forage_is_good_now():
            if self._do_forage_step(t): return
        if self._do_solo_hunt_step(t): return
        # L5 social tail
        self.social_gravity_move(); self.copresence_tick(); self.apply_triadic_closure(); self.relax_rel()
        self.update_heat(self.boredom * 0.05, 0)

# =========================
# Presets
# =========================
FORAGER   = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER   = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER   = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN  = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
SCAVENGER = {"risk_tolerance": 0.3, "curiosity": 0.6, "avoidance": 0.7, "stamina": 0.5, "empathy": 0.5}
NOMAD     = {"risk_tolerance": 0.7, "curiosity": 0.8, "avoidance": 0.1, "stamina": 0.6, "empathy": 0.4}
MEDIATOR  = {"risk_tolerance": 0.3, "curiosity": 0.5, "avoidance": 0.5, "stamina": 0.7, "empathy": 1.0}
HERMIT    = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.9, "stamina": 0.8, "empathy": 0.3}
AGGRESSOR = {"risk_tolerance": 0.8, "curiosity": 0.4, "avoidance": 0.1, "stamina": 0.9, "empathy": 0.2}
COLLECTOR = {"risk_tolerance": 0.4, "curiosity": 0.7, "avoidance": 0.6, "stamina": 0.6, "empathy": 0.7}

# =========================
# Run (example)
# =========================
def run_sim(TICKS=400, predator_spawn_interval=80):
    env = EnvForageBuff(size=40, n_berry=18, n_hunt=10)
    roster = {}
    npcs = []
    npc_configs = [
        ("Forager_A", FORAGER, (15, 15)),
        ("Tracker_B", TRACKER, (25, 15)),
        ("Pioneer_C", PIONEER, (20, 25)),
        ("Guardian_D", GUARDIAN, (10, 20)),
        ("Scavenger_E", SCAVENGER, (30, 20)),
        ("Nomad_F", NOMAD, (5, 5)),
        ("Mediator_G", MEDIATOR, (20, 20)),
        ("Hermit_H", HERMIT, (35, 35)),
        ("Aggressor_I", AGGRESSOR, (10, 30)),
        ("Collector_J", COLLECTOR, (30, 10)),
        ("Forager_K", FORAGER, (15, 30)),
        ("Pioneer_L", PIONEER, (25, 25)),
    ]
    for name, preset, start_pos in npc_configs:
        npc = NPCPriority(name, preset, env, roster, start_pos, horizon=8, horizon_rally=6, rally_ttl=10)
        npc.food_store = 25.0
        roster[name] = npc; npcs.append(npc)
    predator = Predator(env, strength=3.0)
    predator_events = []
    for t in range(TICKS):
        if t % predator_spawn_interval == 0 and t > 0 and not predator.active:
            predator.spawn(t); predator_events.append({"t": t, "event": "spawn"})
        if predator.active and predator.duration >= predator.max_duration:
            predator_events.append({"t": t, "event": "despawn"})
        predator.step()
        for n in npcs:
            if n.alive: n.detect_predator(predator, t)
            n.step(t, predator)
        env.step()
    # metrics
    df = pd.concat([pd.DataFrame(n.log) for n in npcs], ignore_index=True) if any(len(n.log)>0 for n in npcs) else pd.DataFrame(columns=["t","name","action"])
    alive = sum(1 for n in npcs if n.alive)
    deaths = df[df["action"]=="death"]
    death_by_cause = deaths["cause"].value_counts().to_dict() if "cause" in deaths.columns else {}
    rally_calls = df[df["action"]=="rally_for_hunt"]
    join_rally = df[df["action"]=="join_rally"]
    rg_succ = df[df["action"]=="rally_group_hunt_success"]
    rg_fail = df[df["action"]=="rally_group_hunt_failure"]
    print(f"Survivors: {alive} / {len(npcs)}")
    print(f"Deaths by cause: {death_by_cause}")
    print(f"Rally calls: {len(rally_calls)} | Joins: {len(join_rally)} | Group hunts: {len(rg_succ)+len(rg_fail)} (succ {len(rg_succ)} / fail {len(rg_fail)})")
    return npcs, df

if __name__ == "__main__":
    run_sim()
