"""
NPC Modular Base - 分割されたNPCクラス
"""

import sys
import os
import random
from typing import Dict, Any, Tuple

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 各ミックスインをインポート
from .npc_movement import NPCMovementMixin
from .npc_survival import NPCSurvivalMixin
from .npc_hunting import NPCHuntingMixin
from .npc_cooperation import NPCCooperationMixin
from .npc_territory import NPCTerritoryMixin
from .npc_prediction import NPCPredictionMixin
from .npc_core import NPCCoreMixin
from .npc_physical_coherence import NPCPhysicalCoherenceMixin

# 完全独立版 - MonolithNPCから脱却
class NPC(
    NPCPhysicalCoherenceMixin,
    NPCMovementMixin,
    NPCSurvivalMixin,
    NPCHuntingMixin,
    NPCCooperationMixin,
    NPCTerritoryMixin,
    NPCPredictionMixin,
    NPCCoreMixin
):
    """分割されたNPCクラス - 段階的移行用
    
    各ミックスインが元のメソッドをオーバーライドし、
    段階的に機能を分離していく。
    """
    
    def __init__(self, name, preset, env, roster, start_pos, boundary_system=None):
        import random
        from collections import defaultdict
        
        # 基本属性
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

        # 物理基層整合慣性システムの初期化
        self.__init_physical_coherence__()
        self.log = []

        # 性格特性（SSD理論）
        self.curiosity = preset.get("curiosity", 0.5)
        self.sociability = preset.get("sociability", 0.5)
        self.risk_tolerance = preset.get("risk_tolerance", 0.5)
        self.empathy = preset.get("empathy", 0.6)

        # SSD理論パラメータ
        try:
            from config import DEFAULT_KAPPA, DEFAULT_TEMPERATURE
        except ImportError:
            DEFAULT_KAPPA = 1.0
            DEFAULT_TEMPERATURE = 1.0
            
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
        try:
            from systems.future_prediction import FuturePredictionEngine
            self.future_engine = FuturePredictionEngine(self)
        except ImportError:
            self.future_engine = None

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
        
        # 分割版フラグ
        self._is_modularized = True
        
    def _initialize_knowledge(self):
        """初期知識の設定"""
        # 近くのリソースを初期知識として追加
        try:
            # 開始位置の近くのリソースを発見
            for cave_name, cave_pos in self.env.caves.items():
                if self.distance_to(cave_pos) <= 20:
                    self.knowledge_caves.add(cave_name)
                    
            for water_pos in self.env.water:
                if self.distance_to(water_pos) <= 15:
                    self.knowledge_water.add(water_pos)
                    
            for berry_pos in self.env.berries:
                if self.distance_to(berry_pos) <= 10:
                    self.knowledge_berries.add(berry_pos)
        except Exception:
            # 環境アクセスエラーは無視
            pass
        
    def get_module_status(self):
        """分割状況のステータス"""
        modules = {
            "movement": "NPCMovementMixin" in [cls.__name__ for cls in self.__class__.__mro__],
            "survival": "NPCSurvivalMixin" in [cls.__name__ for cls in self.__class__.__mro__],
            "hunting": "NPCHuntingMixin" in [cls.__name__ for cls in self.__class__.__mro__],
            "cooperation": "NPCCooperationMixin" in [cls.__name__ for cls in self.__class__.__mro__],
            "territory": "NPCTerritoryMixin" in [cls.__name__ for cls in self.__class__.__mro__],
            "prediction": "NPCPredictionMixin" in [cls.__name__ for cls in self.__class__.__mro__]
        }
        
        return {
            "modularized": True,
            "base_class": "MonolithNPC",
            "active_mixins": modules,
            "migration_status": "partial - gradual implementation"
        }
    
    # === 基本的な狩猟メソッド（NPCレベル） ===
    
    def evaluate_hunt_opportunity(self, target_prey: Dict[str, Any]) -> float:
        """狩猟機会の評価（SSD統合意思決定）"""
        # SSD拡張NPCが存在する場合はSSD経由で判定
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            return self.ssd_enhanced_ref.evaluate_hunt_opportunity_ssd(target_prey)
        
        # フォールバック: 基本評価
        try:
            prey_size = target_prey.get('size', 1.0)
            own_strength = getattr(self, 'hunting_skill', 0.5)
            
            # 基本成功見込み
            strength_ratio = own_strength / prey_size
            base_opportunity = min(0.8, strength_ratio * 0.7)
            
            # 体力・状態による調整
            health_factor = (100 - self.hunger) / 100.0
            stamina_factor = (100 - self.fatigue) / 100.0
            
            return base_opportunity * health_factor * stamina_factor
            
        except Exception:
            return 0.3  # デフォルト値
    
    def can_form_hunt_group(self) -> bool:
        """狩猟グループ形成可能かの判定（SSD統合意思決定）"""
        # SSD拡張NPCが存在する場合はSSD経由で判定
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            return self.ssd_enhanced_ref.can_form_hunt_group_ssd()
        
        # フォールバック: 基本判定
        return (self.alive and 
                self.hunger < 80 and 
                self.fatigue < 90 and
                hasattr(self, 'hunting_skill') and 
                self.hunting_skill > 0.2)
    
    def get_hunting_coordination_with(self, other_npc) -> float:
        """他のNPCとの狩猟協調性評価"""
        try:
            # 能力の類似性
            skill_diff = abs(getattr(self, 'hunting_skill', 0.5) - 
                           getattr(other_npc, 'hunting_skill', 0.5))
            skill_compatibility = 1.0 - skill_diff
            
            # 信頼関係
            trust_level = self.trust_levels.get(other_npc.name, 0.5)
            
            # 距離による協調性
            distance = self.distance_to(other_npc.pos)
            distance_factor = max(0.3, 1.0 - distance * 0.05)
            
            return (skill_compatibility * 0.4 + trust_level * 0.4 + distance_factor * 0.2)
            
        except Exception:
            return 0.5
    
    # === 基本的な縄張りメソッド（NPCレベル） ===
    
    def assess_territory_value(self, center_pos: Tuple[int, int], radius: int = 5) -> float:
        """縄張り候補地の価値評価（SSD統合意思決定）"""
        # SSD拡張NPCが存在する場合はSSD経由で判定
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            return self.ssd_enhanced_ref.assess_territory_value_ssd(center_pos, radius)
        
        # フォールバック: 基本評価
        try:
            value_score = 0.0
            
            # 知っているリソースとの距離
            for cave_name in self.knowledge_caves:
                if hasattr(self.env, 'caves') and cave_name in self.env.caves:
                    cave_pos = self.env.caves[cave_name]
                    distance = self.distance_to_pos(center_pos, cave_pos)
                    if distance <= radius:
                        value_score += 0.3  # 洞窟は高価値
            
            for water_pos in self.knowledge_water:
                distance = self.distance_to_pos(center_pos, water_pos)
                if distance <= radius:
                    value_score += 0.2  # 水場
            
            for berry_pos in self.knowledge_berries:
                distance = self.distance_to_pos(center_pos, berry_pos)
                if distance <= radius:
                    value_score += 0.1  # ベリー
            
            return min(1.0, value_score)
            
        except Exception:
            return 0.3  # デフォルト値
    
    def should_defend_territory(self, intruder_npc) -> bool:
        """縄張り防衛すべきかの判定（SSD統合意思決定）"""
        # SSD拡張NPCが存在する場合はSSD経由で判定
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            return self.ssd_enhanced_ref.should_defend_territory_ssd(intruder_npc)
        
        # フォールバック: 基本判定
        if not self.territory:
            return False
        
        # 基本的な防衛条件
        return (self.alive and 
                self.fatigue < 85 and
                intruder_npc.name not in self.trust_levels or 
                self.trust_levels.get(intruder_npc.name, 0) < 0.7)
    
    # === 基本的な探索メソッド（NPCレベル） ===
    
    def calculate_exploration_motivation(self) -> float:
        """探索動機の計算（SSD統合意思決定）"""
        # SSD拡張NPCが存在する場合はSSD経由で判定
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            return self.ssd_enhanced_ref.calculate_exploration_motivation_ssd()
        
        # フォールバック: 基本計算
        try:
            # 生存プレッシャー
            survival_pressure = (self.hunger + self.thirst + self.fatigue) / 300.0
            
            # 好奇心による動機
            curiosity_drive = self.curiosity * 0.6
            
            # リソース枯渇による必要性
            resource_scarcity = 1.0 - (len(self.knowledge_caves) + 
                                      len(self.knowledge_water) + 
                                      len(self.knowledge_berries)) * 0.1
            resource_scarcity = max(0.0, resource_scarcity)
            
            return min(1.0, survival_pressure + curiosity_drive + resource_scarcity * 0.3)
            
        except Exception:
            return 0.4  # デフォルト値
    
    def should_explore_leap(self) -> bool:
        """探索跳躍すべきかの判定（SSD統合意思決定）"""
        # SSD拡張NPCが存在する場合はSSD経由で判定
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            return self.ssd_enhanced_ref.should_explore_leap_ssd()
        
        # フォールバック: 基本判定
        exploration_motivation = self.calculate_exploration_motivation()
        current_crisis = getattr(self, 'life_crisis', 0.0)
        
        # 危機状況または高い探索動機で跳躍判定
        leap_threshold = 0.7 - current_crisis * 0.2
        return exploration_motivation > leap_threshold
    
    def distance_to_pos(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """2点間の距離計算ヘルパー"""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
    
    # === SSD統合行動制御 ===
    
    def act(self):
        """SSD統合行動実行 - 全NPCの判断をSSD経由で統一"""
        # SSD拡張NPCが存在する場合はSSD統一意思決定
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            decision = self.ssd_enhanced_ref.make_unified_decision_ssd()
            self._execute_ssd_decision(decision)
        else:
            # フォールバック: 基本的な生存行動
            self._execute_basic_survival()
    
    def _execute_ssd_decision(self, decision: Dict[str, Any]):
        """SSD決定の実行"""
        action_type = decision.get("action", "survival")
        
        try:
            if action_type == "survival":
                self._execute_survival_action()
            elif action_type == "exploration":
                self._execute_exploration_action()
            elif action_type == "hunting":
                self._execute_hunting_action()
            elif action_type == "social":
                self._execute_social_action()
            elif action_type == "territorial":
                self._execute_territorial_action()
            else:
                self._execute_basic_survival()
                
        except Exception as e:
            # 実行エラー時はフォールバック
            self._execute_basic_survival()
    
    def _execute_survival_action(self):
        """生存行動の実行"""
        # 最も緊急なニーズに対応
        if self.thirst > self.hunger and self.thirst > 50:
            self._seek_water()
        elif self.hunger > 60:
            self._seek_food()
        elif self.fatigue > 80:
            self._rest()
        else:
            self._random_move()
    
    def _execute_exploration_action(self):
        """探索行動の実行"""
        if self.should_explore_leap():
            # 大きな探索跳躍
            self._make_exploration_leap()
        else:
            # 通常の探索移動
            self._explore_nearby()
    
    def _execute_hunting_action(self):
        """狩猟行動の実行"""
        if self.can_form_hunt_group():
            # グループ狩猟の試行
            self._attempt_group_hunting()
        else:
            # 単独狩猟の試行
            self._attempt_solo_hunting()
    
    def _execute_social_action(self):
        """社会的行動の実行"""
        nearby_npcs = self._find_nearby_npcs()
        if nearby_npcs:
            self._interact_with_npcs(nearby_npcs)
        else:
            self._seek_social_contact()
    
    def _execute_territorial_action(self):
        """縄張り行動の実行"""
        if hasattr(self, 'territory') and self.territory:
            self._maintain_territory()
        else:
            self._establish_territory()
    
    def _execute_basic_survival(self):
        """基本的な生存行動（フォールバック）"""
        # 最低限の生存行動
        if self.hunger > 80:
            self._seek_food()
        elif self.thirst > 70:
            self._seek_water()
        elif self.fatigue > 90:
            self._rest()
        else:
            self._random_move()
    
    # === 基本行動実装ヘルパー（簡易版） ===
    
    def _seek_water(self):
        """水を探す"""
        if self.knowledge_water:
            # 知っている水場へ移動
            target_water = min(self.knowledge_water, key=lambda w: self.distance_to(w))
            self._move_towards(target_water)
        else:
            self._explore_for_water()
    
    def _seek_food(self):
        """食物を探す"""
        if self.knowledge_berries:
            # 知っているベリー場へ移動
            target_berry = min(self.knowledge_berries, key=lambda b: self.distance_to(b))
            self._move_towards(target_berry)
        else:
            self._explore_for_food()
    
    def _rest(self):
        """休息"""
        self.fatigue = max(0, self.fatigue - 5)
    
    def _random_move(self):
        """ランダム移動"""
        if hasattr(self, 'env'):
            new_x = max(0, min(self.env.width-1, self.x + random.randint(-3, 3)))
            new_y = max(0, min(self.env.height-1, self.y + random.randint(-3, 3)))
            self.x, self.y = new_x, new_y
    
    def _move_towards(self, target_pos):
        """目標位置への移動"""
        if hasattr(self, 'env'):
            dx = 1 if target_pos[0] > self.x else -1 if target_pos[0] < self.x else 0
            dy = 1 if target_pos[1] > self.y else -1 if target_pos[1] < self.y else 0
            
            new_x = max(0, min(self.env.width-1, self.x + dx))
            new_y = max(0, min(self.env.height-1, self.y + dy))
            self.x, self.y = new_x, new_y
    
    def _find_nearby_npcs(self):
        """近隣NPCの発見"""
        if not hasattr(self, 'env'):
            return []
        
        nearby = []
        for other_npc in getattr(self.env, 'npcs', []):
            if other_npc != self and self.distance_to(other_npc.pos) <= 15:
                nearby.append(other_npc)
        return nearby
    
    # プレースホルダーメソッド（詳細実装は各ミックスインで）
    def _make_exploration_leap(self): self._random_move()
    def _explore_nearby(self): self._random_move()
    def _attempt_group_hunting(self): pass
    def _attempt_solo_hunting(self): pass
    def _interact_with_npcs(self, npcs): pass
    def _seek_social_contact(self): self._random_move()
    def _maintain_territory(self): pass
    def _establish_territory(self): pass
    def _explore_for_water(self): self._random_move()
    def _explore_for_food(self): self._random_move()

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