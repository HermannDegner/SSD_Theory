"""
SSD v3.5 統合デモ v3.0: 人狼ゲームAI (構造社会版)

v2.0からの革新的進化:
-------------------
1. **整合慣性（kappa）の動的更新** - 学習の実装
   - 成功体験で kappa 増加 → 推理精度が経験則で向上
   - 失敗で kappa 減少 → 自信喪失と判断力低下
   
2. **議論フェーズと言語的意味圧** - 社会的相互作用
   - プレイヤーが発言（運動）で他者に意味圧を与える
   - 「社会的疑惑圧」が多次元意味圧に追加
   - 影響力の強いプレイヤーが世論を誘導
   
3. **協働快と主観的境界の双方向更新** - 同盟形成
   - 同じ相手に投票 → 信頼度上昇（協働的快）
   - 信頼していた人から投票された → 信頼度急降下（裏切り）
   - 派閥・同盟が自然発生
   
4. **確率的跳躍モデル** - 予測不可能性
   - 決定論的閾値 → ポアソン過程による確率的発火
   - 低ストレスでも稀に跳躍、高ストレスでも稀に耐える
   - 人間的なリアリティ

シナリオ:
--------
7人の村で人狼ゲームが開催される。
- 村人 (Villager): 4人
- 人狼 (Werewolf): 2人
- 占い師 (Seer): 1人

各プレイヤーはSSD v3.5 + 多次元意味圧 + 社会的相互作用で判断を行う。
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


@dataclass
class Statement:
    """発言（言語的運動）"""
    speaker_id: int
    target_id: int  # 疑惑の対象
    intensity: float  # 発言の強さ（E_directから決定）
    day: int


@dataclass
class WerewolfPlayerV3:
    """人狼ゲームのプレイヤー v3.0"""
    id: int
    name: str
    role: Role
    
    # SSD状態
    state: SSDStateV3_5
    engine: SSDCoreEngineV3_5
    pressure_system: MultiDimensionalPressure
    
    # ゲーム状態
    is_alive: bool = True
    suspicion_level: float = 0.0
    trust_map: Dict[int, float] = field(default_factory=dict)
    
    # 社会的意味圧（他者からの発言による疑惑）
    social_suspicion: float = 0.0
    
    # 知識
    known_roles: Dict[int, Role] = field(default_factory=dict)
    has_revealed: bool = False
    
    # 統計
    vote_count: int = 0
    voted_for: List[int] = field(default_factory=list)
    phase_transition_count: int = 0
    total_energy_spent: float = 0.0
    
    # 発言履歴
    statements: List[Statement] = field(default_factory=list)


def create_werewolf_pressure_v3() -> MultiDimensionalPressure:
    """人狼ゲーム用の多次元意味圧システム v3.0"""
    mdp = MultiDimensionalPressure()
    
    # 1. 疑惑圧力（自己認識）
    def suspicion_pressure(context: dict) -> float:
        suspicion = context.get('suspicion_level', 0.0)
        return min(1.0, suspicion / 10.0)
    
    mdp.register_dimension(
        "suspicion",
        suspicion_pressure,
        weight=0.25,  # v2から減少（社会的疑惑圧を追加したため）
        description="自分への疑惑からの圧力"
    )
    
    # 2. 社会的疑惑圧力（NEW! 他者からの言語的意味圧）
    def social_suspicion_pressure(context: dict) -> float:
        social = context.get('social_suspicion', 0.0)
        return min(1.0, social / 8.0)
    
    mdp.register_dimension(
        "social_suspicion",
        social_suspicion_pressure,
        weight=0.25,
        description="他者の発言による疑惑圧力"
    )
    
    # 3. 信頼圧力
    def trust_pressure(context: dict) -> float:
        trust_count = context.get('trusted_count', 0)
        total = context.get('alive_count', 1)
        return 1.0 - (trust_count / max(1, total))
    
    mdp.register_dimension(
        "trust",
        trust_pressure,
        weight=0.2,
        description="信頼できる人の少なさからの圧力"
    )
    
    # 4. 情報圧力
    def information_pressure(context: dict) -> float:
        unknown_count = context.get('unknown_roles', 0)
        total = context.get('alive_count', 1)
        return unknown_count / max(1, total)
    
    mdp.register_dimension(
        "information",
        information_pressure,
        weight=0.15,
        description="未確定情報の多さからの圧力"
    )
    
    # 5. 時間圧力
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
    
    # 6. 生存圧力
    def survival_pressure(context: dict) -> float:
        werewolf_count = context.get('werewolf_count', 1)
        villager_count = context.get('villager_count', 1)
        ratio = werewolf_count / max(1, villager_count)
        return min(1.0, ratio)
    
    mdp.register_dimension(
        "survival",
        survival_pressure,
        weight=0.05,
        description="人狼との人数バランスからの圧力"
    )
    
    return mdp


class WerewolfGameV3:
    """人狼ゲーム v3.0 - 構造社会版"""
    
    def __init__(self, num_players: int = 7):
        self.num_players = num_players
        self.players: List[WerewolfPlayerV3] = []
        self.current_day = 1
        self.max_days = 6
        
        # ゲーム履歴
        self.events = []
        self.execution_history = []
        self.attack_history = []
        self.statements_log = []
        
        # 統計
        self.suspicion_history = {i: [] for i in range(num_players)}
        self.social_suspicion_history = {i: [] for i in range(num_players)}
        self.kappa_history = {i: [] for i in range(num_players)}
        self.energy_history = {i: {'direct': [], 'indirect': [], 'pressure': []} for i in range(num_players)}
        self.phase_transition_events = []
        
        self._initialize_players()
    
    def _initialize_players(self):
        """プレイヤーの初期化"""
        names = ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎", "七郎"]
        roles = [Role.WEREWOLF, Role.WEREWOLF, Role.SEER] + [Role.VILLAGER] * (self.num_players - 3)
        np.random.shuffle(roles)
        
        for i in range(self.num_players):
            if roles[i] == Role.WEREWOLF:
                params = SSDParametersV3_5(
                    use_direct_action=True,
                    use_indirect_action=True,
                    gamma_i2d=0.12,
                    gamma_d2i=0.05,
                    Theta_critical=300.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=15.0,
                )
                initial_E_direct = 100.0
                initial_E_indirect = 140.0
                initial_kappa = 1.2  # 人狼は初期から自信がある
            elif roles[i] == Role.SEER:
                params = SSDParametersV3_5(
                    use_direct_action=False,
                    use_indirect_action=True,
                    gamma_i2d=0.03,
                    gamma_d2i=0.12,
                    Theta_critical=400.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=10.0,
                )
                initial_E_direct = 50.0
                initial_E_indirect = 180.0
                initial_kappa = 1.0
            else:
                params = SSDParametersV3_5(
                    use_direct_action=True,
                    use_indirect_action=True,
                    gamma_i2d=0.06,
                    gamma_d2i=0.06,
                    Theta_critical=350.0,
                    enable_phase_transition=True,
                    phase_transition_multiplier=12.0,
                )
                initial_E_direct = 70.0
                initial_E_indirect = 120.0
                initial_kappa = 1.0
            
            player = WerewolfPlayerV3(
                id=i,
                name=names[i],
                role=roles[i],
                state=SSDStateV3_5(kappa=initial_kappa, E_direct=initial_E_direct, E_indirect=initial_E_indirect),
                engine=SSDCoreEngineV3_5(params),
                pressure_system=create_werewolf_pressure_v3()
            )
            
            # 初期信頼度
            for j in range(self.num_players):
                if i != j:
                    player.trust_map[j] = 0.5
            
            self.players.append(player)
    
    def log_event(self, message: str):
        """イベントログ"""
        self.events.append(f"[Day {self.current_day}] {message}")
        print(f"  {message}")
    
    def get_alive_players(self) -> List[WerewolfPlayerV3]:
        return [p for p in self.players if p.is_alive]
    
    def get_werewolf_count(self) -> int:
        return sum(1 for p in self.get_alive_players() if p.role == Role.WEREWOLF)
    
    def get_villager_count(self) -> int:
        return sum(1 for p in self.get_alive_players() if p.role != Role.WEREWOLF)
    
    def check_game_end(self) -> Optional[str]:
        werewolf_count = self.get_werewolf_count()
        villager_count = self.get_villager_count()
        
        if werewolf_count == 0:
            return "村人側の勝利"
        elif werewolf_count >= villager_count:
            return "人狼側の勝利"
        elif self.current_day > self.max_days:
            return "時間切れ（引き分け）"
        return None
    
    def update_player_energy(self, player: WerewolfPlayerV3):
        """プレイヤーのエネルギー状態を更新"""
        context = {
            'suspicion_level': player.suspicion_level,
            'social_suspicion': player.social_suspicion,  # NEW!
            'trusted_count': sum(1 for t in player.trust_map.values() if t > 0.7),
            'alive_count': len(self.get_alive_players()),
            'unknown_roles': len(self.get_alive_players()) - len(player.known_roles) - 1,
            'current_day': self.current_day,
            'max_days': self.max_days,
            'werewolf_count': self.get_werewolf_count(),
            'villager_count': self.get_villager_count(),
        }
        
        p_external = player.pressure_system.calculate(context)
        
        # SSDエンジンで状態更新
        player.state = player.engine.step(player.state, p_external, dt=0.1)
        
        # 確率的跳躍判定（NEW!）
        self.check_probabilistic_jump(player, p_external)
        
        # 統計記録
        self.suspicion_history[player.id].append(player.suspicion_level)
        self.social_suspicion_history[player.id].append(player.social_suspicion)
        self.kappa_history[player.id].append(player.state.kappa)
        self.energy_history[player.id]['direct'].append(player.state.E_direct)
        self.energy_history[player.id]['indirect'].append(player.state.E_indirect)
        self.energy_history[player.id]['pressure'].append(p_external)
    
    def check_probabilistic_jump(self, player: WerewolfPlayerV3, p_external: float):
        """確率的跳躍判定（整合跳躍数理モデル）"""
        # 発火強度の計算
        h0 = 0.01  # 基底発火率
        gamma = 50.0  # 感度パラメータ
        
        if player.state.E_indirect < player.engine.params.Theta_critical:
            # 臨界点を下回ると発火強度が指数的に増加
            delta_E = player.engine.params.Theta_critical - player.state.E_indirect
            h = h0 * np.exp(delta_E / gamma)
        else:
            # 通常時も低確率で発火
            h = h0
        
        # ポアソン過程による確率的発火
        dt = 0.1
        jump_probability = 1.0 - np.exp(-h * dt)
        
        if np.random.random() < jump_probability:
            player.phase_transition_count += 1
            self.handle_phase_transition(player, spontaneous=(player.state.E_indirect >= player.engine.params.Theta_critical))
    
    def handle_phase_transition(self, player: WerewolfPlayerV3, spontaneous: bool = False):
        """相転移時の特殊行動"""
        if spontaneous:
            event = f"⚡ {player.name} が突発的に跳躍！ (E_indirect={player.state.E_indirect:.1f}, 確率的発火)"
        else:
            event = f"⚡ {player.name} が相転移！ (E_indirect={player.state.E_indirect:.1f} < {player.engine.params.Theta_critical})"
        
        self.log_event(event)
        self.phase_transition_events.append((self.current_day, player.id, player.role, spontaneous))
        
        if player.role == Role.SEER and not player.has_revealed:
            self.log_event(f"  📢 {player.name} が占い師をCO！")
            player.has_revealed = True
            
            for target_id, target_role in player.known_roles.items():
                target = self.players[target_id]
                if target.is_alive:
                    self.log_event(f"     → {target.name} は {target_role.value}！")
                    if target_role == Role.WEREWOLF:
                        target.suspicion_level += 8.0
                        target.social_suspicion += 6.0  # 社会的疑惑も増加
                    else:
                        target.suspicion_level -= 2.0
        
        elif player.role == Role.VILLAGER:
            if player.trust_map:
                most_trusted_id = max(player.trust_map, key=player.trust_map.get)
                most_trusted = self.players[most_trusted_id]
                if most_trusted.is_alive:
                    self.log_event(f"  😱 {player.name} がパニック！ {most_trusted.name} を疑い始めた！")
                    player.trust_map[most_trusted_id] = 0.0
                    most_trusted.suspicion_level += 3.0
                    most_trusted.social_suspicion += 2.0
        
        elif player.role == Role.WEREWOLF:
            self.log_event(f"  😈 {player.name} が強弁モード！攻撃性が増大")
            player.state.E_direct *= 1.5
    
    def discussion_phase(self):
        """議論フェーズ（NEW! 言語的意味圧の交換）"""
        self.log_event("--- 議論タイム ---")
        
        alive = self.get_alive_players()
        
        # 社会的疑惑をリセット（今回の議論で上書き）
        for p in alive:
            p.social_suspicion = 0.0
        
        # 各プレイヤーが発言するか判定
        for speaker in alive:
            # E_directが高く、疑惑が強い対象がいれば発言
            if speaker.state.E_direct < 40.0:
                continue
            
            # 発言対象を選択
            candidates = [p for p in alive if p.id != speaker.id]
            if not candidates:
                continue
            
            # 推理精度（kappa × E_indirect）で対象を選ぶ
            reasoning_quality = min(1.0, (speaker.state.E_indirect / 200.0) * speaker.state.kappa)
            noise_factor = (1.0 - reasoning_quality) * 5.0
            
            if speaker.role == Role.WEREWOLF:
                # 人狼: 村人をランダムに攻撃（嘘の意味圧）
                non_werewolves = [p for p in candidates if p.role != Role.WEREWOLF]
                if non_werewolves:
                    target = np.random.choice(non_werewolves)
                else:
                    continue
            else:
                # 村人/占い師: 疑惑レベルが高い人を指摘
                target = max(candidates, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
            
            # 発言の強さ（E_directに比例）
            intensity = min(3.0, speaker.state.E_direct / 50.0)
            energy_cost = 20.0 + intensity * 5.0
            
            # 発言実行
            statement = Statement(
                speaker_id=speaker.id,
                target_id=target.id,
                intensity=intensity,
                day=self.current_day
            )
            speaker.statements.append(statement)
            self.statements_log.append(statement)
            
            # エネルギー消費
            speaker.state.E_direct -= energy_cost
            speaker.total_energy_spent += energy_cost
            
            # 対象に社会的疑惑圧を付与
            target.social_suspicion += intensity * 1.5
            
            self.log_event(f"  💬 {speaker.name} が {target.name} を疑う発言 (強度: {intensity:.2f})")
    
    def day_phase(self):
        """昼フェーズ"""
        self.log_event(f"=== Day {self.current_day}: 昼フェーズ ===")
        
        alive = self.get_alive_players()
        
        # 1. エネルギー更新
        for player in alive:
            self.update_player_energy(player)
        
        # 2. 議論（NEW!）
        self.discussion_phase()
        
        # 3. 投票
        self.log_event("--- 投票タイム ---")
        votes = self._conduct_vote(alive)
        
        # 4. 処刑と学習（NEW! kappa更新）
        if votes:
            executed_id = max(votes, key=votes.get)
            executed = self.players[executed_id]
            self.log_event(f"💀 {executed.name} ({executed.role.value}) が処刑されました")
            executed.is_alive = False
            self.execution_history.append(executed.id)
            
            # 学習フェーズ（NEW!）
            self.learning_phase(executed, votes)
    
    def learning_phase(self, executed: WerewolfPlayerV3, votes: Dict[int, float]):
        """学習フェーズ（整合慣性の更新）"""
        self.log_event("--- 学習フェーズ ---")
        
        is_werewolf = (executed.role == Role.WEREWOLF)
        
        for player in self.get_alive_players():
            if executed.id in player.voted_for:
                # この人に投票していた
                if is_werewolf:
                    # 成功！ kappa増加
                    delta_kappa = 0.15
                    player.state.kappa += delta_kappa
                    player.state.kappa = min(2.0, player.state.kappa)  # 上限
                    self.log_event(f"  ✅ {player.name} の推理成功！ kappa: {player.state.kappa:.2f} (+{delta_kappa:.2f})")
                else:
                    # 失敗... kappa減少
                    delta_kappa = -0.10
                    player.state.kappa += delta_kappa
                    player.state.kappa = max(0.3, player.state.kappa)  # 下限
                    self.log_event(f"  ❌ {player.name} の推理失敗... kappa: {player.state.kappa:.2f} ({delta_kappa:.2f})")
    
    def _conduct_vote(self, alive: List[WerewolfPlayerV3]) -> Dict[int, float]:
        """投票（協働快の実装）"""
        votes = {p.id: 0.0 for p in alive}
        voted_targets = {}  # {player_id: target_id}
        
        for voter in alive:
            target = self._select_vote_target(voter, alive)
            if target is None:
                continue
            
            # 投票の強さ
            if voter.state.E_direct < 10.0:
                candidates = [p for p in alive if p.id != voter.id]
                target = np.random.choice(candidates) if candidates else None
                if target is None:
                    continue
                vote_power = 0.1
                energy_cost = 5.0
            elif voter.state.E_direct < 30.0:
                vote_power = 1.0
                energy_cost = 10.0
            else:
                # kappa考慮（NEW! 高kappaは確信度が高い）
                vote_power = min(3.0, (voter.state.E_direct / 100.0) * voter.state.kappa)
                energy_cost = 30.0 + vote_power * 10.0
            
            votes[target.id] += vote_power
            target.vote_count += 1
            voter.voted_for.append(target.id)
            voted_targets[voter.id] = target.id
            
            actual_cost = min(energy_cost, voter.state.E_direct * 0.9)
            voter.state.E_direct -= actual_cost
            voter.total_energy_spent += actual_cost
            
            self.log_event(f"  {voter.name} → {target.name} (強さ: {vote_power:.2f}, κ={voter.state.kappa:.2f})")
            
            target.suspicion_level += vote_power * 1.0
        
        # 協働快の処理（NEW!）
        self.process_cooperation(voted_targets, alive)
        
        return votes
    
    def process_cooperation(self, voted_targets: Dict[int, int], alive: List[WerewolfPlayerV3]):
        """協働快の処理（主観的境界の双方向更新）"""
        self.log_event("--- 協働快の処理 ---")
        
        for player_a in alive:
            if player_a.id not in voted_targets:
                continue
            
            target_of_a = voted_targets[player_a.id]
            
            for player_b in alive:
                if player_a.id == player_b.id:
                    continue
                if player_b.id not in voted_targets:
                    continue
                
                target_of_b = voted_targets[player_b.id]
                
                if target_of_a == target_of_b:
                    # 協働成立！
                    old_trust = player_a.trust_map.get(player_b.id, 0.5)
                    player_a.trust_map[player_b.id] = min(1.0, old_trust + 0.15)
                    self.log_event(f"  🤝 {player_a.name} ⇔ {player_b.name} 協働 (信頼: {player_a.trust_map[player_b.id]:.2f})")
                
                elif target_of_b == player_a.id:
                    # 裏切り！
                    old_trust = player_a.trust_map.get(player_b.id, 0.5)
                    player_a.trust_map[player_b.id] = max(0.0, old_trust - 0.3)
                    self.log_event(f"  💔 {player_a.name} が {player_b.name} に裏切られた (信頼: {player_a.trust_map[player_b.id]:.2f})")
    
    def _select_vote_target(self, voter: WerewolfPlayerV3, alive: List[WerewolfPlayerV3]) -> Optional[WerewolfPlayerV3]:
        """投票先選択（kappa × E_indirectで推理精度決定）"""
        candidates = [p for p in alive if p.id != voter.id]
        if not candidates:
            return None
        
        # 推理精度 = kappa × (E_indirect / 200)
        reasoning_quality = min(1.0, (voter.state.E_indirect / 200.0) * voter.state.kappa)
        noise_factor = (1.0 - reasoning_quality) * 5.0
        
        if voter.role == Role.WEREWOLF:
            non_werewolves = [p for p in candidates if p.role != Role.WEREWOLF]
            if non_werewolves:
                if reasoning_quality > 0.7:
                    target = min(non_werewolves, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
                else:
                    target = np.random.choice(non_werewolves)
            else:
                target = np.random.choice(candidates)
        
        elif voter.role == Role.SEER:
            known_werewolves = [p for p in candidates if voter.known_roles.get(p.id) == Role.WEREWOLF]
            if known_werewolves:
                target = known_werewolves[0]
            else:
                target = max(candidates, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
        
        else:
            # 信頼する人は避ける（NEW!）
            untrusted = [p for p in candidates if voter.trust_map.get(p.id, 0.5) < 0.6]
            if untrusted:
                target = max(untrusted, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
            else:
                target = max(candidates, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
        
        return target
    
    def night_phase(self):
        """夜フェーズ"""
        self.log_event(f"=== Day {self.current_day}: 夜のフェーズ ===")
        
        alive = self.get_alive_players()
        
        # 人狼の襲撃
        werewolves = [p for p in alive if p.role == Role.WEREWOLF]
        if werewolves:
            active_werewolf = max(werewolves, key=lambda w: w.state.E_direct)
            
            non_werewolves = [p for p in alive if p.role != Role.WEREWOLF]
            if non_werewolves:
                if active_werewolf.state.E_direct >= 50.0:
                    target = min(non_werewolves, key=lambda p: p.suspicion_level + np.random.random())
                    self.log_event(f"🌙 {active_werewolf.name} が {target.name} ({target.role.value}) を襲撃")
                    energy_cost = 50.0
                elif active_werewolf.state.E_direct >= 20.0:
                    target = np.random.choice(non_werewolves)
                    self.log_event(f"🌙 {active_werewolf.name} が {target.name} ({target.role.value}) を弱い襲撃")
                    energy_cost = 20.0
                else:
                    self.log_event(f"🌙 人狼のエネルギー不足で襲撃失敗")
                    return
                
                target.is_alive = False
                self.attack_history.append(target.id)
                active_werewolf.state.E_direct -= energy_cost
        
        # 占い師の占い
        seers = [p for p in alive if p.role == Role.SEER]
        if seers:
            seer = seers[0]
            unknown = [p for p in alive if p.id not in seer.known_roles and p.id != seer.id]
            if unknown:
                target = np.random.choice(unknown)
                seer.known_roles[target.id] = target.role
                self.log_event(f"🔮 {seer.name} が {target.name} を占い → {target.role.value}")
                
                if target.role == Role.WEREWOLF:
                    target.suspicion_level += 5.0
                    seer.state.E_indirect += 50.0
                    seer.state.kappa += 0.1  # 重要情報で自信増加
    
    def simulate(self):
        """ゲームシミュレーション実行"""
        print("="*70)
        print("SSD v3.0 統合デモ: 人狼ゲームAI (構造社会版)")
        print("="*70)
        
        print("\n[初期配置]")
        for p in self.players:
            print(f"  {p.name}: {p.role.value} (E_d={p.state.E_direct:.0f}, E_i={p.state.E_indirect:.0f}, κ={p.state.kappa:.1f})")
        
        print("\n[ゲーム開始]")
        
        while True:
            self.day_phase()
            
            result = self.check_game_end()
            if result:
                self.log_event(f"🏆 ゲーム終了: {result}")
                break
            
            self.night_phase()
            
            result = self.check_game_end()
            if result:
                self.log_event(f"🏆 ゲーム終了: {result}")
                break
            
            self.current_day += 1
        
        self.show_results()
        self.visualize()
    
    def show_results(self):
        """結果表示"""
        print("\n" + "="*70)
        print("📊 v3.0 最終結果")
        print("="*70)
        
        print("\n[生存者]")
        for p in self.get_alive_players():
            print(f"  {p.name} ({p.role.value})")
            print(f"    kappa: {p.state.kappa:.2f}, E_d: {p.state.E_direct:.1f}, E_i: {p.state.E_indirect:.1f}")
            print(f"    跳躍: {p.phase_transition_count}回, 発言: {len(p.statements)}回")
        
        print("\n[犠牲者]")
        for p in self.players:
            if not p.is_alive:
                cause = "処刑" if p.id in self.execution_history else "襲撃"
                print(f"  {p.name} ({p.role.value}) - {cause}")
                print(f"    最終kappa: {p.state.kappa:.2f}")
        
        print(f"\n[相転移: {len(self.phase_transition_events)}回]")
        for day, pid, role, spont in self.phase_transition_events:
            p = self.players[pid]
            stype = "確率的" if spont else "臨界"
            print(f"  Day{day}: {p.name} ({role.value}) - {stype}跳躍")
        
        print(f"\n[発言: {len(self.statements_log)}回]")
    
    def visualize(self):
        """結果の可視化"""
        fig = plt.figure(figsize=(20, 14))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. kappa（整合慣性）の推移
        ax1 = fig.add_subplot(gs[0, 0])
        for p in self.players:
            if self.kappa_history[p.id]:
                label = f"{p.name} ({p.role.value})"
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax1.plot(self.kappa_history[p.id], label=label, color=color, linewidth=2, alpha=0.7)
        ax1.set_title('Kappa Evolution (Learning)', fontweight='bold')
        ax1.set_xlabel('Time Step')
        ax1.set_ylabel('Kappa (Coherence Inertia)')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # 2. 社会的疑惑圧の推移
        ax2 = fig.add_subplot(gs[0, 1])
        for p in self.players:
            if self.social_suspicion_history[p.id]:
                label = f"{p.name}"
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax2.plot(self.social_suspicion_history[p.id], label=label, color=color, linewidth=2, alpha=0.7)
        ax2.set_title('Social Suspicion Pressure', fontweight='bold')
        ax2.set_xlabel('Time Step')
        ax2.set_ylabel('Social Suspicion')
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # 3. E_indirect
        ax3 = fig.add_subplot(gs[0, 2])
        for p in self.players:
            if self.energy_history[p.id]['indirect']:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax3.plot(self.energy_history[p.id]['indirect'], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax3.axhline(y=300, color='red', linestyle='--', alpha=0.3, label='Werewolf Θc')
        ax3.axhline(y=350, color='green', linestyle='--', alpha=0.3, label='Villager Θc')
        ax3.set_title('E_indirect (Reasoning)', fontweight='bold')
        ax3.set_xlabel('Time Step')
        ax3.set_ylabel('E_indirect')
        ax3.legend(fontsize=7)
        ax3.grid(True, alpha=0.3)
        
        # 4. E_direct
        ax4 = fig.add_subplot(gs[1, 0])
        for p in self.players:
            if self.energy_history[p.id]['direct']:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax4.plot(self.energy_history[p.id]['direct'], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax4.set_title('E_direct (Action)', fontweight='bold')
        ax4.set_xlabel('Time Step')
        ax4.set_ylabel('E_direct')
        ax4.legend(fontsize=8)
        ax4.grid(True, alpha=0.3)
        
        # 5. 疑惑レベル
        ax5 = fig.add_subplot(gs[1, 1])
        for p in self.players:
            if self.suspicion_history[p.id]:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax5.plot(self.suspicion_history[p.id], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax5.set_title('Suspicion Level', fontweight='bold')
        ax5.set_xlabel('Time Step')
        ax5.set_ylabel('Suspicion')
        ax5.legend(fontsize=8)
        ax5.grid(True, alpha=0.3)
        
        # 6. 外部圧力
        ax6 = fig.add_subplot(gs[1, 2])
        for p in self.players:
            if self.energy_history[p.id]['pressure']:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax6.plot(self.energy_history[p.id]['pressure'], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax6.set_title('External Pressure', fontweight='bold')
        ax6.set_xlabel('Time Step')
        ax6.set_ylabel('Pressure')
        ax6.legend(fontsize=8)
        ax6.grid(True, alpha=0.3)
        
        # 7. 信頼ネットワーク（最終状態）
        ax7 = fig.add_subplot(gs[2, :2])
        ax7.axis('off')
        
        trust_text = "Trust Network (Final State):\n" + "="*40 + "\n"
        for p in self.get_alive_players():
            trust_text += f"\n{p.name} ({p.role.value}):\n"
            trusted = [(self.players[tid].name, trust) for tid, trust in p.trust_map.items() 
                      if self.players[tid].is_alive and trust > 0.6]
            if trusted:
                for name, trust in sorted(trusted, key=lambda x: -x[1])[:3]:
                    trust_text += f"  → {name}: {trust:.2f}\n"
            else:
                trust_text += "  (孤立)\n"
        
        ax7.text(0.05, 0.95, trust_text, fontsize=9, family='monospace',
                verticalalignment='top', transform=ax7.transAxes)
        
        # 8. 統計
        ax8 = fig.add_subplot(gs[2, 2])
        ax8.axis('off')
        
        stats = f"""
v3.0 Statistics
{'='*30}

Days: {self.current_day}
Statements: {len(self.statements_log)}
Transitions: {len(self.phase_transition_events)}
  - Critical: {sum(1 for _, _, _, s in self.phase_transition_events if not s)}
  - Stochastic: {sum(1 for _, _, _, s in self.phase_transition_events if s)}

Final Kappa:
"""
        for p in self.get_alive_players():
            stats += f"  {p.name}: {p.state.kappa:.2f}\n"
        
        ax8.text(0.1, 0.95, stats, fontsize=9, family='monospace',
                verticalalignment='top')
        
        plt.savefig('ssd_werewolf_game_v3.png', dpi=150, bbox_inches='tight')
        print("\n💾 グラフ保存: ssd_werewolf_game_v3.png")
        plt.show()


if __name__ == "__main__":
    np.random.seed(42)  # 再現性のため
    game = WerewolfGameV3(num_players=7)
    game.simulate()
    
    print("\n" + "="*70)
    print("✅ v3.0デモ完了")
    print("="*70)
    print("\n🎓 v3.0の革新:")
    print("  1. ✅ 整合慣性（kappa）の動的更新 → AIが学習")
    print("  2. ✅ 議論フェーズと言語的意味圧 → 社会的相互作用")
    print("  3. ✅ 協働快の実装 → 同盟・派閥の自然発生")
    print("  4. ✅ 確率的跳躍モデル → 予測不可能性")
    print("\n🔬 SSD理論の完全実証:")
    print("  - 整合慣性 = 学習と経験")
    print("  - 言語的意味圧 = 社会的影響")
    print("  - 協働快 = 信頼形成")
    print("  - 確率的跳躍 = 人間的リアリティ")
