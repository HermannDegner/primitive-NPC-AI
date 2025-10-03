#!/usr/bin/env python3
"""Integrated SSD Enhanced Simulation System.

This module contains the main simulation execution function extracted
from main_backup.py for better modularity and maintainability.
"""

from typing import Optional, Tuple, List, Dict, Any
import sys
import os
import random

# ログレベル制御
VERBOSE_LOGGING = False
DEATH_LOGGING = True
BASIC_LOGGING = True

# SSD Enhanced NPCのインポート
from ssd_enhanced_npc import SSDEnhancedNPC

# ローカルシステムとの連携
from config import *
from environment import Environment
from npc import NPC
from seasonal_system import SeasonalSystem


def run_ssd_enhanced_simulation(max_ticks: int = 200) -> Tuple[Dict, List, List, List]:
    """Enhanced SSD simulation with territorial behavior and collective boundary formation.
    
    This function runs the main simulation loop integrating:
    - SSD Core Engine for sophisticated decision making
    - Territorial behavior system
    - Collective boundary formation
    - Seasonal survival dynamics
    
    Args:
        max_ticks: Maximum number of simulation ticks
        
    Returns:
        Tuple of (final_roster, ssd_logs, environment_logs, seasonal_logs)
    """
    
    print("🌟 Enhanced SSD Simulation Starting...")
    print(f"🎯 Target Ticks: {max_ticks}")
    print("🏘️ Features: Territory System + Collective Boundary Formation")
    print("=" * 60)
    
    # システム初期化
    environment = Environment()
    seasonal_system = SeasonalSystem()
    
    # NPCとSSD Enhanced NPCの作成
    npcs = []
    ssd_npcs = []
    
    # より多様なNPCロスター（16名）
    npc_templates = [
        "SSD_Pioneer_Alpha", "SSD_Scholar_Beta", "SSD_Scholar_Gamma", "SSD_Diplomat_Zeta",
        "SSD_Guardian_Eta", "SSD_Tracker_Theta", "SSD_Loner_Iota", "SSD_Nomad_Kappa",
        "SSD_Pioneer_Nu", "SSD_Adventurer_Xi", "SSD_Scholar_Omicron", "SSD_Warrior_Pi",
        "SSD_Explorer_Rho", "SSD_Sage_Sigma", "SSD_Ranger_Tau", "SSD_Mystic_Phi"
    ]
    
    for i, name in enumerate(npc_templates):
        # 基本NPCの作成
        npc = NPC(
            name=name,
            x=random.randint(15, MAP_WIDTH-15),
            y=random.randint(15, MAP_HEIGHT-15)
        )
        
        # 個体特性の設定（アーキタイプベース）
        archetype = name.split('_')[1]  # Pioneer, Scholar, etc.
        
        if "Scholar" in archetype:
            npc.hunting_skill = 0.4 + random.random() * 0.2
            npc.cooperation_tendency = 0.7 + random.random() * 0.3
        elif "Tracker" in archetype or "Warrior" in archetype:
            npc.hunting_skill = 0.6 + random.random() * 0.3
            npc.cooperation_tendency = 0.3 + random.random() * 0.4
        elif "Loner" in archetype:
            npc.hunting_skill = 0.5 + random.random() * 0.3
            npc.cooperation_tendency = 0.1 + random.random() * 0.3
        else:  # Pioneer, Guardian, Diplomat, etc.
            npc.hunting_skill = 0.5 + random.random() * 0.3
            npc.cooperation_tendency = 0.5 + random.random() * 0.4
        
        npcs.append(npc)
        environment.add_npc(npc)
        
        # SSD Enhanced NPCでラップ
        ssd_npc = SSDEnhancedNPC(npc)
        ssd_npcs.append(ssd_npc)
        
        if BASIC_LOGGING:
            print(f"✨ Created {name} at ({npc.x}, {npc.y}) - " +
                  f"Hunting:{npc.hunting_skill:.2f} Coop:{npc.cooperation_tendency:.2f}")
    
    # ログ保存用
    ssd_logs = []
    environment_logs = []
    seasonal_logs = []
    
    # シミュレーション統計
    territory_formations = 0
    collective_boundaries = 0
    collective_boundary_memberships = []
    active_territories = {}
    territorial_threats_detected = 0
    
    print(f"🚀 Starting simulation with {len(npcs)} NPCs...")
    
    # メインシミュレーションループ
    for tick in range(max_ticks):
        
        # 季節システムの更新
        current_season = seasonal_system.get_current_season(tick)
        seasonal_logs.append({
            'tick': tick,
            'season': current_season,
            'modifiers': seasonal_system.get_seasonal_modifiers(current_season)
        })
        
        # 環境の更新
        environment.ecosystem_step(tick, seasonal_system)
        
        # 生存者チェック（早期終了条件）
        survivors = [npc for npc in npcs if npc.is_alive()]
        if len(survivors) <= 1:
            if BASIC_LOGGING:
                print(f"⚠️ T{tick}: Only {len(survivors)} survivor(s) remaining. Ending simulation.")
            break
        
        # 縄張り脅威検出（捕食者との相互作用）
        territorial_threats_this_tick = 0
        for predator in environment.predators:
            for territory_name, territory_info in active_territories.items():
                # 縄張り内への捕食者侵入検知の簡易実装
                npc = next((n for n in npcs if n.name == territory_name), None)
                if npc and npc.is_alive():
                    dist = abs(predator.x - npc.x) + abs(predator.y - npc.y)
                    if dist < 20:  # 縄張り脅威範囲
                        territorial_threats_this_tick += 1
                        territorial_threats_detected += 1
                        if VERBOSE_LOGGING:
                            print(f"🚨 T{tick}: 縄張り脅威検出 - {territory_name} vs 捕食者")
        
        # 各NPCの行動処理
        for i, (npc, ssd_npc) in enumerate(zip(npcs, ssd_npcs)):
            if not npc.is_alive():
                continue
            
            # 物理整合性メトリクスの計算
            coherence_metrics = ssd_npc.calculate_coherence_metrics(environment)
            
            if VERBOSE_LOGGING:
                print(f"🧬 T{tick}: {npc.name} 物理整合 - " +
                      f"圧力:{coherence_metrics['pressure']:.2f} " +
                      f"緊張:{coherence_metrics['tension']:.2f} " +
                      f"共鳴:{coherence_metrics['resonance']:.2f}")
                
                # SSDエンジンによる優先度計算の詳細ログ
                priorities = ssd_npc.calculate_priorities()
                hunt_priority = priorities.get('hunt', 0)
                print(f"DEBUG_HUNT: {npc.name} coherence:{coherence_metrics['pressure']:.2f} " +
                      f"need:{npc.hunger/100:.2f} skill:{npc.hunting_skill:.2f} " +
                      f"future:{ssd_npc._calculate_future_pressure():.2f} (SSD) priority:{hunt_priority:.3f}")
            
            # 縄張り行動の処理
            territory_formed = ssd_npc.process_territorial_behavior(environment, tick)
            if territory_formed:
                territory_formations += 1
                active_territories[npc.name] = {
                    'tick': tick,
                    'value': ssd_npc.territory_value,
                    'safety': ssd_npc.safety_score
                }
                
                # 集団境界形成もカウント
                collective_boundary_memberships.append({
                    'npc': npc.name,
                    'tick': tick,
                    'type': 'territory_establishment'
                })
            
            # 基本的な生存行動（既存のNPCロジック）
            npc.act(environment, seasonal_system, tick)
            
            # SSDログの記録
            if tick % 5 == 0:  # ログ頻度を調整
                ssd_logs.append({
                    'tick': tick,
                    'npc': npc.name,
                    'coherence': coherence_metrics,
                    'territory': ssd_npc.territory_established,
                    'position': (npc.x, npc.y),
                    'survival_state': {
                        'hunger': npc.hunger,
                        'thirst': npc.thirst,
                        'fatigue': npc.fatigue
                    }
                })
        
        # 環境状態のログ
        if tick % 25 == 0:  # 25ティックごと
            environment_logs.append({
                'tick': tick,
                'survivors': len(survivors),
                'territories': len(active_territories),
                'predators': len(environment.predators),
                'available_berries': len([b for b in environment.berries if b['respawn_time'] <= 0]),
                'cave_water': sum([c['water'] for c in environment.caves]),
                'territorial_threats': territorial_threats_this_tick
            })
        
        # 進行状況の表示
        if tick % 50 == 0 and tick > 0 and BASIC_LOGGING:
            print(f"📊 T{tick}: {len(survivors)} survivors, " +
                  f"{len(active_territories)} territories, " +
                  f"{territory_formations} formations")
    
    # 最終統計の計算
    final_survivors = [npc for npc in npcs if npc.is_alive()]
    
    # 集団境界形成の統計を推定
    # 実際の集団グループの数を推定（重複を除去）
    unique_groups = set()
    for membership in collective_boundary_memberships:
        if 'group_' in str(membership):  # グループIDが含まれる場合
            unique_groups.add(membership.get('group_id', membership['npc']))
    
    actual_collective_boundaries = len(unique_groups)
    
    # 最終結果の表示
    print("\n" + "="*60)
    print("✅ SSD縄張りシミュレーション完了!")
    print(f"📊 最終生存者: {len(final_survivors)}/{len(npcs)}")
    print(f"🏘️ 確立された縄張り: {len(active_territories)}")
    print(f"🤝 集団境界形成: {len(collective_boundary_memberships)} (個人メンバーシップ)")
    print(f"🤝 アクティブ集団境界: {actual_collective_boundaries} (実際のグループ数)")
    
    # 詳細統計
    if BASIC_LOGGING:
        print(f"\n📈 Territorial Statistics:")
        print(f"   - Territory formations: {territory_formations}")
        print(f"   - Territorial threats detected: {territorial_threats_detected}")
        print(f"   - Average territory value: {sum([t['value'] for t in active_territories.values()]) / max(1, len(active_territories)):.2f}")
    
    # 詳細分析（簡易版）
    if len(final_survivors) > 0:
        print("\n🔍 Basic analysis (detailed analysis temporarily disabled)")
        
        # 生存者のアーキタイプ分析
        survivor_archetypes = {}
        for survivor in final_survivors:
            archetype = survivor.name.split('_')[1] if '_' in survivor.name else 'Unknown'
            survivor_archetypes[archetype] = survivor_archetypes.get(archetype, 0) + 1
        
        print(f"   Survivor archetypes: {dict(survivor_archetypes)}")
    
    print("✅ Simulation completed successfully.")
    
    # 最終ロスターの作成
    final_roster = {}
    for npc in npcs:
        if npc.is_alive():
            final_roster[npc.name] = {
                'position': (npc.x, npc.y),
                'hunger': npc.hunger,
                'thirst': npc.thirst,
                'fatigue': npc.fatigue,
                'ticks_survived': max_ticks,
                'territory_established': npc.name in active_territories,
                'hunting_skill': getattr(npc, 'hunting_skill', 0.5),
                'cooperation_tendency': getattr(npc, 'cooperation_tendency', 0.5),
                'archetype': npc.name.split('_')[1] if '_' in npc.name else 'Unknown'
            }
    
    return final_roster, ssd_logs, environment_logs, seasonal_logs


if __name__ == "__main__":
    """直接実行時のテスト"""
    print("🧪 Testing Integrated SSD Enhanced Simulation...")
    
    try:
        roster, ssd_logs, env_logs, seasonal_logs = run_ssd_enhanced_simulation(100)
        print(f"✅ Test completed: {len(roster)} survivors")
        
        # 簡単な結果表示
        for name, data in roster.items():
            print(f"   {name}: {data['archetype']} - Hunting: {data['hunting_skill']:.2f}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()