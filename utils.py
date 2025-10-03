"""
SSD Village Simulation - Utilities
構造主観力学(SSD)理論に基づく原始村落シミュレーション - ユーティリティ関数
"""

import math
import random


def distance_between(pos1, pos2):
    """2点間の距離を計算"""
    return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def find_nearest_position(current_pos, target_positions, exclude=None):
    """最も近い位置を見つける"""
    if not target_positions:
        return None

    valid_positions = target_positions.copy()
    if exclude:
        valid_positions = {k: v for k, v in valid_positions.items() if k not in exclude}

    if not valid_positions:
        return None

    distances = [
        (name, pos, distance_between(current_pos, pos)) for name, pos in valid_positions.items()
    ]
    distances.sort(key=lambda x: x[2])

    return distances[0]  # (name, position, distance)


def weighted_random_choice(options, weights):
    """重み付きランダム選択"""
    if not options or not weights or len(options) != len(weights):
        return None

    total_weight = sum(weights)
    if total_weight <= 0:
        return random.choice(options)

    rand_val = random.uniform(0, total_weight)
    cumulative = 0

    for option, weight in zip(options, weights):
        cumulative += weight
        if rand_val <= cumulative:
            return option

    return options[-1]  # フォールバック


def clamp(value, min_val, max_val):
    """値を指定範囲内にクランプ"""
    return max(min_val, min(max_val, value))


def normalize_vector(dx, dy):
    """ベクトルを正規化"""
    magnitude = math.sqrt(dx**2 + dy**2)
    if magnitude == 0:
        return 0, 0
    return dx / magnitude, dy / magnitude


def lerp(a, b, t):
    """線形補間"""
    return a + (b - a) * clamp(t, 0.0, 1.0)


def smooth_step(t):
    """スムーズステップ関数"""
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian_random(mean=0.0, std_dev=1.0):
    """ガウシアン乱数生成"""
    return random.gauss(mean, std_dev)


def probability_check(probability):
    """確率チェック"""
    return random.random() < clamp(probability, 0.0, 1.0)


def calculate_social_influence(npc_sociability, group_size, base_influence=0.1):
    """社会的影響力の計算"""
    social_factor = npc_sociability * 0.8
    group_factor = min(1.0, group_size / 5.0) * 0.5
    return base_influence + social_factor + group_factor


def decay_value(current_value, decay_rate, min_value=0.0):
    """値の減衰"""
    decayed = current_value * (1.0 - decay_rate)
    return max(min_value, decayed)


def safe_divide(numerator, denominator, default=0.0):
    """安全な除算"""
    if denominator == 0:
        return default
    return numerator / denominator


def create_position_grid(world_size, spacing=10):
    """位置グリッドの生成"""
    positions = []
    for x in range(0, world_size, spacing):
        for y in range(0, world_size, spacing):
            positions.append((x, y))
    return positions


def log_event(log_list, event_data, max_log_size=1000):
    """イベントログの記録"""
    log_list.append(event_data)
    if len(log_list) > max_log_size:
        log_list.pop(0)  # 古いログを削除
