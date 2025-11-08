"""
SSD理論 対称vs非対称 圧倒的デモンストレーション

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    物理の対称性 vs 言語の非対称性
    同じ数式フレームで炙り出す...圧倒的差分！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【核心】
物理: 作用=反作用（対称）→ 双方が同じ圧を受ける...!
言語: 受け手の構造で強度が決まる（非対称）→ 片方だけが...限界を超える...!

【二段階反応】
t=0.0s  : 基層トリガ（心拍↑・怒り）
t=0.3s~ : 中核/上層が再評価（間に合えば...暴発回避...!）

【跳躍】
E（未処理圧）が Θ（限界）を超えると...
物理: 破壊...!
言語: 暴発・沈黙・離脱...!
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from dataclasses import dataclass
from typing import Tuple, List
import japanize_matplotlib  # 日本語フォント対応

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エージェント定義（物理/言語共通基盤）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class Agent:
    """
    圧倒的...エージェント...!
    
    物理系でも言語系でも使える統一モデル
    """
    name: str
    kappa: float = 1.0      # 整合慣性（慣れ/習熟）
    R: float = 0.5          # 動きにくさ（抵抗）
    E: float = 0.0          # 未処理圧（モヤつき/熱）
    Theta: float = 100.0    # 跳躍閾値（限界）
    G0: float = 0.5         # 基準剛性
    g: float = 0.3          # 剛性増分
    alpha: float = 0.5      # エネルギー変換効率
    beta: float = 0.1       # 減衰率
    h0: float = 0.01        # 基準跳躍率
    gamma: float = 10.0     # 跳躍感度
    
    # 履歴
    E_history: List[float] = None
    j_history: List[float] = None
    p_history: List[float] = None
    jump_prob_history: List[float] = None
    jumped: bool = False
    jump_time: float = -1
    
    def __post_init__(self):
        if self.E_history is None:
            self.E_history = []
        if self.j_history is None:
            self.j_history = []
        if self.p_history is None:
            self.p_history = []
        if self.jump_prob_history is None:
            self.jump_prob_history = []
    
    def calculate_coherence_flow(self, p: float) -> float:
        """
        整合流 j の計算（オーム則アナロジー）
        
        j = (G0 + g·κ) · p / (1 + R)
        
        圧倒的...整合...!
        構造が強ければ（κ大）、同じ圧でも大きく流せる...!
        """
        G = self.G0 + self.g * self.kappa
        j = G * p / (1.0 + self.R)
        return j
    
    def update_energy(self, p: float, dt: float) -> Tuple[float, float]:
        """
        未処理圧 E の更新
        
        dE/dt = α·[|p| - |j|]_+ - β·E
        
        処理しきれない分が...モヤつきとして蓄積...!
        """
        j = self.calculate_coherence_flow(p)
        
        # 未処理分（正の部分のみ）
        unprocessed = max(0, abs(p) - abs(j))
        
        # エネルギー変化
        dE = self.alpha * unprocessed - self.beta * self.E
        self.E += dE * dt
        self.E = max(0, self.E)  # 負値防止
        
        # 履歴記録
        self.E_history.append(self.E)
        self.j_history.append(j)
        self.p_history.append(p)
        
        return j, self.E
    
    def calculate_jump_probability(self, dt: float) -> float:
        """
        跳躍確率の計算
        
        h = h0·exp((E - Θ)/γ)
        P_jump(Δt) = 1 - exp(-h·Δt)
        
        限界を超えると...指数関数的に暴発リスクが...!
        """
        h = self.h0 * np.exp((self.E - self.Theta) / self.gamma)
        P_jump = 1.0 - np.exp(-h * dt)
        
        self.jump_prob_history.append(P_jump)
        
        return P_jump
    
    def attempt_jump(self, dt: float, t: float) -> bool:
        """
        跳躍試行
        
        返り値: True=跳躍発生
        """
        if self.jumped:
            return False
        
        P_jump = self.calculate_jump_probability(dt)
        
        if np.random.random() < P_jump:
            self.jumped = True
            self.jump_time = t
            return True
        
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 物理的相互作用（対称）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PhysicalInteraction:
    """
    圧倒的...対称性...!
    
    作用 = 反作用
    鉄球Aが鉄球Bを押す力 = 鉄球Bが鉄球Aを押し返す力
    """
    
    @staticmethod
    def calculate_pressure(F: float) -> Tuple[float, float]:
        """
        物理的圧力（完全対称）
        
        返り値: (p_A, p_B)
        
        圧倒的...ニュートン第三法則...!
        """
        return F, F  # 完全に等しい


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 言語的相互作用（非対称）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LanguageInteraction:
    """
    圧倒的...非対称性...!
    
    同じ言葉でも...
    受け手の構造（関係性・価値観）で強度が変わる...!
    """
    
    # 言葉の基本強度
    WORD_INTENSITY = {
        "バカ": 5.0,
        "死ね": 20.0,
        "クズ": 15.0,
        "最高": -10.0,  # 正の言葉は負の圧力（癒し）
    }
    
    @staticmethod
    def calculate_structure_sensitivity(
        sender_name: str,
        receiver: Agent,
        relationship: str = "neutral"
    ) -> float:
        """
        受け手の構造感度 s
        
        関係性によって同じ言葉でも重みが変わる...!
        
        Parameters:
        -----------
        relationship: str
            "friend" : 友人（冗談として受け流せる）→ s=0.2
            "neutral": 中立（普通に受け取る）→ s=1.0
            "boss"   : 上司（パワハラとして重く受け取る）→ s=2.0
            "enemy"  : 敵（戦闘状態）→ s=1.5
        """
        sensitivity_map = {
            "friend": 0.2,   # 圧倒的...冗談解釈...!
            "neutral": 1.0,
            "boss": 2.0,     # 圧倒的...パワハラ...!
            "enemy": 1.5,
        }
        
        return sensitivity_map.get(relationship, 1.0)
    
    @staticmethod
    def calculate_pressure(
        word: str,
        sender_name: str,
        receiver: Agent,
        relationship: str = "neutral"
    ) -> float:
        """
        言語的圧力（非対称）
        
        p = g(word) × s(receiver, relationship)
        
        圧倒的...構造依存性...!
        """
        g = LanguageInteraction.WORD_INTENSITY.get(word, 0.0)
        s = LanguageInteraction.calculate_structure_sensitivity(
            sender_name, receiver, relationship
        )
        
        return g * s


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 二段階反応モデル（言語専用）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TwoStageResponse:
    """
    圧倒的...二段階反応...!
    
    第1段階（t=0.0s）: 基層トリガ（即座に E↑、心拍↑）
    第2段階（t=0.3s~）: 中核/上層が再評価（R↑で j抑制可能）
    
    間に合えば...暴発回避...!
    間に合わなければ...限界突破...!
    """
    
    T_IMMEDIATE = 0.0      # 即時反応
    T_REAPPRAISAL = 0.3    # 再評価開始時刻（秒）
    
    @staticmethod
    def apply_reappraisal(agent: Agent, t: float):
        """
        再評価の適用
        
        t >= 0.3s で R（抵抗）を増やし、整合流を抑制
        → E の蓄積速度が下がる
        
        圧倒的...自制...!
        """
        if t >= TwoStageResponse.T_REAPPRAISAL and not agent.jumped:
            # 抵抗を2倍に（冷静になる）
            agent.R = min(agent.R * 1.5, 5.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# シミュレーション実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_physical_trial(duration: float = 5.0, dt: float = 0.01):
    """
    物理トライアル: 鉄球 vs 風船
    
    圧倒的...対称性...!
    双方が同じ圧を受けるが...
    Θ（限界）の違いで結果が変わる...!
    """
    print("\n" + "="*60)
    print("物理トライアル: 鉄球の衝突")
    print("="*60)
    
    # エージェント設定
    steel_ball = Agent(
        name="鉄球",
        kappa=2.0,      # 高剛性
        R=0.3,          # 低抵抗
        Theta=200.0,    # 高い限界（壊れにくい）
        G0=1.0,
        g=0.5
    )
    
    balloon = Agent(
        name="風船",
        kappa=0.5,      # 低剛性
        R=0.1,          # 極低抵抗
        Theta=50.0,     # 低い限界（すぐ割れる）
        G0=0.3,
        g=0.2
    )
    
    # 物理力（対称）
    F = 30.0  # 衝突力
    
    print(f"\n衝突力 F = {F} N（ニュートン）")
    print(f"作用 = 反作用（完全対称）\n")
    
    # シミュレーション
    t = 0.0
    time_points = []
    
    while t < duration:
        # 対称的圧力
        p_steel, p_balloon = PhysicalInteraction.calculate_pressure(F)
        
        # エネルギー更新
        steel_ball.update_energy(p_steel, dt)
        balloon.update_energy(p_balloon, dt)
        
        # 跳躍試行
        if steel_ball.attempt_jump(dt, t):
            print(f"⚠️  t={t:.2f}s: 鉄球が破壊...!")
        
        if balloon.attempt_jump(dt, t):
            print(f"💥 t={t:.2f}s: 風船が破裂...!")
        
        time_points.append(t)
        t += dt
    
    print(f"\n最終状態:")
    print(f"  鉄球: E={steel_ball.E:.2f}, 跳躍={'発生' if steel_ball.jumped else '未発生'}")
    print(f"  風船: E={balloon.E:.2f}, 跳躍={'発生' if balloon.jumped else '未発生'}")
    
    return steel_ball, balloon, np.array(time_points)


def run_language_trial(duration: float = 5.0, dt: float = 0.01):
    """
    言語トライアル: 友人の「バカ」vs 上司の「バカ」
    
    圧倒的...非対称性...!
    同じ言葉でも...
    受け手の構造で強度が変わる...!
    """
    print("\n" + "="*60)
    print("言語トライアル: 「バカ」という言葉")
    print("="*60)
    
    # エージェント設定
    person_with_friend = Agent(
        name="友人に言われた人",
        kappa=1.5,
        R=0.5,
        Theta=100.0,
        h0=0.005
    )
    
    person_with_boss = Agent(
        name="上司に言われた人",
        kappa=1.0,
        R=0.8,          # 初期抵抗（やや高め）
        Theta=80.0,     # やや低い限界（ストレス蓄積）
        h0=0.01
    )
    
    # 言語的圧力（非対称）
    word = "バカ"
    
    p_friend = LanguageInteraction.calculate_pressure(
        word, "友人", person_with_friend, "friend"
    )
    
    p_boss = LanguageInteraction.calculate_pressure(
        word, "上司", person_with_boss, "boss"
    )
    
    print(f"\n同じ言葉「{word}」でも...")
    print(f"  友人からの圧力: {p_friend:.2f}（冗談として軽く受け取る）")
    print(f"  上司からの圧力: {p_boss:.2f}（パワハラとして重く受け取る）")
    print(f"\n圧倒的...非対称性...!\n")
    
    # シミュレーション
    t = 0.0
    time_points = []
    
    # 言葉を浴びせるタイミング（最初の1秒間）
    apply_pressure = True
    
    while t < duration:
        # 圧力適用（最初の1秒のみ）
        if t > 1.0:
            apply_pressure = False
        
        current_p_friend = p_friend if apply_pressure else 0.0
        current_p_boss = p_boss if apply_pressure else 0.0
        
        # 二段階反応（上司ケースのみ）
        TwoStageResponse.apply_reappraisal(person_with_boss, t)
        
        # エネルギー更新
        person_with_friend.update_energy(current_p_friend, dt)
        person_with_boss.update_energy(current_p_boss, dt)
        
        # 跳躍試行
        if person_with_friend.attempt_jump(dt, t):
            print(f"😄 t={t:.2f}s: 友人ケース - 跳躍（笑い返す）")
        
        if person_with_boss.attempt_jump(dt, t):
            if t < TwoStageResponse.T_REAPPRAISAL:
                print(f"💢 t={t:.2f}s: 上司ケース - 即座に暴発...!")
            else:
                print(f"😤 t={t:.2f}s: 上司ケース - 再評価後も限界突破（沈黙/離脱）...!")
        
        time_points.append(t)
        t += dt
    
    print(f"\n最終状態:")
    print(f"  友人ケース: E={person_with_friend.E:.2f}, 跳躍={'発生' if person_with_friend.jumped else '未発生'}")
    print(f"  上司ケース: E={person_with_boss.E:.2f}, 跳躍={'発生' if person_with_boss.jumped else '未発生'}")
    
    if person_with_boss.jumped and person_with_boss.jump_time < TwoStageResponse.T_REAPPRAISAL:
        print(f"\n⚠️  再評価が間に合わず...即座に限界突破...!")
    elif person_with_boss.jumped:
        print(f"\n再評価しても...限界を超えた...!")
    
    return person_with_friend, person_with_boss, np.array(time_points)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 圧倒的...可視化...!
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def visualize_comparison(
    physical_agents: Tuple[Agent, Agent],
    language_agents: Tuple[Agent, Agent],
    time_points: np.ndarray
):
    """
    対称 vs 非対称の圧倒的比較可視化
    
    3×2グリッド:
    - 左列: 物理トライアル（対称）
    - 右列: 言語トライアル（非対称）
    - 上段: p と j の時系列
    - 中段: E vs Θ
    - 下段: P_jump の推移
    """
    steel, balloon = physical_agents
    friend_case, boss_case = language_agents
    
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.25)
    
    # スタイル設定
    plt.rcParams['font.size'] = 11
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 左列: 物理トライアル
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # [0, 0] p と j の時系列
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(time_points, steel.p_history, 'r-', linewidth=2, label='圧力 p（鉄球）', alpha=0.7)
    ax1.plot(time_points, steel.j_history, 'r--', linewidth=2, label='整合流 j（鉄球）')
    ax1.plot(time_points, balloon.p_history, 'b-', linewidth=2, label='圧力 p（風船）', alpha=0.7)
    ax1.plot(time_points, balloon.j_history, 'b--', linewidth=2, label='整合流 j（風船）')
    
    if steel.jumped:
        ax1.axvline(steel.jump_time, color='red', linestyle=':', linewidth=2, alpha=0.5)
        ax1.text(steel.jump_time, max(steel.p_history)*0.9, '鉄球破壊', 
                rotation=90, va='bottom', fontsize=10, color='red', fontweight='bold')
    
    if balloon.jumped:
        ax1.axvline(balloon.jump_time, color='blue', linestyle=':', linewidth=2, alpha=0.5)
        ax1.text(balloon.jump_time, max(balloon.p_history)*0.9, '風船破裂', 
                rotation=90, va='bottom', fontsize=10, color='blue', fontweight='bold')
    
    ax1.set_title('【物理】圧力と整合流（対称）', fontsize=14, fontweight='bold')
    ax1.set_xlabel('時間 [s]')
    ax1.set_ylabel('圧力 / 整合流')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, time_points[-1])
    
    # [1, 0] E vs Θ
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(time_points, steel.E_history, 'r-', linewidth=2.5, label='E（鉄球）')
    ax2.plot(time_points, balloon.E_history, 'b-', linewidth=2.5, label='E（風船）')
    ax2.axhline(steel.Theta, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label=f'Θ（鉄球）={steel.Theta}')
    ax2.axhline(balloon.Theta, color='blue', linestyle='--', linewidth=1.5, alpha=0.5, label=f'Θ（風船）={balloon.Theta}')
    
    if steel.jumped:
        ax2.axvline(steel.jump_time, color='red', linestyle=':', linewidth=2, alpha=0.5)
    if balloon.jumped:
        ax2.axvline(balloon.jump_time, color='blue', linestyle=':', linewidth=2, alpha=0.5)
    
    ax2.set_title('【物理】未処理圧 E vs 限界 Θ', fontsize=14, fontweight='bold')
    ax2.set_xlabel('時間 [s]')
    ax2.set_ylabel('未処理圧 E')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, time_points[-1])
    
    # [2, 0] P_jump の推移
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.plot(time_points, steel.jump_prob_history, 'r-', linewidth=2.5, label='P_jump（鉄球）')
    ax3.plot(time_points, balloon.jump_prob_history, 'b-', linewidth=2.5, label='P_jump（風船）')
    
    if steel.jumped:
        ax3.axvline(steel.jump_time, color='red', linestyle=':', linewidth=2, alpha=0.5)
    if balloon.jumped:
        ax3.axvline(balloon.jump_time, color='blue', linestyle=':', linewidth=2, alpha=0.5)
    
    ax3.set_title('【物理】跳躍確率の推移', fontsize=14, fontweight='bold')
    ax3.set_xlabel('時間 [s]')
    ax3.set_ylabel('跳躍確率 P_jump')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, time_points[-1])
    ax3.set_ylim(0, 1.0)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 右列: 言語トライアル
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # [0, 1] p と j の時系列
    ax4 = fig.add_subplot(gs[0, 1])
    ax4.plot(time_points, friend_case.p_history, 'g-', linewidth=2, label='圧力 p（友人）', alpha=0.7)
    ax4.plot(time_points, friend_case.j_history, 'g--', linewidth=2, label='整合流 j（友人）')
    ax4.plot(time_points, boss_case.p_history, 'm-', linewidth=2, label='圧力 p（上司）', alpha=0.7)
    ax4.plot(time_points, boss_case.j_history, 'm--', linewidth=2, label='整合流 j（上司）')
    
    # 二段階反応のマーカー
    ax4.axvline(TwoStageResponse.T_REAPPRAISAL, color='orange', linestyle=':', 
               linewidth=2, alpha=0.7, label='再評価開始')
    
    if friend_case.jumped:
        ax4.axvline(friend_case.jump_time, color='green', linestyle=':', linewidth=2, alpha=0.5)
        ax4.text(friend_case.jump_time, max(friend_case.p_history)*0.9, '笑い返す', 
                rotation=90, va='bottom', fontsize=10, color='green', fontweight='bold')
    
    if boss_case.jumped:
        ax4.axvline(boss_case.jump_time, color='magenta', linestyle=':', linewidth=2, alpha=0.5)
        jump_label = '即座に暴発' if boss_case.jump_time < TwoStageResponse.T_REAPPRAISAL else '限界突破'
        ax4.text(boss_case.jump_time, max(boss_case.p_history)*0.9, jump_label, 
                rotation=90, va='bottom', fontsize=10, color='magenta', fontweight='bold')
    
    ax4.set_title('【言語】圧力と整合流（非対称）', fontsize=14, fontweight='bold')
    ax4.set_xlabel('時間 [s]')
    ax4.set_ylabel('圧力 / 整合流')
    ax4.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, time_points[-1])
    
    # [1, 1] E vs Θ
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.plot(time_points, friend_case.E_history, 'g-', linewidth=2.5, label='E（友人）')
    ax5.plot(time_points, boss_case.E_history, 'm-', linewidth=2.5, label='E（上司）')
    ax5.axhline(friend_case.Theta, color='green', linestyle='--', linewidth=1.5, alpha=0.5, 
               label=f'Θ（友人）={friend_case.Theta}')
    ax5.axhline(boss_case.Theta, color='magenta', linestyle='--', linewidth=1.5, alpha=0.5, 
               label=f'Θ（上司）={boss_case.Theta}')
    
    ax5.axvline(TwoStageResponse.T_REAPPRAISAL, color='orange', linestyle=':', 
               linewidth=2, alpha=0.7)
    
    if friend_case.jumped:
        ax5.axvline(friend_case.jump_time, color='green', linestyle=':', linewidth=2, alpha=0.5)
    if boss_case.jumped:
        ax5.axvline(boss_case.jump_time, color='magenta', linestyle=':', linewidth=2, alpha=0.5)
    
    ax5.set_title('【言語】未処理圧 E vs 限界 Θ', fontsize=14, fontweight='bold')
    ax5.set_xlabel('時間 [s]')
    ax5.set_ylabel('未処理圧 E')
    ax5.legend(loc='upper right')
    ax5.grid(True, alpha=0.3)
    ax5.set_xlim(0, time_points[-1])
    
    # [2, 1] P_jump の推移
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.plot(time_points, friend_case.jump_prob_history, 'g-', linewidth=2.5, label='P_jump（友人）')
    ax6.plot(time_points, boss_case.jump_prob_history, 'm-', linewidth=2.5, label='P_jump（上司）')
    
    ax6.axvline(TwoStageResponse.T_REAPPRAISAL, color='orange', linestyle=':', 
               linewidth=2, alpha=0.7)
    
    if friend_case.jumped:
        ax6.axvline(friend_case.jump_time, color='green', linestyle=':', linewidth=2, alpha=0.5)
    if boss_case.jumped:
        ax6.axvline(boss_case.jump_time, color='magenta', linestyle=':', linewidth=2, alpha=0.5)
    
    ax6.set_title('【言語】跳躍確率の推移', fontsize=14, fontweight='bold')
    ax6.set_xlabel('時間 [s]')
    ax6.set_ylabel('跳躍確率 P_jump')
    ax6.legend(loc='upper right')
    ax6.grid(True, alpha=0.3)
    ax6.set_xlim(0, time_points[-1])
    ax6.set_ylim(0, 1.0)
    
    # 全体タイトル
    fig.suptitle('SSD理論: 対称vs非対称 圧倒的比較デモ', 
                fontsize=18, fontweight='bold', y=0.98)
    
    plt.savefig('ssd_symmetric_asymmetric_demo.png', dpi=150, bbox_inches='tight')
    print("\n💾 グラフ保存: ssd_symmetric_asymmetric_demo.png")
    
    plt.show()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SSD理論 対称vs非対称 圧倒的デモンストレーション")
    print("="*60)
    print("\n同じ数式フレームで...")
    print("  物理: 対称（作用=反作用）")
    print("  言語: 非対称（受け手の構造で決まる）")
    print("\nこの差を...炙り出す...!")
    
    # 物理トライアル実行
    np.random.seed(42)  # 再現性
    steel, balloon, time_physical = run_physical_trial(duration=5.0, dt=0.01)
    
    # 言語トライアル実行
    np.random.seed(43)
    friend_case, boss_case, time_language = run_language_trial(duration=5.0, dt=0.01)
    
    # 圧倒的可視化
    visualize_comparison(
        (steel, balloon),
        (friend_case, boss_case),
        time_physical  # 両方同じ時間軸
    )
    
    print("\n" + "="*60)
    print("圧倒的...完了...!")
    print("="*60)
    print("\n【結論】")
    print("物理: 対称性により双方が同等の圧を受ける")
    print("     → 限界（Θ）の差で破壊タイミングが決まる")
    print("\n言語: 非対称性により受け手の構造で圧が変わる")
    print("     → 同じ言葉でも関係性次第で全く異なる結果")
    print("\n二段階反応（言語）:")
    print("     → 再評価が間に合えば暴発回避可能")
    print("     → 間に合わなければ即座に限界突破")
    print("\n圧倒的...理論の力...!")
