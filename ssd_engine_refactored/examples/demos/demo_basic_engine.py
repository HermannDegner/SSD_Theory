"""
基本エンジンのデモ
==================

汎用SSDエンジンの基本機能を確認
"""

import sys
sys.path.append('..')

import numpy as np
from ssd_core_engine import (
    SSDCoreEngine, SSDCoreParams, SSDCoreState,
    create_default_state
)


def demo_basic_engine():
    """基本エンジンのデモ"""
    print("=" * 60)
    print("SSD Core Engine - 基本デモ")
    print("=" * 60)
    
    # 2層システムを作成
    print("\n[1] 2層システムの初期化")
    params = SSDCoreParams(
        num_layers=2,
        R_values=[100.0, 1.0],
        gamma_values=[0.1, 0.05],
        beta_values=[0.01, 0.1],
        eta_values=[0.5, 0.2],
        lambda_values=[0.01, 0.05],
        kappa_min_values=[0.8, 0.3],
        Theta_values=[100.0, 30.0]
    )
    
    engine = SSDCoreEngine(params)
    state = create_default_state(num_layers=2)
    
    print(f"  Layers: {params.num_layers}")
    print(f"  R values: {params.R_values}")
    print(f"  Initial E: {state.E}")
    print(f"  Initial κ: {state.kappa}")
    
    # 圧力を加えてシミュレーション
    print("\n[2] 圧力シミュレーション")
    pressure = np.array([50.0, 30.0])  # Layer 0に50、Layer 1に30の圧力
    
    print(f"  Applied pressure: {pressure}")
    
    for step in range(20):
        state = engine.step(state, pressure, dt=0.1)
        
        if step % 5 == 0:
            print(f"\n  Step {step}:")
            print(f"    E: {state.E}")
            print(f"    κ: {state.kappa}")
            
            # 構造的影響力
            power = engine.compute_structural_power(state, pressure)
            print(f"    Structural Power: {power}")
            
            # 支配層
            dominant = engine.get_dominant_layer(state, pressure)
            print(f"    Dominant Layer: {dominant}")
    
    # 跳躍検出
    print("\n[3] 跳躍検出テスト")
    print("  高圧力を加えて跳躍を誘発...")
    
    high_pressure = np.array([200.0, 100.0])
    
    for step in range(50):
        leap_occurred, leap_layer = engine.detect_leap(state, high_pressure)
        
        if leap_occurred:
            print(f"\n  *** LEAP at step {step} ***")
            print(f"      Layer: {leap_layer}")
            print(f"      E before: {state.E}")
            state = engine.execute_leap(state, leap_layer)
            print(f"      E after: {state.E}")
            break
        
        state = engine.step(state, high_pressure, dt=0.1)
    
    print("\n[4] 跳躍履歴")
    for t, leap_type in state.leap_history:
        print(f"  Time {t:.1f}: {leap_type}")
    
    print("\n" + "=" * 60)
    print("デモ完了")
    print("=" * 60)


if __name__ == "__main__":
    demo_basic_engine()
