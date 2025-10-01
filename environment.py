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


class Predator:
    """捕食者システム：コミュニティ形成の外的圧力"""
    def __init__(self, pos, aggression=0.7):
        self.x, self.y = pos
        self.aggression = aggression
        self.hunt_radius = 8
        self.alive = True
        
    def pos(self):
        """現在位置を取得"""
        return (self.x, self.y)
        
    def distance_to(self, pos):
        """指定位置までの距離を計算"""
        return math.sqrt((self.x - pos[0])**2 + (self.y - pos[1])**2)
        
    def hunt_step(self, npcs):
        """NPCを狩る行動"""
        if not self.alive:
            return None
            
        nearby_npcs = [npc for npc in npcs if npc.alive and self.distance_to(npc.pos()) <= self.hunt_radius]
        if not nearby_npcs:
            return None
            
        target = min(nearby_npcs, key=lambda n: self.distance_to(n.pos()))
        nearby_defenders = len([npc for npc in nearby_npcs if self.distance_to(npc.pos()) <= 3])
        
        # 集団防御の効果
        attack_success_rate = self.aggression - (nearby_defenders * 0.3)
        attack_success_rate = max(0.1, min(0.9, attack_success_rate))
        
        if random.random() < attack_success_rate:
            target.alive = False
            return {"victim": target.name, "defenders": nearby_defenders}
        return None


class Environment:
    """環境とリソース管理"""
    def __init__(self, size=90, n_berry=120, n_hunt=60, n_water=40, n_caves=25):
        self.size = size
        self.weather = Weather()
        self.day_night = DayNightCycle()
        self.predators = []
        
        # リソース生成
        self.water_sources = {f"water_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                             for i in range(n_water)}
        self.berries = {f"berry_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                       for i in range(n_berry)}
        self.hunting_grounds = {f"hunt_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                               for i in range(n_hunt)}
        self.caves = {f"cave_{i}": (random.randint(5, size-5), random.randint(5, size-5)) 
                     for i in range(n_caves)}
        
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
    
    def nearest_nodes(self, pos, nodes_dict, k=3):
        """指定位置から最も近いノードを取得"""
        if not nodes_dict:
            return []
        distances = [(node_pos, math.sqrt((pos[0]-node_pos[0])**2 + (pos[1]-node_pos[1])**2)) 
                    for node_pos in nodes_dict.values()]
        distances.sort(key=lambda x: x[1])
        return [pos for pos, _ in distances[:k]]