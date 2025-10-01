import random, math
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

random.seed(55); np.random.seed(55)

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
    
    def get_phase_name(self):
        time = self.get_time_of_day()
        
        if time < 0.25:
            return "Dawn"
        elif time < 0.5:
            return "Morning"
        elif time < self.night_start:
            return "Afternoon"
        elif time < self.night_end:
            return "Night"
        else:
            return "Late_Night"


# -------- Environment with Day/Night --------
class EnvWithDayNight:
    def __init__(self, size=26, n_berry=7, n_hunt=5):
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
        
        # 昼夜修正
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


# -------- NPC with Circadian Rhythm --------
class NPCWithCircadianRhythm:
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
        
        # SSD
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
        
        # 睡眠
        self.sleep_debt = 0.0
        self.is_sleeping = False
        self.sleep_duration = 0
        self.total_sleep_time = 0
        self.sleep_cycles = 0
        
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
        
        total = (env_pressure * 0.5 + 
                debt_pressure * 0.3 + 
                fatigue_pressure * 0.2)
        
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
        
        self.log.append({
            "t": t, "name": self.name, "state": "Sleep", "action": "sleep_start",
            "time_of_day": self.env.day_night.get_phase_name(),
            "sleep_pressure": round(self.get_personal_sleep_pressure(), 2),
            "target": "", "amount": 0,
            "hunger": round(self.hunger, 1), 
            "fatigue": round(self.fatigue, 1),
            "injury": round(self.injury, 1),
            "E": round(self.E, 2),
            "sleep_debt": round(self.sleep_debt, 1),
            "light_level": round(self.env.day_night.get_light_level(), 2)
        })
    
    def process_sleep(self, t):
        self.sleep_duration += 1
        self.total_sleep_time += 1
        
        time_bonus = 1.5 if self.env.day_night.is_night() else 1.0
        recovery = 6.0 * time_bonus * (1 + 0.2 * self.stamina)
        
        self.fatigue = max(0, self.fatigue - recovery)
        self.injury = max(0, self.injury - 2.0 * time_bonus)
        self.hunger = min(120, self.hunger + 0.5)
        
        self.E = max(0, self.E - 0.3 * time_bonus)
        self.sleep_debt = max(0, self.sleep_debt - 4.0 * time_bonus)
        
        # 記憶統合
        if self.env.day_night.get_time_of_day() > 0.7 and self.sleep_duration > 5:
            self.consolidate_memory()
        
        # 起床判定
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
                self.kappa[action] = max(self.kappa_min, 
                                        self.kappa[action] - self.lambda_forget * 3)
    
    def wake_up(self, t, reason):
        self.is_sleeping = False
        self.state = "Awake"
        
        if reason == "natural":
            self.T = self.T0
            self.boredom = 0.0
        
        self.log.append({
            "t": t, "name": self.name, "state": "Sleep", "action": "wake_up",
            "wake_reason": reason,
            "sleep_duration": self.sleep_duration,
            "time_of_day": self.env.day_night.get_phase_name(),
            "target": "", "amount": 0,
            "hunger": round(self.hunger, 1), 
            "fatigue": round(self.fatigue, 1),
            "injury": round(self.injury, 1),
            "E": round(self.E, 2),
            "light_level": round(self.env.day_night.get_light_level(), 2)
        })
        
        self.sleep_duration = 0
    
    def help_utility(self, o):
        need = max(0, (o.hunger - 55) / 40) + max(0, (o.injury - 15) / 50) + max(0, (o.fatigue - 70) / 50)
        base = 0.35 * self.empathy + 0.4 * self.rel[o.name] + 0.35 * self.help_debt[o.name]
        myneed = max(0, (self.hunger - 55) / 40) + max(0, (self.injury - 15) / 50) + max(0, (self.fatigue - 70) / 50)
        return need * base - 0.4 * myneed
    
    def maybe_help(self, t):
        allies = self.nearby_allies(radius=3)
        if not allies:
            return False
        
        best = None
        bestu = 0.0
        for o in allies:
            u = self.help_utility(o)
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
                
                self.log.append({
                    "t": t, "name": self.name, "state": "Help", "action": "share_food",
                    "target": best.name, "amount": delta,
                    "time_of_day": self.env.day_night.get_phase_name(),
                    "hunger": round(self.hunger, 1), 
                    "fatigue": round(self.fatigue, 1),
                    "injury": round(self.injury, 1),
                    "E": round(self.E, 2), 
                    "T": round(self.T, 2),
                    "kappa_help": round(self.kappa["help"], 3)
                })
                return True
        
        return False
    
    def step(self, t):
        if not self.alive:
            return
        
        # 睡眠中
        if self.is_sleeping:
            self.process_sleep(t)
            return
        
        # 代謝
        cost_mult = self.env.day_night.get_activity_cost_multiplier()
        
        self.hunger = min(120, self.hunger + 1.8 * cost_mult)
        self.fatigue = min(120, self.fatigue + 0.8 * cost_mult)
        self.injury = min(120, self.injury + 0.02 * self.fatigue / 100)
        self.sleep_debt = min(200, self.sleep_debt + 1.5)
        
        # 死亡判定
        if self.hunger >= 100 or self.injury >= 100:
            leap_occurred, h, Theta = self.check_leap()
            if leap_occurred or self.hunger >= 110 or self.injury >= 110:
                self.alive = False
                self.log.append({
                    "t": t, "name": self.name, "state": "Dead", "action": "death",
                    "time_of_day": self.env.day_night.get_phase_name(),
                    "target": "", "amount": 0,
                    "hunger": round(self.hunger, 1), 
                    "fatigue": round(self.fatigue, 1),
                    "injury": round(self.injury, 1),
                    "E": round(self.E, 2), 
                    "jump_rate": round(h, 3), 
                    "Theta": round(Theta, 2)
                })
                return
        
        # 睡眠判定
        if self.should_sleep():
            self.enter_sleep(t)
            return
        
        self.update_temperature()
        
        # 夜間は活動控える
        if self.env.day_night.is_night() and self.avoidance > 0.5:
            if random.random() < 0.7:
                self.log.append({
                    "t": t, "name": self.name, "state": "Rest", "action": "night_rest",
                    "time_of_day": "Night",
                    "target": "", "amount": 0,
                    "hunger": round(self.hunger, 1), 
                    "fatigue": round(self.fatigue, 1),
                    "injury": round(self.injury, 1),
                    "E": round(self.E, 2),
                    "light_level": round(self.env.day_night.get_light_level(), 2)
                })
                return
        
        # 助け合い
        if self.maybe_help(t):
            return
        
        # 採餌
        if self.hunger > self.TH_H:
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
                    
                    self.log.append({
                        "t": t, "name": self.name, "state": "Food", "action": "eat_success",
                        "time_of_day": self.env.day_night.get_phase_name(),
                        "light_level": round(self.env.day_night.get_light_level(), 2),
                        "target": "Berry", "amount": round(food, 1),
                        "hunger": round(self.hunger, 1), 
                        "fatigue": round(self.fatigue, 1),
                        "injury": round(self.injury, 1),
                        "E": round(self.E, 2), 
                        "T": round(self.T, 2),
                        "kappa_forage": round(self.kappa["forage"], 3)
                    })
                else:
                    self.update_kappa("forage", False, 0)
                    self.update_heat(meaning_p, 0)
                    
                    self.log.append({
                        "t": t, "name": self.name, "state": "Food", "action": "eat_fail",
                        "time_of_day": self.env.day_night.get_phase_name(),
                        "light_level": round(self.env.day_night.get_light_level(), 2),
                        "target": "Berry", "amount": 0,
                        "hunger": round(self.hunger, 1), 
                        "fatigue": round(self.fatigue, 1),
                        "injury": round(self.injury, 1),
                        "E": round(self.E, 2)
                    })
        
        # パトロール
        else:
            move_range = int(self.T * 2)
            dx = random.randint(-move_range, move_range)
            dy = random.randint(-move_range, move_range)
            
            self.x = max(0, min(self.env.size - 1, self.x + dx))
            self.y = max(0, min(self.env.size - 1, self.y + dy))
            
            self.boredom += 0.05
            self.update_heat(self.boredom * 0.1, 0)
            
            self.log.append({
                "t": t, "name": self.name, "state": "Patrol", "action": "patrol",
                "time_of_day": self.env.day_night.get_phase_name(),
                "light_level": round(self.env.day_night.get_light_level(), 2),
                "target": "", "amount": 0,
                "hunger": round(self.hunger, 1), 
                "fatigue": round(self.fatigue, 1),
                "injury": round(self.injury, 1),
                "E": round(self.E, 2), 
                "T": round(self.T, 2),
                "boredom": round(self.boredom, 2)
            })


# Presets
FORAGER = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
SCAVENGER = {"risk_tolerance": 0.3, "curiosity": 0.6, "avoidance": 0.7, "stamina": 0.5, "empathy": 0.5}

# Setup
env = EnvWithDayNight()
roster = {}
center = (env.size // 2, env.size // 2)
starts = [
    (center[0] - 2, center[1]),
    (center[0] + 2, center[1] - 1),
    (center[0], center[1] + 2),
    (center[0] - 1, center[1] - 2),
    (center[0] + 1, center[1] + 1)
]

npcs = [
    NPCWithCircadianRhythm("Forager_A", FORAGER, env, roster, starts[0]),
    NPCWithCircadianRhythm("Tracker_B", TRACKER, env, roster, starts[1]),
    NPCWithCircadianRhythm("Pioneer_C", PIONEER, env, roster, starts[2]),
    NPCWithCircadianRhythm("Guardian_D", GUARDIAN, env, roster, starts[3]),
    NPCWithCircadianRhythm("Scavenger_E", SCAVENGER, env, roster, starts[4]),
]

for n in npcs:
    roster[n.name] = n

# Run
print("=== SSD + Day/Night Cycle Simulation ===")
print(f"Day length: {env.day_night.day_length} ticks")
print(f"Night: {env.day_night.night_start*100:.0f}% - {env.day_night.night_end*100:.0f}% of day")
print(f"NPCs: {len(npcs)}\n")

TICKS = 240  # 5日分
for t in range(TICKS):
    for n in npcs:
        n.step(t)
    env.step()
    
    if t % 48 == 0:
        day_num = t // 48
        alive_count = sum(1 for n in npcs if n.alive)
        phase = env.day_night.get_phase_name()
        print(f"Day {day_num}, {phase}: {alive_count}/5 alive")

print("\n=== Simulation Complete ===\n")

# Analysis
df_logs = pd.concat([pd.DataFrame(n.log) for n in npcs], ignore_index=True)

death_events = df_logs[df_logs["action"] == "death"]
sleep_events = df_logs[df_logs["action"].isin(["sleep_start", "wake_up"])]

print("=== DEATH EVENTS ===")
if not death_events.empty:
    print(death_events[["t", "name", "time_of_day", "hunger", "E", "jump_rate"]])
else:
    print("No deaths!")

print("\n=== SLEEP STATISTICS ===")
for npc in npcs:
    if npc.alive:
        print(f"{npc.name}:")
        print(f"  Total sleep: {npc.total_sleep_time} ticks")
        print(f"  Sleep cycles: {npc.sleep_cycles}")
        print(f"  Avg sleep length: {npc.total_sleep_time/max(1,npc.sleep_cycles):.1f} ticks")
        print(f"  Final κ_forage: {npc.kappa['forage']:.3f}")

# Visualization
fig, axes = plt.subplots(3, 2, figsize=(16, 12))

# 1. Light level over time
time_data = np.arange(0, TICKS)
light_levels = []
for t in time_data:
    env.day_night.current_tick = t
    light_levels.append(env.day_night.get_light_level())

axes[0, 0].fill_between(time_data, 0, light_levels, alpha=0.3, color='gold', label='Light level')
axes[0, 0].set_xlabel("Time")
axes[0, 0].set_ylabel("Light Level")
axes[0, 0].set_title("Day/Night Cycle", fontweight='bold')
axes[0, 0].set_ylim(0, 1.1)
axes[0, 0].grid(alpha=0.3)

# Add day markers
for day in range(TICKS // 48 + 1):
    axes[0, 0].axvline(x=day * 48, color='gray', linestyle='--', alpha=0.5)

# 2. Sleep patterns (timeline)
for i, npc in enumerate(npcs):
    sleep_data = df_logs[(df_logs["name"] == npc.name) & (df_logs["state"] == "Sleep")]
    if not sleep_data.empty:
        for _, row in sleep_data.iterrows():
            axes[0, 1].barh(i, 1, left=row["t"], height=0.8, 
                          color='blue' if row["action"] == "sleeping" or row["action"] == "sleep_start" else 'cyan',
                          alpha=0.6)

axes[0, 1].set_yticks(range(len(npcs)))
axes[0, 1].set_yticklabels([n.name for n in npcs])
axes[0, 1].set_xlabel("Time")
axes[0, 1].set_title("Sleep Patterns (Blue = Sleeping)", fontweight='bold')
axes[0, 1].grid(alpha=0.3, axis='x')

# 続き...

# 3. Hunger over time with day/night
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    axes[1, 0].plot(g["t"], g["hunger"], label=name, linewidth=2)
    d = g[g["action"] == "death"]
    if not d.empty:
        axes[1, 0].scatter(d["t"], d["hunger"], marker="X", s=200, 
                          c='red', edgecolors='black', linewidths=2, zorder=5)

# Add night shading
for day in range(TICKS // 48 + 1):
    night_start_tick = day * 48 + int(48 * 0.6)
    night_end_tick = day * 48 + int(48 * 0.9)
    axes[1, 0].axvspan(night_start_tick, night_end_tick, alpha=0.15, color='navy')

axes[1, 0].set_xlabel("Time")
axes[1, 0].set_ylabel("Hunger")
axes[1, 0].legend()
axes[1, 0].set_title("Hunger (Gray = Night)", fontweight='bold')
axes[1, 0].axhline(y=100, color='red', linestyle='--', alpha=0.5)
axes[1, 0].grid(alpha=0.3)

# 4. Sleep debt over time
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    sleep_debt_data = g[g["sleep_debt"].notna()]
    if not sleep_debt_data.empty:
        axes[1, 1].plot(sleep_debt_data["t"], sleep_debt_data["sleep_debt"], 
                       label=name, linewidth=2)

axes[1, 1].set_xlabel("Time")
axes[1, 1].set_ylabel("Sleep Debt")
axes[1, 1].legend()
axes[1, 1].set_title("Sleep Debt Accumulation", fontweight='bold')
axes[1, 1].axhline(y=150, color='red', linestyle='--', alpha=0.5, label='Forced sleep threshold')
axes[1, 1].grid(alpha=0.3)

# 5. Heat (E) over time with day/night
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    if "E" in g.columns:
        axes[2, 0].plot(g["t"], g["E"], label=name, linewidth=2)

# Add night shading
for day in range(TICKS // 48 + 1):
    night_start_tick = day * 48 + int(48 * 0.6)
    night_end_tick = day * 48 + int(48 * 0.9)
    axes[2, 0].axvspan(night_start_tick, night_end_tick, alpha=0.15, color='navy')

axes[2, 0].set_xlabel("Time")
axes[2, 0].set_ylabel("Unprocessed Pressure (E)")
axes[2, 0].legend()
axes[2, 0].set_title("Heat Accumulation (Gray = Night)", fontweight='bold')
axes[2, 0].grid(alpha=0.3)

# 6. Activity by time of day
activity_by_phase = df_logs.groupby(["time_of_day", "action"]).size().reset_index(name="count")
activity_pivot = activity_by_phase.pivot(index="time_of_day", columns="action", values="count").fillna(0)

# Select key actions
key_actions = ["eat_success", "eat_fail", "sleep_start", "night_rest", "patrol"]
available_actions = [a for a in key_actions if a in activity_pivot.columns]

if available_actions:
    activity_pivot[available_actions].plot(kind="bar", stacked=True, ax=axes[2, 1])
    axes[2, 1].set_xlabel("Time of Day")
    axes[2, 1].set_ylabel("Action Count")
    axes[2, 1].set_title("Activity Distribution by Time", fontweight='bold')
    axes[2, 1].legend(title="Action", bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[2, 1].grid(alpha=0.3, axis='y')
    plt.setp(axes[2, 1].xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('ssd_daynight_simulation.png', dpi=150, bbox_inches='tight')
print("\n=== Plot saved as 'ssd_daynight_simulation.png' ===")
plt.show()

# === Additional Analysis ===

print("\n=== CIRCADIAN ANALYSIS ===")

# Sleep efficiency by time of day
sleep_starts = df_logs[df_logs["action"] == "sleep_start"]
if not sleep_starts.empty:
    print("\nSleep initiation by phase:")
    print(sleep_starts.groupby("time_of_day").size())

# Night activity analysis
night_activities = df_logs[df_logs["time_of_day"].isin(["Night", "Late_Night"])]
night_active = night_activities[night_activities["action"].isin(["eat_success", "eat_fail", "patrol"])]

if not night_active.empty:
    print("\n=== NIGHT OWLS (NPCs active at night) ===")
    night_counts = night_active.groupby("name").size().reset_index(name="night_actions")
    print(night_counts.sort_values("night_actions", ascending=False))
    
    # Risk analysis
    for npc in npcs:
        night_acts = night_active[night_active["name"] == npc.name]
        if len(night_acts) > 10:
            total_acts = len(df_logs[df_logs["name"] == npc.name])
            night_ratio = len(night_acts) / total_acts
            print(f"\n{npc.name}: {night_ratio*100:.1f}% night activity")
            print(f"  curiosity={npc.curiosity:.2f}, avoidance={npc.avoidance:.2f}")
            print(f"  Survived: {npc.alive}")

# Correlation: Night activity vs survival
print("\n=== NIGHT ACTIVITY vs SURVIVAL ===")
for npc in npcs:
    npc_logs = df_logs[df_logs["name"] == npc.name]
    night_logs = npc_logs[npc_logs["time_of_day"].isin(["Night", "Late_Night"])]
    night_active_count = len(night_logs[night_logs["action"].isin(["eat_success", "eat_fail", "patrol"])])
    
    status = "ALIVE" if npc.alive else "DEAD"
    print(f"{npc.name}: {night_active_count} night actions → {status}")

# Sleep quality analysis
print("\n=== SLEEP QUALITY ANALYSIS ===")
wake_events = df_logs[df_logs["action"] == "wake_up"]
if not wake_events.empty:
    print("\nWake reasons:")
    print(wake_events.groupby("wake_reason").size())
    
    print("\nAverage sleep duration by NPC:")
    for npc in npcs:
        if npc.alive and npc.sleep_cycles > 0:
            avg_sleep = npc.total_sleep_time / npc.sleep_cycles
            print(f"{npc.name}: {avg_sleep:.1f} ticks/cycle")

# Memory consolidation tracking
print("\n=== MEMORY CONSOLIDATION (κ changes) ===")
for npc in npcs:
    if npc.alive:
        npc_logs = df_logs[df_logs["name"] == npc.name]
        
        # κ at start vs end
        forage_logs = npc_logs[npc_logs["kappa_forage"].notna()]
        if not forage_logs.empty:
            initial_kappa = forage_logs.iloc[0]["kappa_forage"]
            final_kappa = forage_logs.iloc[-1]["kappa_forage"]
            change = final_kappa - initial_kappa
            
            print(f"{npc.name}:")
            print(f"  κ_forage: {initial_kappa:.3f} → {final_kappa:.3f} (Δ{change:+.3f})")
            print(f"  Sleep cycles: {npc.sleep_cycles}")

# Time of death analysis
if not death_events.empty:
    print("\n=== TIME OF DEATH ANALYSIS ===")
    for _, death in death_events.iterrows():
        print(f"{death['name']}: died at t={death['t']}, {death['time_of_day']}")
        print(f"  E={death['E']:.2f}, jump_rate={death['jump_rate']:.3f}")

# CSV export with additional columns
df_logs.to_csv("ssd_daynight_logs.csv", index=False)
print("\n=== Logs saved to 'ssd_daynight_logs.csv' ===")

# === Summary Statistics ===
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)

survivors = [n for n in npcs if n.alive]
deceased = [n for n in npcs if not n.alive]

print(f"\nSurvivors: {len(survivors)}/{len(npcs)}")
if survivors:
    print("  " + ", ".join([n.name for n in survivors]))

if deceased:
    print(f"\nDeceased: {len(deceased)}/{len(npcs)}")
    print("  " + ", ".join([n.name for n in deceased]))

# Personality correlations with survival
print("\n=== PERSONALITY vs SURVIVAL ===")
survival_data = []
for npc in npcs:
    survival_data.append({
        "name": npc.name,
        "survived": npc.alive,
        "curiosity": npc.curiosity,
        "avoidance": npc.avoidance,
        "stamina": npc.stamina,
        "empathy": npc.empathy,
        "total_sleep": npc.total_sleep_time,
        "sleep_cycles": npc.sleep_cycles
    })

df_survival = pd.DataFrame(survival_data)
print("\n", df_survival)

# Key insights
print("\n=== KEY INSIGHTS ===")

# 1. Sleep patterns
avg_sleep_per_npc = df_survival["total_sleep"].mean()
print(f"1. Average total sleep time: {avg_sleep_per_npc:.0f} ticks")

# 2. Night activity risk
if not night_active.empty:
    night_active_npcs = night_active.groupby("name").size()
    print(f"2. Most night-active NPC: {night_active_npcs.idxmax()} ({night_active_npcs.max()} actions)")

# 3. Survival factors
if len(survivors) > 0 and len(deceased) > 0:
    survivor_avg_avoidance = df_survival[df_survival["survived"]]["avoidance"].mean()
    deceased_avg_avoidance = df_survival[~df_survival["survived"]]["avoidance"].mean()
    
    print(f"3. Avoidance trait:")
    print(f"   Survivors: {survivor_avg_avoidance:.2f}")
    print(f"   Deceased: {deceased_avg_avoidance:.2f}")
    
    if survivor_avg_avoidance > deceased_avg_avoidance:
        print("   → Higher avoidance correlated with survival")
    else:
        print("   → Lower avoidance in survivors (risky behavior paid off)")

# 4. Heat management
if len(survivors) > 0:
    final_E_values = []
    for npc in survivors:
        npc_logs = df_logs[df_logs["name"] == npc.name]
        if not npc_logs.empty:
            final_E = npc_logs.iloc[-1]["E"]
            final_E_values.append(final_E)
    
    if final_E_values:
        avg_final_E = np.mean(final_E_values)
        print(f"4. Survivors' final avg heat (E): {avg_final_E:.2f}")

print("\n" + "="*60)