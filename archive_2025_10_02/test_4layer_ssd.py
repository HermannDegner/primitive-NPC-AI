"""
SSD Village Simulation - 4層物理構造デモ
4層物理構造システムの動作をテストするためのデモスクリプト
"""

import sys
import os

# ssd_core.pyをインポートするためのパス設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ssd_core import PhysicalStructureSystem, SSDCore
import random

class MockNPC:
    """テスト用のNPCクラス"""
    def __init__(self):
        # 基本パラメータ
        self.name = "TestNPC"
        self.hunger = 120
        self.thirst = 100
        self.fatigue = 60
        self.E = 1.2  # 未処理圧
        
        # 性格パラメータ
        self.curiosity = 0.7
        self.sociability = 0.5
        self.risk_tolerance = 0.6
        
        # 知識
        self.knowledge_caves = ["cave1", "cave2"]
        self.knowledge_water = ["water1"]
        self.knowledge_berries = ["berries1", "berries2", "berries3"]
        
        # 経験値（整合慣性）
        self.kappa = {
            "exploration": 0.3,
            "foraging": 0.5,
            "resting": 0.4,
            "social": 0.2,
            "territory": 0.3
        }
        
        # テリトリー（None = 孤立状態）
        self.territory = None
        
        # 行動ログ
        self.log = []
        
        # 探索モード
        self.exploration_mode = False
        self.exploration_mode_start_tick = 0
        self.exploration_intensity = 1.0

def demonstrate_4layer_structure():
    """4層物理構造システムのデモンストレーション"""
    print("=" * 60)
    print("SSD理論 4層物理構造システム デモンストレーション")
    print("=" * 60)
    
    # テスト用NPCを作成
    npc = MockNPC()
    print(f"NPCステータス: {npc.name}")
    print(f"  飢餓: {npc.hunger}, 渇き: {npc.thirst}, 疲労: {npc.fatigue}")
    print(f"  好奇心: {npc.curiosity}, 社交性: {npc.sociability}, リスク許容度: {npc.risk_tolerance}")
    print(f"  未処理圧(E): {npc.E}")
    print()
    
    # 4層物理構造システムを初期化
    physical_system = PhysicalStructureSystem(npc)
    print("4層物理構造システム初期化完了")
    print()
    
    # 様々な外部刺激をテスト
    test_scenarios = [
        {
            "name": "平常状態",
            "stimuli": {
                'exploration_pressure': 0.5,
                'environmental_pressure': 0.1
            }
        },
        {
            "name": "生存危機状態（高い飢餓）",
            "stimuli": {
                'exploration_pressure': 0.3,
                'environmental_pressure': 0.2
            },
            "npc_changes": {"hunger": 180, "thirst": 150}
        },
        {
            "name": "高探索欲求状態",
            "stimuli": {
                'exploration_pressure': 1.5,
                'environmental_pressure': 0.1
            }
        },
        {
            "name": "極度の疲労状態",
            "stimuli": {
                'exploration_pressure': 0.4,
                'environmental_pressure': 0.3
            },
            "npc_changes": {"fatigue": 110}
        }
    ]
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n--- シナリオ {i+1}: {scenario['name']} ---")
        
        # NPCの状態を一時的に変更
        original_state = {}
        if 'npc_changes' in scenario:
            for attr, value in scenario['npc_changes'].items():
                original_state[attr] = getattr(npc, attr)
                setattr(npc, attr, value)
                print(f"  {attr}を{value}に変更")
        
        print(f"外部刺激: {scenario['stimuli']}")
        
        # 4層構造を通じた処理
        result = physical_system.process_structural_dynamics(scenario['stimuli'])
        
        # 結果を表示
        print("\n4層構造処理結果:")
        print(f"  物理制約: {result.get('physical_constraints', 'N/A')}")
        print(f"  生存メカニズム: {result.get('survival_mechanisms', 'N/A')}")
        print(f"  行動決定: {result.get('behavioral_decisions', 'N/A')}")
        print(f"  最終決定: {result['final_decision']}")
        
        # 従来方式との比較
        traditional_pressure = SSDCore.calculate_meaning_pressure(scenario['stimuli'])
        modern_pressure = SSDCore.calculate_meaning_pressure(scenario['stimuli'], physical_system)
        
        print(f"\n意味圧比較:")
        print(f"  従来方式: {traditional_pressure:.3f}")
        print(f"  4層構造: {modern_pressure:.3f}")
        
        # NPCの状態を元に戻す
        for attr, value in original_state.items():
            setattr(npc, attr, value)
        
        print("-" * 50)
    
    print("\n" + "=" * 60)
    print("デモ完了")
    print("=" * 60)

def analyze_layer_contributions():
    """各層の貢献度分析"""
    print("\n=== 各層の貢献度分析 ===")
    
    npc = MockNPC()
    # 高ストレス状態に設定
    npc.hunger = 170
    npc.thirst = 140
    npc.fatigue = 90
    npc.E = 2.0
    
    physical_system = PhysicalStructureSystem(npc)
    
    # 高圧力刺激
    stimuli = {
        'exploration_pressure': 1.2,
        'environmental_pressure': 0.5
    }
    
    # 各層での処理を段階的に表示
    print(f"入力刺激: {stimuli}")
    
    # 1. 物理層
    physical_constraints = physical_system.physical_layer.process_physical_constraints(stimuli)
    print(f"\n1. 物理層出力:")
    for key, value in physical_constraints.items():
        print(f"   {key}: {value:.3f}")
    
    # 2. 基層
    survival_mechanisms = physical_system.foundation_layer.process_survival_mechanisms(physical_constraints)
    print(f"\n2. 基層出力:")
    for key, value in survival_mechanisms.items():
        if isinstance(value, dict):
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value:.3f}")
    
    # 3. 中核層
    behavioral_decisions = physical_system.core_layer.process_behavioral_decisions(survival_mechanisms)
    print(f"\n3. 中核層出力:")
    for key, value in behavioral_decisions.items():
        if isinstance(value, dict):
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value:.3f}")
    
    # 4. 上層
    adaptive_outputs = physical_system.upper_layer.process_adaptive_learning(behavioral_decisions)
    print(f"\n4. 上層出力:")
    for key, value in adaptive_outputs.items():
        if isinstance(value, dict):
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")

if __name__ == "__main__":
    try:
        demonstrate_4layer_structure()
        analyze_layer_contributions()
    except Exception as e:
        print(f"エラー発生: {e}")
        import traceback
        traceback.print_exc()