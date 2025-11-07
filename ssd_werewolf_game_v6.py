"""
SSD v6.0 統合デモ: 人狼ゲームAI (統合認知版)

v5からv6への進化:
1. 基層エンジンの復元: ssd_core_engine_v3_5.py 再統合 (γ_i2d, γ_d2i 連成復活)
2. 主観的意味圧の復元: ssd_multidimensional_pressure.py 再統合 (Persona別weight)
3. 階層的認知モデル: 第1段階(戦略DB)→第2段階(思考)→認知的不協和解決

SSD理論の完全実装:
- 物理層: ゲームルール（攻撃可能）
- 中核層: STRATEGY_DB（第1段階: 定石参照）
- 上層層: ThinkingPhase（第2段階: 思考検証）+ 認知的不協和解決
- 基層: 連成SSDエンジン（E_i ⇔ E_d 変換）+ 主観的意味圧（Persona→weight）
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Callable
import random
import numpy as np
import matplotlib.pyplot as plt

# ========== SSD v3.5コアエンジン（完全版）インポート ==========
from ssd_core_engine_v3_5 import (
    SSDCoreEngineV3_5,
    SSDStateV3_5,
    SSDParametersV3_5,
    SSDDomain
)

# ========== 多次元意味圧システム（完全版）インポート ==========
from ssd_multidimensional_pressure import (
    MultiDimensionalPressure,
    PressureDimension
)

# ========== v6新機能: ペルソナシステム（動的変異対応） ==========
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

# ========== v6新機能: 戦略データベース（中核構造） ==========
@dataclass
class GameStrategy:
    """人狼ゲームの定石知識"""
    name: str
    condition: callable
    action_type: str
    priority: float
    description: str
    energy_cost: float = 15.0

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

# ========== v6新機能: ルールブレイク（中核構造への跳躍） ==========
class RuleBreakType(Enum):
    VOTE_BOYCOTT = "投票棄権"
    NOISE_SPAM = "無意味発言連発"
    META_STATEMENT = "メタ情報漏洩"

@dataclass
class RuleBreakAction:
    """ゲームルールへの攻撃"""
    break_type: RuleBreakType
    pressure_impact: Dict[str, float]
    persona_requirement: Persona
    trigger_threshold: float

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

# ========== v6新機能: 階層的認知モデル ==========
@dataclass
class ThoughtSimulation:
    """内的シミュレーション結果（第二階層）"""
    target: str
    predicted_suspicion_change: float
    predicted_trust_impact: float
    energy_cost: float = 20.0

@dataclass
class StrategyQuery:
    """戦略DB参照結果（第一階層）"""
    strategy: Optional[GameStrategy]
    confidence: float
    energy_cost: float = 15.0

@dataclass
class CognitiveConflict:
    """認知的不協和（第一階層と第二階層の葛藤）"""
    strategy_suggestion: str  # 戦略DBの提案
    thought_suggestion: str   # 思考の提案
    conflict_detected: bool
    resolution: str          # 解決方法
    final_decision: str      # 最終決定

# ========== プレイヤークラス（v6完全版） ==========
@dataclass
class WerewolfPlayerV6:
    name: str
    role: str
    engine: SSDCoreEngineV3_5
    state: SSDStateV3_5
    pressure_system: MultiDimensionalPressure
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
    cognitive_conflicts: int = 0  # v6: 認知的不協和回数
    thought_priority_decisions: int = 0  # v6: 思考優先決定回数
    strategy_priority_decisions: int = 0  # v6: 戦略優先決定回数

# ========== ゲームマスター（v6完全版） ==========
class WerewolfGameV6:
    def __init__(self):
        self.players: List[WerewolfPlayerV6] = []
        self.day = 0
        self.phase_transitions = 0
        self.events = []
        self.trust_map_global: Dict[Tuple[str, str], float] = {}
        self.seer_revealed = False
        self.total_strategies_invoked = 0
        self.total_rulebreaks = 0
        self.total_cognitive_conflicts = 0
        
    def log_event(self, message: str):
        self.events.append(f"  {message}")
        print(f"  {message}")
    
    def create_persona_weights(self, persona: Persona) -> Dict[str, float]:
        """v6: ペルソナ別の主観的重み付け"""
        weights = {
            'suspicion': 1.0,
            'social_suspicion': 1.0,
            'trust': 1.0,
            'information': 1.0,
            'time': 1.0,
            'boredom': 1.0
        }
        
        if persona == Persona.AGGRESSIVE:
            weights['social_suspicion'] = 1.5  # 他者の発言に過敏
            weights['suspicion'] = 0.8
        elif persona == Persona.STEALTH:
            weights['suspicion'] = 1.5  # 自分が目立つことを恐れる
            weights['social_suspicion'] = 0.7
        elif persona == Persona.LEADER:
            weights['trust'] = 1.3  # 信頼関係を重視
            weights['information'] = 1.2
        elif persona == Persona.DISRUPTOR:
            weights['boredom'] = 1.5  # 退屈を強く感じる
            weights['time'] = 0.6
            
        return weights
    
    def create_werewolf_pressure_v6(self, player: WerewolfPlayerV6, 
                                     context: Dict) -> None:
        """v6: 主観的重み付け付き多次元意味圧登録"""
        weights = self.create_persona_weights(player.persona)
        
        # 各次元を登録
        player.pressure_system.register_dimension(
            name='suspicion',
            calculator=lambda ctx: player.suspicion_level,
            weight=weights['suspicion'],
            description='自己への疑惑圧'
        )
        
        accusers = sum(1 for p in self.players 
                      if p.alive and p.name != player.name 
                      and player.trust_map.get(p.name, 0.5) < 0.3)
        player.pressure_system.register_dimension(
            name='social_suspicion',
            calculator=lambda ctx: accusers * 0.8,
            weight=weights['social_suspicion'],
            description='社会的疑惑圧'
        )
        
        allies = sum(1 for p in self.players 
                    if p.alive and player.trust_map.get(p.name, 0.5) > 0.7)
        player.pressure_system.register_dimension(
            name='trust',
            calculator=lambda ctx: max(0, 3.0 - allies * 1.5),
            weight=weights['trust'],
            description='信頼圧'
        )
        
        player.pressure_system.register_dimension(
            name='information',
            calculator=lambda ctx: 5.0 - player.statement_count * 0.5,
            weight=weights['information'],
            description='情報圧'
        )
        
        player.pressure_system.register_dimension(
            name='time',
            calculator=lambda ctx: self.day * 0.3,
            weight=weights['time'],
            description='時間圧'
        )
        
        player.pressure_system.register_dimension(
            name='boredom',
            calculator=lambda ctx: player.boredom_pressure,
            weight=weights['boredom'],
            description='退屈圧'
        )
    
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
        print("SSD v6.0 統合デモ: 人狼ゲームAI (統合認知版)")
        print("=" * 70)
        print("\n[初期配置]")
        
        for name, role in zip(names, roles):
            persona = self.assign_persona(role)
            
            # v6: 連成SSDエンジン初期化
            params = SSDParametersV3_5(
                gamma_i2d=0.05,  # 思考→行動変換
                gamma_d2i=0.02,  # 行動→思考変換
                Theta_critical=100.0,  # 臨界閾値
                enable_phase_transition=True,
                phase_transition_multiplier=10.0,
                beta_decay=0.01
            )
            
            engine = SSDCoreEngineV3_5(params)
            
            # 初期状態
            if role == "WEREWOLF":
                state = SSDStateV3_5(kappa=1.3, E_direct=100.0, E_indirect=150.0)
            elif role == "SEER":
                state = SSDStateV3_5(kappa=1.1, E_direct=60.0, E_indirect=200.0)
            else:
                state = SSDStateV3_5(kappa=1.0, E_direct=80.0, E_indirect=130.0)
            
            # v6: 多次元意味圧システム初期化
            pressure_system = MultiDimensionalPressure()
            
            player = WerewolfPlayerV6(
                name=name, role=role, engine=engine, state=state,
                pressure_system=pressure_system, persona=persona
            )
            self.players.append(player)
            
            # 圧力次元を登録
            self.create_werewolf_pressure_v6(player, {})
            
            print(f"  {name}: {role} / {persona.value} "
                  f"(E_d={state.E_direct:.0f}, E_i={state.E_indirect:.0f}, "
                  f"κ={state.kappa:.1f})")
        
        for p in self.players:
            p.trust_map = {other.name: 0.5 for other in self.players if other.name != p.name}
    
    def query_strategy_db(self, player: WerewolfPlayerV6) -> Optional[StrategyQuery]:
        """戦略DB参照（第一階層: 中核構造）"""
        if player.state.E_indirect < 15.0:
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
        
        # E_indirectを消費（第一階層の認知コスト）
        player.state.E_indirect -= best_strategy.energy_cost
        player.strategies_used.append(best_strategy.name)
        
        confidence = min(1.0, player.state.kappa / 2.0)
        
        return StrategyQuery(
            strategy=best_strategy,
            confidence=confidence,
            energy_cost=best_strategy.energy_cost
        )
    
    def thinking_phase(self, player: WerewolfPlayerV6, 
                       alive_players: List[WerewolfPlayerV6]) -> Optional[ThoughtSimulation]:
        """思考フェーズ（第二階層: 内的シミュレーション）"""
        if player.state.E_indirect < 20.0:
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
        
        # E_indirectを消費（第二階層の認知コスト）
        player.state.E_indirect -= simulation.energy_cost
        player.simulations_performed += 1
        
        return simulation
    
    def resolve_cognitive_conflict(self, player: WerewolfPlayerV6,
                                   strategy_query: Optional[StrategyQuery],
                                   simulation: Optional[ThoughtSimulation],
                                   default_target: str) -> Tuple[str, Optional[CognitiveConflict]]:
        """v6: 認知的不協和の解決（階層的意思決定）"""
        
        # 戦略も思考もない場合: デフォルト
        if not strategy_query and not simulation:
            return default_target, None
        
        # 戦略のみ: 第一階層の提案採用
        if strategy_query and not simulation:
            if strategy_query.strategy.action_type == "MINIMIZE_STATEMENTS":
                return "SKIP", None
            return default_target, None
        
        # 思考のみ: 第二階層の提案採用
        if simulation and not strategy_query:
            return simulation.target, None
        
        # 両方存在: 認知的不協和の可能性
        strategy_target = default_target  # 戦略が暗示するターゲット
        thought_target = simulation.target
        
        conflict_detected = (strategy_target != thought_target)
        
        if not conflict_detected:
            # 葛藤なし: 両階層が一致
            return strategy_target, CognitiveConflict(
                strategy_suggestion=strategy_target,
                thought_suggestion=thought_target,
                conflict_detected=False,
                resolution="一致",
                final_decision=strategy_target
            )
        
        # 葛藤あり: 解決ロジック
        player.cognitive_conflicts += 1
        self.total_cognitive_conflicts += 1
        
        # 解決基準: ペルソナとE_indirect量
        if player.persona in [Persona.LEADER, Persona.STEALTH]:
            # 思考重視型: E_indirectが十分なら思考を優先
            if player.state.E_indirect > 30.0:
                player.thought_priority_decisions += 1
                return thought_target, CognitiveConflict(
                    strategy_suggestion=strategy_target,
                    thought_suggestion=thought_target,
                    conflict_detected=True,
                    resolution="思考優先（高E_indirect）",
                    final_decision=thought_target
                )
        
        # デフォルト: 戦略（定石）を優先
        player.strategy_priority_decisions += 1
        return strategy_target, CognitiveConflict(
            strategy_suggestion=strategy_target,
            thought_suggestion=thought_target,
            conflict_detected=True,
            resolution="戦略優先（定石/衝動）",
            final_decision=strategy_target
        )
    
    def attempt_persona_transition(self, player: WerewolfPlayerV6) -> bool:
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
                
                # v6: ペルソナ変異時に意味圧の重みを再設定
                player.pressure_system = MultiDimensionalPressure()
                self.create_werewolf_pressure_v6(player, {})
                
                self.log_event(f"🔄 {player.name} が{transition.trigger_message}！ "
                             f"({old_persona.value} → {transition.to_persona.value})")
                return True
        
        return False
    
    def attempt_rulebreak(self, player: WerewolfPlayerV6) -> Optional[RuleBreakAction]:
        """ルールブレイク試行（中核構造への跳躍）"""
        if player.persona != Persona.DISRUPTOR:
            return None
        
        applicable_breaks = [
            rb for rb in RULEBREAK_ACTIONS
            if rb.persona_requirement == player.persona
            and player.state.E_indirect < rb.trigger_threshold
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
    
    def handle_phase_transition(self, player: WerewolfPlayerV6):
        """相転移処理（v6: SSDエンジンの臨界状態を利用）"""
        # v6: エンジンの臨界状態をチェック
        if player.state.is_critical:
            self.phase_transitions += 1
            self.log_event(f"⚡ {player.name}({player.persona.value}) が相転移！ "
                         f"(E_i={player.state.E_indirect:.1f})")
            
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
        """議論フェーズ（v6: E_direct消費）"""
        self.log_event("--- 議論タイム ---")
        alive = [p for p in self.players if p.alive]
        
        for player in alive:
            # 戦略DB参照（第一階層）
            strategy_query = self.query_strategy_db(player)
            
            if strategy_query and strategy_query.strategy:
                self.total_strategies_invoked += 1
                self.log_event(f"    📖 {player.name} が戦略参照: "
                             f"{strategy_query.strategy.description} "
                             f"(信頼度: {strategy_query.confidence:.2f})")
                
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
                    
                    strength = random.uniform(0.5, 1.0) * player.state.kappa
                    player.trust_map[target.name] = max(0, player.trust_map[target.name] - 0.1)
                    target.suspicion_level += strength
                    player.statement_count += 1
                    
                    # v6: E_direct消費（行動コスト）
                    player.state.E_direct -= 5.0
                    
                    self.log_event(f"    💬 {player.name}({player.persona.value}) が "
                                 f"{target.name} を疑う (強度: {strength:.2f})")
    
    def voting_phase(self) -> Optional[WerewolfPlayerV6]:
        """投票フェーズ（v6: 階層的認知モデル）"""
        self.log_event("--- 投票タイム ---")
        alive = [p for p in self.players if p.alive]
        votes = {}
        
        for player in alive:
            # 第一階層: 戦略DB参照
            strategy_query = self.query_strategy_db(player)
            
            # 第二階層: 思考シミュレーション
            simulation = self.thinking_phase(player, alive)
            if simulation:
                self.log_event(f"    🧠 {player.name} が思考シミュレーション実行")
            
            # ルールブレイク（投票棄権）
            rulebreak = self.attempt_rulebreak(player)
            if rulebreak and rulebreak.break_type == RuleBreakType.VOTE_BOYCOTT:
                self.log_event(f"    🚫 {player.name} が投票棄権")
                continue
            
            targets = [p for p in alive if p.name != player.name]
            if not targets:
                continue
            
            # デフォルトターゲット
            default_target = max(targets, 
                               key=lambda p: player.trust_map.get(p.name, 0) * -1 + p.suspicion_level).name
            
            # v6: 認知的不協和の解決
            final_target, conflict = self.resolve_cognitive_conflict(
                player, strategy_query, simulation, default_target
            )
            
            if conflict and conflict.conflict_detected:
                self.log_event(f"    ⚠️  {player.name} に認知的不協和！ "
                             f"戦略:{conflict.strategy_suggestion} vs "
                             f"思考:{conflict.thought_suggestion} "
                             f"→ {conflict.resolution}")
            
            if final_target == "SKIP":
                continue
            
            # 投票実行（v6: E_direct消費）
            vote_strength = min(1.0, player.state.E_direct / 100.0)
            votes[final_target] = votes.get(final_target, 0) + vote_strength
            
            player.state.E_direct -= 10.0  # 投票コスト
            
            self.log_event(f"    {player.name}({player.persona.value}) → {final_target} "
                         f"(強さ: {vote_strength:.2f}, κ={player.state.kappa:.2f})")
        
        if not votes:
            return None
        
        executed = max(votes, key=votes.get)
        executed_player = next(p for p in self.players if p.name == executed)
        return executed_player
    
    def process_cooperation(self):
        """協働快処理（v6: E_direct増加）"""
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
                    p1.state.E_direct += happiness
                    p2.state.E_direct += happiness
                    
                    p1.trust_map[p2.name] = min(1.0, p1.trust_map[p2.name] + 0.15)
                    p2.trust_map[p1.name] = min(1.0, p2.trust_map[p1.name] + 0.15)
                    
                    self.log_event(f"    🤝 {p1.name} ⇔ {p2.name} (信頼: {new_trust:.2f})")
                elif new_trust < 0.4:
                    p1.trust_map[p2.name] = max(0, p1.trust_map[p2.name] - 0.1)
                    p2.trust_map[p1.name] = max(0, p2.trust_map[p1.name] - 0.1)
                    
                    self.log_event(f"    💔 {p1.name} ← {p2.name} (信頼: {new_trust:.2f})")
    
    def learning_phase(self, executed: WerewolfPlayerV6):
        """学習フェーズ（v6: kappa動態）"""
        self.log_event("--- 学習フェーズ ---")
        alive = [p for p in self.players if p.alive]
        
        for player in alive:
            success = (executed.role == "WEREWOLF")
            
            if success:
                player.state.kappa = min(2.0, player.state.kappa + 0.15)
                self.log_event(f"    ✅ {player.name} 成功！ κ: {player.state.kappa:.2f}")
            else:
                player.state.kappa = max(0.5, player.state.kappa - 0.10)
                self.log_event(f"    ❌ {player.name} 失敗... κ: {player.state.kappa:.2f}")
    
    def update_player_energy(self, player: WerewolfPlayerV6):
        """v6: 連成SSDエンジンでエネルギー更新"""
        context = {'day': self.day, 'phase': 'day'}
        
        # 多次元意味圧を計算
        p_external_vector = player.pressure_system.calculate(context)
        
        # 退屈圧力の更新
        p_total = np.linalg.norm(p_external_vector)
        if p_total < 0.3:
            player.boredom_turns += 1
            player.boredom_pressure = 1.0 + 0.1 * player.boredom_turns
            
            if player.boredom_pressure > 2.0:
                self.log_event(f"    💤 {player.name} が退屈から発言")
                player.statement_count += 1
                player.boredom_turns = 0
                player.boredom_pressure = 0.0
                player.state.E_direct -= 5.0  # 発言コスト
        else:
            player.boredom_turns = 0
            player.boredom_pressure = 0.0
        
        # v6: 連成SSDエンジンでステップ実行
        player.state = player.engine.step(
            state=player.state,
            p_external=p_external_vector,
            dt=1.0
        )
        
        # 相転移チェック
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
        """夜フェーズ（v6: E_direct消費）"""
        print(f"  === Day {self.day}: 夜のフェーズ ===")
        
        werewolves = [p for p in self.players if p.alive and p.role == "WEREWOLF"]
        if not werewolves:
            return
        
        wolf = random.choice(werewolves)
        targets = [p for p in self.players if p.alive and p.role != "WEREWOLF"]
        
        if targets:
            strategy_query = self.query_strategy_db(wolf)
            
            if strategy_query and strategy_query.strategy:
                if strategy_query.strategy.action_type == "TARGET_ALLIANCE":
                    target = max(targets, key=lambda p: 
                               sum(p.trust_map.get(other.name, 0) for other in self.players if other.alive))
                else:
                    target = random.choice(targets)
            else:
                target = random.choice(targets)
            
            attack_cost = 30.0 if wolf.state.E_direct >= 30 else 10.0
            wolf.state.E_direct -= attack_cost
            
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
                seer.state.E_indirect -= 15.0
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
        self.visualize_v6()
    
    def print_final_report(self):
        """最終レポート"""
        print("\n" + "=" * 70)
        print("📊 v6.0 最終結果")
        print("=" * 70)
        
        alive = [p for p in self.players if p.alive]
        dead = [p for p in self.players if not p.alive]
        
        print("\n[生存者]")
        for p in alive:
            print(f"  {p.name} ({p.role} / {p.persona.value})")
            print(f"    E_direct: {p.state.E_direct:.1f}, E_indirect: {p.state.E_indirect:.1f}, "
                  f"kappa: {p.state.kappa:.2f}")
            print(f"    思考: {p.simulations_performed}回, 戦略使用: {len(p.strategies_used)}回")
            if p.cognitive_conflicts > 0:
                print(f"    認知的不協和: {p.cognitive_conflicts}回 "
                      f"(思考優先: {p.thought_priority_decisions}回, "
                      f"戦略優先: {p.strategy_priority_decisions}回)")
            if p.persona_transitions > 0:
                print(f"    ペルソナ変異: {p.persona_transitions}回")
        
        print("\n[犠牲者]")
        for p in dead:
            cause = "処刑" if any(e for e in self.events if f"{p.name}({p.persona.value}) が処刑" in e) else "襲撃"
            print(f"  {p.name} ({p.role} / {p.persona.value}) - {cause}")
        
        print("\n[統計]")
        print(f"  相転移: {self.phase_transitions}回")
        print(f"  発言: {sum(p.statement_count for p in self.players)}回")
        print(f"  思考: {sum(p.simulations_performed for p in self.players)}回")
        print(f"  戦略参照: {self.total_strategies_invoked}回")
        print(f"  認知的不協和: {self.total_cognitive_conflicts}回")
        print(f"  ペルソナ変異: {sum(p.persona_transitions for p in self.players)}回")
        print(f"  ルールブレイク: {self.total_rulebreaks}回")
    
    def visualize_v6(self):
        """可視化（v6: 認知的不協和グラフ追加）"""
        fig, axes = plt.subplots(3, 3, figsize=(18, 14))
        fig.suptitle('SSD v6.0: Werewolf Game with Integrated Cognition', 
                     fontsize=16, fontweight='bold')
        
        colors = plt.cm.tab10(np.linspace(0, 1, len(self.players)))
        
        # グラフ1-6: 既存
        for idx, player in enumerate(self.players):
            e_direct_history = [player.state.E_direct]  # 簡略化: 最終値のみ
            axes[0, 0].bar(player.name, player.state.E_direct, color=colors[idx])
        axes[0, 0].set_title('E_direct (行動エネルギー) 最終値', fontweight='bold')
        axes[0, 0].set_ylabel('Energy')
        axes[0, 0].tick_params(axis='x', rotation=45)
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        for idx, player in enumerate(self.players):
            axes[0, 1].bar(player.name, player.state.E_indirect, color=colors[idx])
        axes[0, 1].set_title('E_indirect (思考エネルギー) 最終値', fontweight='bold')
        axes[0, 1].set_ylabel('Energy')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        for idx, player in enumerate(self.players):
            theta = player.state.E_direct + player.state.E_indirect
            axes[0, 2].bar(player.name, theta, color=colors[idx])
        axes[0, 2].set_title('Theta (総エネルギー) 最終値', fontweight='bold')
        axes[0, 2].set_ylabel('Energy')
        axes[0, 2].tick_params(axis='x', rotation=45)
        axes[0, 2].grid(True, alpha=0.3, axis='y')
        
        kappa_data = [p.state.kappa for p in self.players]
        axes[1, 0].bar([p.name for p in self.players], kappa_data, color=colors)
        axes[1, 0].set_title('Kappa (整合慣性) 最終値', fontweight='bold')
        axes[1, 0].set_ylabel('Kappa')
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
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
        
        # v6新規グラフ (7-9)
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
        
        # v6: 認知的不協和グラフ
        conflict_data = [p.cognitive_conflicts for p in self.players]
        thought_priority = [p.thought_priority_decisions for p in self.players]
        strategy_priority = [p.strategy_priority_decisions for p in self.players]
        x = np.arange(len(self.players))
        width = 0.25
        axes[2, 2].bar(x - width, conflict_data, width, label='認知的不協和', color='orange')
        axes[2, 2].bar(x, thought_priority, width, label='思考優先決定', color='skyblue')
        axes[2, 2].bar(x + width, strategy_priority, width, label='戦略優先決定', color='salmon')
        axes[2, 2].set_title('認知的不協和統計', fontweight='bold')
        axes[2, 2].set_ylabel('Count')
        axes[2, 2].set_xticks(x)
        axes[2, 2].set_xticklabels([p.name for p in self.players], rotation=45)
        axes[2, 2].legend()
        axes[2, 2].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('ssd_werewolf_game_v6.png', dpi=150, bbox_inches='tight')
        print("\n💾 グラフ保存: ssd_werewolf_game_v6.png")
        plt.show()

# ========== メイン実行 ==========
if __name__ == "__main__":
    game = WerewolfGameV6()
    game.run()
    
    print("\n" + "=" * 70)
    print("✅ v6.0デモ完了")
    print("=" * 70)
    print("\n🎓 v6.0の統合認知:")
    print("  1. ✅ 連成SSDエンジン → E_indirect ⇔ E_direct 変換復活")
    print("  2. ✅ 主観的意味圧 → Persona別weight動的設定")
    print("  3. ✅ 階層的認知モデル → 第1段階(戦略)→第2段階(思考)→葛藤解決")
    print("  4. ✅ 認知的不協和 → 戦略と思考の矛盾検出・解決ロジック")
    print("\n🔬 SSD理論の完全実証:")
    print("  - 基層（連成エンジン） ← γ_i2d, γ_d2i でE変換")
    print("  - 上層（主観的圧力） ← Personaがweight決定")
    print("  - 中核（戦略DB） ← 第1段階で定石参照")
    print("  - 上層（思考） ← 第2段階で内的シミュレーション")
    print("  - 統合（葛藤解決） ← 階層間の矛盾を意識的に処理")
