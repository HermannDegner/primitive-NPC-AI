#!/usr/bin/env python3
"""
捕食者システムのデバッグテスト
人間を襲う捕食者が正しく動作するかテスト
"""

from environment import Environment, Predator
import random

# 簡易NPCクラス
class SimpleNPC:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.alive = True
        self.fatigue = 0.0
        self.experience = {"predator_awareness": 0.0}
        
    def pos(self):
        return (self.x, self.y)
        
    def get_predator_avoidance_chance(self):
        return 0.3 + self.experience.get("predator_awareness", 0) * 0.5
        
    def get_predator_detection_chance(self):
        return 0.4 + self.experience.get("predator_awareness", 0) * 0.3
        
    def get_predator_escape_chance(self):
        return 0.5 + self.experience.get("predator_awareness", 0) * 0.4
        
    def gain_experience(self, type_, amount, tick=0):
        if type_ not in self.experience:
            self.experience[type_] = 0.0
        self.experience[type_] += amount
        
    def alert_nearby_npcs_about_predator(self, npcs, predator_pos):
        pass

def test_predator_system():
    """捕食者システムの直接テスト"""
    print("🐺 捕食者システムテスト開始")
    
    # 環境作成
    env = Environment(size=100)
    
    # 手動で捕食者を生成
    predator = Predator((50, 50), aggression=0.8)
    env.predators.append(predator)
    print(f"🐺 手動捕食者生成: 位置(50,50) 攻撃性:0.8")
    
    # NPCを生成
    test_npc = SimpleNPC("TestVictim", 45, 45)
    humans = [test_npc]
    
    print(f"👤 テストNPC生成: {test_npc.name} 位置({test_npc.x},{test_npc.y})")
    print(f"📊 捕食者数: {len(env.predators)}")
    print(f"👥 人間数: {len(humans)}")
    
    # 捕食者の攻撃テスト（10回試行）
    for tick in range(10):
        print(f"\n🔄 ティック {tick+1}:")
        
        # 捕食者位置確認
        for i, p in enumerate(env.predators):
            print(f"🐺 捕食者{i}: 位置({p.x},{p.y}) 攻撃性:{p.aggression:.2f}")
        
        # 生存NPC確認
        living_humans = [npc for npc in humans if npc.alive]
        print(f"👥 生存NPC数: {len(living_humans)}")
        
        if not living_humans:
            print("💀 全NPCが死亡 - テスト終了")
            break
            
        # 攻撃実行
        for predator in env.predators:
            attack_result = predator.hunt_step(living_humans, tick)
            
            if attack_result:
                if attack_result.get('success'):
                    if attack_result.get('victim'):
                        print(f"🐺💀 KILL: {attack_result['victim']} が殺害された!")
                    elif attack_result.get('injured'):
                        print(f"🐺🩸 INJURY: {attack_result['injured']} が負傷!")
                else:
                    print(f"🐺❌ 攻撃失敗 - 理由: {attack_result.get('reason', '不明')}")
            else:
                print("🐺🚫 攻撃なし")
    
    print("\n✅ 捕食者テスト完了")

def test_environment_ecosystem():
    """環境のecosystem_stepテスト"""
    print("\n🌍 Environment ecosystem_stepテスト開始")
    
    env = Environment(size=100)
    
    # NPCs作成
    npcs = [SimpleNPC(f"TestNPC_{i}", 
                      random.randint(20, 80), 
                      random.randint(20, 80)) 
           for i in range(3)]
    
    print(f"👥 テストNPC生成: {len(npcs)}人")
    
    # 初期状態確認
    print(f"🐺 初期捕食者数: {len(env.predators)}")
    
    # ecosystem_stepを実行
    for tick in range(5):
        print(f"\n🔄 Ecosystem Step {tick+1}:")
        env.ecosystem_step(npcs, tick)
        
        living_npcs = [npc for npc in npcs if npc.is_alive()]
        print(f"👥 生存NPC: {len(living_npcs)}/{len(npcs)}")
        
        if len(living_npcs) < len(npcs):
            print("💀 死者発生!")
            for npc in npcs:
                if not npc.is_alive():
                    print(f"💀 {npc.name} が死亡")
    
    print("\n✅ Environment ecosystem テスト完了")

if __name__ == "__main__":
    test_predator_system()
    test_environment_ecosystem()