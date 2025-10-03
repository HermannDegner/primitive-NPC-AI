#!/usr/bin/env python3
"""
未使用コード分析レポート - 反復処理継続
"""

def analyze_unused_modules():
    """未使用モジュールの分析"""
    
    print("🔍 未使用コード分析開始...")
    
    # 確認済み：使用されていないモジュール/ファイル
    unused_files = [
        "analysis_system.py",  # main.pyでコメントアウト済み、実際は未使用
    ]
    
    # 不存在ファイル（ドキュメント内でのみ参照）
    missing_files = [
        "enhanced_simulation.py",  # ドキュメント内で参照されているが存在しない
        "smart_environment.py",   # 同様に存在しない
        "main_with_engine.py",    # grep検索に表示されるが実際は存在しない
    ]
    
    # 確認済み：使用されているモジュール
    active_modules = [
        "main.py",
        "npc.py", 
        "environment.py",
        "config.py",
        "utils.py",
        "seasonal_system.py",
        "future_prediction.py",
        "subjective_boundary_system.py",
        "ssd_core_engine/*"  # SSD Core Engine全体
    ]
    
    # アーカイブ済み
    archived_modules = [
        "archived_old_code/ssd_core.py",
        "archived_old_code/social.py"
    ]
    
    print("\n📋 分析結果:")
    print("=" * 50)
    print("✅ 使用中のモジュール:")
    for module in active_modules:
        print(f"  - {module}")
        
    print(f"\n📦 アーカイブ済み:")
    for module in archived_modules:
        print(f"  - {module}")
        
    print(f"\n🗑️ 未使用ファイル発見:")
    for module in unused_files:
        print(f"  - {module} (存在するが使用されていない)")
        
    print(f"\n❌ 不存在ファイル:")
    for module in missing_files:
        print(f"  - {module} (参照されているが存在しない)")
    
    return unused_files, active_modules, archived_modules, missing_files

if __name__ == "__main__":
    analyze_unused_modules()