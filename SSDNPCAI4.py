import random, math
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

random.seed(42); np.random.seed(42)

# -------- Day/Night Cycle --------
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


class EnvWithDayNight:
    def __init__(self, size=40, n_berry=15, n_hunt=10):
        self.size = size
        self.berries = {}
        for _ in range(n_berry):
            x, y = random.randrange(size), random.randrange(size)
            self.berries[(x, y)] = {
                "abundance": random.uniform(0.2, 0.6),
                "regen": random.uniform(0.003, 0.015)
            }
        self.huntzones = {}
        for _ in range(n_hunt):
            x, y = random.randrange(size), random.randrange(size)
            self.huntzones[(x, y)] = {
                "base_success": random.uniform(0.15, 0.45),
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
        p = 0.6 * abundance + 0.2 * max(0, 1 - dist / 12)
        modifier = self.day_night.get_forage_success_modifier()
        p *= modifier
        success = random.random() < p
        if success:
            self.berries[node]["abundance"] = max(0.0, self.berries[node]["abundance"] - random.uniform(0.2, 0.4))
            food = random.uniform(10, 20) * (0.5 + abundance / 2)
        else:
            food = 0.0
        risk = 0.05
        return success, food, risk, p


# -------- Territory System --------
class Territory:
    def __init__(self, owner, center, radius):
        self.owner = owner
        self.center = center
        self.radius = radius
        self.intrusion_tolerance = 0.5
        
        self.memory = {
            "food_found": 0,
            "helped_here": 0,
            "threatened": 0,
            "rested": 0
        }
        
        self.attachment_strength = 0.3
    
    def contains(self, pos):
        dx = pos[0] - self.center[0]
        dy = pos[1] - self.center[1]
        return (dx**2 + dy**2) <= self.radius**2
    
    def distance_from_center(self, pos):
        dx = pos[0] - self.center[0]
        dy = pos[1] - self.center[1]
        return math.sqrt(dx**2 + dy**2)
    
    def update_attachment(self, event_type, positive):
        if event_type in self.memory:
            self.memory[event_type] += 1
        
        if positive:
            self.attachment_strength = min(1.0, self.attachment_strength + 0.05)
        else:
            self.attachment_strength = max(0.1, self.attachment_strength - 0.1)


# -------- NPC with Territory --------
class NPCWithTerritory:
    def __init__(self, name, preset, env, roster_ref, start_pos):
        self.name = name
        self.env = env
        self.roster_ref = roster_ref
        self.x, self.y = start_pos
        
        self.hunger = 50.0
        self.fatigue = 30.0
        self.injury = 0.0
        self.alive = True
        self.state = "Idle"
        
        self.kappa = defaultdict(lambda: 0.1)
        self.kappa_min = 0.05
        self.E = 0.0
        self.T = 0.3
        
        self.G0 = 0.5
        self.g = 0.7
        self.eta = 0.3
        self.lambda_forget = 0.02
        self.rho = 0.1
        self.alpha = 0.6
        self.beta_E = 0.15
        
        self.Theta0 = 1.0
        self.a1 = 0.5
        self.a2 = 0.4
        self.h0 = 0.2
        self.gamma = 0.8
        
        self.T0 = 0.3
        self.c1 = 0.5
        self.c2 = 0.6
        
        p = preset
        self.risk_tolerance = p["risk_tolerance"]
        self.curiosity = p["curiosity"]
        self.avoidance = p["avoidance"]
        self.stamina = p["stamina"]
        self.empathy = p.get("empathy", 0.6)
        
        self.TH_H = 55.0
        self.TH_F = 70.0
        
        self.rel = defaultdict(float)
        self.help_debt = defaultdict(float)
        
        self.sleep_debt = 0.0
        self.is_sleeping = False
        self.sleep_duration = 0
        self.total_sleep_time = 0
        self.sleep_cycles = 0
        
        initial_radius = 5 + self.avoidance * 3
        self.territory = Territory(
            owner=self.name,
            center=self.pos(),
            radius=initial_radius
        )
        
        self.territorial_aggression = 0.3 + (1 - self.empathy) * 0.4
        self.group_loyalty = 0.5 + self.empathy * 0.3
        
        self.detected_intruders = []
        self.invited_guests = set()
        
        self.log = []
        self.boredom = 0.0
    
    def pos(self):
        return (self.x, self.y)
    
    def dist_to(self, o):
        return abs(self.x - o.x) + abs(self.y - o.y)
    
    def move_towards(self, target):
        tx, ty = target
        self.x += (1 if tx > self.x else -1 if tx < self.x else 0)
        self.y += (1 if ty > self.y else -1 if ty < self.y else 0)
    
    def nearby_allies(self, radius=3):
        return [o for on, o in self.roster_ref.items() 
                if on != self.name and o.alive and self.dist_to(o) <= radius]
    
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
    
    def check_leap(self):
        mean_kappa = np.mean(list(self.kappa.values())) if self.kappa else 0.1
        fatigue_factor = self.fatigue / 100.0
        Theta = self.Theta0 + self.a1 * mean_kappa - self.a2 * fatigue_factor
        h = self.h0 * np.exp((self.E - Theta) / self.gamma)
        jump_prob = 1 - np.exp(-h * 1.0)
        if random.random() < jump_prob:
            return True, h, Theta
        return False, h, Theta
    
    def update_temperature(self):
        kappa_values = list(self.kappa.values())
        if len(kappa_values) > 1:
            entropy = np.std(kappa_values)
        else:
            entropy = 0.5
        self.T = self.T0 + self.c1 * self.E - self.c2 * entropy
        self.T = max(0.1, min(1.0, self.T))
    
    def get_personal_sleep_pressure(self):
        env_pressure = self.env.day_night.get_sleep_pressure()
        debt_pressure = min(1.0, self.sleep_debt / 100)
        fatigue_pressure = min(1.0, self.fatigue / 100)
        total = (env_pressure * 0.5 + debt_pressure * 0.3 + fatigue_pressure * 0.2)
        return total
    
    def should_sleep(self):
        if self.is_sleeping:
            return True
        pressure = self.get_personal_sleep_pressure()
        if self.sleep_debt > 150:
            return True
        if self.fatigue > 90:
            return True
        if self.env.day_night.is_night() and self.fatigue > 60:
            return True
        if pressure > 0.7 and self.hunger < 85:
            return True
        return False
    
    def enter_sleep(self, t):
        self.is_sleeping = True
        self.sleep_duration = 0
        self.state = "Sleeping"
        self.sleep_cycles += 1
    
    def consolidate_memory(self):
        if len(self.kappa) < 2:
            return
        actions = list(self.kappa.keys())
        values = list(self.kappa.values())
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
            self.T = self.T0
            self.boredom = 0.0
        self.sleep_duration = 0
    
    def update_territory_center(self):
        current_pos = self.pos()
        cx, cy = self.territory.center
        new_cx = cx * 0.95 + current_pos[0] * 0.05
        new_cy = cy * 0.95 + current_pos[1] * 0.05
        self.territory.center = (new_cx, new_cy)
    
    def detect_intruders(self, t):
        self.detected_intruders = []
        allies = self.nearby_allies(radius=int(self.territory.radius))
        
        for ally in allies:
            if ally.name in self.invited_guests:
                continue
            
            if self.territory.contains(ally.pos()):
                threat = self.calculate_threat(ally)
                self.detected_intruders.append({
                    "name": ally.name,
                    "npc": ally,
                    "detected_at": t,
                    "threat_level": threat
                })
    
    def calculate_threat(self, other_npc):
        base_threat = 0.3
        
        relation = self.rel[other_npc.name]
        if relation < 0:
            base_threat += abs(relation) * 0.5
        elif relation > 0.5:
            base_threat -= 0.3
        
        base_threat += other_npc.territorial_aggression * 0.3
        
        if self.hunger > 70 and other_npc.hunger > 70:
            base_threat += 0.4
        
        return max(0, min(1.0, base_threat))
    
    def react_to_intruder(self, intruder_data, t):
        threat = intruder_data["threat_level"]
        other_npc = intruder_data["npc"]
        
        if threat < 0.3:
            if self.empathy > 0.7 and random.random() < 0.3:
                self.invited_guests.add(other_npc.name)
                self.rel[other_npc.name] += 0.1
                other_npc.rel[self.name] += 0.1
                
                self.log.append({
                    "t": t, "name": self.name, "action": "invite_to_territory",
                    "target": other_npc.name,
                    "threat_level": round(threat, 2)
                })
                return "invited"
        
        elif threat < 0.6:
            edge_x = self.territory.center[0] + self.territory.radius * 0.8
            edge_y = self.territory.center[1]
            self.move_towards((int(edge_x), int(edge_y)))
            self.rel[other_npc.name] -= 0.05
            
            self.log.append({
                "t": t, "name": self.name, "action": "warning_distance",
                "target": other_npc.name,
                "threat_level": round(threat, 2)
            })
            return "warned"
        
        else:
            if self.territorial_aggression > other_npc.territorial_aggression:
                other_npc.E = min(5.0, other_npc.E + 0.5)
                other_npc.rel[self.name] -= 0.15
                self.rel[other_npc.name] -= 0.1
                
                self.log.append({
                    "t": t, "name": self.name, "action": "chase_away",
                    "target": other_npc.name,
                    "threat_level": round(threat, 2)
                })
                return "chased"
            else:
                escape_x = self.territory.center[0] - (other_npc.x - self.territory.center[0])
                escape_y = self.territory.center[1] - (other_npc.y - self.territory.center[1])
                self.move_towards((
                    max(0, min(self.env.size-1, int(escape_x))),
                    max(0, min(self.env.size-1, int(escape_y)))
                ))
                
                self.E = min(5.0, self.E + 0.3)
                
                self.log.append({
                    "t": t, "name": self.name, "action": "retreat_from_territory",
                    "target": other_npc.name,
                    "threat_level": round(threat, 2)
                })
                return "retreated"
        
        return "ignored"
    
    def am_i_home(self):
        return self.territory.contains(self.pos())
    
    def get_home_bonus(self):
        if self.am_i_home():
            attachment = self.territory.attachment_strength
            return {
                "recovery_bonus": 1.0 + attachment * 0.5,
                "heat_reduction": 0.1 * attachment,
                "sleep_quality": 1.0 + attachment * 0.3
            }
        else:
            return {
                "recovery_bonus": 0.8,
                "heat_reduction": 0.0,
                "sleep_quality": 0.9
            }
    
    def help_utility(self, o):
        need = max(0, (o.hunger - 55) / 40) + max(0, (o.injury - 15) / 50) + max(0, (o.fatigue - 70) / 50)
        base = 0.35 * self.empathy + 0.4 * self.rel[o.name] + 0.35 * self.help_debt[o.name]
        myneed = max(0, (self.hunger - 55) / 40) + max(0, (self.injury - 15) / 50) + max(0, (self.fatigue - 70) / 50)
        return need * base - 0.4 * myneed
    
    def help_utility_territorial(self, o):
        base_utility = self.help_utility(o)
        
        if self.territory.contains(o.pos()):
            bonus = 0.3 * self.group_loyalty
            base_utility += bonus
        
        if o.name in self.invited_guests:
            base_utility += 0.2
        
        return base_utility
    
    def maybe_help_territorial(self, t):
        allies = self.nearby_allies(radius=3)
        if not allies:
            return False
        
        best = None
        bestu = 0.0
        for o in allies:
            u = self.help_utility_territorial(o)
            if u > bestu:
                bestu = u
                best = o
        
        if best and bestu > 0.05:
            if self.hunger < 85 and best.hunger > 75:
                delta = 25.0
                self.hunger = min(100.0, self.hunger + 6.0)
                best.hunger = max(0.0, best.hunger - delta)
                self.rel[best.name] += 0.08
                best.rel[self.name] += 0.04
                best.help_debt[self.name] += 0.2
                
                self.update_kappa("help", True, delta * 0.5)
                
                if self.am_i_home():
                    self.territory.update_attachment("helped_here", True)
                
                self.log.append({
                    "t": t, "name": self.name, "action": "share_food_territorial",
                    "target": best.name,
                    "at_home": self.am_i_home(),
                    "target_at_my_home": self.territory.contains(best.pos())
                })
                return True
        
        return False
    
    def step(self, t):
        if not self.alive:
            return
        
        self.update_territory_center()
        self.detect_intruders(t)
        
        for intruder in self.detected_intruders:
            reaction = self.react_to_intruder(intruder, t)
            if reaction in ["chased", "retreated"]:
                return
        
        if self.is_sleeping:
            home_bonus = self.get_home_bonus()
            self.sleep_duration += 1
            self.total_sleep_time += 1
            
            time_bonus = 1.5 if self.env.day_night.is_night() else 1.0
            recovery = 6.0 * time_bonus * (1 + 0.2 * self.stamina)
            recovery *= home_bonus["sleep_quality"]
            
            self.fatigue = max(0, self.fatigue - recovery)
            self.injury = max(0, self.injury - 2.0 * time_bonus)
            self.hunger = min(120, self.hunger + 0.5)
            
            heat_reduction = 0.3 * time_bonus + home_bonus["heat_reduction"]
            self.E = max(0, self.E - heat_reduction)
            self.sleep_debt = max(0, self.sleep_debt - 4.0 * time_bonus)
            
            if self.env.day_night.get_time_of_day() > 0.7 and self.sleep_duration > 5:
                self.consolidate_memory()
            
            should_wake = False
            wake_reason = None
            
            if self.env.day_night.is_day() and self.fatigue < 30 and self.sleep_debt < 40:
                should_wake = True
                wake_reason = "natural"
            
            if self.hunger > 95:
                should_wake = True
                wake_reason = "hunger_emergency"
            
            if self.sleep_duration < 5:
                should_wake = False
            
            if should_wake:
                self.wake_up(t, wake_reason)
                self.territory.update_attachment("rested", True)
            
            return
        
        cost_mult = self.env.day_night.get_activity_cost_multiplier()
        home_bonus = self.get_home_bonus()
        
        if not self.am_i_home():
            cost_mult *= 1.2
        
        self.hunger = min(120, self.hunger + 1.8 * cost_mult)
        self.fatigue = min(120, self.fatigue + 0.8 * cost_mult)
        self.injury = min(120, self.injury + 0.02 * self.fatigue / 100)
        self.sleep_debt = min(200, self.sleep_debt + 1.5)
        
        if self.am_i_home():
            self.E = max(0, self.E - home_bonus["heat_reduction"])
        
        if self.hunger >= 100 or self.injury >= 100:
            leap_occurred, h, Theta = self.check_leap()
            if leap_occurred or self.hunger >= 110 or self.injury >= 110:
                self.alive = False
                self.log.append({
                    "t": t, "name": self.name, "action": "death",
                    "at_home": self.am_i_home()
                })
                return
        
        if self.should_sleep():
            self.enter_sleep(t)
            return
        
        self.update_temperature()
        
        if self.env.day_night.is_night() and self.avoidance > 0.5:
            if random.random() < 0.7:
                return
        
        if self.maybe_help_territorial(t):
            return
        
        if self.hunger > self.TH_H:
            if not self.am_i_home() and random.random() < 0.4:
                self.move_towards((int(self.territory.center[0]), int(self.territory.center[1])))
                return
            
            meaning_p = (self.hunger - self.TH_H) / (100 - self.TH_H)
            j_forage = self.alignment_flow("forage", meaning_p)
            
            nodes = self.env.nearest_nodes(self.pos(), self.env.berries, k=2)
            if nodes:
                node = nodes[0]
                self.move_towards(node)
                success, food, risk, p = self.env.forage(self.pos(), node)
                
                if success:
                    self.hunger = max(0, self.hunger - food)
                    self.fatigue = max(0, self.fatigue - food * 0.1)
                    self.update_kappa("forage", True, food)
                    self.update_heat(meaning_p, j_forage)
                    
                    if self.am_i_home():
                        self.territory.update_attachment("food_found", True)
                else:
                    self.update_kappa("forage", False, 0)
                    self.update_heat(meaning_p, 0)
        
        else:
            if random.random() < 0.5:
                angle = random.uniform(0, 2 * math.pi)
                patrol_radius = self.territory.radius * 0.7
                target_x = self.territory.center[0] + patrol_radius * math.cos(angle)
                target_y = self.territory.center[1] + patrol_radius * math.sin(angle)
                
                self.move_towards((int(target_x), int(target_y)))
            
            self.boredom += 0.05
            self.update_heat(self.boredom * 0.1, 0)


# -------- EXPANDED Setup --------
FORAGER = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
SCAVENGER = {"risk_tolerance": 0.3, "curiosity": 0.6, "avoidance": 0.7, "stamina": 0.5, "empathy": 0.5}
NOMAD = {"risk_tolerance": 0.7, "curiosity": 0.8, "avoidance": 0.1, "stamina": 0.6, "empathy": 0.4}
MEDIATOR = {"risk_tolerance": 0.3, "curiosity": 0.5, "avoidance": 0.5, "stamina": 0.7, "empathy": 1.0}
HERMIT = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.9, "stamina": 0.8, "empathy": 0.3}
AGGRESSOR = {"risk_tolerance": 0.8, "curiosity": 0.4, "avoidance": 0.1, "stamina": 0.9, "empathy": 0.2}
COLLECTOR = {"risk_tolerance": 0.4, "curiosity": 0.7, "avoidance": 0.6, "stamina": 0.6, "empathy": 0.7}

env = EnvWithDayNight(size=40, n_berry=15, n_hunt=10)
roster = {}

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

npcs = []
for name, preset, start_pos in npc_configs:
    npc = NPCWithTerritory(name, preset, env, roster, start_pos)
    npcs.append(npc)
    roster[name] = npc

print("="*70)
print("EXPANDED TERRITORY-BASED SURVIVAL SIMULATION")
print("="*70)
print(f"Population: {len(npcs)} NPCs")
print(f"Map size: {env.size}x{env.size}")
print(f"Resources: {len(env.berries)} berry patches")
print()

type_groups = {}
for npc in npcs:
    npc_type = npc.name.split('_')[0]
    if npc_type not in type_groups:
        type_groups[npc_type] = []
    type_groups[npc_type].append(npc)

print("=== NPC Roster by Type ===")
for npc_type, group in sorted(type_groups.items()):
    print(f"\n{npc_type} ({len(group)}):")
    for npc in group:
        print(f"  {npc.name}: pos={npc.pos()}, territory_r={npc.territory.radius:.1f}, "
              f"aggr={npc.territorial_aggression:.2f}, emp={npc.empathy:.2f}")

print("\n" + "="*70)

TICKS = 400

for t in range(TICKS):
    for n in npcs:
        n.step(t)
    env.step()
    
    if t % 50 == 0:
        alive_count = sum(1 for n in npcs if n.alive)
        alive_by_type = {}
        for n in npcs:
            if n.alive:
                npc_type = n.name.split('_')[0]
                alive_by_type[npc_type] = alive_by_type.get(npc_type, 0) + 1
        
        type_summary = ", ".join([f"{k}:{v}" for k, v in sorted(alive_by_type.items())])
        print(f"t={t:3d}: {alive_count}/{len(npcs)} alive - {type_summary}")
        
        if alive_count == 0:
            print(f"\nEXTINCTION at t={t}")
            break

print("\n" + "="*70)
print("SIMULATION COMPLETE")
print("="*70)

# Analysis
df_logs = pd.concat([pd.DataFrame(n.log) for n in npcs], ignore_index=True)

print("\n=== FINAL STATUS BY TYPE ===")
for npc_type in sorted(type_groups.keys()):
    alive = [n for n in type_groups[npc_type] if n.alive]
    dead = [n for n in type_groups[npc_type] if not n.alive]
    print(f"\n{npc_type}: {len(alive)}/{len(type_groups[npc_type])} survived")
    
    if alive:
        avg_attachment = np.mean([n.territory.attachment_strength for n in alive])
        avg_kappa = np.mean([n.kappa['forage'] for n in alive])
        print(f"  Avg attachment: {avg_attachment:.2f}")
        print(f"  Avg κ_forage: {avg_kappa:.3f}")
        
        for n in alive:
            guests = len(n.invited_guests)
            print(f"    {n.name}: guests={guests}, home={n.am_i_home()}")

print("\n=== TERRITORIAL INTERACTIONS ===")
invitations = df_logs[df_logs["action"] == "invite_to_territory"]
warnings = df_logs[df_logs["action"] == "warning_distance"]
chases = df_logs[df_logs["action"] == "chase_away"]
retreats = df_logs[df_logs["action"] == "retreat_from_territory"]

print(f"Invitations: {len(invitations)}")
print(f"Warnings: {len(warnings)}")
print(f"Chases: {len(chases)}")
print(f"Retreats: {len(retreats)}")

if not invitations.empty:
    print("\nTop Inviters:")
    inv_counts = invitations['name'].value_counts().head(3)
    for name, count in inv_counts.items():
        npc = roster[name]
        print(f"  {name} (emp={npc.empathy:.2f}): {count} invitations")

if not chases.empty:
    print("\nMost Aggressive:")
    chase_counts = chases['name'].value_counts().head(3)
    for name, count in chase_counts.items():
        npc = roster[name]
        print(f"  {name} (aggr={npc.territorial_aggression:.2f}): {count} chases")

print("\n=== COOPERATION ANALYSIS ===")
helping = df_logs[df_logs["action"] == "share_food_territorial"]
print(f"Total help events: {len(helping)}")

if not helping.empty:
    help_at_home = len(helping[helping["at_home"] == True])
    print(f"Help at home: {help_at_home} ({help_at_home/len(helping)*100:.1f}%)")
    
    print("\nMost Helpful:")
    help_counts = helping['name'].value_counts().head(3)
    for name, count in help_counts.items():
        npc = roster[name]
        print(f"  {name} (emp={npc.empathy:.2f}): {count} times")

print("\n=== TERRITORY OVERLAPS ===")
overlaps = []
for i, npc1 in enumerate(npcs):
    if not npc1.alive:
        continue
    for npc2 in npcs[i+1:]:
        if not npc2.alive:
            continue
        
        cx1, cy1 = npc1.territory.center
        cx2, cy2 = npc2.territory.center
        dist = math.sqrt((cx1-cx2)**2 + (cy1-cy2)**2)
        overlap = npc1.territory.radius + npc2.territory.radius - dist
        
        if overlap > 0:
            overlaps.append({
                "npc1": npc1.name,
                "npc2": npc2.name,
                "overlap": overlap,
                "relation": (npc1.rel[npc2.name] + npc2.rel[npc1.name]) / 2
            })

print(f"Found {len(overlaps)} territory overlaps")
if overlaps:
    overlaps.sort(key=lambda x: x['overlap'], reverse=True)
    for ov in overlaps[:5]:
        print(f"  {ov['npc1']} ⟷ {ov['npc2']}: overlap={ov['overlap']:.1f}, relation={ov['relation']:.2f}")

# Visualization
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

# 1. Territory Map
ax1 = fig.add_subplot(gs[0:2, 0:2])

for pos in env.berries.keys():
    ax1.scatter(pos[0], pos[1], c='green', s=100, marker='*', alpha=0.5)

colors_map = {
    'Forager': 'blue', 'Tracker': 'red', 'Pioneer': 'purple',
    'Guardian': 'orange', 'Scavenger': 'brown', 'Nomad': 'cyan',
    'Mediator': 'gold', 'Hermit': 'gray', 'Aggressor': 'darkred',
    'Collector': 'pink'
}

for npc in npcs:
    npc_type = npc.name.split('_')[0]
    color = colors_map.get(npc_type, 'black')
    alpha = 0.3 if npc.alive else 0.1
    
    circle = Circle(npc.territory.center, npc.territory.radius, 
                   color=color, alpha=alpha, linewidth=2, 
                   linestyle='--' if not npc.alive else '-')
    ax1.add_patch(circle)
    
    if npc.alive:
        ax1.scatter(npc.x, npc.y, c=color, s=300, marker='o', 
                   edgecolors='black', linewidths=2, zorder=5)
        ax1.text(npc.x, npc.y+1, npc_type[0], 
                ha='center', fontsize=8, fontweight='bold')
    else:
        ax1.scatter(npc.x, npc.y, c='gray', s=200, marker='x', 
                   linewidths=3, zorder=5)

ax1.set_xlim(0, env.size)
ax1.set_ylim(0, env.size)
ax1.set_aspect('equal')
ax1.set_title("Territory Map (12 NPCs)", fontsize=14, fontweight='bold')
ax1.grid(alpha=0.3)

# 2. Survival by Type
ax2 = fig.add_subplot(gs[0, 2])
survival_data = {}
for npc_type, group in type_groups.items():
    alive = sum(1 for n in group if n.alive)
    survival_data[npc_type] = alive / len(group)

types_sorted = sorted(survival_data.items(), key=lambda x: x[1], reverse=True)
ax2.barh([t[0] for t in types_sorted], [t[1] for t in types_sorted], 
         color=[colors_map.get(t[0], 'black') for t in types_sorted], alpha=0.7)
ax2.set_xlabel("Survival Rate")
ax2.set_title("Survival by Type", fontweight='bold')
ax2.set_xlim(0, 1)
ax2.grid(alpha=0.3, axis='x')

# 3. Attachment Strength
ax3 = fig.add_subplot(gs[1, 2])
alive_npcs = [n for n in npcs if n.alive]
if alive_npcs:
    attachments = [n.territory.attachment_strength for n in alive_npcs]
    names = [n.name.split('_')[0] for n in alive_npcs]
    colors_list = [colors_map.get(n, 'black') for n in names]
    
    ax3.bar(range(len(attachments)), attachments, color=colors_list, alpha=0.7)
    ax3.set_xticks(range(len(names)))
    ax3.set_xticklabels(names, rotation=45, ha='right', fontsize=8)
    ax3.set_ylabel("Attachment")
    ax3.set_title("Territory Attachment", fontweight='bold')
    ax3.set_ylim(0, 1.1)
    ax3.grid(alpha=0.3, axis='y')

# 4. Social Network
ax4 = fig.add_subplot(gs[0, 3])
alive_npcs_sorted = sorted([n for n in npcs if n.alive], key=lambda x: x.name)
n_alive = len(alive_npcs_sorted)
if n_alive > 0:
    relation_matrix = np.zeros((n_alive, n_alive))
    for i, npc1 in enumerate(alive_npcs_sorted):
        for j, npc2 in enumerate(alive_npcs_sorted):
            if i != j:
                relation_matrix[i, j] = npc1.rel[npc2.name]
    
    im = ax4.imshow(relation_matrix, cmap='RdYlGn', vmin=-0.5, vmax=0.5)
    ax4.set_xticks(range(n_alive))
    ax4.set_yticks(range(n_alive))
    ax4.set_xticklabels([n.name.split('_')[0] for n in alive_npcs_sorted], 
                        rotation=45, ha='right', fontsize=7)
    ax4.set_yticklabels([n.name.split('_')[0] for n in alive_npcs_sorted], fontsize=7)
    ax4.set_title("Relations", fontweight='bold')
    plt.colorbar(im, ax=ax4)

# 5. Events Timeline
ax5 = fig.add_subplot(gs[2, 0:2])
event_types = ["invite_to_territory", "warning_distance", "chase_away", "retreat_from_territory"]
event_colors = ['green', 'yellow', 'red', 'orange']

for i, (event_type, color) in enumerate(zip(event_types, event_colors)):
    events = df_logs[df_logs["action"] == event_type]
    if not events.empty:
        ax5.scatter(events["t"], [i]*len(events), c=color, s=30, alpha=0.6)

ax5.set_xlabel("Time")
ax5.set_yticks(range(len(event_types)))
ax5.set_yticklabels([et.replace('_', ' ') for et in event_types])
ax5.set_title("Territorial Events Timeline", fontweight='bold')
ax5.grid(alpha=0.3, axis='x')

# 6. Empathy vs Aggression
ax6 = fig.add_subplot(gs[2, 2])
for npc in npcs:
    npc_type = npc.name.split('_')[0]
    color = colors_map.get(npc_type, 'black')
    marker = 'o' if npc.alive else 'x'
    ax6.scatter(npc.empathy, npc.territorial_aggression, 
               c=color, s=150, marker=marker, alpha=0.7, edgecolors='black')

ax6.set_xlabel("Empathy")
ax6.set_ylabel("Territorial Aggression")
ax6.set_title("Empathy vs Aggression", fontweight='bold')
ax6.grid(alpha=0.3)

# 7. Type Distribution
ax7 = fig.add_subplot(gs[2, 3])
type_counts = {}
for npc_type, group in type_groups.items():
    alive = sum(1 for n in group if n.alive)
    dead = len(group) - alive
    type_counts[npc_type] = {'alive': alive, 'dead': dead}

types = list(type_counts.keys())
alive_counts = [type_counts[t]['alive'] for t in types]
dead_counts = [type_counts[t]['dead'] for t in types]

x = np.arange(len(types))
ax7.bar(x, alive_counts, label='Alive', color='green', alpha=0.7)
ax7.bar(x, dead_counts, bottom=alive_counts, label='Dead', color='red', alpha=0.7)
ax7.set_xticks(x)
ax7.set_xticklabels(types, rotation=45, ha='right', fontsize=8)
ax7.set_ylabel("Count")
ax7.set_title("Population Status", fontweight='bold')
ax7.legend()
ax7.grid(alpha=0.3, axis='y')

plt.suptitle("Expanded Territory Simulation (12 NPCs)", fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

print("\n" + "="*70)
print("SSD THEORETICAL INTERPRETATION")
print("="*70)
print("""
【人口増加の効果】
12個体への拡張により、以下が観測可能に:

1. タイプ別生存戦略の分化
   - Hermit: 高avoidance → 孤立生存
   - Mediator: 高empathy → 協力ネットワーク構築
   - Aggressor: 低empathy → 縄張り競合で消耗?

2. 空間的クラスター形成
   - 縄張り重複 → 関係性により排除 or 統合
   - invited_guests → 「仲間集団」の創発

3. 資源競合の激化
   - 個体密度↑ → 縄張り衝突頻度↑
   - chase/retreat → E(ストレス)蓄積 → 生存率低下

4. 協力の条件依存性
   - 「自分の縄張り内で助ける」バイアス
   - group_loyalty × territory_contains = 協力促進

【構造主観力学的洞察】
縄張りシステムは「空間に刻まれた整合慣性」として機能し:
- 成功体験 → attachment↑ → ホームボーナス
- 他者の侵入 → 脅威判定 → chase/invite の二分岐
- empathy が境界の透過性を決定

これは「家」「故郷」「領土」という
人間の空間認識の構造的基盤である。
""")