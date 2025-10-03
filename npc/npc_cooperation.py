"""
NPC Cooperation Module - 協力と社交システム
"""

import sys
import os

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


class NPCCooperationMixin:
    """NPC協力機能のミックスイン"""
    
    def execute_predictive_cooperation(self, t):
        """予測的協力実行"""
        if self.organize_predictive_group_hunt(t):
            log_event(
                self.log, {"t": t, "name": self.name, "action": "predictive_cooperation_success"}
            )
        else:
            # 協力失敗時は次善策
            self.execute_predictive_hunt(t)

    def consider_cooperation_readiness(self):
        """協力活動への参加準備状況"""
        return (
            self.fatigue < 100
            and self.hunger > 25
            and len(
                [
                    npc
                    for npc in self.roster.values()
                    if npc.alive and self.distance_to(npc.pos()) <= 60
                ]
            )
            >= 1
        )

    def consider_future_cooperation(self, t):
        """将来の資源不足を予測した協力判断（予測的協力）"""

        # 現在の資源状況の分析
        if hasattr(self, "meat_inventory") and self.meat_inventory:
            if isinstance(self.meat_inventory, dict):
                current_meat = sum(self.meat_inventory.values())
            else:
                current_meat = (
                    sum(self.meat_inventory) if isinstance(self.meat_inventory, list) else 0
                )
        else:
            current_meat = 0
        predicted_survival_days = current_meat / 2.0 if current_meat > 0 else 0

        # 将来の困窮予測
        cooperation_urgency = 0.0

        # 肉の在庫が少ない場合の予測的協力
        if current_meat < 5.0:  # 2.5日分以下
            cooperation_urgency += 0.6

        # 飢餓の進行予測（現在の飢餓レベルから将来を予測）
        if self.hunger > 30:  # まだ余裕があるが将来を見据えて
            hunger_trend = (self.hunger - 20) / 60  # 0-1の範囲で正規化
            cooperation_urgency += hunger_trend * 0.4

        # 社会性の高いNPCは協力に積極的
        cooperation_urgency += self.sociability * 0.3

        # 過去の協力成功経験
        coop_success = self.experience.get("group_hunting", 0)
        cooperation_urgency += coop_success * 0.2

        # 環境のリスク予測（季節変化など）
        if hasattr(self.env, "seasonal_modifier"):
            seasonal_risk = 1.0 - self.env.seasonal_modifier.get("prey_availability", 1.0)
            cooperation_urgency += seasonal_risk * 0.3

        print(
            f"  🔮 T{t}: FUTURE COOPERATION - {self.name} predicts cooperation urgency: {cooperation_urgency:.2f}"
        )

        return cooperation_urgency > 0.4  # 予測的協力の閾値

    def consider_strategic_cooperation(self, t):
        """戦略的協力判断（まだ困っていないが将来に備える）"""

        strategic_value = 0.0

        # 経験レベルによる戦略思考
        experience_level = sum(self.experience.values()) / len(self.experience)
        if experience_level > 2.0:  # 経験豊富なNPCは戦略的
            strategic_value += 0.3

        # 個体性格による戦略性
        strategic_value += (self.curiosity + self.sociability) / 2 * 0.3

        # 環境の将来リスク評価
        if hasattr(self.env, "seasonal_modifier"):
            future_risk = self._assess_environmental_future_risk()
            strategic_value += future_risk * 0.4

        return strategic_value > 0.5

    def assess_cooperation_potential(self, other_npc, t):
        """他のNPCとの協力可能性評価"""
        cooperation_score = 0.0

        # 基本的な協力条件
        if not other_npc.alive or other_npc.fatigue > 120:
            return 0.0

        # 距離による協力可能性
        distance = self.distance_to(other_npc.pos())
        if distance > 50:
            distance_factor = 0.0
        else:
            distance_factor = (50 - distance) / 50
        cooperation_score += distance_factor * 0.3

        # 信頼関係
        trust_level = self.trust_levels.get(other_npc.name, 0.5)
        cooperation_score += trust_level * 0.4

        # 相互の社交性
        mutual_sociability = (self.sociability + other_npc.sociability) / 2
        cooperation_score += mutual_sociability * 0.3

        return min(1.0, cooperation_score)

    def integrate_social_network_into_boundary(self):
        """ソーシャルネットワークを境界システムに統合"""
        if not self.boundary_system:
            return

        # 信頼関係を境界として反映
        for other_name, trust_level in self.trust_levels.items():
            if trust_level > 0.3:  # 一定以上の信頼がある場合
                self.boundary_system.subjective_boundaries[self.name]["people"].add(other_name)
                self.boundary_system.boundary_strength[self.name][other_name] = trust_level * 0.6

        # ケア関係を境界として反映
        if self.caregiver:
            self.boundary_system.subjective_boundaries[self.name]["people"].add(self.caregiver.name)
            self.boundary_system.boundary_strength[self.name][self.caregiver.name] = 0.9
        if self.care_target:
            self.boundary_system.subjective_boundaries[self.name]["people"].add(self.care_target.name)
            self.boundary_system.boundary_strength[self.name][self.care_target.name] = 0.9

    def consider_meat_sharing(self, t):
        """肉の共有を検討"""
        if not self.meat_inventory or not self.roster:
            return False

        # 自分の肉の余剰をチェック
        current_meat = len(self.meat_inventory) if isinstance(self.meat_inventory, list) else sum(self.meat_inventory.values())
        
        if current_meat < 3:  # 3個未満は共有しない
            return False

        # 近くの飢えているNPCを探す
        hungry_npcs = []
        for other_name, other_npc in self.roster.items():
            if (other_name != self.name 
                and other_npc.alive 
                and other_npc.hunger > 80 
                and self.distance_to(other_npc.pos()) <= 20):
                
                trust_level = self.trust_levels.get(other_name, 0.5)
                if trust_level > 0.4:  # 一定の信頼が必要
                    hungry_npcs.append((other_npc, trust_level))

        if hungry_npcs:
            # 最も信頼できるNPCに肉を共有
            hungry_npcs.sort(key=lambda x: x[1], reverse=True)
            target_npc, trust = hungry_npcs[0]
            
            return self.attempt_resource_sharing(t, [target_npc])
            
        return False

    def attempt_resource_sharing(self, t, nearby_npcs):
        """資源共有の試行"""
        if not self.meat_inventory or not nearby_npcs:
            return False

        # 最も信頼できる飢えたNPCを選択
        best_target = None
        best_score = 0.0
        
        for target in nearby_npcs:
            if target.hunger > 70:  # 飢えている
                trust_score = self.trust_levels.get(target.name, 0.5)
                hunger_urgency = (target.hunger - 70) / 80.0  # 0-1の緊急度
                total_score = trust_score * 0.6 + hunger_urgency * 0.4
                
                if total_score > best_score:
                    best_score = total_score
                    best_target = target

        if best_target and best_score > 0.6:  # 共有の閾値
            # 肉を1つ共有
            if self.meat_inventory:
                shared_meat = self.meat_inventory.pop(0)
                meat_value = shared_meat if isinstance(shared_meat, (int, float)) else 10
                
                # 相手の空腹度を回復
                best_target.hunger = max(0, best_target.hunger - meat_value * 2)
                
                # 信頼関係向上
                self.trust_levels[best_target.name] = min(1.0, self.trust_levels.get(best_target.name, 0.5) + 0.1)
                best_target.trust_levels[self.name] = min(1.0, best_target.trust_levels.get(self.name, 0.5) + 0.1)
                
                log_event(self.log, {
                    "t": t,
                    "name": self.name,
                    "action": "resource_sharing",
                    "target": best_target.name,
                    "amount": meat_value
                })
                
                print(f"🤝 T{t}: RESOURCE SHARING - {self.name} shared meat with {best_target.name}")
                return True
                
        return False

    def update_trust(self, other_npc_name, event_type, t, emotional_context=None):
        """信頼関係の更新"""
        try:
            from config import TRUST_EVENTS
            trust_events = TRUST_EVENTS
        except ImportError:
            # フォールバック設定
            trust_events = {
                "successful_cooperation": {"base_trust": 0.7, "emotional_heat": 0.3},
                "failed_cooperation": {"base_trust": 0.3, "emotional_heat": -0.2},
                "resource_sharing": {"base_trust": 0.8, "emotional_heat": 0.4},
                "betrayal": {"base_trust": 0.1, "emotional_heat": -0.8}
            }
        
        if event_type not in trust_events:
            return
            
        event_config = trust_events[event_type]
        trust_change = event_config["base_trust"] - 0.5  # -0.5 ~ +0.5の範囲
        
        # 現在の信頼レベル
        current_trust = self.trust_levels.get(other_npc_name, 0.5)
        
        # 信頼変化を適用
        new_trust = max(0.0, min(1.0, current_trust + trust_change))
        self.trust_levels[other_npc_name] = new_trust
        
        # 履歴記録
        if other_npc_name not in self.trust_history:
            self.trust_history[other_npc_name] = []
            
        self.trust_history[other_npc_name].append({
            "t": t,
            "event": event_type,
            "trust_before": current_trust,
            "trust_after": new_trust,
            "emotional_heat": event_config.get("emotional_heat", 0.0)
        })
        
        log_event(self.log, {
            "t": t,
            "name": self.name,
            "action": "trust_update",
            "target": other_npc_name,
            "event": event_type,
            "trust_change": trust_change,
            "new_trust": new_trust
        })

    def _assess_environmental_future_risk(self):
        """環境の将来リスク評価"""
        risk_factor = 0.0
        
        # 季節変化リスク
        if hasattr(self.env, "seasonal_modifier"):
            seasonal_mod = self.env.seasonal_modifier
            # 捕食者活動増加
            if seasonal_mod.get("predator_activity", 1.0) > 1.2:
                risk_factor += 0.3
            # 資源減少
            if seasonal_mod.get("prey_activity", 1.0) < 0.8:
                risk_factor += 0.4
                
        return min(1.0, risk_factor)

    def provide_care(self, t):
        """看護行動"""
        if not self.care_target or not self.care_target.critically_injured:
            self.care_target = None
            return

        patient = self.care_target

        # 患者の近くに移動
        if self.distance_to(patient.pos()) > 1:
            self.move_towards(patient.pos())
            return

        # 食料分配
        if self.hunger < 80 and patient.hunger > 100:
            try:
                from config import CRITICAL_INJURY_SETTINGS
                food_sharing_rate = CRITICAL_INJURY_SETTINGS.get("food_sharing_rate", 0.5)
            except ImportError:
                food_sharing_rate = 0.5
                
            food_to_share = min(30, self.hunger * food_sharing_rate)
            if food_to_share > 0:
                self.hunger += food_to_share * 0.3  # 看護者も少し消費
                patient.hunger = max(0, patient.hunger - food_to_share)

                log_event(
                    self.log,
                    {
                        "t": t,
                        "name": self.name,
                        "action": "care_feed",
                        "patient": patient.name,
                        "amount": food_to_share,
                    },
                )

        # 肉の分配
        if hasattr(self, 'meat_inventory') and self.meat_inventory and patient.hunger > 80:
            if isinstance(self.meat_inventory, list) and self.meat_inventory:
                meat = self.meat_inventory[0]
                if hasattr(meat, 'amount'):
                    share_amount = min(meat.amount * 0.4, meat.amount)
                    if share_amount > 0:
                        shared = meat.share_with(patient.name, share_amount)
                        if hasattr(patient, 'receive_meat_gift'):
                            patient.receive_meat_gift(shared, self, t)

                        log_event(
                            self.log,
                            {
                                "t": t,
                                "name": self.name,
                                "action": "care_meat_share",
                                "patient": patient.name,
                                "amount": shared,
                            },
                        )

        # 洞窟への搬送
        if hasattr(self, "knowledge_caves") and self.knowledge_caves:
            known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
            if known_caves and patient.pos() not in known_caves.values():
                # 最寄りの安全な洞窟を探す
                nearest_cave = min(known_caves.values(), key=lambda cave: self.distance_to(cave))

                # 患者を洞窟に連れて行く
                if patient.pos() != nearest_cave:
                    # 患者を洞窟方向に移動させる
                    dx = (
                        1
                        if nearest_cave[0] > patient.x
                        else -1 if nearest_cave[0] < patient.x else 0
                    )
                    dy = (
                        1
                        if nearest_cave[1] > patient.y
                        else -1 if nearest_cave[1] < patient.y else 0
                    )

                    if dx != 0 or dy != 0:
                        patient.x = max(0, min(self.env.size - 1, patient.x + dx))
                        patient.y = max(0, min(self.env.size - 1, patient.y + dy))

                        log_event(
                            self.log,
                            {
                                "t": t,
                                "name": self.name,
                                "action": "transport_patient",
                                "patient": patient.name,
                                "destination": nearest_cave,
                            },
                        )

        # SSD理論：看護による社会的結束（一時的共感ブースト込み）
        effective_empathy = self.get_effective_empathy() if hasattr(self, 'get_effective_empathy') else self.empathy
        social_bonding = effective_empathy * 0.25
        if hasattr(self, 'E'):
            self.E = max(0.0, self.E - social_bonding)

        # 看護疲労（上限制御）
        self.fatigue = min(150.0, self.fatigue + 2)

        # SSD理論：看護経験の獲得
        try:
            from config import EXPERIENCE_SYSTEM_SETTINGS
            care_exp_rate = EXPERIENCE_SYSTEM_SETTINGS.get("care_exp_rate", 0.1)
        except ImportError:
            care_exp_rate = 0.1
            
        self.gain_experience("care", care_exp_rate, t)