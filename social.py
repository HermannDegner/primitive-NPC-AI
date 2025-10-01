"""
SSD Village Simulation - Social System
構造主観力学(SSD)理論に基づく原始村落シミュレーション - 社会システム
"""

import math


class Territory:
    """縄張りシステム"""
    def __init__(self, center, radius=5, owner=None):
        self.center = center
        self.radius = radius
        self.owner = owner
        self.members = set()
        if owner:
            self.members.add(owner)
        self.established_tick = 0
        
    def contains(self, pos):
        """指定位置が縄張り内にあるかチェック"""
        x, y = pos
        cx, cy = self.center
        return math.sqrt((x-cx)**2 + (y-cy)**2) <= self.radius
        
    def add_member(self, npc_name):
        """メンバーを追加"""
        self.members.add(npc_name)
        
    def remove_member(self, npc_name):
        """メンバーを削除"""
        self.members.discard(npc_name)
        
    def get_member_count(self):
        """メンバー数を取得"""
        return len(self.members)
        
    def is_empty(self):
        """縄張りが空かどうか"""
        return len(self.members) == 0