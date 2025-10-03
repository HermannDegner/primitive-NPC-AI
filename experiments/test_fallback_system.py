#!/usr/bin/env python3
"""フォールバックシステムのテスト用スクリプト

各レベルのフォールバック機能をテストし、警告システムが正常に動作するかを確認します。
"""

import sys
import os

def test_primary_system():
    """プライマリシステム（integrated_simulation.py）のテスト"""
    print("🧪 Testing primary system (integrated_simulation.py)...")
    try:
        from integrated_simulation import run_ssd_enhanced_simulation
        print("✅ Primary system available")
        return True
    except ImportError as e:
        print(f"❌ Primary system failed: {e}")
        return False

def test_secondary_system():
    """セカンダリシステム（ssd_integrated_simulation.py）のテスト"""
    print("🧪 Testing secondary system (ssd_integrated_simulation.py)...")
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation
        print("✅ Secondary system available")
        return True
    except ImportError as e:
        print(f"❌ Secondary system failed: {e}")
        return False

def test_archive_reference():
    """アーカイブ参照システム（archive/main_backup.py）の可用性テスト"""
    print("🧪 Testing archive reference (archive/main_backup.py)...")
    try:
        archive_path = os.path.join(os.path.dirname(__file__), 'archive')
        if archive_path not in sys.path:
            sys.path.insert(0, archive_path)
        from main_backup import run_ssd_enhanced_simulation
        print("✅ Archive reference available (manual use only)")
        return True
    except ImportError as e:
        print(f"❌ Archive reference failed: {e}")
        return False

def test_disabled_fallback_behavior():
    """フォールバック無効化後の動作をテスト"""
    print("\n🔧 Testing behavior with fallback disabled...")
    
    # 一時的にintegrated_simulationを無効化
    original_modules = sys.modules.copy()
    
    # integrated_simulation を一時的に削除
    if 'integrated_simulation' in sys.modules:
        del sys.modules['integrated_simulation']
    
    # ssd_integrated_simulation を一時的に削除  
    if 'ssd_integrated_simulation' in sys.modules:
        del sys.modules['ssd_integrated_simulation']
    
    # main.pyの読み込み動作をシミュレート
    print("📋 Simulating main.py import behavior with disabled primary systems...")
    
    # integrated_simulationインポートの失敗をシミュレート
    sys.modules['integrated_simulation'] = None
    
    try:
        # main.pyのインポートロジックを再実行
        exec("""
try:
    from integrated_simulation import run_ssd_enhanced_simulation as run_enhanced_ssd_simulation
    SIMULATION_AVAILABLE = True
    print("✅ Using integrated simulation system")
except ImportError:
    try:
        from ssd_integrated_simulation import run_ssd_integrated_simulation as run_enhanced_ssd_simulation
        SIMULATION_AVAILABLE = True
        print("⚠️ Using SSD integrated simulation (full feature set)")
    except ImportError:
        try:
            import sys
            import os
            archive_path = os.path.join(os.path.dirname(__file__), 'archive')
            if archive_path not in sys.path:
                sys.path.insert(0, archive_path)
            from main_backup import run_ssd_enhanced_simulation as run_enhanced_ssd_simulation
            SIMULATION_AVAILABLE = True
            print("=" * 70)
            print("🚨 CRITICAL WARNING: Archive backup system activated!")
            print("🔍 This indicates missing functionality in primary systems:")
            print("   - integrated_simulation.py (primary system) failed")
            print("   - ssd_integrated_simulation.py (secondary) failed") 
            print("💡 Recommended actions:")
            print("   1. Check error logs above for missing dependencies")
            print("   2. Extract needed functions from archive/main_backup.py")
            print("   3. Add missing functionality to ssd_integrated_simulation.py")
            print("📍 Running with full legacy feature set from archive")
            print("=" * 70)
        except ImportError:
            SIMULATION_AVAILABLE = False
            print("❌ Warning: No simulation system available")
""")
    finally:
        # モジュール状態を復元
        sys.modules.clear()
        sys.modules.update(original_modules)

def main():
    """フォールバックシステムの総合テスト"""
    print("🚀 Fallback System Comprehensive Test")
    print("=" * 50)
    
    # 各システムの可用性テスト
    primary_ok = test_primary_system()
    secondary_ok = test_secondary_system()
    archive_ok = test_archive_reference()
    
    print(f"\n📊 System Status Summary:")
    print(f"   Primary (integrated_simulation.py): {'✅' if primary_ok else '❌'}")
    print(f"   Secondary (ssd_integrated_simulation.py): {'✅' if secondary_ok else '❌'}")
    print(f"   Archive Reference (archive/main_backup.py): {'✅' if archive_ok else '❌'}")
    
    # フォールバック動作テスト
    test_disabled_fallback_behavior()
    
    print("\n✅ Fallback system test completed")

if __name__ == "__main__":
    main()