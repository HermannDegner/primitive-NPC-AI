#!/usr/bin/env python3
"""
捕食者の動物狩りシステムテスト
"""

import sys
import os
import random

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from environment import Environment, Predator, Prey

def test_predator_prey_hunting():
    """捕食者の動物狩りテスト"""
    print("🐺🦌 捕食者の動物狩りテスト開始")
    
    # 環境作成
    env = Environment(size=100)
    env.predators = []  # 既存捕食者クリア
    env.prey_animals = []  # 既存動物クリア
    
    # 捕食者を配置
    predator = Predator((50, 50), aggression=0.8)
    env.predators.append(predator)
    print(f"🐺 捕食者配置: 位置(50,50) 攻撃性:{predator.aggression:.2f}")
    print(f"   初期飢餓レベル: {predator.hunger_level:.2f}")
    
    # 獲物動物を配置
    prey_positions = [(45, 45), (48, 52), (52, 48), (55, 55), (40, 50)]
    for i, (x, y) in enumerate(prey_positions):
        prey = Prey(x, y, "rabbit")
        env.prey_animals.append(prey)
        print(f"🐰 ウサギ{i+1}配置: 位置({x},{y}) 恐怖度:{prey.fear_level:.2f}")
    
    print(f"\n📊 初期状態:")
    print(f"   🐺 捕食者数: {len(env.predators)}")
    print(f"   🐰 獲物数: {len(env.prey_animals)}")
    
    # 狩猟シミュレーション
    for tick in range(10):
        print(f"\n--- ティック {tick+1} ---")
        
        # 生存している獲物を確認
        living_prey = [p for p in env.prey_animals if p.alive]
        print(f"🐰 生存獲物数: {len(living_prey)}")
        
        if len(living_prey) == 0:
            print("🎯 すべての獲物が狩られました！")
            break
        
        # 捕食者の状態表示
        print(f"🐺 捕食者状態:")
        print(f"   位置: ({predator.x}, {predator.y})")
        print(f"   飢餓レベル: {predator.hunger_level:.2f}")
        print(f"   成功回数: {predator.prey_hunting_success}")
        print(f"   連続失敗: {predator.consecutive_failures}")
        
        # 獲物の恐怖度更新
        for prey in living_prey:
            prey.update_fear([predator], [])
        
        # 捕食者の狩り実行
        hunted = predator.hunt_prey(env.prey_animals, tick)
        
        if hunted:
            print(f"🎯 狩り成功！{len(hunted)}匹の獲物を捕獲:")
            for prey in hunted:
                distance = ((predator.x - prey.x) ** 2 + (predator.y - prey.y) ** 2) ** 0.5
                print(f"   💀 {prey.type} at ({prey.x}, {prey.y}) - 距離:{distance:.1f}")
        else:
            print("❌ 今回は獲物を捕らえられませんでした")
        
        # 捕食者移動（簡単なランダムウォーク）
        predator.x += random.randint(-3, 3)
        predator.y += random.randint(-3, 3)
        predator.x = max(0, min(99, predator.x))
        predator.y = max(0, min(99, predator.y))
        
        # 飢餓レベル増加
        predator.hunger_level = min(1.0, predator.hunger_level + 0.1)
    
    # 最終結果
    final_prey = len([p for p in env.prey_animals if p.alive])
    hunted_count = len(env.prey_animals) - final_prey
    
    print(f"\n✅ 動物狩りテスト完了！")
    print(f"📊 結果:")
    print(f"   🎯 狩った獲物: {hunted_count}/{len(env.prey_animals)}")
    print(f"   🐰 生存獲物: {final_prey}")
    print(f"   🐺 捕食者成功率: {predator.prey_hunting_success}/{tick+1} ティック")
    
    return hunted_count > 0

def test_predator_target_selection():
    """捕食者の狩猟対象選択テスト"""
    print("\n🎯 捕食者の狩猟対象選択テスト")
    
    # 環境作成
    env = Environment(size=100)
    predator = Predator((50, 50), aggression=0.7)
    
    # テストケース1: 獲物が豊富
    print("\n--- ケース1: 獲物豊富 ---")
    many_prey = [Prey(45+i, 45, "rabbit") for i in range(5)]
    humans = []
    
    target = predator.decide_hunt_target(humans, many_prey)
    print(f"🎯 獲物5匹、人間0人 → 対象: {target}")
    
    # テストケース2: 飢餓状態
    print("\n--- ケース2: 捕食者飢餓状態 ---")
    predator.hunger_level = 0.8  # 高い飢餓レベル
    few_prey = [Prey(45, 45, "rabbit")]
    humans = [type('Human', (), {'x': 48, 'y': 48, 'alive': True, 'experience': {}})()]
    
    target = predator.decide_hunt_target(humans, few_prey)
    print(f"🐺 飢餓0.8、獲物1匹、人間1人 → 対象: {target}")
    
    # テストケース3: ストレス状態
    print("\n--- ケース3: 捕食者ストレス状態 ---")
    predator.hunger_level = 0.4
    predator.P = 0.9  # 高いストレス
    predator.E = 0.5
    
    target = predator.decide_hunt_target(humans, few_prey)
    print(f"🧠 ストレス(P=0.9, E=0.5)、獲物1匹、人間1人 → 対象: {target}")

if __name__ == "__main__":
    # 動物狩りテスト
    hunting_success = test_predator_prey_hunting()
    
    # 狩猟対象選択テスト
    test_predator_target_selection()
    
    if hunting_success:
        print("\n🎉 捕食者は正常に動物を狩っています！")
    else:
        print("\n⚠️ 動物狩りで問題が発生している可能性があります")