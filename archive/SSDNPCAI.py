import random, math
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

random.seed(55); np.random.seed(55)

# -------- Environment (同じ) --------
class EnvScarce:
    def __init__(self, size=26, n_berry=7, n_hunt=5):
        self.size = size
        self.berries = {}
        for _ in range(n_berry):
            x,y = random.randrange(size), random.randrange(size)
            self.berries[(x,y)] = {"abundance": random.uniform(0.2,0.6), "regen": random.uniform(0.003,0.015)}
        self.huntzones = {}
        for _ in range(n_hunt):
            x,y = random.randrange(size), random.randrange(size)
            self.huntzones[(x,y)] = {"base_success": random.uniform(0.15,0.45), "danger": random.uniform(0.25,0.65)}
        self.t=0
    
    def step(self):
        for v in self.berries.values():
            v["abundance"] = min(1.0, v["abundance"] + v["regen"]*(1.0 - v["abundance"]))
        for v in self.huntzones.values():
            v["base_success"] = float(np.clip(v["base_success"]+np.random.normal(0,0.01),0.03,0.8))
        self.t+=1
    
    def nearest_nodes(self, pos, node_dict, k=4):
        nodes=list(node_dict.keys())
        nodes.sort(key=lambda p: abs(p[0]-pos[0])+abs(p[1]-pos[1]))
        return nodes[:k]
    
    def forage(self,pos,node):
        abundance=self.berries[node]["abundance"]
        dist=abs(pos[0]-node[0])+abs(pos[1]-node[1])
        p=0.6*abundance+0.2*max(0,1-dist/12)
        success=random.random()<p
        if success:
            self.berries[node]["abundance"]=max(0.0,self.berries[node]["abundance"]-random.uniform(0.2,0.4))
            food=random.uniform(10,20)*(0.5+abundance/2)
        else: food=0.0
        risk=0.05
        return success,food,risk,p
    
    def hunt(self,pos,node,injury_factor=1.0,coop_bonus=0.0):
        zone=self.huntzones[node]
        base=zone["base_success"]
        dist=abs(pos[0]-node[0])+abs(pos[1]-node[1])
        p=base*max(0.15,1-dist/14)
        p*=injury_factor; p*=(1+coop_bonus)
        p=float(np.clip(p,0.01,0.95))
        success=random.random()<p
        if success:
            food=random.uniform(20,45)*(0.5+base/2)*(1+0.25*coop_bonus)
        else: food=0.0
        risk=zone["danger"]*(0.9+dist/18)
        return success,food,risk,p


# -------- NPC with SSD Mathematical Model --------
class NPCWithSSD:
    def __init__(self, name, preset, env, roster_ref, start_pos):
        self.name = name
        self.env = env
        self.roster_ref = roster_ref
        self.x, self.y = start_pos
        
        # === 生理的状態 ===
        self.hunger = 50.0
        self.fatigue = 30.0
        self.injury = 0.0
        self.alive = True
        self.state = "Idle"
        
        # === SSD数理モデルパラメータ ===
        self.kappa = defaultdict(lambda: 0.1)
        self.kappa_min = 0.05
        self.E = 0.0
        self.T = 0.3
        
        # パラメータ
        self.G0 = 0.5
        self.g = 0.7
        self.eta = 0.3
        self.lambda_forget = 0.02
        self.rho = 0.1
        self.alpha = 0.6
        self.beta_E = 0.15
        
        # 跳躍パラメータ
        self.Theta0 = 1.0
        self.a1 = 0.5
        self.a2 = 0.4
        self.h0 = 0.2
        self.gamma = 0.8
        
        # 温度制御パラメータ
        self.T0 = 0.3
        self.c1 = 0.5
        self.c2 = 0.6
        
        # キャラクター特性
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
                    "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                    "injury": round(self.injury, 1),
                    "E": round(self.E, 2), "T": round(self.T, 2),
                    "kappa_help": round(self.kappa["help"], 3)
                })
                return True
            
            elif best.injury > 30 or best.fatigue > 85:
                best.fatigue = max(0, best.fatigue - 28.0 * (1 + 0.2 * self.stamina))
                best.injury = max(0, best.injury - 7.0)
                self.fatigue = min(100, self.fatigue + 6.0)
                self.rel[best.name] += 0.1
                best.rel[self.name] += 0.05
                best.help_debt[self.name] += 0.25
                
                self.update_kappa("help", True, 20.0)
                
                self.log.append({
                    "t": t, "name": self.name, "state": "Help", "action": "escort_rest",
                    "target": best.name, "amount": 0,
                    "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                    "injury": round(self.injury, 1),
                    "E": round(self.E, 2), "T": round(self.T, 2),
                    "kappa_help": round(self.kappa["help"], 3)
                })
                return True
        
        return False
    
    def step(self, t):
        if not self.alive:
            return
        
        # 代謝
        hunger_pressure = 1.8
        fatigue_pressure = 0.8
        self.hunger = min(120, self.hunger + hunger_pressure)
        self.fatigue = min(120, self.fatigue + fatigue_pressure)
        self.injury = min(120, self.injury + 0.02 * self.fatigue / 100)
        
        # 跳躍判定（死）
        if self.hunger >= 100 or self.injury >= 100:
            leap_occurred, h, Theta = self.check_leap()
            if leap_occurred or self.hunger >= 110 or self.injury >= 110:
                self.alive = False
                self.log.append({
                    "t": t, "name": self.name, "state": "Dead", "action": "death",
                    "target": "", "amount": 0,
                    "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                    "injury": round(self.injury, 1),
                    "E": round(self.E, 2), "jump_rate": round(h, 3), "Theta": round(Theta, 2)
                })
                return
        
        # 探索温度の更新
        self.update_temperature()
        
        # ヘルプ判定
        if self.maybe_help(t):
            return
        
        # 休息判定
        if self.fatigue > self.TH_F and self.hunger < self.TH_H * 0.9:
            rest_amount = 30 * (1 + 0.25 * self.stamina)
            self.fatigue = max(0, self.fatigue - rest_amount)
            self.hunger = min(100, self.hunger + 6)
            self.injury = max(0, self.injury - 4 * (1 + 0.1 * self.stamina))
            
            self.update_kappa("rest", True, rest_amount)
            self.update_heat(fatigue_pressure, rest_amount / 30)
            
            self.log.append({
                "t": t, "name": self.name, "state": "Sleep", "action": "sleep",
                "target": "", "amount": rest_amount,
                "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                "injury": round(self.injury, 1),
                "E": round(self.E, 2), "T": round(self.T, 2),
                "kappa_rest": round(self.kappa["rest"], 3)
            })
        
        # 採餌判定
        elif self.hunger > self.TH_H:
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
                        "target": "Berry", "amount": round(food, 1),
                        "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                        "injury": round(self.injury, 1),
                        "E": round(self.E, 2), "T": round(self.T, 2),
                        "kappa_forage": round(self.kappa["forage"], 3)
                    })
                else:
                    self.update_kappa("forage", False, 0)
                    self.update_heat(meaning_p, 0)
                    
                    self.log.append({
                        "t": t, "name": self.name, "state": "Food", "action": "eat_fail",
                        "target": "Berry", "amount": 0,
                        "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                        "injury": round(self.injury, 1),
                        "E": round(self.E, 2), "T": round(self.T, 2),
                        "kappa_forage": round(self.kappa["forage"], 3)
                    })
            else:
                self.update_heat(meaning_p, 0)
                
                self.log.append({
                    "t": t, "name": self.name, "state": "Food", "action": "starve",
                    "target": "", "amount": 0,
                    "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                    "injury": round(self.injury, 1),
                    "E": round(self.E, 2), "T": round(self.T, 2)
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
                "target": "", "amount": 0,
                "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1),
                "injury": round(self.injury, 1),
                "E": round(self.E, 2), "T": round(self.T, 2),
                "boredom": round(self.boredom, 2)
            })


# Presets
FORAGER = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
SCAVENGER = {"risk_tolerance": 0.3, "curiosity": 0.6, "avoidance": 0.7, "stamina": 0.5, "empathy": 0.5}

# Setup
env = EnvScarce()
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
    NPCWithSSD("Forager_A", FORAGER, env, roster, starts[0]),
    NPCWithSSD("Tracker_B", TRACKER, env, roster, starts[1]),
    NPCWithSSD("Pioneer_C", PIONEER, env, roster, starts[2]),
    NPCWithSSD("Guardian_D", GUARDIAN, env, roster, starts[3]),
    NPCWithSSD("Scavenger_E", SCAVENGER, env, roster, starts[4]),
]

for n in npcs:
    roster[n.name] = n

# Run
print("=== Starting SSD-Integrated Simulation ===")
print(f"Environment: {len(env.berries)} berry nodes, {len(env.huntzones)} hunt zones")
print(f"NPCs: {len(npcs)}")
print()

TICKS = 180
for t in range(TICKS):
    for n in npcs:
        n.step(t)
    env.step()
    
    if t % 30 == 0:
        alive_count = sum(1 for n in npcs if n.alive)
        print(f"Tick {t}: {alive_count}/5 NPCs alive")

print("\n=== Simulation Complete ===\n")

# Analysis
df_logs = pd.concat([pd.DataFrame(n.log) for n in npcs], ignore_index=True)

death_events = df_logs[df_logs["action"] == "death"]
help_events = df_logs[df_logs["action"].isin(["share_food", "escort_rest"])]

print("=== DEATH EVENTS ===")
if not death_events.empty:
    print(death_events[["t", "name", "hunger", "injury", "E", "jump_rate", "Theta"]])
else:
    print("No deaths occurred!")

print("\n=== HELP EVENTS (first 10) ===")
if not help_events.empty:
    print(help_events[["t", "name", "target", "action", "E", "T"]].head(10))
else:
    print("No help events occurred!")

print("\n=== FINAL STATUS ===")
for npc in npcs:
    status = "ALIVE" if npc.alive else "DEAD"
    print(f"{npc.name}: {status}")
    if npc.alive:
        print(f"  κ_forage: {npc.kappa['forage']:.3f}")
        print(f"  κ_rest: {npc.kappa['rest']:.3f}")
        print(f"  κ_help: {npc.kappa['help']:.3f}")
        print(f"  E (heat): {npc.E:.2f}")
        print(f"  Hunger: {npc.hunger:.1f}, Fatigue: {npc.fatigue:.1f}")

# Visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Hunger over time
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    axes[0, 0].plot(g["t"], g["hunger"], label=name, linewidth=2)
    d = g[g["action"] == "death"]
    if not d.empty:
        axes[0, 0].scatter(d["t"], d["hunger"], marker="X", s=200, c='red', edgecolors='black', linewidths=2, zorder=5)
axes[0, 0].set_xlabel("Time", fontsize=12)
axes[0, 0].set_ylabel("Hunger", fontsize=12)
axes[0, 0].legend()
axes[0, 0].set_title("Hunger over Time (Deaths marked with X)", fontsize=13, fontweight='bold')
axes[0, 0].axhline(y=100, color='red', linestyle='--', alpha=0.5, label='Death threshold')
axes[0, 0].grid(alpha=0.3)

# 2. Heat (E) over time
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    if "E" in g.columns:
        axes[0, 1].plot(g["t"], g["E"], label=name, linewidth=2)
axes[0, 1].set_xlabel("Time", fontsize=12)
axes[0, 1].set_ylabel("Unprocessed Pressure (E)", fontsize=12)
axes[0, 1].legend()
axes[0, 1].set_title("Heat Accumulation (E)", fontsize=13, fontweight='bold')
axes[0, 1].grid(alpha=0.3)

# 3. Temperature (T) over time
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    if "T" in g.columns:
        axes[1, 0].plot(g["t"], g["T"], label=name, linewidth=2)
axes[1, 0].set_xlabel("Time", fontsize=12)
axes[1, 0].set_ylabel("Exploration Temperature (T)", fontsize=12)
axes[1, 0].legend()
axes[1, 0].set_title("Exploration Temperature", fontsize=13, fontweight='bold')
axes[1, 0].grid(alpha=0.3)

# 4. Kappa (forage) over time
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    forage_logs = g[g["kappa_forage"].notna()]
    if not forage_logs.empty:
        axes[1, 1].plot(forage_logs["t"], forage_logs["kappa_forage"], label=name, linewidth=2)
axes[1, 1].set_xlabel("Time", fontsize=12)
axes[1, 1].set_ylabel("κ (forage)", fontsize=12)
axes[1, 1].legend()
axes[1, 1].set_title("Alignment Inertia (Forage)", fontsize=13, fontweight='bold')
axes[1, 1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('ssd_simulation_results.png', dpi=150, bbox_inches='tight')
print("\n=== Plot saved as 'ssd_simulation_results.png' ===")
plt.show()

# Save logs
df_logs.to_csv("npc5_ssd_integrated_logs.csv", index=False)
print("=== Logs saved to 'npc5_ssd_integrated_logs.csv' ===")