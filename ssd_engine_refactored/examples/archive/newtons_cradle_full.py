"""
ニュートンのゆりかご - SSDフル版
Newton's Cradle with SSD Core (Full Version)

【物理シミュレーション + SSD主観】
- 各球は物理法則に従う（運動量保存、エネルギー保存）
- 各球は「衝突」を意味圧として解釈
- E蓄積による「疲労」で減衰
- κによる「記憶」で予測的反応

作成日: 2025年11月7日
バージョン: 1.0 (Full)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys
import os
from typing import List, Tuple, Optional

# 親ディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ssd_core_engine import SSDCoreEngine, SSDCoreState, SSDCoreParams
from ssd_human_module import HumanAgent, HumanPressure


class Ball:
    """
    ニュートンのゆりかごの球
    
    【物理属性】
    - position: 位置
    - velocity: 速度
    - mass: 質量
    
    【SSD主観属性】
    - engine: SSDコアエンジン（E, κの力学）
    - collision_memory: 衝突記憶
    """
    
    def __init__(self, ball_id: int, initial_position: float, mass: float = 1.0):
        self.ball_id = ball_id
        self.position = initial_position
        self.velocity = 0.0
        self.mass = mass
        self.radius = 0.5
        
        # SSDコアエンジン
        # SSDコアエンジン（各球が主観を持つ）
        self.agent = HumanAgent()
        
        # 衝突記憶
        self.collision_count = 0
        self.total_impact = 0.0
        self.last_collision_time = 0.0
        
        # 減衰（疲労）
        self.damping_factor = 0.0  # E蓄積により増加
    
    def apply_impact(self, impact_velocity: float, current_time: float):
        """
        衝突の影響を受ける
        
        Args:
            impact_velocity: 衝突速度
            current_time: 現在時刻
        """
        # 運動量保存則
        self.velocity = impact_velocity
        
        # SSD主観: 衝突を圧力として解釈
        impact_magnitude = abs(impact_velocity)
        
        # 衝突強度に応じた意味圧
        pressure = HumanPressure(
            base=impact_magnitude * 1.5,  # BASE: 生存脅威（強い衝撃 = 破損リスク）
            core=impact_magnitude * 0.5,  # CORE: 規範的圧力（低）
            upper=impact_magnitude * 0.2  # UPPER: 理念的圧力（低）
        )
        
        # SSDエンジンで処理
        self.agent.step(pressure, dt=0.01)
        
        # E蓄積による減衰（疲労）
        E = self.agent.state.E
        self.damping_factor = np.mean(E) * 0.01  # E平均値で減衰率を決定
        
        # 記憶更新
        self.collision_count += 1
        self.total_impact += impact_magnitude
        self.last_collision_time = current_time
    
    def update_physics(self, dt: float, gravity: float = 9.8, string_length: float = 2.0):
        """
        物理状態を更新
        
        Args:
            dt: 時間刻み
            gravity: 重力加速度
            string_length: 糸の長さ
        """
        # 重力による加速（振り子の運動）
        angle = self.position / string_length
        angular_acceleration = -(gravity / string_length) * np.sin(angle)
        angular_velocity = self.velocity / string_length
        
        # 角速度の更新（減衰あり）
        angular_velocity += angular_acceleration * dt
        angular_velocity *= (1.0 - self.damping_factor)  # SSDによる減衰
        
        # 角度の更新
        angle += angular_velocity * dt
        
        # 位置・速度の更新
        self.position = angle * string_length
        self.velocity = angular_velocity * string_length
        
        # SSD自然減衰
        neutral_pressure = HumanPressure()  # デフォルトは0
        self.agent.step(neutral_pressure, dt=dt)
    
    def get_stats(self) -> dict:
        """統計情報"""
        return {
            'position': self.position,
            'velocity': self.velocity,
            'E': self.agent.state.E.copy(),
            'kappa': self.agent.state.kappa.copy(),
            'collision_count': self.collision_count,
            'damping_factor': self.damping_factor
        }


class NewtonsCradleFull:
    """
    ニュートンのゆりかご - SSDフル版
    
    【物理シミュレーション】
    - 運動量保存則
    - エネルギー保存則（減衰あり）
    - 振り子の運動
    
    【SSD統合】
    - 衝突による意味圧
    - E蓄積による減衰（疲労）
    - κによる慣性学習
    """
    
    def __init__(self, n_balls: int = 5, string_length: float = 2.0, 
                 initial_release_angle: float = 30.0):
        self.n_balls = n_balls
        self.string_length = string_length
        self.gravity = 9.8
        
        # 球の初期化
        self.balls: List[Ball] = []
        spacing = 1.0  # 球の間隔
        
        for i in range(n_balls):
            initial_pos = (i - n_balls/2) * spacing
            ball = Ball(ball_id=i, initial_position=initial_pos)
            self.balls.append(ball)
        
        # 初期条件: 最初の球を持ち上げる
        release_angle_rad = np.radians(initial_release_angle)
        self.balls[0].position = release_angle_rad * string_length
        
        # シミュレーション状態
        self.current_time = 0.0
        self.history = []
    
    def detect_collisions(self) -> List[Tuple[int, int]]:
        """
        衝突検出
        
        Returns:
            衝突ペアのリスト [(ball1_id, ball2_id), ...]
        """
        collisions = []
        
        for i in range(self.n_balls - 1):
            ball1 = self.balls[i]
            ball2 = self.balls[i + 1]
            
            # 位置の差
            distance = abs(ball2.position - ball1.position)
            
            # 衝突判定（半径の和以下）
            if distance <= (ball1.radius + ball2.radius) * 1.01:
                # 相対速度（接近中のみ）
                relative_velocity = ball1.velocity - ball2.velocity
                if (ball1.position < ball2.position and relative_velocity > 0) or \
                   (ball1.position > ball2.position and relative_velocity < 0):
                    collisions.append((i, i+1))
        
        return collisions
    
    def resolve_collision(self, ball1_id: int, ball2_id: int):
        """
        衝突を解決（運動量保存則）
        
        Args:
            ball1_id: 球1のID
            ball2_id: 球2のID
        """
        ball1 = self.balls[ball1_id]
        ball2 = self.balls[ball2_id]
        
        # 質量
        m1 = ball1.mass
        m2 = ball2.mass
        
        # 衝突前の速度
        v1 = ball1.velocity
        v2 = ball2.velocity
        
        # 完全弾性衝突（運動量保存 + エネルギー保存）
        v1_new = ((m1 - m2) * v1 + 2 * m2 * v2) / (m1 + m2)
        v2_new = ((m2 - m1) * v2 + 2 * m1 * v1) / (m1 + m2)
        
        # SSD主観: 衝突を経験
        ball1.apply_impact(v1_new, self.current_time)
        ball2.apply_impact(v2_new, self.current_time)
    
    def step(self, dt: float = 0.001):
        """
        1ステップ進める
        
        Args:
            dt: 時間刻み
        """
        # 物理更新
        for ball in self.balls:
            ball.update_physics(dt, self.gravity, self.string_length)
        
        # 衝突検出と解決
        collisions = self.detect_collisions()
        for ball1_id, ball2_id in collisions:
            self.resolve_collision(ball1_id, ball2_id)
        
        # 時刻更新
        self.current_time += dt
        
        # 履歴記録
        if len(self.history) % 10 == 0:  # 10ステップごと
            snapshot = {
                'time': self.current_time,
                'positions': [b.position for b in self.balls],
                'velocities': [b.velocity for b in self.balls],
                'E_means': [np.mean(b.agent.state.E) for b in self.balls],
                'damping': [b.damping_factor for b in self.balls]
            }
            self.history.append(snapshot)
    
    def simulate(self, duration: float = 10.0, dt: float = 0.001):
        """
        シミュレーション実行
        
        Args:
            duration: 実行時間（秒）
            dt: 時間刻み
        """
        steps = int(duration / dt)
        
        print(f"シミュレーション開始: {duration}秒, {steps}ステップ")
        
        for step_num in range(steps):
            self.step(dt)
            
            if step_num % 10000 == 0:
                print(f"  進行: {self.current_time:.2f}秒 / {duration}秒")
        
        print("シミュレーション完了")
    
    def plot_results(self):
        """結果を可視化"""
        if not self.history:
            print("履歴データがありません")
            return
        
        times = [h['time'] for h in self.history]
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # 1. 位置の時系列
        ax1 = axes[0]
        for i in range(self.n_balls):
            positions = [h['positions'][i] for h in self.history]
            ax1.plot(times, positions, label=f'Ball {i}', linewidth=1)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Position (m)')
        ax1.set_title("Newton's Cradle - Positions (SSD Full Version)")
        ax1.legend(loc='upper right', fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # 2. E蓄積（疲労）
        ax2 = axes[1]
        for i in range(self.n_balls):
            E_means = [h['E_means'][i] for h in self.history]
            ax2.plot(times, E_means, label=f'Ball {i}', linewidth=1)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('E (Accumulated Stress)')
        ax2.set_title('SSD: E Accumulation (Fatigue)')
        ax2.legend(loc='upper right', fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # 3. 減衰率
        ax3 = axes[2]
        for i in range(self.n_balls):
            damping = [h['damping'][i] for h in self.history]
            ax3.plot(times, damping, label=f'Ball {i}', linewidth=1)
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Damping Factor')
        ax3.set_title('SSD: Energy Dissipation by E Accumulation')
        ax3.legend(loc='upper right', fontsize=8)
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def print_stats(self):
        """統計情報を表示"""
        print("\n" + "="*70)
        print("最終統計")
        print("="*70)
        
        for ball in self.balls:
            stats = ball.get_stats()
            print(f"\nBall {ball.ball_id}:")
            print(f"  位置: {stats['position']:.3f} m")
            print(f"  速度: {stats['velocity']:.3f} m/s")
            print(f"  衝突回数: {stats['collision_count']}回")
            print(f"  E蓄積: {np.mean(stats['E']):.4f}")
            print(f"  κ平均: {np.mean(stats['kappa']):.4f}")
            print(f"  減衰率: {stats['damping_factor']:.4f}")


def demo_full():
    """フル版デモ"""
    print("="*70)
    print("ニュートンのゆりかご - SSDフル版")
    print("="*70)
    print("\n【特徴】")
    print("- 完全な物理シミュレーション（運動量保存、振り子運動）")
    print("- SSDコアエンジン統合（各球が主観を持つ）")
    print("- 衝突 -> 意味圧 -> E蓄積 -> 減衰（疲労）")
    print("- κによる慣性学習")
    print()
    
    # ゆりかご作成
    cradle = NewtonsCradleFull(
        n_balls=5,
        string_length=2.0,
        initial_release_angle=30.0
    )
    
    # シミュレーション実行
    cradle.simulate(duration=10.0, dt=0.001)
    
    # 統計表示
    cradle.print_stats()
    
    # 可視化
    print("\n可視化を生成中...")
    cradle.plot_results()
    
    print("\n" + "="*70)
    print("デモ完了")
    print("="*70)


if __name__ == "__main__":
    demo_full()
