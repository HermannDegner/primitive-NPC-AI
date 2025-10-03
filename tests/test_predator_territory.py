#!/usr/bin/env python3
"""
捕食者縄張りシステムテスト
"""

import sys
import os
import random

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from environment import Environment, Predator, Prey
from predator_territory_system import predator_territory_system

# テスト用簡易NPC
class TestNPC:
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
    
    def step(self, tick):
        pass
        
    def get_predator_avoidance_chance(self):
        return 0.3
        
    def get_predator_detection_chance(self):
        return 0.4
        
    def get_predator_escape_chance(self):
        return 0.5
        
    def gain_experience(self, type_, amount, tick=0):
        pass
        
    def alert_nearby_npcs_about_predator(self, npcs, pos):
        pass

def test_predator_territory_establishment():
    """捕食者の縄張り確立テスト"""
    print("🏰 捕食者縄張り確立テスト開始")
    
    # 環境作成
    env = Environment(size=100)
    env.predators = []
    env.prey_animals = []
    
    # 捕食者配置
    predator = Predator((50, 50), aggression=0.9)
    env.predators.append(predator)
    
    # 獲物を周辺に配置
    for i in range(8):
        angle = i * 45  # 45度間隔
        x = 50 + 6 * (1 if angle % 90 == 0 else 0.707) * (1 if angle < 180 else -1)
        y = 50 + 6 * (1 if angle == 90 or angle == 270 else 0) + (6 * 0.707 if angle == 45 or angle == 135 else 0)
        prey = Prey(x, y, "rabbit")
        env.prey_animals.append(prey)
    
    print(f"🐺 攻撃的捕食者配置: 位置(50,50) 攻撃性:{predator.aggression}")
    print(f"🐰 獲物{len(env.prey_animals)}匹を周辺配置")
    
    # 縄張り確立シミュレーション
    for tick in range(20):
        print(f"\n--- ティック {tick+1} ---")
        
        # 獲物狩り
        hunted = predator.hunt_prey(env.prey_animals, tick)
        if hunted:
            print(f"🎯 狩り成功: {len(hunted)}匹捕獲")
        
        # 縄張り情報チェック
        territory_info = predator_territory_system.get_territory_info(predator)
        if territory_info:
            if not predator.has_territory:
                print(f"🏰 縄張り確立！")
                print(f"   中心: {territory_info['center']}")
                print(f"   半径: {territory_info['radius']}")
                print(f"   強度: {territory_info['territorial_strength']:.2f}")
                predator.has_territory = True
            
            print(f"🏰 縄張り状況:")
            print(f"   成功回数: {territory_info['hunt_success_count']}")
            print(f"   獲物密度: {territory_info['prey_density']:.3f}")
        else:
            print(f"🏕️ 縄張りなし（経験蓄積中）")
        
        # 行動修正値
        modifier = predator_territory_system.get_territorial_behavior_modifier(predator, predator.pos())
        print(f"📊 行動修正:")
        print(f"   攻撃性倍率: {modifier['aggression_multiplier']:.2f}")
        print(f"   狩猟ボーナス: {modifier['hunt_success_bonus']:.3f}")
        print(f"   パトロール傾向: {modifier['patrol_tendency']:.2f}")
        
        # 捕食者移動
        predator.x += random.randint(-2, 2)
        predator.y += random.randint(-2, 2)
        predator.x = max(0, min(99, predator.x))
        predator.y = max(0, min(99, predator.y))
        
        living_prey = len([p for p in env.prey_animals if p.alive])
        if living_prey == 0:
            print("🎯 すべての獲物を狩り尽くしました")
            break
    
    return predator.has_territory

def test_territorial_intrusion():
    """縄張り侵入テスト"""
    print("\n⚔️ 縄張り侵入テスト開始")
    
    # 環境作成
    env = Environment(size=100)
    env.predators = []
    
    # 縄張り持ち捕食者
    territory_owner = Predator((40, 40), aggression=0.8)
    env.predators.append(territory_owner)
    
    # 侵入者捕食者
    intruder = Predator((70, 70), aggression=0.6)
    env.predators.append(intruder)
    
    # 縄張り確立のための成功経験を人工的に作成
    for i in range(10):
        predator_territory_system.process_predator_territorial_experience(
            territory_owner, (40, 40), 'hunt', True, i
        )
    
    print(f"🏰 縄張り保持者: 位置(40,40)")
    print(f"👤 侵入者: 位置(70,70)")
    
    # 侵入者を縄張りに近づける
    for step in range(10):
        print(f"\n--- ステップ {step+1} ---")
        
        # 侵入者を縄張りに向かわせる
        if intruder.x > territory_owner.x:
            intruder.x -= 3
        if intruder.y > territory_owner.y:
            intruder.y -= 3
        
        print(f"👤 侵入者位置: ({intruder.x}, {intruder.y})")
        
        # 侵入チェック
        intrusion_result = predator_territory_system.check_territory_intrusion(
            intruder.pos(), 'predator'
        )
        
        if intrusion_result['is_intrusion']:
            print(f"⚠️ 縄張り侵入検出！")
            print(f"   侵入レベル: {intrusion_result['intrusion_level']:.2f}")
            print(f"   推奨行動: {intrusion_result['recommended_action']}")
            
            # 防衛行動
            defense_result = predator_territory_system.process_territory_defense(
                territory_owner, intruder.pos(), 'predator', step
            )
            
            print(f"🛡️ 防衛行動: {defense_result['defense_action']}")
            print(f"   攻撃性ブースト: +{defense_result['aggression_boost']:.2f}")
            
            if defense_result['chase_priority']:
                print(f"🏃‍♂️ 優先追跡モード発動！")
                break
        else:
            print(f"✅ 縄張り外")
    
def test_territorial_humans():
    """人間に対する縄張り行動テスト"""
    print("\n👥 人間に対する縄張り行動テスト")
    
    # 環境作成
    env = Environment(size=80)
    env.predators = []
    
    # 縄張り持ち捕食者
    predator = Predator((40, 40), aggression=0.7)
    env.predators.append(predator)
    
    # 縄張り確立
    for i in range(8):
        predator_territory_system.process_predator_territorial_experience(
            predator, (40, 40), 'hunt', True, i
        )
    
    # 人間NPC配置
    humans = [
        TestNPC("Human1", 35, 35),  # 縄張り内
        TestNPC("Human2", 45, 60),  # 縄張り境界
        TestNPC("Human3", 65, 65)   # 縄張り外
    ]
    
    print(f"🏰 縄張り中心: (40, 40)")
    territory_info = predator_territory_system.get_territory_info(predator)
    if territory_info:
        print(f"🏰 縄張り半径: {territory_info['radius']}")
    
    for human in humans:
        intrusion_result = predator_territory_system.check_territory_intrusion(
            human.pos(), 'human'
        )
        
        if intrusion_result['is_intrusion']:
            print(f"👥 {human.name} ({human.x}, {human.y}): 縄張り侵入")
            print(f"   侵入レベル: {intrusion_result['intrusion_level']:.2f}")
            print(f"   推奨行動: {intrusion_result['recommended_action']}")
        else:
            print(f"👥 {human.name} ({human.x}, {human.y}): 縄張り外")

if __name__ == "__main__":
    # 縄張り確立テスト
    territory_established = test_predator_territory_establishment()
    
    if territory_established:
        # 侵入テスト
        test_territorial_intrusion()
        
        # 人間に対する行動テスト
        test_territorial_humans()
        
        print("\n🎉 捕食者縄張りシステムが正常に動作しています！")
    else:
        print("\n⚠️ 縄張り確立に失敗しました")