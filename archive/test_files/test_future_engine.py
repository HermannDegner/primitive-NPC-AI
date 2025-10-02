#!/usr/bin/env python3
"""
未来予測エンジンの統合テスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from environment import Environment
from npc import NPC

def test_future_prediction_engine():
    """未来予測エンジンの統合テスト"""
    print("未来予測エンジン統合テスト開始...")
    
    # 環境とNPCの初期化
    env = Environment()
    roster = {}
    preset = {"curiosity": 0.6, "sociability": 0.7}
    npc = NPC("予測NPC", preset, env, roster, (25, 25))
    
    # 様々なシナリオでテスト
    scenarios = [
        {"fatigue": 45, "hunger": 30, "thirst": 20, "name": "軽度ストレス"},
        {"fatigue": 70, "hunger": 50, "thirst": 35, "name": "中度ストレス"},
        {"fatigue": 100, "hunger": 65, "thirst": 45, "name": "高ストレス"},
        {"fatigue": 130, "hunger": 80, "thirst": 60, "name": "危機的状況"}
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*50}")
        print(f"シナリオ {i}: {scenario['name']}")
        print(f"{'='*50}")
        
        # NPCの状態をシナリオに設定
        npc.fatigue = scenario['fatigue']
        npc.hunger = scenario['hunger'] 
        npc.thirst = scenario['thirst']
        
        print(f"状態: 疲労={npc.fatigue}, 空腹={npc.hunger}, 渇き={npc.thirst}")
        
        if hasattr(npc, 'future_engine'):
            # 予測サマリーを取得
            prediction_summary = npc.future_engine.get_prediction_summary()
            
            print(f"\n【予測エンジン分析】")
            print(f"推奨行動: {prediction_summary['recommended_action']['action']}")
            print(f"緊急度: {prediction_summary['recommended_action']['urgency']:.2f}")
            print(f"理由: {prediction_summary['recommended_action']['rationale']}")
            print(f"生存リスク: {prediction_summary['survival_risk_level']}")
            
            print(f"\n【3ステップ後の予測状態】")
            future_state = prediction_summary['future_state_3_steps']
            print(f"疲労: {future_state['fatigue']:.1f}")
            print(f"空腹: {future_state['hunger']:.1f}")
            print(f"渇き: {future_state['thirst']:.1f}")
            
            # 行動選択肢の詳細
            options = npc.future_engine.generate_action_options()
            print(f"\n【利用可能な行動選択肢】")
            for j, option in enumerate(options[:3]):  # 上位3つを表示
                print(f"{j+1}. {option.action_type.value}: "
                      f"緊急度={option.urgency:.2f}, "
                      f"成功率={option.probability:.2f}")
        else:
            print("予測エンジンが初期化されていません")
        
        # 実際の行動を1ステップ実行
        print(f"\n【実行結果】")
        npc.step(i)
        
        # ログの確認
        if npc.log:
            last_log = npc.log[-1]
            if 'future_prediction_decision' in last_log.get('action', ''):
                print(f"未来予測決定: {last_log['recommended_action']} "
                      f"(理由: {last_log['rationale']})")
            else:
                print(f"実行行動: {last_log.get('action', 'unknown')}")
        
        print(f"結果状態: 疲労={npc.fatigue:.1f}, 空腹={npc.hunger:.1f}, 渇き={npc.thirst:.1f}")

def test_prediction_accuracy():
    """予測精度のテスト"""
    print(f"\n{'='*60}")
    print("予測精度テスト")
    print(f"{'='*60}")
    
    env = Environment()
    roster = {}
    preset = {"curiosity": 0.5, "sociability": 0.5}
    npc = NPC("テストNPC", preset, env, roster, (25, 25))
    
    # 初期状態
    initial_state = {
        "fatigue": npc.fatigue,
        "hunger": npc.hunger,
        "thirst": npc.thirst
    }
    
    print(f"初期状態: {initial_state}")
    
    if hasattr(npc, 'future_engine'):
        # 3ステップ分の予測
        prediction_summary = npc.future_engine.get_prediction_summary()
        predicted_state = prediction_summary['future_state_3_steps']
        
        print(f"予測状態 (3ステップ後): {predicted_state}")
        
        # 実際に3ステップ実行
        for step in range(1, 4):
            npc.step(step)
        
        actual_state = {
            "fatigue": npc.fatigue,
            "hunger": npc.hunger,
            "thirst": npc.thirst
        }
        
        print(f"実際状態 (3ステップ後): {actual_state}")
        
        # 予測精度計算
        fatigue_error = abs(predicted_state['fatigue'] - actual_state['fatigue'])
        hunger_error = abs(predicted_state['hunger'] - actual_state['hunger'])
        thirst_error = abs(predicted_state['thirst'] - actual_state['thirst'])
        
        print(f"\n【予測精度】")
        print(f"疲労誤差: {fatigue_error:.1f}")
        print(f"空腹誤差: {hunger_error:.1f}")
        print(f"渇き誤差: {thirst_error:.1f}")
        print(f"平均誤差: {(fatigue_error + hunger_error + thirst_error)/3:.1f}")

if __name__ == "__main__":
    test_future_prediction_engine()
    test_prediction_accuracy()