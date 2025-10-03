#!/usr/bin/env python3
"""
捕食者攻撃の詳細デバッグ
"""

from environment import Environment, Predator
import random

# 簡易NPCクラス
class DebugNPC:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.alive = True
        self.fatigue = 0.0
        self.hunger = 50.0
        self.experience = {"predator_awareness": 0.0}
        
    def pos(self):
        return (self.x, self.y)
        
    def get_predator_avoidance_chance(self):
        return 0.0  # 回避なしでテスト
        
    def get_predator_detection_chance(self):
        return 0.0  # 発見なしでテスト
        
    def get_predator_escape_chance(self):
        return 0.0  # 逃走なしでテスト
        
    def gain_experience(self, type_, amount, tick=0):
        if type_ not in self.experience:
            self.experience[type_] = 0.0
        self.experience[type_] += amount
        print(f"  📈 {self.name} gained {amount:.3f} {type_} experience")
        
    def alert_nearby_npcs_about_predator(self, npcs, predator_pos):
        pass

def test_predator_attack_detailed():
    """詳細な捕食者攻撃テスト"""
    print("🐺 詳細捕食者攻撃テスト開始")
    
    # 環境作成（捕食者なし）
    env = Environment(size=100)
    env.predators = []  # 既存の捕食者をクリア
    
    # 捕食者を手動で近い位置に配置
    predator = Predator((50, 50), aggression=0.9)
    env.predators.append(predator)
    
    # NPCを攻撃範囲内に配置
    npc = DebugNPC("Victim", 52, 52)  # 距離2.8で確実に範囲内
    
    print(f"🐺 捕食者: 位置({predator.x}, {predator.y}) 攻撃性:{predator.aggression:.2f} 攻撃範囲:{predator.hunt_radius}")
    print(f"👤 NPC: 位置({npc.x}, {npc.y})")
    
    # 距離計算
    distance = ((npc.x - predator.x) ** 2 + (npc.y - predator.y) ** 2) ** 0.5
    print(f"📏 距離: {distance:.2f} (攻撃範囲: {predator.hunt_radius})")
    
    if distance <= predator.hunt_radius:
        print("✅ 攻撃範囲内です")
    else:
        print("❌ 攻撃範囲外です")
    
    # 手動で攻撃実行
    print("\n🔥 手動攻撃実行:")
    for i in range(5):
        print(f"\n--- 攻撃試行 {i+1} ---")
        
        result = predator.hunt_step([npc], i)
        
        if result is None:
            print("🚫 攻撃なし（回避・距離・その他理由）")
        elif result.get("victim"):
            print(f"💀 致命傷！{result['victim']} が死亡")
            print(f"   防御者数: {result.get('defenders', 0)}")
            print(f"   死亡率: {result.get('death_rate', 0)*100:.1f}%")
            break
        elif result.get("injured"):
            injury_type = result.get("injury_type", "heavy")
            print(f"🩸 負傷！{result['injured']} が {injury_type} injury")
            print(f"   防御者数: {result.get('defenders', 0)}")
            if "injury_damage" in result:
                print(f"   ダメージ: {result['injury_damage']:.1f}")
        elif result.get("escaped"):
            print(f"💨 逃走成功！{result['escaped']} が逃げ切った")
            print(f"   防御者数: {result.get('defenders', 0)}")
        
        if not npc.alive:
            print(f"💀 {npc.name} は死亡しました")
            break
        else:
            print(f"❤️ {npc.name} は生存中（疲労: {npc.fatigue:.1f}）")

if __name__ == "__main__":
    test_predator_attack_detailed()