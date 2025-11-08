"""
全デモの統合実行スクリプト
==========================

すべてのデモを順次実行して動作確認
"""

import sys
import os

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def run_all_demos():
    """全デモを実行"""
    print("\n" + "=" * 80)
    print(" SSD Engine Refactored - 全デモ統合実行")
    print("=" * 80)
    
    # Demo 1: 基本エンジン
    print("\n\n")
    print("█" * 80)
    print("█ DEMO 1: 基本エンジン")
    print("█" * 80)
    try:
        from examples.demo_basic_engine import demo_basic_engine
        demo_basic_engine()
        print("\n✅ Demo 1 完了")
    except Exception as e:
        print(f"\n❌ Demo 1 エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # Demo 2: 人間心理
    print("\n\n")
    print("█" * 80)
    print("█ DEMO 2: 人間心理モジュール")
    print("█" * 80)
    try:
        from examples.demo_human_psychology import demo_human_psychology
        demo_human_psychology()
        print("\n✅ Demo 2 完了")
    except Exception as e:
        print(f"\n❌ Demo 2 エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # Demo 3: 社会ダイナミクス
    print("\n\n")
    print("█" * 80)
    print("█ DEMO 3: 社会ダイナミクス")
    print("█" * 80)
    try:
        from examples.demo_social_dynamics import demo_social_dynamics
        demo_social_dynamics()
        print("\n✅ Demo 3 完了")
    except Exception as e:
        print(f"\n❌ Demo 3 エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # Demo 4: 多次元意味圧システム
    print("\n\n")
    print("█" * 80)
    print("█ DEMO 4: 多次元意味圧システム")
    print("█" * 80)
    try:
        from examples.demo_pressure_system import demo_pressure_system
        demo_pressure_system()
        print("\n✅ Demo 4 完了")
    except Exception as e:
        print(f"\n❌ Demo 4 エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 最終サマリー
    print("\n\n")
    print("=" * 80)
    print(" 全デモ実行完了")
    print("=" * 80)
    print("\n構造の特徴:")
    print("  ✅ 汎用エンジン: ドメイン非依存の計算")
    print("  ✅ 人間モジュール: 四層構造の心理モデル")
    print("  ✅ 社会ダイナミクス: 多エージェント相互作用")
    print("  ✅ 意味圧システム: 多次元入力のモデリング")
    print("\n利点:")
    print("  • 計算効率: NumPyベクトル演算")
    print("  • 拡張性: 任意のレイヤー数・パラメータ")
    print("  • 保守性: モジュール分離、明確な責務")
    print("  • 柔軟性: 層別圧力入力、葛藤分析")
    print("=" * 80)


if __name__ == "__main__":
    run_all_demos()
