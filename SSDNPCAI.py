import random, math
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

random.seed(55); np.random.seed(55)

# ----------------------------------------------------------------------
# 1. EnvScarce クラス (環境) - 修正なし (距離計算はNPC側で処理)
# ----------------------------------------------------------------------
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
        # 距離の影響を考慮して成功率を計算
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
        # 距離、怪我、協力の影響を考慮して成功率を計算
        p=base*max(0.15,1-dist/14)
        p*=injury_factor; p*=(1+coop_bonus)
        p=float(np.clip(p,0.01,0.95))
        success=random.random()<p
        if success:
            food=random.uniform(20,45)*(0.5+base/2)*(1+0.25*coop_bonus)
        else: food=0.0
        risk=zone["danger"]*(0.9+dist/18)
        return success,food,risk,p


# ----------------------------------------------------------------------
# 2. NPCWithSSD クラス (キャラクター) - 修正と狩猟行動の追加
# ----------------------------------------------------------------------
class NPCWithSSD:
    """
    構造主観力学（Structural Subjectivity Dynamics, SSD）モデルを実装したNPCエージェント。
    このクラスは、SSD理論に基づいた動的な意思決定プロセスを持ち、
    生理的・心理的な「意味圧」に応じて自律的に行動する。
    """
    def __init__(self, name, preset, env, roster_ref, start_pos):
        self.name = name
        self.x, self.y = start_pos
        self.env = env
        self.roster_ref = roster_ref
        
        self.alive = True
        self.state = "Idle"
        self.action_type = None
        self.target_pos = None
        self.target_node = None
        self.coop_target = None
        
        # 生理状態
        self.hunger = 50.0
        self.fatigue = 30.0
        self.injury = 0.0
        
        # --- 構造主観力学 (SSD) パラメータ ---
        # 理論上の各概念とコード上の変数の対応:
        #   - 整合慣性 (κ, kappa): 各行動への習熟度や習慣の強さ。高いほどその行動が選択されやすい。
        #   - 熱 (E, Heat): 処理されなかった意味圧の蓄積。ストレスや衝動性の源泉。
        #   - 探索温度 (T, Temperature): 行動の多様性を制御する。Tが高いと普段取らない行動も選択しやすくなる。
        #   - 跳躍 (Leap): Eが極度に高まった際に発生する、死などの非連続的な状態変化。

        # 整合(Alignment)関連パラメータ
        self.kappa = defaultdict(lambda: 0.1) # κ: 各行動タイプの整合慣性 (初期値は低め)
        self.kappa['forage'] = 0.8             # ★修正: 根源的欲求の初期値を高く設定
        self.kappa['hunt'] = 0.6               # ★修正: 根源的欲求の初期値を高く設定
        self.kappa['rest'] = 1.0               # ★修正: 根源的欲求の初期値を高く設定
        self.kappa['help'] = 0.1
        self.kappa['patrol'] = 0.1
        self.kappa_min = 0.05                  # κの最小値
        self.G0 = 0.1                          # 基礎整合流係数
        self.g = 0.05                          # 慣性依存係数
        self.eta = 0.2                         # ★修正: 報酬によるκ学習率 (0.01 -> 0.2)

        # 熱(Heat)関連パラメータ
        self.E = 0.0                           # E: 熱 (未処理の意味圧の蓄積量)
        self.alpha = 0.6                       # 熱の蓄積係数
        self.beta_E = 0.15                     # 熱の自然散逸係数

        # 忘却(Forgetting)関連パラメータ
        self.lambda_forget = 0.02              # 選択された行動のκ忘却係数
        self.lambda_forget_other = 0.002       # 未選択行動のκ忘却係数
        self.rho = 0.05                        # ★修正: 失敗時のκペナルティ係数 (0.1 -> 0.05)

        # 跳躍(Leap)関連パラメータ
        self.Theta0 = 1.0                      # 跳躍発生の基礎閾値
        self.a1 = 0.5                          # κ平均による閾値上昇係数
        self.a2 = 0.4                          # 疲労による閾値下降係数
        self.h0 = 0.2                          # 跳躍レートの基礎係数
        self.gamma = 0.8                       # Eが閾値を超えた際の跳躍レート感度

        # 温度(Temperature)関連パラメータ
        self.T = 0.3                           # T: 探索温度
        self.T0 = 0.3                          # ★修正: 基礎温度を0.3に戻す
        self.c1 = 0.7                          # Eによる温度上昇係数
        self.c2 = 0.6                          # κエントロピーによる温度下降係数
        
        # キャラクター特性
        p = preset
        self.risk_tolerance = p["risk_tolerance"]
        self.curiosity = p["curiosity"]
        self.avoidance = p["avoidance"]
        self.stamina = p["stamina"]
        self.empathy = p.get("empathy", 0.6)
        
        # 閾値
        self.TH_H = 55.0
        self.TH_F = 70.0
        self.TH_I = 40.0
        self.TH_B = 60.0
        self.TH_JUMP_FATIGUE = 100.0
        
        self.rel = defaultdict(float)
        self.help_debt = defaultdict(float)
        
        self.log = []
        self.boredom = 0.0
    
    def pos(self):
        return (self.x, self.y)
    
    def dist_to(self, target_pos):
        return abs(self.x - target_pos[0]) + abs(self.y - target_pos[1])
    
    def move_towards(self, target):
        tx, ty = target
        dx = (1 if tx > self.x else -1 if tx < self.x else 0)
        dy = (1 if ty > self.y else -1 if ty < self.y else 0)
        
        if dx != 0 and dy != 0:
            if random.random() < 0.5: dy = 0
            else: dx = 0
        
        self.x += dx
        self.y += dy
        self.fatigue = min(120, self.fatigue + 0.2)
        return (self.x, self.y) == target

    def nearby_allies(self, radius=3):
        return [o for on, o in self.roster_ref.items() 
                if on != self.name and o.alive and self.dist_to(o.pos()) <= radius]
    
    # --- SSD コア計算メソッド群 ---

    def alignment_flow(self, action_type, meaning_pressure):
        """
        理論式: J = (G0 + g*κ) * P_meaning
        特定の行動(action_type)が、ある意味圧(meaning_pressure)をどれだけ処理できるかの流量(J)を計算する。
        整合慣性κが高いほど、同じ意味圧からより大きな整合流を生み出せる。
        """
        kappa = self.kappa[action_type]
        j = (self.G0 + self.g * kappa) * meaning_pressure
        return j
    
    def update_kappa(self, action_type, success, reward, chosen_action):
        """
        整合慣性κを更新する（学習と忘却）。
        - 実行した行動(chosen_action)は、成功すれば報酬(reward)に応じてκが増加し、失敗すればペナルティを受ける。
        - 実行されなかった他の行動のκは、lambda_forget_other分だけ僅かに減少（忘却）する。
        """
        for at in list(self.kappa.keys()):
            if at != chosen_action:
                self.kappa[at] = max(self.kappa_min, self.kappa[at] - self.lambda_forget_other)

        kappa = self.kappa[action_type]
        
        if success:
            work = self.eta * reward
        else:
            work = -self.rho * (kappa ** 2)
        
        decay = self.lambda_forget * (kappa - self.kappa_min)
        self.kappa[action_type] = max(self.kappa_min, kappa + work - decay)
    
    def update_heat(self, meaning_pressure, processed_amount):
        """
        熱Eを更新する。
        意味圧(meaning_pressure)が行動によって処理(processed_amount)しきれなかった場合、
        その残差が熱(E)として蓄積される。熱は自然にも少しずつ散逸する。
        """
        unprocessed = max(0, meaning_pressure - processed_amount)
        self.E += self.alpha * unprocessed - self.beta_E * self.E
        self.E = max(0, self.E)
    
    def check_leap(self):
        """
        跳躍（死などの非連続的な状態変化）の発生を判定する。
        - 熱Eが、現在のκの平均や疲労度から決まる閾値Θ(Theta)をどれだけ超えているかに基づいて、
          跳躍レートhが指数関数的に増加する。
        - このhから計算される確率で跳躍が発生する。
        """
        mean_kappa = np.mean(list(self.kappa.values())) if self.kappa else 0.1
        fatigue_factor = self.fatigue / 100.0
        Theta = self.Theta0 + self.a1 * mean_kappa - self.a2 * fatigue_factor
        
        h = self.h0 * np.exp((self.E - Theta) / self.gamma)
        jump_prob = 1 - np.exp(-h * 1.0)
        
        if random.random() < jump_prob:
            return True, h, Theta
        return False, h, Theta
    
    def update_temperature(self):
        """
        探索温度Tを更新する。
        - 熱Eが高いほど、Tは上昇する（衝動的・探索的になる）。
        - κの多様性(標準偏差で代用)が高い（色々な行動が満遍なく得意）ほど、Tは下降する（安定する）。
        """
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
        if self.state == "Helping":
            if not self.coop_target or not self.coop_target.alive:
                self.state = "Idle"; self.coop_target = None; return False
            
            best = self.coop_target
            if self.hunger < 85 and best.hunger > 75:
                delta = 15.0
                self.hunger = min(100.0, self.hunger + 3.0); best.hunger = max(0.0, best.hunger - delta)
                self.rel[best.name] += 0.04; best.rel[self.name] += 0.02; best.help_debt[self.name] += 0.1
                self.update_kappa("help", True, delta * 0.2, "help")
                self.log.append({"t": t, "name": self.name, "state": "Helping", "action": "share_food_cont", "target": best.name, "amount": delta, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_help": round(self.kappa["help"], 3)})
                return True
            elif best.injury > 30 or best.fatigue > 85:
                best.fatigue = max(0, best.fatigue - 14.0 * (1 + 0.1 * self.stamina)); best.injury = max(0, best.injury - 3.0)
                self.fatigue = min(100, self.fatigue + 3.0)
                self.rel[best.name] += 0.05; best.rel[self.name] += 0.02; best.help_debt[self.name] += 0.1
                self.update_kappa("help", True, 10.0, "help")
                self.log.append({"t": t, "name": self.name, "state": "Helping", "action": "escort_rest_cont", "target": best.name, "amount": 0, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_help": round(self.kappa["help"], 3)})
                if best.hunger <= 75 and best.injury <= 30 and best.fatigue <= 85: self.state = "Idle"; self.coop_target = None
                return True
            else:
                self.state = "Idle"; self.coop_target = None; return False

        allies = self.nearby_allies(radius=2) # ★修正: 範囲を3から2に
        if not allies: return False
        
        best = None; bestu = 0.0
        for o in allies:
            if o.state == "Helping": continue
            u = self.help_utility(o)
            if u > bestu: bestu = u; best = o
        
        if best and bestu > 0.06: # ★修正: 閾値を0.08から0.06に
            self.state = "Helping"; self.coop_target = best
            if self.hunger < 85 and best.hunger > 75:
                delta = 25.0
                self.hunger = min(100.0, self.hunger + 6.0); best.hunger = max(0.0, best.hunger - delta)
                self.rel[best.name] += 0.08; best.rel[self.name] += 0.04; best.help_debt[self.name] += 0.2
                self.update_kappa("help", True, delta * 0.5, "help")
                self.log.append({"t": t, "name": self.name, "state": "Helping", "action": "share_food_start", "target": best.name, "amount": delta, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_help": round(self.kappa["help"], 3)})
                return True
            elif best.injury > 30 or best.fatigue > 85:
                best.fatigue = max(0, best.fatigue - 28.0 * (1 + 0.2 * self.stamina)); best.injury = max(0, best.injury - 7.0)
                self.fatigue = min(100, self.fatigue + 6.0)
                self.rel[best.name] += 0.1; best.rel[self.name] += 0.05; best.help_debt[self.name] += 0.25
                self.update_kappa("help", True, 20.0, "help")
                self.log.append({"t": t, "name": self.name, "state": "Helping", "action": "escort_rest_start", "target": best.name, "amount": 0, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_help": round(self.kappa["help"], 3)})
                return True
            else:
                self.state = "Idle"; self.coop_target = None; return False
        return False

    def do_forage(self, t):
        if self.action_type == "forage" and self.target_pos:
            if self.pos() != self.target_pos:
                self.move_towards(self.target_pos)
                self.log.append({"t": t, "name": self.name, "state": "Moving", "action": "move_forage", "target": self.target_pos, "amount": self.dist_to(self.target_pos), "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2)})
                return True
            else:
                self.state = "Foraging"
                node = self.target_node
                success, food, risk, p = self.env.forage(self.pos(), node)
                meaning_p = (self.hunger - self.TH_H) / (100 - self.TH_H)
                j_forage = self.alignment_flow("forage", meaning_p)
                if success:
                    self.hunger = max(0, self.hunger - food); self.fatigue = min(100, self.fatigue + 1.0)
                    self.update_kappa("forage", True, food, "forage"); self.update_heat(meaning_p, j_forage)
                    self.log.append({"t": t, "name": self.name, "state": "Foraging", "action": "eat_success", "target": "Berry", "amount": round(food, 1), "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_forage": round(self.kappa["forage"], 3)})
                else:
                    self.fatigue = min(100, self.fatigue + 2.0)
                    self.update_kappa("forage", False, 0, "forage"); self.update_heat(meaning_p, 0)
                    self.log.append({"t": t, "name": self.name, "state": "Foraging", "action": "eat_fail", "target": "Berry", "amount": 0, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_forage": round(self.kappa["forage"], 3)})
                self.state = "Idle"; self.target_pos = None; self.target_node = None; self.action_type = None
                return True
        return False

    def do_hunt(self, t):
        if self.action_type == "hunt" and self.target_pos:
            if self.pos() != self.target_pos:
                self.move_towards(self.target_pos)
                self.log.append({"t": t, "name": self.name, "state": "Moving", "action": "move_hunt", "target": self.target_pos, "amount": self.dist_to(self.target_pos), "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2)})
                return True
            else:
                self.state = "Hunting"
                node = self.target_node
                allies = self.nearby_allies(radius=1); coop_bonus = len(allies) * 0.15 * (1 + self.empathy)
                injury_factor = 1.0 - self.injury / 100.0
                success, food, risk, p = self.env.hunt(self.pos(), node, injury_factor, coop_bonus)
                meaning_p = (self.hunger - self.TH_H) / (100 - self.TH_H)
                j_hunt = self.alignment_flow("hunt", meaning_p)
                if success:
                    self.hunger = max(0, self.hunger - food); self.fatigue = min(100, self.fatigue + 5.0); self.injury = min(100, self.injury + 2.0 * risk * self.risk_tolerance)
                    self.update_kappa("hunt", True, food, "hunt"); self.update_heat(meaning_p, j_hunt)
                    self.log.append({"t": t, "name": self.name, "state": "Hunting", "action": "hunt_success", "target": "HuntZone", "amount": round(food, 1), "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_hunt": round(self.kappa["hunt"], 3)})
                else:
                    self.fatigue = min(100, self.fatigue + 10.0); self.injury = min(100, self.injury + 5.0 * risk * self.risk_tolerance)
                    self.update_kappa("hunt", False, 0, "hunt"); self.update_heat(meaning_p, 0)
                    self.log.append({"t": t, "name": self.name, "state": "Hunting", "action": "hunt_fail", "target": "HuntZone", "amount": 0, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_hunt": round(self.kappa["hunt"], 3)})
                self.state = "Idle"; self.target_pos = None; self.target_node = None; self.action_type = None
                return True
        return False

    # --- 新しい行動選択メソッド群 (SSD理論の中核) ---
    
    def _calculate_meaning_pressures(self):
        """
        【STEP 1】意味圧の計算
        現在の生理的・心理的状態（飢え、疲労など）を、理論上の「意味圧ベクトル」に変換する。
        各圧力は0-1の範囲に正規化される。
        """
        pressures = {
            'hunger': max(0, (self.hunger - self.TH_H) / (100 - self.TH_H)),
            'fatigue': max(0, (self.fatigue - self.TH_F) / (100 - self.TH_F)),
            'injury': max(0, (self.injury - self.TH_I) / (100 - self.TH_I)),
            'boredom': max(0, (self.boredom - self.TH_B) / (100 - self.TH_B)),
            'help': 0.0
        }
        allies = self.nearby_allies(radius=2)
        if allies:
            best_help_utility = max([self.help_utility(o) for o in allies] + [0.0])
            pressures['help'] = max(0, best_help_utility * 2.0)
        return pressures

    def _calculate_action_utilities(self, pressures):
        """
        【STEP 2】行動効用値の計算
        各行動が、現在の意味圧ベクトルをどれだけ解消できそうか（効用）を評価する。
        - 各行動は特定の種類（複数も可）の意味圧を解消するのに役立つ。
        - 効用値は、その行動の整合慣性κの大きさに応じてブーストされる。
        """
        utilities = defaultdict(float)
        utilities['rest'] = pressures['fatigue'] * 1.5 + pressures['injury'] * 0.5
        utilities['forage'] = pressures['hunger'] * (1.0 - self.risk_tolerance) * 1.2
        utilities['hunt'] = pressures['hunger'] * self.risk_tolerance * 1.2
        utilities['help'] = pressures['help'] * 1.1
        utilities['patrol'] = pressures['boredom'] * 0.8 + 0.05
        for action, util in utilities.items():
            utilities[action] = util * (1 + self.kappa[action] * self.g)
        return utilities

    def _softmax_selection(self, utilities):
        """
        【STEP 3】ソフトマックスによる行動選択
        計算された効用値ベクトルに基づき、実行する行動を確率的に選択する。
        - 探索温度Tが低い時：効用値が最も高い行動が選ばれやすい（合理的選択）。
        - 探索温度Tが高い時：効用値が低い行動も選ばれる可能性が上がる（探索的選択）。
        """
        temp = max(self.T, 0.01)
        action_names = list(utilities.keys())
        utils = np.array([utilities[name] for name in action_names])
        exp_utils = np.exp((utils - np.max(utils)) / temp)
        probs = exp_utils / np.sum(exp_utils)
        chosen_action = np.random.choice(action_names, p=probs)
        return chosen_action

    # --- メインの行動サイクル ---

    def step(self, t):
        if not self.alive: return

        # 代謝
        self.hunger = min(120, self.hunger + 1.8)
        self.fatigue = min(120, self.fatigue + 0.8)
        self.injury = min(120, self.injury + 0.02 * self.fatigue / 100)
        self.boredom = min(120, self.boredom + 0.1)
        
        # 跳躍判定（死）
        death_risk_factor = 1.0 + max(0, (self.fatigue - self.TH_JUMP_FATIGUE) / 20.0)
        if self.hunger >= 100 or self.injury >= 100 or self.fatigue >= 120:
            leap_occurred, h, Theta = self.check_leap()
            if leap_occurred * death_risk_factor > 0.5 or self.hunger >= 110 or self.injury >= 110 or self.fatigue >= 120:
                self.alive = False
                self.log.append({"t": t, "name": self.name, "state": "Dead", "action": "death", "target": "", "amount": 0, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "jump_rate": round(h, 3), "Theta": round(Theta, 2)})
                return
        
        self.update_temperature()
        
        # --- 進行中の行動の継続 ---
        if self.state == "Moving":
            if self.action_type == 'forage': self.do_forage(t); return
            elif self.action_type == 'hunt': self.do_hunt(t); return
            elif self.action_type == 'patrol':
                # ★修正: パトロール完了時に正しくアイドルに戻る
                if self.move_towards(self.target_pos):
                    self.state = "Idle"; self.action_type = None; self.target_pos = None
                return

        if self.state == "Helping":
            if self.maybe_help(t): return
        
        # === 新しい行動選択ロジック ===
        if self.state == "Idle":
            pressures = self._calculate_meaning_pressures()
            utilities = self._calculate_action_utilities(pressures)
            action = self._softmax_selection(utilities)

            if action == 'help':
                if self.maybe_help(t): return

            elif action == 'rest':
                self.state = "Resting"
                rest_amount = 30 * (1 + 0.25 * self.stamina)
                self.fatigue = max(0, self.fatigue - rest_amount)
                self.injury = max(0, self.injury - 4 * (1 + 0.1 * self.stamina))
                self.boredom = min(100, self.boredom + 5)
                # ★修正: 休息のκ更新重みを0.6倍に落とす
                self.update_kappa("rest", True, rest_amount * 0.6, action)
                self.update_heat(pressures.get('fatigue', 0), rest_amount / 30)
                self.log.append({"t": t, "name": self.name, "state": "Resting", "action": "rest", "target": "", "amount": rest_amount, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "kappa_rest": round(self.kappa["rest"], 3)})
                self.state = "Idle"
                return

            elif action == 'forage':
                nodes = self.env.nearest_nodes(self.pos(), self.env.berries, k=1)
                if nodes:
                    self.target_pos, self.target_node = nodes[0], nodes[0]
                    self.state = "Moving"; self.action_type = "forage"
                    self.boredom = max(0, self.boredom - 10)
                    self.do_forage(t) # ★修正: 即座に最初の移動を開始
                    return

            elif action == 'hunt':
                nodes = self.env.nearest_nodes(self.pos(), self.env.huntzones, k=1)
                if nodes:
                    self.target_pos, self.target_node = nodes[0], nodes[0]
                    self.state = "Moving"; self.action_type = "hunt"
                    self.boredom = max(0, self.boredom - 15)
                    self.do_hunt(t) # ★修正: 即座に最初の移動を開始
                    return
            
            elif action == 'patrol':
                self.state = "Moving"; self.action_type = "patrol"
                move_range = int(1 + self.T * 4)
                tx = self.x + random.randint(-move_range, move_range)
                ty = self.y + random.randint(-move_range, move_range)
                self.target_pos = (max(0, min(self.env.size - 1, tx)), max(0, min(self.env.size - 1, ty)))
                self.boredom = max(0, self.boredom - 20)
                self.update_heat(pressures.get('boredom',0), 0.1)
                self.log.append({"t": t, "name": self.name, "state": "Patrol", "action": "patrol_start", "target": self.target_pos, "amount": 0, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2), "boredom": round(self.boredom, 2)})
                self.move_towards(self.target_pos)
                return

            # フォールバック
            self.update_heat(sum(pressures.values()), 0)
            self.log.append({"t": t, "name": self.name, "state": "Idle", "action": "idle", "target": "", "amount": 0, "hunger": round(self.hunger, 1), "fatigue": round(self.fatigue, 1), "injury": round(self.injury, 1), "E": round(self.E, 2), "T": round(self.T, 2)})
            return
# ----------------------------------------------------------------------
# 3. シミュレーション実行部と分析コード - 修正
# ----------------------------------------------------------------------
# Presets
FORAGER = {"risk_tolerance": 0.2, "curiosity": 0.3, "avoidance": 0.8, "stamina": 0.6, "empathy": 0.8}
TRACKER = {"risk_tolerance": 0.6, "curiosity": 0.5, "avoidance": 0.2, "stamina": 0.8, "empathy": 0.6}
PIONEER = {"risk_tolerance": 0.5, "curiosity": 0.9, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5}
GUARDIAN = {"risk_tolerance": 0.4, "curiosity": 0.4, "avoidance": 0.6, "stamina": 0.9, "empathy": 0.9}
HUNTER = {"risk_tolerance": 0.8, "curiosity": 0.4, "avoidance": 0.3, "stamina": 0.7, "empathy": 0.5} # SCAVENGERをHUNTERに変更

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
    NPCWithSSD("Hunter_E", HUNTER, env, roster, starts[4]),
]

for n in npcs:
    roster[n.name] = n

# Run
print("=== Starting SSD-Integrated Simulation (Fixed) ===")
print(f"Environment: {len(env.berries)} berry nodes, {len(env.huntzones)} hunt zones")
print(f"NPCs: {len(npcs)}")
print()

TICKS = 400 # ティック数を増加
for t in range(TICKS):
    for n in npcs:
        n.step(t)
    env.step()
    
    if t % 50 == 0:
        alive_count = sum(1 for n in npcs if n.alive)
        print(f"Tick {t}: {alive_count}/5 NPCs alive. E: {np.mean([n.E for n in npcs if n.alive]):.2f}, T: {np.mean([n.T for n in npcs if n.alive]):.2f}")

print("\n=== Simulation Complete ===\n")

# Analysis
# 改善点2.1: ログのデータ構造はそのまま (修正が複雑になるため)
df_logs = pd.concat([pd.DataFrame(n.log) for n in npcs], ignore_index=True)

death_events = df_logs[df_logs["action"] == "death"]
help_events = df_logs[df_logs["action"].str.contains("share_food|escort_rest", na=False)]
hunt_events = df_logs[df_logs["action"].str.contains("hunt_success|hunt_fail", na=False)]

print("=== DEATH EVENTS ===")
if not death_events.empty:
    print(death_events[["t", "name", "hunger", "fatigue", "injury", "E", "jump_rate", "Theta"]])
else:
    print("No deaths occurred!")

print("\n=== HELP EVENTS (first 10) ===")
if not help_events.empty:
    print(help_events[["t", "name", "target", "action", "state", "E", "T"]].head(10))
else:
    print("No help events occurred!")

# 狩猟イベントの表示を追加
print("\n=== HUNT EVENTS (first 10) ===")
if not hunt_events.empty:
    print(hunt_events[["t", "name", "action", "amount", "E", "T"]].head(10))
else:
    print("No hunt events occurred!")

print("\n=== FINAL STATUS ===")
for npc in npcs:
    status = "ALIVE" if npc.alive else "DEAD"
    print(f"{npc.name}: {status}")
    if npc.alive:
        print(f"  κ_forage: {npc.kappa['forage']:.3f}")
        print(f"  κ_hunt: {npc.kappa['hunt']:.3f}")
        print(f"  κ_rest: {npc.kappa['rest']:.3f}")
        print(f"  κ_help: {npc.kappa['help']:.3f}")
        print(f"  E (heat): {npc.E:.2f}, T (temp): {npc.T:.2f}")
        print(f"  Hunger: {npc.hunger:.1f}, Fatigue: {npc.fatigue:.1f}, Injury: {npc.injury:.1f}")

# Visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 10)) # グラフを6つに拡張

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
axes[0, 0].set_title("1. Hunger over Time (Deaths marked with X)", fontsize=13, fontweight='bold')
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
axes[0, 1].set_title("2. Heat Accumulation (E)", fontsize=13, fontweight='bold')
axes[0, 1].grid(alpha=0.3)

# 3. Temperature (T) over time
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    if "T" in g.columns:
        axes[0, 2].plot(g["t"], g["T"], label=name, linewidth=2)
axes[0, 2].set_xlabel("Time", fontsize=12)
axes[0, 2].set_ylabel("Exploration Temperature (T)", fontsize=12)
axes[0, 2].legend()
axes[0, 2].set_title("3. Exploration Temperature (T)", fontsize=13, fontweight='bold')
axes[0, 2].grid(alpha=0.3)

# 4. Kappa (forage) over time
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    forage_logs = g[g["kappa_forage"].notna()]
    if not forage_logs.empty:
        axes[1, 0].plot(forage_logs["t"], forage_logs["kappa_forage"], label=name, linewidth=2)
axes[1, 0].set_xlabel("Time", fontsize=12)
axes[1, 0].set_ylabel("κ (forage)", fontsize=12)
axes[1, 0].legend()
axes[1, 0].set_title("4. Alignment Inertia (Forage)", fontsize=13, fontweight='bold')
axes[1, 0].grid(alpha=0.3)

# 5. Kappa (hunt) over time (新規追加)
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    hunt_logs = g[g["kappa_hunt"].notna()]
    if not hunt_logs.empty:
        axes[1, 1].plot(hunt_logs["t"], hunt_logs["kappa_hunt"], label=name, linewidth=2)
axes[1, 1].set_xlabel("Time", fontsize=12)
axes[1, 1].set_ylabel("κ (hunt)", fontsize=12)
axes[1, 1].legend()
axes[1, 1].set_title("5. Alignment Inertia (Hunt)", fontsize=13, fontweight='bold')
axes[1, 1].grid(alpha=0.3)

# 6. Fatigue over time (新規追加)
for name in [n.name for n in npcs]:
    g = df_logs[df_logs["name"] == name]
    axes[1, 2].plot(g["t"], g["fatigue"], label=name, linewidth=2)
    d = g[g["action"] == "death"]
    if not d.empty:
        axes[1, 2].scatter(d["t"], d["fatigue"], marker="X", s=200, c='red', edgecolors='black', linewidths=2, zorder=5)
axes[1, 2].set_xlabel("Time", fontsize=12)
axes[1, 2].set_ylabel("Fatigue", fontsize=12)
axes[1, 2].legend()
axes[1, 2].set_title("6. Fatigue over Time", fontsize=13, fontweight='bold')
axes[1, 2].grid(alpha=0.3)


plt.tight_layout()
plt.savefig('ssd_simulation_results_fixed.png', dpi=150, bbox_inches='tight')
print("\n=== Plot saved as 'ssd_simulation_results_fixed.png' ===")
# plt.show() # サンドボックス環境では実行しない

# Save logs
df_logs.to_csv("npc5_ssd_integrated_logs_fixed.csv", index=False)
print("=== Logs saved to 'npc5_ssd_integrated_logs_fixed.csv' ===")
