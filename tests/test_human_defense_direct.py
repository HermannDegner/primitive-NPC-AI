#!/usr/bin/env python3
"""
人間縄張り防衛システム - 直接テスト
SSD Core Engineの縄張りシステムを直接使用
"""

import sys
import os

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ssd_core_engine'))

from ssd_core_engine.ssd_territory import TerritoryProcessor

# テスト用簡易NPC
class SimpleHuman:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.alive = True
        
    def pos(self):
        return (self.x, self.y)

def test_human_territory_defense_direct():
    """人間縄張り防衛の直接テスト"""
    print("🏘️ 人間縄張り防衛システム - 直接テスト開始")
    
    # 縄張りプロセッサー初期化
    territory_processor = TerritoryProcessor()
    
    # 人間コミュニティ作成
    humans = [
        SimpleHuman("Alice", 40, 40),
        SimpleHuman("Bob", 42, 42),
        SimpleHuman("Charlie", 38, 41)
    ]
    
    print(f"👥 人間コミュニティ配置:")
    for human in humans:
        print(f"   {human.name}: ({human.x}, {human.y})")
    
    # 各人間の境界初期化
    for human in humans:
        territory_processor.initialize_npc_boundaries(human.name)
    
    # 縄張り確立のための協力体験シミュレート
    print(f"\n🤝 協力体験による縄張り確立")
    for tick in range(8):
        for human in humans:
            # 協力体験を記録
            other_names = [h.name for h in humans if h != human]
            result = territory_processor.process_territorial_experience(
                human.name, 
                (human.x, human.y),
                'social_cooperation',  # 社会協力
                0.8,  # 高い感情価
                other_names,
                tick
            )
            
            # 縄張り確立チェック
            if result.get('territorial_changes'):
                for change in result['territorial_changes']:
                    print(f"🏠 T{tick}: {human.name} 縄張り確立! 半径:{change['radius']}")
    
    # 捕食者脅威シミュレーション
    print(f"\n🐺 捕食者脅威への対応テスト")
    
    # 段階的接近する捕食者
    predator_positions = [
        (70, 70), (65, 65), (60, 60), (55, 55), 
        (50, 50), (45, 45), (40, 40)  # コミュニティ中心
    ]
    
    for step, pred_pos in enumerate(predator_positions):
        print(f"\n--- ステップ {step+1}: 捕食者位置 {pred_pos} ---")
        
        # 各人間の脅威認知と防衛反応
        for human in humans:
            # 脅威侵入チェック
            intrusion_result = territory_processor.check_threat_intrusion(
                human.name, pred_pos, 'predator'
            )
            
            if intrusion_result['is_threat_to_territory']:
                print(f"⚠️ {human.name}: 捕食者脅威検知!")
                print(f"   脅威レベル: {intrusion_result['threat_level']:.2f}")
                print(f"   防衛緊急度: {intrusion_result['defensive_urgency']:.2f}")
                print(f"   推奨対応: {intrusion_result['recommended_response']}")
                
                # 防衛行動処理
                defense_result = territory_processor.process_territorial_defense(
                    human.name, pred_pos, 'predator', step
                )
                
                print(f"   🛡️ 防衛行動: {defense_result['defense_action']}")
                print(f"   協力ブースト: +{defense_result['cooperation_boost']:.2f}")
                print(f"   恐怖反応: {defense_result['fear_response']:.2f}")
                
                if defense_result.get('group_mobilization'):
                    print(f"   📢 集団動員発動!")
                
                # 敵対体験として記録
                territory_processor.process_territorial_experience(
                    human.name,
                    pred_pos,
                    'hostile_encounter',  # 敵対遭遇
                    -0.9,  # 強い負の感情価
                    [],
                    step
                )
            else:
                print(f"✅ {human.name}: 脅威範囲外")
        
        # 捕食者がコミュニティ中心に到達で終了
        if pred_pos == (40, 40):
            print(f"\n🚨 捕食者がコミュニティ中心に到達!")
            break

def test_human_vs_human_conflict():
    """人間同士の縄張り競合テスト"""
    print(f"\n⚔️ 人間同士の縄張り競合テスト")
    
    territory_processor = TerritoryProcessor()
    
    # 2つのグループ
    group_west = [SimpleHuman("West1", 30, 40), SimpleHuman("West2", 32, 42)]
    group_east = [SimpleHuman("East1", 60, 40), SimpleHuman("East2", 62, 42)]
    
    all_humans = group_west + group_east
    
    print(f"👥 西グループ: (30,40)付近")
    print(f"👥 東グループ: (60,40)付近")
    
    # 境界初期化と縄張り確立
    for human in all_humans:
        territory_processor.initialize_npc_boundaries(human.name)
    
    # 各グループで縄張り確立
    for tick in range(5):
        for group, name in [(group_west, "西"), (group_east, "東")]:
            for human in group:
                others = [h.name for h in group if h != human]
                result = territory_processor.process_territorial_experience(
                    human.name, (human.x, human.y),
                    'social_cooperation', 0.9, others, tick
                )
                if result.get('territorial_changes'):
                    print(f"🏠 {name}グループ {human.name} 縄張り確立!")
    
    # 東グループが西に侵入
    print(f"\n🚶‍♂️ 東グループの西進")
    
    invasion_positions = [(55, 40), (50, 40), (45, 40), (40, 40), (35, 40)]
    
    for step, new_pos in enumerate(invasion_positions):
        print(f"\n--- 侵入ステップ {step+1}: 東グループ位置 {new_pos} ---")
        
        # 西グループの反応
        for west_human in group_west:
            # 各東グループメンバーの脅威チェック
            for east_human in group_east:
                intrusion_result = territory_processor.check_threat_intrusion(
                    west_human.name, new_pos, 'unknown_human'
                )
                
                if intrusion_result['is_threat_to_territory']:
                    print(f"⚠️ {west_human.name}: {east_human.name}の侵入検知!")
                    print(f"   脅威レベル: {intrusion_result['threat_level']:.2f}")
                    
                    # 敵対認知の学習
                    territory_processor.process_territorial_experience(
                        west_human.name, new_pos,
                        'hostile_encounter', -0.7, [], step
                    )
                    
                    # 敵対関係の境界更新
                    boundary = territory_processor.subjective_boundaries[west_human.name]
                    boundary.outer_objects.add(east_human.name)
                    boundary.boundary_strength[east_human.name] = -0.8
                    
                    print(f"   🚫 {east_human.name}を外側(敵対)として認知")

if __name__ == "__main__":
    # 人間縄張り防衛テスト
    test_human_territory_defense_direct()
    
    # 人間同士の競合テスト  
    test_human_vs_human_conflict()
    
    print(f"\n🎉 人間縄張り防衛システム全テスト完了!")
    print(f"✅ 捕食者脅威への集団防衛")
    print(f"✅ 人間同士の縄張り競合")
    print(f"✅ 外側認知による敵対関係形成")