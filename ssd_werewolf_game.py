"""
SSD v3.5 統合デモ: 人狼ゲームAI (Werewolf/Mafia Game)

シナリオ:
--------
7人の村で人狼ゲームが開催される。
- 村人 (Villager): 4人
- 人狼 (Werewolf): 2人
- 占い師 (Seer): 1人

各プレイヤーはSSD v3.5 + 多次元意味圧で判断を行う。

多次元意味圧:
------------
1. 疑惑圧 (Suspicion Pressure): 自分への疑いの強さ
2. 信頼圧 (Trust Pressure): 他プレイヤーへの信頼度
3. 情報圧 (Information Pressure): 未確定情報の多さ
4. 時間圧 (Time Pressure): ゲーム進行度（残り日数）
5. 生存圧 (Survival Pressure): 残り人数のバランス

SSD連成:
--------
- E_indirect: 推理・情報・心理状態
- E_direct: 投票行動・発言の強さ
- 相転移: 疑惑が限界を超えると「暴露」や「強弁」

ゲームフロー:
-----------
昼フェーズ: 議論 → 投票 → 処刑
夜フェーズ: 人狼が襲撃 → 占い師が占い
"""

import numpy as np
import matplotlib.pyplot as plt
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ssd_core_engine_v3_5 import SSDCoreEngineV3_5, SSDParametersV3_5, SSDStateV3_5
from ssd_multidimensional_pressure import MultiDimensionalPressure


class Role(Enum):
    """役職"""
    VILLAGER = "村人"
    WEREWOLF = "人狼"
    SEER = "占い師"


class GamePhase(Enum):
    """ゲームフェーズ"""
    DAY_DISCUSSION = "昼_議論"
    DAY_VOTE = "昼_投票"
    NIGHT_WEREWOLF = "夜_人狼"
    NIGHT_SEER = "夜_占い"


@dataclass
class WerewolfPlayer:
    """人狼ゲームのプレイヤー"""
    id: int
    name: str
    role: Role
    
    # SSD状態
    state: SSDStateV3_5
    engine: SSDCoreEngineV3_5
    pressure_system: MultiDimensionalPressure
    
    # ゲーム状態
    is_alive: bool = True
    suspicion_level: float = 0.0  # 疑惑レベル (0-10)
    trust_map: Dict[int, float] = field(default_factory=dict)  # 他プレイヤーへの信頼度
    
    # 知識（占い師のみ）
    known_roles: Dict[int, Role] = field(default_factory=dict)
    
    # 統計
    vote_count: int = 0  # 投票された回数
    voted_for: List[int] = field(default_factory=list)  # 投票した相手の履歴


def create_werewolf_pressure() -> MultiDimensionalPressure:
    """人狼ゲーム用の多次元意味圧システム"""
    mdp = MultiDimensionalPressure()
    
    # 1. 疑惑圧力
    def suspicion_pressure(context: dict) -> float:
        suspicion = context.get('suspicion_level', 0.0)
        return min(1.0, suspicion / 10.0)
    
    mdp.register_dimension(
        "suspicion",
        suspicion_pressure,
        weight=0.35,
        description="自分への疑惑からの圧力"
    )
    
    # 2. 信頼圧力（信頼できる人が少ない = 高圧力）
    def trust_pressure(context: dict) -> float:
        trust_count = context.get('trusted_count', 0)
        total = context.get('alive_count', 1)
        return 1.0 - (trust_count / max(1, total))
    
    mdp.register_dimension(
        "trust",
        trust_pressure,
        weight=0.25,
        description="信頼できる人の少なさからの圧力"
    )
    
    # 3. 情報圧力
    def information_pressure(context: dict) -> float:
        unknown_count = context.get('unknown_roles', 0)
        total = context.get('alive_count', 1)
        return unknown_count / max(1, total)
    
    mdp.register_dimension(
        "information",
        information_pressure,
        weight=0.2,
        description="未確定情報の多さからの圧力"
    )
    
    # 4. 時間圧力
    def time_pressure(context: dict) -> float:
        day = context.get('current_day', 1)
        max_days = context.get('max_days', 5)
        return day / max_days
    
    mdp.register_dimension(
        "time",
        time_pressure,
        weight=0.1,
        description="ゲーム進行からの圧力"
    )
    
    # 5. 生存圧力
    def survival_pressure(context: dict) -> float:
        werewolf_count = context.get('werewolf_count', 1)
        villager_count = context.get('villager_count', 1)
        # 人狼と村人の比率が近いほど危機感
        ratio = werewolf_count / max(1, villager_count)
        return min(1.0, ratio)
    
    mdp.register_dimension(
        "survival",
        survival_pressure,
        weight=0.1,
        description="人狼との人数バランスからの圧力"
    )
    
    return mdp


class WerewolfGame:
    """人狼ゲーム"""
    
    def __init__(self, num_players: int = 7):
        self.num_players = num_players
        self.players: List[WerewolfPlayer] = []
        self.current_day = 1
        self.max_days = 5
        self.phase = GamePhase.DAY_DISCUSSION
        
        # ゲーム履歴
        self.events = []
        self.execution_history = []
        self.attack_history = []
        
        # 統計
        self.suspicion_history = {i: [] for i in range(num_players)}
        self.energy_history = {i: {'direct': [], 'indirect': []} for i in range(num_players)}
        
        self._initialize_players()
    
    def _initialize_players(self):
        """プレイヤーの初期化"""
        names = ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎", "七郎"]
        roles = [Role.WEREWOLF, Role.WEREWOLF, Role.SEER] + [Role.VILLAGER] * (self.num_players - 3)
        np.random.shuffle(roles)
        
        for i in range(self.num_players):
            # 役職によってパラメータを変える
            if roles[i] == Role.WEREWOLF:
                # 人狼: 攻撃的、情報優位
                params = SSDParametersV3_5(
                    use_direct_action=True,
                    use_indirect_action=True,
                    gamma_i2d=0.1,
                    gamma_d2i=0.05,
                    Theta_critical=300.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=15.0,
                )
            elif roles[i] == Role.SEER:
                # 占い師: 情報重視、慎重
                params = SSDParametersV3_5(
                    use_direct_action=False,
                    use_indirect_action=True,
                    gamma_i2d=0.03,
                    gamma_d2i=0.1,
                    Theta_critical=400.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=10.0,
                )
            else:
                # 村人: バランス型
                params = SSDParametersV3_5(
                    use_direct_action=True,
                    use_indirect_action=True,
                    gamma_i2d=0.05,
                    gamma_d2i=0.05,
                    Theta_critical=350.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=12.0,
                )
            
            player = WerewolfPlayer(
                id=i,
                name=names[i],
                role=roles[i],
                state=SSDStateV3_5(kappa=1.0, E_direct=50.0, E_indirect=100.0),
                engine=SSDCoreEngineV3_5(params),
                pressure_system=create_werewolf_pressure()
            )
            
            # 初期信頼度（全員に対して中立）
            for j in range(self.num_players):
                if i != j:
                    player.trust_map[j] = 0.5
            
            self.players.append(player)
    
    def log_event(self, message: str):
        """イベントログ"""
        self.events.append(f"[Day {self.current_day}] {message}")
        print(f"  {message}")
    
    def get_alive_players(self) -> List[WerewolfPlayer]:
        """生存者リストを取得"""
        return [p for p in self.players if p.is_alive]
    
    def get_werewolf_count(self) -> int:
        """生存人狼数"""
        return sum(1 for p in self.get_alive_players() if p.role == Role.WEREWOLF)
    
    def get_villager_count(self) -> int:
        """生存村人側数"""
        return sum(1 for p in self.get_alive_players() if p.role != Role.WEREWOLF)
    
    def check_game_end(self) -> Optional[str]:
        """ゲーム終了判定"""
        werewolf_count = self.get_werewolf_count()
        villager_count = self.get_villager_count()
        
        if werewolf_count == 0:
            return "村人側の勝利"
        elif werewolf_count >= villager_count:
            return "人狼側の勝利"
        elif self.current_day > self.max_days:
            return "時間切れ（引き分け）"
        return None
    
    def day_phase(self):
        """昼フェーズ: 議論と投票"""
        self.log_event(f"=== Day {self.current_day}: 昼の議論開始 ===")
        
        alive = self.get_alive_players()
        
        # 各プレイヤーの意味圧を計算
        for player in alive:
            context = {
                'suspicion_level': player.suspicion_level,
                'trusted_count': sum(1 for t in player.trust_map.values() if t > 0.7),
                'alive_count': len(alive),
                'unknown_roles': len(alive) - len(player.known_roles) - 1,  # 自分除く
                'current_day': self.current_day,
                'max_days': self.max_days,
                'werewolf_count': self.get_werewolf_count(),
                'villager_count': self.get_villager_count(),
            }
            
            p_external = player.pressure_system.calculate(context)
            
            # SSDエンジンで状態更新
            player.state = player.engine.step(player.state, p_external, dt=0.1)
            
            # 統計記録
            self.suspicion_history[player.id].append(player.suspicion_level)
            self.energy_history[player.id]['direct'].append(player.state.E_direct)
            self.energy_history[player.id]['indirect'].append(player.state.E_indirect)
        
        # 投票
        self.log_event("--- 投票タイム ---")
        votes = self._conduct_vote(alive)
        
        # 処刑
        if votes:
            executed_id = max(votes, key=votes.get)
            executed = self.players[executed_id]
            self.log_event(f"💀 {executed.name} ({executed.role.value}) が処刑されました")
            executed.is_alive = False
            self.execution_history.append(executed.id)
    
    def _conduct_vote(self, alive: List[WerewolfPlayer]) -> Dict[int, int]:
        """投票を実施"""
        votes = {p.id: 0 for p in alive}
        
        for voter in alive:
            # 最も疑わしい人に投票（人狼は村人を、村人は疑惑の高い人を）
            candidates = [p for p in alive if p.id != voter.id]
            
            if voter.role == Role.WEREWOLF:
                # 人狼: 村人をランダムに狙う
                non_werewolves = [p for p in candidates if p.role != Role.WEREWOLF]
                if non_werewolves:
                    target = np.random.choice(non_werewolves)
                else:
                    target = np.random.choice(candidates)
            else:
                # 村人/占い師: 疑惑レベルが高い人を狙う
                target = max(candidates, key=lambda p: p.suspicion_level + np.random.random() * 2)
            
            votes[target.id] += 1
            target.vote_count += 1
            voter.voted_for.append(target.id)
            
            self.log_event(f"  {voter.name} → {target.name} に投票")
            
            # 投票された人の疑惑レベルを上げる
            target.suspicion_level += 1.5
        
        return votes
    
    def night_phase(self):
        """夜フェーズ: 人狼の襲撃と占い師の占い"""
        self.log_event(f"=== Day {self.current_day}: 夜のフェーズ ===")
        
        alive = self.get_alive_players()
        
        # 人狼の襲撃
        werewolves = [p for p in alive if p.role == Role.WEREWOLF]
        if werewolves:
            # 村人の中からランダムに襲撃
            non_werewolves = [p for p in alive if p.role != Role.WEREWOLF]
            if non_werewolves:
                target = np.random.choice(non_werewolves)
                self.log_event(f"🌙 人狼が {target.name} ({target.role.value}) を襲撃しました")
                target.is_alive = False
                self.attack_history.append(target.id)
        
        # 占い師の占い
        seers = [p for p in alive if p.role == Role.SEER]
        if seers:
            seer = seers[0]
            # 未知の役職をランダムに占う
            unknown = [p for p in alive if p.id not in seer.known_roles and p.id != seer.id]
            if unknown:
                target = np.random.choice(unknown)
                seer.known_roles[target.id] = target.role
                self.log_event(f"🔮 占い師が {target.name} を占い → {target.role.value}")
                
                # 人狼を発見したら疑惑レベルを大幅UP
                if target.role == Role.WEREWOLF:
                    target.suspicion_level += 5.0
    
    def simulate(self):
        """ゲームシミュレーション実行"""
        print("="*70)
        print("SSD v3.5 統合デモ: 人狼ゲームAI")
        print("="*70)
        
        print("\n[初期配置]")
        for p in self.players:
            print(f"  {p.name}: {p.role.value}")
        
        print("\n[ゲーム開始]")
        
        while True:
            # 昼フェーズ
            self.day_phase()
            
            # 終了判定
            result = self.check_game_end()
            if result:
                self.log_event(f"🏆 ゲーム終了: {result}")
                break
            
            # 夜フェーズ
            self.night_phase()
            
            # 終了判定
            result = self.check_game_end()
            if result:
                self.log_event(f"🏆 ゲーム終了: {result}")
                break
            
            self.current_day += 1
        
        # 結果表示
        self.show_results()
        self.visualize()
    
    def show_results(self):
        """結果表示"""
        print("\n" + "="*70)
        print("📊 最終結果")
        print("="*70)
        
        print("\n[生存者]")
        for p in self.get_alive_players():
            print(f"  {p.name} ({p.role.value})")
        
        print("\n[犠牲者]")
        for p in self.players:
            if not p.is_alive:
                cause = "処刑" if p.id in self.execution_history else "襲撃"
                print(f"  {p.name} ({p.role.value}) - {cause}")
        
        print("\n[疑惑レベル推移]")
        for p in self.players:
            if self.suspicion_history[p.id]:
                max_suspicion = max(self.suspicion_history[p.id])
                print(f"  {p.name}: 最大 {max_suspicion:.1f}")
    
    def visualize(self):
        """結果の可視化"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 疑惑レベルの推移
        ax1 = axes[0, 0]
        for p in self.players:
            if self.suspicion_history[p.id]:
                label = f"{p.name} ({p.role.value})"
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax1.plot(self.suspicion_history[p.id], label=label, color=color, linewidth=2, alpha=0.7)
        
        ax1.set_xlabel('Time Step', fontsize=12)
        ax1.set_ylabel('Suspicion Level', fontsize=12)
        ax1.set_title('Suspicion Level Evolution', fontsize=13, fontweight='bold')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # 2. E_indirect の推移
        ax2 = axes[0, 1]
        for p in self.players:
            if self.energy_history[p.id]['indirect']:
                label = f"{p.name} ({p.role.value})"
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax2.plot(self.energy_history[p.id]['indirect'], label=label, color=color, linewidth=2, alpha=0.7)
        
        ax2.set_xlabel('Time Step', fontsize=12)
        ax2.set_ylabel('E_indirect (Reasoning Energy)', fontsize=12)
        ax2.set_title('Indirect Energy (Information/Psychology)', fontsize=13, fontweight='bold')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # 3. E_direct の推移
        ax3 = axes[1, 0]
        for p in self.players:
            if self.energy_history[p.id]['direct']:
                label = f"{p.name} ({p.role.value})"
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax3.plot(self.energy_history[p.id]['direct'], label=label, color=color, linewidth=2, alpha=0.7)
        
        ax3.set_xlabel('Time Step', fontsize=12)
        ax3.set_ylabel('E_direct (Action Energy)', fontsize=12)
        ax3.set_title('Direct Energy (Voting/Action)', fontsize=13, fontweight='bold')
        ax3.legend(loc='best', fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        # 4. 投票ネットワーク（累積）
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        stats_text = f"""
Game Statistics
{'='*40}

Total Days: {self.current_day}
Executions: {len(self.execution_history)}
Attacks: {len(self.attack_history)}

Final Status:
  Werewolves: {self.get_werewolf_count()}
  Villagers: {self.get_villager_count()}

Most Suspected:
"""
        
        # 最も疑われたプレイヤー
        suspicions = [(p, max(self.suspicion_history[p.id]) if self.suspicion_history[p.id] else 0) 
                     for p in self.players]
        max_suspicion = max(suspicions, key=lambda x: x[1])
        max_player = max_suspicion[0]
        stats_text += f"  {max_player.name} ({max_player.role.value}): {max_suspicion[1]:.1f}\n"
        
        ax4.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
                verticalalignment='center')
        
        plt.tight_layout()
        plt.savefig('ssd_werewolf_game.png', dpi=150, bbox_inches='tight')
        print("\n💾 グラフ保存: ssd_werewolf_game.png")
        plt.show()


if __name__ == "__main__":
    game = WerewolfGame(num_players=7)
    game.simulate()
    
    print("\n" + "="*70)
    print("✅ デモ完了")
    print("="*70)
    print("\n🎓 学んだこと:")
    print("  1. 多次元意味圧が心理戦ゲームに適用できる")
    print("  2. 疑惑・信頼・情報などの複雑な圧力を統合")
    print("  3. SSD v3.5で推理（E_indirect）と行動（E_direct）を分離")
    print("  4. 相転移で極端な行動（暴露・強弁）を表現")
