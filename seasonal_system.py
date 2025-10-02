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
        self.season_names = ["🌸Spring", "🌞Summer", "🍂Autumn", "❄️Winter"]
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
        
        if season == 0:  # 春 - 成長期
            return {
                'berry_abundance': 1.0 + (progress * 0.8),  # 段階的増加
                'prey_activity': 1.0 + (progress * 0.6),
                'water_availability': 1.2,
                'temperature_stress': 0.0,
                'predator_activity': 0.8,  # 捕食者は比較的大人しい
                'exploration_bonus': 0.3,  # 探索に適した季節
                'social_gathering_bonus': 0.2
            }
        elif season == 1:  # 夏 - 豊穣期
            return {
                'berry_abundance': 1.8 - (progress * 0.3),  # 前半ピーク、後半減少
                'prey_activity': 1.4,
                'water_availability': 1.0 - (progress * 0.4),  # 段階的減少
                'temperature_stress': progress * 0.3,  # 暑さによるストレス
                'predator_activity': 1.2,  # 捕食者も活発
                'exploration_bonus': -0.1,  # 暑さで探索困難
                'social_gathering_bonus': 0.4  # 豊富な食料で社交活発
            }
        elif season == 2:  # 秋 - 準備期
            return {
                'berry_abundance': 1.2 - (progress * 0.7),  # 急激な減少
                'prey_activity': 1.0 - (progress * 0.3),
                'water_availability': 0.8 + (progress * 0.3),  # 雨期で回復
                'temperature_stress': 0.1,
                'predator_activity': 1.0 + (progress * 0.4),  # 冬に備えて活発化
                'exploration_bonus': 0.1,
                'social_gathering_bonus': -0.2,  # 準備で忙しく社交減少
                'hoarding_pressure': progress * 0.6  # 蓄え圧力
            }
        else:  # 冬 - 試練期
            return {
                'berry_abundance': 0.2 + (math.sin(progress * 3.14159) * 0.1),  # 極少
                'prey_activity': 0.4,  # 動物も少ない
                'water_availability': 0.6,  # 氷結などで減少
                'temperature_stress': 0.4 + (progress * 0.3),  # 寒さストレス
                'predator_activity': 0.6 - (progress * 0.2),  # 後半は冬眠傾向
                'exploration_bonus': -0.3,  # 探索困難
                'social_gathering_bonus': 0.5,  # 寒さで集まる傾向
                'survival_pressure': 0.4 + (progress * 0.4),  # 生存圧力最大
                'shelter_importance': 0.8
            }
    
    def apply_seasonal_effects(self, env, npcs, t):
        """環境とNPCに季節効果を適用"""
        modifiers = self.get_seasonal_modifiers(t)
        
        # 捕食者の活動度調整
        for predator in env.predators:
            if hasattr(predator, 'aggression'):
                if not hasattr(predator, 'base_aggression'):
                    predator.base_aggression = predator.aggression
                predator.aggression = predator.base_aggression * modifiers.get('predator_activity', 1.0)
        
        # NPCへの効果
        for npc in npcs:
            if not npc.alive:
                continue
                
            # 温度ストレス
            temp_stress = modifiers.get('temperature_stress', 0.0)
            if temp_stress > 0:
                npc.fatigue += temp_stress * 2
            
            # 探索ボーナス/ペナルティ
            exploration_mod = modifiers.get('exploration_bonus', 0.0)
            if hasattr(npc, 'seasonal_curiosity_mod'):
                npc.seasonal_curiosity_mod = exploration_mod
            else:
                npc.seasonal_curiosity_mod = exploration_mod
            
            # 社交性への影響
            social_mod = modifiers.get('social_gathering_bonus', 0.0)
            if hasattr(npc, 'seasonal_social_mod'):
                npc.seasonal_social_mod = social_mod
            else:
                npc.seasonal_social_mod = social_mod
            
            # 生存圧力
            survival_pressure = modifiers.get('survival_pressure', 0.0)
            if survival_pressure > 0:
                npc.hunger += survival_pressure * 1.5
                npc.thirst += survival_pressure * 1.0
        
        return modifiers