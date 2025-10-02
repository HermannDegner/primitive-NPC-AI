#!/usr/bin/env python3
"""
昼夜サイクル統合未来予測エンジンのテスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from environment import Environment
from npc import NPC

def test_day_night_prediction():
    """昼夜サイクルを考慮した未来予測のテスト"""
    print("🌅🌙 昼夜サイクル統合未来予測エンジンのテスト開始...")
    
    # 環境とNPCの初期化
    env = Environment()
    roster = {}
    preset = {"curiosity": 0.7, "sociability": 0.8}
    npc = NPC("昼夜NPC", preset, env, roster, (25, 25))
    
    # 様々な時間帯でのテスト
    time_scenarios = [
        {"hour": 7, "name": "朝 (7:00)", "tick": 14},    # 7時 = 14ティック (7*2)
        {"hour": 12, "name": "昼 (12:00)", "tick": 24},   # 12時 = 24ティック
        {"hour": 18, "name": "夕方 (18:00)", "tick": 36}, # 18時 = 36ティック
        {"hour": 22, "name": "夜 (22:00)", "tick": 44},   # 22時 = 44ティック
        {"hour": 2, "name": "深夜 (2:00)", "tick": 4},    # 2時 = 4ティック
    ]
    
    for scenario in time_scenarios:
        print(f"\n{'='*60}")
        print(f"シナリオ: {scenario['name']}")
        print(f"{'='*60}")
        
        # 時間を設定
        env.day_night.tick_counter = scenario['tick']
        env.day_night.time_of_day = scenario['hour']
        
        # NPCの状態を中程度に設定
        npc.fatigue = 60
        npc.hunger = 45
        npc.thirst = 30
        
        is_night = env.day_night.is_night()
        danger_multiplier = env.day_night.get_night_danger_multiplier()
        
        print(f"時刻: {scenario['hour']}:00")
        print(f"夜間判定: {'🌙 夜' if is_night else '☀️ 昼'}")
        print(f"危険度倍率: {danger_multiplier}x")
        print(f"NPCの状態: 疲労={npc.fatigue}, 空腹={npc.hunger}, 渇き={npc.thirst}")
        
        if hasattr(npc, 'future_engine'):
            # 予測サマリーを取得
            prediction_summary = npc.future_engine.get_prediction_summary()
            
            print(f"\n【昼夜対応未来予測分析】")
            time_context = prediction_summary.get('time_context', {})
            print(f"時間フェーズ: {time_context.get('phase', 'unknown')}")
            print(f"危険レベル: {time_context.get('danger_level', 1.0)}x")
            
            print(f"\n【推奨行動】")
            recommended = prediction_summary['recommended_action']
            print(f"行動: {recommended['action']}")
            print(f"緊急度: {recommended['urgency']:.2f}")
            print(f"理由: {recommended['rationale']}")
            print(f"生存リスク: {prediction_summary['survival_risk_level']}")
            
            # 行動選択肢の詳細
            options = npc.future_engine.generate_action_options()
            print(f"\n【時間帯別行動選択肢 (上位3つ)】")
            for i, option in enumerate(sorted(options, key=lambda x: x.urgency * x.probability, reverse=True)[:3]):
                prerequisites_str = ", ".join(option.prerequisites) if option.prerequisites else "なし"
                print(f"{i+1}. {option.action_type.value}:")
                print(f"   緊急度: {option.urgency:.2f}, 成功率: {option.probability:.2f}")
                print(f"   前提条件: {prerequisites_str}")
                
                # コストと利益の詳細
                cost_str = ", ".join([f"{k}:{v:+.0f}" for k, v in option.cost.items()])
                benefit_str = ", ".join([f"{k}:{v:+.0f}" for k, v in option.benefit.items()])
                print(f"   コスト: {cost_str}")
                print(f"   利益: {benefit_str}")
        else:
            print("予測エンジンが初期化されていません")
        
        # 実際の行動を1ステップ実行
        print(f"\n【実行結果】")
        npc.step(scenario['tick'])
        
        # ログの確認
        if npc.log:
            last_log = npc.log[-1]
            action_name = last_log.get('action', 'unknown')
            if 'future_prediction_decision' in action_name:
                print(f"未来予測決定: {last_log.get('recommended_action', 'unknown')} "
                      f"(理由: {last_log.get('rationale', 'unknown')})")
            else:
                print(f"実行行動: {action_name}")
        
        print(f"結果状態: 疲労={npc.fatigue:.1f}, 空腹={npc.hunger:.1f}, 渇き={npc.thirst:.1f}")

def test_night_vs_day_behavior():
    """昼間と夜間の行動パターンの違いを比較"""
    print(f"\n{'='*80}")
    print("昼夜行動パターン比較テスト")
    print(f"{'='*80}")
    
    env = Environment()
    roster = {}
    preset = {"curiosity": 0.6, "sociability": 0.7}
    
    # 昼間のNPC
    day_npc = NPC("昼間NPC", preset, env, roster, (25, 25))
    env.day_night.time_of_day = 10  # 10時
    env.day_night.tick_counter = 20
    
    # 夜間のNPC
    night_npc = NPC("夜間NPC", preset, env, roster, (25, 25))
    env.day_night.time_of_day = 23  # 23時
    env.day_night.tick_counter = 46
    
    # 同じ条件で比較
    for npc_name, npc in [("昼間", day_npc), ("夜間", night_npc)]:
        npc.fatigue = 50
        npc.hunger = 40
        npc.thirst = 25
        
        # 時間設定を個別に調整
        if npc_name == "昼間":
            env.day_night.time_of_day = 10
        else:
            env.day_night.time_of_day = 23
            
        print(f"\n【{npc_name}の行動傾向】")
        print(f"時刻: {env.day_night.time_of_day}:00 ({'夜' if env.day_night.is_night() else '昼'})")
        
        if hasattr(npc, 'future_engine'):
            prediction = npc.future_engine.get_prediction_summary()
            print(f"推奨行動: {prediction['recommended_action']['action']}")
            print(f"理由: {prediction['recommended_action']['rationale']}")
            print(f"危険レベル: {prediction['time_context']['danger_level']}x")
            
            # 各行動の優先度を比較
            options = npc.future_engine.generate_action_options()
            action_priorities = {}
            for option in options:
                action_priorities[option.action_type.value] = {
                    'urgency': option.urgency,
                    'probability': option.probability,
                    'score': option.urgency * option.probability
                }
            
            print(f"行動優先度ランキング:")
            sorted_actions = sorted(action_priorities.items(), 
                                  key=lambda x: x[1]['score'], reverse=True)
            for i, (action, stats) in enumerate(sorted_actions[:5]):
                print(f"  {i+1}. {action}: スコア={stats['score']:.3f} "
                      f"(緊急度={stats['urgency']:.2f}, 確率={stats['probability']:.2f})")

if __name__ == "__main__":
    test_day_night_prediction()
    test_night_vs_day_behavior()