"""
SSD v3.0 統一フレームワーク実演: 太郎と次郎の物語

シナリオ:
1. 太郎が次郎に「禿」と言う (間接作用 - 意味圧)
2. 次郎はそれを解釈して怒る (間接作用でE_indirect蓄積)
3. 次郎は太郎に向かって突進 (E_indirectが運動エネルギーに変換)
4. 次郎が太郎にぶつかる (直接作用 - 物理的衝突)
5. 太郎は物理エネルギーで動かされる (直接作用のエネルギー伝達)

これは「間接作用→直接作用」の変換プロセスを示す
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from ssd_core_engine_v3_5 import SSDCoreEngineV3_5, SSDParametersV3_5, SSDStateV3_5, SSDDomain
from dataclasses import dataclass
from typing import List


@dataclass
class IronBall:
    """鉄球 (太郎 or 次郎)"""
    name: str
    position: float  # 1D位置 [m]
    velocity: float  # 速度 [m/s]
    mass: float      # 質量 [kg]
    radius: float    # 半径 [m]
    
    # SSD状態
    state: SSDStateV3_5
    engine: SSDCoreEngineV3_5
    
    # 心理状態
    anger_level: float = 0.0  # 怒りレベル (0-10)
    is_angry: bool = False
    
    def __post_init__(self):
        """初期化後処理"""
        self.state.kappa = self.mass  # 質量を構造整合性に反映


class TaroJiroSimulation:
    """太郎と次郎のシミュレーション"""
    
    def __init__(self):
        self.time = 0.0
        self.g = 9.8
        
        # Phase tracking
        self.phase = "waiting"  # waiting, insult, angry, charging, collision, aftermath
        self.phase_time = 0.0
        
        # SSD parameters - MIXED MODE (直接 + 間接)
        self.params_indirect = SSDParametersV3_5(
            # 間接作用モード (言葉を受け取る)
            use_direct_action=False,
            use_indirect_action=True,
            amplification_factor=30.0,  # 言葉の増幅効果
            
            G0=0.8,
            g=1.0,
            alpha=2.0,      # 意味圧の蓄積率
            beta_decay=0.1, # ゆっくり減衰
            gamma_i2d=0.01,  # v3.5: indirect→direct変換率
            gamma_d2i=0.05,  # v3.5: direct→indirect変換率
        )
        
        self.params_direct = SSDParametersV3_5(
            # 直接作用モード (物理的衝突)
            use_direct_action=True,
            use_indirect_action=False,
            amplification_factor=1.0,
            
            G0=0.5,
            g=0.3,
            alpha=0.1,
            beta_decay=0.5,
            gamma_i2d=0.0,  # v3.5: 物理系では変換なし
            gamma_d2i=0.0,  # v3.5: 物理系では変換なし
        )
        
        # 太郎 (右側、挑発者)
        state_taro = SSDStateV3_5(kappa=1.0, E_direct=0.0, E_indirect=0.0)
        engine_taro = SSDCoreEngineV3_5(self.params_direct)
        engine_taro.domain = SSDDomain.PHYSICS
        
        self.taro = IronBall(
            name="太郎",
            position=3.0,   # 右側
            velocity=0.0,
            mass=1.0,
            radius=0.2,
            state=state_taro,
            engine=engine_taro
        )
        
        # 次郎 (左側、被害者→加害者)
        state_jiro = SSDStateV3_5(kappa=1.0, E_direct=0.0, E_indirect=0.0)
        engine_jiro = SSDCoreEngineV3_5(self.params_indirect)  # 最初は間接作用
        engine_jiro.domain = SSDDomain.SOCIAL
        
        self.jiro = IronBall(
            name="次郎",
            position=1.0,   # 左側
            velocity=0.0,
            mass=1.0,
            radius=0.2,
            state=state_jiro,
            engine=engine_jiro
        )
        
        # Event log
        self.events = []
        
        # Data recording
        self.time_data = []
        self.taro_pos_data = []
        self.jiro_pos_data = []
        self.taro_vel_data = []
        self.jiro_vel_data = []
        self.jiro_anger_data = []
        self.jiro_E_indirect_data = []
        self.phase_data = []
        
    def log_event(self, message: str):
        """イベントログ"""
        self.events.append(f"t={self.time:.2f}s: {message}")
        print(f"  {message}")
    
    def detect_collision(self) -> bool:
        """衝突検出"""
        distance = abs(self.taro.position - self.jiro.position)
        return distance <= (self.taro.radius + self.jiro.radius)
    
    def step(self, dt: float):
        """1ステップ実行"""
        
        # Phase 1: Waiting (0-1s)
        if self.phase == "waiting":
            if self.time >= 1.0:
                self.phase = "insult"
                self.phase_time = 0.0
                self.log_event(f"💬 {self.taro.name}: 「おい{self.jiro.name}、禿げてるな」")
        
        # Phase 2: Insult - 間接作用 (1-2s)
        elif self.phase == "insult":
            # 太郎の言葉 → 次郎への意味圧
            insult_pressure = np.array([5.0, 0.0, 0.0])  # 強い侮辱
            
            # 次郎が言葉を受け取る (間接作用)
            self.jiro.state = self.jiro.engine.step(
                self.jiro.state,
                p_external=insult_pressure,
                dt=dt
            )
            
            # 怒りレベルの更新
            self.jiro.anger_level = self.jiro.state.E_indirect * 2.0
            
            if self.jiro.anger_level > 5.0 and not self.jiro.is_angry:
                self.jiro.is_angry = True
                self.log_event(f"😡 {self.jiro.name}: 怒りが臨界点を突破! (anger={self.jiro.anger_level:.1f})")
            
            # 十分怒ったら突進開始
            if self.phase_time > 1.0 and self.jiro.is_angry:
                # E_indirect → 運動エネルギーに変換
                kinetic_energy = self.jiro.state.E_indirect * 0.5  # 50%を運動に変換
                self.jiro.velocity = np.sqrt(2 * kinetic_energy / self.jiro.mass)
                
                self.phase = "charging"
                self.phase_time = 0.0
                self.log_event(f"💨 {self.jiro.name}: 「許さん!」と突進開始 (v={self.jiro.velocity:.2f}m/s)")
                self.log_event(f"   E_indirect={self.jiro.state.E_indirect:.3f}J → KE={kinetic_energy:.3f}J に変換")
                
                # エンジンを直接作用モードに切り替え
                self.jiro.engine = SSDCoreEngineV3_5(self.params_direct)
                self.jiro.engine.domain = SSDDomain.PHYSICS
        
        # Phase 3: Charging - 次郎が突進 (2-3s)
        elif self.phase == "charging":
            # 次郎が移動
            self.jiro.position += self.jiro.velocity * dt
            
            # 衝突検出
            if self.detect_collision():
                self.phase = "collision"
                self.phase_time = 0.0
                
                # 衝突時のエネルギー
                jiro_KE = 0.5 * self.jiro.mass * self.jiro.velocity ** 2
                self.log_event(f"💥 衝突! {self.jiro.name} → {self.taro.name}")
                self.log_event(f"   {self.jiro.name}の運動エネルギー: {jiro_KE:.3f}J")
                
                # 直接作用: 運動量保存則による衝突
                # 完全弾性衝突 (質量同じ → 速度交換)
                v1_before = self.jiro.velocity
                v2_before = self.taro.velocity
                
                self.jiro.velocity = v2_before
                self.taro.velocity = v1_before
                
                self.log_event(f"   直接作用: 運動量保存則により速度交換")
                self.log_event(f"   {self.taro.name}の新速度: {self.taro.velocity:.2f}m/s")
                
                # 太郎のSSDに物理的圧力
                contact_force = 1000.0 * abs(v1_before)  # 衝撃力
                contact_pressure = np.array([contact_force, 0.0, 0.0])
                
                self.taro.state = self.taro.engine.step(
                    self.taro.state,
                    p_external=np.zeros(3),
                    dt=dt,
                    contact_pressure=contact_pressure
                )
        
        # Phase 4: Aftermath - 衝突後 (3s~)
        elif self.phase == "collision":
            # 両者とも慣性で移動
            self.jiro.position += self.jiro.velocity * dt
            self.taro.position += self.taro.velocity * dt
            
            # 減速 (摩擦)
            friction = 0.98
            self.jiro.velocity *= friction
            self.taro.velocity *= friction
            
            if self.phase_time > 2.0:
                self.phase = "aftermath"
                self.log_event(f"✅ シミュレーション完了")
                self.log_event(f"   {self.taro.name}の最終位置: {self.taro.position:.2f}m")
                self.log_event(f"   {self.jiro.name}の最終位置: {self.jiro.position:.2f}m")
        
        # 境界条件
        self.jiro.position = max(0.0, min(5.0, self.jiro.position))
        self.taro.position = max(0.0, min(5.0, self.taro.position))
        
        # データ記録
        self.time_data.append(self.time)
        self.taro_pos_data.append(self.taro.position)
        self.jiro_pos_data.append(self.jiro.position)
        self.taro_vel_data.append(self.taro.velocity)
        self.jiro_vel_data.append(self.jiro.velocity)
        self.jiro_anger_data.append(self.jiro.anger_level)
        self.jiro_E_indirect_data.append(self.jiro.state.E_indirect)
        self.phase_data.append(self.phase)
        
        self.time += dt
        self.phase_time += dt
    
    def run(self, duration: float = 6.0, dt: float = 0.01):
        """シミュレーション実行"""
        print("\n" + "="*70)
        print("SSD v3.0 統一フレームワーク実演: 太郎と次郎")
        print("="*70)
        print("\n📖 シナリオ:")
        print("  1. 太郎が次郎に「禿」と言う (間接作用 - 意味圧)")
        print("  2. 次郎はそれを解釈して怒る (E_indirect蓄積)")
        print("  3. 次郎が突進 (E_indirect → 運動エネルギー)")
        print("  4. 衝突 (直接作用 - 運動量保存)")
        print("  5. 太郎は物理的に動かされる")
        print("\n⚙️  実行中...\n")
        
        steps = int(duration / dt)
        for _ in range(steps):
            self.step(dt)
        
        print("\n" + "="*70)
        print("📊 最終統計")
        print("="*70)
        print(f"\n{self.jiro.name}の怒り:")
        print(f"  最大怒りレベル: {max(self.jiro_anger_data):.2f}")
        print(f"  最大E_indirect: {max(self.jiro_E_indirect_data):.3f}J")
        print(f"\n運動:")
        print(f"  {self.jiro.name}の最大速度: {max(self.jiro_vel_data):.2f}m/s")
        print(f"  {self.taro.name}の最大速度: {max(self.taro_vel_data):.2f}m/s")
        print(f"  {self.taro.name}の移動距離: {abs(self.taro_pos_data[-1] - self.taro_pos_data[0]):.2f}m")
        
        print("\n🔬 エネルギー変換:")
        print(f"  間接作用 (言葉) → E_indirect: {max(self.jiro_E_indirect_data):.3f}J")
        print(f"  E_indirect → 運動エネルギー: ~{0.5 * self.jiro.mass * max(self.jiro_vel_data)**2:.3f}J")
        print(f"  直接作用 (衝突) → 太郎の運動: {0.5 * self.taro.mass * max(self.taro_vel_data)**2:.3f}J")
        
        self.visualize()
    
    def visualize(self):
        """結果の可視化"""
        fig, axes = plt.subplots(4, 1, figsize=(14, 12))
        
        # Phase color map
        phase_colors = {
            'waiting': 'gray',
            'insult': 'yellow',
            'charging': 'orange',
            'collision': 'red',
            'aftermath': 'blue'
        }
        
        # 1. 位置
        ax1 = axes[0]
        ax1.plot(self.time_data, self.jiro_pos_data, 'b-', linewidth=2, label='次郎 (被害者→加害者)')
        ax1.plot(self.time_data, self.taro_pos_data, 'r-', linewidth=2, label='太郎 (挑発者→被害者)')
        
        # Phase背景
        phase_starts = {}
        for i, (t, phase) in enumerate(zip(self.time_data, self.phase_data)):
            if phase not in phase_starts:
                phase_starts[phase] = t
            if i < len(self.time_data) - 1 and self.phase_data[i+1] != phase:
                ax1.axvspan(phase_starts[phase], self.time_data[i], 
                           alpha=0.2, color=phase_colors.get(phase, 'white'))
                phase_starts = {}
        
        ax1.set_xlabel('Time (s)', fontsize=11)
        ax1.set_ylabel('Position (m)', fontsize=11)
        ax1.set_title('太郎と次郎の位置', fontsize=12, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(-0.5, 5.5)
        
        # 2. 速度
        ax2 = axes[1]
        ax2.plot(self.time_data, self.jiro_vel_data, 'b-', linewidth=2, label='次郎')
        ax2.plot(self.time_data, self.taro_vel_data, 'r-', linewidth=2, label='太郎')
        ax2.axhline(0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
        ax2.set_xlabel('Time (s)', fontsize=11)
        ax2.set_ylabel('Velocity (m/s)', fontsize=11)
        ax2.set_title('速度 (直接作用による運動量伝達)', fontsize=12, fontweight='bold')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # 3. 次郎の怒り (間接作用)
        ax3 = axes[2]
        ax3.plot(self.time_data, self.jiro_anger_data, 'darkred', linewidth=2.5, label='怒りレベル')
        ax3.axhline(5.0, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='臨界点')
        ax3.fill_between(self.time_data, 0, self.jiro_anger_data, alpha=0.3, color='red')
        ax3.set_xlabel('Time (s)', fontsize=11)
        ax3.set_ylabel('Anger Level', fontsize=11)
        ax3.set_title('次郎の怒り (間接作用 - 意味圧の蓄積)', fontsize=12, fontweight='bold')
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)
        
        # 4. E_indirect (間接作用エネルギー)
        ax4 = axes[3]
        ax4.plot(self.time_data, self.jiro_E_indirect_data, 'purple', linewidth=2.5, label='E_indirect (次郎)')
        ax4.fill_between(self.time_data, 0, self.jiro_E_indirect_data, alpha=0.3, color='purple')
        
        # 変換ポイント
        if len(self.jiro_vel_data) > 0:
            charge_start = next((i for i, phase in enumerate(self.phase_data) if phase == 'charging'), None)
            if charge_start:
                ax4.axvline(self.time_data[charge_start], color='orange', linestyle='--', 
                           linewidth=2, alpha=0.7, label='E_indirect→運動エネルギー変換')
        
        ax4.set_xlabel('Time (s)', fontsize=11)
        ax4.set_ylabel('E_indirect (J)', fontsize=11)
        ax4.set_title('間接作用エネルギー (言葉が蓄積されたエネルギー)', fontsize=12, fontweight='bold')
        ax4.legend(loc='best')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('ssd_taro_jiro_demo.png', dpi=150, bbox_inches='tight')
        print("\n💾 グラフ保存: ssd_taro_jiro_demo.png")
        
        # Phase説明
        print("\n📈 Phase説明:")
        print("  灰色 (waiting):   開始前")
        print("  黄色 (insult):    太郎が「禿」と言う → 次郎が間接作用で怒り蓄積")
        print("  橙色 (charging):  次郎が突進 (E_indirect → 運動エネルギー)")
        print("  赤色 (collision): 衝突 (直接作用による運動量伝達)")
        print("  青色 (aftermath): 衝突後の慣性運動")
        
        plt.show()


if __name__ == "__main__":
    sim = TaroJiroSimulation()
    sim.run(duration=6.0, dt=0.01)
    
    print("\n" + "="*70)
    print("✅ デモ完了!")
    print("="*70)
    print("\n🎓 学んだこと:")
    print("  1. 間接作用 (言葉) は E_indirect に蓄積される")
    print("  2. E_indirect は運動エネルギーに変換可能")
    print("  3. 直接作用 (衝突) は運動量保存則に従う")
    print("  4. v3.0統一フレームワークで両方を扱える!")
    print("\n  「言葉が物理的影響を持つ」過程の完全な形式化")
    print("="*70)
