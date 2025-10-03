#!/usr/bin/env python3
"""
Seasonal System Module - 季節システム
環境と資源の動的変化を管理
"""

import math


class SeasonalSystem:
    """季節システム - 環境と資源の動的変化"""

    def __init__(self, season_length=50):
        self.season_length = season_length  # 1季節の長さ（ティック）
        self.current_season = 0  # 0:春, 1:夏, 2:秋, 3:冬
        self.season_names = ["Spring", "Summer", "Autumn", "Winter"]
        self.season_tick = 0

    def get_current_season(self, t):
        """現在の季節を取得"""
        self.season_tick = t % (self.season_length * 4)
        self.current_season = self.season_tick // self.season_length
        return self.current_season

    def get_season_name(self, t):
        """季節名を取得"""
        season = self.get_current_season(t)
        return self.season_names[season]

    def get_seasonal_modifiers(self, t):
        """季節による環境修正値"""
        season = self.get_current_season(t)
        progress = (self.season_tick % self.season_length) / self.season_length

        if season == 0:  # 春 - 成長期（改善版）
            return {
                "berry_abundance": 0.8 + (progress * 0.4),  # 植物性食物も適度に復活
                "prey_activity": 0.8 + (progress * 0.4),  # 動物も適度に活発
                "water_availability": 1.2,
                "temperature_stress": 0.0,
                "predator_activity": 1.0,  # 捕食者活動を有効化
                "exploration_bonus": 0.3,  # 探索に適した季節
                "social_gathering_bonus": 0.2,  # 積極的な社交
                "starvation_risk": 0.0,  # 春に飢餓リスクなし
            }
        elif season == 1:  # 夏 - 豊穣期（環境圧大幅緩和版）
            return {
                "berry_abundance": 1.5,  # 植物性食物を大幅増量
                "prey_activity": 1.5,  # 動物も大幅増量
                "water_availability": 1.3,  # 水も十分に確保
                "temperature_stress": 0.0,  # 暑さストレスを完全に除去
                "predator_activity": 0.7,  # 捕食者活動を軽減
                "exploration_bonus": 0.3,  # 探索しやすく
                "social_gathering_bonus": 0.5,  # 社交を活発に
                "starvation_risk": 0.0,  # 夏に飢餓リスクなし
                "thirst_resistance": 0.5,  # 脱水耐性を追加
            }
        elif season == 2:  # 秋 - 準備期（さらに緩和版）
            return {
                "berry_abundance": 1.0 - (progress * 0.3),  # 徐々に減るが緩やか
                "prey_activity": 0.9 - (progress * 0.2),  # 動物も緩やかに減る
                "water_availability": 0.9 + (progress * 0.2),  # 雨期で回復
                "temperature_stress": 0.05,  # 温度ストレスを軽減
                "predator_activity": 1.0,  # 捕食者活動を有効化
                "exploration_bonus": 0.2,  # 探索は可能
                "social_gathering_bonus": 0.4,  # 社交を適度に
                "hoarding_pressure": progress * 0.1,  # 蓄え圧力をさらに軽減
                "starvation_risk": progress * 0.02,  # 飢餓リスクをさらに軽減
            }
        else:  # 冬 - 試練期（さらに緩和版）
            return {
                "berry_abundance": 1.0,  # 植物性食物を最大化
                "prey_activity": 1.0,  # 動物を最大化
                "water_availability": 0.8,  # 水の可用性を上げる
                "temperature_stress": 0.0,  # 寒さストレスをゼロに
                "predator_activity": 1.0,  # 捕食者活動を有効化
                "exploration_bonus": 0.0,  # 探索を中立的
                "social_gathering_bonus": 0.6,  # 社交を適度に
                "survival_pressure": 0.0,  # 生存圧力をゼロに
                "shelter_importance": 0.0,  # 避難所の重要性をゼロに
                "starvation_risk": 0.0,  # 飢餓リスクをゼロに
            }

    def apply_seasonal_effects(self, env, npcs, t):
        """環境とNPCに季節効果を適用"""
        modifiers = self.get_seasonal_modifiers(t)

        # 捕食者の活動度調整
        for predator in env.predators:
            if hasattr(predator, "aggression"):
                if not hasattr(predator, "base_aggression"):
                    predator.base_aggression = predator.aggression
                predator.aggression = predator.base_aggression * modifiers.get(
                    "predator_activity", 1.0
                )

        # NPCへの効果
        for npc in npcs:
            if not npc.alive:
                continue

            # 温度ストレス
            temp_stress = modifiers.get("temperature_stress", 0.0)
            if temp_stress > 0:
                npc.fatigue += temp_stress * 2

            # 探索ボーナス/ペナルティ
            exploration_mod = modifiers.get("exploration_bonus", 0.0)
            if hasattr(npc, "seasonal_curiosity_mod"):
                npc.seasonal_curiosity_mod = exploration_mod
            else:
                npc.seasonal_curiosity_mod = exploration_mod

            # 社交性への影響
            social_mod = modifiers.get("social_gathering_bonus", 0.0)
            if hasattr(npc, "seasonal_social_mod"):
                npc.seasonal_social_mod = social_mod
            else:
                npc.seasonal_social_mod = social_mod

            # 生存圧力
            survival_pressure = modifiers.get("survival_pressure", 0.0)
            if survival_pressure > 0:
                npc.hunger += survival_pressure * 1.5
                npc.thirst += survival_pressure * 1.0

        return modifiers
