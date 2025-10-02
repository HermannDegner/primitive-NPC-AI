#!/usr/bin/env python3
"""
水源テスト - 水源が有限かどうかの検証
Enhanced SSD Theory における水源システムの仕組み分析
"""

from environment import Environment
from config import *

def test_water_source_mechanics():
    """水源の仕組みをテストする"""
    
    print("🔍 水源システム分析テスト")
    print("=" * 50)
    
    # 小さな環境で水源を少数作成
    env = Environment(size=20, n_berry=0, n_hunt=0, n_water=3, n_caves=0, enable_smart_world=False)
    
    print(f"🌊 初期水源数: {len(env.water_sources)}")
    print("初期水源位置:")
    for name, pos in env.water_sources.items():
        print(f"   {name}: {pos}")
    
    # 簡易NPCクラスを作成（テスト用）
    class TestNPC:
        def __init__(self, name, pos, env):
            self.name = name
            self.x, self.y = pos
            self.env = env
            self.thirst = 100
            self.knowledge_water = set(env.water_sources.keys())  # 全水源を知っている状態
            self.alive = True
        
        def pos(self):
            return (self.x, self.y)
        
        def move_to(self, target_pos):
            self.x, self.y = target_pos
        
        def drink_water(self, t):
            """水を飲む"""
            known_water = {k: v for k, v in self.env.water_sources.items() if k in self.knowledge_water}
            if known_water:
                nearest_water = self.env.nearest_nodes(self.pos(), known_water, k=1)
                if nearest_water:
                    target = nearest_water[0]
                    if self.pos() == target:
                        old_thirst = self.thirst
                        self.thirst = max(0, self.thirst - 35)
                        print(f"💧 T{t}: {self.name} drank water at {target}, thirst: {old_thirst:.1f} → {self.thirst:.1f}")
                        return True
                    else:
                        self.move_to(target)
                        print(f"🚶 T{t}: {self.name} moved to water source at {target}")
            return False
    
    # テストNPCを作成
    test_npc1 = TestNPC("Test_Alpha", (5, 5), env)
    test_npc2 = TestNPC("Test_Beta", (10, 10), env)
    test_npc3 = TestNPC("Test_Gamma", (15, 15), env)
    
    npcs = [test_npc1, test_npc2, test_npc3]
    
    print(f"\n🧪 水源使用テスト開始")
    print(f"NPCs: {[npc.name for npc in npcs]}")
    
    # 50ティック間、各NPCが水を飲み続ける
    for t in range(1, 51):
        print(f"\n--- T{t} ---")
        
        # 水源の存在確認
        print(f"🌊 現在の水源数: {len(env.water_sources)}")
        
        for npc in npcs:
            if npc.alive:
                npc.thirst += 5  # 渇きを人工的に増加
                if npc.thirst > 50:
                    npc.drink_water(t)
        
        # 水源が減っているかチェック
        if len(env.water_sources) != 3:
            print(f"⚠️ 水源数変化: {len(env.water_sources)}")
            break
    
    print(f"\n📊 テスト結果:")
    print(f"   最終水源数: {len(env.water_sources)}")
    print(f"   水源は消費されるか: {'はい' if len(env.water_sources) != 3 else 'いいえ'}")
    
    # 同じ水源での複数回使用テスト
    print(f"\n🔄 同一水源複数使用テスト:")
    
    # 最初の水源に全員を移動
    first_water_pos = list(env.water_sources.values())[0]
    for npc in npcs:
        npc.move_to(first_water_pos)
        npc.thirst = 100
    
    print(f"全NPCを {first_water_pos} に配置")
    
    # 全員が同じ水源で飲む
    for i in range(5):
        print(f"\nラウンド {i+1}:")
        for npc in npcs:
            npc.thirst = 100  # 渇きをリセット
            success = npc.drink_water(100 + i)
            if not success:
                print(f"❌ {npc.name} 水を飲めませんでした")
    
    print(f"\n📈 結論:")
    if len(env.water_sources) == 3:
        print("✅ 水源は無限 - 何度でも使用可能")
    else:
        print("❌ 水源は有限 - 使用すると消費される")
    
    return len(env.water_sources) == 3

if __name__ == "__main__":
    is_infinite = test_water_source_mechanics()
    print(f"\n🌊 水源システム: {'無限' if is_infinite else '有限'}")