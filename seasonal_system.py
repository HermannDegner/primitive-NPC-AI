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
        
        if season == 0:  # 春 - 成長期（改善版）
            return {
                'berry_abundance': 0.8 + (progress * 0.4),  # 植物性食物も適度に復活
                'prey_activity': 0.8 + (progress * 0.4),  # 動物も適度に活発
                'water_availability': 1.2,
                'temperature_stress': 0.0,
                'predator_activity': 0.0,  # 捕食者なし
                'exploration_bonus': 0.3,  # 探索に適した季節
                'social_gathering_bonus': 0.2,  # 積極的な社交
                'starvation_risk': 0.0  # 春に飢餓リスクなし
            }
        elif season == 1:  # 夏 - 豊穣期（改善版）
            return {
                'berry_abundance': 1.2 - (progress * 0.2),  # 豊かな植物性食物
                'prey_activity': 1.3 - (progress * 0.1),  # 動物も活発
                'water_availability': 1.0 - (progress * 0.2),  # 緊急時以外は十分
                'temperature_stress': progress * 0.2,  # 暑さストレスは緊急時以外
                'predator_activity': 0.0,  # 捕食者なし
                'exploration_bonus': 0.1,  # 探索も可能
                'social_gathering_bonus': 0.4,  # 豊かな食料で社交活発
                'starvation_risk': 0.0  # 夏に飢餓リスクなし
            }
        elif season == 2:  # 秋 - 準備期（改善版）
            return {
                'berry_abundance': 1.0 - (progress * 0.5),  # 源減していくが適度
                'prey_activity': 0.9 - (progress * 0.3),  # 動物も減っていくが適度
                'water_availability': 0.9 + (progress * 0.2),  # 雨期で回復
                'temperature_stress': 0.1,
                'predator_activity': 0.0,  # 捕食者なし
                'exploration_bonus': 0.2,  # 探索は可能
                'social_gathering_bonus': 0.5,  # 冬の準備で集結
                'hoarding_pressure': progress * 0.5,  # 適度な蓄え圧力
                'starvation_risk': progress * 0.2  # 軽微な飢餓リスク
            }
        else:  # 冬 - 試練期（改善版）
            return {
                'berry_abundance': 0.1 + (math.sin(progress * 3.14159) * 0.05),  # 植物性食物極少
                'prey_activity': 0.3 - (progress * 0.1),  # 動物も少ないが存在
                'water_availability': 0.7,  # 水は確保可能
                'temperature_stress': 0.4 + (progress * 0.3),  # 寒さストレス
                'predator_activity': 0.0,  # 捕食者なし
                'exploration_bonus': -0.2,  # 探索困難だが可能
                'social_gathering_bonus': 0.8,  # 寒さで集まる必要性
                'survival_pressure': 0.6 + (progress * 0.2),  # 適度な生存圧力
                'shelter_importance': 0.7,  # 避難所の重要性
                'starvation_risk': 0.3 + (progress * 0.3)  # 管理可能な飢餓リスク
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