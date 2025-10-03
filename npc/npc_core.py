"""
NPC Core Module - 分割されたNPCの中心部
"""

# 元のnpc.pyのコアクラスを分割バージョンとしてインポート
# これにより段階的な分割が可能

import sys
import os

# システムパスを追加して元のファイルにアクセス
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 元のNPCクラスを基底クラスとして使用し、段階的に機能を分離
from npc_original_backup import NPC as OriginalNPC


class NPC(OriginalNPC):
    """分割されたNPCクラス - 段階的移行用"""
    
    def __init__(self, *args, **kwargs):
        # 元のコンストラクタを呼び出し
        super().__init__(*args, **kwargs)
        
        # 分割版フラグ
        self._is_modularized = True
        
    def get_module_status(self):
        """分割状況のステータス"""
        return {
            "modularized": True,
            "base_class": "OriginalNPC",
            "status": "Transitioning to modular design"
        }