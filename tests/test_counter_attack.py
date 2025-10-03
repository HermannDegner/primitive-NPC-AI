#!/usr/bin/env python3
"""
捕食者逆襲システム強化テスト
逆襲が起きやすい環境でテスト
"""

import sys
import os
import random
from collections import defaultdict

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from environment import Environment, Predator

# 強化版NPCクラス（逆襲しやすい）
class CounterAttackNPC:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.alive = True
        self.fatigue = 0.0
        self.hunger = 50.0
        self.experience = {"predator_awareness": 0.5}  # 経験値高め
        self.risk_tolerance = 0.8  # リスク許容度高め
        
    def pos(self):
        return (self.x, self.y)
        
    def get_predator_avoidance_chance(self):
        return 0.1  # 低い回避率で攻撃を受けやすく
        
    def get_predator_detection_chance(self):
        return 0.8  # 高い発見率
        
    def get_predator_escape_chance(self):
        return 0.2  # 低い逃走率で被害を受けやすく
        
    def gain_experience(self, type_, amount, tick=0):
        if type_ not in self.experience:
            self.experience[type_] = 0.0
        self.experience[type_] += amount
        
    def alert_nearby_npcs_about_predator(self, npcs, predator_pos):
        pass
        
    # 捕食者狩りメソッドを簡単に実装
    def attempt_predator_hunting(self, predators, all_npcs, current_tick):
        """簡易捕食者狩り"""
        if not predators:
            return None
            
        # 近くの捕食者を探す
        nearby_predators = []
        for predator in predators:
            if predator.alive:
                distance = ((self.x - predator.x) ** 2 + (self.y - predator.y) ** 2) ** 0.5
                if distance <= 15:  # 検出範囲15
                    nearby_predators.append((predator, distance))
        
        if not nearby_predators:
            return None
            
        target_predator, distance = min(nearby_predators, key=lambda x: x[1])
        
        # グループ形成
        hunting_group = [self]
        for npc in all_npcs:
            if (npc != self and npc.alive and 
                ((self.x - npc.x) ** 2 + (self.y - npc.y) ** 2) ** 0.5 <= 10 and
                len(hunting_group) < 5):
                participation_chance = 0.7  # 高い参加率
                if random.random() < participation_chance:
                    hunting_group.append(npc)
        
        print(f"  🏹 {self.name} organizing predator hunt with {len(hunting_group)} members")
        
        # 成功率計算
        base_success = 0.15
        group_bonus = (len(hunting_group) - 1) * 0.05
        experience_bonus = sum(npc.experience.get("predator_awareness", 0) for npc in hunting_group) * 0.2
        
        total_success_rate = min(0.6, base_success + group_bonus + experience_bonus)
        
        print(f"  📊 Success rate: {total_success_rate:.2f} (base:{base_success:.2f} + group:{group_bonus:.2f} + exp:{experience_bonus:.2f})")
        
        if random.random() < total_success_rate:
            # 成功
            target_predator.alive = False
            print(f"  ✅ PREDATOR HUNT SUCCESS! Killed predator at ({target_predator.x}, {target_predator.y})")
            
            # 経験獲得
            for npc in hunting_group:
                npc.gain_experience("predator_awareness", 0.15, current_tick)
                npc.fatigue = min(100.0, npc.fatigue + 30.0)  # 疲労
                
            return {
                "success": True,
                "predator_killed": True,
                "group_size": len(hunting_group),
                "meat_gained": 50
            }
        else:
            # 失敗
            print(f"  ❌ PREDATOR HUNT FAILED!")
            casualties = []
            
            for npc in hunting_group:
                if random.random() < 0.2:  # 20%で死亡
                    npc.alive = False
                    casualties.append(npc.name)
                    print(f"    💀 {npc.name} died in the hunt")
                elif random.random() < 0.4:  # 40%で負傷
                    npc.fatigue = min(100.0, npc.fatigue + 50.0)
                    print(f"    🩸 {npc.name} was injured")
                    
            return {
                "success": False,
                "predator_killed": False,
                "group_size": len(hunting_group),
                "casualties": casualties
            }

def test_predator_counter_attack():
    """捕食者逆襲システムのテスト"""
    print("⚔️ 捕食者逆襲システム強化テスト開始")
    
    # 環境作成
    env = Environment(size=60)  # 小さい環境で密度を上げる
    env.predators = []  # 既存捕食者クリア
    
    # 攻撃的な捕食者を複数配置
    for i in range(3):
        x = random.randint(20, 40)
        y = random.randint(20, 40)
        predator = Predator((x, y), aggression=0.9)
        env.predators.append(predator)
        print(f"🐺 Aggressive predator {i+1} placed at ({x}, {y})")
    
    # 逆襲志向のNPCを配置
    npcs = []
    for i in range(6):
        x = random.randint(25, 35)
        y = random.randint(25, 35)
        npc = CounterAttackNPC(f"Fighter_{i+1}", x, y)
        npcs.append(npc)
        print(f"⚔️ Fighter NPC {i+1} placed at ({x}, {y})")
    
    print(f"\n📊 Initial state:")
    print(f"   🐺 Predators: {len(env.predators)}")
    print(f"   ⚔️ Fighters: {len(npcs)}")
    
    # 逆襲テストループ
    for tick in range(20):
        print(f"\n--- ティック {tick+1} ---")
        
        # 捕食者の攻撃
        living_npcs = [npc for npc in npcs if npc.alive]
        living_predators = [p for p in env.predators if p.alive]
        
        if not living_npcs or not living_predators:
            break
            
        attacks = 0
        for predator in living_predators:
            attack_result = predator.hunt_step(living_npcs, tick)
            if attack_result:
                attacks += 1
                if attack_result.get("victim"):
                    print(f"  💀 PREDATOR KILL: {attack_result['victim']}")
                elif attack_result.get("injured"):
                    print(f"  🩸 PREDATOR INJURY: {attack_result['injured']}")
                elif attack_result.get("escaped"):
                    print(f"  💨 PREDATOR ESCAPE: {attack_result['escaped']}")
        
        if attacks == 0:
            print(f"  🛡️ No predator attacks this turn")
        
        # 逆襲チャンス（高確率）
        for npc in living_npcs:
            if random.random() < 0.3:  # 30%の確率で逆襲試行
                hunt_result = npc.attempt_predator_hunting(living_predators, living_npcs, tick)
                if hunt_result and hunt_result.get("predator_killed"):
                    break  # 1ターンに1回まで
        
        # 状況報告
        living_npcs = [npc for npc in npcs if npc.alive]
        living_predators = [p for p in env.predators if p.alive]
        
        print(f"  📊 Status: NPCs:{len(living_npcs)}/{len(npcs)}, Predators:{len(living_predators)}/{len(env.predators)}")
        
        if len(living_predators) == 0:
            print("  🎉 ALL PREDATORS DEFEATED!")
            break
        elif len(living_npcs) == 0:
            print("  💀 ALL NPCS ELIMINATED!")
            break
    
    print("\n✅ Counter-attack test completed!")
    final_npcs = len([npc for npc in npcs if npc.alive])
    final_predators = len([p for p in env.predators if p.alive])
    print(f"📊 Final score: NPCs:{final_npcs}/{len(npcs)}, Predators:{final_predators}/{len(env.predators)}")

if __name__ == "__main__":
    test_predator_counter_attack()