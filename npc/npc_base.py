"""
NPC Base Module - SSD Core Engine Integrated NPCs

🤖 SSD INTEGRATION PRINCIPLE: NPCs are designed around ssd_core_engine.
Each NPC should receive a dedicated SSD engine instance and use SSD
decision-making systems rather than hardcoded behavior logic.

NPCの基本クラスと初期化 - SSD Core Engine統合版
"""

import random
import math
from collections import defaultdict
import sys
import os

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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
from systems.future_prediction import FuturePredictionEngine
from systems.utils import distance_between, probability_check, log_event

# 各モジュールから必要なミックスインをインポート
from .npc_movement import NPCMovementMixin
from .npc_survival import NPCSurvivalMixin
from .npc_hunting import NPCHuntingMixin
from .npc_cooperation import NPCCooperationMixin
from .npc_territory import NPCTerritoryMixin
from .npc_prediction import NPCPredictionMixin
from .npc_physical_coherence import NPCPhysicalCoherenceMixin


class NPC(
    NPCMovementMixin,
    NPCSurvivalMixin,
    NPCHuntingMixin,
    NPCCooperationMixin,
    NPCTerritoryMixin,
    NPCPredictionMixin,
    NPCPhysicalCoherenceMixin
):
    """SSD理論に基づくNPCエージェント - 基本クラス"""

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
        
        # 危機感ヒートシステム
        self.survival_heat = 0.0  # 生存危機感の蓄積レベル (0-100)
        self.crisis_threshold = 30.0  # 危機感が行動に影響し始める閾値
        self.panic_threshold = 60.0   # パニックレベル
        self.desperation_threshold = 80.0  # 絶望レベル

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
        
        # 物理基層整合慣性システムの初期化
        if hasattr(self, '__init_physical_coherence__'):
            self.__init_physical_coherence__()

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
        
        lambda_param = TERRITORY_SETTINGS.get("I_decay_rate", 0.02)
        eta_r = TERRITORY_SETTINGS.get("reinforcement_rate", 0.05)
        eta_m = TERRITORY_SETTINGS.get("memory_rate", 0.03)

        I_before = self.I_by_target[target_id]
        I_after = (1 - lambda_param) * I_before + eta_r * r_val + eta_m * m_val
        delta = I_after - I_before

        self.I_by_target[target_id] = max(0.0, min(1.0, I_after))

        return I_before, I_after, delta

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

    def step_metabolism(self, tick):
        """基本的な新陳代謝処理"""
        # 基本代謝率（減少版：環境圧緩和）
        base_hunger_rate = 0.8  # 1.5 → 0.8 (-47%)
        base_thirst_rate = 0.9  # 1.8 → 0.9 (-50%)
        base_fatigue_rate = 0.5  # 1.0 → 0.5 (-50%)
        
        # 季節・環境による補正
        temp_stress = 0.0
        if hasattr(self.env, 'seasonal_modifier'):
            temp_stress = self.env.seasonal_modifier.get('temperature_stress', 0.0)
        
        # 代謝増加（高温時）
        hunger_rate = base_hunger_rate * (1.0 + temp_stress * 0.3)
        thirst_rate = base_thirst_rate * (1.0 + temp_stress * 0.5)  # 渇きは温度の影響大
        fatigue_rate = base_fatigue_rate * (1.0 + temp_stress * 0.2)
        
        # 状態更新
        self.hunger = min(100, self.hunger + hunger_rate)
        self.thirst = min(100, self.thirst + thirst_rate)
        self.fatigue = min(100, self.fatigue + fatigue_rate)

    def gain_experience(self, experience_type, amount, t):
        """経験値の獲得"""
        if experience_type in self.experience:
            old_value = self.experience[experience_type]
            self.experience[experience_type] = min(10.0, old_value + amount)
            
            # SSD理論：経験の蓄積は整合慣性κとして機能
            kappa_key = f"experience_{experience_type}"
            if kappa_key not in self.kappa:
                self.kappa[kappa_key] = 0.1
            self.kappa[kappa_key] = min(1.0, self.kappa[kappa_key] + amount * 0.1)