#!/usr/bin/env python3
"""Enhanced SSD simulation integrating boundaries, smart environment and seasons."""
import random
import os
import csv
import json
from config import (
    DEFAULT_WORLD_SIZE,
    PIONEER,
    ADVENTURER,
    SCHOLAR,
    WARRIOR,
    HEALER,
    DIPLOMAT,
    GUARDIAN,
    TRACKER,
    LONER,
    NOMAD,
    FORAGER,
    LEADER,
)
from environment import Environment, Predator
from npc import NPC
from smart_environment import SmartEnvironment
from ssd_core import PhysicalStructureSystem, SSDCore
from subjective_boundary_system import (
    integrate_subjective_boundary_system,
    SubjectiveBoundarySystem,
)
from seasonal_system import SeasonalSystem

from utils import distance_between

# グローバル境界システム
boundary_system = None
seasonal_system = None  # 季節システムをグローバルに


def adapt_action_to_season(action, season, modifiers, npc):
    """季節に応じて行動を適応させる"""
    import random

    # 冬（season 3）の場合、狩猟や貯蔵を優先
    if season == 3:  # 冬
        if action == "foraging" and random.random() < 0.7:  # 70%の確率で狩猟に変更
            return "hunting"
        elif action == "exploration" and random.random() < 0.5:  # 50%の確率で休息に変更
            return "resting"

    # 夏（season 1）の場合、探索を増やす
    elif season == 1:  # 夏
        if action == "resting" and random.random() < 0.3:  # 30%の確率で探索に変更
            return "exploration"

    # 春（season 0）の場合、社交を増やす
    elif season == 0:  # 春
        if action == "resting" and random.random() < 0.4:  # 40%の確率で社交に変更
            return "social"

    # 秋（season 2）の場合、貯蔵を意識
    elif season == 2:  # 秋
        if action == "exploration" and random.random() < 0.3:  # 30%の確率で採取に変更
            return "foraging"

    return action  # そのままの行動


def run_enhanced_ssd_simulation(ticks=800):
    """SSD完全統合シミュレーション実行 + 季節システム（長期間）"""

    # 季節システム初期化
    global seasonal_system
    seasonal_system = SeasonalSystem(season_length=100)  # 1季節100ティック（2年間実行）

    # シミュレーション統計変数 (currently unused placeholders)
    # _total_predator_hunting_attempts = 0
    # _total_predator_kills = 0
    global boundary_system

    # ランダムシード設定
    seed = random.randint(1, 1000)
    random.seed(seed)

    # シミュレーション開始メッセージ
    print(f"Enhanced SSD Simulation with SEASONAL SYSTEM - Random seed: {seed}")
    print("FOUR SEASONS OMNIVORE SURVIVAL CHALLENGE")
    print("   Base: Berries: 24 (SEASONAL VARIATION), Water: 20, Hunt: 30, Caves: 10")
    print("   SEASONAL EFFECTS: Resource fluctuation, behavior changes, social dynamics")

    # 環境設定（協力テスト用 - 資源を増やして生存を容易に）
    env = Environment(
        size=DEFAULT_WORLD_SIZE,
        n_berry=48,  # ベリーを倍増 - 16人に3個/人
        n_hunt=50,  # 狩猟場を増加 - 16人に約3個/人
        n_water=35,  # 水源を増加 - 16人に2個以上/人
        n_caves=20,  # 洞窟を倍増 - 十分な避難所
        enable_smart_world=True,
    )

    # 捕食者の初期化
    predator_positions = [(15, 85), (85, 15), (50, 20), (20, 50)]  # 捕食者の位置を設定
    for i, pos in enumerate(predator_positions):
        predator = Predator(pos, aggression=0.7)  # 捕食者を作成
        predator.hunt_radius = 12  # 狩猟範囲を設定
        env.predators.append(predator)  # 環境に捕食者を追加
        print(f"Added Predator_{i+1} at position {predator.x}, {predator.y}")

    print("HUNT EXPANSION MODE - 30 Hunt Sources")

    # スマート環境とバウンダリシステム初期化
    smart_env = SmartEnvironment(world_size=DEFAULT_WORLD_SIZE)
    boundary_system = SubjectiveBoundarySystem()
    experience_handler, boundary_checker = integrate_subjective_boundary_system()

    # NPCロスター作成
    roster = create_npc_roster(env)
    boundary_system.set_npc_roster(roster)

    print("=" * 60)

    # メインシミュレーションループ
    logs, ssd_decision_logs, environment_intelligence_logs, seasonal_logs = run_simulation_loop(
        seasonal_system, env, smart_env, roster, experience_handler, boundary_checker, ticks
    )

    return roster, ssd_decision_logs, environment_intelligence_logs, seasonal_logs


def create_npc_roster(env):
    """NPCロスターの作成"""
    roster = {}

    # NPCの作成（SSD物理構造システム統合）- 16人バージョン
    npc_configs = [
        ("SSD_Pioneer_Alpha", PIONEER, (20, 20)),
        ("SSD_Adventurer_Beta", ADVENTURER, (25, 25)),
        ("SSD_Scholar_Gamma", SCHOLAR, (30, 30)),
        ("SSD_Warrior_Delta", WARRIOR, (35, 35)),
        ("SSD_Healer_Echo", HEALER, (40, 40)),
        ("SSD_Diplomat_Zeta", DIPLOMAT, (45, 45)),
        ("SSD_Guardian_Eta", GUARDIAN, (50, 20)),
        ("SSD_Tracker_Theta", TRACKER, (55, 25)),
        ("SSD_Loner_Iota", LONER, (60, 30)),
        ("SSD_Nomad_Kappa", NOMAD, (65, 35)),
        ("SSD_Forager_Lambda", FORAGER, (20, 50)),
        ("SSD_Leader_Mu", LEADER, (25, 55)),
        ("SSD_Pioneer_Nu", PIONEER, (30, 60)),
        ("SSD_Adventurer_Xi", ADVENTURER, (35, 65)),
        ("SSD_Scholar_Omicron", SCHOLAR, (60, 50)),
        ("SSD_Warrior_Pi", WARRIOR, (65, 55)),
    ]

    for name, preset, start_pos in npc_configs:
        npc = NPC(name, preset, env, roster, start_pos, boundary_system)
        # SSD物理構造システムを追加
        npc.physical_system = PhysicalStructureSystem(npc)
        # 季節関連属性初期化
        npc.seasonal_curiosity_mod = 0.0
        npc.seasonal_social_mod = 0.0
        roster[name] = npc
        # ソーシャルネットワークを境界システムに統合
        npc.integrate_social_network_into_boundary()
        print(f"Created {name} with SSD 4-Layer System + Seasonal Adaptation")

    print(f"\\nTotal NPCs with SSD Integration: {len(roster)}")
    
    # 初期集団境界の作成
    create_initial_collective_boundaries(roster, boundary_system)
    
    return roster


def run_simulation_loop(
    seasonal_system, env, smart_env, roster, experience_handler, boundary_checker, ticks
):
    """メインシミュレーションループ"""

    # ログ初期化
    logs = []
    ssd_decision_logs = []
    environment_intelligence_logs = []
    seasonal_logs = []

    # --- NPC状態時系列ロガー初期化 ---------------------------------
    # 出力先: ./logs/npc_state_timeseries.csv
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    csv_path = os.path.join(logs_dir, "npc_state_timeseries.csv")
    try:
        csv_file = open(csv_path, "w", newline="", encoding="utf-8")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            [
                "t",
                "npc",
                "E",
                "mean_kappa",
                "kappa_json",
                "mean_I",
                "I_json",
                "max_I",
                "owns_territory",
            ]
        )
    except Exception as e:
        csv_file = None
        csv_writer = None
        print(f"Warning: could not open CSV logger at {csv_path}: {e}")
    # ---------------------------------------------------------------

    for t in range(1, ticks + 1):
        # 季節効果の適用
        current_season_name = seasonal_system.get_season_name(t)
        seasonal_modifiers = seasonal_system.apply_seasonal_effects(env, list(roster.values()), t)

        # 季節変化の通知
        if t % seasonal_system.season_length == 1:
            print(f"\\n🌍 T{t}: SEASON CHANGE TO {current_season_name}!")
            print(
                f"   📊 Effects: Berry×{seasonal_modifiers.get('berry_abundance', 1.0):.1f}, "
                f"Prey×{seasonal_modifiers.get('prey_activity', 1.0):.1f}, "
                f"Predator×{seasonal_modifiers.get('predator_activity', 1.0):.1f}"
            )

        # エコシステム更新
        env.ecosystem_step(list(roster.values()), t)

        # 捕食者狩り処理 - 食料制限テスト用にコメントアウト
        process_predator_hunting(env, roster, seasonal_modifiers, current_season_name, t)

        # 捕食者攻撃処理 - 食料制限テスト用にコメントアウト
        # predator_attacks = process_predator_attacks(env, roster, current_season_name, t)
        predator_attacks = 0  # 捕食者なしなので攻撃もなし

        # スマート環境分析
        smart_env.analyze_npc_impact(list(roster.values()), t)

        # NPC個別処理
        process_npc_decisions(
            roster,
            env,
            smart_env,
            seasonal_modifiers,
            experience_handler,
            boundary_checker,
            ssd_decision_logs,
            seasonal_logs,
            current_season_name,
            t,
        )

        # 死亡NPCを除去
        dead_npcs = [name for name, npc in roster.items() if not npc.alive]
        for name in dead_npcs:
            _cause = "starvation" if roster[name].hunger > 150 else "dehydration"
            print(
                (
                    f"  💀 T{t} ({current_season_name}): "
                    f"STARVATION/DEHYDRATION DEATH - {name} died from {_cause}!"
                )
            )
            del roster[name]

        # 進捗表示
        display_progress(roster, seasonal_modifiers, current_season_name, predator_attacks, t)

        # 環境情報記録
        if t % 25 == 0:
            env_state = smart_env.get_intelligence_summary()
            env_state["t"] = t
            environment_intelligence_logs.append(env_state)

        # ティックごとの NPC 状態を CSV に書き出し
        if csv_writer is not None:
            try:
                for npc in roster.values():
                    if not npc.alive:
                        continue
                    # kappa と I を辞書化して JSON にシリアライズ
                    try:
                        kappa_dict = {k: float(v) for k, v in dict(npc.kappa).items()}
                    except Exception:
                        kappa_dict = {k: float(v) for k, v in getattr(npc, "kappa", {}).items()}

                    try:
                        I_dict = {k: float(v) for k, v in dict(npc.I_by_target).items()}
                    except Exception:
                        I_dict = {k: float(v) for k, v in getattr(npc, "I_by_target", {}).items()}

                    mean_kappa = (
                        sum(kappa_dict.values()) / len(kappa_dict) if len(kappa_dict) > 0 else 0.0
                    )
                    mean_I = sum(I_dict.values()) / len(I_dict) if len(I_dict) > 0 else 0.0
                    max_I = max(I_dict.values()) if len(I_dict) > 0 else 0.0
                    owns_territory = 1 if getattr(npc, "territory", None) is not None else 0

                    csv_writer.writerow(
                        [
                            t,
                            npc.name,
                            float(getattr(npc, "E", 0.0)),
                            mean_kappa,
                            json.dumps(kappa_dict, ensure_ascii=False),
                            mean_I,
                            json.dumps(I_dict, ensure_ascii=False),
                            max_I,
                            owns_territory,
                        ]
                    )
            except Exception as e:
                print(f"Warning: failed to write npc state to CSV at t={t}: {e}")

    # CSV ファイルを閉じる
    try:
        if csv_file is not None:
            csv_file.close()
    except Exception:
        pass

    return logs, ssd_decision_logs, environment_intelligence_logs, seasonal_logs


def process_predator_hunting(env, roster, seasonal_modifiers, current_season_name, t):
    """捕食者狩り処理"""
    hunting_chance = 0.02 * seasonal_modifiers.get("predator_activity", 1.0)

    for npc in roster.values():
        if npc.alive and random.random() < hunting_chance:
            hunt_result = npc.attempt_predator_hunting(env.predators, list(roster.values()), t)
            if hunt_result:
                if hunt_result.get("predator_killed"):
                    print(
                        f"  🏹 T{t} ({current_season_name}): PREDATOR HUNTING SUCCESS"
                    )
                    print(f"    group_size={hunt_result['group_size']}")
                    # 境界システムに成功体験を記録
                    boundary_system.process_subjective_experience(
                        npc,
                        "predator_defense_success",
                        "group_victory",
                        {"group_size": hunt_result["group_size"]},
                        t,
                    )
                elif hunt_result.get("casualties"):
                    casualties = ", ".join(hunt_result["casualties"]) if hunt_result.get("casualties") else ""
                    print(f"  💀 T{t} ({current_season_name}): PREDATOR HUNTING FAILED")
                    if casualties:
                        print(f"    casualties: {casualties}")


def process_predator_attacks(env, roster, current_season_name, t):
    """捕食者攻撃処理"""
    predator_attacks = 0
    for predator in env.predators:
        if predator.alive:
            attack_result = predator.hunt_step(list(roster.values()), t)
            if attack_result:
                predator_attacks += 1
                if attack_result.get("victim"):
                    print(f"  💀 T{t} ({current_season_name}): PREDATOR KILL - {attack_result['victim']}")
                    # 境界システムに脅威体験を記録
                    for npc in roster.values():
                        if npc.alive and npc.distance_to((predator.x, predator.y)) < 15:
                            boundary_system.process_subjective_experience(
                                npc,
                                "predator_threat_witness",
                                "external_danger",
                                {"victim": attack_result["victim"]},
                                t,
                            )
    return predator_attacks


def process_npc_decisions(
    roster,
    env,
    smart_env,
    seasonal_modifiers,
    experience_handler,
    boundary_checker,
    ssd_decision_logs,
    seasonal_logs,
    current_season_name,
    t,
):
    """NPC個別決定処理"""

    for npc in roster.values():
        if not npc.alive:
            continue

        env_feedback = smart_env.provide_npc_environmental_feedback(npc, t)

        if hasattr(npc, "physical_system"):
            # 捕食者脅威計算
            predator_threat = 0.0
            for predator in env.predators:
                if predator.alive:
                    distance = ((npc.x - predator.x) ** 2 + (npc.y - predator.y) ** 2) ** 0.5
                    if distance < 20:
                        predator_threat += max(0, (20 - distance) / 20)

            # 季節圧力の追加
            seasonal_pressure = seasonal_modifiers.get("survival_pressure", 0.0)

            # 外部刺激作成（季節統合版）
            exploration_base = 0.3 + (npc.curiosity * 0.4)
            exploration_seasonal = exploration_base + npc.seasonal_curiosity_mod

            external_stimuli = {
                "exploration_pressure": max(0, exploration_seasonal),
                "environmental_pressure": env_feedback.get("environmental_pressure", 0.0)
                + seasonal_pressure,
                "resource_pressure": env_feedback.get("resource_scarcity", 0.0)
                * seasonal_modifiers.get("berry_abundance", 1.0),
                "social_pressure": 0.1 + (npc.sociability * 0.2) + npc.seasonal_social_mod,
                "survival_pressure": max(0, (npc.hunger + npc.thirst - 100) / 200)
                + seasonal_pressure,
                "predator_threat": predator_threat,
                "seasonal_stress": seasonal_modifiers.get("temperature_stress", 0.0),
            }

            # SSD構造力学処理
            result = npc.physical_system.process_structural_dynamics(external_stimuli)
            decision = result["final_decision"]

            # 中央での E 更新（意味圧 p_norm と整合流 j_norm を用いる）
            p_norm = result.get("p_norm", 0.0)
            j_norm = result.get("j_norm", 0.0)
            # call SSDCore.update_E to update npc.E
            try:
                SSDCore.update_E(npc, p_norm, j_norm)
            except Exception as e:
                print(f"Error updating E for {npc.name}: {e}")

            # ログ記録
            log_npc_decision(
                npc,
                decision,
                result,
                env_feedback,
                seasonal_modifiers,
                current_season_name,
                ssd_decision_logs,
                seasonal_logs,
                t,
            )

            # 境界システム処理
            process_boundary_interactions(
                npc, decision, roster, experience_handler, boundary_checker, t
            )

            # 決定に基づく実際の行動実行（季節適応付き）
            action = decision.get("action", "resting")
            seasonal_modifiers = seasonal_system.get_seasonal_modifiers(t)
            current_season = seasonal_system.get_current_season(t)

            # 季節による行動適応
            adapted_action = adapt_action_to_season(action, current_season, seasonal_modifiers, npc)

            if adapted_action == "foraging":
                npc.seek_food(t)
            elif adapted_action == "exploration":
                npc.explore_for_resource(t, "any")
            elif adapted_action == "resting":
                npc.seek_rest(t)
            elif adapted_action == "social":
                # 協力行動を強化
                if npc.attempt_social_cooperation(t, roster):
                    pass  # 協力成功
                else:
                    npc.explore_or_socialize(t)  # フォールバック
            elif adapted_action == "territory":
                if not npc.territory:
                    npc.claim_cave_territory(npc.pos(), t)
                else:
                    npc.invite_nearby_to_territory(t)
            elif adapted_action == "hunting":  # 季節適応で追加された狩猟優先
                npc.attempt_solo_hunt(t)
            elif adapted_action == "drink":
                npc.execute_predictive_drink(t)

            # 危機的状況からの学習
            life_crisis = npc.exploration_manager.calculate_life_crisis_pressure()
            if life_crisis > 1.0:
                # 現在の場所を特定
                current_location = "unknown"
                npc_pos = npc.pos()
                
                # 最も近いリソースを場所として特定
                nearest_water = npc.env.nearest_nodes(npc_pos, npc.env.water_sources, k=1)
                nearest_berry = npc.env.nearest_nodes(npc_pos, npc.env.berries, k=1)
                nearest_hunt = npc.env.nearest_nodes(npc_pos, npc.env.hunting_grounds, k=1)
                
                if nearest_water:
                    water_dist = distance_between(npc_pos, nearest_water[0])
                    if water_dist < 5:
                        current_location = "water_source"
                if nearest_berry and not current_location.startswith("water"):
                    berry_dist = distance_between(npc_pos, nearest_berry[0])
                    if berry_dist < 5:
                        current_location = "berry_patch"
                if nearest_hunt and current_location == "unknown":
                    hunt_dist = distance_between(npc_pos, nearest_hunt[0])
                    if hunt_dist < 5:
                        current_location = "hunting_ground"
                
                # 危機の種類を判定
                crisis_type = "general"
                if npc.thirst > 120:
                    crisis_type = "thirst"
                elif npc.hunger > 120:
                    crisis_type = "hunger"
                elif npc.fatigue > 120:
                    crisis_type = "fatigue"
                
                # 学習実行
                npc.learn_from_crisis(t, crisis_type, current_location)


def log_npc_decision(
    npc,
    decision,
    result,
    env_feedback,
    seasonal_modifiers,
    current_season_name,
    ssd_decision_logs,
    seasonal_logs,
    t,
):
    """NPCの決定をログに記録"""

    # SSD決定ログ
    ssd_decision_logs.append(
        {
            "t": t,
            "npc": npc.name,
            "decision_action": decision["action"],
            "decision_type": decision["type"],
            "environmental_pressure": env_feedback.get("environmental_pressure", 0),
            "resource_scarcity": env_feedback.get("resource_scarcity", 0),
            "meaning_pressure": result.get("meaning_pressure", 0),
            "leap_probability": result.get("leap_probability", 0),
            "curiosity": npc.curiosity,
            "exploration_mode": npc.exploration_mode,
        }
    )

    # 季節ログ
    seasonal_logs.append(
        {
            "t": t,
            "season": current_season_name,
            "npc": npc.name,
            "seasonal_pressure": seasonal_modifiers.get("survival_pressure", 0.0),
            "temperature_stress": seasonal_modifiers.get("temperature_stress", 0.0),
            "resource_modifier": seasonal_modifiers.get("berry_abundance", 1.0),
            "exploration_mod": npc.seasonal_curiosity_mod,
            "social_mod": npc.seasonal_social_mod,
        }
    )


def process_boundary_interactions(npc, decision, roster, experience_handler, boundary_checker, t):
    """境界システムの相互作用処理"""

    # 決定をNPC行動に反映
    if decision["type"] == "leap":
        npc.exploration_mode = True

    # 主観的境界システム: 経験処理
    action_context = {
        "action": decision.get("action", "foraging"),
        "target_location": (npc.x, npc.y),
        "decision_type": decision["type"],
    }

    # 成功/失敗をランダムに決定（より詳細な実装が可能）
    success = random.random() < 0.7
    experience_result = {"success": success}

    # --- テスト用フラグ: 人→人共有イベントを強制発生させる（短期検証用） ---
    # config のフラグで制御
    from config import TEST_FORCE_PERSON_SHARING

    if TEST_FORCE_PERSON_SHARING and action_context.get("action") in ("foraging", "cooperate"):
        # 近傍に alive な NPC がいれば一人選んで強制的に共有イベントを発生
        nearby = [
            o for o in roster.values() if o.alive and o != npc and npc.distance_to(o.pos()) <= 6
        ]
        if nearby:
            partner = random.choice(nearby)
            action_context["target_npc"] = partner
            action_context["social_interaction"] = True
            # 成功フラグと回復量（リリーフ）を含める
            experience_result = {"success": True, "recovery": 30}

    experience_handler(npc, experience_result, action_context, t)

    # 他NPCとの相互作用チェック
    for other_npc in roster.values():
        if other_npc.alive and other_npc != npc:
            distance = npc.distance_to((other_npc.x, other_npc.y))
            if distance < 12:
                interaction_types = ["social_approach"]
                if action_context["action"] == "foraging":
                    interaction_types.append("resource_use")
                if distance < 8:
                    interaction_types.append("territory_enter")

                for interaction_type in interaction_types:
                    interaction_result = boundary_checker(
                        npc, other_npc, interaction_type, action_context, t
                    )

                    if not interaction_result["allowed"]:
                        if interaction_result["response"] == "aggressive_defense":
                            print(f"⚔️ T{t}: BOUNDARY CONFLICT - {interaction_result['message']}")
                        elif interaction_result["response"] == "firm_warning":
                            print(f"⚠️ T{t}: BOUNDARY WARNING - {interaction_result['message']}")
                    elif interaction_result["response"] == "cooperative":
                        print(f"🤝 T{t}: BOUNDARY SHARING - {interaction_result['message']}")


def display_progress(roster, seasonal_modifiers, current_season_name, predator_attacks, t):
    """進捗表示"""
    if t % 25 == 0:
        alive_count = len([npc for npc in roster.values() if npc.alive])
        exploration_count = len(
            [npc for npc in roster.values() if npc.alive and npc.exploration_mode]
        )

        # 境界形成状況をチェック
        total_boundaries = sum(
            len(boundaries["people"]) + len(boundaries["places"]) + len(boundaries["resources"])
            for boundaries in boundary_system.subjective_boundaries.values()
        )
        collective_count = len(boundary_system.collective_boundaries)
        violations_today = sum(
            len([v for v in violations if t - v["tick"] < 25])
            for violations in boundary_system.boundary_violations.values()
        )

        print(
            f"T{t} ({current_season_name}): 👥{alive_count} survivors, 🔍{exploration_count} exploring"
        )
        if total_boundaries > 0 or collective_count > 0 or violations_today > 0:
            print(
                f"      🏘️{total_boundaries} boundaries, 🤝{collective_count} collectives, 🚫{violations_today} violations"
            )

        # 季節サマリー
        berry_mod = seasonal_modifiers.get("berry_abundance", 1.0)
        temp_stress = seasonal_modifiers.get("temperature_stress", 0.0)
        print(f"      🌍 Resources: {berry_mod:.1f}x, Temperature stress: {temp_stress:.1f}")

        # 季節サマリー


def create_initial_collective_boundaries(roster, boundary_system):
    """初期集団境界の作成 - 全員を一つの協力グループに"""
    
    # 全員を一つのグループに
    npc_names = list(roster.keys())
    group1_names = npc_names  # 全員
    group2_names = []  # 空
    
    # グループ1の集団境界作成
    group1_id = "collective_group_united"
    boundary_system.collective_boundaries[group1_id] = set(group1_names)
    boundary_system.collective_identity[group1_id] = {
        "core_values": ["cooperation", "survival", "united_territory"],
        "shared_experiences": ["initial_grouping", "resource_sharing"],
        "activity_type": "settlement",
        "group_name": "United Settlement"
    }
    
    # グループ2は作成しない
    
    # グループ内のメンバーを相互に境界として設定
    for group_names, group_id in [(group1_names, group1_id)]:
        for member_name in group_names:
            for other_member in group_names:
                if member_name != other_member:
                    # グループメンバー同士の境界強度を高く設定
                    boundary_system.subjective_boundaries[member_name]["people"].add(other_member)
                    boundary_system.boundary_strength[member_name][other_member] = 0.8
                    
                    # 信頼も初期設定
                    if member_name in roster and other_member in roster:
                        roster[member_name].trust_levels[other_member] = 0.6  # 初期信頼
                        roster[other_member].trust_levels[member_name] = 0.6
    
    print(f"Created initial collective boundaries:")
    print(f"  United Settlement: {len(group1_names)} members - {group1_names}")
    return
