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