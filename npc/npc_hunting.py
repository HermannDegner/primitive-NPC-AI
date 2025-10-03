"""
NPC Hunting Module - 狩猟システム（ソロ・グループ）
"""

import sys
import os
import random

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from systems.utils import probability_check, log_event


class NPCHuntingMixin:
    """NPC狩猟機能のミックスイン"""
    
    def execute_predictive_hunt(self, t):
        """予測的狩猟実行"""
        # 協力可能性を先に評価
        cooperation_potential = self.future_engine._assess_cooperation_potential()

        if cooperation_potential and self.organize_predictive_group_hunt(t):
            log_event(
                self.log, {"t": t, "name": self.name, "action": "predictive_group_hunt_organized"}
            )
        else:
            # ソロ狩猟
            if hasattr(self, "attempt_solo_hunt"):
                self.attempt_solo_hunt(t)
            else:
                self.seek_food(t)
            log_event(self.log, {"t": t, "name": self.name, "action": "predictive_solo_hunt"})

    def calculate_hunting_confidence(self):
        """狩りの自信レベルを計算（経験値統合）"""
        base_confidence = self.hunting_skill

        # SSD理論：経験による効率向上
        experience_boost = self.get_experience_efficiency("hunting") - 1.0
        base_confidence += experience_boost * 0.4

        # 従来の成功率による修正
        total_attempts = self.hunt_success_count + self.hunt_failure_count
        if total_attempts > 0:
            success_ratio = self.hunt_success_count / total_attempts
            base_confidence += (success_ratio - 0.5) * 0.3

        return max(0.1, min(0.9, base_confidence))

    def attempt_solo_hunt(self, t):
        """単独狩りの試行"""
        from config import HUNTING_SETTINGS, PREY_TYPES

        self.last_hunt_attempt = t
        print(f"  🏹 T{t}: HUNT ATTEMPT - {self.name} trying solo hunt...")

        # 疲労コスト（上限制御）
        hunt_cost = HUNTING_SETTINGS["hunt_fatigue_cost"]
        self.fatigue = min(150.0, self.fatigue + hunt_cost)

        # 成功判定
        confidence = self.calculate_hunting_confidence()
        base_rate = HUNTING_SETTINGS["solo_success_rate"]
        success_rate = base_rate + confidence * 0.2

        hunt_successful = probability_check(success_rate)

        if hunt_successful:
            # 狩り成功
            prey_type = "small_game"  # 単独では小動物のみ
            meat_amount = PREY_TYPES[prey_type]["meat_amount"]

            # 肉リソース獲得 - SSD Core Engine版
            if self.use_ssd_engine_social and self.ssd_enhanced_ref:
                meat_id = self.ssd_enhanced_ref.create_meat_resource_v2(meat_amount, self.name)
                self.meat_inventory.append(meat_id)
            else:
                # 従来版 - 値のみ追加
                self.meat_inventory.append(meat_amount)
            
            print(f"  🎯 T{t}: SOLO HUNT SUCCESS - {self.name} caught {prey_type}, gained {meat_amount} meat!")

            # 狩り経験の増加
            experience_gain = HUNTING_SETTINGS.get("experience_gain", 0.1)
            self.experience["hunting"] = min(10.0, self.experience["hunting"] + experience_gain)
            
            # 成功記録
            self.hunt_success_count += 1
            
            log_event(self.log, {
                "t": t,
                "name": self.name,
                "action": "solo_hunt_success",
                "prey_type": prey_type,
                "meat_gained": meat_amount,
                "confidence": confidence,
                "success_rate": success_rate
            })
            
            return True
        else:
            # 狩り失敗
            print(f"  ❌ T{t}: SOLO HUNT FAILED - {self.name} unsuccessful hunt")
            
            # 失敗記録
            self.hunt_failure_count += 1
            
            log_event(self.log, {
                "t": t,
                "name": self.name,
                "action": "solo_hunt_failure",
                "confidence": confidence,
                "success_rate": success_rate
            })
            
            return False

    def consider_hunting(self, t):
        """狩猟の検討"""
        # 基本的な狩猟判断
        if self.hunger < 30:
            return False  # 空腹でなければ狩猟しない
            
        if self.fatigue > 120:
            return False  # 疲労が激しい場合は狩猟しない
            
        # 狩猟場の知識をチェック
        if not self.knowledge_hunting:
            return "explore_hunt"  # 狩猟場を探索する必要がある
            
        # 自信レベルをチェック
        confidence = self.calculate_hunting_confidence()
        if confidence < 0.3:
            return "group_hunt"  # グループ狩猟を検討
            
        return "solo_hunt"  # ソロ狩猟を実行

    def manage_meat_inventory(self, t):
        """肉インベントリの管理"""
        if not self.meat_inventory:
            return
            
        # 肉の腐敗チェック（簡略化）
        fresh_meat = []
        for meat in self.meat_inventory:
            if isinstance(meat, (int, float)):
                fresh_meat.append(meat)  # 数値の場合はそのまま保持
            else:
                # SSD版の肉リソースの場合は別途処理
                fresh_meat.append(meat)
                
        self.meat_inventory = fresh_meat
        
        # 空腹時の自動消費
        if self.hunger > 60 and self.meat_inventory:
            self.consume_meat_if_hungry(t)

    def consume_meat_if_hungry(self, t):
        """空腹時の肉消費"""
        if not self.meat_inventory or self.hunger < 40:
            return False
            
        # 最初の肉を消費
        meat = self.meat_inventory.pop(0)
        
        if isinstance(meat, (int, float)):
            meat_value = meat
        else:
            # SSD版リソースの場合
            meat_value = 10  # デフォルト値
            
        # 空腹度回復
        old_hunger = self.hunger
        self.hunger = max(0, self.hunger - meat_value * 2)  # 肉は効率的
        
        print(f"🥩 T{t}: MEAT CONSUMED - {self.name} ate meat, hunger: {old_hunger:.1f} → {self.hunger:.1f}")
        
        log_event(self.log, {
            "t": t,
            "name": self.name,
            "action": "consume_meat",
            "meat_value": meat_value,
            "hunger_recovery": old_hunger - self.hunger
        })
        
        return True

    def organize_predictive_group_hunt(self, t):
        """予測的グループハンティングの組織（将来に備えた協力）"""
        if not self.roster:
            return False

        print(f"  🔮🤝 T{t}: PREDICTIVE GROUP HUNT - {self.name} organizing future-oriented cooperation...")
        
        # より広範囲で協力者を探す（予測的協力のため）
        cooperation_range = 60  # 通常より広い範囲
        
        all_npcs = [npc for npc in self.roster.values() if npc != self and npc.alive]
        print(f"    🔍 PREDICTIVE: Checking {len(all_npcs)} alive NPCs for future cooperation")

        potential_members = []
        for npc in all_npcs:
            distance = self.distance_to(npc.pos())
            print(f"      - {npc.name}: distance={distance:.1f}, hunt_group={npc.hunt_group}, fatigue={npc.fatigue:.1f}")

            # 予測的協力では条件を大幅緩和（生存のため）
            if (npc.hunt_group is None 
                and distance <= cooperation_range  # より広い範囲
                and npc.fatigue < 151):  # 疲労制限も緩和
                
                print(f"        ✅ ELIGIBLE for predictive group hunt")
                
                # 協力意欲を計算（未来志向）
                cooperation_desire = self._calculate_predictive_cooperation_desire(npc)
                potential_members.append((npc, cooperation_desire))
            else:
                print(f"        ❌ NOT ELIGIBLE for predictive cooperation")

        print(f"    👥 Found {len(potential_members)} potential members for predictive hunt (range: {cooperation_range}, fatigue<151)")

        # 最低2人（リーダー含めて3人）で予測グループ形成
        if len(potential_members) >= 1:
            print(f"    ✅ Enough members for predictive group hunt! Creating group...")
            
            # 協力意欲の高い順にソート
            potential_members.sort(key=lambda x: x[1], reverse=True)
            
            # グループ形成（最大5人まで）
            group_members = [self]
            for npc, desire in potential_members[:4]:  # 自分含めて最大5人
                group_members.append(npc)
                print(f"      ✅ {npc.name} joined predictive group hunt (desire: {desire:.2f})")
            
            # グループ名生成
            group_name = f"hunt_group_{self.name}_medium_game"
            
            # 全メンバーにグループ設定
            for member in group_members:
                member.hunt_group = group_name
                
            print(f"  🔮🎯 T{t}: PREDICTIVE GROUP FORMED - {self.name} organized future-oriented group with {len(group_members)} members: {[m.name for m in group_members]}")
            
            log_event(self.log, {
                "t": t,
                "name": self.name,
                "action": "predictive_group_hunt_organized",
                "group_size": len(group_members),
                "members": [m.name for m in group_members],
                "cooperation_type": "predictive"
            })
            
            return True
        else:
            print(f"    ❌ Not enough members for predictive group hunt")
            return False

    def _calculate_predictive_cooperation_desire(self, other_npc):
        """予測的協力の意欲計算"""
        base_desire = 0.8  # 予測的協力は基本的に高い意欲
        
        # 性格による補正
        sociability_bonus = other_npc.sociability * 0.3
        empathy_bonus = other_npc.empathy * 0.2
        
        # 経験による補正
        hunting_exp = other_npc.experience.get("hunting", 0.1)
        experience_bonus = hunting_exp * 0.1
        
        # 信頼関係による補正
        trust_bonus = 0
        if other_npc.name in self.trust_levels:
            trust_bonus = self.trust_levels[other_npc.name] * 0.2
            
        total_desire = base_desire + sociability_bonus + empathy_bonus + experience_bonus + trust_bonus
        return min(1.5, total_desire)  # 最大1.5（高い協力意欲）