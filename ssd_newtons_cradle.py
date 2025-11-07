"""
SSD Newton's Cradle - ニュートンのゆりかご

SSD方程式でエネルギー・運動量保存を実現
整合流=運動量フロー、整合慣性=質量、意味圧=衝突力
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, FancyBboxPatch
from dataclasses import dataclass
from typing import List
import matplotlib
matplotlib.use('TkAgg')


@dataclass
class Pendulum:
    """振り子（SSD駆動）"""
    id: int
    mass: float = 1.0           # 質量
    length: float = 1.0         # 紐の長さ
    
    # SSD状態
    theta: float = 0.0          # 角度 [rad]
    omega: float = 0.0          # 角速度 [rad/s]
    j: float = 0.0              # 整合流（運動量フロー）
    kappa: float = 1.0          # 整合慣性（質量に対応）
    E: float = 0.0              # 未処理圧（余剰エネルギー）
    
    # 衝突状態
    in_contact: bool = False
    contact_force: float = 0.0
    
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


class NewtonsCradle:
    """ニュートンのゆりかご（SSDエンジン）"""
    
    def __init__(self, n_pendulums: int = 5, spacing: float = 0.21):
        self.n = n_pendulums
        self.spacing = spacing  # 振り子間隔（球の直径=0.2なので0.21で軽く接触）
        self.pendulums: List[Pendulum] = []
        
        # 振り子を生成（等間隔配置）
        for i in range(n_pendulums):
            pend = Pendulum(
                id=i,
                mass=1.0,
                length=1.0,
                theta=0.0,  # 初期は垂直（静止位置）
                omega=0.0,
                kappa=1.0  # 質量＝整合慣性
            )
            self.pendulums.append(pend)
        
        # SSDパラメータ
        self.g_gravity = 9.8
        self.G0 = 0.1               # 基底応答
        self.g_coupling = 1.0       # 結合強度
        self.eta = 0.0              # 学習率（今回は固定質量）
        self.damping = 0.0005       # 減衰（空気抵抗）小さくしてよりリアルに
        self.restitution = 0.995    # 反発係数（エネルギー損失）
        
        # 統計
        self.total_energy_history = []
        self.collision_count = 0
        self.time = 0.0
        
    def compute_meaning_pressure(self, pend: Pendulum) -> float:
        """
        意味圧の計算
        p = 重力トルク + 衝突力
        """
        # 重力による復元トルク（意味圧）
        p_gravity = -self.g_gravity * np.sin(pend.theta) / pend.length
        
        # 衝突による意味圧
        p_collision = pend.contact_force
        
        return p_gravity + p_collision
    
    def detect_collisions(self):
        """衝突検出"""
        # 全振り子の接触をリセット
        for pend in self.pendulums:
            pend.in_contact = False
            pend.contact_force = 0.0
        
        # 隣接振り子との衝突判定
        ball_radius = 0.1  # 球の半径
        collision_threshold = ball_radius * 2.1  # 接触判定距離（少し余裕を持たせる）
        
        for i in range(self.n - 1):
            pend_left = self.pendulums[i]
            pend_right = self.pendulums[i + 1]
            
            # 各振り子の支点
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
                # 相対速度（接線速度）
                v_left = pend_left.get_velocity()
                v_right = pend_right.get_velocity()
                v_rel = v_left - v_right
                
                # 接近中のみ衝突処理（離れる方向なら無視）
                if v_rel > 0.01:
                    pend_left.in_contact = True
                    pend_right.in_contact = True
                    
                    # 弾性衝突の運動量・エネルギー保存則
                    m1 = pend_left.mass
                    m2 = pend_right.mass
                    
                    # 完全弾性衝突の公式
                    v1_new = ((m1 - m2) * v_left + 2 * m2 * v_right) / (m1 + m2)
                    v2_new = ((m2 - m1) * v_right + 2 * m1 * v_left) / (m1 + m2)
                    
                    # 反発係数
                    v1_new *= self.restitution
                    v2_new *= self.restitution
                    
                    # 速度を直接角速度に変換
                    pend_left.omega = v1_new / pend_left.length
                    pend_right.omega = v2_new / pend_right.length
                    
                    self.collision_count += 1
    
    def update_pendulum_ssd(self, pend: Pendulum, dt: float):
        """振り子のSSD更新"""
        # 意味圧計算
        p = self.compute_meaning_pressure(pend)
        
        # 整合流（SSD基本式）
        G = self.G0 + self.g_coupling * pend.kappa
        pend.j = G * p
        
        # 整合流 = 角加速度
        alpha = pend.j
        
        # 角速度更新（運動方程式）
        pend.omega += alpha * dt
        
        # 減衰
        pend.omega *= (1.0 - self.damping)
        
        # 角度更新
        pend.theta += pend.omega * dt
        
        # エネルギー更新（未処理圧）
        # 理論値との差異がE（散逸エネルギー）
        theoretical_energy = pend.get_kinetic_energy() + pend.get_potential_energy()
        pend.E = abs(theoretical_energy - (pend.get_kinetic_energy() + pend.get_potential_energy()))
    
    def step(self, dt: float = 0.001):
        """1ステップ更新"""
        # 衝突検出
        self.detect_collisions()
        
        # 全振り子を更新
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


# ========================================
# ビジュアライゼーション
# ========================================

class CradleVisualizer:
    """ニュートンのゆりかごビジュアライザー"""
    
    def __init__(self, cradle: NewtonsCradle):
        self.cradle = cradle
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.suptitle("SSD Newton's Cradle - ニュートンのゆりかご", 
                         fontsize=14, fontweight='bold')
        
        # 描画要素
        self.pendulum_lines = []
        self.pendulum_circles = []
        
        # エネルギー履歴
        self.energy_history = []
        self.time_history = []
        
    def init_animation(self):
        """アニメーション初期化"""
        ax = self.axes[0, 0]
        ax.clear()
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 0.5)
        ax.set_aspect('equal')
        ax.set_title('物理シミュレーション', fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # 支点
        support_x = [(p.id - (self.cradle.n - 1) / 2) * self.cradle.spacing 
                     for p in self.cradle.pendulums]
        ax.plot(support_x, [0] * len(support_x), 'ko-', markersize=8, linewidth=2)
        
        return []
    
    def update_frame(self, frame):
        """フレーム更新"""
        # 複数ステップ実行（滑らかな動き）
        for _ in range(10):
            self.cradle.step(dt=0.001)
        
        # 描画更新
        self.draw_pendulums()
        self.draw_energy_plot()
        self.draw_phase_space()
        self.draw_statistics()
        
        return []
    
    def draw_pendulums(self):
        """振り子の描画"""
        ax = self.axes[0, 0]
        ax.clear()
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 0.5)
        ax.set_aspect('equal')
        ax.set_title('物理シミュレーション', fontweight='bold')
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
        ax.set_title('エネルギー保存則', fontweight='bold')
        
        if len(self.cradle.total_energy_history) > 1:
            times = np.arange(len(self.cradle.total_energy_history)) * 0.01
            energies = self.cradle.total_energy_history
            
            ax.plot(times, energies, 'b-', linewidth=2, label='総エネルギー')
            
            # 各振り子のエネルギー
            for i, pend in enumerate(self.cradle.pendulums):
                ke = pend.get_kinetic_energy()
                pe = pend.get_potential_energy()
                # 簡易表示（最新値のみ）
                if i == 0:
                    ax.axhline(ke, color='green', linestyle='--', 
                              alpha=0.3, label='運動E')
                    ax.axhline(pe, color='orange', linestyle='--', 
                              alpha=0.3, label='位置E')
            
            # 初期エネルギー
            if len(energies) > 10:
                initial_energy = np.mean(energies[:10])
                ax.axhline(initial_energy, color='red', linestyle='--', 
                          alpha=0.5, label=f'初期E={initial_energy:.3f}')
            
            ax.set_xlabel('時間 [s]')
            ax.set_ylabel('エネルギー [J]')
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
    
    def draw_phase_space(self):
        """位相空間（角度-角速度）"""
        ax = self.axes[1, 0]
        ax.clear()
        ax.set_title('位相空間 (θ-ω)', fontweight='bold')
        
        for i, pend in enumerate(self.cradle.pendulums):
            color = plt.cm.viridis(i / self.cradle.n)
            ax.plot(np.degrees(pend.theta), pend.omega, 'o', 
                   color=color, markersize=10, alpha=0.7,
                   label=f'球{i+1}')
        
        ax.set_xlabel('角度 θ [度]')
        ax.set_ylabel('角速度 ω [rad/s]')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='upper right')
        ax.axhline(0, color='black', linewidth=0.5)
        ax.axvline(0, color='black', linewidth=0.5)
    
    def draw_statistics(self):
        """統計情報"""
        ax = self.axes[1, 1]
        ax.clear()
        ax.set_title('SSD統計', fontweight='bold')
        ax.axis('off')
        
        total_energy = sum(p.get_kinetic_energy() + p.get_potential_energy() 
                          for p in self.cradle.pendulums)
        
        # エネルギー損失率
        if len(self.cradle.total_energy_history) > 10:
            initial_energy = np.mean(self.cradle.total_energy_history[:10])
            energy_loss = (initial_energy - total_energy) / initial_energy * 100
        else:
            energy_loss = 0.0
        
        text = (f"時刻: {self.cradle.time:.2f} s\n"
               f"衝突回数: {self.cradle.collision_count}\n\n"
               f"総エネルギー: {total_energy:.4f} J\n"
               f"エネルギー損失: {energy_loss:.2f}%\n\n"
               f"各振り子の状態:\n")
        
        for i, pend in enumerate(self.cradle.pendulums):
            status = "🔴" if pend.in_contact else "⚪"
            text += (f"\n球{i+1} {status}\n"
                    f"  角度: {np.degrees(pend.theta):6.2f}°\n"
                    f"  角速度: {pend.omega:6.3f} rad/s\n"
                    f"  速度: {pend.get_velocity():6.3f} m/s\n")
        
        text += (f"\nSSDパラメータ:\n"
                f"  反発係数: {self.cradle.restitution:.3f}\n"
                f"  減衰: {self.cradle.damping:.4f}\n"
                f"  整合慣性κ: {self.cradle.pendulums[0].kappa:.2f}")
        
        ax.text(0.05, 0.95, text, fontsize=9, family='monospace',
               verticalalignment='top', transform=ax.transAxes)
    
    def animate(self, frames: int = 1000):
        """アニメーション実行"""
        anim = FuncAnimation(self.fig, self.update_frame, 
                           init_func=self.init_animation,
                           frames=frames, interval=20, blit=False, repeat=True)
        return anim


# ========================================
# デモシナリオ
# ========================================

def demo_classic_cradle():
    """クラシックなニュートンのゆりかご"""
    print("=" * 70)
    print("SSD Newton's Cradle - ニュートンのゆりかご")
    print("=" * 70)
    print("\n🎯 デモ: クラシック動作（1球→1球）")
    print("\nSSD方程式による実装:")
    print("  整合流 j = (G₀ + gκ)p")
    print("  意味圧 p = 重力トルク + 衝突力")
    print("  整合慣性 κ = 質量")
    print("\n運動量・エネルギー保存を整合流で実現")
    
    # ゆりかご生成
    cradle = NewtonsCradle(n_pendulums=5, spacing=0.22)
    
    # 左端の球を持ち上げる（45度）
    cradle.set_initial_angle(0, 45.0)
    
    print(f"\n初期状態:")
    print(f"  球1: 角度 = 45°")
    print(f"  球2-5: 角度 = 0°")
    
    # ビジュアライザー
    viz = CradleVisualizer(cradle)
    
    print("\n🎬 アニメーション開始...")
    print("観察ポイント:")
    print("  ✓ 運動量保存（1球→1球の転送）")
    print("  ✓ エネルギー保存（減衰は最小）")
    print("  ✓ 周期運動の安定性")
    
    anim = viz.animate(frames=1500)
    
    plt.tight_layout()
    plt.show()
    
    print("\n✓ デモ完了")


def demo_two_ball_cradle():
    """2球同時リリース"""
    print("\n" + "=" * 70)
    print("🎯 デモ: 2球同時（2球→2球）")
    print("=" * 70)
    
    cradle = NewtonsCradle(n_pendulums=5, spacing=0.22)
    
    # 左端2球を持ち上げる
    cradle.set_initial_angle(0, 40.0)
    cradle.set_initial_angle(1, 35.0)
    
    print(f"\n初期状態:")
    print(f"  球1: 角度 = 40°")
    print(f"  球2: 角度 = 35°")
    print(f"  球3-5: 角度 = 0°")
    print("\n予想: 右端から2球が跳ね返る")
    
    viz = CradleVisualizer(cradle)
    anim = viz.animate(frames=1500)
    
    plt.tight_layout()
    plt.savefig('C:\\Users\\Public\\ssd_newtons_cradle.png', 
                dpi=150, bbox_inches='tight')
    print("\n✓ 図を保存: ssd_newtons_cradle.png")
    
    plt.show()


def demo_chaos_cradle():
    """カオスモード（全球ランダム）"""
    print("\n" + "=" * 70)
    print("🎯 デモ: カオスモード（全球同時リリース）")
    print("=" * 70)
    
    cradle = NewtonsCradle(n_pendulums=5, spacing=0.22)
    
    # 全球にランダムな初期角度
    for i in range(5):
        angle = np.random.uniform(-30, 30)
        cradle.set_initial_angle(i, angle)
        print(f"  球{i+1}: 角度 = {angle:.1f}°")
    
    print("\n予想: 複雑な衝突パターン→やがて減衰")
    
    viz = CradleVisualizer(cradle)
    anim = viz.animate(frames=2000)
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("SSD Newton's Cradle - デモ選択")
    print("=" * 70)
    print("\n[1] クラシック（1球→1球）")
    print("[2] 2球同時リリース（2球→2球）")
    print("[3] カオスモード（全球ランダム）")
    print("[0] すべて実行")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\n選択 [0-3]: ").strip()
    
    if choice == "1":
        demo_classic_cradle()
    elif choice == "2":
        demo_two_ball_cradle()
    elif choice == "3":
        demo_chaos_cradle()
    else:
        # デフォルト: クラシック
        demo_classic_cradle()
