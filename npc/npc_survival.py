"""
NPC Survival Module - 生存行動（水、食べ物、休息）
"""

import sys
import os

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from systems.utils import probability_check, log_event


class NPCSurvivalMixin:
    """NPC生存機能のミックスイン"""
    
    def seek_water(self, t):
        """水分補給行動（季節統合版 + 洞窟雨水）"""
        print(f"💧 T{t}: WATER ATTEMPT - {self.name} thirst: {self.thirst:.1f}")

        # 1. 洞窟雨水を優先チェック（近い洞窟から）
        if self._try_drink_cave_water(t):
            return

        # 2. 通常の水源を探す
        known_water = {k: v for k, v in self.env.water_sources.items() if k in self.knowledge_water}
        if known_water:
            nearest_water = self.env.nearest_nodes(self.pos(), known_water, k=1)
            if nearest_water:
                target = nearest_water[0]
                if self.pos() == target:
                    # capture pre-state
                    pre_thirst = float(self.thirst)
                    old_thirst = self.thirst
                    # 季節によって回復量を調整
                    recovery_amount = 35
                    if hasattr(self.env, "seasonal_modifier"):
                        temp_stress = self.env.seasonal_modifier.get("temperature_stress", 0.0)
                        recovery_amount = max(30, 35 - (temp_stress * 10))  # 高温時は回復量減少

                    self.thirst = max(0, self.thirst - recovery_amount)
                    post_thirst = float(self.thirst)
                    print(
                        f"🚰 T{t}: WATER CONSUMED - {self.name} drank water, thirst: {old_thirst:.1f} → {self.thirst:.1f}"
                    )
                    result = {
                        "t": t,
                        "name": self.name,
                        "action": "drink",
                        "recovery": recovery_amount,
                        "actual_recovery": recovery_amount,
                        "pre_thirst": pre_thirst,
                        "post_thirst": post_thirst,
                    }
                    log_event(self.log, result)
                    # Save last action result for integration handlers
                    self.last_action_result = result
                    return result
                else:
                    self.move_towards(target)
        else:
            # 水源不明時はより積極的に探索 - 渇きレベルに応じて強化
            if self.thirst > 120:  # 深刻な渇き時
                self.exploration_mode = True
                self.exploration_intensity = min(2.0, self.thirst / 100.0)
            self.explore_for_resource(t, "water")
            # 緊急時は他のNPCの知識も参照
            if self.thirst > 100:
                self._request_water_location_info(t)

    def _request_water_location_info(self, t):
        """緊急時の水源情報共有"""
        if not self.roster:
            return

        for other_name, other_npc in self.roster.items():
            if other_name != self.name and other_npc.alive:
                # 近くのNPCから水源情報を取得
                if self.distance_to(other_npc.pos()) < 20 and other_npc.knowledge_water:
                    shared_water = list(other_npc.knowledge_water)[:1]  # 1つだけ共有
                    for water_pos in shared_water:
                        if water_pos not in self.knowledge_water:
                            self.knowledge_water.add(water_pos)
                            print(f"💡 T{t}: {other_name} shared water location with {self.name}")
                            break

    def _try_drink_cave_water(self, t):
        """洞窟雨水を飲む試み"""
        if not hasattr(self.env, "cave_water_storage"):
            return False

        # 現在位置の洞窟をチェック
        current_pos = self.pos()
        for cave_id, cave_pos in self.env.caves.items():
            if current_pos == cave_pos:
                # 洞窟の水情報を取得
                water_info = self.env.get_cave_water_info(cave_id)
                if water_info and water_info["water_amount"] > 0:
                    old_thirst = self.thirst
                    recovery_amount = min(60, water_info["water_amount"])  # 35→60に増量

                    # 季節によって回復量を調整（大幅緩和）
                    if hasattr(self.env, "seasonal_modifier"):
                        temp_stress = self.env.seasonal_modifier.get("temperature_stress", 0.0)
                        recovery_amount = max(50, recovery_amount - (temp_stress * 2))  # 20→50、5→2に緩和

                    # 洞窟の水を飲む
                    actual_recovery = self.env.drink_cave_water(cave_id, self.name, recovery_amount)
                    if actual_recovery > 0:
                        # capture pre/post
                        pre_thirst = float(self.thirst)
                        self.thirst = max(0, self.thirst - actual_recovery)
                        post_thirst = float(self.thirst)
                        result = {
                            "t": t,
                            "name": self.name,
                            "action": "drink_cave_water",
                            "cave_id": cave_id,
                            "recovery": actual_recovery,
                            "actual_recovery": actual_recovery,
                            "pre_thirst": pre_thirst,
                            "post_thirst": post_thirst,
                        }
                        log_event(self.log, result)
                        self.last_action_result = result
                        
                        # 経験学習記録: 水分補給成功
                        if hasattr(self, 'record_survival_experience'):
                            context = {
                                "recovery_amount": actual_recovery,
                                "cave_id": cave_id,
                                "initial_thirst": pre_thirst
                            }
                            self.record_survival_experience("water", True, context)
                        
                        return result

        # 近くの水のある洞窟を探す
        water_found = self._seek_nearby_cave_with_water(t)
        
        # 水分補給失敗時の経験学習記録
        if not water_found and hasattr(self, 'record_survival_experience'):
            context = {
                "reason": "no_accessible_water",
                "current_thirst": getattr(self, 'thirst', 0)
            }
            self.record_survival_experience("water", False, context)
        
        return water_found

    def _seek_nearby_cave_with_water(self, t):
        """近くの水のある洞窟を探す"""
        if not hasattr(self.env, "cave_water_storage"):
            return False

        caves_with_water = []
        for cave_id, cave_pos in self.env.caves.items():
            water_info = self.env.get_cave_water_info(cave_id)
            if water_info and water_info["water_amount"] > 5:  # 5以上の水がある洞窟
                distance = ((self.x - cave_pos[0]) ** 2 + (self.y - cave_pos[1]) ** 2) ** 0.5
                caves_with_water.append((cave_id, cave_pos, distance, water_info["water_amount"]))

        if caves_with_water:
            # 最も近い水のある洞窟に移動
            caves_with_water.sort(key=lambda x: x[2])  # 距離でソート
            target_cave_id, target_pos, distance, water_amount = caves_with_water[0]

            if distance <= 15:  # 15マス以内の洞窟のみ対象
                print(
                    f"🏞️💧 T{t}: {self.name} seeking cave water at {target_cave_id} {target_pos} (water: {water_amount:.1f})"
                )
                self.move_towards(target_pos)
                return True

        return False

    def seek_food(self, t):
        """食料探索行動"""
        print(f"🍎 T{t}: FOOD ATTEMPT - {self.name} hunger: {self.hunger:.1f}")
        
        known_berries = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
        print(f"🍎 T{t}: {self.name} knows {len(known_berries)}/{len(self.env.berries)} berries")
        
        if known_berries:
            nearest_berries = self.env.nearest_nodes(self.pos(), known_berries, k=1)
            if nearest_berries:
                target = nearest_berries[0]
                if self.pos() == target:
                    success_rate = 0.8
                    if probability_check(success_rate):
                        old_hunger = self.hunger
                        self.hunger = max(0, self.hunger - 40)
                        print(f"🍎🍽️ T{t}: {self.name} foraged! hunger: {old_hunger:.1f} → {self.hunger:.1f}")
                        log_event(
                            self.log,
                            {"t": t, "name": self.name, "action": "forage", "recovery": 40},
                        )
                    else:
                        print(f"🍎❌ T{t}: {self.name} failed to forage (success rate: {success_rate})")
                else:
                    print(f"🍎🚶 T{t}: {self.name} moving towards berries at {target}")
                    self.move_towards(target)
        else:
            print(f"🍎🔍 T{t}: {self.name} exploring for food (no known berries)")
            self.explore_for_resource(t, "food")

    def seek_rest(self, t):
        """休息行動"""
        known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}

        # 予測的休憩判断
        should_rest, rest_type = self.consider_predictive_rest(t)

        # デバッグログ追加
        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": "seek_rest_attempt",
                "fatigue": self.fatigue,
                "known_caves": len(known_caves),
                "pos": self.pos(),
                "rest_type": rest_type,
            },
        )

        if known_caves:
            nearest_cave = self.env.nearest_nodes(self.pos(), known_caves, k=1)
            if nearest_cave:
                target = nearest_cave[0]
                if self.pos() == target:
                    # 洞窟で休息
                    safety_feeling = self.calculate_cave_safety_feeling(target)
                    
                    # より効果的な休憩（安全度に応じて）
                    rest_effectiveness = 0.6 + (safety_feeling * 0.4)  # 0.6~1.0の効果
                    fatigue_reduction = 25 * rest_effectiveness
                    
                    old_fatigue = self.fatigue
                    self.fatigue = max(0, self.fatigue - fatigue_reduction)
                    
                    print(f"😴 T{t}: REST COMPLETED - {self.name} rested in cave, fatigue: {old_fatigue:.1f} → {self.fatigue:.1f}")
                    
                    result = {
                        "t": t,
                        "name": self.name,
                        "action": "rest_cave",
                        "location": target,
                        "recovery": fatigue_reduction,
                        "safety_feeling": safety_feeling,
                        "rest_type": rest_type,
                        "pre_fatigue": old_fatigue,
                        "post_fatigue": self.fatigue,
                    }
                    log_event(self.log, result)
                    self.last_action_result = result

                    # 縄張り主張の判定（十分安全と感じる場合）
                    has_territory = (self.use_ssd_engine_social and self.territory_id) or (not self.use_ssd_engine_social and self.territory)
                    if safety_feeling >= self.territory_claim_threshold and not has_territory:
                        try:
                            self.claim_cave_territory(target, t, safety_feeling)
                        except Exception as e:
                            print(f"Territory claim failed: {e}")

                    return result
                else:
                    self.move_towards(target)
        else:
            # 洞窟知識がない場合は探索
            self.explore_for_resource(t, "shelter")

    def consider_predictive_rest(self, t):
        """未来予測的な休憩判断"""
        # 現在の疲労と活動予測に基づく休憩判断
        current_fatigue = self.fatigue

        # 未来の疲労予測（今後の行動コストを考慮）
        predicted_activities = self.predict_next_activities()
        predicted_fatigue_cost = sum(activity["cost"] for activity in predicted_activities)
        future_fatigue = current_fatigue + predicted_fatigue_cost

        # 洞窟までの距離による移動コスト
        known_caves = {k: v for k, v in self.env.caves.items() if k in self.knowledge_caves}
        if known_caves:
            nearest_cave = min(known_caves.values(), key=lambda pos: self.distance_to(pos))
            travel_cost = self.distance_to(nearest_cave) * 1.5  # 移動疲労係数
        else:
            travel_cost = 20  # 洞窟探索コスト

        # 予測的休憩条件
        rest_threshold = 50  # より早い段階で休憩を検討
        emergency_threshold = 100  # 緊急休憩レベル

        # 予測疲労が危険レベルに達する場合、予防的休憩
        if future_fatigue + travel_cost > emergency_threshold:
            return True, "preventive"
        # 現在疲労が中程度で、今後の活動で危険になる場合
        elif current_fatigue > rest_threshold and future_fatigue > 80:
            return True, "strategic"
        # 緊急時（従来の反応的休憩）
        elif current_fatigue > 70:
            return True, "reactive"

        return False, "none"

    def predict_next_activities(self):
        """今後の活動とそのコストを予測"""
        activities = []

        # 空腹状態に基づく狩猟予測
        if self.hunger > 40:
            activities.append({"action": "hunt", "cost": 25})
        elif self.hunger > 20:
            activities.append({"action": "forage", "cost": 15})

        # 喉の渇きに基づく水探し予測
        if self.thirst > 30:
            activities.append({"action": "seek_water", "cost": 10})

        # 探索モードの予測
        if self.exploration_mode:
            activities.append({"action": "explore", "cost": 12})

        # 協力活動の予測
        if hasattr(self, 'consider_cooperation_readiness') and self.consider_cooperation_readiness():
            activities.append({"action": "cooperation", "cost": 20})

        return activities

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