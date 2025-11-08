"""
ニュートンのゆりかご - アニメーション版
Newton's Cradle with SSD Core (Animated Visualization)

【リアルタイムアニメーション】
- 振り子の動き
- エネルギー保存
- SSD状態（E蓄積）
- 統計情報

作成日: 2025年11月7日
バージョン: 1.0 (Animated)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
import sys
import os

# 親ディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ssd_human_module import HumanAgent, HumanPressure


class Ball:
    """球（SSD統合版）"""
    
    def __init__(self, ball_id: int, initial_position: float, mass: float = 1.0):
        self.ball_id = ball_id
        self.mass = mass
        
        # 物理状態
        self.position = initial_position  # 水平位置
        self.velocity = 0.0
        
        # SSD状態
        self.agent = HumanAgent()
        
        # 衝突記録
        self.collision_count = 0
        self.total_impact = 0.0
        self.last_collision_time = 0.0
        self.damping_factor = 0.0
    
    def apply_impact(self, impact_velocity: float, current_time: float):
        """衝突を適用"""
        self.velocity = impact_velocity
        
        impact_magnitude = abs(impact_velocity)
        
        # 衝突を意味圧として解釈
        pressure = HumanPressure(
            base=impact_magnitude * 1.5,  # 破損リスク
            core=impact_magnitude * 0.5,  # 規範的圧力
            upper=impact_magnitude * 0.2  # 理念的圧力
        )
        
        self.agent.step(pressure, dt=0.01)
        
        # E蓄積による減衰
        E = self.agent.state.E
        self.damping_factor = np.mean(E) * 0.01
        
        self.collision_count += 1
        self.total_impact += impact_magnitude
        self.last_collision_time = current_time
    
    def update_physics(self, dt: float, gravity: float = 9.8, string_length: float = 2.0):
        """物理更新"""
        angle = self.position / string_length
        angular_acceleration = -(gravity / string_length) * np.sin(angle)
        angular_velocity = self.velocity / string_length
        
        # 角速度更新（減衰あり）
        angular_velocity += angular_acceleration * dt
        angular_velocity *= (1.0 - self.damping_factor)
        
        # 角度更新
        angle += angular_velocity * dt
        
        # 位置・速度更新
        self.position = angle * string_length
        self.velocity = angular_velocity * string_length
        
        # SSD自然減衰
        neutral_pressure = HumanPressure()
        self.agent.step(neutral_pressure, dt=dt)
    
    def get_kinetic_energy(self) -> float:
        """運動エネルギー"""
        return 0.5 * self.mass * (self.velocity ** 2)
    
    def get_potential_energy(self, string_length: float = 2.0) -> float:
        """位置エネルギー"""
        angle = self.position / string_length
        height = string_length * (1.0 - np.cos(angle))
        return self.mass * 9.8 * height


class NewtonsCradleAnimated:
    """ニュートンのゆりかご - アニメーション版"""
    
    def __init__(self, n_balls: int = 5, spacing: float = 1.0,
                 string_length: float = 2.0, initial_release_angle: float = 30.0):
        self.n_balls = n_balls
        self.string_length = string_length
        self.gravity = 9.8
        self.radius = 0.5
        self.mass = 1.0
        self.spacing = spacing
        
        # 球の初期化
        self.balls = []
        for i in range(n_balls):
            initial_pos = 0.0
            ball = Ball(ball_id=i, initial_position=initial_pos, mass=self.mass)
            self.balls.append(ball)
        
        # 初期条件: 最初の球を持ち上げる
        release_angle_rad = np.radians(initial_release_angle)
        self.balls[0].position = release_angle_rad * string_length
        
        # シミュレーション状態
        self.current_time = 0.0
        self.total_steps = 0
        
        # エネルギー履歴
        self.energy_history = []
        self.initial_energy = None
    
    def detect_collisions(self):
        """衝突検出"""
        collisions = []
        
        for i in range(self.n_balls - 1):
            ball1 = self.balls[i]
            ball2 = self.balls[i + 1]
            
            # 支点からの水平位置
            x1 = (i - self.n_balls/2) * self.spacing + self.string_length * np.sin(ball1.position / self.string_length)
            x2 = (i + 1 - self.n_balls/2) * self.spacing + self.string_length * np.sin(ball2.position / self.string_length)
            
            distance = abs(x2 - x1)
            
            if distance <= self.radius * 2.0 * 1.01:
                relative_velocity = ball1.velocity - ball2.velocity
                if (x1 < x2 and relative_velocity > 0) or (x1 > x2 and relative_velocity < 0):
                    collisions.append((i, i+1))
        
        return collisions
    
    def resolve_collision(self, ball1_id: int, ball2_id: int):
        """衝突解決"""
        ball1 = self.balls[ball1_id]
        ball2 = self.balls[ball2_id]
        
        v1 = ball1.velocity
        v2 = ball2.velocity
        m1 = ball1.mass
        m2 = ball2.mass
        
        # 完全弾性衝突
        v1_new = ((m1 - m2) * v1 + 2 * m2 * v2) / (m1 + m2)
        v2_new = ((m2 - m1) * v2 + 2 * m1 * v1) / (m1 + m2)
        
        # 衝突適用
        ball1.apply_impact(v1_new, self.current_time)
        ball2.apply_impact(v2_new, self.current_time)
    
    def step(self, dt: float = 0.001):
        """1ステップ"""
        # 物理更新
        for ball in self.balls:
            ball.update_physics(dt, self.gravity, self.string_length)
        
        # 衝突検出・解決
        collisions = self.detect_collisions()
        for ball1_id, ball2_id in collisions:
            self.resolve_collision(ball1_id, ball2_id)
        
        # 時刻更新
        self.current_time += dt
        self.total_steps += 1
        
        # エネルギー記録
        total_energy = sum(b.get_kinetic_energy() + b.get_potential_energy(self.string_length) 
                          for b in self.balls)
        self.energy_history.append(total_energy)
        
        if self.initial_energy is None:
            self.initial_energy = total_energy
    
    def get_ball_position_xy(self, ball_id: int) -> tuple:
        """球のXY座標"""
        ball = self.balls[ball_id]
        angle = ball.position / self.string_length
        
        # 支点位置
        support_x = (ball_id - self.n_balls/2) * self.spacing
        
        # 球の位置
        x = support_x + self.string_length * np.sin(angle)
        y = -self.string_length * np.cos(angle)
        
        return (x, y)
    
    def get_support_position(self, ball_id: int) -> float:
        """支点のX座標"""
        return (ball_id - self.n_balls/2) * self.spacing


class CradleVisualizer:
    """アニメーションビジュアライザー"""
    
    def __init__(self, cradle: NewtonsCradleAnimated):
        self.cradle = cradle
        
        # Figure作成
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.suptitle("Newton's Cradle with SSD - ニュートンのゆりかご", 
                         fontsize=16, fontweight='bold')
        
        # サブプロット
        gs = self.fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        self.ax_pendulum = self.fig.add_subplot(gs[0, :])  # 上段全体: 振り子
        self.ax_energy = self.fig.add_subplot(gs[1, 0])    # 下段左: エネルギー
        self.ax_ssd = self.fig.add_subplot(gs[1, 1])       # 下段右: SSD状態
        
        # 初期化
        self.init_pendulum_plot()
    
    def init_pendulum_plot(self):
        """振り子プロット初期化"""
        self.ax_pendulum.clear()
        self.ax_pendulum.set_xlim(-4, 4)
        self.ax_pendulum.set_ylim(-3, 1)
        self.ax_pendulum.set_aspect('equal')
        self.ax_pendulum.set_title('Physical Simulation', fontweight='bold', fontsize=12)
        self.ax_pendulum.grid(True, alpha=0.3)
        
        # 支点を描画
        support_positions = [self.cradle.get_support_position(i) for i in range(self.cradle.n_balls)]
        self.ax_pendulum.plot(support_positions, [0] * len(support_positions), 
                             'ko-', markersize=10, linewidth=3, zorder=5)
        self.ax_pendulum.axhline(y=0, color='black', linewidth=2, alpha=0.5)
    
    def update_frame(self, frame):
        """フレーム更新"""
        # 複数ステップ実行（スムーズなアニメーション）
        for _ in range(5):
            self.cradle.step(dt=0.001)
        
        # 描画更新
        self.draw_pendulums()
        self.draw_energy()
        self.draw_ssd_state()
        
        return []
    
    def draw_pendulums(self):
        """振り子描画"""
        self.ax_pendulum.clear()
        self.ax_pendulum.set_xlim(-4, 4)
        self.ax_pendulum.set_ylim(-3, 1)
        self.ax_pendulum.set_aspect('equal')
        self.ax_pendulum.set_title(f'Physical Simulation (t={self.cradle.current_time:.2f}s)', 
                                   fontweight='bold', fontsize=12)
        self.ax_pendulum.grid(True, alpha=0.3)
        
        # 支点
        support_positions = [self.cradle.get_support_position(i) for i in range(self.cradle.n_balls)]
        self.ax_pendulum.plot(support_positions, [0] * len(support_positions), 
                             'ko-', markersize=10, linewidth=3, zorder=5)
        self.ax_pendulum.axhline(y=0, color='black', linewidth=2, alpha=0.5)
        
        # 各球
        for i in range(self.cradle.n_balls):
            ball = self.cradle.balls[i]
            support_x = self.cradle.get_support_position(i)
            ball_x, ball_y = self.cradle.get_ball_position_xy(i)
            
            # 紐
            self.ax_pendulum.plot([support_x, ball_x], [0, ball_y], 
                                 'k-', linewidth=2, alpha=0.7, zorder=1)
            
            # 球（衝突中は赤、通常は青）
            color = 'red' if ball.collision_count > 0 and (self.cradle.current_time - ball.last_collision_time) < 0.1 else 'blue'
            circle = Circle((ball_x, ball_y), self.cradle.radius, 
                          color=color, alpha=0.8, zorder=10)
            self.ax_pendulum.add_patch(circle)
            
            # 球のID
            self.ax_pendulum.text(ball_x, ball_y, str(i), 
                                ha='center', va='center', 
                                fontsize=10, fontweight='bold', color='white', zorder=11)
            
            # 速度ベクトル
            if abs(ball.velocity) > 0.1:
                angle = ball.position / self.cradle.string_length
                vx = ball.velocity * np.cos(angle) * 0.3
                vy = ball.velocity * np.sin(angle) * 0.3
                self.ax_pendulum.arrow(ball_x, ball_y, vx, vy,
                                      head_width=0.15, head_length=0.1,
                                      fc='green', ec='green', alpha=0.7, zorder=9)
    
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
            
            if self.cradle.initial_energy is not None:
                self.ax_energy.axhline(self.cradle.initial_energy, 
                                      color='r', linestyle='--', linewidth=1.5, 
                                      alpha=0.7, label='Initial Energy')
            
            self.ax_energy.legend(fontsize=9)
            self.ax_energy.grid(True, alpha=0.3)
    
    def draw_ssd_state(self):
        """SSD状態プロット"""
        self.ax_ssd.clear()
        self.ax_ssd.set_title('SSD State: E Accumulation', fontweight='bold', fontsize=11)
        self.ax_ssd.set_xlabel('Ball ID')
        self.ax_ssd.set_ylabel('E (Accumulated Stress)')
        
        ball_ids = list(range(self.cradle.n_balls))
        
        # E蓄積（各層）
        E_base = [b.agent.state.E[1] for b in self.cradle.balls]
        E_core = [b.agent.state.E[2] for b in self.cradle.balls]
        E_upper = [b.agent.state.E[3] for b in self.cradle.balls]
        
        width = 0.25
        self.ax_ssd.bar([i - width for i in ball_ids], E_base, width, 
                       label='E_BASE', alpha=0.7, color='orange')
        self.ax_ssd.bar(ball_ids, E_core, width, 
                       label='E_CORE', alpha=0.7, color='red')
        self.ax_ssd.bar([i + width for i in ball_ids], E_upper, width, 
                       label='E_UPPER', alpha=0.7, color='purple')
        
        self.ax_ssd.legend(fontsize=9)
        self.ax_ssd.grid(True, alpha=0.3)
        
        # 統計情報（テキスト）
        total_collisions = sum(b.collision_count for b in self.cradle.balls)
        total_E = sum(np.mean(b.agent.state.E) for b in self.cradle.balls)
        avg_damping = np.mean([b.damping_factor for b in self.cradle.balls])
        
        stats_text = f'Collisions: {total_collisions} | Total E: {total_E:.3f} | Avg Damping: {avg_damping:.4f}'
        self.ax_ssd.text(0.5, 0.95, stats_text, 
                        transform=self.ax_ssd.transAxes,
                        ha='center', va='top', fontsize=9,
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def animate(self, frames: int = 1000, interval: int = 20):
        """アニメーション開始"""
        print(f"\nアニメーション開始: {frames}フレーム")
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
        
        return anim


def demo_classic():
    """クラシックデモ: 1球"""
    print("="*70)
    print("Newton's Cradle - Classic Demo (1 Ball)")
    print("="*70)
    print("\nシナリオ: 左端の球を30度持ち上げて離す")
    print("期待: 右端の球が跳ね上がる（運動量保存）\n")
    
    cradle = NewtonsCradleAnimated(
        n_balls=5,
        spacing=1.0,
        string_length=2.0,
        initial_release_angle=30.0
    )
    
    viz = CradleVisualizer(cradle)
    viz.animate(frames=1000, interval=20)


def demo_multiple():
    """複数球デモ: 2球"""
    print("="*70)
    print("Newton's Cradle - Multiple Balls Demo (2 Balls)")
    print("="*70)
    print("\nシナリオ: 左端2球を持ち上げて離す")
    print("期待: 右端2球が跳ね上がる\n")
    
    cradle = NewtonsCradleAnimated(
        n_balls=5,
        spacing=1.0,
        string_length=2.0,
        initial_release_angle=30.0
    )
    
    # 2球目も持ち上げる
    cradle.balls[1].position = np.radians(29.0) * cradle.string_length
    
    viz = CradleVisualizer(cradle)
    viz.animate(frames=1000, interval=20)


def demo_extreme():
    """極端デモ: 大きな角度"""
    print("="*70)
    print("Newton's Cradle - Extreme Demo (60 degrees)")
    print("="*70)
    print("\nシナリオ: 左端の球を60度持ち上げて離す")
    print("期待: 高エネルギー伝達、SSDによる減衰観察\n")
    
    cradle = NewtonsCradleAnimated(
        n_balls=5,
        spacing=1.0,
        string_length=2.0,
        initial_release_angle=60.0
    )
    
    viz = CradleVisualizer(cradle)
    viz.animate(frames=1500, interval=20)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "multiple":
            demo_multiple()
        elif sys.argv[1] == "extreme":
            demo_extreme()
        else:
            demo_classic()
    else:
        demo_classic()
    
    print("\n" + "="*70)
    print("デモ完了!")
    print("="*70)
    print("\n💡 Tip:")
    print("  python examples/newtons_cradle_animated.py           # 1球デモ")
    print("  python examples/newtons_cradle_animated.py multiple  # 2球デモ")
    print("  python examples/newtons_cradle_animated.py extreme   # 極端デモ (60度)")
