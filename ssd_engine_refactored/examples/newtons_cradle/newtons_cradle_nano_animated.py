"""
ニュートンのゆりかご - Nano最適化版 + アニメーション
Newton's Cradle with SSD Core (Nano Optimized + Animated)

【特徴】
- Numba JIT コンパイル + 並列化
- リアルタイムアニメーション
- 100球でもスムーズに動作
- SSD状態の可視化

作成日: 2025年11月7日
バージョン: 1.0 (Nano + Animation)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from numba import njit, prange
import time
from typing import Tuple


# Numba最適化された物理演算
@njit
def update_physics_vectorized(positions: np.ndarray, velocities: np.ndarray,
                              E_array: np.ndarray, damping_factors: np.ndarray,
                              dt: float, gravity: float, string_length: float) -> Tuple:
    """全球の物理状態を一括更新（ベクトル化）"""
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
            E_array[i, j] *= 0.99
        
        # 減衰率の更新
        E_mean = (E_array[i, 0] + E_array[i, 1] + E_array[i, 2] + E_array[i, 3]) / 4.0
        damping_factors[i] = E_mean * 0.01
    
    return positions, velocities, damping_factors


@njit
def detect_collisions_fast(positions: np.ndarray, velocities: np.ndarray,
                           radius: float, string_length: float, spacing: float) -> np.ndarray:
    """高速衝突検出"""
    n_balls = len(positions)
    collision_list = np.empty((n_balls, 2), dtype=np.int32)
    collision_count = 0
    
    for i in range(n_balls - 1):
        # 支点からの水平位置を計算
        angle1 = positions[i] / string_length
        angle2 = positions[i+1] / string_length
        
        support_x1 = (i - n_balls/2) * spacing
        support_x2 = (i + 1 - n_balls/2) * spacing
        
        x1 = support_x1 + string_length * np.sin(angle1)
        x2 = support_x2 + string_length * np.sin(angle2)
        
        distance = abs(x2 - x1)
        
        if distance <= radius * 2.0 * 1.01:
            relative_velocity = velocities[i] - velocities[i+1]
            if (x1 < x2 and relative_velocity > 0) or (x1 > x2 and relative_velocity < 0):
                collision_list[collision_count, 0] = i
                collision_list[collision_count, 1] = i + 1
                collision_count += 1
    
    return collision_list[:collision_count]


@njit
def resolve_collisions_vectorized(positions: np.ndarray, velocities: np.ndarray,
                                  E_array: np.ndarray, collision_counts: np.ndarray,
                                  collisions: np.ndarray, mass: float) -> Tuple:
    """衝突を一括解決（ベクトル化）"""
    for k in range(len(collisions)):
        i = collisions[k, 0]
        j = collisions[k, 1]
        
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


class NewtonsCradleNanoAnimated:
    """ニュートンのゆりかご - Nano最適化版 + アニメーション"""
    
    def __init__(self, n_balls: int = 10, string_length: float = 2.0,
                 initial_release_angle: float = 30.0, spacing: float = 1.0):
        self.n_balls = n_balls
        self.string_length = string_length
        self.gravity = 9.8
        self.radius = 0.5
        self.mass = 1.0
        self.spacing = spacing
        
        # 状態配列（ベクトル化）
        self.positions = np.zeros(n_balls, dtype=np.float64)
        self.velocities = np.zeros(n_balls, dtype=np.float64)
        self.E_array = np.zeros((n_balls, 4), dtype=np.float64)
        self.damping_factors = np.zeros(n_balls, dtype=np.float64)
        self.collision_counts = np.zeros(n_balls, dtype=np.int32)
        
        # 初期位置: 等間隔
        for i in range(n_balls):
            self.positions[i] = 0.0
        
        # 初期条件: 最初の球を持ち上げる
        release_angle_rad = np.radians(initial_release_angle)
        self.positions[0] = release_angle_rad * string_length
        
        # シミュレーション状態
        self.current_time = 0.0
        self.total_steps = 0
        
        # エネルギー履歴（アニメーション用）
        self.energy_history = []
        self.max_history = 1000  # 最大履歴数
    
    def step(self, dt: float = 0.001):
        """1ステップ進める（高速版）"""
        # 物理更新（並列化）
        self.positions, self.velocities, self.damping_factors = \
            update_physics_vectorized(
                self.positions, self.velocities, self.E_array,
                self.damping_factors, dt, self.gravity, self.string_length
            )
        
        # 衝突検出（高速）
        collisions = detect_collisions_fast(
            self.positions, self.velocities, self.radius,
            self.string_length, self.spacing
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
        
        # エネルギー記録（履歴制限）
        total_energy = self.get_total_energy()
        self.energy_history.append(total_energy)
        if len(self.energy_history) > self.max_history:
            self.energy_history.pop(0)
    
    def get_total_energy(self) -> float:
        """総エネルギー計算"""
        total_KE = 0.0
        total_PE = 0.0
        
        for i in range(self.n_balls):
            # 運動エネルギー
            total_KE += 0.5 * self.mass * (self.velocities[i] ** 2)
            
            # 位置エネルギー
            angle = self.positions[i] / self.string_length
            height = self.string_length * (1.0 - np.cos(angle))
            total_PE += self.mass * self.gravity * height
        
        return total_KE + total_PE
    
    def get_ball_position_xy(self, ball_id: int) -> tuple:
        """球のXY座標"""
        angle = self.positions[ball_id] / self.string_length
        support_x = (ball_id - self.n_balls/2) * self.spacing
        x = support_x + self.string_length * np.sin(angle)
        y = -self.string_length * np.cos(angle)
        return (x, y)
    
    def get_support_position(self, ball_id: int) -> float:
        """支点のX座標"""
        return (ball_id - self.n_balls/2) * self.spacing


class NanoCradleVisualizer:
    """Nano版アニメーションビジュアライザー"""
    
    def __init__(self, cradle: NewtonsCradleNanoAnimated):
        self.cradle = cradle
        
        # Figure作成
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.suptitle(f"Newton's Cradle Nano - ニュートンのゆりかご ({cradle.n_balls} balls, Numba optimized)", 
                         fontsize=16, fontweight='bold')
        
        # サブプロット
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        self.ax_pendulum = self.fig.add_subplot(gs[0, :])  # 上段全体: 振り子
        self.ax_energy = self.fig.add_subplot(gs[1, 0])    # 下段左: エネルギー
        self.ax_ssd = self.fig.add_subplot(gs[1, 1])       # 下段右: SSD状態
        
        # パフォーマンス計測
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_history = []
        
        # 初期化
        self.init_pendulum_plot()
    
    def init_pendulum_plot(self):
        """振り子プロット初期化"""
        self.ax_pendulum.clear()
        
        # 表示範囲を球数に応じて調整
        x_range = max(4, self.cradle.n_balls * 0.6)
        self.ax_pendulum.set_xlim(-x_range, x_range)
        self.ax_pendulum.set_ylim(-3, 1)
        self.ax_pendulum.set_aspect('equal')
        self.ax_pendulum.set_title('Physical Simulation (Numba Optimized)', 
                                   fontweight='bold', fontsize=12)
        self.ax_pendulum.grid(True, alpha=0.3)
        
        # 支点
        support_positions = [self.cradle.get_support_position(i) 
                           for i in range(self.cradle.n_balls)]
        self.ax_pendulum.plot(support_positions, [0] * len(support_positions), 
                             'ko-', markersize=8, linewidth=2, zorder=5)
        self.ax_pendulum.axhline(y=0, color='black', linewidth=2, alpha=0.5)
    
    def update_frame(self, frame):
        """フレーム更新"""
        # 複数ステップ実行（スムーズなアニメーション）
        steps_per_frame = 5
        for _ in range(steps_per_frame):
            self.cradle.step(dt=0.001)
        
        # FPS計測
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            elapsed = time.time() - self.start_time
            fps = self.frame_count / elapsed
            self.fps_history.append(fps)
        
        # 描画更新
        self.draw_pendulums()
        self.draw_energy()
        self.draw_ssd_state()
        
        return []
    
    def draw_pendulums(self):
        """振り子描画"""
        self.ax_pendulum.clear()
        
        x_range = max(4, self.cradle.n_balls * 0.6)
        self.ax_pendulum.set_xlim(-x_range, x_range)
        self.ax_pendulum.set_ylim(-3, 1)
        self.ax_pendulum.set_aspect('equal')
        
        # FPS表示
        avg_fps = np.mean(self.fps_history[-10:]) if self.fps_history else 0
        title = f'Physical Simulation (t={self.cradle.current_time:.2f}s, FPS={avg_fps:.1f})'
        self.ax_pendulum.set_title(title, fontweight='bold', fontsize=12)
        self.ax_pendulum.grid(True, alpha=0.3)
        
        # 支点
        support_positions = [self.cradle.get_support_position(i) 
                           for i in range(self.cradle.n_balls)]
        self.ax_pendulum.plot(support_positions, [0] * len(support_positions), 
                             'ko-', markersize=8, linewidth=2, zorder=5)
        self.ax_pendulum.axhline(y=0, color='black', linewidth=2, alpha=0.5)
        
        # 各球（球数に応じて描画を調整）
        show_labels = self.cradle.n_balls <= 20
        show_velocities = self.cradle.n_balls <= 10
        
        for i in range(self.cradle.n_balls):
            support_x = self.cradle.get_support_position(i)
            ball_x, ball_y = self.cradle.get_ball_position_xy(i)
            
            # 紐
            self.ax_pendulum.plot([support_x, ball_x], [0, ball_y], 
                                 'k-', linewidth=1.5, alpha=0.6, zorder=1)
            
            # 球（最近衝突したら赤）
            recent_collision = self.cradle.collision_counts[i] > 0
            color = 'red' if recent_collision else 'blue'
            
            circle = Circle((ball_x, ball_y), self.cradle.radius, 
                          color=color, alpha=0.7, zorder=10)
            self.ax_pendulum.add_patch(circle)
            
            # ラベル（球数が少ない場合のみ）
            if show_labels:
                self.ax_pendulum.text(ball_x, ball_y, str(i), 
                                    ha='center', va='center', 
                                    fontsize=8, fontweight='bold', 
                                    color='white', zorder=11)
            
            # 速度ベクトル（球数が少ない場合のみ）
            if show_velocities and abs(self.cradle.velocities[i]) > 0.1:
                angle = self.cradle.positions[i] / self.cradle.string_length
                vx = self.cradle.velocities[i] * np.cos(angle) * 0.2
                vy = self.cradle.velocities[i] * np.sin(angle) * 0.2
                self.ax_pendulum.arrow(ball_x, ball_y, vx, vy,
                                      head_width=0.1, head_length=0.08,
                                      fc='green', ec='green', alpha=0.6, zorder=9)
    
    def draw_energy(self):
        """エネルギープロット"""
        self.ax_energy.clear()
        self.ax_energy.set_title('Energy Conservation', fontweight='bold', fontsize=11)
        self.ax_energy.set_xlabel('Time Step')
        self.ax_energy.set_ylabel('Energy (J)')
        
        if len(self.cradle.energy_history) > 0:
            steps = list(range(len(self.cradle.energy_history)))
            self.ax_energy.plot(steps, self.cradle.energy_history, 
                              'b-', linewidth=1.5, label='Total Energy')
            
            initial_energy = self.cradle.energy_history[0]
            self.ax_energy.axhline(initial_energy, 
                                  color='r', linestyle='--', linewidth=1.5, 
                                  alpha=0.7, label='Initial Energy')
            
            # エネルギー保存率
            current_energy = self.cradle.energy_history[-1]
            conservation = (current_energy / initial_energy * 100) if initial_energy > 0 else 100
            self.ax_energy.text(0.02, 0.98, f'Conservation: {conservation:.2f}%',
                              transform=self.ax_energy.transAxes,
                              va='top', fontsize=9,
                              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            self.ax_energy.legend(fontsize=9)
            self.ax_energy.grid(True, alpha=0.3)
    
    def draw_ssd_state(self):
        """SSD状態プロット"""
        self.ax_ssd.clear()
        self.ax_ssd.set_title('SSD State: E Accumulation (Nano)', 
                             fontweight='bold', fontsize=11)
        self.ax_ssd.set_xlabel('Ball ID')
        self.ax_ssd.set_ylabel('E (Accumulated Stress)')
        
        # サンプリング（球数が多い場合）
        if self.cradle.n_balls > 20:
            # 代表的な球のみ表示
            sample_indices = np.linspace(0, self.cradle.n_balls-1, 20, dtype=int)
            ball_ids = sample_indices
            E_means = [np.mean(self.cradle.E_array[i]) for i in sample_indices]
        else:
            ball_ids = np.arange(self.cradle.n_balls)
            E_means = [np.mean(self.cradle.E_array[i]) for i in ball_ids]
        
        self.ax_ssd.bar(ball_ids, E_means, alpha=0.7, color='orange')
        self.ax_ssd.grid(True, alpha=0.3)
        
        # 統計情報
        total_collisions = np.sum(self.cradle.collision_counts)
        total_E = np.sum(self.cradle.E_array)
        avg_damping = np.mean(self.cradle.damping_factors)
        
        stats_text = (f'Collisions: {total_collisions} | '
                     f'Total E: {total_E:.2f} | '
                     f'Avg Damping: {avg_damping:.4f}')
        self.ax_ssd.text(0.5, 0.95, stats_text, 
                        transform=self.ax_ssd.transAxes,
                        ha='center', va='top', fontsize=9,
                        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    def animate(self, frames: int = 1000, interval: int = 20):
        """アニメーション開始"""
        print(f"\nNano版アニメーション開始: {self.cradle.n_balls}球, {frames}フレーム")
        print("ウィンドウを閉じると終了します\n")
        
        anim = FuncAnimation(
            self.fig,
            self.update_frame,
            init_func=self.init_pendulum_plot,
            frames=frames,
            interval=interval,
            blit=False
        )
        
        plt.tight_layout()
        plt.show()
        
        # 最終統計
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
        print(f"\n統計:")
        print(f"  総フレーム数: {self.frame_count}")
        print(f"  実行時間: {elapsed:.2f}秒")
        print(f"  平均FPS: {avg_fps:.1f}")
        
        return anim


def demo_nano_small():
    """Nano版デモ: 10球"""
    print("="*70)
    print("Newton's Cradle Nano - Small Demo (10 balls)")
    print("="*70)
    print("\nNumba JIT最適化 + リアルタイムアニメーション")
    
    cradle = NewtonsCradleNanoAnimated(
        n_balls=10,
        string_length=2.0,
        initial_release_angle=30.0,
        spacing=1.0
    )
    
    viz = NanoCradleVisualizer(cradle)
    viz.animate(frames=1000, interval=20)


def demo_nano_large():
    """Nano版デモ: 50球"""
    print("="*70)
    print("Newton's Cradle Nano - Large Demo (50 balls)")
    print("="*70)
    print("\nNumba並列化でスムーズに動作")
    
    cradle = NewtonsCradleNanoAnimated(
        n_balls=50,
        string_length=2.0,
        initial_release_angle=30.0,
        spacing=1.0
    )
    
    viz = NanoCradleVisualizer(cradle)
    viz.animate(frames=1000, interval=20)


def demo_nano_extreme():
    """Nano版デモ: 100球"""
    print("="*70)
    print("Newton's Cradle Nano - Extreme Demo (100 balls)")
    print("="*70)
    print("\nNumbaの威力: 100球でもリアルタイム!")
    
    cradle = NewtonsCradleNanoAnimated(
        n_balls=100,
        string_length=2.0,
        initial_release_angle=30.0,
        spacing=1.0
    )
    
    viz = NanoCradleVisualizer(cradle)
    viz.animate(frames=1000, interval=20)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "large":
            demo_nano_large()
        elif sys.argv[1] == "extreme":
            demo_nano_extreme()
        else:
            demo_nano_small()
    else:
        demo_nano_small()
    
    print("\n" + "="*70)
    print("デモ完了!")
    print("="*70)
    print("\n💡 Tip:")
    print("  python examples/newtons_cradle_nano_animated.py           # 10球")
    print("  python examples/newtons_cradle_nano_animated.py large     # 50球")
    print("  python examples/newtons_cradle_nano_animated.py extreme   # 100球")
