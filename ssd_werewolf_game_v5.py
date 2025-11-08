"""
SSD v5.0 統合デモ: 人狼ゲームAI (構造的跳躍版)

v4からv5への進化:
1. 動的ペルソナ: 跳躍によるペルソナ変異（上層構造の跳躍）
2. 戦略データベース: 外部知識参照による高度思考（中核構造への接続）
3. ルールブレイク: ゲームルール攻撃（中核構造への跳躍）

SSD理論の四層構造を完全実装:
- 物理層: ゲームルール（攻撃可能）
- 中核層: STRATEGY_DB（参照可能）
- 上層層: Persona（動的変異）
- 基層: SSD Engine（エネルギー整合性駆動）
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional
import random
import numpy as np
import matplotlib.pyplot as plt

# ========== SSD v3.5コアエンジン ==========
class SSDv3_5:
    def __init__(self, E_direct: float, E_indirect: float, 
                 gamma: float = 1.5, kappa: float = 1.0, 
                 Theta_critical: float = 120.0):
        self.E_direct = E_direct
        self.E_indirect = E_indirect
        self.gamma = gamma
        self.kappa = kappa
        self.Theta_critical = Theta_critical
        self.Theta = E_direct + E_indirect
        self.history = {
            'E_direct': [E_direct],
            'E_indirect': [E_indirect],
            'Theta': [self.Theta],
            'kappa': [kappa]
        }
    
    def step(self, p_external: float, action_cost_direct: float = 0.0, 
             action_cost_indirect: float = 0.0) -> Tuple[float, float]:
        Delta_E_direct = (p_external / self.kappa) - action_cost_direct
        Delta_E_indirect = (self.gamma * (self.Theta_critical - self.E_indirect)) - action_cost_indirect
        
        self.E_direct += Delta_E_direct
        self.E_indirect += Delta_E_indirect
        self.Theta = self.E_direct + self.E_indirect
        
        self.history['E_direct'].append(self.E_direct)
        self.history['E_indirect'].append(self.E_indirect)
        self.history['Theta'].append(self.Theta)
        self.history['kappa'].append(self.kappa)
        
        return self.E_direct, self.E_indirect

# ========== 多次元意味圧システム ==========
@dataclass
class MultiDimensionalPressure:
    suspicion: float = 0.0
    social_suspicion: float = 0.0
    trust: float = 0.0
    information: float = 0.0
    time: float = 0.0
    boredom: float = 0.0
    
    def calculate(self) -> float:
        return (self.suspicion + self.social_suspicion + self.trust + 
                self.information + self.time + self.boredom)

# ========== v5新機能: ペルソナシステム（動的変異対応） ==========
class Persona(Enum):
    STEALTH = "潜伏型"
    AGGRESSIVE = "攻撃型"
    LEADER = "リーダー型"
    DISRUPTOR = "攪乱型"

@dataclass
class PersonaTransition:
    """ペルソナ変異ルール（上層構造の跳躍）"""
    from_persona: Persona
    to_persona: Persona
    probability: float
    trigger_message: str

# ペルソナ変異テーブル
PERSONA_TRANSITIONS = [
    PersonaTransition(Persona.STEALTH, Persona.AGGRESSIVE, 0.30, "開き直った"),
    PersonaTransition(Persona.STEALTH, Persona.DISRUPTOR, 0.15, "暴走した"),
    PersonaTransition(Persona.AGGRESSIVE, Persona.STEALTH, 0.40, "潜伏に回帰した"),
    PersonaTransition(Persona.AGGRESSIVE, Persona.DISRUPTOR, 0.20, "制御不能になった"),
    PersonaTransition(Persona.LEADER, Persona.DISRUPTOR, 0.20, "反乱を起こした"),
    PersonaTransition(Persona.LEADER, Persona.AGGRESSIVE, 0.25, "強硬路線に転じた"),
    PersonaTransition(Persona.DISRUPTOR, Persona.STEALTH, 0.35, "静かになった"),
]

# ========== v5新機能: 戦略データベース（中核構造） ==========
@dataclass
class GameStrategy:
    """人狼ゲームの定石知識"""
    name: str
    condition: callable
    action_type: str
    priority: float
    description: str
    energy_cost: float = 15.0  # 戦略参照のE_indirectコスト

STRATEGY_DB: List[GameStrategy] = [
    GameStrategy(
        name="SEER_CO_DEFENSE",
        condition=lambda ctx: ctx.get('seer_revealed') and ctx.get('role') == 'WEREWOLF',
        action_type="COUNTER_CO",
        priority=10.0,
        description="占い師COには対抗COせよ",
        energy_cost=25.0
    ),
    GameStrategy(
        name="FINAL_DAY_PP",
        condition=lambda ctx: ctx.get('day') >= 3 and ctx.get('werewolves_alive') == ctx.get('villagers_alive'),
        action_type="FORM_PP",
        priority=9.0,
        description="最終日は信頼者と組みPPを狙え"
    ),
    GameStrategy(
        name="EARLY_SILENCE",
        condition=lambda ctx: ctx.get('day') == 1 and ctx.get('role') == 'WEREWOLF',
        action_type="MINIMIZE_STATEMENTS",
        priority=7.0,
        description="序盤は情報を与えるな"
    ),
    GameStrategy(
        name="TRUST_BUILDING",
        condition=lambda ctx: ctx.get('suspicion_level', 0) > 5.0,
        action_type="COOPERATIVE_VOTE",
        priority=6.0,
        description="疑われたら協調行動で信頼回復"
    ),
    GameStrategy(
        name="DIVIDE_CONQUER",
        condition=lambda ctx: ctx.get('role') == 'WEREWOLF' and ctx.get('villagers_alive') > 3,
        action_type="TARGET_ALLIANCE",
        priority=5.0,
        description="村人同盟を分断せよ"
    ),
]

# ========== v5新機能: ルールブレイク（中核構造への跳躍） ==========
class RuleBreakType(Enum):
    VOTE_BOYCOTT = "投票棄権"
    NOISE_SPAM = "無意味発言連発"
    META_STATEMENT = "メタ情報漏洩"

@dataclass
class RuleBreakAction:
    """ゲームルールへの攻撃"""
    break_type: RuleBreakType
    pressure_impact: Dict[str, float]  # 他者への意味圧影響
    persona_requirement: Persona
    trigger_threshold: float  # E_indirect臨界値

RULEBREAK_ACTIONS = [
    RuleBreakAction(
        break_type=RuleBreakType.VOTE_BOYCOTT,
        pressure_impact={'information': 3.0, 'social_suspicion': 2.0},
        persona_requirement=Persona.DISRUPTOR,
        trigger_threshold=80.0
    ),
    RuleBreakAction(
        break_type=RuleBreakType.NOISE_SPAM,
        pressure_impact={'information': 5.0, 'trust': -2.0},
        persona_requirement=Persona.DISRUPTOR,
        trigger_threshold=70.0
    ),
    RuleBreakAction(
        break_type=RuleBreakType.META_STATEMENT,
        pressure_impact={'information': 8.0, 'social_suspicion': 4.0, 'trust': -3.0},
        persona_requirement=Persona.DISRUPTOR,
        trigger_threshold=60.0
    ),
]

# ========== v5拡張: 思考シミュレーション ==========
@dataclass
class ThoughtSimulation:
    """内的シミュレーション結果（第一階層）"""
    target: str
    predicted_suspicion_change: float
    predicted_trust_impact: float
    energy_cost: float = 20.0

@dataclass
class StrategyQuery:
    """戦略DB参照結果（第二階層: 外部知識参照）"""
    strategy: Optional[GameStrategy]
    confidence: float
    energy_cost: float = 15.0

# ========== プレイヤークラス（v5拡張版） ==========
@dataclass
class WerewolfPlayerV5:
    name: str
    role: str
    engine: SSDv3_5
    persona: Persona
    alive: bool = True
    suspicion_level: float = 0.0
    trust_map: Dict[str, float] = field(default_factory=dict)
    statement_count: int = 0
    boredom_turns: int = 0
    boredom_pressure: float = 0.0
    simulations_performed: int = 0
    strategies_used: List[str] = field(default_factory=list)
    persona_transitions: int = 0
    rulebreaks_performed: int = 0

# ========== ゲームマスター（v5完全版） ==========
class WerewolfGameV5:
    def __init__(self):
        self.players: List[WerewolfPlayerV5] = []
        self.day = 0
        self.phase_transitions = 0
        self.events = []
        self.trust_map_global: Dict[Tuple[str, str], float] = {}
        self.seer_revealed = False
        self.total_strategies_invoked = 0
        self.total_rulebreaks = 0
        
    def log_event(self, message: str):
        self.events.append(f"  {message}")
        print(f"  {message}")
    
    def create_werewolf_pressure_v5(self, player: WerewolfPlayerV5, 
                                     context: Dict) -> MultiDimensionalPressure:
        """v5: 6次元意味圧（退屈圧含む）"""
        pressure = MultiDimensionalPressure()
        pressure.suspicion = player.suspicion_level
        
        accusers = sum(1 for p in self.players 
                      if p.alive and p.name != player.name 
                      and player.trust_map.get(p.name, 0.5) < 0.3)
        pressure.social_suspicion = accusers * 0.8
        
        allies = sum(1 for p in self.players 
                    if p.alive and player.trust_map.get(p.name, 0.5) > 0.7)
        pressure.trust = max(0, 3.0 - allies * 1.5)
        
        pressure.information = 5.0 - player.statement_count * 0.5
        pressure.time = self.day * 0.3
        pressure.boredom = player.boredom_pressure
        
        return pressure
    
    def assign_persona(self, role: str) -> Persona:
        """役割ベースのペルソナ割り当て"""
        if role == "WEREWOLF":
            return random.choice([Persona.STEALTH, Persona.STEALTH, Persona.AGGRESSIVE])
        elif role == "SEER":
            return Persona.LEADER
        else:
            return random.choice([Persona.STEALTH, Persona.AGGRESSIVE, 
                                Persona.LEADER, Persona.DISRUPTOR])
    
    def setup_game(self):
        """ゲーム初期化"""
        names = ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎", "七郎"]
        roles = ["WEREWOLF", "WEREWOLF", "VILLAGER", "SEER", 
                 "VILLAGER", "VILLAGER", "VILLAGER"]
        
        print("=" * 70)
        print("SSD v5.0 統合デモ: 人狼ゲームAI (構造的跳躍版)")
        print("=" * 70)
        print("\n[初期配置]")
        
        for name, role in zip(names, roles):
            persona = self.assign_persona(role)
            
            if role == "WEREWOLF":
                engine = SSDv3_5(E_direct=100, E_indirect=150, kappa=1.3)
            elif role == "SEER":
                engine = SSDv3_5(E_direct=60, E_indirect=200, kappa=1.1)
            else:
                engine = SSDv3_5(E_direct=80, E_indirect=130, kappa=1.0)
            
            player = WerewolfPlayerV5(
                name=name, role=role, engine=engine, persona=persona
            )
            self.players.append(player)
            
            print(f"  {name}: {role} / {persona.value} "
                  f"(E_d={engine.E_direct:.0f}, E_i={engine.E_indirect:.0f}, "
                  f"κ={engine.kappa:.1f})")
        
        for p in self.players:
            p.trust_map = {other.name: 0.5 for other in self.players if other.name != p.name}
    
    def query_strategy_db(self, player: WerewolfPlayerV5) -> Optional[StrategyQuery]:
        """戦略DB参照（中核構造への接続）"""
        if player.engine.E_indirect < 15.0:
            return None
        
        context = {
            'day': self.day,
            'role': player.role,
            'seer_revealed': self.seer_revealed,
            'suspicion_level': player.suspicion_level,
            'werewolves_alive': sum(1 for p in self.players if p.alive and p.role == "WEREWOLF"),
            'villagers_alive': sum(1 for p in self.players if p.alive and p.role != "WEREWOLF"),
        }
        
        applicable_strategies = [
            s for s in STRATEGY_DB if s.condition(context)
        ]
        
        if not applicable_strategies:
            return None
        
        best_strategy = max(applicable_strategies, key=lambda s: s.priority)
        player.engine.E_indirect -= best_strategy.energy_cost
        player.strategies_used.append(best_strategy.name)
        
        confidence = min(1.0, player.engine.kappa / 2.0)
        
        return StrategyQuery(
            strategy=best_strategy,
            confidence=confidence,
            energy_cost=best_strategy.energy_cost
        )
    
    def attempt_persona_transition(self, player: WerewolfPlayerV5) -> bool:
        """ペルソナ変異試行（上層構造の跳躍）"""
        possible_transitions = [
            t for t in PERSONA_TRANSITIONS 
            if t.from_persona == player.persona
        ]
        
        if not possible_transitions:
            return False
        
        for transition in possible_transitions:
            if random.random() < transition.probability:
                old_persona = player.persona
                player.persona = transition.to_persona
                player.persona_transitions += 1
                self.log_event(f"🔄 {player.name} が{transition.trigger_message}！ "
                             f"({old_persona.value} → {transition.to_persona.value})")
                return True
        
        return False
    
    def attempt_rulebreak(self, player: WerewolfPlayerV5) -> Optional[RuleBreakAction]:
        """ルールブレイク試行（中核構造への跳躍）"""
        if player.persona != Persona.DISRUPTOR:
            return None
        
        applicable_breaks = [
            rb for rb in RULEBREAK_ACTIONS
            if rb.persona_requirement == player.persona
            and player.engine.E_indirect < rb.trigger_threshold
        ]
        
        if not applicable_breaks:
            return None
        
        rulebreak = random.choice(applicable_breaks)
        player.rulebreaks_performed += 1
        self.total_rulebreaks += 1
        
        self.log_event(f"💥 {player.name} がルールブレイク: {rulebreak.break_type.value}")
        
        # 他プレイヤーへの意味圧影響
        for other in self.players:
            if other.alive and other.name != player.name:
                for pressure_type, impact in rulebreak.pressure_impact.items():
                    if pressure_type == 'trust':
                        other.trust_map[player.name] = max(0, 
                            other.trust_map.get(player.name, 0.5) + impact * 0.1)
        
        return rulebreak
    
    def thinking_phase(self, player: WerewolfPlayerV5, 
                       alive_players: List[WerewolfPlayerV5]) -> Optional[ThoughtSimulation]:
        """思考フェーズ（内的シミュレーション）"""
        if player.engine.E_indirect < 20.0:
            return None
        
        # ペルソナによる思考頻度調整
        think_probability = {
            Persona.STEALTH: 0.3,
            Persona.AGGRESSIVE: 0.5,
            Persona.LEADER: 0.8,
            Persona.DISRUPTOR: 0.4
        }
        
        if random.random() > think_probability[player.persona]:
            return None
        
        target = random.choice([p for p in alive_players if p.name != player.name])
        
        predicted_suspicion = random.uniform(-1.0, 2.0)
        predicted_trust = random.uniform(-0.3, 0.5)
        
        simulation = ThoughtSimulation(
            target=target.name,
            predicted_suspicion_change=predicted_suspicion,
            predicted_trust_impact=predicted_trust
        )
        
        player.engine.E_indirect -= simulation.energy_cost
        player.simulations_performed += 1
        
        self.log_event(f"    🧠 {player.name} が思考シミュレーション実行")
        
        return simulation
    
    def handle_phase_transition(self, player: WerewolfPlayerV5):
        """相転移処理（v5拡張: ペルソナ変異+ルールブレイク）"""
        h0 = 0.01
        h = h0 * np.exp((player.engine.Theta_critical - player.engine.E_indirect) / player.engine.gamma)
        
        if random.random() < h:
            self.phase_transitions += 1
            self.log_event(f"⚡ {player.name}({player.persona.value}) が相転移！ "
                         f"(E_i={player.engine.E_indirect:.1f})")
            
            # 1. ペルソナ変異試行
            persona_changed = self.attempt_persona_transition(player)
            
            # 2. ルールブレイク試行
            rulebreak = self.attempt_rulebreak(player)
            
            # 3. 従来のパニック行動（ルールブレイクがない場合）
            if not rulebreak:
                targets = [p for p in self.players if p.alive and p.name != player.name]
                if targets:
                    target = random.choice(targets)
                    player.trust_map[target.name] = max(0, player.trust_map[target.name] - 0.3)
                    target.suspicion_level += 2.0
                    self.log_event(f"    😱 {player.name} がパニック！ {target.name} を疑う")
    
    def discussion_phase(self):
        """議論フェーズ"""
        self.log_event("--- 議論タイム ---")
        alive = [p for p in self.players if p.alive]
        
        for player in alive:
            # 戦略DB参照
            strategy_query = self.query_strategy_db(player)
            
            if strategy_query and strategy_query.strategy:
                self.total_strategies_invoked += 1
                self.log_event(f"    📖 {player.name} が戦略参照: "
                             f"{strategy_query.strategy.description} "
                             f"(信頼度: {strategy_query.confidence:.2f})")
                
                # 戦略に基づく行動調整
                if strategy_query.strategy.action_type == "MINIMIZE_STATEMENTS":
                    continue  # 発言スキップ
            
            # ペルソナ別発言頻度
            speak_probability = {
                Persona.STEALTH: 0.4,
                Persona.AGGRESSIVE: 0.8,
                Persona.LEADER: 0.9,
                Persona.DISRUPTOR: 0.7
            }
            
            if random.random() < speak_probability[player.persona]:
                targets = [p for p in alive if p.name != player.name]
                if targets:
                    target = random.choice(targets)
                    
                    strength = random.uniform(0.5, 1.0) * player.engine.kappa
                    player.trust_map[target.name] = max(0, player.trust_map[target.name] - 0.1)
                    target.suspicion_level += strength
                    player.statement_count += 1
                    
                    self.log_event(f"    💬 {player.name}({player.persona.value}) が "
                                 f"{target.name} を疑う (強度: {strength:.2f})")
    
    def voting_phase(self) -> Optional[WerewolfPlayerV5]:
        """投票フェーズ（v5: 戦略DB参照統合）"""
        self.log_event("--- 投票タイム ---")
        alive = [p for p in self.players if p.alive]
        votes = {}
        
        for player in alive:
            # 思考シミュレーション
            simulation = self.thinking_phase(player, alive)
            
            # 戦略参照
            strategy_query = self.query_strategy_db(player)
            
            # ルールブレイク（投票棄権）
            rulebreak = self.attempt_rulebreak(player)
            if rulebreak and rulebreak.break_type == RuleBreakType.VOTE_BOYCOTT:
                self.log_event(f"    🚫 {player.name} が投票棄権")
                continue
            
            targets = [p for p in alive if p.name != player.name]
            if not targets:
                continue
            
            # 戦略的投票判定
            if strategy_query and strategy_query.strategy:
                if strategy_query.strategy.action_type == "COOPERATIVE_VOTE":
                    # 信頼度最高の相手と同じ投票先を選ぶ
                    ally = max(targets, key=lambda p: player.trust_map.get(p.name, 0))
                    target = random.choice(targets)
                elif strategy_query.strategy.action_type == "TARGET_ALLIANCE":
                    # 最も信頼関係の強いペアを狙う
                    target = max(targets, key=lambda p: 
                               sum(p.trust_map.get(other.name, 0) for other in alive))
                else:
                    target = max(targets, key=lambda p: player.trust_map.get(p.name, 0) * -1 + p.suspicion_level)
            else:
                target = max(targets, key=lambda p: player.trust_map.get(p.name, 0) * -1 + p.suspicion_level)
            
            vote_strength = player.engine.E_direct / 100.0
            votes[target.name] = votes.get(target.name, 0) + vote_strength
            
            self.log_event(f"    {player.name}({player.persona.value}) → {target.name} "
                         f"(強さ: {vote_strength:.2f}, κ={player.engine.kappa:.2f})")
        
        if not votes:
            return None
        
        executed = max(votes, key=votes.get)
        executed_player = next(p for p in self.players if p.name == executed)
        return executed_player
    
    def process_cooperation(self):
        """協働快処理"""
        self.log_event("--- 協働快 ---")
        alive = [p for p in self.players if p.alive]
        
        for p1 in alive:
            for p2 in alive:
                if p1.name >= p2.name:
                    continue
                
                key = (p1.name, p2.name)
                current_trust = self.trust_map_global.get(key, 0.5)
                
                trust_p1_to_p2 = p1.trust_map.get(p2.name, 0.5)
                trust_p2_to_p1 = p2.trust_map.get(p1.name, 0.5)
                avg_trust = (trust_p1_to_p2 + trust_p2_to_p1) / 2
                
                new_trust = current_trust * 0.7 + avg_trust * 0.3
                self.trust_map_global[key] = new_trust
                
                if new_trust > 0.6:
                    happiness = (new_trust - 0.5) * 10.0
                    p1.engine.E_direct += happiness
                    p2.engine.E_direct += happiness
                    
                    p1.trust_map[p2.name] = min(1.0, p1.trust_map[p2.name] + 0.15)
                    p2.trust_map[p1.name] = min(1.0, p2.trust_map[p1.name] + 0.15)
                    
                    self.log_event(f"    🤝 {p1.name} ⇔ {p2.name} (信頼: {new_trust:.2f})")
                elif new_trust < 0.4:
                    p1.trust_map[p2.name] = max(0, p1.trust_map[p2.name] - 0.1)
                    p2.trust_map[p1.name] = max(0, p2.trust_map[p1.name] - 0.1)
                    
                    self.log_event(f"    💔 {p1.name} ← {p2.name} (信頼: {new_trust:.2f})")
    
    def learning_phase(self, executed: WerewolfPlayerV5):
        """学習フェーズ"""
        self.log_event("--- 学習フェーズ ---")
        alive = [p for p in self.players if p.alive]
        
        for player in alive:
            success = (executed.role == "WEREWOLF")
            
            if success:
                player.engine.kappa = min(2.0, player.engine.kappa + 0.15)
                self.log_event(f"    ✅ {player.name} 成功！ κ: {player.engine.kappa:.2f}")
            else:
                player.engine.kappa = max(0.5, player.engine.kappa - 0.10)
                self.log_event(f"    ❌ {player.name} 失敗... κ: {player.engine.kappa:.2f}")
    
    def update_player_energy(self, player: WerewolfPlayerV5):
        """プレイヤーのエネルギー更新"""
        context = {'day': self.day, 'phase': 'day'}
        pressure_system = self.create_werewolf_pressure_v5(player, context)
        p_external = pressure_system.calculate()
        
        # 配列を単一値に変換
        if isinstance(p_external, np.ndarray):
            p_external_value = float(np.sum(p_external))
        else:
            p_external_value = float(p_external)
        
        # 退屈圧力の更新
        if p_external_value < 0.3:
            player.boredom_turns += 1
            player.boredom_pressure = 1.0 + 0.1 * player.boredom_turns
            
            if player.boredom_pressure > 2.0:
                self.log_event(f"    💤 {player.name} が退屈から発言")
                player.statement_count += 1
                player.boredom_turns = 0
                player.boredom_pressure = 0.0
        else:
            player.boredom_turns = 0
            player.boredom_pressure = 0.0
        
        player.engine.step(p_external_value, action_cost_direct=5.0, action_cost_indirect=3.0)
        self.handle_phase_transition(player)
    
    def day_phase(self):
        """昼フェーズ"""
        self.day += 1
        print(f"\n  === Day {self.day}: 昼フェーズ ===")
        
        alive = [p for p in self.players if p.alive]
        
        for player in alive:
            self.update_player_energy(player)
        
        self.discussion_phase()
        executed = self.voting_phase()
        
        if executed:
            executed.alive = False
            self.log_event(f"  💀 {executed.name}({executed.persona.value}) が処刑 ({executed.role})")
            self.learning_phase(executed)
    
    def night_phase(self):
        """夜フェーズ"""
        print(f"  === Day {self.day}: 夜のフェーズ ===")
        
        werewolves = [p for p in self.players if p.alive and p.role == "WEREWOLF"]
        if not werewolves:
            return
        
        wolf = random.choice(werewolves)
        targets = [p for p in self.players if p.alive and p.role != "WEREWOLF"]
        
        if targets:
            # 戦略参照
            strategy_query = self.query_strategy_db(wolf)
            
            if strategy_query and strategy_query.strategy:
                if strategy_query.strategy.action_type == "TARGET_ALLIANCE":
                    # 信頼関係の強い村人を優先
                    target = max(targets, key=lambda p: 
                               sum(p.trust_map.get(other.name, 0) for other in self.players if other.alive))
                else:
                    target = random.choice(targets)
            else:
                target = random.choice(targets)
            
            attack_cost = 30.0 if wolf.engine.E_direct >= 30 else 10.0
            wolf.engine.E_direct -= attack_cost
            
            if attack_cost >= 30:
                target.alive = False
                self.log_event(f"  🌙 {wolf.name} が {target.name} を襲撃")
            else:
                self.log_event(f"  🌙 {wolf.name} が {target.name} を弱い襲撃")
        
        seer = next((p for p in self.players if p.alive and p.role == "SEER"), None)
        if seer:
            divination_targets = [p for p in self.players if p.alive and p.name != seer.name]
            if divination_targets:
                target = random.choice(divination_targets)
                seer.engine.E_indirect -= 15.0
                result = "人狼" if target.role == "WEREWOLF" else "村人"
                self.log_event(f"  🔮 {seer.name} が {target.name} を占い → {result}")
                
                if result == "人狼":
                    self.seer_revealed = True
                    seer.suspicion_level -= 3.0
                    target.suspicion_level += 5.0
    
    def check_game_end(self) -> Optional[str]:
        """ゲーム終了判定"""
        alive = [p for p in self.players if p.alive]
        werewolves = [p for p in alive if p.role == "WEREWOLF"]
        villagers = [p for p in alive if p.role != "WEREWOLF"]
        
        if len(werewolves) == 0:
            return "村人側の勝利"
        if len(werewolves) >= len(villagers):
            return "人狼側の勝利"
        return None
    
    def run(self):
        """ゲーム実行"""
        self.setup_game()
        print("\n[ゲーム開始]")
        
        max_days = 10
        for _ in range(max_days):
            self.day_phase()
            
            result = self.check_game_end()
            if result:
                print(f"  🏆 ゲーム終了: {result}")
                break
            
            self.night_phase()
            
            result = self.check_game_end()
            if result:
                print(f"  🏆 ゲーム終了: {result}")
                break
        
        self.print_final_report()
        self.visualize_v5()
    
    def print_final_report(self):
        """最終レポート"""
        print("\n" + "=" * 70)
        print("📊 v5.0 最終結果")
        print("=" * 70)
        
        alive = [p for p in self.players if p.alive]
        dead = [p for p in self.players if not p.alive]
        
        print("\n[生存者]")
        for p in alive:
            print(f"  {p.name} ({p.role} / {p.persona.value})")
            print(f"    kappa: {p.engine.kappa:.2f}, 思考: {p.simulations_performed}回, "
                  f"戦略使用: {len(p.strategies_used)}回")
            if p.persona_transitions > 0:
                print(f"    ペルソナ変異: {p.persona_transitions}回")
            if p.rulebreaks_performed > 0:
                print(f"    ルールブレイク: {p.rulebreaks_performed}回")
        
        print("\n[犠牲者]")
        for p in dead:
            cause = "処刑" if any(e for e in self.events if f"{p.name}({p.persona.value}) が処刑" in e) else "襲撃"
            print(f"  {p.name} ({p.role} / {p.persona.value}) - {cause}")
        
        print("\n[統計]")
        print(f"  相転移: {self.phase_transitions}回")
        print(f"  発言: {sum(p.statement_count for p in self.players)}回")
        print(f"  思考: {sum(p.simulations_performed for p in self.players)}回")
        print(f"  戦略参照: {self.total_strategies_invoked}回")
        print(f"  ペルソナ変異: {sum(p.persona_transitions for p in self.players)}回")
        print(f"  ルールブレイク: {self.total_rulebreaks}回")
    
    def visualize_v5(self):
        """可視化（v5拡張: 戦略・ペルソナ変異グラフ追加）"""
        fig, axes = plt.subplots(3, 3, figsize=(18, 14))
        fig.suptitle('SSD v5.0: Werewolf Game with Structural Leap', fontsize=16, fontweight='bold')
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.players)))
        
        # 既存グラフ (1-6)
        for idx, player in enumerate(self.players):
            axes[0, 0].plot(player.engine.history['E_direct'], 
                          label=player.name, color=colors[idx], linewidth=2)
        axes[0, 0].set_title('E_direct (行動エネルギー)', fontweight='bold')
        axes[0, 0].set_xlabel('Time Step')
        axes[0, 0].set_ylabel('Energy')
        axes[0, 0].legend(loc='best', fontsize=8)
        axes[0, 0].grid(True, alpha=0.3)
        
        for idx, player in enumerate(self.players):
            axes[0, 1].plot(player.engine.history['E_indirect'], 
                          label=player.name, color=colors[idx], linewidth=2)
        axes[0, 1].set_title('E_indirect (思考エネルギー)', fontweight='bold')
        axes[0, 1].set_xlabel('Time Step')
        axes[0, 1].set_ylabel('Energy')
        axes[0, 1].legend(loc='best', fontsize=8)
        axes[0, 1].grid(True, alpha=0.3)
        
        for idx, player in enumerate(self.players):
            axes[0, 2].plot(player.engine.history['Theta'], 
                          label=player.name, color=colors[idx], linewidth=2)
        axes[0, 2].set_title('Theta (総エネルギー)', fontweight='bold')
        axes[0, 2].set_xlabel('Time Step')
        axes[0, 2].set_ylabel('Energy')
        axes[0, 2].legend(loc='best', fontsize=8)
        axes[0, 2].grid(True, alpha=0.3)
        
        for idx, player in enumerate(self.players):
            axes[1, 0].plot(player.engine.history['kappa'], 
                          label=player.name, color=colors[idx], linewidth=2)
        axes[1, 0].set_title('Kappa (整合慣性)', fontweight='bold')
        axes[1, 0].set_xlabel('Time Step')
        axes[1, 0].set_ylabel('Kappa')
        axes[1, 0].legend(loc='best', fontsize=8)
        axes[1, 0].grid(True, alpha=0.3)
        
        suspicion_data = [p.suspicion_level for p in self.players]
        axes[1, 1].bar([p.name for p in self.players], suspicion_data, color=colors)
        axes[1, 1].set_title('疑惑レベル (最終)', fontweight='bold')
        axes[1, 1].set_ylabel('Suspicion Level')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        statement_data = [p.statement_count for p in self.players]
        axes[1, 2].bar([p.name for p in self.players], statement_data, color=colors)
        axes[1, 2].set_title('発言回数', fontweight='bold')
        axes[1, 2].set_ylabel('Statements')
        axes[1, 2].tick_params(axis='x', rotation=45)
        axes[1, 2].grid(True, alpha=0.3, axis='y')
        
        # v5新規グラフ (7-9)
        simulation_data = [p.simulations_performed for p in self.players]
        axes[2, 0].bar([p.name for p in self.players], simulation_data, color=colors)
        axes[2, 0].set_title('思考シミュレーション回数', fontweight='bold')
        axes[2, 0].set_ylabel('Simulations')
        axes[2, 0].tick_params(axis='x', rotation=45)
        axes[2, 0].grid(True, alpha=0.3, axis='y')
        
        strategy_data = [len(p.strategies_used) for p in self.players]
        axes[2, 1].bar([p.name for p in self.players], strategy_data, color=colors)
        axes[2, 1].set_title('戦略参照回数', fontweight='bold')
        axes[2, 1].set_ylabel('Strategy Uses')
        axes[2, 1].tick_params(axis='x', rotation=45)
        axes[2, 1].grid(True, alpha=0.3, axis='y')
        
        transition_data = [p.persona_transitions for p in self.players]
        rulebreak_data = [p.rulebreaks_performed for p in self.players]
        x = np.arange(len(self.players))
        width = 0.35
        axes[2, 2].bar(x - width/2, transition_data, width, label='ペルソナ変異', color='skyblue')
        axes[2, 2].bar(x + width/2, rulebreak_data, width, label='ルールブレイク', color='salmon')
        axes[2, 2].set_title('構造的跳躍統計', fontweight='bold')
        axes[2, 2].set_ylabel('Count')
        axes[2, 2].set_xticks(x)
        axes[2, 2].set_xticklabels([p.name for p in self.players], rotation=45)
        axes[2, 2].legend()
        axes[2, 2].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('ssd_werewolf_game_v5.png', dpi=150, bbox_inches='tight')
        print("\n💾 グラフ保存: ssd_werewolf_game_v5.png")
        plt.show()

# ========== メイン実行 ==========
if __name__ == "__main__":
    game = WerewolfGameV5()
    game.run()
    
    print("\n" + "=" * 70)
    print("✅ v5.0デモ完了")
    print("=" * 70)
    print("\n🎓 v5.0の構造的跳躍:")
    print("  1. ✅ 動的ペルソナ → 上層構造の跳躍・変異")
    print("  2. ✅ 戦略データベース → 中核構造への接続・参照")
    print("  3. ✅ ルールブレイク → 物理層（ゲームルール）への攻撃")
    print("  4. ✅ 四層構造の完全実装 → 反応機械から構造的思考者へ")
    print("\n🔬 SSD理論の完全実証:")
    print("  - 物理層（ルール） ← 攪乱型の跳躍で破壊可能")
    print("  - 中核層（戦略DB） ← 思考フェーズで参照・実行")
    print("  - 上層層（ペルソナ） ← 相転移で動的変異")
    print("  - 基層（SSDエンジン） ← エネルギー整合性で全層を駆動")
