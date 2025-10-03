"""
SSD縄張りシステム - 縄張り管理と領域制御

このモジュールは、NPCの縄張り作成・管理に関する機能を提供します。
"""

from typing import Tuple, Dict, Any
import random


class SSDTerritorySystem:
    """SSD Core Engine版縄張りシステム"""
    
    def __init__(self, ssd_enhanced_npc):
        self.enhanced_npc = ssd_enhanced_npc
        self.npc = ssd_enhanced_npc.npc
        self.engine = ssd_enhanced_npc.engine

    def process_territorial_experience(self, experience_type: str, experience_valence: float, 
                                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """縄張り関連の経験処理"""
        try:
            # 経験の構造化
            experience_data = {
                "type": experience_type,
                "valence": experience_valence,
                "timestamp": getattr(self.npc, 'current_tick', 0),
                "context": context or {}
            }
            
            # SSD Engineに経験を登録
            if hasattr(self.engine, 'process_experience'):
                return self.engine.process_experience(experience_data)
            else:
                return {"status": "processed", "experience": experience_data}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_territory_v2(self, center: Tuple[int, int], radius: int = 5, owner: str = None) -> str:
        """SSD Core Engine版: 縄張り作成（NPCの基本評価を拡張）"""
        try:
            territory_id = f"territory_{owner or self.npc.name}_{center[0]}_{center[1]}"
            
            # NPCレベルの価値評価を基盤とする
            base_value = self.npc.assess_territory_value(center, radius)
            
            # SSD拡張評価
            ssd_enhancements = self._assess_ssd_territory_enhancements(center, radius)
            
            # 縄張りデータの構築
            territory_data = {
                "center": center,
                "radius": radius,
                "owner": owner or self.npc.name,
                "establishment_tick": getattr(self.npc, 'current_tick', 0),
                "base_value": base_value,  # NPCレベル評価
                "resource_density": self._assess_resource_density(center, radius),
                "defensive_value": self._calculate_defensive_value(center, radius),
                "ssd_enhancements": ssd_enhancements,  # SSD拡張評価
                "maintenance_cost": radius * 0.1,
                "total_value": base_value * 0.6 + ssd_enhancements * 0.4
            }
            
            # SSD Engine の社会層に追加
            if hasattr(self.engine, 'add_structural_element'):
                self.engine.add_structural_element(
                    'SOCIAL',  # LayerType.SOCIALの代替
                    territory_id,
                    territory_data
                )
            
            return territory_id
            
        except Exception as e:
            # フォールバック: 簡易縄張り作成
            return f"fallback_territory_{random.randint(1000, 9999)}"

    def check_territory_contains_v2(self, territory_id: str, pos: Tuple[int, int]) -> bool:
        """SSD Core Engine版: 位置が縄張り内かチェック"""
        try:
            # SSD Engineから縄張りデータを取得
            if hasattr(self.engine, 'get_structural_element'):
                territory_data = self.engine.get_structural_element('SOCIAL', territory_id)
                if territory_data:
                    center = territory_data.get('center', (0, 0))
                    radius = territory_data.get('radius', 5)
                    
                    distance = ((pos[0] - center[0]) ** 2 + (pos[1] - center[1]) ** 2) ** 0.5
                    return distance <= radius
            
            return False
            
        except Exception as e:
            return False

    def _assess_resource_density(self, center: Tuple[int, int], radius: int) -> float:
        """縄張りエリア内のリソース密度を評価"""
        try:
            resource_count = 0
            area_points = (radius * 2) ** 2
            
            # 環境から近隣のリソースをカウント
            if hasattr(self.npc, 'env'):
                # 洞窟のチェック
                for cave in getattr(self.npc.env, 'caves', []):
                    distance = ((cave.x - center[0]) ** 2 + (cave.y - center[1]) ** 2) ** 0.5
                    if distance <= radius:
                        resource_count += cave.water_amount + cave.food_amount
                
                # ベリーパッチのチェック
                for patch_type, patches in getattr(self.npc.env, 'berry_patches', {}).items():
                    for patch_pos in patches:
                        distance = ((patch_pos[0] - center[0]) ** 2 + (patch_pos[1] - center[1]) ** 2) ** 0.5
                        if distance <= radius:
                            resource_count += getattr(self.npc.env, 'berry_nutrition', {}).get(patch_type, 1)
            
            return min(1.0, resource_count / (area_points * 0.1))
            
        except Exception as e:
            return 0.5  # デフォルト値

    def _calculate_defensive_value(self, center: Tuple[int, int], radius: int) -> float:
        """縄張りの防御価値を計算"""
        try:
            # 地形的な防御利点を評価
            defensive_score = 0.5  # ベースライン
            
            # 洞窟の近さによる防御ボーナス
            if hasattr(self.npc, 'env'):
                for cave in getattr(self.npc.env, 'caves', []):
                    distance = ((cave.x - center[0]) ** 2 + (cave.y - center[1]) ** 2) ** 0.5
                    if distance <= radius:
                        defensive_score += 0.2  # 洞窟は避難場所として有効
                        break
            
            # 境界部のランダムな地形特性（簡易版）
            border_complexity = hash(str(center)) % 100 / 100.0
            defensive_score += border_complexity * 0.3
            
            return min(1.0, defensive_score)
            
        except Exception as e:
            return 0.5
    
    def _assess_ssd_territory_enhancements(self, center: Tuple[int, int], radius: int) -> float:
        """SSDレベルの縄張り拡張評価"""
        try:
            # 将来的なリソース変化予測
            future_resource_stability = 0.7  # デフォルト
            if hasattr(self.engine, 'predict_resource_changes'):
                try:
                    prediction = self.engine.predict_resource_changes(center, radius)
                    future_resource_stability = prediction.get('stability', 0.7)
                except Exception:
                    pass
            
            # 社会的要因（他NPCとの競合予測）
            social_competition_risk = 0.3  # デフォルト
            if hasattr(self.engine, 'assess_social_competition'):
                try:
                    competition = self.engine.assess_social_competition(center, radius)
                    social_competition_risk = competition.get('risk_level', 0.3)
                except Exception:
                    pass
            
            # 環境的脅威評価
            environmental_threat = 0.2  # デフォルト
            if hasattr(self.npc, 'env'):
                predator_proximity = getattr(self.npc.env, 'predator_density', {}).get(str(center), 0.2)
                environmental_threat = min(0.8, predator_proximity)
            
            # SSD統合評価
            ssd_enhancement = (
                future_resource_stability * 0.4 +
                (1.0 - social_competition_risk) * 0.3 +
                (1.0 - environmental_threat) * 0.3
            )
            
            return max(0.0, min(1.0, ssd_enhancement))
            
        except Exception as e:
            return 0.6  # デフォルト拡張評価