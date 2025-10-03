"""
NPC Package - 分割されたNPCシステム

主要モジュール:
- npc_core: NPCの中心クラス（段階的移行用）
- npc_movement: 移動とナビゲーション
- npc_survival: 生存行動（水、食べ物、休息）
- npc_hunting: 狩猟システム（ソロ・グループ）
- npc_cooperation: 協力と社交システム
- npc_territory: 縄張りと安全システム
- npc_prediction: 予測システムと将来計画
"""

from .npc_modular import NPC

__all__ = ['NPC']