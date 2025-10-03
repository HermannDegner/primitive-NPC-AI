"""
NPC Movement Module - 移動とナビゲーション機能
"""

import math
import sys
import os

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import distance_between, log_event


class NPCMovementMixin:
    """NPC移動機能のミックスイン"""
    
    def distance_to(self, pos):
        """指定位置までの距離を計算"""
        return distance_between(self.pos(), pos)

    def move_towards(self, target):
        """目標に向かって移動"""
        tx, ty = target
        dx = tx - self.x
        dy = ty - self.y

        if dx == 0 and dy == 0:
            return

        # 移動距離を正規化
        distance = math.sqrt(dx**2 + dy**2)
        move_distance = min(2, distance)

        if distance > 0:
            self.x += int(dx / distance * move_distance)
            self.y += int(dy / distance * move_distance)

        self.x = max(0, min(self.env.size - 1, self.x))
        self.y = max(0, min(self.env.size - 1, self.y))

    def move_towards_efficiently(self, target):
        """効率的な移動（疲労時の緊急移動）"""
        tx, ty = target
        dx = tx - self.x
        dy = ty - self.y

        if dx == 0 and dy == 0:
            return

        # より大きなステップで移動（最大3歩）
        distance = math.sqrt(dx**2 + dy**2)
        move_distance = min(3, distance)  # 通常の1.5倍速

        if distance > 0:
            self.x += int(dx / distance * move_distance)
            self.y += int(dy / distance * move_distance)

        self.x = max(0, min(self.env.size - 1, self.x))
        self.y = max(0, min(self.env.size - 1, self.y))

    def consider_exploration_mode_shift(self, t):
        """SSD理論：意味圧に応じた探索モードの跳躍的変化と復帰判定 (SSD Core Engine版)"""
        
        # SSD Core Engine版の探索機能を使用
        if self.ssd_enhanced_ref:
            life_crisis = self.ssd_enhanced_ref.calculate_life_crisis_pressure_v2()
            
            if self.exploration_mode:
                # 命の危機時は即座に探索モードを終了
                if life_crisis > 1.5:
                    self.exploration_mode = False
                    log_event(
                        self.log,
                        {
                            "t": t,
                            "name": self.name,
                            "action": "emergency_exploration_exit_v2",
                            "life_crisis": life_crisis,
                            "reason": "ssd_engine_life_crisis_override",
                        },
                    )
                    return True

                # 通常の復帰判定（SSD Core Engine版）
                exploration_pressure = self.ssd_enhanced_ref.calculate_exploration_pressure_v2()
                return self.ssd_enhanced_ref.consider_mode_reversion_v2(t, exploration_pressure)
            else:
                # 命の危機時は探索モードへの突入を抑制
                if life_crisis > 1.0:
                    return False

                # 通常の跳躍判定（SSD Core Engine版）
                exploration_pressure = self.ssd_enhanced_ref.calculate_exploration_pressure_v2()
                return self.ssd_enhanced_ref.consider_exploration_leap_v2(t, exploration_pressure)
        else:
            # フォールバック: SSD Enhanced NPCが設定されていない場合は探索モード変更しない
            return False

    def assess_predator_threat(self):
        """捕食者脅威の評価"""
        threat_level = 0.0
        nearby_predators = []

        for predator in self.env.predators:
            if predator.alive and self.distance_to(predator.pos()) <= 10:
                distance = self.distance_to(predator.pos())
                threat = (10 - distance) / 10 * predator.aggression
                threat_level += threat
                nearby_predators.append(predator)

        return threat_level, nearby_predators