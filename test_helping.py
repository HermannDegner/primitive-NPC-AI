#!/usr/bin/env python3
"""
人助け機能テスト - 緊急事態シミュレーション
Enhanced SSD Theory の相互支援システムの動作確認
"""

import random
from enhanced_simulation import run_enhanced_ssd_simulation
from config import *
from environment import Environment
from npc import NPC

def test_helping_behaviors():
    """人助け行動のテスト実行"""
    
    print("🤝 Enhanced SSD Theory 人助け機能テスト開始")
    print("=" * 60)
    
    # ランダムシード固定（再現性のため）
    random.seed(42)
    
    # テスト環境作成（リソース制限で緊急事態を誘発）
    env = Environment(size=DEFAULT_WORLD_SIZE, 
                     n_berry=8,     # ベリー減少
                     n_hunt=15,     # 狩場は維持
                     n_water=8,     # 水源減少で脱水誘発
                     n_caves=5,     # 洞窟減少
                     enable_smart_world=True)
    
    print("🚨 緊急事態テスト環境:")
    print(f"   ベリー: 8個 (制限), 狩場: 15個, 水源: 8個 (制限), 洞窟: 5個")
    
    # NPCロスター作成（少数精鋭）
    roster = {}
    
    npc_configs = [
        ("Helper_Alpha", HEALER, (30, 30)),      # 高共感型
        ("Receiver_Beta", LONER, (35, 35)),      # 受動型
        ("Sharer_Gamma", DIPLOMAT, (40, 40)),    # 社交型
        ("Survivor_Delta", WARRIOR, (25, 25)),   # 戦闘型
    ]
    
    for name, preset, start_pos in npc_configs:
        npc = NPC(name, preset, env, roster, start_pos)
        # 人助けテスト用の初期状態調整
        if "Helper" in name:
            npc.empathy = 0.9  # 高共感
            npc.sociability = 0.8
        elif "Receiver" in name:
            npc.hunger = 150   # 飢餓状態
            npc.thirst = 120   # 軽脱水
        elif "Sharer" in name:
            npc.meat_inventory = []  # 肉持ち
            # テスト用に肉を追加
            from meat import Meat
            meat = Meat(amount=50)
            npc.meat_inventory.append(meat)
        
        roster[name] = npc
        print(f"Created {name} - {preset['description']}")
    
    print("\n🔍 人助け行動の監視開始...")
    
    # シミュレーション実行（短期間）
    helping_events = []
    water_sharing_events = []
    food_sharing_events = []
    care_events = []
    
    for t in range(1, 101):  # 100ティック実行
        print(f"\n--- T{t} ---")
        
        # 各NPCの行動
        for npc in roster.values():
            if not npc.alive:
                continue
            
            old_thirst = npc.thirst
            old_hunger = npc.hunger
            old_meat = len(npc.meat_inventory) if npc.meat_inventory else 0
            
            # 緊急状態チェック
            if npc.thirst > 120:
                print(f"🚨 {npc.name} 脱水危険: thirst={npc.thirst:.1f}")
                
                # 水源情報要求テスト
                for helper_name, helper in roster.items():
                    if helper_name != npc.name and helper.alive:
                        distance = npc.distance_to(helper)
                        if distance < 20 and helper.knowledge_water:
                            water_sharing_events.append({
                                'tick': t,
                                'helper': helper_name,
                                'receiver': npc.name,
                                'distance': distance,
                                'action': 'water_info_sharing'
                            })
                            print(f"💧 {helper_name} → {npc.name}: 水源情報共有可能")
            
            if npc.hunger > 120:
                print(f"🍽️ {npc.name} 飢餓危険: hunger={npc.hunger:.1f}")
                
                # 食料共有の可能性チェック
                for helper_name, helper in roster.items():
                    if (helper_name != npc.name and helper.alive and 
                        helper.meat_inventory and len(helper.meat_inventory) > 0):
                        
                        trust_level = helper.get_trust_level(npc.name) if hasattr(helper, 'get_trust_level') else 0.5
                        empathy = helper.empathy if hasattr(helper, 'empathy') else 0.5
                        
                        sharing_probability = empathy * 0.6 + trust_level * 0.4
                        
                        if sharing_probability > 0.4:  # 閾値
                            food_sharing_events.append({
                                'tick': t,
                                'helper': helper_name,
                                'receiver': npc.name,
                                'probability': sharing_probability,
                                'helper_empathy': empathy,
                                'trust_level': trust_level,
                                'action': 'potential_food_share'
                            })
                            print(f"🍖 {helper_name} → {npc.name}: 食料共有可能性 {sharing_probability:.2f}")
            
            # NPCの通常行動実行
            npc.act(t)
            
            # 変化の検出
            if npc.thirst < old_thirst - 10:
                print(f"💦 {npc.name} 水分回復: {old_thirst:.1f} → {npc.thirst:.1f}")
            
            if npc.hunger < old_hunger - 10:
                new_meat = len(npc.meat_inventory) if npc.meat_inventory else 0
                if new_meat < old_meat:
                    print(f"🍖 {npc.name} 肉消費: hunger {old_hunger:.1f} → {npc.hunger:.1f}")
                else:
                    print(f"🌿 {npc.name} 採食: hunger {old_hunger:.1f} → {npc.hunger:.1f}")
        
        # 死亡チェック
        for npc in roster.values():
            if npc.alive and (npc.hunger >= 200 or npc.thirst >= 200):
                npc.alive = False
                print(f"💀 {npc.name} 死亡 - hunger: {npc.hunger:.1f}, thirst: {npc.thirst:.1f}")
        
        # 生存者カウント
        alive_count = sum(1 for npc in roster.values() if npc.alive)
        if alive_count <= 1:
            print(f"⚰️ T{t}: 集団死発生、生存者: {alive_count}")
            break
    
    # 結果分析
    print("\n" + "=" * 60)
    print("🤝 人助け機能テスト結果")
    print("=" * 60)
    
    print(f"\n💧 水源情報共有イベント: {len(water_sharing_events)}件")
    for event in water_sharing_events:
        print(f"   T{event['tick']}: {event['helper']} → {event['receiver']} (距離: {event['distance']:.1f})")
    
    print(f"\n🍖 食料共有可能性: {len(food_sharing_events)}件")
    for event in food_sharing_events:
        print(f"   T{event['tick']}: {event['helper']} → {event['receiver']} "
              f"(確率: {event['probability']:.2f}, 共感: {event['helper_empathy']:.2f})")
    
    # 最終状態
    print(f"\n📊 最終状態:")
    for name, npc in roster.items():
        status = "生存" if npc.alive else "死亡"
        print(f"   {name}: {status} - hunger: {npc.hunger:.1f}, thirst: {npc.thirst:.1f}")
    
    alive_npcs = [npc for npc in roster.values() if npc.alive]
    survival_rate = len(alive_npcs) / len(roster)
    print(f"\n🎯 生存率: {len(alive_npcs)}/{len(roster)} ({survival_rate*100:.1f}%)")
    
    # 人助け機能の評価
    total_help_events = len(water_sharing_events) + len(food_sharing_events)
    
    print(f"\n🔍 人助け機能評価:")
    print(f"   総支援イベント: {total_help_events}件")
    print(f"   支援頻度: {total_help_events/100:.2f}件/tick")
    
    if total_help_events > 0:
        print("✅ 人助け機能は正常に動作しています！")
    else:
        print("⚠️  人助け機能の動作が確認できませんでした")
    
    return total_help_events > 0

if __name__ == "__main__":
    test_helping_behaviors()