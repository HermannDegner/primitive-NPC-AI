"""
SSD Village Simulation - NPC Agent
構造主観力学(SSD)理論に基づく原始村落シミュレーション - NPCエージェント
"""

import random
import math
from collections import defaultdict

from config import (
    DEFAULT_KAPPA,
    DEFAULT_TEMPERATURE,
    TERRITORY_RADIUS,
    THIRST_DANGER_THRESHOLD,
    HUNGER_DANGER_THRESHOLD,
    EXPERIENCE_SYSTEM_SETTINGS,
    CRITICAL_INJURY_SETTINGS,
    TRUST_EVENTS,
    TRUST_SYSTEM_SETTINGS,
    PREDATOR_AWARENESS_SETTINGS,
    PREDATOR_HUNTING,
)
# from social import Territory  # Replaced by SSD Social Layer
from future_prediction import FuturePredictionEngine
from utils import distance_between
from utils import probability_check
from utils import log_event


class NPC:
    """SSD理論に基づくNPCエージェント"""

    def __init__(self, name, preset, env, roster, start_pos, boundary_system=None):
        self.name = name
        self.env = env
        self.roster = roster
        self.x, self.y = start_pos
        self.boundary_system = boundary_system

        # 基本状態
        self.hunger = 20.0
        self.thirst = 10.0
        self.fatigue = 20.0
        self.alive = True
        self.log = []

        # 性格特性（SSD理論）
        self.curiosity = preset.get("curiosity", 0.5)
        self.sociability = preset.get("sociability", 0.5)
        self.risk_tolerance = preset.get("risk_tolerance", 0.5)
        self.empathy = preset.get("empathy", 0.6)

        # SSD理論パラメータ
        self.kappa = defaultdict(lambda: DEFAULT_KAPPA)  # 整合慣性
        self.E = 0.0  # 未処理圧
        self.T = DEFAULT_TEMPERATURE  # 温度パラメータ
        self.T0 = DEFAULT_TEMPERATURE

        # 探索モード（SSD理論の跳躍メカニズム）
        self.exploration_mode = False
        self.exploration_mode_start_tick = 0
        self.exploration_intensity = 1.0
        
        # SSD Core Engine版の探索機能（デフォルト有効）
        self.use_ssd_engine_exploration = True  # 新版使用フラグ
        self.ssd_enhanced_ref = None  # SSDEnhancedNPCへの参照
        
        # SSD Core Engine版の社会システム
        self.use_ssd_engine_social = True  # 社会システム新版フラグ
        self.territory_id = None  # SSD版縄張りID

        # 未来予測エンジンの初期化
        self.future_engine = FuturePredictionEngine(self)

        # 知識と記憶
        self.knowledge_caves = set()
        self.knowledge_water = set()
        self.knowledge_berries = set()
        self.knowledge_hunting = set()

        # 洞窟雨水システム関連
        self.last_cave_water_check = 0  # 最後に洞窟水をチェックした時刻

        # 縄張りとコミュニティ
        self.territory = None
        self.territory_claim_threshold = 0.8

        # 狩りシステム
        self.hunting_skill = preset.get("risk_tolerance", 0.5) * 0.7 + random.random() * 0.3
        self.hunting_experience = 0.0
        self.hunt_group = None  # 参加している狩りグループ
        self.meat_inventory = []  # 所有している肉リソース
        self.last_hunt_attempt = 0
        self.hunt_success_count = 0
        self.hunt_failure_count = 0

        # 重症システム関連属性
        self.critically_injured = False
        self.injury_recovery_time = 0
        self.injury_start_tick = 0
        self.caregiver = None  # 看護してくれる仲間
        self.care_target = None  # 看護している相手
        self.temporary_empathy_boost = 0.0  # 重症者目撃による一時的共感増加
        self.witnessed_injuries = set()  # 目撃した重症者のリスト（重複防止）

        # 信頼関係システム
        self.trust_levels = {}  # 他のNPCに対する信頼度 {npc_name: trust_value}
        self.trust_history = {}  # 信頼関係の履歴 {npc_name: [events...]}
        self.last_interaction = {}  # 最後の直接インタラクション {npc_name: tick}

        # SSD理論統合型経験システム（整合慣性κとして機能）
        self.experience = {
            "hunting": 0.1,  # 狩り経験（初期値）
            "exploration": 0.1,  # 探索経験
            "survival": 0.1,  # 野宿・生存経験
            "care": 0.1,  # 看護・治療経験
            "social": 0.1,  # 社交・協力経験
            "predator_awareness": 0.1,  # 捕食者警戒経験
            "crisis_learning": 0.1,  # 危機的状況での学習経験
        }
        self.last_experience_update = 0  # 最後の経験値更新時刻
        # 縄張りの内側度（I_X）: {object_id: I_value}
        self.I_by_target = defaultdict(lambda: 0.1)
        # 捕食者警戒状態
        self.predator_alert_time = 0  # 警戒状態の残り時間
        self.known_predator_location = None  # 既知の捕食者位置
        self.predator_encounters = 0  # 捕食者遭遇回数
        self.predator_escapes = 0  # 捕食者からの逃走成功回数

        # 危機的状況での学習システム
        self.crisis_learning = {
            "trusted_water_sources": set(),  # 信頼できる水場
            "trusted_hunting_grounds": set(),  # 信頼できる狩場
            "trusted_foraging_spots": set(),  # 信頼できる採取場
            "crisis_behaviors": {
                "caution_level": 0.1,  # 慎重さレベル
                "risk_aversion": 0.1,  # リスク回避度
                "resource_prioritization": {
                    "water": 0.1,  # 水場の優先度
                    "hunting": 0.1,  # 狩場の優先度
                    "foraging": 0.1,  # 採取場の優先度
                },
            },
            "crisis_experiences": [],  # 危機的経験の履歴
        }

        # 基本パラメータ
        self.age = random.randint(20, 40)
        self.experience_points = 0.0
        self.lifetime_discoveries = 0

        # 危機レベルの初期化
        self.life_crisis = 0.0

        # 初期知識の設定
        self._initialize_knowledge()

    def _initialize_knowledge(self):
        """初期知識の設定"""
        # 近くのリソースを初期知識として追加
        initial_cave = self.env.nearest_nodes(self.pos(), self.env.caves, k=1)
        if initial_cave:
            cave_name = next(k for k, v in self.env.caves.items() if v == initial_cave[0])
            self.knowledge_caves.add(cave_name)

        initial_waters = self.env.nearest_nodes(self.pos(), self.env.water_sources, k=2)
        for water_pos in initial_waters:
            water_name = next(k for k, v in self.env.water_sources.items() if v == water_pos)
            self.knowledge_water.add(water_name)

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

    def pos(self):
        """現在位置を取得"""
        return (self.x, self.y)

    def update_I_for_target(self, target_id, r_val=0.0, m_val=0.0, tick=None):
        """対象に対する内側度 I を更新する。

        I(t+1) = (1-λ) * I(t) + η_r * r_val + η_m * m_val
        Returns (I_before, I_after, delta)
        """
        from config import TERRITORY_SETTINGS

        current = self.I_by_target.get(target_id, 0.1)
        I_before = current
        lam = TERRITORY_SETTINGS.get("forget_rate", 0.01)
        eta_r = TERRITORY_SETTINGS.get("eta_r", 0.1)
        eta_m = TERRITORY_SETTINGS.get("eta_m", 0.05)

        new_I = (1 - lam) * current + eta_r * r_val + eta_m * m_val
        new_I = max(
            TERRITORY_SETTINGS.get("min_I", 0.0), min(TERRITORY_SETTINGS.get("max_I", 1.0), new_I)
        )
        self.I_by_target[target_id] = new_I
        return I_before, new_I, new_I - I_before

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

    def seek_group_protection(self, t):
        """集団防御の追求"""
        threat_level, nearby_predators = self.assess_predator_threat()

        if threat_level > 0.3:
            # 近くの仲間を探す
            nearby_npcs = [
                npc
                for npc in self.roster.values()
                if npc != self and npc.alive and self.distance_to(npc.pos()) <= 15
            ]

            if nearby_npcs:
                # 最も近い仲間のところに向かう
                closest_ally = min(nearby_npcs, key=lambda n: self.distance_to(n.pos()))
                self.move_towards(closest_ally.pos())

                log_event(
                    self.log,
                    {
                        "t": t,
                        "name": self.name,
                        "action": "group_protection",
                        "threat_level": threat_level,
                        "ally": closest_ally.name,
                    },
                )
                return True

        return False

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
        if self.use_ssd_engine_social and self.ssd_enhanced_ref and self.territory_id:
            # SSD Core Engine版
            if self.ssd_enhanced_ref.check_territory_contains_v2(self.territory_id, location):
                oxytocin_effect += 0.3
        elif self.territory and self.territory.contains(location):
            # 従来版
            oxytocin_effect += 0.3

        # 2. 仲間の結束による安心感
        territory_members = 0
        if self.use_ssd_engine_social and self.ssd_enhanced_ref:
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
        protection_instinct = self.empathy * 0.5
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
        """洞窟縄張りの設定

        safety_feeling: optional float value (0..1) passed from caller for diagnostics/logging
        """
        # SSD Core Engine版の社会システム使用
        if self.use_ssd_engine_social and self.ssd_enhanced_ref and self.territory_id is None:
            self.territory_id = self.ssd_enhanced_ref.create_territory_v2(cave_pos, TERRITORY_RADIUS, self.name)
            
            # 近くの仲間を招待（SSD版）
            self.invite_nearby_to_territory_v2(t)
            
        # 従来バージョン - SSDエンジンでない場合は縄張り機能なし
        else:
            log_event(
                "WARNING",
                f"{self.name}: Territory claim disabled - SSD Engine not available",
                t,
                npc_name=self.name
            )

            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "establish_territory",
                    "location": cave_pos,
                    "radius": TERRITORY_RADIUS,
                    "safety_feeling": safety_feeling,
                },
            )

            # 境界システム統合 - SSDエンジンでは無効化
            # if self.boundary_system and not self.use_ssd_engine_social:
            #     self.boundary_system.integrate_territory_as_boundary(self, self.territory)
            try:
                import os, csv

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
                            TERRITORY_RADIUS,
                            safety_feeling,
                        ]
                    )
            except Exception:
                # ログ失敗は致命的ではないので無視
                pass

    # invite_nearby_to_territory - Removed (replaced by SSD Social Layer)
    
    def invite_nearby_to_territory_v2(self, t):
        """縄張りへの招待（SSD Core Engine版）"""
        if not self.territory_id or not self.ssd_enhanced_ref:
            return

        nearby_npcs = [
            npc
            for npc in self.roster.values()
            if npc != self
            and npc.alive
            and npc.territory_id is None  # SSD版フィールドをチェック
            and self.distance_to(npc.pos()) <= 12
        ]

        for npc in nearby_npcs:
            if probability_check(0.7):  # 70%の確率で招待
                if probability_check(0.2):  # 20%の確率で受諾
                    # SSD版では同じ縄張りIDを共有
                    npc.territory_id = self.territory_id
                    
                    # ログ記録
                    log_event(
                        self.log,
                        {
                            "t": t,
                            "name": self.name,
                            "action": "invite_to_territory_v2",
                            "invitee": npc.name,
                            "accepted": True,
                            "territory_id": self.territory_id,
                        },
                    )

    def emergency_survival_action(self, t, life_crisis):
        """命の危機時の緊急行動"""
        if self.thirst > THIRST_DANGER_THRESHOLD:
            print(f"🚨💧 T{t}: EMERGENCY WATER NEEDED - {self.name} thirst: {self.thirst:.1f}")
            known_water = {
                k: v for k, v in self.env.water_sources.items() if k in self.knowledge_water
            }
            if known_water:
                nearest_water = self.env.nearest_nodes(self.pos(), known_water, k=1)
                if nearest_water:
                    target = nearest_water[0]
                    if self.pos() == target:
                        pre_thirst = float(self.thirst)
                        old_thirst = self.thirst
                        self.thirst = max(0, self.thirst - 45)
                        post_thirst = float(self.thirst)
                        print(
                            f"🚑💧 T{t}: EMERGENCY WATER CONSUMED - {self.name} emergency drink, thirst: {old_thirst:.1f} → {self.thirst:.1f}"
                        )
                        log_event(
                            self.log,
                            {
                                "t": t,
                                "name": self.name,
                                "action": "emergency_drink",
                                "recovery": 45,
                                "life_crisis": life_crisis,
                                "pre_thirst": pre_thirst,
                                "post_thirst": post_thirst,
                            },
                        )
                    else:
                        self.move_towards(target)
                    return True

        if self.hunger > HUNGER_DANGER_THRESHOLD:
            # 緊急食料探索
            known_food = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
            if known_food:
                nearest_berries = self.env.nearest_nodes(self.pos(), known_food, k=1)
                if nearest_berries:
                    target = nearest_berries[0]
                    if self.pos() == target:
                        pre_hunger = float(self.hunger)
                        self.hunger = max(0, self.hunger - 50)
                        post_hunger = float(self.hunger)
                        log_event(
                            self.log,
                            {
                                "t": t,
                                "name": self.name,
                                "action": "emergency_eat",
                                "recovery": 50,
                                "life_crisis": life_crisis,
                                "pre_hunger": pre_hunger,
                                "post_hunger": post_hunger,
                            },
                        )
                    else:
                        self.move_towards(target)
                    return True

        return False

    def step(self, t):
        """メインの行動ステップ"""
        if not self.alive:
            return

        # 基本的な劣化（疲労は上限制御）
        self.hunger += 1.5
        self.thirst += 2.0
        self.fatigue = min(150.0, self.fatigue + 1.0)  # 疲労上限を150に設定

        # 生存チェック（バランス調整された生存条件）
        if self.thirst > 180 or self.hunger > 200:
            self.alive = False
            cause = "dehydration" if self.thirst > 180 else "starvation"
            log_event(self.log, {"t": t, "name": self.name, "action": "death", "cause": cause})
            return

        # SSD理論：意味圧による探索モードシフト
        self.consider_exploration_mode_shift(t)

        # 重症回復チェック
        self.check_injury_recovery(t)

        # 記憶の鮮明さ減衰（信頼度は維持）
        self.decay_memory_over_time(t)

        # 経験値の減衰処理（使わないと錆びる）
        self.decay_unused_experience(t)

        # 危機的状況での学習システム
        self.crisis_learning = {
            "trusted_water_sources": set(),  # 信頼できる水場
            "trusted_hunting_grounds": set(),  # 信頼できる狩場
            "trusted_foraging_spots": set(),  # 信頼できる採取場
            "crisis_behaviors": {
                "caution_level": 0.1,  # 慎重さレベル
                "risk_aversion": 0.1,  # リスク回避度
                "resource_prioritization": {
                    "water": 0.1,  # 水場の優先度
                    "hunting": 0.1,  # 狩場の優先度
                    "foraging": 0.1,  # 採取場の優先度
                },
            },
            "crisis_experiences": [],  # 危機的経験の履歴
        }

        # 重症者支援システム
        if self.seek_help_for_injured(t):
            return  # 支援活動を優先

        # 命の危機対応（SSD Core Engine版）
        if self.ssd_enhanced_ref:
            life_crisis = self.ssd_enhanced_ref.calculate_life_crisis_pressure_v2()
        else:
            life_crisis = 0.0  # フォールバック
        if life_crisis > 1.0:
            # 現在の場所を特定
            current_location = "unknown"
            npc_pos = self.pos()
            
            # 最も近いリソースを場所として特定
            nearest_water = self.env.nearest_nodes(npc_pos, self.env.water_sources, k=1)
            nearest_berry = self.env.nearest_nodes(npc_pos, self.env.berries, k=1)
            nearest_hunt = self.env.nearest_nodes(npc_pos, self.env.hunting_grounds, k=1)
            
            if nearest_water:
                water_dist = distance_between(npc_pos, nearest_water[0])
                if water_dist < 5:
                    current_location = "water_source"
            if nearest_berry and not current_location.startswith("water"):
                berry_dist = distance_between(npc_pos, nearest_berry[0])
                if berry_dist < 5:
                    current_location = "berry_patch"
            if nearest_hunt and current_location == "unknown":
                hunt_dist = distance_between(npc_pos, nearest_hunt[0])
                if hunt_dist < 5:
                    current_location = "hunting_ground"
            
            # 危機の種類を判定
            crisis_type = "general"
            if self.thirst > 120:
                crisis_type = "thirst"
            elif self.hunger > 120:
                crisis_type = "hunger"
            elif self.fatigue > 120:
                crisis_type = "fatigue"
            
            # 危機的状況での学習
            self.life_crisis = life_crisis  # 現在の危機レベルを保存
            self.learn_from_crisis(t, crisis_type, current_location)
            if self.emergency_survival_action(t, life_crisis):
                return
        if self.seek_group_protection(t):
            return

        # 重症者は行動制限
        if self.critically_injured:
            # 重症者は基本的に待機（看護を受ける）
            if self.caregiver:
                log_event(
                    self.log,
                    {
                        "t": t,
                        "name": self.name,
                        "action": "being_cared",
                        "caregiver": self.caregiver.name,
                    },
                )
            return

        # 看護中は看護を優先
        if self.care_target and self.care_target.critically_injured:
            self.provide_care(t)
            return

        # 【未来予測エンジンによる統合的行動決定】
        if hasattr(self, "future_engine"):
            recommended_action = self.future_engine.get_immediate_action_recommendation()

            if recommended_action:
                self.execute_predicted_action(recommended_action, t)
                return

        # フォールバック: 従来の優先順位ベース行動（未来予測統合版）
        if self.thirst > 60:  # 未来予測に合わせて閾値を下げる
            self.seek_water(t)
        elif self.hunger > 40:  # 予測的協力：まだ余裕があるうちから協力を検討
            # 将来の食料不足を予測して事前に協力
            if self.consider_future_cooperation(t):
                # 予測的集団狩りを優先的に試行
                if not self.organize_predictive_group_hunt(t):
                    # 通常の狩り判断にフォールバック
                    if self.consider_hunting(t):
                        if not self.attempt_solo_hunt(t):
                            self.seek_food(t)
                    else:
                        self.seek_food(t)
            elif self.consider_hunting(t):
                # 従来の反応的狩り
                if not self.organize_group_hunt(t):
                    if not self.attempt_solo_hunt(t):
                        self.seek_food(t)
            else:
                self.seek_food(t)
        elif self.hunt_group and self.hunt_group.status == "forming":
            # 狩りグループの実行
            self.execute_group_hunt(t)
        # 予測的疲労管理
        should_rest, rest_type = self.consider_predictive_rest(t)
        if should_rest:
            self.seek_rest(t)
        else:
            # 予測的協力の機会検討（低優先度）
            if self.hunger > 25:  # 非常に早い段階から協力を検討
                if self.consider_strategic_cooperation(t):
                    if not self.organize_predictive_group_hunt(t):
                        pass  # 通常行動に移行
            self.explore_or_socialize(t)

    def execute_predicted_action(self, action, t):
        """予測されたアクションの実行"""
        action_type = action.action_type

        # 予測エンジンのサマリーをログに記録
        prediction_summary = self.future_engine.get_prediction_summary()
        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": "future_prediction_decision",
                "recommended_action": action_type.value,
                "urgency": action.urgency,
                "rationale": prediction_summary["recommended_action"]["rationale"],
                "survival_risk": prediction_summary["survival_risk_level"],
            },
        )

        # アクション実行
        if action_type.value == "hunt":
            self.execute_predictive_hunt(t)
        elif action_type.value == "forage":
            self.execute_predictive_forage(t)
        elif action_type.value == "drink":
            self.execute_predictive_drink(t)
        elif action_type.value == "rest":
            self.execute_predictive_rest(t)
        elif action_type.value == "explore":
            self.execute_predictive_explore(t)
        elif action_type.value == "cooperate":
            self.execute_predictive_cooperation(t)
        else:
            # 未対応のアクションはフォールバック
            self.explore_or_socialize(t)

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

    def execute_predictive_forage(self, t):
        """予測的採集実行"""
        self.seek_food(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_forage"})

    def execute_predictive_drink(self, t):
        """予測的水分補給実行"""
        self.seek_water(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_drink"})

    def execute_predictive_rest(self, t):
        """予測的休憩実行"""
        self.seek_rest(t)
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_rest"})

    def execute_predictive_explore(self, t):
        """予測的探索実行"""
        self.explore_for_resource(t, "any")
        log_event(self.log, {"t": t, "name": self.name, "action": "predictive_explore"})

    def execute_predictive_cooperation(self, t):
        """予測的協力実行"""
        if self.organize_predictive_group_hunt(t):
            log_event(
                self.log, {"t": t, "name": self.name, "action": "predictive_cooperation_success"}
            )
        else:
            # 協力失敗時は次善策
            self.execute_predictive_hunt(t)

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
                if self.distance_to(other_npc) < 20 and other_npc.knowledge_water:
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
                    recovery_amount = min(35, water_info["water_amount"])

                    # 季節によって回復量を調整
                    if hasattr(self.env, "seasonal_modifier"):
                        temp_stress = self.env.seasonal_modifier.get("temperature_stress", 0.0)
                        recovery_amount = max(20, recovery_amount - (temp_stress * 5))

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
                        return result
                else:
                    print(f"🏞️🚫 {self.name} found empty cave {cave_id} at {cave_pos}")

        # 現在位置に洞窟がない場合、近くの水のある洞窟を探す
        return self._seek_nearby_cave_with_water(t)

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
            caves_with_water.sort(key=lambda x: x[2])  # 識別子でソート
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
        known_berries = {k: v for k, v in self.env.berries.items() if k in self.knowledge_berries}
        if known_berries:
            nearest_berries = self.env.nearest_nodes(self.pos(), known_berries, k=1)
            if nearest_berries:
                target = nearest_berries[0]
                if self.pos() == target:
                    success_rate = 0.8
                    if probability_check(success_rate):
                        self.hunger = max(0, self.hunger - 40)
                        log_event(
                            self.log,
                            {"t": t, "name": self.name, "action": "forage", "recovery": 40},
                        )
                else:
                    self.move_towards(target)
        else:
            self.explore_for_resource(t, "food")

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
        if self.consider_cooperation_readiness():
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
            # 安全感に基づく洞窟選択
            cave_safety = {}
            for cave_name, cave_pos in known_caves.items():
                safety_feeling = self.calculate_cave_safety_feeling(cave_pos)
                cave_safety[cave_pos] = safety_feeling

            if cave_safety:
                # --- 追加: 各洞窟の safety_feeling をログに残す (解析用) ---
                try:
                    import os, csv

                    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
                    os.makedirs(logs_dir, exist_ok=True)
                    safety_path = os.path.join(logs_dir, "cave_safety_timeseries.csv")
                    header_needed = not os.path.exists(safety_path)
                    with open(safety_path, "a", newline="", encoding="utf-8") as sf:
                        writer = csv.writer(sf)
                        if header_needed:
                            writer.writerow(
                                [
                                    "t",
                                    "npc",
                                    "cave_pos",
                                    "safety_feeling",
                                    "is_best",
                                    "territory_claim_threshold",
                                ]
                            )
                        # write each cave's safety
                        for pos, sf_val in cave_safety.items():
                            # is_best will be filled after best selection; mark provisional False here
                            writer.writerow(
                                [
                                    t,
                                    self.name,
                                    str(pos),
                                    float(sf_val),
                                    False,
                                    float(self.territory_claim_threshold),
                                ]
                            )
                except Exception:
                    pass

                best_cave = max(cave_safety.keys(), key=lambda pos: cave_safety[pos])
                safety_feeling = cave_safety[best_cave]

                if self.pos() == best_cave:
                    # 洞窟での休息
                    base_recovery = 25
                    safety_bonus = safety_feeling * 15
                    total_recovery = base_recovery + safety_bonus

                    self.fatigue = max(0, self.fatigue - total_recovery)

                    # SSD理論：野宿・生存経験の獲得
                    survival_quality = safety_feeling * (total_recovery / 40)  # 回復効率に基づく
                    self.gain_experience(
                        "survival",
                        EXPERIENCE_SYSTEM_SETTINGS["survival_exp_rate"] * survival_quality,
                        t,
                    )

                    # 縄張り設定の検討
                    has_territory = (self.use_ssd_engine_social and self.territory_id) or (not self.use_ssd_engine_social and self.territory)
                    if safety_feeling >= self.territory_claim_threshold and not has_territory:
                        # mark the best cave row as is_best and then claim
                        try:
                            import os, csv

                            safety_path = os.path.join(
                                os.path.dirname(__file__), "logs", "cave_safety_timeseries.csv"
                            )
                            # append a row specifically marking the best cave (safer than editing file)
                            with open(safety_path, "a", newline="", encoding="utf-8") as sf:
                                writer = csv.writer(sf)
                                writer.writerow(
                                    [
                                        t,
                                        self.name,
                                        str(best_cave),
                                        float(safety_feeling),
                                        True,
                                        float(self.territory_claim_threshold),
                                    ]
                                )
                        except Exception:
                            pass
                        self.claim_cave_territory(best_cave, t, safety_feeling=safety_feeling)

                    log_event(
                        self.log,
                        {
                            "t": t,
                            "name": self.name,
                            "action": "rest_in_cave",
                            "recovery": total_recovery,
                            "safety_feeling": safety_feeling,
                        },
                    )
                else:
                    # 疲労レベルに応じた移動速度調整
                    if self.fatigue > 100:
                        # 緊急時は直線的に素早く移動
                        self.move_towards_efficiently(best_cave)
                    else:
                        self.move_towards(best_cave)
        else:
            # 洞窟を知らない場合のログ
            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "explore_for_shelter",
                    "fatigue": self.fatigue,
                    "reason": "no_known_caves",
                },
            )
            self.explore_for_resource(t, "shelter")

    def explore_for_resource(self, t, resource_type):
        """リソース探索"""
        # 探索移動
        explore_distance = 3 if self.exploration_mode else 2
        dx = random.randint(-explore_distance, explore_distance)
        dy = random.randint(-explore_distance, explore_distance)

        new_x = max(0, min(self.env.size - 1, self.x + dx))
        new_y = max(0, min(self.env.size - 1, self.y + dy))
        self.x, self.y = new_x, new_y

        # SSD理論：探索経験の獲得
        exploration_intensity = self.exploration_intensity if self.exploration_mode else 0.5
        self.gain_experience(
            "exploration",
            EXPERIENCE_SYSTEM_SETTINGS["exploration_exp_rate"] * exploration_intensity,
            t,
        )

        # リソース発見判定
        discovery_chance = 0.3
        if self.exploration_mode:
            discovery_chance *= self.exploration_intensity

        if probability_check(discovery_chance):
            self.discover_nearby_resources(t, resource_type)

    def discover_nearby_resources(self, t, target_type):
        """近くのリソースを発見"""
        # 疲労時の発見半径拡大 - 緊急時のリソース発見促進
        base_radius = 15  # 基本半径を5から15に拡大
        fatigue_bonus = max(0, (self.fatigue - 70) * 0.3)  # 疲労70超過時にボーナス半径
        discovery_radius = base_radius + fatigue_bonus
        discovered = False

        # 水源の発見
        if target_type in ["water", "any"]:
            for water_name, water_pos in self.env.water_sources.items():
                if (
                    water_name not in self.knowledge_water
                    and self.distance_to(water_pos) <= discovery_radius
                ):
                    self.knowledge_water.add(water_name)
                    self.record_discovery_experience(t, "water", 0.8)
                    discovered = True

        # ベリーの発見
        if target_type in ["food", "any"]:
            for berry_name, berry_pos in self.env.berries.items():
                if (
                    berry_name not in self.knowledge_berries
                    and self.distance_to(berry_pos) <= discovery_radius
                ):
                    self.knowledge_berries.add(berry_name)
                    self.record_discovery_experience(t, "berries", 0.7)
                    discovered = True

        # 洞窟の発見
        if target_type in ["shelter", "any"]:
            for cave_name, cave_pos in self.env.caves.items():
                if (
                    cave_name not in self.knowledge_caves
                    and self.distance_to(cave_pos) <= discovery_radius
                ):
                    self.knowledge_caves.add(cave_name)
                    self.record_discovery_experience(t, "cave", 0.9)
                    discovered = True

        return discovered

    def record_discovery_experience(self, t, resource_type, meaning_pressure):
        """SSD理論：発見体験の記録"""
        resource_values = {"water": 0.9, "berries": 0.7, "cave": 0.85, "hunting_ground": 0.8}

        value = resource_values.get(resource_type, 0.7)
        mode_multiplier = self.exploration_intensity if self.exploration_mode else 1.0
        pleasure = meaning_pressure * value * mode_multiplier

        # SSD理論パラメータの更新
        self.kappa["exploration"] = min(1.0, self.kappa.get("exploration", 0.1) + 0.15)
        self.E = min(5.0, self.E + pleasure * 0.5)  # 未処理圧の蓄積
        self.T = max(self.T0, self.T - 0.3)

        self.experience_points += pleasure * 0.3
        self.lifetime_discoveries += 1

        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": f"discovery_{resource_type}",
                "pleasure": pleasure,
                "E": self.E,
            },
        )

    def explore_or_socialize(self, t):
        """探索または社会化行動"""
        if self.exploration_mode or probability_check(self.curiosity):
            self.explore_for_resource(t, "any")
        else:
            # 社会的行動
            nearby_npcs = [
                npc
                for npc in self.roster.values()
                if npc != self and npc.alive and self.distance_to(npc.pos()) <= 8
            ]

            if nearby_npcs and probability_check(self.sociability):
                closest_npc = min(nearby_npcs, key=lambda n: self.distance_to(n.pos()))
                self.move_towards(closest_npc.pos())
                log_event(
                    self.log,
                    {"t": t, "name": self.name, "action": "socialize", "target": closest_npc.name},
                )

    # === 狩りシステム ===

    def consider_hunting(self, t):
        """狩りの検討"""

        # 狩りクールダウンチェック
        hunt_cooldown = max(3, 8 - int(self.experience["hunting"] * 2))  # 経験で短縮
        if t - self.last_hunt_attempt < hunt_cooldown:
            return False

        # 狩りを行う条件
        hunting_desire = 0.0

        # 飢餓レベルによる狩り欲求
        if self.hunger > 60:  # より低い閾値
            hunting_desire += (self.hunger - 60) / 140

        # 性格による狩り傾向
        hunting_desire += self.risk_tolerance * 0.4

        # 肉の不足による欲求
        if not self.meat_inventory:
            hunting_desire += 0.5

        # 狩り経験による自信
        success_rate = self.calculate_hunting_confidence()
        hunting_desire += success_rate * 0.4

        return hunting_desire > 0.05  # 0.2 → 0.05 に大幅に下げて群れ狩り促進

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

        # リーダーシップのあるNPCは積極的に協力を組織
        if hasattr(self, "leadership"):
            strategic_value += self.leadership * 0.4

        # 社会性による戦略的判断
        strategic_value += self.sociability * 0.5

        # 周囲の仲間の状況を観察
        nearby_npcs = [
            npc
            for npc in self.roster.values()
            if npc != self and npc.alive and self.distance_to(npc.pos()) <= 30
        ]

        if nearby_npcs:
            avg_hunger = sum(npc.hunger for npc in nearby_npcs) / len(nearby_npcs)
            if avg_hunger > 40:  # 周囲が困り始めている
                strategic_value += 0.3

        # 経験豊富なNPCは戦略的に協力を判断
        hunting_exp = self.experience.get("hunting", 0)
        strategic_value += hunting_exp * 0.2

        print(
            f"  🎯 T{t}: STRATEGIC COOPERATION - {self.name} strategic value: {strategic_value:.2f}"
        )

        return strategic_value > 0.3  # 戦略的協力の閾値

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
        # from social import MeatResource  # Replaced by SSD Social Layer

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
                # 従来版無効化 - 値のみ追加
                self.meat_inventory.append(meat_amount)
            print(
                f"  🎯 T{t}: SOLO HUNT SUCCESS - {self.name} caught {prey_type}, gained {meat_amount} meat!"
            )

            # 経験値更新
            self.hunt_success_count += 1
            self.hunting_experience += 0.2

            # SSD理論：狩り経験の獲得
            self.gain_experience("hunting", EXPERIENCE_SYSTEM_SETTINGS["hunting_exp_rate"], t)

            # SSD理論：成功による快感（跳躍的報酬）
            success_pleasure = meat_amount * 0.5 + confidence * 0.3
            self.E = max(0.0, self.E - success_pleasure * 0.4)  # 未処理圧の軽減
        else:
            # 狩り失敗
            self.hunt_failure_count += 1

            # SSD理論：失敗による未処理圧の蓄積
            failure_pressure = confidence * 0.3 + 0.2
            self.E = min(5.0, self.E + failure_pressure)

        # 成功・失敗に関わらず怪我リスクあり（成功時は確率減少）
        injury_rate = HUNTING_SETTINGS["danger_rate"]
        if hunt_successful:
            injury_rate *= 0.6  # 成功時は怪我確率40%減

        injured = False
        critical_injury = False
        if probability_check(injury_rate):
            injury_damage = random.randint(5, 15) if not hunt_successful else random.randint(3, 12)
            self.fatigue = min(150.0, self.fatigue + injury_damage)  # 疲労上限制御
            injured = True

            # 重症判定
            if probability_check(HUNTING_SETTINGS["critical_injury_rate"]):
                self.become_critically_injured(t)
                critical_injury = True

            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "hunt_injury",
                    "damage": injury_damage,
                    "hunt_success": hunt_successful,
                    "critical_injury": critical_injury,
                },
            )

        # 結果ログ
        if hunt_successful:
            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "solo_hunt_success",
                    "prey_type": prey_type,
                    "meat_amount": meat_amount,
                    "pleasure": success_pleasure,
                    "injured": injured,
                },
            )
        else:
            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "solo_hunt_failure",
                    "pressure_increase": failure_pressure,
                    "injured": injured,
                },
            )

        return hunt_successful

    def organize_group_hunt(self, t):
        """集団狩りの組織化 - SSD Core Engineでは予測版を使用"""
        # SSD Core Engine使用時は予測版を優先
        if self.use_ssd_engine_social:
            return self.organize_predictive_group_hunt(t)
        
        # 従来版は無効化
        print(f"    ❌ Group hunt disabled - SSD Engine required")
        return False

        print(f"  🤝 T{t}: GROUP HUNT ATTEMPT - {self.name} trying to organize group hunt...")

        # 近くの仲間を探す - デバッグ版
        all_npcs = [npc for npc in self.roster.values() if npc != self and npc.alive]
        print(f"    🔍 DEBUG: Checking {len(all_npcs)} alive NPCs for group formation")

        potential_members = []
        for npc in all_npcs:
            distance = self.distance_to(npc.pos())
            print(
                f"      - {npc.name}: distance={distance:.1f}, hunt_group={npc.hunt_group}, fatigue={npc.fatigue:.1f}"
            )

            if npc.hunt_group is None and distance <= 60 and npc.fatigue < 151:
                potential_members.append(npc)
                print("        ✅ ELIGIBLE for group hunt")
            else:
                print(
                    f"        ❌ NOT ELIGIBLE: hunt_group={npc.hunt_group}, distance={distance:.1f} (≤25?), fatigue={npc.fatigue:.1f} (<120?)"
                )

        print(f"    👥 Found {len(potential_members)} potential members within range 60")

        if len(potential_members) >= 1: # 最低2人（自分含む）で組織
            print("    ✅ Enough members for group hunt! Creating group...")
            # 狩りグループ作成 - SSD Core Engine版
            if self.use_ssd_engine_social and self.ssd_enhanced_ref:
                hunt_group_id = self.ssd_enhanced_ref.create_hunt_group_v2(self.name, "medium_game")
            else:
                # 従来版無効化
                print("    ❌ Group hunt disabled - SSD Engine required")
                return False

            # メンバー募集
            recruited = 0
            for npc in potential_members[:4]:  # 最大5人まで
                # 参加意欲の計算（信頼関係考慮）
                trust_level = npc.get_trust_level(self.name)
                trust_bonus = trust_level * 0.3  # 信頼できるリーダーなら参加しやすい

                join_probability = (
                    npc.risk_tolerance * 0.4
                    + npc.sociability * 0.3
                    + (npc.hunger / 200) * 0.2
                    + trust_bonus
                )

                if probability_check(join_probability):
                    hunt_group.add_member(npc)
                    npc.hunt_group = hunt_group
                    recruited += 1

            if hunt_group.can_start_hunt():
                self.hunt_group = hunt_group

                # 境界システムに狩りグループを統合
                if self.boundary_system:
                    self.boundary_system.integrate_hunt_group_as_boundary(hunt_group)

                print(
                    f"  🎯 T{t}: GROUP HUNT FORMED - {self.name} organized group with {len(hunt_group.members)} members: {[m.name for m in hunt_group.members]}"
                )
                log_event(
                    self.log,
                    {
                        "t": t,
                        "name": self.name,
                        "action": "organize_hunt_group",
                        "members": [m.name for m in hunt_group.members],
                        "target_prey": hunt_group.target_prey_type,
                    },
                )

                return True
            else:
                print(f"    ❌ Group hunt failed: not enough recruited members ({recruited})")
        else:
            print(
                f"    ❌ Not enough potential members: {len(potential_members)} (need 1+, range: 60, fatigue<151)"
            )

        return False

    def organize_predictive_group_hunt(self, t):
        """予測的グループハンティングの組織（将来に備えた協力）"""
        # from social import HuntGroup  # Replaced by SSD Social Layer
        from config import HUNTING_SETTINGS

        # 既にグループに参加している場合はスキップ
        if self.hunt_group:
            return False

        print(
            f"  🔮🤝 T{t}: PREDICTIVE GROUP HUNT - {self.name} organizing future-oriented cooperation..."
        )

        # より広範囲での仲間探索（予測的協力では範囲を拡大）
        potential_members = []
        all_npcs = [npc for npc in self.roster.values() if npc != self and npc.alive]
        print(f"    🔍 PREDICTIVE: Checking {len(all_npcs)} alive NPCs for future cooperation")

        for npc in all_npcs:
            distance = self.distance_to(npc.pos())
            print(
                f"      - {npc.name}: distance={distance:.1f}, hunt_group={npc.hunt_group}, fatigue={npc.fatigue:.1f}"
            )

            # 予測的協力では条件を大幅緩和（生存のため）
            if (
                npc.hunt_group is None
                and distance <= 60  # 範囲拡大 40 → 60（生存圏拡大）
                and npc.fatigue < 151  # 疲労閾値を上限以上に設定（生存優先）
                and self.assess_cooperation_potential(npc, t)
            ):  # 協力ポテンシャル評価
                potential_members.append(npc)
                print("        ✅ ELIGIBLE for predictive group hunt")
            else:
                print("        ❌ NOT ELIGIBLE for predictive cooperation")

        print(
            f"    👥 Found {len(potential_members)} potential members for predictive hunt (range: 60, fatigue<151)"
        )

        if len(potential_members) >= 1: # 最低2人（自分含む）で組織
            print("    ✅ Enough members for predictive group hunt! Creating group...")
            # 狩りグループ作成 - SSD Core Engine版
            if self.use_ssd_engine_social and self.ssd_enhanced_ref:
                hunt_group_id = self.ssd_enhanced_ref.create_hunt_group_v2(self.name, "medium_game")
            else:
                # 従来版無効化
                print("    ❌ Predictive group hunt disabled - SSD Engine required")
                return False

            # メンバー募集（予測的協力では成功しやすい）- SSD Core Engine版
            member_names = [self.name]
            recruited = 0
            for npc in potential_members[:4]:  # 最大5人まで
                # 予測的協力の参加意欲（通常より高い）
                trust_level = npc.get_trust_level(self.name)
                future_benefit = npc.sociability * 0.5  # 将来利益への理解
                participation_desire = 0.6 + trust_level * 0.2 + future_benefit

                if participation_desire > 0.4:  # 予測的協力では参加しやすい
                    npc.hunt_group = hunt_group_id  # SSD版のIDを設定
                    member_names.append(npc.name)
                    recruited += 1
                    print(
                        f"      ✅ {npc.name} joined predictive group hunt (desire: {participation_desire:.2f})"
                    )

            if recruited >= 1:  # SSD版では最低メンバー数チェック
                self.hunt_group = hunt_group_id

                print(
                    f"  🔮🎯 T{t}: PREDICTIVE GROUP FORMED - {self.name} organized future-oriented group with {len(member_names)} members: {member_names}"
                )
                log_event(
                    self.log,
                    {
                        "t": t,
                        "name": self.name,
                        "action": "organize_predictive_hunt_group",
                        "members": member_names,
                        "target_prey": "medium_game",
                        "cooperation_type": "predictive",
                        "hunt_group_id": hunt_group_id,
                    },
                )

                return True
            else:
                print(
                    f"    ❌ Predictive group hunt failed: not enough recruited members ({recruited})"
                )
        else:
            print(
                f"    ❌ Not enough potential members for predictive cooperation: {len(potential_members)}"
            )

        return False

    def assess_cooperation_potential(self, other_npc, t):
        """他のNPCとの協力ポテンシャルを評価"""

        potential = 0.0

        # 信頼関係
        trust = self.get_trust_level(other_npc.name)
        potential += trust * 0.3

        # 相互の社会性
        social_compatibility = (self.sociability + other_npc.sociability) / 2
        potential += social_compatibility * 0.4

        # 相互の経験値（経験豊富なペアは協力しやすい）
        combined_experience = self.experience.get("hunting", 0) + other_npc.experience.get(
            "hunting", 0
        )
        potential += min(combined_experience * 0.1, 0.2)

        # 将来の困窮予測（どちらかが困りそうな場合）
        future_need = max((self.hunger - 20) / 80, (other_npc.hunger - 20) / 80)  # 0-1で正規化
        potential += future_need * 0.3

        return potential > 0.15  # 協力ポテンシャル閾値を緩和（0.3 → 0.15）

    def execute_group_hunt(self, t):
        """集団狩りの実行"""
        from config import HUNTING_SETTINGS, PREY_TYPES
        # from social import MeatResource  # Replaced by SSD Social Layer

        # SSD Core Engine版ではgroup huntは無効化（単独huntのみ）
        if self.use_ssd_engine_social:
            print(f"  ❌ Group hunt execution disabled - using individual hunt instead")
            return self.attempt_solo_hunt(t)
        
        # 従来版も無効化
        return False

        # 全メンバーの疲労コスト（上限制御）
        hunt_cost = HUNTING_SETTINGS["hunt_fatigue_cost"]
        for member in hunt_group.members:
            member.fatigue = min(150.0, member.fatigue + hunt_cost)
            member.last_hunt_attempt = t

        # 成功判定
        success_rate = hunt_group.get_success_rate()

        hunt_successful = probability_check(success_rate)

        if hunt_successful:
            # 狩り成功
            prey_type = hunt_group.target_prey_type
            meat_amount = PREY_TYPES[prey_type]["meat_amount"]

            print(
                f"  🎉 T{t}: GROUP HUNT SUCCESS - {self.name}'s group caught {prey_type}, gained {meat_amount} meat!"
            )

            # 肉リソース作成（グループ共有）
            meat = MeatResource(meat_amount, owner=self.name, hunt_group=hunt_group)
            meat.creation_tick = t

            # リーダーが肉を管理
            self.meat_inventory.append(meat)
            hunt_group.success = True
            hunt_group.meat_acquired = meat_amount

            # 全メンバーの経験値更新
            for member in hunt_group.members:
                member.hunt_success_count += 1
                member.hunting_experience += 0.3

                # SSD理論：集団狩りでの経験獲得（協力学習）
                base_exp = EXPERIENCE_SYSTEM_SETTINGS["hunting_exp_rate"] * 1.2  # 集団ボーナス
                member.gain_experience("hunting", base_exp, t)
                member.gain_experience("social", EXPERIENCE_SYSTEM_SETTINGS["social_exp_rate"], t)

                # SSD理論：集団成功による快感と社会的結束
                success_pleasure = (meat_amount / len(hunt_group.members)) * 0.6
                social_bonding = len(hunt_group.members) * 0.1
                total_pleasure = success_pleasure + social_bonding

                member.E = max(0.0, member.E - total_pleasure * 0.5)
                member.kappa["group_hunting"] = min(1.0, member.kappa.get("group_hunting", 0.1) + 0.25)

                # 信頼度更新：共に危険を乗り越えた結束
                for other_member in hunt_group.members:
                    if other_member != member:
                        # 成功した狩りでの信頼関係
                        emotional_context = {
                            "shared_danger": True,
                            "life_threatening": False,  # 成功したので危険は過ぎた
                        }
                        member.update_trust(
                            other_member.name, "hunt_together_success", t, emotional_context
                        )
        else:
            print(
                f"  💔 T{t}: GROUP HUNT FAILED - {self.name}'s group failed to catch {hunt_group.target_prey_type}"
            )
            # 狩り失敗
            for member in hunt_group.members:
                member.hunt_failure_count += 1

            # SSD理論：集団失敗による未処理圧
            for member in hunt_group.members:
                failure_pressure = 0.4 / len(hunt_group.members)  # 集団では圧力分散
                member.E = min(5.0, member.E + failure_pressure)

        # 成功・失敗に関わらず全メンバーに怪我リスク
        injured_members = []
        for member in hunt_group.members:
            # 集団では危険分散、成功時はさらに減少
            base_danger_rate = HUNTING_SETTINGS["danger_rate"] / len(hunt_group.members)
            if hunt_successful:
                injury_rate = base_danger_rate * 0.5  # 成功時は怪我確率50%減
            else:
                injury_rate = base_danger_rate

            if probability_check(injury_rate):
                injury_damage = random.randint(2, 8) if hunt_successful else random.randint(3, 10)
                member.fatigue = min(150.0, member.fatigue + injury_damage)  # 疲労上限制御
                critical_injury = False

                # 重症判定（集団では確率低下）
                critical_rate = HUNTING_SETTINGS["critical_injury_rate"] * 0.5
                if probability_check(critical_rate):
                    member.become_critically_injured(t)
                    critical_injury = True

                injured_members.append(
                    {"name": member.name, "damage": injury_damage, "critical": critical_injury}
                )

                log_event(
                    member.log,
                    {
                        "t": t,
                        "name": member.name,
                        "action": "hunt_injury",
                        "damage": injury_damage,
                        "hunt_success": hunt_successful,
                        "group_hunt": True,
                        "critical_injury": critical_injury,
                    },
                )

        # 結果ログ
        if hunt_successful:
            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "group_hunt_success",
                    "members": [m.name for m in hunt_group.members],
                    "prey_type": prey_type,
                    "meat_amount": meat_amount,
                    "injured_members": injured_members,
                },
            )
        else:
            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "group_hunt_failure",
                    "members": [m.name for m in hunt_group.members],
                    "injured_members": injured_members,
                },
            )

        # 狩りグループ解散
        for member in hunt_group.members:
            member.hunt_group = None
        hunt_group.status = "disbanded"

        return success_rate > 0.5  # 成功したかどうかを返す

    def manage_meat_inventory(self, t):
        """肉の在庫管理（腐敗処理）"""
        if not self.meat_inventory:
            return

        # 腐敗処理
        spoiled_meat = []
        for meat in self.meat_inventory:
            if meat.decay():
                spoiled_meat.append(meat)

        # 腐った肉を削除
        for meat in spoiled_meat:
            self.meat_inventory.remove(meat)
            log_event(
                self.log,
                {"t": t, "name": self.name, "action": "meat_spoiled", "amount": meat.amount},
            )

    def consume_meat_if_hungry(self, t):
        """空腹時に肉を消費して回復"""
        if self.hunger > 40 and self.meat_inventory:  # より積極的に肉を消費（60→40）
            meat = self.meat_inventory[0]  # 最初の肉を消費
            consume_amount = meat.amount  # 制限を削除：全ての肉を消費可能

            # 空腹回復
            hunger_recovery = consume_amount
            pre_hunger = float(self.hunger)
            old_hunger = self.hunger
            self.hunger = max(0, self.hunger - hunger_recovery)
            post_hunger = float(self.hunger)

            # 肉の量を減らすか除去
            meat.amount -= consume_amount
            if meat.amount <= 0:
                self.meat_inventory.remove(meat)

            print(
                f"  🍖 T{t}: MEAT CONSUMED - {self.name} ate {consume_amount:.1f} meat, hunger: {old_hunger:.1f} → {self.hunger:.1f}"
            )
            result = {
                "t": t,
                "name": self.name,
                "action": "consume_meat",
                "amount": consume_amount,
                "hunger_recovery": hunger_recovery,
                "new_hunger": self.hunger,
                "actual_recovery": hunger_recovery,
                "pre_hunger": pre_hunger,
                "post_hunger": post_hunger,
            }
            log_event(self.log, result)
            self.last_action_result = result
            return result

    def consider_meat_sharing(self, t):
        """肉の分配検討"""
        if not self.meat_inventory:
            return

        for meat in self.meat_inventory:
            sharing_pressure = meat.get_sharing_pressure()

            # 分配圧力が高い場合
            if sharing_pressure > 0.7:
                # 近くの仲間に分配
                nearby_npcs = [
                    npc
                    for npc in self.roster.values()
                    if npc != self
                    and npc.alive
                    and npc.hunger > 60
                    and self.distance_to(npc.pos()) <= 10
                ]

                if nearby_npcs:
                    # 最も飢えている仲間に分配
                    hungriest = max(nearby_npcs, key=lambda n: n.hunger)
                    share_amount = min(meat.amount * 0.3, meat.amount)

                    if share_amount > 0:
                        shared = meat.share_with(hungriest.name, share_amount)
                        hungriest.receive_meat_gift(shared, self, t)

                        # SSD理論：分配による社会的報酬（一時的共感ブースト込み）
                        effective_empathy = self.get_effective_empathy()
                        social_reward = shared * effective_empathy * 0.4
                        self.E = max(0.0, self.E - social_reward)

                        log_event(
                            self.log,
                            {
                                "t": t,
                                "name": self.name,
                                "action": "share_meat",
                                "recipient": hungriest.name,
                                "amount": shared,
                                "social_reward": social_reward,
                            },
                        )

    def receive_meat_gift(self, amount, giver, t):
        """肉の贈り物を受け取る"""
        # 直接栄養として摂取
        pre_hunger = float(self.hunger)
        nutrition = amount * 0.8  # 肉の栄養価
        self.hunger = max(0, self.hunger - nutrition)
        post_hunger = float(self.hunger)

        # 社会的絆の強化
        if hasattr(self, "social_bonds"):
            if not hasattr(self, "social_bonds"):
                self.social_bonds = {}
            self.social_bonds[giver.name] = self.social_bonds.get(giver.name, 0.0) + 0.3

        # 信頼度更新：飢饉程度によって情動的文脈が変化
        if self.hunger > 150:
            event_type = "food_in_hunger" if self.hunger > 180 else "meat_share_starving"
            emotional_context = {"desperate_situation": self.hunger > 200}
        else:
            event_type = "casual_food_share"
            emotional_context = {"desperate_situation": False}

        self.update_trust(giver.name, event_type, t, emotional_context)

        result = {
            "t": t,
            "name": self.name,
            "action": "receive_meat_gift",
            "giver": giver.name,
            "amount": amount,
            "nutrition": nutrition,
            "actual_recovery": nutrition,
            "pre_hunger": pre_hunger,
            "post_hunger": post_hunger,
        }
        log_event(self.log, result)

        # 境界システムに肉共有を反映
        if self.boundary_system:
            self.boundary_system.integrate_meat_sharing_as_boundary(giver.name, self.name, amount, t)

        self.last_action_result = result
        return result

    # === 重症システム ===

    def become_critically_injured(self, t):
        """重症状態になる"""
        self.critically_injured = True
        self.injury_start_tick = t
        self.injury_recovery_time = random.randint(
            CRITICAL_INJURY_SETTINGS["duration_min"], CRITICAL_INJURY_SETTINGS["duration_max"]
        )

        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": "critical_injury",
                "recovery_time": self.injury_recovery_time,
            },
        )

        # 境界システムに重症状態を反映
        if self.boundary_system:
            self.boundary_system.process_subjective_experience(
                self, "critical_injury", f"health_{self.name}", {"severity": "critical"}, t
            )

    def check_injury_recovery(self, t):
        """重症の回復チェック"""
        if not self.critically_injured:
            return

        elapsed_time = t - self.injury_start_tick
        recovery_progress = elapsed_time / self.injury_recovery_time

        # 看護による回復加速
        if self.caregiver:
            recovery_progress *= 1 + CRITICAL_INJURY_SETTINGS["care_effectiveness"]

        if recovery_progress >= 1.0:
            self.critically_injured = False
            caregiver_name = self.caregiver.name if self.caregiver else None
            self.caregiver = None

            # 境界システムからケア関係を解除
            if self.boundary_system and caregiver_name:
                self.boundary_system.subjective_boundaries[self.name]["people"].discard(caregiver_name)
                self.boundary_system.subjective_boundaries[caregiver_name]["people"].discard(self.name)

            # 回復時に看護してくれた人への特別な信頼
            if caregiver_name:
                emotional_context = {"life_threatening": True, "desperate_situation": True}
                self.update_trust(caregiver_name, "life_saved_critical", t, emotional_context)

            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "injury_recovery",
                    "duration": elapsed_time,
                    "caregiver": self.caregiver.name if self.caregiver else None,
                },
            )

    def seek_help_for_injured(self, t):
        """重症者への支援を探す・提供する"""
        if self.critically_injured:
            # 重症者：助けを求める
            if not self.caregiver:
                nearby_npcs = [
                    npc
                    for npc in self.roster.values()
                    if npc != self
                    and npc.alive
                    and not npc.critically_injured
                    and self.distance_to(npc.pos()) <= 8
                    and npc.care_target is None
                ]

                if nearby_npcs:
                    # 最も共感的な仲間を選ぶ
                    potential_caregiver = max(nearby_npcs, key=lambda n: n.empathy)

                    # 看護意欲の判定（一時的共感ブースト、信頼関係込み）
                    effective_empathy = potential_caregiver.get_effective_empathy()
                    trust_level = potential_caregiver.get_trust_level(self.name)
                    care_willingness = effective_empathy * 0.6 + trust_level * 0.4 + 0.1
                    if probability_check(care_willingness):
                        self.caregiver = potential_caregiver
                        potential_caregiver.care_target = self

                        # 境界システムにケア関係を反映
                        if self.boundary_system:
                            self.boundary_system.subjective_boundaries[self.name]["people"].add(potential_caregiver.name)
                            self.boundary_system.boundary_strength[self.name][potential_caregiver.name] = 0.9
                            self.boundary_system.subjective_boundaries[potential_caregiver.name]["people"].add(self.name)
                            self.boundary_system.boundary_strength[potential_caregiver.name][self.name] = 0.9

                        # 信頼度更新：重症時の看護は高い情動的熟量
                        emotional_context = {
                            "life_threatening": True,
                            "desperate_situation": self.critically_injured,
                        }
                        self.update_trust(
                            potential_caregiver.name, "care_during_injury", t, emotional_context
                        )

                        log_event(
                            self.log,
                            {
                                "t": t,
                                "name": self.name,
                                "action": "receive_care",
                                "caregiver": potential_caregiver.name,
                            },
                        )

                        return True
        else:
            # 健康者：重症者を探して支援
            if not self.care_target:
                nearby_injured = [
                    npc
                    for npc in self.roster.values()
                    if npc != self
                    and npc.alive
                    and npc.critically_injured
                    and self.distance_to(npc.pos()) <= 10
                    and npc.caregiver is None
                ]

                if nearby_injured:
                    injured_npc = nearby_injured[0]  # 最初の重症者を支援
                    effective_empathy = self.get_effective_empathy()
                    care_willingness = effective_empathy * 0.9 + 0.1

                    if probability_check(care_willingness):
                        self.care_target = injured_npc
                        injured_npc.caregiver = self

                        log_event(
                            self.log,
                            {
                                "t": t,
                                "name": self.name,
                                "action": "start_caring",
                                "patient": injured_npc.name,
                            },
                        )

                        return True
        return False

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
            food_to_share = min(30, self.hunger * CRITICAL_INJURY_SETTINGS["food_sharing_rate"])
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
        if self.meat_inventory and patient.hunger > 80:
            meat = self.meat_inventory[0]
            share_amount = min(meat.amount * 0.4, meat.amount)
            if share_amount > 0:
                shared = meat.share_with(patient.name, share_amount)
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
        effective_empathy = self.get_effective_empathy()
        social_bonding = effective_empathy * 0.25
        self.E = max(0.0, self.E - social_bonding)

        # 看護疲労（上限制御）
        self.fatigue = min(150.0, self.fatigue + 2)

        # SSD理論：看護経験の獲得
        self.gain_experience("care", EXPERIENCE_SYSTEM_SETTINGS["care_exp_rate"], t)

    # === 信頼関係システム ===

    def update_trust(self, other_npc_name, event_type, t, emotional_context=None):
        """情動的熟量を考慮した信頼度更新"""
        if other_npc_name == self.name:
            return  # 自分自身とは信頼関係なし

        # 情動的状態を評価（「熟」の大きさ）
        emotional_heat = self.calculate_emotional_heat(t, emotional_context)

        # イベントに基づく信頼度確定
        if event_type in TRUST_EVENTS:
            event_data = TRUST_EVENTS[event_type]
            base_trust = event_data["base_trust"]
            event_heat = event_data["emotional_heat"]

            # 情動的熟量が高いほど、信頼度の確定が強くなる
            heat_multiplier = 0.5 + (emotional_heat * event_heat * 0.5)
            final_trust = base_trust * heat_multiplier

            # 現在の信頼度との重み付き平均（新しい経験が強い影響）
            current_trust = self.trust_levels.get(
                other_npc_name, TRUST_SYSTEM_SETTINGS["neutral_trust"]
            )
            weight_new = 0.7 + (emotional_heat * 0.3)  # 熟が高いほど新しい経験を重視

            new_trust = (final_trust * weight_new) + (current_trust * (1 - weight_new))
        else:
            # 未定義イベントは小さな変化
            current_trust = self.trust_levels.get(
                other_npc_name, TRUST_SYSTEM_SETTINGS["neutral_trust"]
            )
            change = 0.05 * emotional_heat  # 小さな変化
            new_trust = current_trust + change

        # 信頼度の範囲制限
        new_trust = max(
            TRUST_SYSTEM_SETTINGS["min_trust_level"],
            min(TRUST_SYSTEM_SETTINGS["max_trust_level"], new_trust),
        )

        self.trust_levels[other_npc_name] = new_trust
        self.last_interaction[other_npc_name] = t

        # 履歴記録（情動的熟量も含む）
        if other_npc_name not in self.trust_history:
            self.trust_history[other_npc_name] = []

        self.trust_history[other_npc_name].append(
            {
                "tick": t,
                "event": event_type,
                "emotional_heat": emotional_heat,
                "trust_level": new_trust,
                "memory_strength": 1.0,  # 初期は鮮明
            }
        )

        # 履歴の上限（最新15件まで保持）
        if len(self.trust_history[other_npc_name]) > 15:
            self.trust_history[other_npc_name] = self.trust_history[other_npc_name][-15:]

        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": "trust_established",
                "target": other_npc_name,
                "event_type": event_type,
                "emotional_heat": emotional_heat,
                "trust_level": new_trust,
            },
        )

        # 境界強度同期
        if self.boundary_system:
            self.boundary_system.boundary_strength[self.name][other_npc_name] = new_trust * 0.5

    def calculate_emotional_heat(self, t, context=None):
        """情動的熟量（「熟」の大きさ）を計算"""
        heat = 0.3  # ベースライン

        # 生存危機による熟量
        if self.critically_injured:
            heat += 0.7  # 重症時は情動が高まる
        elif self.hunger > 150:
            heat += 0.4  # 飢饿時
        elif self.thirst > 150:
            heat += 0.4  # 渇き時
        elif self.fatigue > 80:
            heat += 0.2  # 疲労時

        # 最近の危険経験による熟量
        recent_injury = any(
            log.get("action") == "hunt_injury" and t - log.get("t", 0) < 20
            for log in self.log[-10:]
            if isinstance(log, dict)
        )
        if recent_injury:
            heat += 0.3

        # コンテキストによる調整
        if context:
            if context.get("life_threatening", False):
                heat += 0.5
            if context.get("desperate_situation", False):
                heat += 0.4
            if context.get("shared_danger", False):
                heat += 0.3

        return min(1.0, heat)  # 最大0～1.0

    def get_trust_level(self, other_npc_name):
        """記憶に基づいた総合的な信頼度を取得"""
        if other_npc_name == self.name:
            return 1.0  # 自分自身は完全に信頼

        # 直接的な信頼度がある場合
        if other_npc_name in self.trust_levels:
            return self.trust_levels[other_npc_name]

        # 記憶から信頼度を推定
        if other_npc_name in self.trust_history and self.trust_history[other_npc_name]:
            memories = self.trust_history[other_npc_name]

            # 記憶の重み付き平均（鮮明な記憶ほど強い影響）
            weighted_trust = 0
            total_weight = 0

            for memory in memories:
                weight = memory.get("memory_strength", 0.5) * memory.get("emotional_heat", 0.3)
                weighted_trust += memory.get("trust_level", 0.5) * weight
                total_weight += weight

            if total_weight > 0:
                return weighted_trust / total_weight

        return TRUST_SYSTEM_SETTINGS["neutral_trust"]  # 未知は中立

    def get_trusted_npcs(self, threshold=None):
        """信頼できるNPCのリストを取得"""
        if threshold is None:
            threshold = TRUST_SYSTEM_SETTINGS["high_trust_threshold"]

        return [
            npc_name
            for npc_name, trust in self.trust_levels.items()
            if trust >= threshold and npc_name in self.roster and self.roster[npc_name].alive
        ]

    def decay_memory_over_time(self, t):
        """記憶の鮮明さの減衰（信頼度は維持）"""
        decay_rate = TRUST_SYSTEM_SETTINGS["memory_decay_rate"]
        min_strength = TRUST_SYSTEM_SETTINGS["min_memory_strength"]

        # 各人の記憶履歴の鮮明さを減衰
        for npc_name in self.trust_history:
            for memory in self.trust_history[npc_name]:
                # 記憶の鮮明さのみ減衰（情動的熟量が高いほど減衰しにくい）
                emotional_protection = memory.get("emotional_heat", 0.3)
                effective_decay = decay_rate + (
                    emotional_protection * 0.003
                )  # 熟が高いほど減衰しにくい

                memory["memory_strength"] = max(
                    min_strength, memory.get("memory_strength", 1.0) * effective_decay
                )

        # 非常に古い記憶は削除（完全に忘れることはない）
        for npc_name in list(self.trust_history.keys()):
            self.trust_history[npc_name] = [
                memory
                for memory in self.trust_history[npc_name]
                if memory.get("memory_strength", 0) > 0.01
                or t - memory.get("tick", 0) < 200  # 200ティック以内は保持
            ]

    def is_trusted_ally(self, other_npc_name):
        """指定したNPCが信頼できる仲間かどうか"""
        return self.get_trust_level(other_npc_name) >= TRUST_SYSTEM_SETTINGS["high_trust_threshold"]

    # === SSD理論統合型経験システム ===

    def gain_experience(self, experience_type, base_amount, t):
        """SSD理論に基づく経験値獲得（整合慣性κとして機能）"""
        if experience_type not in self.experience:
            return

        # 現在の意味圧(E)を計算
        current_meaning_pressure = self.E

        # 経験値の上限は意味圧の95%まで（SSD理論の制約）
        max_experience = current_meaning_pressure * EXPERIENCE_SYSTEM_SETTINGS["kappa_growth_limit"]
        current_exp = self.experience[experience_type]

        # 意味圧を超える経験知は獲得不可
        if current_exp >= max_experience:
            return  # これ以上の成長はない

        # 学習効率は現在の経験値と意味圧の差に依存
        learning_efficiency = (max_experience - current_exp) / max_experience
        learning_rate = EXPERIENCE_SYSTEM_SETTINGS["base_learning_rate"] * learning_efficiency

        # 経験値獲得
        exp_gain = base_amount * learning_rate
        new_experience = min(max_experience, current_exp + exp_gain)

        self.experience[experience_type] = new_experience
        self.last_experience_update = t

        # 整合慣性κの更新（経験がκ値として機能）
        kappa_key = f"exp_{experience_type}"
        self.kappa[kappa_key] = min(1.0, new_experience / 5.0)  # 正規化

        log_event(
            self.log,
            {
                "t": t,
                "name": self.name,
                "action": "experience_gain",
                "type": experience_type,
                "gain": exp_gain,
                "new_exp": new_experience,
                "meaning_pressure": current_meaning_pressure,
                "max_possible": max_experience,
            },
        )

    def get_experience_efficiency(self, experience_type):
        """経験に基づく行動効率の計算"""
        if experience_type not in self.experience:
            return 1.0

        exp_value = self.experience[experience_type]
        threshold = EXPERIENCE_SYSTEM_SETTINGS["experience_threshold"]
        max_boost = EXPERIENCE_SYSTEM_SETTINGS["max_efficiency_boost"]

        # 経験による効率向上（漸近的成長）
        if exp_value < threshold:
            efficiency = 1.0 + (exp_value / threshold) * (max_boost * 0.3)
        else:
            remaining = exp_value - threshold
            efficiency = 1.0 + max_boost * 0.3 + (remaining / (remaining + 2)) * (max_boost * 0.7)

        return min(1.0 + max_boost, efficiency)

    def decay_unused_experience(self, t):
        """使わない経験は微細に減衰（錆びる）"""
        if t - self.last_experience_update < 20:  # 最近更新されていれば減衰しない
            return

        decay_rate = EXPERIENCE_SYSTEM_SETTINGS["experience_decay"]
        min_exp = EXPERIENCE_SYSTEM_SETTINGS["min_experience"]

        for exp_type in self.experience:
            old_exp = self.experience[exp_type]
            self.experience[exp_type] = max(min_exp, old_exp * decay_rate)

        self.last_experience_update = t

    def witness_critical_injuries(self, t):
        """重症者の目撃による共感増加"""
        if self.critically_injured:
            return  # 自分が重症の場合はスキップ

        # 一時的共感ブーストの自然減衰
        self.temporary_empathy_boost *= CRITICAL_INJURY_SETTINGS["empathy_decay_rate"]

        # 周囲の重症者をチェック
        witness_range = CRITICAL_INJURY_SETTINGS["witness_range"]
        nearby_injured = [
            npc
            for npc in self.roster.values()
            if npc != self
            and npc.alive
            and npc.critically_injured
            and self.distance_to(npc.pos()) <= witness_range
            and npc.name not in self.witnessed_injuries
        ]

        for injured_npc in nearby_injured:
            # 新しい重症者を目撃
            self.witnessed_injuries.add(injured_npc.name)

            # 共感の増加
            empathy_increase = CRITICAL_INJURY_SETTINGS["witness_empathy_boost"]

            # 距離による影響（近いほど強い衝撃）
            distance_factor = max(0.3, 1.0 - (self.distance_to(injured_npc.pos()) / witness_range))
            empathy_increase *= distance_factor

            # 既存の共感度による影響（共感的な人ほど強く反応）
            base_empathy_factor = 0.5 + (self.empathy * 0.5)
            empathy_increase *= base_empathy_factor

            # 一時的共感ブーストに追加（上限あり）
            max_boost = CRITICAL_INJURY_SETTINGS["max_empathy_boost"]
            self.temporary_empathy_boost = min(
                max_boost, self.temporary_empathy_boost + empathy_increase
            )

            log_event(
                self.log,
                {
                    "t": t,
                    "name": self.name,
                    "action": "witness_critical_injury",
                    "injured_npc": injured_npc.name,
                    "empathy_increase": empathy_increase,
                    "total_boost": self.temporary_empathy_boost,
                },
            )

        # 回復した人を目撃リストから削除
        recovered_npcs = {
            npc.name
            for npc in self.roster.values()
            if npc.name in self.witnessed_injuries and not npc.critically_injured
        }
        self.witnessed_injuries -= recovered_npcs

    def get_effective_empathy(self):
        """一時的ブーストを含む実効共感度"""
        return min(1.0, self.empathy + self.temporary_empathy_boost)

    def get_predator_escape_chance(self):
        """捕食者からの逃走成功率を計算（経験考慮）"""
        from config import PREDATOR_AWARENESS_SETTINGS

        # 基本逃走率（体力状態に基づく）
        base_escape_rate = PREDATOR_AWARENESS_SETTINGS["base_escape_rate"]

        # 疲労ペナルティ（0-100の範囲を0-1に正規化）
        fatigue_penalty = (self.fatigue / 100.0) * 0.3

        # 飢えや渇きによる体力低下を考慮
        hunger_penalty = max(0, (self.hunger - 100) / 200.0) * 0.2
        thirst_penalty = max(0, (self.thirst - 100) / 200.0) * 0.2

        adjusted_base = base_escape_rate - fatigue_penalty - hunger_penalty - thirst_penalty

        # 警戒経験によるボーナス
        awareness_exp = self.experience.get("predator_awareness", 0.0)
        experience_bonus = awareness_exp * PREDATOR_AWARENESS_SETTINGS["escape_bonus"]

        # 最終逃走成功率
        final_escape_rate = min(
            PREDATOR_AWARENESS_SETTINGS["max_escape_rate"],
            max(0.05, adjusted_base + experience_bonus),
        )

        return final_escape_rate

    def get_predator_detection_chance(self):
        """捕食者の早期発見確率を計算（経験考慮）"""
        from config import PREDATOR_AWARENESS_SETTINGS

        # 基本発見率
        base_detection = PREDATOR_AWARENESS_SETTINGS["base_detection_rate"]

        # 警戒経験によるボーナス
        awareness_exp = self.experience.get("predator_awareness", 0.0)
        experience_bonus = awareness_exp * PREDATOR_AWARENESS_SETTINGS["detection_bonus"]

        # 疲労による影響
        fatigue_penalty = self.fatigue * 0.2

        # 最終発見確率
        final_detection = min(
            PREDATOR_AWARENESS_SETTINGS["max_detection_rate"],
            max(0.01, base_detection + experience_bonus - fatigue_penalty),
        )

        return final_detection

    def get_predator_avoidance_chance(self):
        """捕食者との遭遇回避確率を計算（経験考慮）"""
        from config import PREDATOR_AWARENESS_SETTINGS

        # 基本回避率
        base_avoidance = PREDATOR_AWARENESS_SETTINGS["base_avoidance_rate"]

        # 警戒経験によるボーナス
        awareness_exp = self.experience.get("predator_awareness", 0.0)
        experience_bonus = awareness_exp * PREDATOR_AWARENESS_SETTINGS["avoidance_bonus"]

        # 最終回避確率
        final_avoidance = min(
            PREDATOR_AWARENESS_SETTINGS["max_avoidance_rate"], base_avoidance + experience_bonus
        )

        return final_avoidance

    def alert_nearby_npcs_about_predator(self, all_npcs, predator_location):
        """近くのNPCに捕食者の存在を警告（経験による効果向上）"""
        from config import PREDATOR_AWARENESS_SETTINGS
        from utils import distance_between

        awareness_exp = self.experience.get("predator_awareness", 0.0)
        alert_effectiveness = 0.5 + (
            awareness_exp * PREDATOR_AWARENESS_SETTINGS["group_alert_bonus"]
        )

        alerted_count = 0
        alert_range = (
            PREDATOR_AWARENESS_SETTINGS["alert_range_base"]
            + awareness_exp * PREDATOR_AWARENESS_SETTINGS["alert_range_bonus"]
        )

        for other_npc in all_npcs:
            if other_npc != self and other_npc.alive:
                distance = distance_between((self.x, self.y), (other_npc.x, other_npc.y))

                if distance <= alert_range and random.random() < alert_effectiveness:
                    # 他のNPCに警戒状態を付与
                    other_npc.predator_alert_time = 20  # 20ティック間警戒
                    other_npc.known_predator_location = predator_location
                    alerted_count += 1

        if alerted_count > 0:
            self.add_ssd_observation("group_alert", alerted_count)

        return alerted_count

    def add_ssd_observation(self, observation_type, value):
        """SSD観察データの追加（簡易実装）"""
        # 将来のSSD理論拡張のためのプレースホルダー
        pass

    def attempt_predator_hunting(self, predators, all_npcs, current_tick):
        """捕食者狩りの試行（超ハイリスク）"""
        from config import PREDATOR_HUNTING

        if not predators:
            return None

        # 近くの捕食者を探す
        nearby_predators = []
        for predator in predators:
            if predator.alive:
                distance = distance_between(self.pos(), predator.pos())
                if distance <= PREDATOR_HUNTING["detection_range"]:
                    nearby_predators.append((predator, distance))

        if not nearby_predators:
            return None

        # 最も近い捕食者を選択
        target_predator, distance = min(nearby_predators, key=lambda x: x[1])

        # 狩猟グループの形成
        hunting_group = [self]
        for npc in all_npcs:
            if (
                npc != self
                and npc.alive
                and distance_between(self.pos(), npc.pos())
                <= PREDATOR_HUNTING["group_formation_range"]
                and len(hunting_group) < PREDATOR_HUNTING["max_group_size"]
            ):
                # グループ参加意思決定
                participation_chance = (
                    npc.risk_tolerance * 0.3
                    + npc.experience.get("predator_awareness", 0) * 0.4
                    + 0.3
                )
                if random.random() < participation_chance:
                    hunting_group.append(npc)

        # 狩猟実行
        return self.execute_predator_hunt(target_predator, hunting_group, current_tick)

    def execute_predator_hunt(self, predator, hunting_group, current_tick):
        """捕食者狩りの実行"""
        from config import PREDATOR_HUNTING

        group_size = len(hunting_group)

        # 成功率計算
        base_success_rate = PREDATOR_HUNTING["success_rate_base"]
        group_bonus = (group_size - 1) * PREDATOR_HUNTING["group_size_bonus"]
        experience_bonus = (
            sum(npc.experience.get("predator_awareness", 0) for npc in hunting_group)
            * PREDATOR_HUNTING["experience_bonus"]
        )

        total_success_rate = min(0.4, base_success_rate + group_bonus + experience_bonus)

        # 狩猟結果判定
        if random.random() < total_success_rate:
            return self.predator_hunt_success(predator, hunting_group, current_tick)
        else:
            return self.predator_hunt_failure(predator, hunting_group, current_tick)

    def predator_hunt_success(self, predator, hunting_group, current_tick):
        """捕食者狩り成功"""
        from config import PREDATOR_HUNTING

        # 捕食者を除去
        predator.alive = False

        results = {
            "success": True,
            "predator_killed": True,
            "group_size": len(hunting_group),
            "casualties": [],
            "injured": [],
            "meat_gained": PREDATOR_HUNTING["meat_reward"],
        }

        # 各参加者への報酬と経験
        for npc in hunting_group:
            # 肉の分配
            npc.hunger = max(0, npc.hunger - PREDATOR_HUNTING["meat_reward"] / len(hunting_group))

            # 経験獲得
            npc.gain_experience("predator_awareness", 0.15, current_tick)
            npc.gain_experience("combat", 0.1, current_tick)

            # SSD学習: 成功体験
            npc.add_ssd_observation("predator_hunt_success", 1.0)

            # 成功時でも疲労
            npc.fatigue = min(100.0, npc.fatigue + 30.0)

        return results

    def predator_hunt_failure(self, predator, hunting_group, current_tick):
        """捕食者狩り失敗"""
        from config import PREDATOR_HUNTING

        results = {
            "success": False,
            "predator_killed": False,
            "group_size": len(hunting_group),
            "casualties": [],
            "injured": [],
            "meat_gained": 0,
        }

        # 各参加者の被害判定
        for member in hunting_group:
            injury_roll = random.random()

            if injury_roll < PREDATOR_HUNTING["death_rate_on_failure"]:
                # 死亡
                member.alive = False
                results["casualties"].append(member.name)
            elif injury_roll < PREDATOR_HUNTING["injury_rate"]:
                # 重傷
                member.fatigue = min(100.0, member.fatigue + 50.0)
                member.hunger = min(200.0, member.hunger + 30.0)  # 代謝亢進
                results["injured"].append(member.name)

                # 重傷でも経験は得る
                member.gain_experience("predator_awareness", 0.08, current_tick)

            # 失敗による疲労とストレス
            member.fatigue = min(100.0, member.fatigue + 40.0)

            # SSD学習: 失敗体験
            member.add_ssd_observation("predator_hunt_failure", 1.0)

        return results

    def attempt_social_cooperation(self, t, roster):
        """協力行動の試行 - 資源共有やグループ狩猟"""
        # 近くの生存NPCを探す
        nearby_npcs = [
            other for other in roster.values()
            if other != self and other.alive and self.distance_to(other.pos()) <= 8
        ]
        
        if not nearby_npcs:
            return False
            
        # 協力行動の種類を決定
        cooperation_type = random.choice(["resource_sharing", "group_hunting", "mutual_help"])
        
        if cooperation_type == "resource_sharing":
            # 資源共有
            return self.attempt_resource_sharing(t, nearby_npcs)
        elif cooperation_type == "group_hunting":
            # グループ狩猟
            return self.attempt_group_hunting(t, nearby_npcs)
        elif cooperation_type == "mutual_help":
            # 相互支援
            return self.attempt_mutual_help(t, nearby_npcs)
            
        return False

    def attempt_resource_sharing(self, t, nearby_npcs):
        """資源共有の試行"""
        # 自分の肉在庫を確認
        if not self.meat_inventory:
            return False
            
        # 最も空腹のNPCを選ぶ
        target = max(nearby_npcs, key=lambda npc: npc.hunger)
        
        if target.hunger > 50:  # 空腹の相手にのみ共有
            # 肉を共有
            shared_meat = min(10.0, self.meat_inventory[0].amount * 0.3)  # 在庫の30%まで
            
            # 自分の在庫を減らす
            self.meat_inventory[0].amount -= shared_meat
            if self.meat_inventory[0].amount <= 0:
                self.meat_inventory.pop(0)
                
            # 相手の空腹を減らす
            target.hunger = max(0, target.hunger - shared_meat * 2)
            
            print(f"🤝 T{t}: RESOURCE SHARING - {self.name} shared {shared_meat:.1f} meat with {target.name}")
            
            # 信頼関係を強化
            self.trust_levels[target.name] = min(1.0, self.trust_levels.get(target.name, 0.5) + 0.1)
            target.trust_levels[self.name] = min(1.0, target.trust_levels.get(self.name, 0.5) + 0.1)
            
            log_event(self.log, {
                "t": t,
                "name": self.name,
                "action": "resource_sharing",
                "target": target.name,
                "amount": shared_meat
            })
            
            return True
        return False

    def attempt_group_hunting(self, t, nearby_npcs):
        """グループ狩猟の試行"""
        # 同じ集団のメンバーを優先
        same_group = []
        for npc in nearby_npcs:
            if (hasattr(self, 'boundary_system') and self.boundary_system and
                self.name in self.boundary_system.collective_boundaries.get('collective_group_north', set()) and
                npc.name in self.boundary_system.collective_boundaries.get('collective_group_north', set())) or \
               (self.name in self.boundary_system.collective_boundaries.get('collective_group_south', set()) and
                npc.name in self.boundary_system.collective_boundaries.get('collective_group_south', set())):
                same_group.append(npc)
        
        if len(same_group) < 1:
            return False
            
        # グループ狩猟を組織
        group_members = [self] + same_group[:2]  # 最大3人
        
        # 狩猟成功率を計算
        base_success = 0.4
        group_bonus = len(group_members) * 0.15
        success_rate = min(0.8, base_success + group_bonus)
        
        if random.random() < success_rate:
            # 成功
            meat_gained = 15.0 * len(group_members)  # グループサイズに応じて増加
            meat_per_member = meat_gained / len(group_members)
            
            # SSD Core Engine版のグループ処理
            if self.use_ssd_engine_social and self.ssd_enhanced_ref:
                hunt_group_id = self.ssd_enhanced_ref.create_hunt_group_v2(self.name, "group_hunt")
            
            for member in group_members:
                member.hunger = max(0, member.hunger - meat_per_member)
                member.fatigue = min(100.0, member.fatigue + 10.0)
                
                # 肉在庫に追加 - SSD Core Engine版
                if member.use_ssd_engine_social and member.ssd_enhanced_ref:
                    meat_id = member.ssd_enhanced_ref.create_meat_resource_v2(meat_per_member, member.name)
                    member.meat_inventory.append(meat_id)
                else:
                    member.meat_inventory.append(meat_per_member)
            
            print(f"🏹 T{t}: GROUP HUNT SUCCESS - {len(group_members)} members gained {meat_gained:.1f} meat")
            
            # グループ内の信頼を強化
            for m1 in group_members:
                for m2 in group_members:
                    if m1 != m2:
                        m1.trust_levels[m2.name] = min(1.0, m1.trust_levels.get(m2.name, 0.5) + 0.05)
            
            return True
        else:
            # 失敗
            for member in group_members:
                member.fatigue = min(100.0, member.fatigue + 15.0)
                
            print(f"🏹 T{t}: GROUP HUNT FAILED - {len(group_members)} members tired")
            return False

    def attempt_mutual_help(self, t, nearby_npcs):
        """相互支援の試行"""
        # 疲労が溜まっているNPCを探す
        tired_npcs = [npc for npc in nearby_npcs if npc.fatigue > 60]
        
        if tired_npcs:
            target = random.choice(tired_npcs)
            
            # 支援行動（休息を見守る、資源を探すなど）
            help_amount = 10.0
            target.fatigue = max(0, target.fatigue - help_amount)
            
            print(f"🤝 T{t}: MUTUAL HELP - {self.name} helped {target.name} reduce fatigue")
            
            # 信頼関係を強化
            self.trust_levels[target.name] = min(1.0, self.trust_levels.get(target.name, 0.5) + 0.08)
            target.trust_levels[self.name] = min(1.0, target.trust_levels.get(self.name, 0.5) + 0.08)
            
            log_event(self.log, {
                "t": t,
                "name": self.name,
                "action": "mutual_help",
                "target": target.name,
                "help_type": "fatigue_reduction"
            })
            
            return True
        return False

    def learn_from_crisis(self, t, crisis_type, current_location):
        """危機状況から学習し、将来の行動を改善する"""
        # 危機体験を記録
        crisis_experience = {
            "t": t,
            "type": crisis_type,
            "location": current_location,
            "severity": self.life_crisis
        }
        self.crisis_learning["crisis_experiences"].append(crisis_experience)

        # 信頼できるリソース場所を更新
        if crisis_type == "thirst":
            self.crisis_learning["trusted_water_sources"].add(current_location)
            self.crisis_learning["crisis_behaviors"]["resource_prioritization"]["water"] = min(1.0, 
                self.crisis_learning["crisis_behaviors"]["resource_prioritization"].get("water", 0.5) + 0.2)
            self.kappa["thirst"] = min(1.0, self.kappa.get("thirst", 0.1) + 0.1)  # 整合慣性を更新
        elif crisis_type == "hunger":
            if "hunting" in current_location.lower() or "forest" in current_location.lower():
                self.crisis_learning["trusted_hunting_grounds"].add(current_location)
                self.crisis_learning["crisis_behaviors"]["resource_prioritization"]["hunting"] = min(1.0, 
                    self.crisis_learning["crisis_behaviors"]["resource_prioritization"].get("hunting", 0.5) + 0.2)
                self.kappa["hunting"] = min(1.0, self.kappa.get("hunting", 0.1) + 0.1)  # 整合慣性を更新
            elif "berry" in current_location.lower() or "bush" in current_location.lower():
                self.crisis_learning["trusted_foraging_spots"].add(current_location)
                self.crisis_learning["crisis_behaviors"]["resource_prioritization"]["foraging"] = min(1.0, 
                    self.crisis_learning["crisis_behaviors"]["resource_prioritization"].get("foraging", 0.5) + 0.2)
                self.kappa["foraging"] = min(1.0, self.kappa.get("foraging", 0.1) + 0.1)  # 整合慣性を更新

        # 慎重さを高める
        self.crisis_learning["crisis_behaviors"]["caution_level"] = min(1.0, self.crisis_learning["crisis_behaviors"]["caution_level"] + 0.1)
        self.crisis_learning["crisis_behaviors"]["risk_aversion"] = min(1.0, self.crisis_learning["crisis_behaviors"]["risk_aversion"] + 0.05)
        self.kappa["caution"] = min(1.0, self.kappa.get("caution", 0.1) + 0.05)  # 整合慣性を更新

        # 経験値を更新
        self.experience["crisis_learning"] = min(1.0, self.experience.get("crisis_learning", 0.1) + 0.05)
        self.kappa["crisis_learning"] = min(1.0, self.kappa.get("crisis_learning", 0.1) + 0.05)  # 整合慣性を更新

        log_event(self.log, {
            "t": t,
            "name": self.name,
            "action": "crisis_learning",
            "crisis_type": crisis_type,
            "location": current_location,
            "new_caution": self.crisis_learning["crisis_behaviors"]["caution_level"],
            "new_risk_aversion": self.crisis_learning["crisis_behaviors"]["risk_aversion"]
        })

    def seek_help_for_hunger_or_thirst(self, t):
        """渇きや飢えの危険時に救援を求める"""
        if self.thirst > THIRST_DANGER_THRESHOLD or self.hunger > HUNGER_DANGER_THRESHOLD:
            # 近くのNPCを探す
            nearby_npcs = [
                npc
                for npc in self.roster.values()
                if npc != self
                and npc.alive
                and self.distance_to(npc.pos()) <= 8
                and (npc.water_inventory > 0 or npc.food_inventory > 0)
            ]

            if nearby_npcs:
                # 危険度に応じて信頼度の低いNPCにも頼む
                danger_level = max(
                    (self.thirst - THIRST_DANGER_THRESHOLD) / 40,
                    (self.hunger - HUNGER_DANGER_THRESHOLD) / 40,
                )

                # 熱量 E を考慮した調整
                self.E = danger_level * 1.5  # 危険度に比例して熱量を増加

                for npc in sorted(nearby_npcs, key=lambda n: self.get_trust_level(n.name), reverse=True):
                    trust_level = self.get_trust_level(npc.name)
                    adjusted_willingness = trust_level * 0.6 + self.E * 0.4 + 0.2

                    if probability_check(adjusted_willingness):
                        if self.thirst > THIRST_DANGER_THRESHOLD and npc.water_inventory > 0:
                            # 水を共有
                            shared_water = min(20, npc.water_inventory)
                            npc.water_inventory -= shared_water
                            self.thirst = max(0, self.thirst - shared_water)
                            print(f"🤝 T{t}: {npc.name} shared {shared_water} water with {self.name}")
                        elif self.hunger > HUNGER_DANGER_THRESHOLD and npc.food_inventory > 0:
                            # 食料を共有
                            shared_food = min(20, npc.food_inventory)
                            npc.food_inventory -= shared_food
                            self.hunger = max(0, self.hunger - shared_food)
                            print(f"🤝 T{t}: {npc.name} shared {shared_food} food with {self.name}")

                        # 信頼度を更新
                        self.update_trust(npc.name, "received_help", t, {"life_threatening": True})
                        npc.update_trust(self.name, "provided_help", t, {"life_threatening": True})

                        return True

        return False
