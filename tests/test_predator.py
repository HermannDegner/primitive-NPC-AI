# 捕食者システム復活テスト
from environment import Environment, Predator
import random

# テスト環境作成
env = Environment(
    size=100, n_berry=30, n_water=20, n_caves=10, enable_smart_world=True
)

# 捕食者を追加
predator1 = Predator((25, 25), aggression=0.8)
predator2 = Predator((75, 75), aggression=0.7)
env.predators = [predator1, predator2]

print(f"🐺 捕食者システム復活完了!")
print(f"   捕食者数: {len(env.predators)}")
print(f"   捕食者1: 位置({predator1.x}, {predator1.y}) 攻撃性{predator1.aggression}")
print(f"   捕食者2: 位置({predator2.x}, {predator2.y}) 攻撃性{predator2.aggression}")

# 捕食者の基本機能テスト
print(f"   捕食者1 SSDパラメータ - E:{predator1.E} κ:{predator1.kappa} P:{predator1.P}")
