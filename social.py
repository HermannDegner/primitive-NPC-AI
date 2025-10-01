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


class HuntGroup:
    """狩りグループの管理"""
    def __init__(self, leader, target_prey_type='medium_game'):
        self.leader = leader
        self.members = [leader]
        self.target_prey_type = target_prey_type
        self.formation_tick = 0
        self.status = 'forming'  # forming, hunting, returning, disbanded
        self.hunt_location = None
        self.success = False
        self.meat_acquired = 0.0
        
    def add_member(self, npc):
        """狩りグループにメンバーを追加"""
        if npc not in self.members:
            self.members.append(npc)
            return True
        return False
    
    def remove_member(self, npc):
        """メンバーを削除"""
        if npc in self.members and npc != self.leader:
            self.members.remove(npc)
            
    def get_success_rate(self):
        """狩りの成功率を計算"""
        from config import HUNTING_SETTINGS, PREY_TYPES
        
        base_rate = HUNTING_SETTINGS['group_success_base']
        member_bonus = len(self.members) * HUNTING_SETTINGS['group_success_per_member']
        max_bonus = HUNTING_SETTINGS['max_group_bonus']
        
        prey_difficulty = PREY_TYPES[self.target_prey_type]['difficulty']
        
        success_rate = base_rate + min(member_bonus, max_bonus) - prey_difficulty
        return max(0.1, min(0.9, success_rate))
    
    def can_start_hunt(self):
        """狩りを開始できるかチェック"""
        from config import PREY_TYPES
        required_hunters = PREY_TYPES[self.target_prey_type]['required_hunters']
        return len(self.members) >= required_hunters


class MeatResource:
    """肉リソースの管理（腐敗システム付き）"""
    def __init__(self, amount, owner=None, hunt_group=None):
        self.amount = amount
        self.freshness = 1.0
        self.owner = owner  # 獲得者
        self.hunt_group = hunt_group  # 獲得した狩りグループ
        self.creation_tick = 0
        self.shared_with = set()  # 分配された相手
        
    def decay(self, ticks=1):
        """肉の腐敗進行"""
        from config import HUNTING_SETTINGS
        decay_rate = HUNTING_SETTINGS['meat_decay_rate']
        
        for _ in range(ticks):
            self.freshness *= (1.0 - decay_rate)
            
        # 完全に腐った場合
        if self.freshness < 0.1:
            self.amount = 0.0
            return True  # 腐敗完了
        return False
    
    def get_effective_nutrition(self):
        """現在の栄養価を取得（新鮮さ考慮）"""
        from config import HUNTING_SETTINGS
        base_nutrition = HUNTING_SETTINGS['meat_nutrition_value']
        return self.amount * base_nutrition * self.freshness
    
    def get_sharing_pressure(self):
        """分配圧力を計算"""
        from config import HUNTING_SETTINGS
        
        # 腐敗が進むほど分配圧力が増加
        decay_pressure = (1.0 - self.freshness) * 0.5
        
        # 大きな獲物ほど分配圧力が増加
        amount_pressure = min(1.0, self.amount / 3.0) * 0.3
        
        # 狩りグループのサイズによる社会的圧力
        group_pressure = 0.0
        if self.hunt_group:
            group_pressure = len(self.hunt_group.members) * 0.1
            
        total_pressure = decay_pressure + amount_pressure + group_pressure
        return min(1.0, total_pressure)
    
    def share_with(self, recipient, amount):
        """肉を分配"""
        if amount <= self.amount:
            self.amount -= amount
            self.shared_with.add(recipient)
            return amount
        else:
            # 残り全部を分配
            remaining = self.amount
            self.amount = 0.0
            self.shared_with.add(recipient)
            return remaining


class GroupFeast:
    """集団での食事イベント"""
    def __init__(self, participants, food_resources):
        self.participants = participants
        self.food_resources = food_resources  # MeatResourceのリスト
        self.social_bonding_effect = 0.0
        self.information_sharing = []
        self.start_tick = 0
        
    def calculate_social_effects(self):
        """共食による社会的効果を計算"""
        participant_count = len(self.participants)
        
        # 参加者数による結束効果
        bonding_base = min(0.8, participant_count * 0.1)
        
        # 食料の質による効果（新鮮な肉ほど効果大）
        food_quality = sum(res.freshness for res in self.food_resources) / len(self.food_resources)
        quality_bonus = food_quality * 0.2
        
        self.social_bonding_effect = bonding_base + quality_bonus
        return self.social_bonding_effect
    
    def execute_feast(self):
        """共食の実行"""
        total_nutrition = sum(res.get_effective_nutrition() for res in self.food_resources)
        nutrition_per_person = total_nutrition / len(self.participants)
        
        effects = []
        for participant in self.participants:
            # 栄養回復
            participant.hunger = max(0, participant.hunger - nutrition_per_person)
            
            # 社会的効果
            participant.social_satisfaction = getattr(participant, 'social_satisfaction', 0.0)
            participant.social_satisfaction += self.social_bonding_effect
            
            # SSD理論：共食による整合慣性の同期化
            if hasattr(participant, 'kappa'):
                participant.kappa['social_eating'] = min(1.0, 
                    participant.kappa.get('social_eating', 0.1) + 0.2)
            
            effects.append({
                'participant': participant.name,
                'nutrition_gained': nutrition_per_person,
                'social_effect': self.social_bonding_effect
            })
            
        return effects