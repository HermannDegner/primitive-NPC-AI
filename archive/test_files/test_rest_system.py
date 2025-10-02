#!/usr/bin/env python3
"""
疲労回復システムのテスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from environment import Environment
from npc import NPC

def test_rest_system():
    """疲労回復システムのテスト"""
    print("未来予測的疲労管理システムのテスト開始...")
    
    # 環境とNPCの初期化
    env = Environment()
    roster = {}  # ダミーのロスター
    preset = {"curiosity": 0.5, "sociability": 0.5}  # デフォルトプリセット
    npc = NPC("テストNPC", preset, env, roster, (25, 25))
    
    # 予測的休憩のテスト - 中程度の疲労から開始
    npc.fatigue = 55
    npc.hunger = 45  # 狩猟予定で疲労コスト予測
    print(f"初期疲労: {npc.fatigue}")
    print(f"知っている洞窟数: {len(npc.knowledge_caves)}")
    
    # 洞窟の位置と距離を確認
    if npc.knowledge_caves:
        for cave_name in npc.knowledge_caves:
            cave_pos = env.caves[cave_name]
            distance = npc.distance_to(cave_pos)
            print(f"洞窟 {cave_name}: 位置 {cave_pos}, 距離 {distance}")
    else:
        print("洞窟を知らない！")
        # 強制的に洞窟を教える
        nearest_cave = env.nearest_nodes(npc.pos(), env.caves, k=1)[0]
        cave_name = next(k for k, v in env.caves.items() if v == nearest_cave)
        npc.knowledge_caves.add(cave_name)
        print(f"最寄りの洞窟を教えた: {cave_name} at {nearest_cave}")
    
    # 予測的疲労管理テスト
    print("\n未来予測的疲労管理テスト:")
    for tick in range(1, 11):
        print(f"\nTick {tick}:")
        print(f"  疲労: {npc.fatigue}, 空腹: {npc.hunger}")
        print(f"  位置: {npc.pos()}")
        
        # 予測的休憩判断をテスト
        should_rest, rest_type = npc.consider_predictive_rest(tick)
        print(f"  休憩判断: {should_rest}, タイプ: {rest_type}")
        
        if should_rest:
            print(f"  → 休憩実行 ({rest_type})")
            npc.seek_rest(tick)
        else:
            # 通常活動で疲労増加をシミュレート
            npc.fatigue += 15  # 狩猟など
            print(f"  → 通常活動継続 (+15疲労)")
        
        print(f"  結果疲労: {npc.fatigue}")
        
        # ログの最後のエントリを確認
        if npc.log:
            last_log = npc.log[-1]
            if 'rest_type' in last_log:
                print(f"  ログ: action={last_log['action']}, rest_type={last_log['rest_type']}")
        
        # 疲労が十分回復したら終了
        if should_rest and npc.fatigue < 50:
            print("予測的システムにより疲労が管理されました！")
            break
    
    print(f"\n最終疲労: {npc.fatigue}")

if __name__ == "__main__":
    test_rest_system()