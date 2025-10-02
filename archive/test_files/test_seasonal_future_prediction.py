#!/usr/bin/env python3
"""
季節統合版未来予測エンジンのテスト
"""

from future_prediction import FuturePredictionEngine
from environment import Environment
from npc import NPC, ADVENTURER
import random

def test_seasonal_future_prediction():
    """季節予測システムのテスト"""
    print("🔮 季節統合版未来予測エンジン テスト")
    print("=" * 50)
    
    # 環境とNPCを作成
    env = Environment(size=50, n_berry=0, n_hunt=10, n_water=5, n_caves=3)
    npc = NPC("TestNPC", ADVENTURER, env, {}, (25, 25))
    
    # 季節修正係数をシミュレート
    seasonal_scenarios = [
        {
            'name': '🌸春（資源回復期）',
            'seasonal_modifier': {
                'prey_activity': 0.8,
                'temperature_stress': 0.0,
                'seasonal_pressure': 0.1
            }
        },
        {
            'name': '🌞夏（豊穣期）',
            'seasonal_modifier': {
                'prey_activity': 1.3,
                'temperature_stress': 0.1,
                'seasonal_pressure': 0.0
            }
        },
        {
            'name': '🍂秋（準備期）',
            'seasonal_modifier': {
                'prey_activity': 0.9,
                'temperature_stress': 0.1,
                'seasonal_pressure': 0.2
            }
        },
        {
            'name': '❄️冬（厳しい季節）',
            'seasonal_modifier': {
                'prey_activity': 0.4,
                'temperature_stress': 0.4,
                'seasonal_pressure': 0.5
            }
        }
    ]
    
    # 各季節での未来予測をテスト
    for i, scenario in enumerate(seasonal_scenarios):
        print(f"\n{scenario['name']}")
        print("-" * 30)
        
        # 季節修正係数を設定
        env.seasonal_modifier = scenario['seasonal_modifier']
        env.tick = i * 100 + 80  # 季節終了近くをシミュレート
        
        # NPCの状態を設定（やや厳しい状況）
        npc.hunger = 60 + random.randint(-10, 20)
        npc.thirst = 40 + random.randint(-10, 20)
        npc.fatigue = 80 + random.randint(-20, 30)
        
        # 未来予測実行
        future_engine = FuturePredictionEngine(npc)
        
        print(f"NPCステータス: 空腹={npc.hunger}, 喉渇き={npc.thirst}, 疲労={npc.fatigue}")
        
        # 季節コンテキスト取得
        seasonal_context = future_engine._get_seasonal_prediction_context()
        print(f"季節コンテキスト:")
        print(f"  - 緊急度修正: {seasonal_context['urgency_modifier']:.2f}")
        print(f"  - 資源利用可能性: {seasonal_context['resource_availability']:.2f}")
        print(f"  - 温度ストレス: {seasonal_context['temperature_stress']:.2f}")
        print(f"  - 次季節リスク: {seasonal_context['upcoming_season_risk']:.2f}")
        
        # 行動選択肢生成
        actions = future_engine.generate_action_options()
        print(f"生成された行動選択肢: {len(actions)}個")
        
        # 上位3つの行動を表示
        actions.sort(key=lambda x: x.urgency, reverse=True)
        for j, action in enumerate(actions[:3]):
            rationale = future_engine._get_action_rationale(action)
            print(f"  {j+1}. {action.action_type.value}: 緊急度={action.urgency:.3f}, "
                  f"確率={action.probability:.2f}, 理由={rationale}")
        
        # 予測サマリー
        summary = future_engine.get_prediction_summary()
        if summary['recommended_action']['action']:
            print(f"推奨行動: {summary['recommended_action']['action']} "
                  f"(緊急度: {summary['recommended_action']['urgency']:.3f})")
            print(f"理由: {summary['recommended_action']['rationale']}")

if __name__ == "__main__":
    test_seasonal_future_prediction()