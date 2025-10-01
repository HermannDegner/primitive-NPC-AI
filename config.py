"""
SSD Village Simulation - Configuration
構造主観力学(SSD)理論に基づく原始村落シミュレーション - 設定ファイル
https://github.com/HermannDegner/Structural-Subjectivity-Dynamics
"""

# SSD理論：性格プリセット
# 各NPCの基本的な性格特性を定義
PIONEER = {"curiosity": 0.9, "sociability": 0.4, "risk_tolerance": 0.8, "empathy": 0.5}
ADVENTURER = {"curiosity": 0.8, "sociability": 0.6, "risk_tolerance": 0.9, "empathy": 0.4}
TRACKER = {"curiosity": 0.6, "sociability": 0.5, "risk_tolerance": 0.6, "empathy": 0.7}
SCHOLAR = {"curiosity": 0.95, "sociability": 0.3, "risk_tolerance": 0.4, "empathy": 0.8}
WARRIOR = {"curiosity": 0.4, "sociability": 0.6, "risk_tolerance": 0.9, "empathy": 0.5}
GUARDIAN = {"curiosity": 0.3, "sociability": 0.8, "risk_tolerance": 0.7, "empathy": 0.9}
HEALER = {"curiosity": 0.5, "sociability": 0.9, "risk_tolerance": 0.3, "empathy": 0.95}
DIPLOMAT = {"curiosity": 0.6, "sociability": 0.95, "risk_tolerance": 0.4, "empathy": 0.8}
FORAGER = {"curiosity": 0.7, "sociability": 0.7, "risk_tolerance": 0.5, "empathy": 0.6}
LEADER = {"curiosity": 0.5, "sociability": 0.9, "risk_tolerance": 0.7, "empathy": 0.7}
LONER = {"curiosity": 0.8, "sociability": 0.2, "risk_tolerance": 0.6, "empathy": 0.3}
NOMAD = {"curiosity": 0.85, "sociability": 0.4, "risk_tolerance": 0.8, "empathy": 0.4}

# 性格プリセットのリスト
PERSONALITY_PRESETS = [
    PIONEER, ADVENTURER, TRACKER, SCHOLAR, WARRIOR, GUARDIAN,
    HEALER, DIPLOMAT, FORAGER, LEADER, LONER, NOMAD
]

# シミュレーション設定
DEFAULT_WORLD_SIZE = 90
DEFAULT_BERRY_COUNT = 120
DEFAULT_HUNTING_GROUND_COUNT = 60
DEFAULT_WATER_SOURCE_COUNT = 40
DEFAULT_CAVE_COUNT = 25

# SSD理論パラメータ
DEFAULT_KAPPA = 0.1  # 基本整合慣性
DEFAULT_TEMPERATURE = 1.0  # 温度パラメータ
EXPLORATION_MODE_DURATION_THRESHOLD = 15  # 探索モード継続時間閾値

# 生存パラメータ
HUNGER_DANGER_THRESHOLD = 160
THIRST_DANGER_THRESHOLD = 140
FATIGUE_DANGER_THRESHOLD = 80

# 社会的相互作用パラメータ
TERRITORY_RADIUS = 5
OXYTOCIN_EFFECT_RADIUS = 8
GROUP_PROTECTION_RADIUS = 10

# 狩りシステムパラメータ
HUNTING_SETTINGS = {
    'solo_success_rate': 0.15,      # 単独狩りの成功率
    'group_success_base': 0.4,      # 集団狩りの基本成功率
    'group_success_per_member': 0.1, # メンバー1人あたりの成功率増加
    'max_group_bonus': 0.4,         # 集団ボーナスの上限
    'danger_rate': 0.25,            # 狩り中の怪我確率（成功・失敗関係なく）
    'critical_injury_rate': 0.05,   # 重症確率（怪我の中での割合）
    'meat_decay_rate': 0.15,        # 肉の腐敗率(1ティックあたり)
    'meat_nutrition_value': 0.8,    # 肉の栄養価(ベリーの約2.7倍)
    'sharing_pressure_threshold': 0.7, # 分配圧力の閾値
    'hunt_fatigue_cost': 15,        # 狩り行動の疲労コスト
    'hunt_organization_threshold': 3 # 集団狩り組織化の最低人数
}

# 獲物の種類
PREY_TYPES = {
    'small_game': {
        'meat_amount': 0.6,
        'difficulty': 0.3,
        'danger': 0.1,
        'required_hunters': 1
    },
    'medium_game': {
        'meat_amount': 2.0,
        'difficulty': 0.6,
        'danger': 0.3,
        'required_hunters': 2
    },
    'large_game': {
        'meat_amount': 5.0,
        'difficulty': 0.8,
        'danger': 0.5,
        'required_hunters': 4
    }
}

# 重症システム設定
CRITICAL_INJURY_SETTINGS = {
    'duration_min': 50,             # 最低回復時間
    'duration_max': 120,            # 最大回復時間
    'mobility_loss': True,          # 移動不可
    'care_effectiveness': 0.3,      # 看護の回復効果
    'food_sharing_rate': 0.8,       # 重症者への食料分配率
    'witness_empathy_boost': 0.15,  # 重症者目撃時の共感増加
    'empathy_decay_rate': 0.98,     # 共感の自然減衰率(1ティックあたり)
    'max_empathy_boost': 0.4,       # 共感増加の上限
    'witness_range': 12,            # 重症者を目撃する範囲
}

# 信頼関係システム設定（情動的熟量ベース）
TRUST_SYSTEM_SETTINGS = {
    'max_trust_level': 1.0,         # 最大信頼度
    'min_trust_level': 0.0,         # 最低信頼度
    'neutral_trust': 0.5,           # 初期中立値
    'high_trust_threshold': 0.75,   # 高信頼関係の闾値
    'memory_decay_rate': 0.995,     # 記憶の鮮明さの減衰（信頼度ではない）
    'min_memory_strength': 0.05,    # 完全には忘れない
}

# 情動的熟量と信頼庤定（一回で確定）
TRUST_EVENTS = {
    # 生死に関わる支援（最高の熟量）
    'life_saved_critical': {'base_trust': 0.9, 'emotional_heat': 1.0},
    'care_during_injury': {'base_trust': 0.8, 'emotional_heat': 0.9},
    
    # 飢饿時の支援（高い熟量）
    'food_in_hunger': {'base_trust': 0.7, 'emotional_heat': 0.8},
    'meat_share_starving': {'base_trust': 0.75, 'emotional_heat': 0.85},
    
    # 危陾共有（中程度の熟量）
    'hunt_together_success': {'base_trust': 0.6, 'emotional_heat': 0.6},
    'hunt_together_injury': {'base_trust': 0.65, 'emotional_heat': 0.7},
    
    # 日常的支援（低い熟量）
    'casual_food_share': {'base_trust': 0.55, 'emotional_heat': 0.3},
    'hunt_cooperation': {'base_trust': 0.52, 'emotional_heat': 0.2},
    
    # 裏切りや危害（ネガティブな熟量）
    'abandon_in_crisis': {'base_trust': 0.1, 'emotional_heat': 0.9},
    'food_theft': {'base_trust': 0.2, 'emotional_heat': 0.6},
}

# SSD理論統合型経験システム設定
EXPERIENCE_SYSTEM_SETTINGS = {
    # 経験値の上限は意味圧(E)によって決まる
    'base_learning_rate': 0.1,      # 基本学習速度
    'kappa_growth_limit': 0.95,     # κの最大成長率(意味圧の95%まで)
    'experience_decay': 0.999,      # 経験の微細な減衰(使わないと錆びる)
    'min_experience': 0.01,         # 最小経験値
    
    # 各活動の経験係数
    'hunting_exp_rate': 0.15,       # 狩り経験の獲得率
    'exploration_exp_rate': 0.08,   # 探索経験の獲得率
    'survival_exp_rate': 0.05,      # 野宿経験の獲得率
    'care_exp_rate': 0.12,          # 看護経験の獲得率
    'social_exp_rate': 0.06,        # 社交経験の獲得率
    'predator_awareness_exp_rate': 0.1,  # 捕食者警戒経験の獲得率
    
    # 経験による効率向上
    'max_efficiency_boost': 0.5,    # 最大効率向上(50%まで)
    'experience_threshold': 2.0,     # 効率向上が顕著になる経験値
}

# 捕食者警戒経験システム設定
PREDATOR_AWARENESS_SETTINGS = {
    'escape_bonus': 0.3,            # 逃走成功率ボーナス (経験値×30%)
    'detection_bonus': 0.25,        # 早期発見ボーナス (経験値×25%)
    'avoidance_bonus': 0.2,         # 遭遇回避ボーナス (経験値×20%)
    'group_alert_bonus': 0.15,      # 集団警戒ボーナス (経験値×15%)
    'base_escape_rate': 0.4,        # 基本逃走成功率
    'base_detection_rate': 0.2,     # 基本早期発見率
    'base_avoidance_rate': 0.05,    # 基本遭遇回避率
    'alert_range_base': 15,         # 基本警告範囲
    'alert_range_bonus': 10,        # 経験による警告範囲拡大
    'max_escape_rate': 0.95,        # 最大逃走成功率
    'max_detection_rate': 0.8,      # 最大早期発見率
    'max_avoidance_rate': 0.4,      # 最大遭遇回避率
}

# 捕食者狩り設定
PREDATOR_HUNTING = {
    'success_rate_base': 0.15,        # 基本成功率（超低確率）
    'group_size_bonus': 0.05,         # グループサイズボーナス（人数-1×5%）
    'experience_bonus': 0.2,          # 経験ボーナス（経験値×20%）
    'weapon_bonus': 0.15,             # 武器ボーナス（将来実装）
    'injury_rate': 0.6,               # 怪我確率（成功時でも60%）
    'severe_injury_rate': 0.3,        # 重症確率（失敗時30%）
    'death_rate_on_failure': 0.4,     # 失敗時死亡確率
    'meat_reward': 3.0,               # 成功時の肉獲得量（通常の3倍）
    'experience_gain': 0.2,           # 経験値獲得（大幅）
    'detection_range': 15,            # 捕食者検出範囲
    'group_formation_range': 8,       # グループ形成範囲
    'max_group_size': 4,              # 最大グループサイズ
}

# 狩場競合設定
HUNTING_GROUND_COMPETITION = {
    'competition_radius': 20,          # 競合範囲
    'human_penalty_per_predator': 0.15, # 捕食者1匹につき人間への15%ペナルティ
    'prey_depletion_rate': 0.1,       # 獲物枯渇率
    'competition_aggression': 0.3,     # 競合時の攻撃性増加
    'territorial_bonus': 0.2,         # 縄張り防衛ボーナス
}

# 動物（獲物）設定
PREY_ANIMALS = {
    'deer': {
        'spawn_count': 8,              # 初期個体数
        'spawn_rate': 0.05,
        'meat_value': 1.0,
        'difficulty': 0.3,
        'predator_preference': 0.8     # 捕食者の好み
    },
    'rabbit': {
        'spawn_count': 12,             # 初期個体数
        'spawn_rate': 0.1,
        'meat_value': 0.3,
        'difficulty': 0.1,
        'predator_preference': 0.4
    },
    'boar': {
        'spawn_count': 4,              # 初期個体数
        'spawn_rate': 0.03,
        'meat_value': 2.0,
        'difficulty': 0.7,
        'predator_preference': 0.6
    }
}