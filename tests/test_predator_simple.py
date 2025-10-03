#!/usr/bin/env python3
"""
捕食者システムの基本テスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# 基本的なNPCクラスを直接定義
class SimpleNPC:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.health = 100
        self.alive = True
        self.fatigue = 0.0
        self.hunger = 0.0
        self.experience = {"predator_awareness": 0.0}
        self.predator_escapes = 0
        self.cooperation_count = 0
    
    def pos(self):
        return (self.x, self.y)
    
    def is_alive(self):
        return self.alive
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            return True  # died
        return False  # survived
    
    def die(self):
        """死亡処理"""
        self.alive = False
        self.health = 0
    
    def gain_experience(self, skill, amount):
        """経験値獲得"""
        if skill in self.experience:
            self.experience[skill] += amount
        else:
            self.experience[skill] = amount

def test_predator_basics():
    """捕食者の基本機能をテスト"""
    print("🐺 捕食者基本テスト開始")
    
    # 手動でPredatorクラスをインポート
    from environment import Predator
    
    # 捕食者作成
    predator = Predator((50, 50), aggression=0.8)
    print(f"🐺 捕食者生成: 位置({predator.x},{predator.y}) 攻撃性:{predator.aggression}")
    
    # ターゲット作成
    target = SimpleNPC("TestVictim", 45, 45)
    humans = [target]
    
    print(f"👤 ターゲットNPC: {target.name} 位置({target.x},{target.y}) HP:{target.health}")
    
    # 距離計算テスト
    from math import sqrt
    distance = sqrt((predator.x - target.x)**2 + (predator.y - target.y)**2)
    print(f"📏 捕食者-ターゲット間距離: {distance:.2f}")
    
    # 攻撃テスト
    print("\n🔄 攻撃テスト開始:")
    for i in range(5):
        print(f"\nティック {i+1}:")
        
        if not target.is_alive():
            print("💀 ターゲット既に死亡")
            break
            
        # hunt_stepを呼び出し
        attack_result = predator.hunt_step(humans, i)
        
        if attack_result:
            print(f"📊 攻撃結果: {attack_result}")
            
            if attack_result.get('victim'):
                print(f"🐺💀 KILL: {attack_result['victim']} が殺害された!")
                target.die()  # 手動で死亡処理
            elif attack_result.get('injured'):
                print(f"🐺🩸 INJURY: {attack_result['injured']} が負傷!")
            else:
                print(f"🐺❌ 攻撃失敗")
        else:
            print("🐺🚫 攻撃結果なし")
            
        print(f"👤 ターゲット状態: HP:{target.health} 生存:{target.is_alive()}")

def test_environment_predators():
    """Environment内の捕食者テスト"""
    print("\n🌍 Environment捕食者テスト開始")
    
    from environment import Environment
    
    # 環境作成
    env = Environment(size=100)
    
    print(f"🏞️ 環境生成: サイズ{env.size}x{env.size}")
    print(f"🐺 初期捕食者数: {len(env.predators)}")
    
    # _spawn_initial_predatorsが呼ばれているか確認
    env._spawn_initial_predators()
    print(f"🐺 手動生成後の捕食者数: {len(env.predators)}")
    
    # 各捕食者の詳細確認
    for i, predator in enumerate(env.predators):
        print(f"🐺 捕食者{i}: 位置({predator.x},{predator.y}) 攻撃性:{predator.aggression:.2f}")

if __name__ == "__main__":
    test_predator_basics()
    test_environment_predators()