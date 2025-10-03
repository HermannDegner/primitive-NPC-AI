"""
SSD Village Simulation - Smart Dynamic World System
4層物理構造SSDと連携する知的環境システム
"""

import random
import math
from collections import defaultdict, deque
from typing import Dict, List, Tuple


class SmartEnvironment:
    """4層物理構造SSDと連携する知的環境システム"""

    def __init__(self, world_size: int = 90):
        self.world_size = world_size

        # 環境知性パラメータ
        self.adaptation_memory = deque(maxlen=50)  # 環境の記憶
        self.npc_activity_patterns = defaultdict(float)
        self.resource_pressure_map = {}

        # 動的環境特性
        self.biodiversity_level = 1.0
        self.resource_regeneration_rate = 1.0
        self.environmental_stress = 0.0
        self.climate_stability = 1.0

        # 地形特性マップ（簡略化）
        self.terrain_quality = self._generate_terrain_quality()

    def _generate_terrain_quality(self) -> Dict[Tuple[int, int], float]:
        """地形品質マップ生成"""
        quality_map = {}
        for x in range(0, self.world_size, 5):
            for y in range(0, self.world_size, 5):
                # 簡単な地形品質計算
                quality = 0.5 + 0.3 * math.sin(x * 0.1) * math.cos(y * 0.1)
                quality += 0.2 * random.uniform(-0.3, 0.3)
                quality = max(0.1, min(1.0, quality))
                quality_map[(x, y)] = quality
        return quality_map

    def analyze_npc_impact(self, npcs: List, current_tick: int):
        """NPCの活動が環境に与える影響を分析"""
        if not npcs:
            return

        # 活動パターンの分析
        activity_summary = {
            "exploration_activity": 0,
            "foraging_pressure": 0,
            "hunting_pressure": 0,
            "settlement_density": 0,
            "total_population": len([npc for npc in npcs if npc.alive]),
        }

        for npc in npcs:
            if not npc.alive:
                continue

            # 最近の活動分析
            if npc.log and len(npc.log) > 0:
                recent_activity = npc.log[-1]
                action = recent_activity.get("action", "")

                if "exploration" in action:
                    activity_summary["exploration_activity"] += 1
                elif "foraging" in action or "berries" in action:
                    activity_summary["foraging_pressure"] += 1
                elif "hunting" in action:
                    activity_summary["hunting_pressure"] += 1

            # 定住密度の計算
            if npc.territory:
                activity_summary["settlement_density"] += 1

        # 環境への影響計算
        self._update_environmental_parameters(activity_summary)

        # 記憶に追加
        self.adaptation_memory.append(
            {
                "tick": current_tick,
                "activity": activity_summary,
                "biodiversity": self.biodiversity_level,
                "stress": self.environmental_stress,
            }
        )

    def _update_environmental_parameters(self, activity_summary: Dict):
        """活動サマリーに基づく環境パラメータ更新"""
        total_pop = activity_summary["total_population"]
        if total_pop == 0:
            return

        # 採集圧力による資源再生率への影響
        foraging_rate = activity_summary["foraging_pressure"] / max(1, total_pop)
        self.resource_regeneration_rate *= 1.0 - foraging_rate * 0.1
        self.resource_regeneration_rate = max(0.5, min(1.5, self.resource_regeneration_rate))

        # 狩猟圧力による生物多様性への影響
        hunting_rate = activity_summary["hunting_pressure"] / max(1, total_pop)
        self.biodiversity_level *= 1.0 - hunting_rate * 0.05

        # 探索活動による環境発見効果
        exploration_rate = activity_summary["exploration_activity"] / max(1, total_pop)
        if exploration_rate > 0.3:
            self.biodiversity_level += 0.02  # 新種発見効果

        # 環境ストレスの計算
        total_pressure = foraging_rate + hunting_rate * 1.5
        self.environmental_stress = min(1.0, total_pressure)

        # 自然回復
        self.biodiversity_level = min(1.0, self.biodiversity_level + 0.001)
        self.environmental_stress *= 0.98
        self.resource_regeneration_rate = min(1.0, self.resource_regeneration_rate + 0.002)

    def get_regional_conditions(self, location: Tuple[int, int]) -> Dict[str, float]:
        """指定地域の環境条件を取得"""
        # 最寄りの地形品質を取得
        terrain_quality = self._get_interpolated_terrain_quality(location)

        # 地域の環境条件を計算
        conditions = {
            "terrain_quality": terrain_quality,
            "resource_abundance": terrain_quality * self.resource_regeneration_rate,
            "biodiversity": self.biodiversity_level,
            "environmental_stress": self.environmental_stress,
            "climate_stability": self.climate_stability,
        }

        return conditions

    def _get_interpolated_terrain_quality(self, location: Tuple[int, int]) -> float:
        """地形品質の補間取得"""
        x, y = location
        x_base, y_base = (x // 5) * 5, (y // 5) * 5

        # 最寄りの品質値を使用
        if (x_base, y_base) in self.terrain_quality:
            return self.terrain_quality[(x_base, y_base)]

        # 近傍値の平均を計算
        nearby_values = []
        for dx in [-5, 0, 5]:
            for dy in [-5, 0, 5]:
                point = (x_base + dx, y_base + dy)
                if point in self.terrain_quality:
                    nearby_values.append(self.terrain_quality[point])

        return sum(nearby_values) / len(nearby_values) if nearby_values else 0.5

    def generate_environmental_pressure(
        self, location: Tuple[int, int], base_pressure: float = 0.0
    ) -> float:
        """環境圧力の生成"""
        pressure = base_pressure

        # 地域の環境ストレスを追加
        pressure += self.environmental_stress * 0.3

        # 気候不安定性による圧力
        pressure += (1.0 - self.climate_stability) * 0.4

        # 資源枯渇による圧力
        regional_conditions = self.get_regional_conditions(location)
        if regional_conditions["resource_abundance"] < 0.5:
            pressure += (0.5 - regional_conditions["resource_abundance"]) * 0.5

        return min(2.0, max(0.0, pressure))

    def provide_npc_environmental_feedback(self, npc, current_tick: int) -> Dict[str, float]:
        """NPCに提供する環境フィードバック"""
        if not npc.alive:
            return {}

        location = npc.pos()
        regional_conditions = self.get_regional_conditions(location)
        environmental_pressure = self.generate_environmental_pressure(location)

        # NPCの4層物理構造システム用のフィードバック
        feedback = {
            "environmental_pressure": environmental_pressure,
            "resource_scarcity": 1.0 - regional_conditions["resource_abundance"],
            "biodiversity_health": regional_conditions["biodiversity"],
            "climate_stress": 1.0 - regional_conditions["climate_stability"],
            "adaptation_opportunity": self._calculate_adaptation_opportunity(npc),
        }

        return feedback

    def _calculate_adaptation_opportunity(self, npc) -> float:
        """NPCの適応機会を計算"""
        # NPCの経験レベルに基づく適応機会
        if hasattr(npc, "experience") and npc.experience:
            avg_experience = sum(npc.experience.values()) / len(npc.experience)
            experience_factor = min(1.0, avg_experience / 5.0)
        else:
            experience_factor = 0.1

        # 環境の多様性による機会
        biodiversity_factor = self.biodiversity_level

        # 探索モードボーナス
        exploration_bonus = 0.3 if getattr(npc, "exploration_mode", False) else 0.0

        opportunity = experience_factor * 0.4 + biodiversity_factor * 0.4 + exploration_bonus
        return min(1.0, opportunity)

    def get_intelligence_summary(self) -> Dict[str, float]:
        """環境知性のサマリー取得"""
        return {
            "biodiversity_level": self.biodiversity_level,
            "resource_regeneration_rate": self.resource_regeneration_rate,
            "environmental_stress": self.environmental_stress,
            "climate_stability": self.climate_stability,
            "adaptation_memory_size": len(self.adaptation_memory),
            "learning_capacity": min(1.0, len(self.adaptation_memory) / 50.0),
        }


def integrate_smart_environment_with_ssd(environment, npcs, current_tick):
    """スマート環境と4層物理構造SSDの統合"""
    if not hasattr(environment, "smart_env"):
        # スマート環境システムを初期化
        environment.smart_env = SmartEnvironment(environment.size)
        print("Smart Environment System initialized")

    # NPCの活動を分析
    environment.smart_env.analyze_npc_impact(npcs, current_tick)

    # 各NPCに環境フィードバックを提供
    for npc in npcs:
        if npc.alive and hasattr(npc, "physical_system") and npc.physical_system:
            feedback = environment.smart_env.provide_npc_environmental_feedback(npc, current_tick)

            # 物理層に環境情報を統合（メソッドが存在する場合）
            if hasattr(npc.physical_system.physical_layer, "update_environmental_constraints"):
                npc.physical_system.physical_layer.update_environmental_constraints(feedback)

            # 上層構造に適応機会を提供
            if hasattr(npc.physical_system.upper_layer, "receive_environmental_feedback"):
                npc.physical_system.upper_layer.receive_environmental_feedback(feedback)


# テスト関数
def test_smart_environment():
    """スマート環境システムのテスト"""
    print("Smart Environment System Test")
    print("=" * 40)

    smart_env = SmartEnvironment(world_size=90)
    print(f"Initial state: {smart_env.get_intelligence_summary()}")

    # サンプルNPC活動のシミュレーション
    class MockNPC:
        def __init__(self, name):
            self.name = name
            self.alive = True
            self.territory = None
            self.exploration_mode = False
            self.log = []
            self.experience = {"foraging": 2.0, "exploration": 1.5}

        def pos(self):
            return (30, 40)

    # モックNPCの作成
    npcs = [MockNPC(f"NPC_{i}") for i in range(5)]

    # 活動ログの追加
    npcs[0].log = [{"action": "exploration_leap", "t": 100}]
    npcs[1].log = [{"action": "foraging_berries", "t": 101}]
    npcs[2].log = [{"action": "hunting_deer", "t": 102}]
    npcs[3].territory = "Territory1"
    npcs[4].exploration_mode = True

    # 環境分析の実行
    smart_env.analyze_npc_impact(npcs, 100)

    print(f"After analysis: {smart_env.get_intelligence_summary()}")

    # 地域条件の確認
    location = (30, 40)
    conditions = smart_env.get_regional_conditions(location)
    print(f"Regional conditions at {location}: {conditions}")

    # 環境フィードバックのテスト
    feedback = smart_env.provide_npc_environmental_feedback(npcs[0], 100)
    print(f"Environmental feedback for {npcs[0].name}: {feedback}")

    print("Test completed successfully!")


if __name__ == "__main__":
    test_smart_environment()
