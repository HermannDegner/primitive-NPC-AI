#!/usr/bin/env python3
"""
人間NPC縄張り防衛システムテスト
"""

import sys
import os
import random

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from environment import Environment, Predator
from ssd_enhanced_npc import SSDEnhancedNPC

# テスト用簡易NPC
class TestNPC:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.alive = True
        self.fatigue = 0.0
        self.hunger = 50.0
        self.thirst = 30.0
        
    def pos(self):
        return (self.x, self.y)
    
    def get_survival_score(self):
        return (100 - self.hunger + 100 - self.thirst + 100 - self.fatigue) / 3
        
    def step(self, tick):
        pass

def test_human_territorial_defense():
    """人間NPC縄張り防衛テスト"""
    print("🏘️ 人間NPC縄張り防衛システムテスト開始")
    
    # 環境作成
    env = Environment(size=100)
    
    # 人間NPCコミュニティ作成
    human_npcs = []
    for i in range(3):
        test_npc = TestNPC(f"Human_{i}", 40 + i*2, 40 + i*2)
        try:
            enhanced_npc = SSDEnhancedNPC(test_npc)
            human_npcs.append(enhanced_npc)
            print(f"👥 {test_npc.name} 配置: ({test_npc.x}, {test_npc.y})")
        except Exception as e:
            print(f"⚠️ SSDEnhancedNPC初期化失敗: {e}")
            # フォールバック: 基本NPCとして追加
            human_npcs.append(test_npc)
    
    # 縄張り確立のための成功体験をシミュレート
    for tick in range(5):
        for enhanced_npc in human_npcs:
            if hasattr(enhanced_npc, 'process_territorial_experience'):
                location = (enhanced_npc.npc.x, enhanced_npc.npc.y)
                result = enhanced_npc.process_territorial_experience(
                    'safe_rest', location, 0.8, 
                    [other.npc.name for other in human_npcs if other != enhanced_npc],
                    tick
                )
                if result.get('territorial_changes'):
                    print(f"🏠 T{tick}: {enhanced_npc.npc.name} 縄張り確立!")
    
    # 捕食者接近シミュレーション
    print(f"\n⚔️ 捕食者接近シミュレーション")
    predator = Predator((70, 70), aggression=0.9)
    
    # 捕食者を段階的にコミュニティに近づける
    for step in range(8):
        print(f"\n--- ステップ {step+1} ---")
        
        # 捕食者を人間コミュニティに近づける
        predator.x -= 3
        predator.y -= 3
        
        print(f"🐺 捕食者位置: ({predator.x}, {predator.y})")
        
        # 各人間NPCの脅威検知と反応
        for enhanced_npc in human_npcs:
            if hasattr(enhanced_npc, 'check_territorial_threats'):
                threat_response = enhanced_npc.check_territorial_threats(
                    [predator], step
                )
                
                if threat_response['threats_detected']:
                    threat = threat_response['threats_detected'][0]
                    print(f"👥 {enhanced_npc.npc.name}: 脅威検知!")
                    print(f"   脅威レベル: {threat['threat_level']:.2f}")
                    print(f"   緊急度: {threat['urgency']:.2f}")
                    
                    # 防衛行動
                    if threat_response['defense_actions']:
                        defense = threat_response['defense_actions'][0]
                        print(f"   🛡️ 防衛行動: {defense['defense_action']}")
                        print(f"   協力ブースト: +{defense['cooperation_boost']:.2f}")
                        
                        if defense.get('group_mobilization'):
                            print(f"   📢 集団動員要請!")
                    
                    # 行動変更
                    if threat_response['behavioral_changes']:
                        changes = threat_response['behavioral_changes']
                        if 'cooperation_tendency' in changes:
                            print(f"   🤝 協力傾向: +{changes['cooperation_tendency']:.2f}")
                        if 'fear_level' in changes:
                            print(f"   😨 恐怖レベル: {changes['fear_level']:.2f}")
        
        # 捕食者がコミュニティ中心に到達したら終了
        if predator.x <= 42 and predator.y <= 42:
            print(f"\n🚨 捕食者がコミュニティ中心に到達！")
            break

def test_human_vs_human_territorial_conflict():
    """人間同士の縄張り競合テスト"""
    print(f"\n⚔️ 人間同士の縄張り競合テスト")
    
    # 2つの人間グループ
    group_a = []
    group_b = []
    
    # グループA (西側)
    for i in range(2):
        test_npc = TestNPC(f"GroupA_{i}", 30, 40 + i*3)
        try:
            enhanced_npc = SSDEnhancedNPC(test_npc)
            group_a.append(enhanced_npc)
        except Exception:
            group_a.append(test_npc)
    
    # グループB (東側)
    for i in range(2):
        test_npc = TestNPC(f"GroupB_{i}", 60, 40 + i*3)
        try:
            enhanced_npc = SSDEnhancedNPC(test_npc)
            group_b.append(enhanced_npc)
        except Exception:
            group_b.append(test_npc)
    
    print(f"👥 グループA: 西側 (30, 40)付近")
    print(f"👥 グループB: 東側 (60, 40)付近")
    
    # 各グループで縄張り確立
    for tick in range(3):
        for group, name in [(group_a, "A"), (group_b, "B")]:
            for enhanced_npc in group:
                if hasattr(enhanced_npc, 'process_territorial_experience'):
                    location = (enhanced_npc.npc.x, enhanced_npc.npc.y)
                    enhanced_npc.process_territorial_experience(
                        'social_cooperation', location, 0.9, 
                        [other.npc.name for other in group if other != enhanced_npc],
                        tick
                    )
    
    # グループBをグループAの縄張りに侵入させる
    print(f"\n🚶‍♂️ グループBがグループAの縄張りに接近")
    
    for step in range(6):
        print(f"\n--- 侵入ステップ {step+1} ---")
        
        # グループBを西に移動
        for member in group_b:
            if hasattr(member, 'npc'):
                member.npc.x -= 4
            else:
                member.x -= 4
        
        # グループAの反応チェック
        for enhanced_npc in group_a:
            if hasattr(enhanced_npc, 'check_territorial_threats'):
                intruders = [member.npc if hasattr(member, 'npc') else member for member in group_b]
                threat_response = enhanced_npc.check_territorial_threats(intruders, step)
                
                if threat_response['threats_detected']:
                    print(f"👥 {enhanced_npc.npc.name}: 侵入者検知!")
                    for threat in threat_response['threats_detected']:
                        print(f"   侵入者: {threat['entity'].name if hasattr(threat['entity'], 'name') else 'Unknown'}")
                        print(f"   脅威レベル: {threat['threat_level']:.2f}")

if __name__ == "__main__":
    # 縄張り防衛テスト
    test_human_territorial_defense()
    
    # 人間同士の競合テスト
    test_human_vs_human_territorial_conflict()
    
    print("\n🎉 人間NPC縄張り防衛システムテスト完了！")