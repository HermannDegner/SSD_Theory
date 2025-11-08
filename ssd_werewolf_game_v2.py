"""
SSD v3.5 統合デモ v2.0: 人狼ゲームAI (エネルギー駆動版)

v1.0からの改良点:
----------------
1. 投票にE_directを使用（エネルギーが高いほど強く投票）
2. 相転移時の特殊行動を実装
   - 村人: パニックで信頼していた人を攻撃
   - 占い師: CO（カミングアウト）して情報暴露
   - 人狼: 強弁・攻撃性増大
3. E_indirectで推理精度が変化
4. エネルギー消費システム（行動後にE_directが減少）

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
- E_indirect: 推理・情報・心理状態（高いほど推理精度向上）
- E_direct: 投票行動・発言の強さ（実際の行動に使用）
- 相転移: Theta_critical超過で極端な行動
"""

import numpy as np
import matplotlib.pyplot as plt
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
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
    has_revealed: bool = False  # CO済みか
    
    # 統計
    vote_count: int = 0  # 投票された回数
    voted_for: List[int] = field(default_factory=list)  # 投票した相手の履歴
    phase_transition_count: int = 0  # 相転移回数
    
    # エネルギー履歴
    total_energy_spent: float = 0.0


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


class WerewolfGameV2:
    """人狼ゲーム v2.0 - エネルギー駆動版"""
    
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
        self.energy_history = {i: {'direct': [], 'indirect': [], 'pressure': []} for i in range(num_players)}
        self.phase_transition_events = []
        
        self._initialize_players()
    
    def _initialize_players(self):
        """プレイヤーの初期化"""
        names = ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎", "七郎"]
        roles = [Role.WEREWOLF, Role.WEREWOLF, Role.SEER] + [Role.VILLAGER] * (self.num_players - 3)
        np.random.shuffle(roles)
        
        for i in range(self.num_players):
            # 役職によってパラメータを変える
            if roles[i] == Role.WEREWOLF:
                # 人狼: 攻撃的、情報優位、相転移しやすい
                params = SSDParametersV3_5(
                    use_direct_action=True,
                    use_indirect_action=True,
                    gamma_i2d=0.12,
                    gamma_d2i=0.05,
                    Theta_critical=300.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=15.0,
                )
                initial_E_direct = 80.0
                initial_E_indirect = 120.0
            elif roles[i] == Role.SEER:
                # 占い師: 情報重視、慎重、相転移でCO
                params = SSDParametersV3_5(
                    use_direct_action=False,
                    use_indirect_action=True,
                    gamma_i2d=0.03,
                    gamma_d2i=0.12,
                    Theta_critical=400.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=10.0,
                )
                initial_E_direct = 40.0
                initial_E_indirect = 150.0
            else:
                # 村人: バランス型、パニック相転移
                params = SSDParametersV3_5(
                    use_direct_action=True,
                    use_indirect_action=True,
                    gamma_i2d=0.06,
                    gamma_d2i=0.06,
                    Theta_critical=350.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=12.0,
                )
                initial_E_direct = 60.0
                initial_E_indirect = 100.0
            
            player = WerewolfPlayer(
                id=i,
                name=names[i],
                role=roles[i],
                state=SSDStateV3_5(kappa=1.0, E_direct=initial_E_direct, E_indirect=initial_E_indirect),
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
    
    def update_player_energy(self, player: WerewolfPlayer):
        """プレイヤーのエネルギー状態を更新"""
        context = {
            'suspicion_level': player.suspicion_level,
            'trusted_count': sum(1 for t in player.trust_map.values() if t > 0.7),
            'alive_count': len(self.get_alive_players()),
            'unknown_roles': len(self.get_alive_players()) - len(player.known_roles) - 1,
            'current_day': self.current_day,
            'max_days': self.max_days,
            'werewolf_count': self.get_werewolf_count(),
            'villager_count': self.get_villager_count(),
        }
        
        p_external = player.pressure_system.calculate(context)
        
        # 相転移前の状態を記録
        was_critical = player.state.E_indirect < player.engine.params.Theta_critical
        
        # SSDエンジンで状態更新
        player.state = player.engine.step(player.state, p_external, dt=0.1)
        
        # 相転移検出
        is_critical = player.state.E_indirect < player.engine.params.Theta_critical
        if is_critical and not was_critical:
            player.phase_transition_count += 1
            self.handle_phase_transition(player)
        
        # 統計記録
        self.suspicion_history[player.id].append(player.suspicion_level)
        self.energy_history[player.id]['direct'].append(player.state.E_direct)
        self.energy_history[player.id]['indirect'].append(player.state.E_indirect)
        self.energy_history[player.id]['pressure'].append(p_external)
    
    def handle_phase_transition(self, player: WerewolfPlayer):
        """相転移時の特殊行動"""
        event = f"⚡ {player.name} が相転移！ (E_indirect={player.state.E_indirect:.1f} < {player.engine.params.Theta_critical})"
        self.log_event(event)
        self.phase_transition_events.append((self.current_day, player.id, player.role))
        
        if player.role == Role.SEER and not player.has_revealed:
            # 占い師のCO（カミングアウト）
            self.log_event(f"  📢 {player.name} が占い師をCO！")
            player.has_revealed = True
            
            # 知っている情報を暴露
            for target_id, target_role in player.known_roles.items():
                target = self.players[target_id]
                if target.is_alive:
                    self.log_event(f"     → {target.name} は {target_role.value}！")
                    if target_role == Role.WEREWOLF:
                        target.suspicion_level += 8.0
                    else:
                        target.suspicion_level -= 2.0
        
        elif player.role == Role.VILLAGER:
            # 村人のパニック: 最も信頼していた人を疑う
            if player.trust_map:
                most_trusted_id = max(player.trust_map, key=player.trust_map.get)
                most_trusted = self.players[most_trusted_id]
                if most_trusted.is_alive:
                    self.log_event(f"  😱 {player.name} がパニック！ {most_trusted.name} を疑い始めた！")
                    player.trust_map[most_trusted_id] = 0.0
                    most_trusted.suspicion_level += 3.0
        
        elif player.role == Role.WEREWOLF:
            # 人狼の強弁: 攻撃性増大
            self.log_event(f"  😈 {player.name} が強弁モード！攻撃性が増大")
            # E_directをブースト
            player.state.E_direct *= 1.5
    
    def day_phase(self):
        """昼フェーズ: 議論と投票"""
        self.log_event(f"=== Day {self.current_day}: 昼の議論開始 ===")
        
        alive = self.get_alive_players()
        
        # 各プレイヤーのエネルギー状態を更新
        for player in alive:
            self.update_player_energy(player)
        
        # 投票（エネルギー駆動）
        self.log_event("--- 投票タイム ---")
        votes = self._conduct_energy_driven_vote(alive)
        
        # 処刑
        if votes:
            executed_id = max(votes, key=votes.get)
            executed = self.players[executed_id]
            self.log_event(f"💀 {executed.name} ({executed.role.value}) が処刑されました")
            executed.is_alive = False
            self.execution_history.append(executed.id)
    
    def _conduct_energy_driven_vote(self, alive: List[WerewolfPlayer]) -> Dict[int, float]:
        """エネルギー駆動型の投票システム"""
        votes = {p.id: 0.0 for p in alive}
        
        for voter in alive:
            # 投票先の決定
            target = self._select_vote_target(voter, alive)
            if target is None:
                continue
            
            # E_directに応じて投票の強さが変わる
            if voter.state.E_direct < 10.0:
                # エネルギー極小: ランダムな弱い投票（0.1票分）
                candidates = [p for p in alive if p.id != voter.id]
                target = np.random.choice(candidates) if candidates else None
                if target is None:
                    continue
                vote_power = 0.1
                energy_cost = 5.0
                self.log_event(f"  {voter.name} → {target.name} に弱い投票 (E不足: {voter.state.E_direct:.1f})")
            elif voter.state.E_direct < 30.0:
                # エネルギー不足: 通常の1票だがコスト減
                vote_power = 1.0
                energy_cost = 10.0
                self.log_event(f"  {voter.name} → {target.name} に投票 (E低下: {voter.state.E_direct:.1f})")
            else:
                # 通常: E_directに比例した強い投票（最大3票分）
                vote_power = min(3.0, voter.state.E_direct / 100.0)
                energy_cost = 30.0 + vote_power * 10.0
                self.log_event(f"  {voter.name} → {target.name} に投票 (強さ: {vote_power:.2f}, 消費E: {energy_cost:.1f})")
            
            votes[target.id] += vote_power
            target.vote_count += 1
            voter.voted_for.append(target.id)
            
            # エネルギー消費（残量を下回らないように）
            actual_cost = min(energy_cost, voter.state.E_direct * 0.9)
            voter.state.E_direct -= actual_cost
            voter.total_energy_spent += actual_cost
            
            # 投票された人の疑惑レベルを上げる（投票の強さに比例）
            target.suspicion_level += vote_power * 1.0
            
            # 投票した人への信頼度を下げる
            if target.id in voter.trust_map:
                voter.trust_map[target.id] = max(0.0, voter.trust_map[target.id] - 0.2)
        
        return votes
    
    def _select_vote_target(self, voter: WerewolfPlayer, alive: List[WerewolfPlayer]) -> Optional[WerewolfPlayer]:
        """投票先の選択（推理精度はE_indirectに依存）"""
        candidates = [p for p in alive if p.id != voter.id]
        if not candidates:
            return None
        
        # E_indirectが高いほど推理精度が高い（ノイズが減る）
        reasoning_quality = min(1.0, voter.state.E_indirect / 200.0)
        noise_factor = (1.0 - reasoning_quality) * 5.0  # 0〜5のランダムノイズ
        
        if voter.role == Role.WEREWOLF:
            # 人狼: 村人を狙う（E_indirectが高いとバレにくい人を選ぶ）
            non_werewolves = [p for p in candidates if p.role != Role.WEREWOLF]
            if non_werewolves:
                if reasoning_quality > 0.7:
                    # 推理力が高い: 疑惑レベルが低い人を狙う（カモフラージュ）
                    target = min(non_werewolves, key=lambda p: p.suspicion_level + np.random.random() * noise_factor)
                else:
                    # 推理力が低い: ランダム
                    target = np.random.choice(non_werewolves)
            else:
                target = np.random.choice(candidates)
        
        elif voter.role == Role.SEER:
            # 占い師: 既知の人狼を最優先
            known_werewolves = [p for p in candidates if voter.known_roles.get(p.id) == Role.WEREWOLF]
            if known_werewolves:
                target = known_werewolves[0]
            else:
                # 疑惑レベルが高い人（推理精度によってノイズ変化）
                target = max(candidates, key=lambda p: p.suspicion_level + np.random.random() * noise_factor)
        
        else:
            # 村人: 疑惑レベルが高い人（推理精度によってノイズ変化）
            target = max(candidates, key=lambda p: p.suspicion_level + np.random.random() * noise_factor)
        
        return target
    
    def night_phase(self):
        """夜フェーズ: 人狼の襲撃と占い師の占い"""
        self.log_event(f"=== Day {self.current_day}: 夜のフェーズ ===")
        
        alive = self.get_alive_players()
        
        # 人狼の襲撃
        werewolves = [p for p in alive if p.role == Role.WEREWOLF]
        if werewolves:
            # 最もE_directが高い人狼が襲撃
            active_werewolf = max(werewolves, key=lambda w: w.state.E_direct)
            
            non_werewolves = [p for p in alive if p.role != Role.WEREWOLF]
            if non_werewolves:
                if active_werewolf.state.E_direct >= 50.0:
                    # 十分なエネルギー: 戦略的襲撃（疑惑レベルが低い人）
                    target = min(non_werewolves, key=lambda p: p.suspicion_level + np.random.random())
                    self.log_event(f"🌙 {active_werewolf.name} が {target.name} ({target.role.value}) を襲撃")
                    energy_cost = 50.0
                elif active_werewolf.state.E_direct >= 20.0:
                    # エネルギー不足: ランダム襲撃（精度低下）
                    target = np.random.choice(non_werewolves)
                    self.log_event(f"🌙 {active_werewolf.name} が {target.name} ({target.role.value}) を弱い襲撃 (E不足)")
                    energy_cost = 20.0
                else:
                    # エネルギー極小: 襲撃失敗
                    self.log_event(f"🌙 人狼のエネルギー不足で襲撃失敗 (E_direct={active_werewolf.state.E_direct:.1f})")
                    return
                
                target.is_alive = False
                self.attack_history.append(target.id)
                active_werewolf.state.E_direct -= energy_cost
                active_werewolf.total_energy_spent += energy_cost
        
        # 占い師の占い
        seers = [p for p in alive if p.role == Role.SEER]
        if seers:
            seer = seers[0]
            # 未知の役職をランダムに占う
            unknown = [p for p in alive if p.id not in seer.known_roles and p.id != seer.id]
            if unknown:
                target = np.random.choice(unknown)
                seer.known_roles[target.id] = target.role
                self.log_event(f"🔮 {seer.name} が {target.name} を占い → {target.role.value}")
                
                # 人狼を発見したら疑惑レベルを大幅UP
                if target.role == Role.WEREWOLF:
                    target.suspicion_level += 5.0
                    # 占い師のE_indirectが増加（重要情報取得）
                    seer.state.E_indirect += 50.0
    
    def simulate(self):
        """ゲームシミュレーション実行"""
        print("="*70)
        print("SSD v3.5 統合デモ v2.0: 人狼ゲームAI (エネルギー駆動版)")
        print("="*70)
        
        print("\n[初期配置]")
        for p in self.players:
            print(f"  {p.name}: {p.role.value} (E_direct={p.state.E_direct:.1f}, E_indirect={p.state.E_indirect:.1f})")
        
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
            print(f"    E_direct: {p.state.E_direct:.1f}, E_indirect: {p.state.E_indirect:.1f}")
            print(f"    相転移回数: {p.phase_transition_count}, 消費エネルギー: {p.total_energy_spent:.1f}")
        
        print("\n[犠牲者]")
        for p in self.players:
            if not p.is_alive:
                cause = "処刑" if p.id in self.execution_history else "襲撃"
                print(f"  {p.name} ({p.role.value}) - {cause}")
                print(f"    最終疑惑: {p.suspicion_level:.1f}, 相転移: {p.phase_transition_count}回")
        
        print(f"\n[相転移イベント: {len(self.phase_transition_events)}回]")
        for day, player_id, role in self.phase_transition_events:
            player = self.players[player_id]
            print(f"  Day {day}: {player.name} ({role.value})")
    
    def visualize(self):
        """結果の可視化"""
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        
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
        
        # 相転移閾値を表示
        for p in self.players:
            if self.energy_history[p.id]['indirect']:
                ax2.axhline(y=p.engine.params.Theta_critical, color='gray', linestyle='--', alpha=0.3)
        
        ax2.set_xlabel('Time Step', fontsize=12)
        ax2.set_ylabel('E_indirect (Reasoning Energy)', fontsize=12)
        ax2.set_title('Indirect Energy (Information/Psychology)', fontsize=13, fontweight='bold')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # 3. E_direct の推移
        ax3 = axes[0, 2]
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
        
        # 4. 外部圧力の推移
        ax4 = axes[1, 0]
        for p in self.players:
            if self.energy_history[p.id]['pressure']:
                label = f"{p.name} ({p.role.value})"
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax4.plot(self.energy_history[p.id]['pressure'], label=label, color=color, linewidth=2, alpha=0.7)
        
        ax4.set_xlabel('Time Step', fontsize=12)
        ax4.set_ylabel('External Pressure', fontsize=12)
        ax4.set_title('Multi-Dimensional Pressure Evolution', fontsize=13, fontweight='bold')
        ax4.legend(loc='best', fontsize=9)
        ax4.grid(True, alpha=0.3)
        
        # 5. エネルギー消費統計
        ax5 = axes[1, 1]
        alive_players = [p for p in self.players]
        names = [p.name for p in alive_players]
        energy_spent = [p.total_energy_spent for p in alive_players]
        colors = ['red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green' 
                 for p in alive_players]
        
        ax5.bar(names, energy_spent, color=colors, alpha=0.7)
        ax5.set_xlabel('Player', fontsize=12)
        ax5.set_ylabel('Total Energy Spent', fontsize=12)
        ax5.set_title('Energy Consumption by Player', fontsize=13, fontweight='bold')
        ax5.tick_params(axis='x', rotation=45)
        ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. 統計情報
        ax6 = axes[1, 2]
        ax6.axis('off')
        
        stats_text = f"""
Game Statistics (v2.0)
{'='*40}

Total Days: {self.current_day}
Executions: {len(self.execution_history)}
Attacks: {len(self.attack_history)}
Phase Transitions: {len(self.phase_transition_events)}

Final Status:
  Werewolves: {self.get_werewolf_count()}
  Villagers: {self.get_villager_count()}

Energy Analysis:
  Max Energy Spent: {max(p.total_energy_spent for p in self.players):.1f}
  Most Transitions: {max(p.phase_transition_count for p in self.players)}

Key Events:
"""
        
        # 相転移イベント
        for day, player_id, role in self.phase_transition_events[:3]:
            player = self.players[player_id]
            stats_text += f"  Day{day}: {player.name} ({role.value})\n"
        
        ax6.text(0.1, 0.5, stats_text, fontsize=10, family='monospace',
                verticalalignment='center')
        
        plt.tight_layout()
        plt.savefig('ssd_werewolf_game_v2.png', dpi=150, bbox_inches='tight')
        print("\n💾 グラフ保存: ssd_werewolf_game_v2.png")
        plt.show()


if __name__ == "__main__":
    game = WerewolfGameV2(num_players=7)
    game.simulate()
    
    print("\n" + "="*70)
    print("✅ デモ完了")
    print("="*70)
    print("\n🎓 v2.0の改良点:")
    print("  1. ✅ 投票にE_directを使用（エネルギーが高いほど強い投票）")
    print("  2. ✅ エネルギー消費システム（行動後にE_directが減少）")
    print("  3. ✅ 推理精度がE_indirectに依存（高いほどノイズ減少）")
    print("  4. ✅ 相転移時の特殊行動実装:")
    print("       - 村人: パニックで信頼していた人を攻撃")
    print("       - 占い師: CO（カミングアウト）で情報暴露")
    print("       - 人狼: 強弁モードでE_directブースト")
    print("\n🔬 SSD理論の実証:")
    print("  - E_indirectとE_directの分離が意思決定に影響")
    print("  - 相転移メカニズムが劇的な行動変化を生む")
    print("  - 多次元意味圧が複雑な心理状態を統合")
