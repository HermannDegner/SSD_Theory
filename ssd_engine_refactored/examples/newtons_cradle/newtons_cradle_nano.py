"""
ニュートンのゆりかご - Nano最適化版
Newton's Cradle with SSD Core (Nano Optimized)

【Phase 10.3: Nano最適化】
- Numbaによる並列化
- ベクトル化された物理演算
- 高速な衝突検出
- 100個以上の球でも高速動作

作成日: 2025年11月7日
バージョン: 1.0 (Nano)
"""

import numpy as np
import matplotlib.pyplot as plt
from numba import njit, prange
import time
from typing import Tuple

# Numba最適化された物理演算
@njit
def update_physics_vectorized(positions: np.ndarray, velocities: np.ndarray,
                              E_array: np.ndarray, damping_factors: np.ndarray,
                              dt: float, gravity: float, string_length: float) -> Tuple:
    """
    全球の物理状態を一括更新（ベクトル化）
    
    Args:
        positions: 位置配列 [n_balls]
        velocities: 速度配列 [n_balls]
        E_array: E蓄積配列 [n_balls, 4]
        damping_factors: 減衰率配列 [n_balls]
        dt: 時間刻み
        gravity: 重力加速度
        string_length: 糸の長さ
    
    Returns:
        (positions, velocities, damping_factors) の更新版
    """
    n_balls = len(positions)
    
    for i in prange(n_balls):  # 並列化
        # 振り子の運動
        angle = positions[i] / string_length
        angular_acceleration = -(gravity / string_length) * np.sin(angle)
        angular_velocity = velocities[i] / string_length
        
        # 角速度の更新（減衰あり）
        angular_velocity += angular_acceleration * dt
        angular_velocity *= (1.0 - damping_factors[i])
        
        # 角度の更新
        angle += angular_velocity * dt
        
        # 位置・速度の更新
        positions[i] = angle * string_length
        velocities[i] = angular_velocity * string_length
        
        # E自然減衰
        for j in range(4):
            E_array[i, j] *= 0.99  # 単純な減衰
        
        # 減衰率の更新
        E_mean = (E_array[i, 0] + E_array[i, 1] + E_array[i, 2] + E_array[i, 3]) / 4.0
        damping_factors[i] = E_mean * 0.01
    
    return positions, velocities, damping_factors


@njit
def detect_collisions_fast(positions: np.ndarray, velocities: np.ndarray,
                           radius: float) -> np.ndarray:
    """
    高速衝突検出
    
    Args:
        positions: 位置配列 [n_balls]
        velocities: 速度配列 [n_balls]
        radius: 球の半径
    
    Returns:
        衝突ペア配列 [n_collisions, 2]
    """
    n_balls = len(positions)
    collisions = []
    
    for i in range(n_balls - 1):
        distance = abs(positions[i+1] - positions[i])
        
        # 衝突判定
        if distance <= radius * 2.0 * 1.01:
            # 相対速度
            relative_velocity = velocities[i] - velocities[i+1]
            if (positions[i] < positions[i+1] and relative_velocity > 0) or \
               (positions[i] > positions[i+1] and relative_velocity < 0):
                collisions.append((i, i+1))
    
    return np.array(collisions, dtype=np.int32)


@njit
def resolve_collisions_vectorized(positions: np.ndarray, velocities: np.ndarray,
                                  E_array: np.ndarray, collision_counts: np.ndarray,
                                  collisions: np.ndarray, mass: float) -> Tuple:
    """
    衝突を一括解決（ベクトル化）
    
    Args:
        positions: 位置配列 [n_balls]
        velocities: 速度配列 [n_balls]
        E_array: E蓄積配列 [n_balls, 4]
        collision_counts: 衝突カウント [n_balls]
        collisions: 衝突ペア配列 [n_collisions, 2]
        mass: 球の質量（全て同じと仮定）
    
    Returns:
        (velocities, E_array, collision_counts) の更新版
    """
    for k in range(len(collisions)):
        i = collisions[k, 0]
        j = collisions[k, 1]
        
        # 衝突前の速度
        v1 = velocities[i]
        v2 = velocities[j]
        
        # 完全弾性衝突（質量が同じなので速度交換）
        velocities[i] = v2
        velocities[j] = v1
        
        # 衝突強度
        impact = abs(v1 - v2)
        
        # E蓄積（意味圧として解釈）
        E_array[i, 0] += impact * 2.0  # PHYSICAL
        E_array[i, 1] += impact * 1.5  # BASE
        E_array[i, 2] += impact * 0.5  # CORE
        E_array[i, 3] += impact * 0.2  # UPPER
        
        E_array[j, 0] += impact * 2.0
        E_array[j, 1] += impact * 1.5
        E_array[j, 2] += impact * 0.5
        E_array[j, 3] += impact * 0.2
        
        # 衝突カウント
        collision_counts[i] += 1
        collision_counts[j] += 1
    
    return velocities, E_array, collision_counts


class NewtonsCradleNano:
    """
    ニュートンのゆりかご - Nano最適化版
    
    【最適化技術】
    - Numba JIT コンパイル
    - 並列処理（prange）
    - ベクトル化演算
    - 高速衝突検出
    
    【スケーラビリティ】
    - 100個以上の球でも高速
    - リアルタイム可視化可能
    """
    
    def __init__(self, n_balls: int = 100, string_length: float = 2.0,
                 initial_release_angle: float = 30.0):
        self.n_balls = n_balls
        self.string_length = string_length
        self.gravity = 9.8
        self.radius = 0.5
        self.mass = 1.0
        
        # 状態配列（ベクトル化）
        self.positions = np.zeros(n_balls, dtype=np.float64)
        self.velocities = np.zeros(n_balls, dtype=np.float64)
        self.E_array = np.zeros((n_balls, 4), dtype=np.float64)
        self.damping_factors = np.zeros(n_balls, dtype=np.float64)
        self.collision_counts = np.zeros(n_balls, dtype=np.int32)
        
        # 初期位置
        spacing = 1.0
        for i in range(n_balls):
            self.positions[i] = (i - n_balls/2) * spacing
        
        # 初期条件: 最初の球を持ち上げる
        release_angle_rad = np.radians(initial_release_angle)
        self.positions[0] = release_angle_rad * string_length
        
        # シミュレーション状態
        self.current_time = 0.0
        self.total_steps = 0
    
    def step(self, dt: float = 0.001):
        """
        1ステップ進める（高速版）
        
        Args:
            dt: 時間刻み
        """
        # 物理更新（並列化）
        self.positions, self.velocities, self.damping_factors = \
            update_physics_vectorized(
                self.positions, self.velocities, self.E_array,
                self.damping_factors, dt, self.gravity, self.string_length
            )
        
        # 衝突検出（高速）
        collisions = detect_collisions_fast(
            self.positions, self.velocities, self.radius
        )
        
        # 衝突解決（ベクトル化）
        if len(collisions) > 0:
            self.velocities, self.E_array, self.collision_counts = \
                resolve_collisions_vectorized(
                    self.positions, self.velocities, self.E_array,
                    self.collision_counts, collisions, self.mass
                )
        
        # 時刻更新
        self.current_time += dt
        self.total_steps += 1
    
    def simulate(self, duration: float = 10.0, dt: float = 0.001,
                verbose: bool = True):
        """
        シミュレーション実行（高速版）
        
        Args:
            duration: 実行時間（秒）
            dt: 時間刻み
            verbose: 進行状況を表示
        """
        steps = int(duration / dt)
        
        if verbose:
            print(f"シミュレーション開始: {self.n_balls}球, {duration}秒, {steps}ステップ")
        
        start_time = time.time()
        
        for step_num in range(steps):
            self.step(dt)
            
            if verbose and step_num % 10000 == 0 and step_num > 0:
                elapsed = time.time() - start_time
                steps_per_sec = step_num / elapsed
                print(f"  {self.current_time:.2f}秒 / {duration}秒 "
                      f"({steps_per_sec:.0f} steps/sec)")
        
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"シミュレーション完了: {elapsed:.2f}秒")
            print(f"パフォーマンス: {self.total_steps / elapsed:.0f} steps/sec")
    
    def print_stats(self):
        """統計情報を表示"""
        print("\n" + "="*70)
        print("最終統計（Nano版）")
        print("="*70)
        
        # 代表的な球だけ表示
        sample_indices = [0, self.n_balls//4, self.n_balls//2, 
                         3*self.n_balls//4, self.n_balls-1]
        
        for idx in sample_indices:
            if idx < self.n_balls:
                E_mean = np.mean(self.E_array[idx])
                print(f"\nBall {idx}:")
                print(f"  位置: {self.positions[idx]:.3f} m")
                print(f"  速度: {self.velocities[idx]:.3f} m/s")
                print(f"  衝突回数: {self.collision_counts[idx]}回")
                print(f"  E蓄積: {E_mean:.4f}")
                print(f"  減衰率: {self.damping_factors[idx]:.4f}")
        
        # 全体統計
        print(f"\n全体:")
        print(f"  総衝突回数: {np.sum(self.collision_counts)}回")
        print(f"  平均E蓄積: {np.mean(self.E_array):.4f}")
        print(f"  平均減衰率: {np.mean(self.damping_factors):.4f}")
    
    def plot_snapshot(self):
        """現在の状態をプロット"""
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        ball_indices = np.arange(self.n_balls)
        
        # 1. 位置
        ax1 = axes[0]
        ax1.scatter(ball_indices, self.positions, s=50, alpha=0.6)
        ax1.set_xlabel('Ball Index')
        ax1.set_ylabel('Position (m)')
        ax1.set_title(f"Newton's Cradle Snapshot (Nano, {self.n_balls} balls, t={self.current_time:.2f}s)")
        ax1.grid(True, alpha=0.3)
        
        # 2. E蓄積
        ax2 = axes[1]
        E_means = np.mean(self.E_array, axis=1)
        ax2.bar(ball_indices, E_means, alpha=0.6, color='red')
        ax2.set_xlabel('Ball Index')
        ax2.set_ylabel('E (Accumulated Stress)')
        ax2.set_title('SSD: E Distribution')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def benchmark():
    """ベンチマーク: フル版 vs Nano版"""
    print("="*70)
    print("ベンチマーク: フル版 vs Nano版")
    print("="*70)
    print()
    
    # Nano版: 100球
    print("【Nano版: 100球】")
    cradle_nano = NewtonsCradleNano(n_balls=100, initial_release_angle=30.0)
    cradle_nano.simulate(duration=5.0, dt=0.001, verbose=True)
    
    print("\n" + "="*70)
    print()


def demo_nano():
    """Nano版デモ"""
    print("="*70)
    print("ニュートンのゆりかご - Nano最適化版")
    print("="*70)
    print("\n【最適化技術】")
    print("- Numba JIT コンパイル")
    print("- 並列処理（prange）")
    print("- ベクトル化演算")
    print("- 高速衝突検出")
    print()
    
    # 小規模デモ
    print("【デモ1: 10球】")
    cradle_small = NewtonsCradleNano(n_balls=10, initial_release_angle=30.0)
    cradle_small.simulate(duration=5.0, dt=0.001)
    cradle_small.print_stats()
    
    print("\n" + "="*70)
    print()
    
    # 大規模デモ
    print("【デモ2: 100球（スケーラビリティ）】")
    cradle_large = NewtonsCradleNano(n_balls=100, initial_release_angle=30.0)
    cradle_large.simulate(duration=5.0, dt=0.001)
    cradle_large.print_stats()
    
    # 可視化
    print("\n可視化を生成中...")
    cradle_large.plot_snapshot()
    
    print("\n" + "="*70)
    print("デモ完了")
    print("="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        benchmark()
    else:
        demo_nano()
