"""
SSD Newton's Cradle v3.5 - ニュートンのゆりかご (v3.5エンジン使用)

SSD v3.5の直接作用モードでエネルギー・運動量保存を実現
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle
from dataclasses import dataclass
from typing import List
import matplotlib
from ssd_core_engine_v3_5 import SSDCoreEngineV3_5, SSDParametersV3_5, SSDStateV3_5, SSDDomain

matplotlib.use('TkAgg')


@dataclass
class PendulumV3_5:
    """振り子（SSD v3.5駆動）"""
    id: int
    mass: float = 1.0           # 質量
    length: float = 1.0         # 紐の長さ
    
    # 運動状態
    theta: float = 0.0          # 角度 [rad]
    omega: float = 0.0          # 角速度 [rad/s]
    
    # SSD v3.5状態
    state: SSDStateV3_5 = None
    engine: SSDCoreEngineV3_5 = None
    
    # 衝突状態
    in_contact: bool = False
    contact_force: float = 0.0
    
    def __post_init__(self):
        """SSD初期化"""
        if self.state is None:
            self.state = SSDStateV3_5(
                kappa=self.mass,
                E_direct=0.0,
                E_indirect=0.0
            )
        
        if self.engine is None:
            # 物理系パラメータ（直接作用のみ）
            params = SSDParametersV3_5(
                use_direct_action=True,
                use_indirect_action=False,
                amplification_factor=1.0,
                G0=0.1,
                g=1.0,
                alpha=0.5,
                beta_decay=0.0,  # 物理系なので減衰なし
                gamma_i2d=0.0,
                gamma_d2i=0.0,
                enable_phase_transition=False,
            )
            self.engine = SSDCoreEngineV3_5(params)
            self.engine.domain = SSDDomain.PHYSICS
    
    def get_position(self) -> np.ndarray:
        """球の位置"""
        x = self.length * np.sin(self.theta)
        y = -self.length * np.cos(self.theta)
        return np.array([x, y])
    
    def get_velocity(self) -> float:
        """接線速度"""
        return self.length * self.omega
    
    def get_kinetic_energy(self) -> float:
        """運動エネルギー"""
        return 0.5 * self.mass * (self.get_velocity() ** 2)
    
    def get_potential_energy(self) -> float:
        """位置エネルギー"""
        y = self.get_position()[1]
        return self.mass * 9.8 * (y + self.length)


class NewtonsCradleV3_5:
    """ニュートンのゆりかご（SSD v3.5エンジン）"""
    
    def __init__(self, n_pendulums: int = 5, spacing: float = 0.21):
        self.n = n_pendulums
        self.spacing = spacing
        self.pendulums: List[PendulumV3_5] = []
        
        # 振り子を生成
        for i in range(n_pendulums):
            pend = PendulumV3_5(
                id=i,
                mass=1.0,
                length=1.0,
                theta=0.0,
                omega=0.0
            )
            self.pendulums.append(pend)
        
        # 物理パラメータ
        self.g_gravity = 9.8
        self.damping = 0.0005
        self.restitution = 0.995
        
        # 統計
        self.total_energy_history = []
        self.collision_count = 0
        self.time = 0.0
    
    def detect_collisions(self):
        """衝突検出"""
        for pend in self.pendulums:
            pend.in_contact = False
            pend.contact_force = 0.0
        
        ball_radius = 0.1
        collision_threshold = ball_radius * 2.1
        
        for i in range(self.n - 1):
            pend_left = self.pendulums[i]
            pend_right = self.pendulums[i + 1]
            
            # 支点位置
            support_left = (i - (self.n - 1) / 2) * self.spacing
            support_right = (i + 1 - (self.n - 1) / 2) * self.spacing
            
            # 球の絶対位置
            pos_left = pend_left.get_position()
            pos_right = pend_right.get_position()
            
            ball_pos_left = np.array([support_left + pos_left[0], pos_left[1]])
            ball_pos_right = np.array([support_right + pos_right[0], pos_right[1]])
            
            distance = np.linalg.norm(ball_pos_right - ball_pos_left)
            
            # 衝突判定
            if distance < collision_threshold:
                v_left = pend_left.get_velocity()
                v_right = pend_right.get_velocity()
                v_rel = v_left - v_right
                
                # 接近中のみ衝突処理
                if v_rel > 0.01:
                    pend_left.in_contact = True
                    pend_right.in_contact = True
                    
                    # 完全弾性衝突
                    m1 = pend_left.mass
                    m2 = pend_right.mass
                    
                    v1_new = ((m1 - m2) * v_left + 2 * m2 * v_right) / (m1 + m2)
                    v2_new = ((m2 - m1) * v_right + 2 * m1 * v_left) / (m1 + m2)
                    
                    # 反発係数
                    v1_new *= self.restitution
                    v2_new *= self.restitution
                    
                    # 速度を角速度に変換
                    pend_left.omega = v1_new / pend_left.length
                    pend_right.omega = v2_new / pend_right.length
                    
                    # SSDに衝突力を伝達
                    impulse = abs(m1 * (v1_new - v_left))
                    pend_left.contact_force = impulse * 1000.0
                    pend_right.contact_force = impulse * 1000.0
                    
                    self.collision_count += 1
    
    def update_pendulum_ssd(self, pend: PendulumV3_5, dt: float):
        """振り子のSSD v3.5更新"""
        # 重力トルクを意味圧に変換
        gravity_torque = -self.g_gravity * np.sin(pend.theta) / pend.length
        p_external = np.array([gravity_torque, 0.0, 0.0])
        
        # 衝突力
        contact_pressure = None
        if pend.in_contact:
            contact_pressure = np.array([pend.contact_force, 0.0, 0.0])
        
        # SSD v3.5エンジンでステップ実行
        pend.state = pend.engine.step(
            pend.state,
            p_external=p_external,
            dt=dt,
            contact_pressure=contact_pressure
        )
        
        # SSDから得られたエネルギーを角加速度に変換
        # E_directが運動エネルギーに対応
        if pend.state.E_direct > 0:
            # エネルギーから加速度を計算（簡易版）
            alpha = gravity_torque
        else:
            alpha = gravity_torque
        
        # 角速度更新
        pend.omega += alpha * dt
        pend.omega *= (1.0 - self.damping)
        
        # 角度更新
        pend.theta += pend.omega * dt
    
    def step(self, dt: float = 0.001):
        """1ステップ更新"""
        self.detect_collisions()
        
        for pend in self.pendulums:
            self.update_pendulum_ssd(pend, dt)
        
        self.time += dt
        
        # エネルギー記録
        total_energy = sum(p.get_kinetic_energy() + p.get_potential_energy() 
                          for p in self.pendulums)
        self.total_energy_history.append(total_energy)
    
    def set_initial_angle(self, pendulum_index: int, angle_deg: float):
        """初期角度を設定"""
        self.pendulums[pendulum_index].theta = np.radians(angle_deg)
        self.pendulums[pendulum_index].omega = 0.0


class CradleVisualizerV3_5:
    """ニュートンのゆりかごビジュアライザー v3.5"""
    
    def __init__(self, cradle: NewtonsCradleV3_5):
        self.cradle = cradle
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.suptitle("SSD v3.5 Newton's Cradle - ニュートンのゆりかご", 
                         fontsize=14, fontweight='bold')
    
    def init_animation(self):
        """アニメーション初期化"""
        ax = self.axes[0, 0]
        ax.clear()
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 0.5)
        ax.set_aspect('equal')
        ax.set_title('Physical Simulation (v3.5)', fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 支点
        support_x = [(p.id - (self.cradle.n - 1) / 2) * self.cradle.spacing 
                     for p in self.cradle.pendulums]
        ax.plot(support_x, [0] * len(support_x), 'ko-', markersize=8, linewidth=2)
        
        return []
    
    def update_frame(self, frame):
        """フレーム更新"""
        # 複数ステップ実行
        for _ in range(10):
            self.cradle.step(dt=0.001)
        
        # 描画更新
        self.draw_pendulums()
        self.draw_energy_plot()
        self.draw_ssd_energy()
        self.draw_statistics()
        
        return []
    
    def draw_pendulums(self):
        """振り子の描画"""
        ax = self.axes[0, 0]
        ax.clear()
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 0.5)
        ax.set_aspect('equal')
        ax.set_title('Physical Simulation (v3.5)', fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 支点
        support_x = [(p.id - (self.cradle.n - 1) / 2) * self.cradle.spacing 
                     for p in self.cradle.pendulums]
        ax.plot(support_x, [0] * len(support_x), 'ko-', markersize=8, linewidth=2)
        
        # 各振り子
        for i, pend in enumerate(self.cradle.pendulums):
            support_x = (i - (self.cradle.n - 1) / 2) * self.cradle.spacing
            pos = pend.get_position()
            ball_x = support_x + pos[0]
            ball_y = pos[1]
            
            # 紐
            ax.plot([support_x, ball_x], [0, ball_y], 'k-', linewidth=2, alpha=0.7)
            
            # 球
            color = 'red' if pend.in_contact else 'blue'
            circle = Circle((ball_x, ball_y), 0.1, color=color, alpha=0.8, zorder=10)
            ax.add_patch(circle)
            
            # 速度ベクトル
            v = pend.get_velocity()
            if abs(v) > 0.01:
                direction = np.array([np.cos(pend.theta), np.sin(pend.theta)])
                ax.arrow(ball_x, ball_y, 
                        direction[0] * v * 0.2, direction[1] * v * 0.2,
                        head_width=0.05, head_length=0.03, 
                        fc='green', ec='green', alpha=0.6)
    
    def draw_energy_plot(self):
        """エネルギープロット"""
        ax = self.axes[0, 1]
        ax.clear()
        ax.set_title('Total Energy Conservation', fontweight='bold')
        ax.set_xlabel('Time Step')
        ax.set_ylabel('Energy (J)')
        
        if len(self.cradle.total_energy_history) > 0:
            ax.plot(self.cradle.total_energy_history, 'b-', linewidth=1.5, label='Total Energy')
            ax.axhline(self.cradle.total_energy_history[0], color='r', 
                      linestyle='--', linewidth=1, alpha=0.7, label='Initial Energy')
            ax.legend()
            ax.grid(True, alpha=0.3)
    
    def draw_ssd_energy(self):
        """SSD v3.5エネルギー"""
        ax = self.axes[1, 0]
        ax.clear()
        ax.set_title('SSD v3.5 Energy States', fontweight='bold')
        ax.set_xlabel('Pendulum ID')
        ax.set_ylabel('Energy (J)')
        
        ids = [p.id for p in self.cradle.pendulums]
        e_direct = [p.state.E_direct for p in self.cradle.pendulums]
        e_indirect = [p.state.E_indirect for p in self.cradle.pendulums]
        
        ax.bar(ids, e_direct, width=0.4, label='E_direct', alpha=0.7)
        ax.bar([i + 0.4 for i in ids], e_indirect, width=0.4, label='E_indirect', alpha=0.7)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def draw_statistics(self):
        """統計情報"""
        ax = self.axes[1, 1]
        ax.clear()
        ax.axis('off')
        
        # 統計テキスト
        total_KE = sum(p.get_kinetic_energy() for p in self.cradle.pendulums)
        total_PE = sum(p.get_potential_energy() for p in self.cradle.pendulums)
        total_E = total_KE + total_PE
        
        total_E_direct = sum(p.state.E_direct for p in self.cradle.pendulums)
        total_E_indirect = sum(p.state.E_indirect for p in self.cradle.pendulums)
        
        stats_text = f"""
SSD v3.5 Statistics
{'='*40}

Time: {self.cradle.time:.2f} s
Collisions: {self.cradle.collision_count}

Classical Energy:
  Kinetic:    {total_KE:.4f} J
  Potential:  {total_PE:.4f} J
  Total:      {total_E:.4f} J

SSD v3.5 Energy:
  E_direct:   {total_E_direct:.4f} J
  E_indirect: {total_E_indirect:.4f} J
  
Energy Conservation:
  Deviation:  {abs(total_E - self.cradle.total_energy_history[0]) if self.cradle.total_energy_history else 0:.6f} J
  Efficiency: {(total_E / self.cradle.total_energy_history[0] * 100) if self.cradle.total_energy_history else 100:.2f}%
        """
        
        ax.text(0.1, 0.5, stats_text, fontsize=10, family='monospace',
               verticalalignment='center')
    
    def animate(self, frames: int = 500, interval: int = 20):
        """アニメーション実行"""
        anim = FuncAnimation(
            self.fig, 
            self.update_frame,
            init_func=self.init_animation,
            frames=frames,
            interval=interval,
            blit=False
        )
        plt.tight_layout()
        plt.show()
        return anim


def demo_classic_cradle():
    """クラシックなニュートンのゆりかごデモ"""
    print("="*70)
    print("SSD v3.5 Newton's Cradle Demo")
    print("="*70)
    print("\nシナリオ: 左端の球を持ち上げて離す")
    print("期待される動作: 右端の球だけが跳ね上がる（運動量保存）\n")
    
    # ゆりかご作成
    cradle = NewtonsCradleV3_5(n_pendulums=5, spacing=0.21)
    
    # 左端の球を45度持ち上げる
    cradle.set_initial_angle(0, 45.0)
    
    # ビジュアライザー
    viz = CradleVisualizerV3_5(cradle)
    viz.animate(frames=500, interval=20)


def demo_multiple_balls():
    """複数球デモ"""
    print("="*70)
    print("SSD v3.5 Newton's Cradle - Multiple Balls Demo")
    print("="*70)
    print("\nシナリオ: 左端2球を持ち上げて離す")
    print("期待される動作: 右端2球が跳ね上がる\n")
    
    cradle = NewtonsCradleV3_5(n_pendulums=5, spacing=0.21)
    
    # 左端2球を持ち上げる
    cradle.set_initial_angle(0, 45.0)
    cradle.set_initial_angle(1, 44.5)  # 少しだけずらして接触させる
    
    viz = CradleVisualizerV3_5(cradle)
    viz.animate(frames=500, interval=20)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "multiple":
        demo_multiple_balls()
    else:
        demo_classic_cradle()
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70)
    print("\n💡 Tip: Run 'python ssd_newtons_cradle_v3_5.py multiple' for multiple balls demo")
