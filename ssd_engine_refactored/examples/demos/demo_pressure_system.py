"""
多次元意味圧システムのデモ
==========================

四層構造に対応した意味圧の計算と、層間葛藤の可視化
"""

import sys
sys.path.append('..')

from ssd_pressure_system import (
    MultiDimensionalPressure,
    HumanLayer,
    rank_pressure_calculator,
    score_pressure_calculator,
    time_pressure_calculator,
    survival_pressure_calculator,
    social_pressure_calculator,
    physical_fatigue_calculator,
    ideological_pressure_calculator
)


def demo_pressure_system():
    """多次元意味圧システムのデモ"""
    print("=" * 70)
    print("SSD Multidimensional Pressure - デモ")
    print("=" * 70)
    
    # システム初期化
    print("\n[1] 圧力システム初期化")
    pressure_system = MultiDimensionalPressure()
    
    # 各層に圧力次元を登録
    print("\n[2] 圧力次元の登録")
    
    # PHYSICAL層
    pressure_system.register_dimension(
        name="physical_fatigue",
        calculator=physical_fatigue_calculator,
        layer=HumanLayer.PHYSICAL,
        weight=2.0,
        description="物理的疲労・ダメージ"
    )
    print("  ✓ PHYSICAL層: physical_fatigue (weight=2.0)")
    
    # BASE層
    pressure_system.register_dimension(
        name="survival_pressure",
        calculator=survival_pressure_calculator,
        layer=HumanLayer.BASE,
        weight=1.5,
        description="生存圧力（HP減少）"
    )
    print("  ✓ BASE層: survival_pressure (weight=1.5)")
    
    # CORE層
    pressure_system.register_dimension(
        name="rank_pressure",
        calculator=rank_pressure_calculator,
        layer=HumanLayer.CORE,
        weight=1.0,
        description="順位圧力"
    )
    
    pressure_system.register_dimension(
        name="score_pressure",
        calculator=score_pressure_calculator,
        layer=HumanLayer.CORE,
        weight=1.2,
        description="スコア差圧力"
    )
    
    pressure_system.register_dimension(
        name="social_pressure",
        calculator=social_pressure_calculator,
        layer=HumanLayer.CORE,
        weight=1.3,
        description="社会的圧力（疑惑・投票）"
    )
    print("  ✓ CORE層: rank_pressure, score_pressure, social_pressure")
    
    # UPPER層
    pressure_system.register_dimension(
        name="time_pressure",
        calculator=time_pressure_calculator,
        layer=HumanLayer.UPPER,
        weight=0.8,
        description="時間圧力"
    )
    
    pressure_system.register_dimension(
        name="ideological_pressure",
        calculator=ideological_pressure_calculator,
        layer=HumanLayer.UPPER,
        weight=1.0,
        description="イデオロギー圧力"
    )
    print("  ✓ UPPER層: time_pressure, ideological_pressure")
    
    # 統計表示
    print("\n[3] システム統計")
    stats = pressure_system.get_statistics()
    print(f"  総次元数: {stats['num_dimensions']}")
    print(f"  有効次元数: {stats['num_enabled']}")
    print(f"  総重み: {stats['total_weight']:.2f}")
    
    print("\n  層別統計:")
    for layer_name, layer_stat in stats['layer_stats'].items():
        print(f"    {layer_name}: {layer_stat['num_dimensions']}次元, "
              f"重み合計={layer_stat['total_weight']:.2f}")
    
    # シナリオ1: 通常状態
    print("\n" + "=" * 70)
    print("[4] シナリオ1: 通常状態")
    print("=" * 70)
    
    context_normal = {
        'fatigue': 0.2,
        'damage': 0.0,
        'hp': 80.0,
        'max_hp': 100.0,
        'rank': 3,
        'total_players': 10,
        'score': 50.0,
        'target_score': 100.0,
        'threshold': 100.0,
        'suspicion': 0.3,
        'votes': 1,
        'total_votes': 10,
        'elapsed': 30.0,
        'total': 100.0,
        'belief_conflict': 0.2,
        'moral_dilemma': 0.1
    }
    
    pressures_normal = pressure_system.calculate(context_normal)
    
    print("\n  計算結果:")
    for layer, pressure in pressures_normal.items():
        print(f"    {layer.name}: {pressure:.3f}")
    
    dominant_layer, dominant_pressure = pressure_system.get_dominant_layer()
    print(f"\n  支配層: {dominant_layer.name} (圧力={dominant_pressure:.3f})")
    
    conflicts = pressure_system.get_layer_conflict_index()
    print("\n  層間葛藤指数:")
    for conflict_pair, index in conflicts.items():
        print(f"    {conflict_pair}: {index:.3f}")
    
    leap_layer = pressure_system.should_trigger_leap(threshold=0.5)
    if leap_layer:
        print(f"\n  ⚠️ 跳躍トリガー: {leap_layer.name}層")
    else:
        print("\n  ✓ 跳躍なし（安定状態）")
    
    # シナリオ2: 極限状態（疲労MAX + 生存危機）
    print("\n" + "=" * 70)
    print("[5] シナリオ2: 極限状態（疲労MAX + 生存危機）")
    print("=" * 70)
    
    context_extreme = {
        'fatigue': 0.9,
        'damage': 0.7,
        'hp': 10.0,
        'max_hp': 100.0,
        'rank': 8,
        'total_players': 10,
        'score': 20.0,
        'target_score': 100.0,
        'threshold': 100.0,
        'suspicion': 0.8,
        'votes': 5,
        'total_votes': 10,
        'elapsed': 90.0,
        'total': 100.0,
        'belief_conflict': 0.6,
        'moral_dilemma': 0.5
    }
    
    pressures_extreme = pressure_system.calculate(context_extreme)
    
    print("\n  計算結果:")
    for layer, pressure in pressures_extreme.items():
        print(f"    {layer.name}: {pressure:.3f}")
    
    dominant_layer, dominant_pressure = pressure_system.get_dominant_layer()
    print(f"\n  支配層: {dominant_layer.name} (圧力={dominant_pressure:.3f})")
    
    conflicts = pressure_system.get_layer_conflict_index()
    print("\n  層間葛藤指数:")
    for conflict_pair, index in conflicts.items():
        print(f"    {conflict_pair}: {index:.3f}")
    
    leap_layer = pressure_system.should_trigger_leap(threshold=0.5)
    if leap_layer:
        print(f"\n  ⚠️ 跳躍トリガー: {leap_layer.name}層")
        print(f"     → この層の跳躍が最も強く支配的")
    else:
        print("\n  ✓ 跳躍なし（安定状態）")
    
    # シナリオ3: イデオロギー葛藤
    print("\n" + "=" * 70)
    print("[6] シナリオ3: イデオロギー葛藤（本能 vs 理念）")
    print("=" * 70)
    
    context_conflict = {
        'fatigue': 0.1,
        'damage': 0.0,
        'hp': 90.0,
        'max_hp': 100.0,
        'rank': 5,
        'total_players': 10,
        'score': 70.0,
        'target_score': 100.0,
        'threshold': 100.0,
        'suspicion': 0.9,  # 高い疑惑
        'votes': 6,
        'total_votes': 10,
        'elapsed': 50.0,
        'total': 100.0,
        'belief_conflict': 0.9,  # 強い信念の衝突
        'moral_dilemma': 0.8     # 高い道徳的ジレンマ
    }
    
    pressures_conflict = pressure_system.calculate(context_conflict)
    
    print("\n  計算結果:")
    for layer, pressure in pressures_conflict.items():
        print(f"    {layer.name}: {pressure:.3f}")
    
    dominant_layer, dominant_pressure = pressure_system.get_dominant_layer()
    print(f"\n  支配層: {dominant_layer.name} (圧力={dominant_pressure:.3f})")
    
    conflicts = pressure_system.get_layer_conflict_index()
    print("\n  層間葛藤指数:")
    for conflict_pair, index in conflicts.items():
        status = "🔥 強い葛藤" if index > 0.5 else "   普通"
        print(f"    {conflict_pair}: {index:.3f}  {status}")
    
    leap_layer = pressure_system.should_trigger_leap(threshold=0.5)
    if leap_layer:
        print(f"\n  ⚠️ 跳躍トリガー: {leap_layer.name}層")
    else:
        print("\n  ✓ 跳躍なし（安定状態）")
    
    # HumanPressure変換デモ
    print("\n" + "=" * 70)
    print("[7] HumanPressure形式への変換")
    print("=" * 70)
    
    try:
        human_pressure = pressure_system.to_human_pressure()
        print("\n  変換成功:")
        print(f"    physical: {human_pressure.physical:.3f}")
        print(f"    base:     {human_pressure.base:.3f}")
        print(f"    core:     {human_pressure.core:.3f}")
        print(f"    upper:    {human_pressure.upper:.3f}")
        print("\n  → HumanAgent.step()に直接渡せます")
    except Exception as e:
        print(f"\n  ⚠️ 変換スキップ: {e}")
        print("     (ssd_human_module未インポート時)")
    
    # 次元情報表示
    print("\n" + "=" * 70)
    print("[8] 次元詳細情報")
    print("=" * 70)
    
    dim_info = pressure_system.get_dimension_info()
    for name, info in dim_info.items():
        print(f"\n  {name}:")
        print(f"    層:   {info['layer']}")
        print(f"    重み: {info['weight']:.2f}")
        print(f"    説明: {info['description']}")
        print(f"    最新値: {info['last_value']:.3f}" if info['last_value'] is not None else "    最新値: N/A")
    
    print("\n" + "=" * 70)
    print("デモ完了")
    print("=" * 70)


if __name__ == "__main__":
    demo_pressure_system()
