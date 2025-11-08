"""
SSD v3.5 統合デモ v4.0: 人狼ゲームAI (認知戦略版)

v3.0からの認知的跳躍:
-------------------
1. **上層構造（ペルソナ・戦略モジュール）** - 一貫した戦略
   - 潜伏型/攻撃型/リーダー型/攪乱型のペルソナ
   - 戦略が長期的行動の一貫性を生む
   - 「上層 → 中核 → 基層」の階層的制御
   
2. **思考（内的シミュレーション）** - E_indirectの消費
   - 「もしAならばB」という未来予測計算
   - 思考にコスト → E_indirect枯渇で衝動的行動
   - 反応の二段階モデルの実装
   
3. **退屈（整合駆動型探索）** - 能動的行動
   - 低意味圧が続くと「退屈」発生
   - 退屈が探索行動を駆動
   - 受動的反応 → 能動的探索
   
4. **戦略的欺瞞** - 高度な社会的運動
   - 人狼が味方に投票（村人アピール）
   - 信頼構築のための戦略的協働
   - シミュレーションに基づく複雑な判断

これにより、AIは「反応機械」から「戦略的思考者」へと跳躍する。
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


class Persona(Enum):
    """ペルソナ（上層構造）"""
    STEALTH = "潜伏型"      # 目立たず生き残る
    AGGRESSIVE = "攻撃型"   # 積極的に疑惑を向ける
    LEADER = "リーダー型"   # 場を支配する
    DISRUPTOR = "攪乱型"    # 混乱を生む


@dataclass
class Statement:
    """発言（言語的運動）"""
    speaker_id: int
    target_id: int
    intensity: float
    day: int


@dataclass
class ThoughtSimulation:
    """思考シミュレーション結果"""
    action: str  # "vote_A", "speak_against_B", etc.
    predicted_trust_change: Dict[int, float]  # 予測される信頼度変化
    predicted_suspicion_change: float  # 予測される疑惑変化
    cost: float  # E_indirect消費量


@dataclass
class WerewolfPlayerV4:
    """人狼ゲームのプレイヤー v4.0"""
    id: int
    name: str
    role: Role
    persona: Persona  # NEW! 上層構造
    
    # SSD状態
    state: SSDStateV3_5
    engine: SSDCoreEngineV3_5
    pressure_system: MultiDimensionalPressure
    
    # ゲーム状態
    is_alive: bool = True
    suspicion_level: float = 0.0
    trust_map: Dict[int, float] = field(default_factory=dict)
    social_suspicion: float = 0.0
    
    # 退屈（NEW! 整合駆動型探索）
    boredom_turns: int = 0  # 低意味圧が続いたターン数
    boredom_pressure: float = 0.0
    
    # 知識
    known_roles: Dict[int, Role] = field(default_factory=dict)
    has_revealed: bool = False
    
    # 統計
    vote_count: int = 0
    voted_for: List[int] = field(default_factory=list)
    phase_transition_count: int = 0
    total_energy_spent: float = 0.0
    statements: List[Statement] = field(default_factory=list)
    
    # 思考（NEW!）
    simulations_performed: int = 0
    thought_energy_spent: float = 0.0


def create_werewolf_pressure_v4() -> MultiDimensionalPressure:
    """人狼ゲーム用の多次元意味圧システム v4.0"""
    mdp = MultiDimensionalPressure()
    
    # 1. 疑惑圧力
    def suspicion_pressure(context: dict) -> float:
        suspicion = context.get('suspicion_level', 0.0)
        return min(1.0, suspicion / 10.0)
    
    mdp.register_dimension("suspicion", suspicion_pressure, weight=0.25, description="自分への疑惑")
    
    # 2. 社会的疑惑圧力
    def social_suspicion_pressure(context: dict) -> float:
        social = context.get('social_suspicion', 0.0)
        return min(1.0, social / 8.0)
    
    mdp.register_dimension("social_suspicion", social_suspicion_pressure, weight=0.25, description="他者からの疑惑")
    
    # 3. 信頼圧力
    def trust_pressure(context: dict) -> float:
        trust_count = context.get('trusted_count', 0)
        total = context.get('alive_count', 1)
        return 1.0 - (trust_count / max(1, total))
    
    mdp.register_dimension("trust", trust_pressure, weight=0.15, description="孤立圧力")
    
    # 4. 情報圧力
    def information_pressure(context: dict) -> float:
        unknown = context.get('unknown_roles', 0)
        total = context.get('alive_count', 1)
        return unknown / max(1, total)
    
    mdp.register_dimension("information", information_pressure, weight=0.15, description="情報不足")
    
    # 5. 時間圧力
    def time_pressure(context: dict) -> float:
        day = context.get('current_day', 1)
        max_days = context.get('max_days', 6)
        return day / max_days
    
    mdp.register_dimension("time", time_pressure, weight=0.1, description="時間切迫")
    
    # 6. 退屈圧力（NEW! 整合駆動型探索）
    def boredom_pressure(context: dict) -> float:
        boredom = context.get('boredom_pressure', 0.0)
        return min(0.5, boredom)  # 最大0.5
    
    mdp.register_dimension("boredom", boredom_pressure, weight=0.1, description="退屈（探索駆動）")
    
    return mdp


def assign_persona(role: Role, player_id: int) -> Persona:
    """役職に応じたペルソナの割り当て（上層構造）"""
    np.random.seed(player_id + 100)  # 再現性のため
    
    if role == Role.WEREWOLF:
        # 人狼: 潜伏型 or 攪乱型
        return np.random.choice([Persona.STEALTH, Persona.DISRUPTOR], p=[0.7, 0.3])
    elif role == Role.SEER:
        # 占い師: リーダー型 or 潜伏型
        return np.random.choice([Persona.LEADER, Persona.STEALTH], p=[0.6, 0.4])
    else:
        # 村人: すべての可能性
        return np.random.choice([Persona.STEALTH, Persona.AGGRESSIVE, Persona.LEADER, Persona.DISRUPTOR])


class WerewolfGameV4:
    """人狼ゲーム v4.0 - 認知戦略版"""
    
    def __init__(self, num_players: int = 7):
        self.num_players = num_players
        self.players: List[WerewolfPlayerV4] = []
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
        self.boredom_history = {i: [] for i in range(num_players)}
        self.energy_history = {i: {'direct': [], 'indirect': [], 'pressure': []} for i in range(num_players)}
        self.phase_transition_events = []
        
        self._initialize_players()
    
    def _initialize_players(self):
        """プレイヤーの初期化"""
        names = ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎", "七郎"]
        roles = [Role.WEREWOLF, Role.WEREWOLF, Role.SEER] + [Role.VILLAGER] * (self.num_players - 3)
        np.random.shuffle(roles)
        
        for i in range(self.num_players):
            persona = assign_persona(roles[i], i)
            
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
                initial_E_indirect = 150.0
                initial_kappa = 1.3
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
                initial_E_direct = 60.0
                initial_E_indirect = 200.0
                initial_kappa = 1.1
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
                initial_E_direct = 80.0
                initial_E_indirect = 130.0
                initial_kappa = 1.0
            
            player = WerewolfPlayerV4(
                id=i,
                name=names[i],
                role=roles[i],
                persona=persona,
                state=SSDStateV3_5(kappa=initial_kappa, E_direct=initial_E_direct, E_indirect=initial_E_indirect),
                engine=SSDCoreEngineV3_5(params),
                pressure_system=create_werewolf_pressure_v4()
            )
            
            for j in range(self.num_players):
                if i != j:
                    player.trust_map[j] = 0.5
            
            self.players.append(player)
    
    def log_event(self, message: str):
        self.events.append(f"[Day {self.current_day}] {message}")
        print(f"  {message}")
    
    def get_alive_players(self) -> List[WerewolfPlayerV4]:
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
    
    def update_player_energy(self, player: WerewolfPlayerV4):
        """プレイヤーのエネルギー状態を更新"""
        context = {
            'suspicion_level': player.suspicion_level,
            'social_suspicion': player.social_suspicion,
            'trusted_count': sum(1 for t in player.trust_map.values() if t > 0.7),
            'alive_count': len(self.get_alive_players()),
            'unknown_roles': len(self.get_alive_players()) - len(player.known_roles) - 1,
            'current_day': self.current_day,
            'max_days': self.max_days,
            'boredom_pressure': player.boredom_pressure,  # NEW!
        }
        
        p_external = player.pressure_system.calculate(context)
        
        # p_externalをスカラー値に変換（配列の場合は合計）
        if isinstance(p_external, (np.ndarray, list, tuple)):
            p_external_value = float(np.sum(p_external))
        else:
            p_external_value = float(p_external)
        
        # 退屈の更新（NEW! 整合駆動型探索）
        if p_external_value < 0.3:  # 低意味圧
            player.boredom_turns += 1
            player.boredom_pressure = min(0.5, player.boredom_turns * 0.1)
        else:
            player.boredom_turns = 0
            player.boredom_pressure *= 0.5  # 減衰
        
        # SSDエンジンで状態更新
        player.state = player.engine.step(player.state, p_external_value, dt=0.1)
        
        # 確率的跳躍判定
        self.check_probabilistic_jump(player, p_external_value)
        
        # 統計記録
        self.suspicion_history[player.id].append(player.suspicion_level)
        self.social_suspicion_history[player.id].append(player.social_suspicion)
        self.kappa_history[player.id].append(player.state.kappa)
        self.boredom_history[player.id].append(player.boredom_pressure)
        self.energy_history[player.id]['direct'].append(player.state.E_direct)
        self.energy_history[player.id]['indirect'].append(player.state.E_indirect)
        self.energy_history[player.id]['pressure'].append(p_external_value)
    
    def check_probabilistic_jump(self, player: WerewolfPlayerV4, p_external: float):
        """確率的跳躍判定"""
        h0 = 0.01
        gamma = 50.0
        
        if player.state.E_indirect < player.engine.params.Theta_critical:
            delta_E = player.engine.params.Theta_critical - player.state.E_indirect
            h = h0 * np.exp(delta_E / gamma)
        else:
            h = h0
        
        dt = 0.1
        jump_probability = 1.0 - np.exp(-h * dt)
        
        if np.random.random() < jump_probability:
            player.phase_transition_count += 1
            self.handle_phase_transition(player, spontaneous=(player.state.E_indirect >= player.engine.params.Theta_critical))
    
    def handle_phase_transition(self, player: WerewolfPlayerV4, spontaneous: bool = False):
        """相転移時の特殊行動"""
        if spontaneous:
            event = f"⚡ {player.name}({player.persona.value}) が突発的に跳躍！"
        else:
            event = f"⚡ {player.name}({player.persona.value}) が相転移！ (E_i={player.state.E_indirect:.1f})"
        
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
                        target.social_suspicion += 6.0
                    else:
                        target.suspicion_level -= 2.0
        
        elif player.role == Role.VILLAGER:
            if player.trust_map:
                most_trusted_id = max(player.trust_map, key=player.trust_map.get)
                most_trusted = self.players[most_trusted_id]
                if most_trusted.is_alive:
                    self.log_event(f"  😱 {player.name} がパニック！ {most_trusted.name} を疑う")
                    player.trust_map[most_trusted_id] = 0.0
                    most_trusted.suspicion_level += 3.0
                    most_trusted.social_suspicion += 2.0
        
        elif player.role == Role.WEREWOLF:
            self.log_event(f"  😈 {player.name} が強弁モード！")
            player.state.E_direct *= 1.5
    
    def thinking_phase(self, player: WerewolfPlayerV4, alive: List[WerewolfPlayerV4]) -> Optional[ThoughtSimulation]:
        """思考フェーズ（NEW! 内的シミュレーション）"""
        # E_indirectが不足していたら思考できない
        thought_cost = 20.0
        if player.state.E_indirect < thought_cost:
            return None
        
        # ペルソナに応じて思考を実行するか決定
        if player.persona == Persona.STEALTH and np.random.random() < 0.3:
            return None  # 潜伏型は思考を控える傾向
        
        # E_indirect消費
        player.state.E_indirect -= thought_cost
        player.thought_energy_spent += thought_cost
        player.simulations_performed += 1
        
        # 簡易シミュレーション: 「各候補に投票した場合の信頼度変化を予測」
        candidates = [p for p in alive if p.id != player.id]
        if not candidates:
            return None
        
        best_action = None
        best_score = -999.0
        
        for target in candidates:
            # 予測: この人に投票したら...
            predicted_trust = {}
            predicted_suspicion = 0.0
            
            # 他のプレイヤーも同じ人に投票しそうか？
            for other in alive:
                if other.id == player.id or other.id == target.id:
                    continue
                
                # 他者も疑っているか？
                if target.suspicion_level > 3.0 or target.social_suspicion > 2.0:
                    # 協働の可能性
                    predicted_trust[other.id] = player.trust_map.get(other.id, 0.5) + 0.1
                else:
                    # 孤立の可能性
                    predicted_trust[other.id] = player.trust_map.get(other.id, 0.5) - 0.05
            
            # 自分への疑惑変化を予測
            if player.role == Role.WEREWOLF and target.role == Role.WEREWOLF:
                # 味方人狼に投票 → 村人アピール成功 → 疑惑減少
                predicted_suspicion = -1.0
            elif target.suspicion_level > 5.0:
                # 明らかに疑わしい人に投票 → 疑惑減少
                predicted_suspicion = -0.5
            else:
                # 普通の人に投票 → やや疑われる
                predicted_suspicion = 0.2
            
            # スコア計算（ペルソナに応じて重み付け）
            trust_gain = sum(predicted_trust.values()) - sum(player.trust_map.values())
            
            if player.persona == Persona.LEADER:
                score = trust_gain * 2.0 - predicted_suspicion
            elif player.persona == Persona.STEALTH:
                score = -predicted_suspicion * 3.0 + trust_gain
            elif player.persona == Persona.AGGRESSIVE:
                score = -predicted_suspicion + trust_gain * 0.5
            else:  # DISRUPTOR
                score = np.random.random() * 5.0 - 2.5  # ランダム
            
            if score > best_score:
                best_score = score
                best_action = f"vote_{target.id}"
        
        return ThoughtSimulation(
            action=best_action,
            predicted_trust_change=predicted_trust,
            predicted_suspicion_change=predicted_suspicion,
            cost=thought_cost
        )
    
    def discussion_phase(self):
        """議論フェーズ"""
        self.log_event("--- 議論タイム ---")
        
        alive = self.get_alive_players()
        
        for p in alive:
            p.social_suspicion = 0.0
        
        for speaker in alive:
            # ペルソナに応じた発言判定（NEW! 上層構造による制御）
            should_speak = False
            
            if speaker.persona == Persona.LEADER:
                should_speak = speaker.state.E_direct >= 30.0  # リーダーは積極的
            elif speaker.persona == Persona.AGGRESSIVE:
                should_speak = speaker.state.E_direct >= 35.0
            elif speaker.persona == Persona.STEALTH:
                should_speak = speaker.state.E_direct >= 60.0  # 潜伏型は慎重
            elif speaker.persona == Persona.DISRUPTOR:
                should_speak = speaker.state.E_direct >= 40.0 or speaker.boredom_pressure > 0.3  # 退屈でも発言
            
            # 退屈圧力が高いと能動的に発言（NEW! 整合駆動型探索）
            if speaker.boredom_pressure > 0.4:
                should_speak = True
                self.log_event(f"  💤 {speaker.name} が退屈から発言を仕掛ける")
            
            if not should_speak:
                continue
            
            candidates = [p for p in alive if p.id != speaker.id]
            if not candidates:
                continue
            
            # 発言対象の選択
            reasoning_quality = min(1.0, (speaker.state.E_indirect / 200.0) * speaker.state.kappa)
            noise_factor = (1.0 - reasoning_quality) * 5.0
            
            if speaker.role == Role.WEREWOLF:
                non_werewolves = [p for p in candidates if p.role != Role.WEREWOLF]
                if non_werewolves:
                    target = np.random.choice(non_werewolves)
                else:
                    continue
            else:
                target = max(candidates, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
            
            intensity = min(3.0, speaker.state.E_direct / 50.0)
            energy_cost = 20.0 + intensity * 5.0
            
            statement = Statement(
                speaker_id=speaker.id,
                target_id=target.id,
                intensity=intensity,
                day=self.current_day
            )
            speaker.statements.append(statement)
            self.statements_log.append(statement)
            
            speaker.state.E_direct -= energy_cost
            speaker.total_energy_spent += energy_cost
            
            target.social_suspicion += intensity * 1.5
            
            self.log_event(f"  💬 {speaker.name}({speaker.persona.value}) が {target.name} を疑う (強度: {intensity:.2f})")
    
    def day_phase(self):
        """昼フェーズ"""
        self.log_event(f"=== Day {self.current_day}: 昼フェーズ ===")
        
        alive = self.get_alive_players()
        
        # 1. エネルギー更新
        for player in alive:
            self.update_player_energy(player)
        
        # 2. 議論
        self.discussion_phase()
        
        # 3. 投票
        self.log_event("--- 投票タイム ---")
        votes = self._conduct_vote(alive)
        
        # 4. 処刑と学習
        if votes:
            executed_id = max(votes, key=votes.get)
            executed = self.players[executed_id]
            self.log_event(f"💀 {executed.name}({executed.persona.value}) が処刑 ({executed.role.value})")
            executed.is_alive = False
            self.execution_history.append(executed.id)
            
            self.learning_phase(executed, votes)
    
    def learning_phase(self, executed: WerewolfPlayerV4, votes: Dict[int, float]):
        """学習フェーズ"""
        self.log_event("--- 学習フェーズ ---")
        
        is_werewolf = (executed.role == Role.WEREWOLF)
        
        for player in self.get_alive_players():
            if executed.id in player.voted_for:
                if is_werewolf:
                    delta_kappa = 0.15
                    player.state.kappa += delta_kappa
                    player.state.kappa = min(2.0, player.state.kappa)
                    self.log_event(f"  ✅ {player.name} 成功！ κ: {player.state.kappa:.2f}")
                else:
                    delta_kappa = -0.10
                    player.state.kappa += delta_kappa
                    player.state.kappa = max(0.3, player.state.kappa)
                    self.log_event(f"  ❌ {player.name} 失敗... κ: {player.state.kappa:.2f}")
    
    def _conduct_vote(self, alive: List[WerewolfPlayerV4]) -> Dict[int, float]:
        """投票（思考シミュレーション統合）"""
        votes = {p.id: 0.0 for p in alive}
        voted_targets = {}
        
        for voter in alive:
            # 思考フェーズ（NEW! 内的シミュレーション）
            simulation = self.thinking_phase(voter, alive)
            
            if simulation:
                # シミュレーション結果を使用
                self.log_event(f"  🧠 {voter.name} が思考シミュレーション実行")
                target_id = int(simulation.action.split("_")[1])
                target = self.players[target_id]
            else:
                # E_indirect不足 → 短絡的判断
                target = self._select_vote_target_simple(voter, alive)
            
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
                vote_power = min(3.0, (voter.state.E_direct / 100.0) * voter.state.kappa)
                energy_cost = 30.0 + vote_power * 10.0
            
            votes[target.id] += vote_power
            target.vote_count += 1
            voter.voted_for.append(target.id)
            voted_targets[voter.id] = target.id
            
            actual_cost = min(energy_cost, voter.state.E_direct * 0.9)
            voter.state.E_direct -= actual_cost
            voter.total_energy_spent += actual_cost
            
            self.log_event(f"  {voter.name}({voter.persona.value}) → {target.name} (強さ: {vote_power:.2f}, κ={voter.state.kappa:.2f})")
            
            target.suspicion_level += vote_power * 1.0
        
        # 協働快
        self.process_cooperation(voted_targets, alive)
        
        return votes
    
    def _select_vote_target_simple(self, voter: WerewolfPlayerV4, alive: List[WerewolfPlayerV4]) -> Optional[WerewolfPlayerV4]:
        """単純な投票先選択（思考なし）"""
        candidates = [p for p in alive if p.id != voter.id]
        if not candidates:
            return None
        
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
            untrusted = [p for p in candidates if voter.trust_map.get(p.id, 0.5) < 0.6]
            if untrusted:
                target = max(untrusted, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
            else:
                target = max(candidates, key=lambda p: p.suspicion_level + p.social_suspicion + np.random.random() * noise_factor)
        
        return target
    
    def process_cooperation(self, voted_targets: Dict[int, int], alive: List[WerewolfPlayerV4]):
        """協働快の処理"""
        self.log_event("--- 協働快 ---")
        
        for player_a in alive:
            if player_a.id not in voted_targets:
                continue
            
            target_of_a = voted_targets[player_a.id]
            
            for player_b in alive:
                if player_a.id == player_b.id or player_b.id not in voted_targets:
                    continue
                
                target_of_b = voted_targets[player_b.id]
                
                if target_of_a == target_of_b:
                    old_trust = player_a.trust_map.get(player_b.id, 0.5)
                    player_a.trust_map[player_b.id] = min(1.0, old_trust + 0.15)
                    self.log_event(f"  🤝 {player_a.name} ⇔ {player_b.name} (信頼: {player_a.trust_map[player_b.id]:.2f})")
                elif target_of_b == player_a.id:
                    old_trust = player_a.trust_map.get(player_b.id, 0.5)
                    player_a.trust_map[player_b.id] = max(0.0, old_trust - 0.3)
                    self.log_event(f"  💔 {player_a.name} ← {player_b.name} (信頼: {player_a.trust_map[player_b.id]:.2f})")
    
    def night_phase(self):
        """夜フェーズ"""
        self.log_event(f"=== Day {self.current_day}: 夜のフェーズ ===")
        
        alive = self.get_alive_players()
        
        werewolves = [p for p in alive if p.role == Role.WEREWOLF]
        if werewolves:
            active_werewolf = max(werewolves, key=lambda w: w.state.E_direct)
            
            non_werewolves = [p for p in alive if p.role != Role.WEREWOLF]
            if non_werewolves:
                if active_werewolf.state.E_direct >= 50.0:
                    target = min(non_werewolves, key=lambda p: p.suspicion_level + np.random.random())
                    self.log_event(f"🌙 {active_werewolf.name} が {target.name}({target.role.value}) を襲撃")
                    energy_cost = 50.0
                elif active_werewolf.state.E_direct >= 20.0:
                    target = np.random.choice(non_werewolves)
                    self.log_event(f"🌙 {active_werewolf.name} が {target.name} を弱い襲撃")
                    energy_cost = 20.0
                else:
                    self.log_event(f"🌙 人狼エネルギー不足")
                    return
                
                target.is_alive = False
                self.attack_history.append(target.id)
                active_werewolf.state.E_direct -= energy_cost
        
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
                    seer.state.kappa += 0.1
    
    def simulate(self):
        """ゲームシミュレーション実行"""
        print("="*70)
        print("SSD v4.0 統合デモ: 人狼ゲームAI (認知戦略版)")
        print("="*70)
        
        print("\n[初期配置]")
        for p in self.players:
            print(f"  {p.name}: {p.role.value} / {p.persona.value} (E_d={p.state.E_direct:.0f}, E_i={p.state.E_indirect:.0f}, κ={p.state.kappa:.1f})")
        
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
        print("📊 v4.0 最終結果")
        print("="*70)
        
        print("\n[生存者]")
        for p in self.get_alive_players():
            print(f"  {p.name} ({p.role.value} / {p.persona.value})")
            print(f"    kappa: {p.state.kappa:.2f}, 思考: {p.simulations_performed}回")
        
        print("\n[犠牲者]")
        for p in self.players:
            if not p.is_alive:
                cause = "処刑" if p.id in self.execution_history else "襲撃"
                print(f"  {p.name} ({p.role.value} / {p.persona.value}) - {cause}")
        
        print(f"\n[統計]")
        print(f"  相転移: {len(self.phase_transition_events)}回")
        print(f"  発言: {len(self.statements_log)}回")
        total_thoughts = sum(p.simulations_performed for p in self.players)
        print(f"  思考: {total_thoughts}回")
    
    def visualize(self):
        """結果の可視化"""
        fig = plt.figure(figsize=(22, 16))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        # 1. Kappa
        ax1 = fig.add_subplot(gs[0, 0])
        for p in self.players:
            if self.kappa_history[p.id]:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax1.plot(self.kappa_history[p.id], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax1.set_title('Kappa (Learning)', fontweight='bold')
        ax1.legend(fontsize=7)
        ax1.grid(True, alpha=0.3)
        
        # 2. Boredom
        ax2 = fig.add_subplot(gs[0, 1])
        for p in self.players:
            if self.boredom_history[p.id]:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax2.plot(self.boredom_history[p.id], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax2.set_title('Boredom Pressure', fontweight='bold')
        ax2.legend(fontsize=7)
        ax2.grid(True, alpha=0.3)
        
        # 3. E_indirect
        ax3 = fig.add_subplot(gs[0, 2])
        for p in self.players:
            if self.energy_history[p.id]['indirect']:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax3.plot(self.energy_history[p.id]['indirect'], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax3.set_title('E_indirect (Thought)', fontweight='bold')
        ax3.legend(fontsize=7)
        ax3.grid(True, alpha=0.3)
        
        # 4. E_direct
        ax4 = fig.add_subplot(gs[0, 3])
        for p in self.players:
            if self.energy_history[p.id]['direct']:
                color = 'red' if p.role == Role.WEREWOLF else 'blue' if p.role == Role.SEER else 'green'
                ax4.plot(self.energy_history[p.id]['direct'], label=p.name, color=color, linewidth=2, alpha=0.7)
        ax4.set_title('E_direct (Action)', fontweight='bold')
        ax4.legend(fontsize=7)
        ax4.grid(True, alpha=0.3)
        
        # 5-8: その他のグラフ（省略）
        
        plt.savefig('ssd_werewolf_game_v4.png', dpi=150, bbox_inches='tight')
        print("\n💾 グラフ保存: ssd_werewolf_game_v4.png")
        plt.show()


if __name__ == "__main__":
    np.random.seed(42)
    game = WerewolfGameV4(num_players=7)
    game.simulate()
    
    print("\n" + "="*70)
    print("✅ v4.0デモ完了")
    print("="*70)
    print("\n🎓 v4.0の認知的跳躍:")
    print("  1. ✅ 上層構造（ペルソナ）→ 戦略的一貫性")
    print("  2. ✅ 思考（シミュレーション）→ E_indirect消費")
    print("  3. ✅ 退屈（探索駆動）→ 能動的行動")
    print("  4. ✅ 戦略的欺瞞 → 高度な社会的運動")
    print("\n🔬 SSD理論の完全実証:")
    print("  - 上層構造 → 中核 → 基層の階層制御")
    print("  - 思考 = 内的シミュレーション（エネルギー消費）")
    print("  - 退屈 = 整合駆動型探索")
    print("  - 反応機械 → 戦略的思考者への跳躍")
