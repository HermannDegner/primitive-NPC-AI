"""
NPC Territory Module - 縄張りと安全システム
"""

import sys
import os
import csv

# 親ディレクトリをパスに追加
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from systems.utils import log_event
except ImportError:
    # フォールバック実装
    def log_event(log_dict, event_data):
        print(f"LOG: {event_data}")


class NPCTerritoryMixin:
    """NPC縄張り機能のミックスイン"""
    
    def calculate_cave_safety_feeling(self, cave_pos):
        """洞窟への安全感計算"""
        # 1. 物理的安全感
        intrinsic_safety = 0.7  # 洞窟の基本安全性

        # 2. 体験に基づく安全感
        cave_name = next((k for k, v in self.env.caves.items() if v == cave_pos), None)
        safety_events = 0
        if cave_name:
            for log_entry in self.log:
                if log_entry.get("location") == cave_pos and log_entry.get("action") in [
                    "rest_in_cave",
                    "safe_shelter",
                ]:
                    safety_events += 1

        experiential_safety = min(1.0, safety_events / 3.0)

        # 3. 社会的安全感
        social_safety = self.calculate_social_safety_at_location(cave_pos)

        # 4. オキシトシン的縄張り効果
        oxytocin_effect = self.calculate_oxytocin_territory_effect(cave_pos)

        # 総合安全感
        total_safety_feeling = (
            intrinsic_safety * 0.15
            + experiential_safety * 0.4
            + social_safety * 0.25
            + oxytocin_effect * 0.2
        )

        return min(1.0, total_safety_feeling)

    def calculate_social_safety_at_location(self, location):
        """特定場所での社会的安全感"""
        nearby_npcs = [
            npc
            for npc in self.roster.values()
            if npc != self and npc.alive and npc.distance_to(location) <= 5
        ]

        if not nearby_npcs:
            return 0.0

        # 仲間の数による安心感
        group_safety = min(0.8, len(nearby_npcs) * 0.2)

        return group_safety * self.sociability

    def calculate_oxytocin_territory_effect(self, location):
        """オキシトシン的縄張り効果（場所＋人の統合的安全感）"""
        oxytocin_effect = 0.0

        # 1. 縄張りメンバーシップによる安心感
        if (hasattr(self, 'use_ssd_engine_social') and self.use_ssd_engine_social 
            and hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref 
            and hasattr(self, 'territory_id') and self.territory_id):
            # SSD Core Engine版
            if self.ssd_enhanced_ref.check_territory_contains_v2(self.territory_id, location):
                oxytocin_effect += 0.3
        elif hasattr(self, 'territory') and self.territory and self.territory.contains(location):
            # 従来版
            oxytocin_effect += 0.3

        # 2. 仲間の結束による安心感
        territory_members = 0
        if (hasattr(self, 'use_ssd_engine_social') and self.use_ssd_engine_social 
            and hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref):
            # SSD Core Engine版 - 縄張りメンバーを取得
            for npc in self.roster.values():
                if (npc != self and npc.alive and 
                    hasattr(npc, "territory_id") and npc.territory_id and
                    self.ssd_enhanced_ref.check_territory_contains_v2(npc.territory_id, location)):
                    territory_members += 1
        else:
            # 従来版は無効化
            territory_members = 0

        bonding_effect = min(0.4, territory_members * 0.15)
        oxytocin_effect += bonding_effect

        # 3. 保護本能による安心感強化
        protection_instinct = getattr(self, 'empathy', 0.5) * 0.5
        oxytocin_effect += min(0.4, protection_instinct)

        # 4. 安心感の相互強化（基本的な縄張り一致による信頼感）
        collective_confidence = 0.0
        for npc in self.roster.values():
            if (
                npc != self
                and npc.alive
                and hasattr(npc, "territory")
                and npc.territory
                and npc.territory.center == location
            ):
                collective_confidence += 0.1

        oxytocin_effect += min(0.3, collective_confidence)

        return min(1.0, oxytocin_effect)

    def claim_cave_territory(self, cave_pos, t, safety_feeling=None):
        """洞窟縄張りの設定"""
        # Territory radius設定
        try:
            from config import TERRITORY_RADIUS
            territory_radius = TERRITORY_RADIUS
        except ImportError:
            territory_radius = 5  # デフォルト値
            
        # SSD Core Engine版の社会システム使用
        if (hasattr(self, 'use_ssd_engine_social') and self.use_ssd_engine_social 
            and hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref 
            and hasattr(self, 'territory_id') and self.territory_id is None):
            
            self.territory_id = self.ssd_enhanced_ref.create_territory_v2(cave_pos, territory_radius, self.name)
            
            # 近くの仲間を招待（SSD版）
            self.invite_nearby_to_territory_v2(t)
            
        # 従来バージョン - SSDエンジンでない場合は縄張り機能なし
        else:
            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "WARNING_territory_claim_disabled",
                    "reason": "SSD_Engine_not_available"
                }
            )

        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": "establish_territory",
                "location": cave_pos,
                "radius": territory_radius,
                "safety_feeling": safety_feeling,
            },
        )

        # CSV ログ記録
        self._log_territory_event(t, cave_pos, territory_radius, safety_feeling)

    def invite_nearby_to_territory_v2(self, t):
        """縄張りへの招待（SSD Core Engine版）"""
        if (not hasattr(self, 'territory_id') or not self.territory_id 
            or not hasattr(self, 'ssd_enhanced_ref') or not self.ssd_enhanced_ref):
            return

        nearby_npcs = [
            npc
            for npc in self.roster.values()
            if npc != self
            and npc.alive
            and hasattr(npc, 'territory_id') and npc.territory_id is None
            and self.distance_to(npc.pos()) <= 12
        ]

        # 信頼関係と社交性に基づく招待
        for npc in nearby_npcs:
            trust_level = getattr(self, 'trust_levels', {}).get(npc.name, 0.5)
            mutual_sociability = (getattr(self, 'sociability', 0.5) + getattr(npc, 'sociability', 0.5)) / 2
            
            invitation_score = trust_level * 0.6 + mutual_sociability * 0.4
            
            if invitation_score > 0.5:  # 招待の閾値
                # SSDシステムを使用して縄張りに招待
                success = self.ssd_enhanced_ref.invite_to_territory_v2(self.territory_id, npc.name)
                if success:
                    npc.territory_id = self.territory_id
                    
                    log_event(
                        self.log,
                        {
                            "t": t,
                            "name": self.name,
                            "action": "territory_invitation",
                            "target": npc.name,
                            "territory_id": self.territory_id,
                            "invitation_score": invitation_score
                        },
                    )

    def check_territory_safety(self, location):
        """縄張りの安全性チェック"""
        if not hasattr(self, 'territory_id') or not self.territory_id:
            return 0.5  # 縄張りなしの場合は中程度の安全性
            
        # SSDシステムでの縄張り内チェック
        if (hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref and
            self.ssd_enhanced_ref.check_territory_contains_v2(self.territory_id, location)):
            
            # 縄張り内での安全性計算
            base_safety = 0.8  # 縄張り内基本安全性
            
            # 縄張りメンバー数による安全性向上
            member_count = len(self.get_territory_members()) - 1  # 自分を除く
            member_bonus = min(0.2, member_count * 0.05)
            return min(1.0, base_safety + member_bonus)
            
        return 0.3  # 縄張り外は低い安全性

    def get_territory_members(self):
        """縄張りメンバーの取得"""
        if not hasattr(self, 'territory_id') or not self.territory_id:
            return [self]
            
        members = []
        for npc in self.roster.values():
            if (npc.alive and hasattr(npc, 'territory_id') and npc.territory_id == self.territory_id):
                members.append(npc)
                
        return members

    def _log_territory_event(self, t, cave_pos, territory_radius, safety_feeling):
        """縄張りイベントのCSVログ記録"""
        try:
            events_path = os.path.join(
                os.path.dirname(__file__), "logs", "territory_events.csv"
            )
            os.makedirs(os.path.dirname(events_path), exist_ok=True)
            header_needed = not os.path.exists(events_path)
            with open(events_path, "a", newline="", encoding="utf-8") as ef:
                writer = csv.writer(ef)
                if header_needed:
                    writer.writerow(
                        ["t", "npc", "action", "location", "radius", "safety_feeling"]
                    )
                writer.writerow(
                    [
                        t,
                        self.name,
                        "establish_territory",
                        str(cave_pos),
                        territory_radius,
                        safety_feeling,
                    ]
                )
        except Exception:
            # ログ失敗は致命的ではないので無視
            pass