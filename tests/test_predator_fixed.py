# 捕食者システム復活テスト（修正版）
from environment import Environment, Predator

# テスト環境作成（正しいパラメータ）
env = Environment(size=100, n_berry=30, n_hunt=20, n_water=20, n_caves=10)

# 捕食者を追加
predator1 = Predator((25, 25), aggression=0.8)
predator2 = Predator((75, 75), aggression=0.7)
env.predators = [predator1, predator2]

print(f"🐺 捕食者システム復活完了!")
print(f"   捕食者数: {len(env.predators)}")
print(f"   捕食者1: 位置({predator1.x}, {predator1.y}) 攻撃性{predator1.aggression}")
print(f"   捕食者2: 位置({predator2.x}, {predator2.y}) 攻撃性{predator2.aggression}")
print(f"   捕食者1 SSDパラメータ - E:{predator1.E} κ:{predator1.kappa} P:{predator1.P}")

# 捕食者攻撃テスト
class MockNPC:
    def __init__(self, name, x, y):
        self.name = name
        self.x, self.y = x, y
        self.alive = True
        self.predator_encounters = 0
        self.predator_escapes = 0
        self.hunger = 50
        self.fatigue = 30
        
    def pos(self):
        return (self.x, self.y)
        
    def get_predator_avoidance_chance(self):
        return 0.3
        
    def get_predator_detection_chance(self):
        return 0.4
        
    def get_predator_escape_chance(self):
        return 0.5
        
    def alert_nearby_npcs_about_predator(self, npcs, location):
        pass
        
    def gain_experience(self, type, amount, tick):
        pass

# テスト用NPC作成
test_npc = MockNPC("TestNPC", 26, 26)

# 捕食者攻撃シミュレーション
print(f"\\n🎯 捕食者攻撃テスト:")
result = predator1.hunt_step([test_npc], 1)
if result:
    print(f"   攻撃結果: {result}")
else:
    print(f"   攻撃なし（範囲外または回避成功）")

print(f"\\n✅ 捕食者システム動作確認完了!")
