"""
NPC Physical Coherence Module - 物理基層レベルの整合慣性システム
生存欲求（渇水・飢餓）を整合慣性κとして統合実装

🧠 CORE THEORETICAL BREAKTHROUGH:
整合慣性κ (Coherence Inertia) = 記憶蓄積システム

【理論的洞察】
整合慣性κは単なる物理パラメータではなく、エージェントの「記憶の強度」を表現する:
- κ ↑ = より多くの記憶、より強い適応反応
- κ ↓ = 記憶が少ない、学習段階の状態  
- 過去の体験が整合慣性に蓄積され、将来の行動に影響
- 記憶が強いほど（κが大きいほど）、より早期に適応行動を開始

【実装における意味】
- 成功体験 → κ最適化、効率的行動パターンの記憶
- 失敗体験 → κ強化、早期警告システムの構築
- Structure Subjective Dynamics における主観的体験の物理的実装

この理解により、NPCは過去の体験を蓄積し、それに基づいて将来の行動を
動的に調整する真の学習システムが実現されました。
"""

import sys
import os
from collections import defaultdict

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import DEFAULT_KAPPA
from systems.utils import log_event

# ロギング制御フラグをインポート（実行時にmain.pyから利用可能）
try:
    from __main__ import VERBOSE_LOGGING
except ImportError:
    VERBOSE_LOGGING = True  # デフォルト値


class NPCPhysicalCoherenceMixin:
    """物理基層レベルの整合慣性ミックスイン"""
    
    def __init_physical_coherence__(self):
        """物理整合慣性システムの初期化"""
        # 物理基層整合慣性パラメータ
        self.physical_kappa = defaultdict(lambda: DEFAULT_KAPPA)
        
        # 生存整合慣性の初期値設定（生存効率重視）
        self.physical_kappa["thirst_coherence"] = 0.7  # 脱水防止を最優先
        self.physical_kappa["hunger_coherence"] = 0.6  # 飢餓防止も強化
        self.physical_kappa["fatigue_coherence"] = 0.4  # 疲労管理も重要
        self.physical_kappa["territory_coherence"] = 0.5  # 縄張り整合性向上
        self.physical_kappa["hunting_coherence"] = 0.7  # 狩り整合慣性（テスト強化版）
        
        # 物理基層動態パラメータ
        self.coherence_pressure = 0.0  # 整合圧力
        self.physical_tension = 0.0    # 物理的緊張度
        self.survival_resonance = 1.0  # 生存共鳴度
        
        # 縄張りとの整合性
        self.territory_coherence_factor = 1.0
        self.resource_coherence_map = {}  # リソース位置との整合性マップ
        
        # 経験学習システム
        self.survival_experiences = {
            "water_success": [],  # 水分補給成功の経験
            "water_failure": [],  # 水分補給失敗の経験
            "food_success": [],   # 食料獲得成功の経験
            "food_failure": [],   # 食料獲得失敗の経験
            "crisis_survival": [], # 危機回避成功の経験
            "near_death": []      # 瀕死経験
        }
        self.learned_thresholds = {
            "water_urgency": 50.0,  # 学習により調整される水分補給開始閾値
            "food_urgency": 50.0,   # 学習により調整される食料探索開始閾値
            "panic_threshold": 75.0 # 学習により調整されるパニック閾値
        }
        
    def update_physical_coherence(self, t):
        """物理基層整合慣性の更新"""
        # 1. 生存状態による整合慣性の計算
        self._calculate_survival_coherence()
        
        # 2. 縄張りとの整合性評価
        self._evaluate_territory_coherence()
        
        # 3. 物理的緊張度の更新
        self._update_physical_tension()
        
        # 4. 整合圧力の計算
        self._calculate_coherence_pressure()
        
        # 5. 生存共鳴度の更新
        self._update_survival_resonance()
        
        # デバッグログ
        if self.coherence_pressure > 0.3 or self.physical_tension > 0.5:
            print(f"🧬 T{t}: {self.name} 物理整合 - 圧力:{self.coherence_pressure:.2f} 緊張:{self.physical_tension:.2f} 共鳴:{self.survival_resonance:.2f}")
        
    def _calculate_survival_coherence(self):
        """生存状態による整合慣性の計算（記憶統合版）"""
        # 渇水整合慣性 = 渇水記憶の累積と現在状態の統合
        if self.thirst > 60:
            # 基本的な渇き強度
            thirst_intensity = min(1.0, self.thirst / 80.0)
            
            # 記憶による修正: 過去の失敗経験が整合慣性を強化
            memory_boost = self._get_memory_influence("thirst")
            
            # 統合された整合慣性 = 現在状態 × 記憶影響
            total_boost = (0.12 if self.thirst > 85 else 0.08) + memory_boost
            self.physical_kappa["thirst_coherence"] = min(1.0, 
                self.physical_kappa["thirst_coherence"] + thirst_intensity * total_boost)
        
        # 飢餓整合慣性 = 飢餓記憶の累積と現在状態の統合
        if self.hunger > 60:
            # 基本的な飢餓強度
            hunger_intensity = min(1.0, self.hunger / 90.0)
            
            # 記憶による修正: 過去の食料獲得経験が整合慣性を調整
            memory_boost = self._get_memory_influence("hunger")
            
            # 統合された整合慣性 = 現在状態 × 記憶影響
            total_boost = (0.10 if self.hunger > 95 else 0.06) + memory_boost
            self.physical_kappa["hunger_coherence"] = min(1.0,
                self.physical_kappa["hunger_coherence"] + hunger_intensity * total_boost)
        
        # 疲労整合慣性 - 疲労時の休息場所との整合性
        if hasattr(self, 'fatigue') and self.fatigue > 70:
            fatigue_intensity = min(1.0, self.fatigue / 100.0)
            boost = 0.06 if self.fatigue > 110 else 0.04
            self.physical_kappa["fatigue_coherence"] = min(1.0,
                self.physical_kappa["fatigue_coherence"] + fatigue_intensity * boost)
        
        # 狩り整合慣性 - 狩り成功・失敗による動的調整
        if hasattr(self, 'hunt_success_count') and hasattr(self, 'hunt_failure_count'):
            total_hunts = self.hunt_success_count + self.hunt_failure_count
            if total_hunts > 0:
                success_rate = self.hunt_success_count / total_hunts
                # 成功率に応じて狩り整合慣性を調整
                if success_rate > 0.6:  # 高成功率
                    self.physical_kappa["hunting_coherence"] = min(0.9, 
                        self.physical_kappa["hunting_coherence"] + 0.02)
                elif success_rate < 0.3:  # 低成功率
                    self.physical_kappa["hunting_coherence"] = max(0.1,
                        self.physical_kappa["hunting_coherence"] - 0.01)
        
        # 整合慣性の自然減衰を緩和（生存重視）
        for key in ["thirst_coherence", "hunger_coherence", "fatigue_coherence", "hunting_coherence"]:
            if key == "hunting_coherence":
                # 狩り整合慣性は未来志向のため減衰を大幅に抑制
                decay = 0.001 if self.physical_kappa[key] > 0.5 else 0.002
                min_value = 0.25  # 狩りの最小値を上げて持続性向上
            else:
                decay = 0.003 if self.physical_kappa[key] > 0.8 else 0.006  # 高レベルでは減衰を抑制
                min_value = 0.3
            self.physical_kappa[key] = max(min_value, self.physical_kappa[key] - decay)
    
    def _evaluate_territory_coherence(self):
        """縄張りとの整合性評価"""
        if not hasattr(self, 'territory') or not self.territory:
            self.territory_coherence_factor = 0.5  # 縄張りなしは低整合性
            return
        
        # 現在地と縄張り中心の距離に基づく整合性
        if hasattr(self.territory, 'center'):
            distance_to_center = self.distance_to(self.territory.center)
            territory_radius = getattr(self.territory, 'radius', 15)
            
            # 縄張り内での整合性は高い
            if distance_to_center <= territory_radius:
                self.territory_coherence_factor = min(1.5, 1.0 + (territory_radius - distance_to_center) / territory_radius * 0.5)
            else:
                # 縄張り外では整合性が低下
                self.territory_coherence_factor = max(0.3, 1.0 - (distance_to_center - territory_radius) / territory_radius * 0.3)
        
        # 縄張り整合慣性の更新
        coherence_change = (self.territory_coherence_factor - 1.0) * 0.02
        self.physical_kappa["territory_coherence"] = min(1.0, max(0.1,
            self.physical_kappa["territory_coherence"] + coherence_change))
    
    def _update_physical_tension(self):
        """物理的緊張度の更新"""
        # 生存欲求による緊張
        survival_tension = (
            min(1.0, self.thirst / 120.0) * 0.4 +
            min(1.0, self.hunger / 150.0) * 0.3 +
            (min(1.0, getattr(self, 'fatigue', 0) / 120.0) * 0.2)
        )
        
        # 縄張り不整合による緊張
        territory_tension = max(0, 1.0 - self.territory_coherence_factor) * 0.3
        
        # 整合慣性不足による緊張
        coherence_deficit = 1.0 - (
            self.physical_kappa["thirst_coherence"] +
            self.physical_kappa["hunger_coherence"] +
            self.physical_kappa["territory_coherence"] +
            self.physical_kappa["hunting_coherence"]
        ) / 4.0
        coherence_tension = max(0, coherence_deficit) * 0.2
        
        self.physical_tension = min(1.0, survival_tension + territory_tension + coherence_tension)
    
    def _calculate_coherence_pressure(self):
        """整合圧力の計算"""
        # 物理的緊張度から整合圧力を生成
        base_pressure = self.physical_tension
        
        # 複数要因の相互作用による圧力増幅
        interaction_factor = 1.0
        active_tensions = 0
        
        if self.thirst > 60:
            active_tensions += 1
        if self.hunger > 70:
            active_tensions += 1
        if hasattr(self, 'fatigue') and self.fatigue > 90:
            active_tensions += 1
        if self.territory_coherence_factor < 0.7:
            active_tensions += 1
        
        if active_tensions >= 2:
            interaction_factor = 1.0 + (active_tensions - 1) * 0.3
        
        self.coherence_pressure = min(1.0, base_pressure * interaction_factor)
    
    def _update_survival_resonance(self):
        """生存共鳴度の更新"""
        # 整合慣性が高いほど共鳴度が向上
        average_coherence = (
            self.physical_kappa["thirst_coherence"] +
            self.physical_kappa["hunger_coherence"] +
            self.physical_kappa["territory_coherence"] +
            self.physical_kappa["hunting_coherence"]
        ) / 4.0
        
        # 圧力が適度な時に最大共鳴
        pressure_factor = 1.0 - abs(self.coherence_pressure - 0.3) * 2.0
        pressure_factor = max(0.2, pressure_factor)
        
        self.survival_resonance = average_coherence * pressure_factor
    
    def get_coherence_driven_behavior_priority(self):
        """整合慣性に基づく行動優先度の取得"""
        print(f"COHERENCE_CALL: {getattr(self, 'name', 'Unknown')} calculating priorities")
        priorities = {}
        
        # 渇水整合慣性による水源探索優先度（生存重視）
        if self.physical_kappa["thirst_coherence"] > 0.3:  # 閾値を下げて早期発動
            urgency_factor = min(2.0, self.thirst / 60.0)  # より早期に高優先度
            water_priority = self.physical_kappa["thirst_coherence"] * urgency_factor
            priorities["seek_water"] = min(1.0, water_priority)
        
        # 飢餓整合慣性による食料探索優先度（生存重視）
        if self.physical_kappa["hunger_coherence"] > 0.3:  # 閾値を下げて早期発動
            urgency_factor = min(2.0, self.hunger / 70.0)  # より早期に高優先度
            food_priority = self.physical_kappa["hunger_coherence"] * urgency_factor
            priorities["seek_food"] = min(1.0, food_priority)
        
        # 縄張り整合慣性による縄張り行動優先度
        if self.physical_kappa["territory_coherence"] > 0.3:
            if self.territory_coherence_factor < 0.8:
                # 縄張り外にいる場合は戻る優先度が高い
                priorities["return_to_territory"] = min(1.0, 
                    self.physical_kappa["territory_coherence"] * (1.0 - self.territory_coherence_factor))
            else:
                # 縄張り内では強化・防衛の優先度
                priorities["strengthen_territory"] = min(0.5,
                    self.physical_kappa["territory_coherence"] * self.territory_coherence_factor * 0.3)
        
        # 狩り整合慣性による狩り行動優先度（未来予測強化版）
        hunting_coherence = self.physical_kappa["hunting_coherence"]
        hunt_need_factor = min(2.5, self.hunger / 50.0)  # より早期に狩りニーズが発生
        skill_factor = max(0.5, getattr(self, 'hunting_skill', 0.3))  # 最低スキルを保証
        
        # SSD Core Engine未来予測による大型獲物への動機強化
        future_motivation_factor = 1.0
        
        # SSD Enhanced NPCのエンジンアクセス
        ssd_engine = None
        if hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref:
            ssd_engine = self.ssd_enhanced_ref.engine
        
        if ssd_engine:
            try:
                # SSD Core Engine の予測システムを使用
                # 食料オブジェクトの将来状態を予測
                food_prediction = ssd_engine.predict_future_state('food_resources', steps_ahead=10)
                # 危機条件検出
                crisis_info = ssd_engine.detect_crisis_conditions()
                
                # 食料不足リスクを評価（より敏感な判定）
                food_scarcity_risk = 1.2  # ベースライン向上
                if hasattr(food_prediction, 'crisis_level'):
                    if food_prediction.crisis_level == 'high':
                        food_scarcity_risk = 2.0
                    elif food_prediction.crisis_level == 'medium':
                        food_scarcity_risk = 1.6
                
                # 環境食料密度から予測的価値を評価
                if hasattr(food_prediction, 'properties') and food_prediction.properties:
                    density = food_prediction.properties.get('food_density', 0.005)
                    if density < 0.002:
                        food_scarcity_risk = max(food_scarcity_risk, 1.8)
                    elif density < 0.004:
                        food_scarcity_risk = max(food_scarcity_risk, 1.4)
                
                # 危機情報から大型獲物の価値を評価
                large_prey_value = 1.3  # ベースライン向上（予測的狩り動機）
                if crisis_info and 'food_shortage' in crisis_info.get('detected_crises', []):
                    large_prey_value = 1.8  # 食料危機時は大型獲物の価値が高い
                
                # 時間経過による予測的動機（長期的視点）
                time_factor = min(1.5, 1.0 + (getattr(self, 'age', 0) * 0.01))  # 経験による先見性
                
                # SSD予測統合動機ファクター
                future_motivation_factor = 1.0 + (food_scarcity_risk - 1.0) * 0.6 + (large_prey_value - 1.0) * 0.7 + (time_factor - 1.0) * 0.3
                future_motivation_factor = min(3.2, future_motivation_factor)  # SSD使用時はより高い上限
                
            except (AttributeError, TypeError, KeyError) as e:
                # SSD予測システムエラー時は簡易計算にフォールバック
                future_motivation_factor = self._calculate_simple_future_hunting_motivation()
        else:
            # SSDエンジンがない場合の簡易予測システム
            future_motivation_factor = self._calculate_simple_future_hunting_motivation()
        
        # 強制的に狩り優先度を計算（未来予測統合版）
        hunt_priority = hunting_coherence * hunt_need_factor * skill_factor * future_motivation_factor * 1.2
        priorities["hunt"] = min(1.0, hunt_priority)
        
        # デバッグ出力（SSD予測統合版）
        ssd_used = "SSD" if (hasattr(self, 'ssd_enhanced_ref') and self.ssd_enhanced_ref) else "Simple"
        if VERBOSE_LOGGING:
            print(f"DEBUG_HUNT: {getattr(self, 'name', 'Unknown')} coherence:{hunting_coherence:.2f} need:{hunt_need_factor:.2f} skill:{skill_factor:.2f} future:{future_motivation_factor:.2f} ({ssd_used}) priority:{hunt_priority:.3f}")
        
        return priorities
    
    def _calculate_simple_future_hunting_motivation(self):
        """未来予測エンジンがない場合の簡易狩り動機計算"""
        motivation_factor = 1.0
        
        # 現在の飢餓状況から将来のリスクを推定
        hunger_trend_risk = min(1.5, self.hunger / 40.0)  # 飢餓進行リスク
        
        # 季節要因（冬の接近など）を考慮
        seasonal_factor = 1.0
        if hasattr(self.env, 'current_season'):
            if self.env.current_season in ['Autumn', 'Winter']:
                seasonal_factor = 1.4  # 冬への備えが必要
        
        # 環境の食料密度から大型獲物の価値を推定
        food_scarcity_factor = 1.0
        if hasattr(self.env, 'berry_patches') and hasattr(self.env, 'world_size'):
            total_berries = sum(len(patches) for patches in self.env.berry_patches.values())
            area = self.env.world_size ** 2
            food_density = total_berries / area if area > 0 else 0.01
            # 食料密度が低いほど狩りの価値が高い
            if food_density < 0.002:  # 低密度閾値
                food_scarcity_factor = 1.6
            elif food_density < 0.005:
                food_scarcity_factor = 1.3
        
        # 過去の狩り成功率から将来性を評価
        hunt_success_factor = 1.0
        if hasattr(self, 'hunt_success_count') and hasattr(self, 'hunt_failure_count'):
            total_hunts = self.hunt_success_count + self.hunt_failure_count
            if total_hunts > 0:
                success_rate = self.hunt_success_count / total_hunts
                # 成功率が高いほど将来の狩りに意欲的
                hunt_success_factor = 1.0 + (success_rate * 0.8)
        
        # 総合的な未来動機ファクター
        motivation_factor = 1.0 + (
            (hunger_trend_risk - 1.0) * 0.5 +
            (seasonal_factor - 1.0) * 0.6 +
            (food_scarcity_factor - 1.0) * 0.7 +
            (hunt_success_factor - 1.0) * 0.4
        )
        
        return min(2.2, max(0.8, motivation_factor))  # 0.8-2.2倍の範囲
    
    def apply_coherence_to_movement(self, target, base_speed=2):
        """整合慣性を考慮した移動調整（生存重視強化版）"""
        # 整合慣性レベルが高いほど移動効率向上（生存重視）
        coherence_bonus = (
            self.physical_kappa["thirst_coherence"] * 0.8 +  # 水源探索を最優先
            self.physical_kappa["hunger_coherence"] * 0.6 +  # 食料探索も強化
            self.physical_kappa["territory_coherence"] * 0.3
        )
        
        # 物理的緊張度による緊急時速度大幅向上
        tension_factor = 1.0 + self.physical_tension * 1.5  # 緊急時の速度向上を倍増
        
        # 生存危機時の特別ボーナス
        crisis_bonus = 1.0
        if self.thirst > 80 or self.hunger > 90:
            crisis_bonus = 2.2  # 危機時は大幅速度向上
        elif self.thirst > 65 or self.hunger > 75:
            crisis_bonus = 1.6  # 準危機時も速度向上
        
        # 整合圧力による追加ボーナス
        pressure_boost = 1.0 + self.coherence_pressure * 0.8
        
        adjusted_speed = base_speed * (1.0 + coherence_bonus) * tension_factor * crisis_bonus * pressure_boost
        return min(6, int(adjusted_speed))  # 最大6倍まで向上
    
    def get_physical_coherence_state(self):
        """物理整合慣性状態の取得（デバッグ用）"""
        return {
            "physical_kappa": dict(self.physical_kappa),
            "coherence_pressure": self.coherence_pressure,
            "physical_tension": self.physical_tension,
            "survival_resonance": self.survival_resonance,
            "territory_coherence_factor": self.territory_coherence_factor,
            "learned_thresholds": self.learned_thresholds.copy()
        }
    
    def record_survival_experience(self, action_type, success, context):
        """生存行動の経験を記録"""
        experience = {
            "thirst_level": getattr(self, 'thirst', 0),
            "hunger_level": getattr(self, 'hunger', 0),
            "fatigue_level": getattr(self, 'fatigue', 0),
            "success": success,
            "context": context,
            "timestamp": getattr(self, '_current_tick', 0)
        }
        
        if action_type == "water":
            if success:
                self.survival_experiences["water_success"].append(experience)
            else:
                self.survival_experiences["water_failure"].append(experience)
        elif action_type == "food":
            if success:
                self.survival_experiences["food_success"].append(experience)
            else:
                self.survival_experiences["food_failure"].append(experience)
        
        # 経験に基づく閾値調整
        self._adjust_thresholds_from_experience(action_type)
    
    def record_crisis_experience(self, survived=True):
        """危機・瀕死経験を記録"""
        experience = {
            "thirst_level": getattr(self, 'thirst', 0),
            "hunger_level": getattr(self, 'hunger', 0),
            "survived": survived,
            "timestamp": getattr(self, '_current_tick', 0)
        }
        
        if survived and (self.thirst > 80 or self.hunger > 90):
            self.survival_experiences["crisis_survival"].append(experience)
            print(f"📚 {self.name}: Crisis survival experience recorded (T:{self.thirst:.1f} H:{self.hunger:.1f})")
        elif not survived:
            self.survival_experiences["near_death"].append(experience)
    
    def _adjust_thresholds_from_experience(self, action_type):
        """経験に基づく閾値調整"""
        if action_type == "water":
            successes = self.survival_experiences["water_success"]
            failures = self.survival_experiences["water_failure"]
            
            if len(failures) > 0 and len(successes) > 0:
                # 失敗時の平均渇きレベルより早めに行動開始
                avg_failure_thirst = sum(exp["thirst_level"] for exp in failures[-5:]) / min(5, len(failures))
                avg_success_thirst = sum(exp["thirst_level"] for exp in successes[-5:]) / min(5, len(successes))
                
                # 失敗を避けるため、より早期に行動開始
                new_threshold = min(avg_failure_thirst - 5, avg_success_thirst - 2)
                self.learned_thresholds["water_urgency"] = max(30.0, min(70.0, new_threshold))
                
                if len(failures) % 3 == 0:  # 3回に1回調整をログ
                    print(f"💡 {self.name}: Water urgency learned -> {self.learned_thresholds['water_urgency']:.1f}")
        
        elif action_type == "food":
            successes = self.survival_experiences["food_success"]
            failures = self.survival_experiences["food_failure"]
            
            if len(failures) > 0 and len(successes) > 0:
                avg_failure_hunger = sum(exp["hunger_level"] for exp in failures[-5:]) / min(5, len(failures))
                avg_success_hunger = sum(exp["hunger_level"] for exp in successes[-5:]) / min(5, len(successes))
                
                new_threshold = min(avg_failure_hunger - 5, avg_success_hunger - 2)
                self.learned_thresholds["food_urgency"] = max(30.0, min(70.0, new_threshold))
                
                if len(failures) % 3 == 0:
                    print(f"💡 {self.name}: Food urgency learned -> {self.learned_thresholds['food_urgency']:.1f}")
    
    def get_learned_urgency_threshold(self, resource_type):
        """学習済み緊急度閾値を取得"""
        if resource_type == "water":
            return self.learned_thresholds["water_urgency"]
        elif resource_type == "food":
            return self.learned_thresholds["food_urgency"]
        else:
            return 50.0  # デフォルト
    
    def _get_memory_influence(self, need_type):
        """記憶による整合慣性への影響計算"""
        if need_type == "thirst":
            successes = len(self.survival_experiences.get("water_success", []))
            failures = len(self.survival_experiences.get("water_failure", []))
        elif need_type == "hunger":
            successes = len(self.survival_experiences.get("food_success", []))
            failures = len(self.survival_experiences.get("food_failure", []))
        else:
            return 0.0
        
        total_experiences = successes + failures
        if total_experiences == 0:
            return 0.0  # 記憶なし = 影響なし
        
        # 失敗記憶が多いほど整合慣性を強化（早期行動促進）
        failure_ratio = failures / total_experiences
        
        # 成功記憶は適度な整合慣性を維持
        success_ratio = successes / total_experiences
        
        # 記憶による整合慣性修正
        # 失敗記憶 → より強い整合慣性（危険回避）
        # 成功記憶 → 適度な整合慣性（効率的行動）
        memory_influence = (failure_ratio * 0.15) - (success_ratio * 0.05)
        
        # 経験数による重み（多くの経験 = より信頼できる記憶）
        experience_weight = min(1.0, total_experiences / 10.0)  # 10回で最大重み
        
        final_influence = memory_influence * experience_weight
        
        # デバッグ情報（重要な記憶影響時のみ）
        if abs(final_influence) > 0.05:
            print(f"🧠 {self.name}: Memory influence on {need_type} = {final_influence:.3f} (S:{successes}, F:{failures})")
        
        return final_influence
    
    def get_coherence_as_memory_state(self):
        """整合慣性を記憶状態として取得"""
        return {
            "survival_memories": {
                "thirst_memory_strength": self.physical_kappa["thirst_coherence"],
                "hunger_memory_strength": self.physical_kappa["hunger_coherence"],
                "territory_memory_strength": self.physical_kappa["territory_coherence"],
                "hunting_memory_strength": self.physical_kappa["hunting_coherence"]
            },
            "experience_count": {
                "water_experiences": len(self.survival_experiences.get("water_success", [])) + len(self.survival_experiences.get("water_failure", [])),
                "food_experiences": len(self.survival_experiences.get("food_success", [])) + len(self.survival_experiences.get("food_failure", [])),
                "crisis_experiences": len(self.survival_experiences.get("crisis_survival", []))
            },
            "learned_adaptations": self.learned_thresholds.copy(),
            "memory_coherence_pressure": self.coherence_pressure
        }