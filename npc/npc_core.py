"""
NPCCoreMixin - NPC基本機能ミックスイン

MonolithNPCから完全独立を目指すため、
基本的なライフサイクルとコア機能を提供します。
"""
import math
import random
import sys
import os
from typing import Tuple, Any, Dict

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import EXPERIENCE_SYSTEM_SETTINGS


class NPCCoreMixin:
    """
    NPCのコア機能を提供するミックスイン
    
    以下の基本機能を含む：
    - step(): メインライフサイクル
    - pos関連メソッド
    - 死亡処理
    - 緊急サバイバル
    """
    
    def step(self, current_tick=None) -> None:
        """
        NPCの1ステップ実行 - MonolithNPC互換版
        
        Args:
            current_tick: 現在のシミュレーションティック
        """
        t = current_tick or 0
        
        # 生存チェック
        if hasattr(self, 'alive') and not self.alive:
            return
            
        # 基本的な劣化（大幅緩和版）
        if hasattr(self, 'hunger'):
            self.hunger += 0.5  # 1.0→0.5に大幅緩和（半分の速度）
        if hasattr(self, 'thirst'):
            self.thirst += 0.7  # 1.5→0.7に大幅緩和（半分以下の速度）
        if hasattr(self, 'fatigue'):
            self.fatigue = min(150.0, self.fatigue + 0.5)  # 疲労蓄積も半分に
        
        # 物理基層整合慣性システムの更新
        if hasattr(self, 'update_physical_coherence'):
            self.update_physical_coherence(t)
            
        # 危機感ヒートの計算・更新（物理整合慣性と統合）
        if hasattr(self, 'survival_heat'):
            self.update_survival_heat()
            
        # 生存チェック（緩和された閾値）
        death_occurred = False
        if hasattr(self, 'thirst') and self.thirst > 300:  # 220→300にさらに緩和
            death_occurred = True
            cause = "dehydration"
        elif hasattr(self, 'hunger') and self.hunger > 240:  # 200→240に緩和
            death_occurred = True
            cause = "starvation"
            
        if death_occurred:
            if hasattr(self, 'alive'):
                self.alive = False
            print(f"💀 T{t}: {getattr(self, 'name', 'NPC')} died from {cause}! (Hunger: {getattr(self, 'hunger', 0):.1f}, Thirst: {getattr(self, 'thirst', 0):.1f})")
            return
            
        # 物理基層整合慣性ベース行動システム
        if hasattr(self, 'get_coherence_driven_behavior_priority'):
            # SSDシステムは既に詳細ログを持っているので、VERBOSE_LOGGINGチェック不要
            # print(f"BEHAVIOR_SYSTEM: {getattr(self, 'name', 'Unknown')} using COHERENCE system")
            self.execute_coherence_based_behavior(t)
        elif hasattr(self, 'survival_heat'):
            # フォールバック: ヒートベースシステム
            # print(f"BEHAVIOR_SYSTEM: {getattr(self, 'name', 'Unknown')} using HEAT system")
            self.execute_heat_based_behavior(t)
        else:
            # フォールバック: 従来システム
            # print(f"BEHAVIOR_SYSTEM: {getattr(self, 'name', 'Unknown')} using TRADITIONAL system")
            self.execute_traditional_behavior(t)
                
        # 経験値獲得
        self.gain_experience(0.1, "survival")
    
    def update_survival_heat(self):
        """危機感ヒートの更新ロジック"""
        # ヒートの基本減衰（時間とともに自然回復）
        heat_decay = 0.5
        self.survival_heat = max(0, self.survival_heat - heat_decay)
        
        # 生存状況に基づくヒート蓄積
        heat_increase = 0
        
        # 空腹による危機感（段階的増加）
        if hasattr(self, 'hunger'):
            if self.hunger > 100:  # 深刻な空腹
                heat_increase += 3.0
            elif self.hunger > 60:  # 中程度の空腹
                heat_increase += 1.5
            elif self.hunger > 35:  # 軽い空腹
                heat_increase += 0.5
        
        # 渇きによる危機感（より急激）
        if hasattr(self, 'thirst'):
            if self.thirst > 80:  # 深刻な渇き
                heat_increase += 4.0
            elif self.thirst > 50:  # 中程度の渇き
                heat_increase += 2.0
            elif self.thirst > 30:  # 軽い渇き
                heat_increase += 0.7
        
        # 疲労による危機感
        if hasattr(self, 'fatigue'):
            if self.fatigue > 120:  # 深刻な疲労
                heat_increase += 2.0
            elif self.fatigue > 90:  # 中程度の疲労
                heat_increase += 1.0
            elif self.fatigue > 60:  # 軽い疲労
                heat_increase += 0.3
        
        # 複合的危機（複数の要因が重なると危機感が増幅）
        critical_factors = 0
        if hasattr(self, 'hunger') and self.hunger > 50:
            critical_factors += 1
        if hasattr(self, 'thirst') and self.thirst > 40:
            critical_factors += 1
        if hasattr(self, 'fatigue') and self.fatigue > 80:
            critical_factors += 1
        
        if critical_factors >= 2:
            heat_increase *= 1.5  # 複数要因での危機感増幅
        
        # ヒート更新
        self.survival_heat = min(100.0, self.survival_heat + heat_increase)
        
        # デバッグログ（ヒート蓄積時）
        if self.survival_heat > 10.0:  # より低いレベルでもログ出力
            heat_level = self.get_heat_level_name()
            print(f"🔥 T{getattr(self, '_current_tick', '?')}: {getattr(self, 'name', 'NPC')} survival heat: {self.survival_heat:.1f} ({heat_level})")
    
    def get_heat_level_name(self):
        """ヒートレベルの名前を取得"""
        if self.survival_heat >= self.desperation_threshold:
            return "絶望"
        elif self.survival_heat >= self.panic_threshold:
            return "パニック" 
        elif self.survival_heat >= self.crisis_threshold:
            return "危機"
        else:
            return "平常"
    
    def execute_heat_based_behavior(self, t):
        """ヒートレベルに基づく行動決定"""
        self._current_tick = t  # デバッグ用
        
        # ヒートレベルによる行動変化
        heat_level = self.survival_heat
        
        # 絶望レベル (80+): 極端な行動
        if heat_level >= self.desperation_threshold:
            self.execute_desperate_behavior(t)
        # パニックレベル (60-79): 非効率だが積極的な行動
        elif heat_level >= self.panic_threshold:
            self.execute_panic_behavior(t)
        # 危機レベル (30-59): より積極的で合理的な行動
        elif heat_level >= self.crisis_threshold:
            self.execute_crisis_behavior(t)
        # 平常レベル (0-29): 通常行動
        else:
            self.execute_calm_behavior(t)
    
    def execute_desperate_behavior(self, t):
        """絶望レベルの行動: 最も緊急な問題に集中"""
        # 死に最も近い要因を特定（閾値緩和）
        death_risk_thirst = hasattr(self, 'thirst') and self.thirst > 70  # 120→70により早い対応
        death_risk_hunger = hasattr(self, 'hunger') and self.hunger > 70  # 120→70により早い対応
        
        if death_risk_thirst and hasattr(self, 'seek_water'):
            self.seek_water(t)
        elif death_risk_hunger and hasattr(self, 'seek_food'):
            # 絶望時は探索も強化
            if hasattr(self, 'exploration_mode'):
                self.exploration_mode = True
                self.exploration_intensity = 2.5
            self.aggressive_food_search(t)
        else:
            # 通常の危機行動にフォールバック
            self.execute_crisis_behavior(t)
    
    def execute_coherence_based_behavior(self, t):
        """物理基層整合慣性に基づく行動決定"""
        # 整合慣性による行動優先度を取得
        priorities = self.get_coherence_driven_behavior_priority()
        
        if not priorities:
            # 優先度がない場合は従来システムにフォールバック
            if hasattr(self, 'survival_heat'):
                self.execute_heat_based_behavior(t)
            else:
                self.execute_traditional_behavior(t)
            return
        
        # 最も高い優先度の行動を実行
        top_action = max(priorities.items(), key=lambda x: x[1])
        action_name, priority = top_action
        
        # デバッグ: 狩り優先度をチェック（詳細ログは不要に）
        # if "hunt" in priorities:
        #     print(f"DEBUG_SELECT: T{t} {self.name} hunt_priority:{priorities['hunt']:.3f} selected:{action_name}")
        
        # 整合慣性による移動速度調整
        coherence_speed = 2
        if hasattr(self, 'apply_coherence_to_movement'):
            coherence_speed = self.apply_coherence_to_movement(None, 2)
        
        # 優先度に基づく行動実行
        if action_name == "seek_water" and hasattr(self, 'seek_water'):
            # 整合慣性強化水源探索（生存最優先版）
            old_exploration = getattr(self, 'exploration_intensity', 1.0)
            old_mode = getattr(self, 'exploration_mode', False)
            
            # 生存危機時の特別強化
            if self.thirst > 85:
                self.exploration_intensity = 3.0  # 危機時は探索強度最大化
                execute_count = 3  # 複数回実行で確実に水源発見
            elif self.thirst > 70:
                self.exploration_intensity = 2.0
                execute_count = 2
            else:
                self.exploration_intensity = 1.0 + priority * 1.2  # 通常時も強化
                execute_count = 1
            
            self.exploration_mode = True
            
            # 整合慣性による複数回実行で生存確率向上
            for _ in range(execute_count):
                self.seek_water(t)
                if hasattr(self, 'thirst') and self.thirst < 40:  # 十分な水分補給完了で停止
                    break
            
            self.exploration_intensity = old_exploration
            self.exploration_mode = old_mode
            
        elif action_name == "seek_food" and hasattr(self, 'seek_food'):
            # 整合慣性強化食料探索
            old_exploration = getattr(self, 'exploration_intensity', 1.0)
            self.exploration_intensity = 1.0 + priority * 0.6
            self.coherence_enhanced_food_search(t, priority)
            self.exploration_intensity = old_exploration
            
        elif action_name == "return_to_territory" and hasattr(self, 'territory'):
            # 縄張り整合慣性による帰還行動
            self.coherence_driven_territory_return(t, priority)
            
        elif action_name == "strengthen_territory":
            # 縄張り強化行動
            self.coherence_driven_territory_strengthen(t, priority)
            
        elif action_name == "hunt" and hasattr(self, 'attempt_solo_hunt'):
            # 整合慣性による狩り行動
            self.coherence_driven_hunt(t, priority)
            
        else:
            # デフォルト行動
            self.execute_traditional_behavior(t)
    
    def coherence_enhanced_food_search(self, t, coherence_priority):
        """整合慣性強化食料探索（生存効率最優先版）"""
        if hasattr(self, 'seek_food'):
            # 整合慣性による探索範囲大幅拡大
            old_mode = getattr(self, 'exploration_mode', False)
            old_intensity = getattr(self, 'exploration_intensity', 1.0)
            self.exploration_mode = True
            
            # 物理的緊張度による緊急度大幅調整（生存重視）
            urgency_factor = 1.0
            if hasattr(self, 'physical_tension'):
                urgency_factor = 1.0 + self.physical_tension * 1.2  # 緊急時効果を倍増
            
            # 生存危機時の特別強化
            if self.hunger > 90:
                urgency_factor *= 1.8  # 危機時は更に強化
                self.exploration_intensity = 2.0  # 探索強度も最大化
            elif self.hunger > 75:
                urgency_factor *= 1.4
                self.exploration_intensity = 1.5
            
            # 整合慣性による大幅成功率向上
            if hasattr(self, 'physical_kappa') and 'hunger_coherence' in self.physical_kappa:
                coherence_bonus = self.physical_kappa['hunger_coherence'] * 0.3  # ボーナス3倍
                old_curiosity = getattr(self, 'curiosity', 0.5)
                self.curiosity = min(1.0, self.curiosity + coherence_bonus)
                
                # 整合慣性による複数回実行
                execute_count = 1 + int(coherence_priority * 2)  # 最大3回実行
                for _ in range(execute_count):
                    self.seek_food(t)
                    if hasattr(self, 'hunger') and self.hunger < 50:  # 満腹になったら停止
                        break
                        
                self.curiosity = old_curiosity
            else:
                self.seek_food(t)
                
            self.exploration_mode = old_mode
            self.exploration_intensity = old_intensity
        else:
            # フォールバック
            self.execute_traditional_behavior(t)
    
    def coherence_driven_territory_return(self, t, coherence_priority):
        """整合慣性による縄張り帰還"""
        if hasattr(self, 'territory') and self.territory and hasattr(self.territory, 'center'):
            # 整合慣性による移動速度調整
            speed_factor = 1.0 + coherence_priority * 0.5
            
            # 縄張り中心への移動
            target = self.territory.center
            if hasattr(self, 'move_towards'):
                # 整合慣性による効率的移動
                for _ in range(int(speed_factor)):
                    if self.distance_to(target) > 2:
                        self.move_towards(target)
                    else:
                        break
            
            # 縄張り整合慣性の向上
            if hasattr(self, 'physical_kappa'):
                self.physical_kappa["territory_coherence"] = min(1.0,
                    self.physical_kappa.get("territory_coherence", 0.1) + 0.02)
        else:
            self.execute_traditional_behavior(t)
    
    def coherence_driven_territory_strengthen(self, t, coherence_priority):
        """整合慣性による縄張り強化"""
        # 縄張り内でのリソース管理・パトロール
        if hasattr(self, 'territory') and self.territory:
            # 縄張り内の探索を優先
            if hasattr(self, 'exploration_mode'):
                self.exploration_mode = True
                self.exploration_intensity = 0.8 + coherence_priority * 0.4
            
            # 近くのリソースをマッピング
            self.coherence_map_local_resources(t)
            
            # 基本的な縄張り行動
            if hasattr(self, 'seek_food'):
                self.seek_food(t)
            elif hasattr(self, 'seek_water'):
                self.seek_water(t)
            else:
                self.execute_traditional_behavior(t)
        else:
            self.execute_traditional_behavior(t)
    
    def coherence_driven_hunt(self, t, coherence_priority):
        """整合慣性による狩り行動（生存効率重視版）"""
        if not hasattr(self, 'attempt_solo_hunt'):
            # 狩りスキルがない場合は食料探索にフォールバック
            self.coherence_enhanced_food_search(t, coherence_priority)
            return
        
        # 狩り整合慣性による能力向上
        old_hunting_skill = getattr(self, 'hunting_skill', 0.3)
        coherence_boost = self.physical_kappa.get("hunting_coherence", 0.1) * 0.2
        
        # 一時的に狩りスキルを向上
        self.hunting_skill = min(1.0, old_hunting_skill + coherence_boost)
        
        # 物理的緊張度による緊急時強化
        urgency_factor = 1.0
        if hasattr(self, 'physical_tension'):
            urgency_factor = 1.0 + self.physical_tension * 0.8
        
        # 生存危機時の特別強化
        if self.hunger > 90:
            urgency_factor *= 1.5
            # 危機時は複数回挑戦
            hunt_attempts = 2
        elif self.hunger > 75:
            urgency_factor *= 1.2
            hunt_attempts = 1
        else:
            hunt_attempts = 1
        
        print(f"🧬 T{t}: {self.name} 整合慣性狩り - 優先度:{coherence_priority:.2f} 緊急度:{urgency_factor:.2f}")
        
        # 整合慣性による複数回狩り実行
        for attempt in range(hunt_attempts):
            try:
                # クールダウンチェックを一時的に緩和
                old_last_hunt = getattr(self, 'last_hunt_attempt', 0)
                if t - old_last_hunt >= 3:  # 整合慣性時はクールダウンを短縮
                    self.attempt_solo_hunt(t)
                    
                    # 成功した場合は整合慣性を向上
                    if hasattr(self, 'hunger'):
                        if self.hunger < 60:  # 狩り成功で満腹になった
                            self.physical_kappa["hunting_coherence"] = min(0.9,
                                self.physical_kappa["hunting_coherence"] + 0.05)
                            break  # 成功したら追加挑戦は不要
                else:
                    # クールダウン中は食料探索にフォールバック
                    self.seek_food(t)
                    
            except Exception as e:
                # エラー時は食料探索にフォールバック
                print(f"⚠️ T{t}: {self.name} 狩り失敗、食料探索にフォールバック: {e}")
                self.seek_food(t)
                break
        
        # 狩りスキルを元に戻す
        self.hunting_skill = old_hunting_skill
    
    def coherence_map_local_resources(self, t):
        """整合慣性によるローカルリソースマッピング"""
        # 整合慣性による知識獲得強化
        if not hasattr(self, 'resource_coherence_map'):
            self.resource_coherence_map = {}
        
        # 現在位置周辺のリソースを記録
        current_pos = self.pos() if hasattr(self, 'pos') else (self.x, self.y)
        
        # 水源の整合性マッピング
        if hasattr(self, 'env') and hasattr(self.env, 'water_sources'):
            for water_pos, water_data in self.env.water_sources.items():
                distance = self.distance_to(water_pos) if hasattr(self, 'distance_to') else float('inf')
                if distance < 15:  # 整合慣性範囲内
                    coherence_value = max(0, 1.0 - distance / 15.0)
                    self.resource_coherence_map[f"water_{water_pos}"] = coherence_value
        
        # 食料源の整合性マッピング
        if hasattr(self, 'env') and hasattr(self.env, 'food_sources'):
            for food_pos, food_data in self.env.food_sources.items():
                distance = self.distance_to(food_pos) if hasattr(self, 'distance_to') else float('inf')
                if distance < 15:
                    coherence_value = max(0, 1.0 - distance / 15.0)
                    self.resource_coherence_map[f"food_{food_pos}"] = coherence_value
    
    def execute_panic_behavior(self, t):
        """パニックレベルの行動: 効率より積極性"""
        # パニック時は探索が活発になる
        if hasattr(self, 'exploration_mode'):
            self.exploration_mode = True
            self.exploration_intensity = 1.8
        
        # より低い閾値で行動開始
        panic_thirst = hasattr(self, 'thirst') and self.thirst > 35
        panic_hunger = hasattr(self, 'hunger') and self.hunger > 25
        
        if panic_thirst and hasattr(self, 'seek_water'):
            self.seek_water(t)
        elif panic_hunger and hasattr(self, 'seek_food'):
            self.aggressive_food_search(t)
        else:
            # パニック探索
            if hasattr(self, 'explore_for_resource'):
                self.explore_for_resource(t, "any")
    
    def execute_crisis_behavior(self, t):
        """危機レベルの行動: バランスの取れた積極的行動"""
        # 危機時はより早期に行動
        crisis_thirst = hasattr(self, 'thirst') and self.thirst > 45
        crisis_hunger = hasattr(self, 'hunger') and self.hunger > 30
        
        if crisis_thirst and hasattr(self, 'seek_water'):
            self.seek_water(t)
        elif crisis_hunger and hasattr(self, 'seek_food'):
            self.seek_food(t)
        else:
            # 危機時の予防的探索
            if hasattr(self, 'explore_for_resource'):
                exploration_mode = getattr(self, 'exploration_mode', False)
                curiosity = getattr(self, 'curiosity', 0.5)
                
                # 危機時は探索確率を上げる
                crisis_exploration_boost = 0.3
                import random
                if exploration_mode or random.random() < (curiosity + crisis_exploration_boost):
                    self.explore_for_resource(t, "any")
    
    def execute_calm_behavior(self, t):
        """平常レベルの行動: 従来の閾値ベース行動"""
        # 従来の行動ロジック（余裕がある時の標準的な行動）
        moderate_thirst = hasattr(self, 'thirst') and self.thirst > 50
        moderate_hunger = hasattr(self, 'hunger') and self.hunger > 35
        moderate_fatigue = hasattr(self, 'fatigue') and self.fatigue > 70
        
        if moderate_thirst and hasattr(self, 'seek_water'):
            self.seek_water(t)
        elif moderate_hunger and hasattr(self, 'seek_food'):
            self.seek_food(t)
        elif moderate_fatigue and hasattr(self, 'seek_rest'):
            self.seek_rest(t)
        else:
            # 平常時の探索
            if hasattr(self, 'explore_for_resource'):
                exploration_mode = getattr(self, 'exploration_mode', False)
                curiosity = getattr(self, 'curiosity', 0.5)
                
                import random
                if exploration_mode or random.random() < curiosity:
                    self.explore_for_resource(t, "any")
    
    def aggressive_food_search(self, t):
        """積極的な食料探索（パニック・絶望時）"""
        # 知られているベリーの確認
        has_known_berries = (hasattr(self, 'knowledge_berries') and 
                           hasattr(self, 'env') and 
                           bool([k for k in self.env.berries.keys() if k in self.knowledge_berries]))
        
        if has_known_berries and hasattr(self, 'seek_food'):
            self.seek_food(t)
        else:
            # 積極的な食料探索
            if hasattr(self, 'explore_for_resource'):
                self.explore_for_resource(t, "food")
    
    def execute_traditional_behavior(self, t):
        """従来の固定閾値システム（フォールバック）"""
        urgent_thirst = hasattr(self, 'thirst') and self.thirst > 60
        urgent_hunger = hasattr(self, 'hunger') and self.hunger > 40
        urgent_fatigue = hasattr(self, 'fatigue') and self.fatigue > 80
        
        if urgent_thirst and hasattr(self, 'seek_water'):
            self.seek_water(t)
        elif urgent_hunger and hasattr(self, 'seek_food'):
            self.seek_food(t)
        elif urgent_fatigue and hasattr(self, 'seek_rest'):
            self.seek_rest(t)
        else:
            if hasattr(self, 'explore_for_resource'):
                exploration_mode = getattr(self, 'exploration_mode', False)
                curiosity = getattr(self, 'curiosity', 0.5)
                
                import random
                if exploration_mode or random.random() < curiosity:
                    self.explore_for_resource(t, "any")
    
    def pos(self) -> Tuple[float, float]:
        """
        現在位置を返す
        
        Returns:
            Tuple[float, float]: (x, y)座標
        """
        if hasattr(self, 'x') and hasattr(self, 'y'):
            return (self.x, self.y)
        return (0.0, 0.0)
    
    def die(self) -> None:
        """
        NPCの死亡処理
        
        死亡フラグを設定し、必要な後処理を実行
        """
        if hasattr(self, 'is_alive'):
            self.is_alive = False
            
        if hasattr(self, 'health'):
            self.health = 0
            
        # 死亡ログ
        print(f"NPC at {self.pos()} has died")
    
    def emergency_survival_action(self) -> None:
        """
        緊急サバイバル行動
        
        健康状態が危険な時の緊急処置
        """
        # 最も近い食料源へ移動を試みる
        if hasattr(self, 'find_nearest_food'):
            target = self.find_nearest_food()
            if target and hasattr(self, 'move_toward'):
                self.move_toward(target)
        
        # エネルギー消費を最小限に
        if hasattr(self, 'energy'):
            # 緊急時はエネルギー消費を削減
            pass
            
        # 協力要請
        if hasattr(self, 'request_help'):
            self.request_help()
    
    def gain_experience(self, amount: float, category: str = "survival") -> None:
        """
        経験値獲得処理
        
        Args:
            amount (float): 獲得経験値量
            category (str): 経験カテゴリ
        """
        if hasattr(self, 'experience'):
            if isinstance(self.experience, dict):
                # 辞書形式の経験値システム
                if category in self.experience:
                    self.experience[category] += amount
                else:
                    self.experience[category] = amount
            else:
                # 単純な数値形式
                self.experience += amount
            
        # 経験値による能力向上
        if hasattr(self, 'experience'):
            if isinstance(self.experience, dict):
                total_exp = sum(self.experience.values())
                if total_exp > 10 and hasattr(self, 'hunting_skill'):
                    self.hunting_skill *= 1.001  # スキル微増
            elif self.experience > 100:
                if hasattr(self, 'hunting_skill'):
                    self.hunting_skill *= 1.01  # スキル微増
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        現在の状態情報を取得
        
        Returns:
            Dict[str, Any]: 状態情報辞書
        """
        state = {
            'position': self.pos(),
            'is_alive': getattr(self, 'is_alive', True),
        }
        
        # 利用可能な属性を追加
        for attr in ['health', 'energy', 'age', 'experience']:
            if hasattr(self, attr):
                state[attr] = getattr(self, attr)
                
        return state
    
    def distance_to(self, target_pos: Tuple[float, float]) -> float:
        """
        指定位置までの距離を計算
        
        Args:
            target_pos (Tuple[float, float]): 目標位置
            
        Returns:
            float: 距離
        """
        x1, y1 = self.pos()
        x2, y2 = target_pos
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def is_near(self, target_pos: Tuple[float, float], threshold: float = 5.0) -> bool:
        """
        指定位置が近くにあるかチェック
        
        Args:
            target_pos (Tuple[float, float]): 目標位置
            threshold (float): 距離閾値
            
        Returns:
            bool: 近くにあるかどうか
        """
        return self.distance_to(target_pos) <= threshold
    
    def explore_for_resource(self, t, resource_type):
        """
        リソース探索
        
        Args:
            t: 現在時刻
            resource_type (str): 探索対象リソースタイプ
        """
        # 探索移動
        explore_distance = 3 if getattr(self, 'exploration_mode', False) else 2
        dx = random.randint(-explore_distance, explore_distance)
        dy = random.randint(-explore_distance, explore_distance)

        if hasattr(self, 'env') and hasattr(self, 'x') and hasattr(self, 'y'):
            new_x = max(0, min(self.env.size - 1, self.x + dx))
            new_y = max(0, min(self.env.size - 1, self.y + dy))
            self.x, self.y = new_x, new_y

        # 探索経験の獲得
        exploration_intensity = getattr(self, 'exploration_intensity', 1.0) if getattr(self, 'exploration_mode', False) else 0.5
        self.gain_experience(exploration_intensity * 0.1, "exploration")

        # リソース発見判定
        discovery_chance = 0.3
        if getattr(self, 'exploration_mode', False):
            discovery_chance *= exploration_intensity

        if random.random() < discovery_chance:
            self.discover_nearby_resources(t, resource_type)

    def discover_nearby_resources(self, t, target_type):
        """
        近くのリソースを発見
        
        Args:
            t: 現在時刻
            target_type (str): 目標リソースタイプ
        """
        # 発見半径設定
        base_radius = 15
        fatigue_bonus = max(0, (getattr(self, 'fatigue', 0) - 70) * 0.3) if hasattr(self, 'fatigue') else 0
        discovery_radius = base_radius + fatigue_bonus
        discovered = False

        if not hasattr(self, 'env'):
            return discovered

        # 水源の発見
        if target_type in ["water", "any"] and hasattr(self, 'knowledge_water'):
            for water_name, water_pos in self.env.water_sources.items():
                if (
                    water_name not in self.knowledge_water
                    and self.distance_to(water_pos) <= discovery_radius
                ):
                    self.knowledge_water.add(water_name)
                    self.gain_experience(0.8, "exploration")
                    discovered = True

        # ベリーの発見
        if target_type in ["food", "any"] and hasattr(self, 'knowledge_berries'):
            for berry_name, berry_pos in self.env.berries.items():
                if (
                    berry_name not in self.knowledge_berries
                    and self.distance_to(berry_pos) <= discovery_radius
                ):
                    self.knowledge_berries.add(berry_name)
                    self.gain_experience(0.7, "exploration")
                    discovered = True

        # 洞窟の発見
        if target_type in ["shelter", "any"] and hasattr(self, 'knowledge_caves'):
            for cave_name, cave_pos in self.env.caves.items():
                if (
                    cave_name not in self.knowledge_caves
                    and self.distance_to(cave_pos) <= discovery_radius
                ):
                    self.knowledge_caves.add(cave_name)
                    self.gain_experience(0.9, "exploration")
                    discovered = True

        return discovered
        
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

    def gain_experience(self, amount, experience_type):
        """経験値の獲得"""
        if experience_type not in self.experience:
            self.experience[experience_type] = 0.0
        
        self.experience[experience_type] = min(10.0, self.experience[experience_type] + amount)

    def get_module_status(self):
        """分割状況のステータス"""
        return {
            "modularized": True,
            "base_class": "OriginalNPC",
            "status": "Transitioning to modular design"
        }