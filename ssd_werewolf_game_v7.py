"""
SSD v7.0 四層構造統合版: 人狼ゲームAI (Four-Layer Human Module)

v6からv7への理論的跳躍:
=====================================
v6: 多次元意味圧を「単一プール」に集約
    → どの構造層が悲鳴を上げているかを区別できない
    → 内的葛藤（整合不能）をモデル化できない

v7: SSD人間モジュール四層構造への統合
    → PHYSICAL層: 発言制限、時間制約（R→∞）
    → BASE層: 生存本能、疑惑恐怖（R=large）
    → CORE層: 役割遂行、順位、戦略（R=medium）
    → UPPER層: 長期戦略、理念、物語（R=small）
    → 層間葛藤の定量化 → 構造的跳躍のトリガー

理論的意義:
----------
1. 内的葛藤のモデル化:
   BASE圧高（疑惑恐怖）× UPPER圧高（理念遂行）
   → 「逃げるべきか、理念を貫くべきか」
   
2. R値に基づく跳躍判定:
   最も動かしにくい層（R値最大）が最優先で跳躍
   BASE層の本能的行動 > UPPER層の理念的行動
   
3. 人間らしいAI:
   単なる最適化ではなく、構造的葛藤を抱え、
   それを解決しようとする主体へ
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

# ========== [v7新機能] 四層構造多次元意味圧システム ==========
from ssd_multidimensional_pressure_v2 import (
    MultiDimensionalPressure,
    PressureDimension,
    SSDLayer,
    create_apex_survivor_pressure_v2
)

# ========== v6継承: ペルソナシステム（動的変異対応） ==========
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

# ========== v6継承: 戦略データベース（中核構造） ==========
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

# ========== v6継承: ルールブレイク（中核構造への跳躍） ==========
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

# ========== v6継承: 階層的認知モデル ==========
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

# ========== [v7新機能] 四層構造統計データ ==========
@dataclass
class LayerConflictEvent:
    """層間葛藤イベント"""
    day: int
    player_name: str
    dominant_layer: str
    conflict_pair: str
    conflict_index: float
    decision: str

# ========== プレイヤークラス（v7完全版） ==========
@dataclass
class WerewolfPlayerV7:
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
    
    # [v7新機能] 四層構造統計
    layer_conflicts: List[LayerConflictEvent] = field(default_factory=list)
    base_leaps: int = 0  # BASE層由来の跳躍回数
    upper_leaps: int = 0  # UPPER層由来の跳躍回数
    physical_constraints: int = 0  # PHYSICAL層制約回数

# ========== ゲームマスター（v7完全版） ==========
class WerewolfGameV7:
    def __init__(self):
        self.players: List[WerewolfPlayerV7] = []
        self.day = 0
        self.phase_transitions = 0
        self.events = []
        self.trust_map_global: Dict[Tuple[str, str], float] = {}
        self.seer_revealed = False
        self.total_strategies_invoked = 0
        self.total_rulebreaks = 0
        self.total_cognitive_conflicts = 0
        self.total_layer_conflicts = 0  # [v7] 層間葛藤総数
        
    def log_event(self, message: str):
        self.events.append(f"  {message}")
        print(f"  {message}")
    
    # ========== [v7核心機能] 四層構造圧力計算関数群 ==========
    
    def physical_constraint_calculator(self, player: WerewolfPlayerV7) -> Callable:
        """PHYSICAL層: 発言制限・時間制約（R→∞）"""
        max_statements = 12
        def calc(context: dict) -> float:
            # 発言回数が制限に近づくほど圧力増加
            fatigue = player.statement_count / max_statements
            return min(1.0, fatigue)
        return calc
    
    def survival_instinct_calculator(self, player: WerewolfPlayerV7) -> Callable:
        """BASE層: 生存本能（疑惑恐怖）（R=large）"""
        def calc(context: dict) -> float:
            # 疑惑レベルが高いほど生存本能が高まる
            return min(1.0, player.suspicion_level / 10.0)
        return calc
    
    def risk_avoidance_calculator(self, player: WerewolfPlayerV7) -> Callable:
        """BASE層: リスク回避本能（R=large）"""
        def calc(context: dict) -> float:
            # 告発者が多いほどリスク圧増加
            accusers = sum(1 for p in self.players 
                          if p.alive and p.name != player.name 
                          and player.trust_map.get(p.name, 0.5) < 0.3)
            return min(1.0, accusers / 4.0)
        return calc
    
    def role_performance_calculator(self, player: WerewolfPlayerV7) -> Callable:
        """CORE層: 役割遂行圧力（R=medium）"""
        def calc(context: dict) -> float:
            # 役割に応じた遂行度
            if player.role == "WEREWOLF":
                # 人狼は生存者数で評価
                werewolves = sum(1 for p in self.players if p.alive and p.role == "WEREWOLF")
                return max(0.0, 1.0 - werewolves / 2.0)
            elif player.role == "SEER":
                # 占い師は情報提供度で評価
                return max(0.0, 1.0 - player.statement_count / 8.0)
            else:
                # 村人は疑惑度で評価
                return min(1.0, player.suspicion_level / 8.0)
        return calc
    
    def trust_system_calculator(self, player: WerewolfPlayerV7) -> Callable:
        """CORE層: 信頼システム圧力（R=medium）"""
        def calc(context: dict) -> float:
            allies = sum(1 for p in self.players 
                        if p.alive and player.trust_map.get(p.name, 0.5) > 0.7)
            return max(0.0, 1.0 - allies / 3.0)
        return calc
    
    def strategic_narrative_calculator(self, player: WerewolfPlayerV7) -> Callable:
        """UPPER層: 戦略的物語圧力（R=small）"""
        def calc(context: dict) -> float:
            # 長期的戦略の必要性（日数に応じて増加）
            return min(1.0, self.day / 4.0)
        return calc
    
    def ideological_pressure_calculator(self, player: WerewolfPlayerV7) -> Callable:
        """UPPER層: 理念圧力（R=small）"""
        def calc(context: dict) -> float:
            # ペルソナに応じた理念的圧力
            if player.persona == Persona.LEADER:
                # リーダーは理念を強く感じる
                return 0.7
            elif player.persona == Persona.DISRUPTOR:
                # 攪乱者は理念から解放されている
                return 0.2
            else:
                return 0.4
        return calc
    
    def create_werewolf_pressure_v7(self, player: WerewolfPlayerV7) -> None:
        """
        [v7核心機能] 四層構造多次元意味圧の登録
        
        理論的意義:
        - 各圧力が作用する層（SSDLayer）を明示的に指定
        - 層ごとに集計された圧力を取得可能
        - 層間葛藤を定量化可能
        """
        
        # --- PHYSICAL層: 物理的制約（R→∞） ---
        player.pressure_system.register_dimension(
            name='physical_constraint',
            calculator=self.physical_constraint_calculator(player),
            layer=SSDLayer.PHYSICAL,
            weight=1.0,
            description='発言制限・時間制約（物理層）'
        )
        
        # --- BASE層: 本能・生存・恐怖（R=large） ---
        player.pressure_system.register_dimension(
            name='survival_instinct',
            calculator=self.survival_instinct_calculator(player),
            layer=SSDLayer.BASE,
            weight=0.6,
            description='生存本能（疑惑恐怖）（基層）'
        )
        player.pressure_system.register_dimension(
            name='risk_avoidance',
            calculator=self.risk_avoidance_calculator(player),
            layer=SSDLayer.BASE,
            weight=0.4,
            description='リスク回避本能（基層）'
        )
        
        # --- CORE層: ルール・社会・役割（R=medium） ---
        player.pressure_system.register_dimension(
            name='role_performance',
            calculator=self.role_performance_calculator(player),
            layer=SSDLayer.CORE,
            weight=0.5,
            description='役割遂行圧力（中核層）'
        )
        player.pressure_system.register_dimension(
            name='trust_system',
            calculator=self.trust_system_calculator(player),
            layer=SSDLayer.CORE,
            weight=0.5,
            description='信頼システム圧力（中核層）'
        )
        
        # --- UPPER層: 意味・文脈・理念（R=small） ---
        player.pressure_system.register_dimension(
            name='strategic_narrative',
            calculator=self.strategic_narrative_calculator(player),
            layer=SSDLayer.UPPER,
            weight=0.6,
            description='戦略的物語圧力（上層）'
        )
        player.pressure_system.register_dimension(
            name='ideological_pressure',
            calculator=self.ideological_pressure_calculator(player),
            layer=SSDLayer.UPPER,
            weight=0.4,
            description='理念圧力（上層）'
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
        """ゲーム初期化（v7版）"""
        names = ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎", "七郎"]
        roles = ["WEREWOLF", "WEREWOLF", "VILLAGER", "SEER", 
                 "VILLAGER", "VILLAGER", "VILLAGER"]
        
        print("=" * 70)
        print("SSD v7.0 四層構造統合版: 人狼ゲームAI")
        print("=" * 70)
        print("\n[初期配置]")
        
        for name, role in zip(names, roles):
            persona = self.assign_persona(role)
            
            # v6継承: 連成SSDエンジン初期化
            params = SSDParametersV3_5(
                gamma_i2d=0.05,
                gamma_d2i=0.02,
                Theta_critical=100.0,
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
            
            # [v7新機能] 四層構造多次元意味圧システム
            pressure_system = MultiDimensionalPressure()
            
            player = WerewolfPlayerV7(
                name=name, role=role, engine=engine, state=state,
                pressure_system=pressure_system, persona=persona
            )
            self.players.append(player)
            
            # [v7] 四層構造圧力次元を登録
            self.create_werewolf_pressure_v7(player)
            
            print(f"  {name}: {role} / {persona.value} "
                  f"(E_d={state.E_direct:.0f}, E_i={state.E_indirect:.0f}, "
                  f"κ={state.kappa:.1f})")
        
        for p in self.players:
            p.trust_map = {other.name: 0.5 for other in self.players if other.name != p.name}
    
    def query_strategy_db(self, player: WerewolfPlayerV7) -> Optional[StrategyQuery]:
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
        
        # E_indirectを消費
        player.state.E_indirect -= best_strategy.energy_cost
        player.strategies_used.append(best_strategy.name)
        
        confidence = min(1.0, player.state.kappa / 2.0)
        
        return StrategyQuery(
            strategy=best_strategy,
            confidence=confidence,
            energy_cost=best_strategy.energy_cost
        )
    
    def thinking_phase(self, player: WerewolfPlayerV7, 
                       alive_players: List[WerewolfPlayerV7]) -> Optional[ThoughtSimulation]:
        """思考フェーズ（第二階層: 内的シミュレーション）"""
        if player.state.E_indirect < 20.0:
            return None
        
        think_probability = {
            Persona.STEALTH: 0.3,
            Persona.AGGRESSIVE: 0.5,
            Persona.LEADER: 0.8,
            Persona.DISRUPTOR: 0.4
        }.get(player.persona, 0.5)
        
        if random.random() > think_probability:
            return None
        
        # ターゲット選定
        targets = [p for p in alive_players if p.name != player.name]
        if not targets:
            return None
        
        target = random.choice(targets)
        
        # 予測シミュレーション
        predicted_suspicion_change = random.uniform(-2.0, 3.0)
        predicted_trust_impact = random.uniform(-1.0, 2.0)
        
        # E_indirectを消費
        player.state.E_indirect -= 20.0
        player.simulations_performed += 1
        
        return ThoughtSimulation(
            target=target.name,
            predicted_suspicion_change=predicted_suspicion_change,
            predicted_trust_impact=predicted_trust_impact
        )
    
    def resolve_cognitive_conflict(self, player: WerewolfPlayerV7,
                                    strategy: Optional[StrategyQuery],
                                    thought: Optional[ThoughtSimulation]) -> CognitiveConflict:
        """認知的不協和解決"""
        if strategy is None and thought is None:
            return CognitiveConflict(
                strategy_suggestion="なし",
                thought_suggestion="なし",
                conflict_detected=False,
                resolution="両方なし",
                final_decision="デフォルト行動"
            )
        
        if strategy and not thought:
            return CognitiveConflict(
                strategy_suggestion=strategy.strategy.name if strategy.strategy else "なし",
                thought_suggestion="なし",
                conflict_detected=False,
                resolution="戦略優先",
                final_decision=strategy.strategy.action_type if strategy.strategy else "デフォルト"
            )
        
        if thought and not strategy:
            return CognitiveConflict(
                strategy_suggestion="なし",
                thought_suggestion=f"{thought.target}への働きかけ",
                conflict_detected=False,
                resolution="思考優先",
                final_decision=f"{thought.target}をターゲット"
            )
        
        # 両方存在 → 葛藤発生の可能性
        strategy_action = strategy.strategy.action_type if strategy and strategy.strategy else "なし"
        thought_action = f"{thought.target}への働きかけ" if thought else "なし"
        
        if strategy and thought:
            # κ値で判定
            if player.state.kappa > 1.5:
                # 高整合度 → 戦略を信頼
                player.strategy_priority_decisions += 1
                return CognitiveConflict(
                    strategy_suggestion=strategy_action,
                    thought_suggestion=thought_action,
                    conflict_detected=True,
                    resolution="高κ→戦略優先",
                    final_decision=strategy_action
                )
            else:
                # 低整合度 → 直感（思考）を信頼
                player.thought_priority_decisions += 1
                return CognitiveConflict(
                    strategy_suggestion=strategy_action,
                    thought_suggestion=thought_action,
                    conflict_detected=True,
                    resolution="低κ→思考優先",
                    final_decision=thought_action
                )
        
        return CognitiveConflict(
            strategy_suggestion=strategy_action,
            thought_suggestion=thought_action,
            conflict_detected=False,
            resolution="不明",
            final_decision="デフォルト"
        )
    
    def attempt_rulebreak(self, player: WerewolfPlayerV7, 
                         pressures: Dict[SSDLayer, float]) -> Optional[RuleBreakAction]:
        """
        ルールブレイク試行（v7版: 四層構造圧力を受け取る）
        
        理論的変更:
        v6: total_pressure（単一値）で判定
        v7: 層別圧力を使用し、BASE層が高い場合に本能的ルールブレイク
        """
        if player.persona != Persona.DISRUPTOR:
            return None
        
        # [v7] BASE層圧力が高い場合、本能的ルールブレイク
        base_pressure = pressures.get(SSDLayer.BASE, 0.0)
        total_pressure = sum(pressures.values())
        
        # BASE層が支配的な場合、閾値を下げる
        threshold_modifier = 0.7 if base_pressure > 0.6 else 1.0
        
        applicable = [
            rb for rb in RULEBREAK_ACTIONS 
            if total_pressure * 100 > rb.trigger_threshold * threshold_modifier
        ]
        
        if not applicable:
            return None
        
        selected = random.choice(applicable)
        player.rulebreaks_performed += 1
        self.total_rulebreaks += 1
        
        return selected
    
    def attempt_persona_transition(self, player: WerewolfPlayerV7,
                                    pressures: Dict[SSDLayer, float]) -> bool:
        """
        ペルソナ変異試行（v7版: 四層構造圧力を使用）
        
        理論的変更:
        v6: total_pressure（単一値）で判定
        v7: UPPER層圧力が高い場合に理念的変異、BASE層圧力が高い場合に本能的変異
        """
        upper_pressure = pressures.get(SSDLayer.UPPER, 0.0)
        base_pressure = pressures.get(SSDLayer.BASE, 0.0)
        
        # UPPER層が高い場合、理念的変異（LEADER, AGGRESSIVE方向）
        # BASE層が高い場合、本能的変異（STEALTH, DISRUPTOR方向）
        
        base_prob = 0.05
        if upper_pressure > 0.7:
            transition_prob = base_prob * 2.0
        elif base_pressure > 0.7:
            transition_prob = base_prob * 2.5  # 本能的変異はより強い
        else:
            transition_prob = base_prob
        
        if random.random() > transition_prob:
            return False
        
        applicable = [
            t for t in PERSONA_TRANSITIONS 
            if t.from_persona == player.persona
        ]
        
        if not applicable:
            return False
        
        # BASE層優勢 → STEALTH/DISRUPTORへの変異を優先
        # UPPER層優勢 → LEADER/AGGRESSIVEへの変異を優先
        if base_pressure > upper_pressure:
            # 本能的変異
            preferred = [t for t in applicable 
                        if t.to_persona in [Persona.STEALTH, Persona.DISRUPTOR]]
            selected = random.choice(preferred if preferred else applicable)
        else:
            # 理念的変異
            preferred = [t for t in applicable 
                        if t.to_persona in [Persona.LEADER, Persona.AGGRESSIVE]]
            selected = random.choice(preferred if preferred else applicable)
        
        if random.random() < selected.probability:
            old_persona = player.persona
            player.persona = selected.to_persona
            player.persona_transitions += 1
            self.log_event(f"    💥 {player.name}が{selected.trigger_message}! "
                          f"{old_persona.value}→{player.persona.value}")
            return True
        
        return False
    
    def run_day_phase(self):
        """1日フェーズの実行（v7版）"""
        self.day += 1
        print(f"\n{'='*70}")
        print(f"Day {self.day}")
        print(f"{'='*70}")
        
        alive_players = [p for p in self.players if p.alive]
        
        for player in alive_players:
            print(f"\n[{player.name}のターン] ({player.role} / {player.persona.value})")
            
            # [v7核心機能] 四層構造圧力計算
            context = {}
            pressures = player.pressure_system.calculate(context)
            
            # 層別圧力表示
            print(f"  層別圧力:")
            for layer, pressure in pressures.items():
                print(f"    {layer.name:10s}: {pressure:.3f}")
            
            # [v7新機能] 支配的な層を判定
            dominant_layer, dominant_pressure = player.pressure_system.get_dominant_layer()
            print(f"  支配的層: {dominant_layer.name} ({dominant_pressure:.3f})")
            
            # [v7新機能] 層間葛藤を計算
            conflicts = player.pressure_system.get_layer_conflict_index()
            max_conflict = max(conflicts.items(), key=lambda x: x[1]) if conflicts else (None, 0.0)
            if max_conflict[0] and max_conflict[1] > 0.3:
                print(f"  ⚠️ 層間葛藤: {max_conflict[0]} = {max_conflict[1]:.3f}")
                self.total_layer_conflicts += 1
                
                # 葛藤イベント記録
                player.layer_conflicts.append(LayerConflictEvent(
                    day=self.day,
                    player_name=player.name,
                    dominant_layer=dominant_layer.name,
                    conflict_pair=max_conflict[0],
                    conflict_index=max_conflict[1],
                    decision="調査中"
                ))
            
            # [v7新機能] 跳躍判定（R値ベース）
            leap_layer = player.pressure_system.should_trigger_leap(threshold=0.6)
            if leap_layer:
                print(f"  🔥 跳躍トリガー: {leap_layer.name}層")
                if leap_layer == SSDLayer.BASE:
                    print(f"      → 本能的行動（生存優先）")
                    player.base_leaps += 1
                elif leap_layer == SSDLayer.UPPER:
                    print(f"      → 理念的行動（戦略優先）")
                    player.upper_leaps += 1
                elif leap_layer == SSDLayer.PHYSICAL:
                    print(f"      → 物理的制約（強制的行動変更）")
                    player.physical_constraints += 1
            
            # 既存のロジック継続（戦略DB、思考フェーズ、認知的不協和）
            strategy = self.query_strategy_db(player)
            if strategy and strategy.strategy:
                print(f"  📖 戦略DB参照: {strategy.strategy.name} (信頼度={strategy.confidence:.2f})")
                self.total_strategies_invoked += 1
            
            thought = self.thinking_phase(player, alive_players)
            if thought:
                print(f"  💭 内的シミュレーション: {thought.target} "
                      f"(疑惑Δ={thought.predicted_suspicion_change:+.1f}, "
                      f"信頼Δ={thought.predicted_trust_impact:+.1f})")
            
            # 認知的不協和解決
            conflict_result = self.resolve_cognitive_conflict(player, strategy, thought)
            if conflict_result.conflict_detected:
                print(f"  ⚖️ 認知的不協和検出")
                print(f"      戦略提案: {conflict_result.strategy_suggestion}")
                print(f"      思考提案: {conflict_result.thought_suggestion}")
                print(f"      解決: {conflict_result.resolution}")
                print(f"      最終決定: {conflict_result.final_decision}")
                player.cognitive_conflicts += 1
                self.total_cognitive_conflicts += 1
            
            # [v7改良] ルールブレイク（四層構造圧力を使用）
            rulebreak = self.attempt_rulebreak(player, pressures)
            if rulebreak:
                print(f"  🚨 ルールブレイク: {rulebreak.break_type.value}")
            
            # [v7改良] ペルソナ変異（四層構造圧力を使用）
            self.attempt_persona_transition(player, pressures)
            
            # SSDエンジン更新
            total_pressure_value = sum(pressures.values())
            p_external = np.array([total_pressure_value, 0.0, 0.0])
            
            new_state = player.engine.step(player.state, p_external, dt=1.0)
            
            if new_state.is_critical:
                self.phase_transitions += 1
                print(f"  ⚡ 相転移発生! E_i({player.state.E_indirect:.1f}) < Θ({player.engine.params.Theta_critical:.1f})")
                print(f"      → γ_i2d強化: 言葉→暴力への跳躍")
            
            player.state = new_state
            player.statement_count += 1
            
            # 疑惑レベル更新
            player.suspicion_level += random.uniform(-0.5, 1.0)
            player.suspicion_level = max(0.0, player.suspicion_level)
            
            print(f"  最終状態: E_d={player.state.E_direct:.1f}, "
                  f"E_i={player.state.E_indirect:.1f}, κ={player.state.kappa:.2f}")
    
    def print_final_statistics(self):
        """最終統計（v7版: 四層構造統計を含む）"""
        print("\n" + "=" * 70)
        print("最終統計")
        print("=" * 70)
        
        print(f"\n[システム全体]")
        print(f"  総ターン数: {self.day}")
        print(f"  相転移回数: {self.phase_transitions}")
        print(f"  戦略DB参照: {self.total_strategies_invoked}回")
        print(f"  認知的不協和: {self.total_cognitive_conflicts}回")
        print(f"  層間葛藤: {self.total_layer_conflicts}回")  # [v7]
        print(f"  ルールブレイク: {self.total_rulebreaks}回")
        
        print(f"\n[プレイヤー別統計]")
        for p in self.players:
            print(f"\n  {p.name} ({p.role} / {p.persona.value}):")
            print(f"    発言: {p.statement_count}回")
            print(f"    思考: {p.simulations_performed}回")
            print(f"    戦略: {len(p.strategies_used)}回")
            print(f"    認知的不協和: {p.cognitive_conflicts}回")
            print(f"    ペルソナ変異: {p.persona_transitions}回")
            print(f"    ルールブレイク: {p.rulebreaks_performed}回")
            
            # [v7新機能] 四層構造統計
            print(f"    BASE跳躍: {p.base_leaps}回")
            print(f"    UPPER跳躍: {p.upper_leaps}回")
            print(f"    PHYSICAL制約: {p.physical_constraints}回")
            print(f"    層間葛藤: {len(p.layer_conflicts)}回")
            
            if p.layer_conflicts:
                print(f"    主要葛藤:")
                for conflict in p.layer_conflicts[:3]:  # 上位3件
                    print(f"      Day{conflict.day}: {conflict.conflict_pair} "
                          f"({conflict.conflict_index:.3f})")
            
            print(f"    最終状態: E_d={p.state.E_direct:.1f}, "
                  f"E_i={p.state.E_indirect:.1f}, κ={p.state.kappa:.2f}")

# ========== メイン実行 ==========
if __name__ == "__main__":
    game = WerewolfGameV7()
    game.setup_game()
    
    # 3日分実行
    for _ in range(3):
        game.run_day_phase()
    
    game.print_final_statistics()
    
    print("\n" + "=" * 70)
    print("✅ v7.0デモ完了")
    print("=" * 70)
    print("\n💡 v7.0の理論的成果:")
    print("  1. 四層構造圧力の可視化 → どの構造層が悲鳴を上げているかを区別")
    print("  2. 層間葛藤の定量化 → BASE×UPPER高 = 本能と理念の対立")
    print("  3. R値ベースの跳躍判定 → 最も動かしにくい層が最優先で跳躍")
    print("  4. 人間らしいAI → 構造的葛藤を抱え、それを解決しようとする主体")
