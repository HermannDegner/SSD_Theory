"""
SSD v8.0 層別E・κ統合版: 人狼ゲームAI

v7からv8への理論的跳躍:
=====================================
v7の限界:
- E_indirectが単一プール → 本能的不満と理念的不満を区別できない
- kappaが単一値 → 本能的学習と理念的学習を区別できない
- 層別圧力を計算しても、最終的には単一Eに混ぜ込まれる

v8の革新:
- ssd_core_engine_v4.py の統合
  * E_base, E_core, E_upper の独立管理
  * kappa_base, kappa_core, kappa_upper の独立学習
  * 層別の臨界判定と異なるタイプの跳躍
  
理論的意義:
----------
1. 本能的跳躍 vs 理念的跳躍の区別:
   E_base高 → 衝動的行動（パニック、逃走）
   E_upper高 → 計画的行動（革命、メタ戦略）
   
2. 構造的抵抗の可視化:
   kappa × R = 動かしにくさ
   BASE: kappa_base(大) × R(100.0) = 最も強固
   UPPER: kappa_upper(小) × R(1.0) = 最も柔軟
   
3. 葛藤解決の高度化:
   構造的影響力 = Pressure × E × kappa × R
   最も影響力が高い層が行動を支配
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Callable
import random
import numpy as np

# ========== [v8核心] SSD v4.0コアエンジン（層別E・κ）インポート ==========
from ssd_core_engine_v4 import (
    SSDCoreEngineV4,
    SSDStateV4,
    SSDParametersV4,
    SSDLayer
)

# ========== [v8継続] 四層構造多次元意味圧システム ==========
from ssd_multidimensional_pressure_v2 import (
    MultiDimensionalPressure
)

# ========== v7継承: ペルソナシステム ==========
class Persona(Enum):
    STEALTH = "潜伏型"
    AGGRESSIVE = "攻撃型"
    LEADER = "リーダー型"
    DISRUPTOR = "攪乱型"

@dataclass
class PersonaTransition:
    from_persona: Persona
    to_persona: Persona
    probability: float
    trigger_message: str

PERSONA_TRANSITIONS = [
    PersonaTransition(Persona.STEALTH, Persona.AGGRESSIVE, 0.30, "開き直った"),
    PersonaTransition(Persona.STEALTH, Persona.DISRUPTOR, 0.15, "暴走した"),
    PersonaTransition(Persona.AGGRESSIVE, Persona.STEALTH, 0.40, "潜伏に回帰した"),
    PersonaTransition(Persona.AGGRESSIVE, Persona.DISRUPTOR, 0.20, "制御不能になった"),
    PersonaTransition(Persona.LEADER, Persona.DISRUPTOR, 0.20, "反乱を起こした"),
    PersonaTransition(Persona.LEADER, Persona.AGGRESSIVE, 0.25, "強硬路線に転じた"),
    PersonaTransition(Persona.DISRUPTOR, Persona.STEALTH, 0.35, "静かになった"),
]

# ========== v7継承: 戦略データベース ==========
@dataclass
class GameStrategy:
    name: str
    condition: callable
    action_type: str
    priority: float
    description: str
    energy_cost_layer: str = "CORE"  # [v8] エネルギー消費層を指定

STRATEGY_DB: List[GameStrategy] = [
    GameStrategy(
        name="EARLY_SILENCE",
        condition=lambda ctx: ctx.get('day') == 1 and ctx.get('role') == 'WEREWOLF',
        action_type="MINIMIZE_STATEMENTS",
        priority=7.0,
        description="序盤は情報を与えるな",
        energy_cost_layer="CORE"
    ),
    GameStrategy(
        name="TRUST_BUILDING",
        condition=lambda ctx: ctx.get('suspicion_level', 0) > 5.0,
        action_type="COOPERATIVE_VOTE",
        priority=6.0,
        description="疑われたら協調行動で信頼回復",
        energy_cost_layer="CORE"
    ),
    GameStrategy(
        name="DIVIDE_CONQUER",
        condition=lambda ctx: ctx.get('role') == 'WEREWOLF' and ctx.get('villagers_alive') > 3,
        action_type="TARGET_ALLIANCE",
        priority=5.0,
        description="村人同盟を分断せよ",
        energy_cost_layer="UPPER"
    ),
]

# ========== [v8新機能] 構造的影響力モデル ==========
@dataclass
class StructuralPower:
    """構造的影響力 = Pressure × E × kappa × R"""
    layer_name: str
    pressure: float
    energy: float
    kappa: float
    R_value: float
    total_power: float
    
    def __str__(self):
        return (f"{self.layer_name}: "
                f"P={self.pressure:.2f} × E={self.energy:.1f} × "
                f"κ={self.kappa:.2f} × R={self.R_value:.1f} "
                f"= {self.total_power:.1f}")

# ========== プレイヤークラス（v8完全版） ==========
@dataclass
class WerewolfPlayerV8:
    name: str
    role: str
    engine: SSDCoreEngineV4
    state: SSDStateV4
    pressure_system: MultiDimensionalPressure
    persona: Persona
    alive: bool = True
    suspicion_level: float = 0.0
    trust_map: Dict[str, float] = field(default_factory=dict)
    statement_count: int = 0
    
    # [v8新機能] 層別跳躍統計
    base_instinct_leaps: int = 0      # BASE層由来の本能的跳躍
    core_normative_leaps: int = 0     # CORE層由来の規範的跳躍
    upper_ideological_leaps: int = 0  # UPPER層由来の理念的跳躍
    
    # v7継承統計
    strategies_used: List[str] = field(default_factory=list)
    persona_transitions: int = 0
    cognitive_conflicts: int = 0

# ========== ゲームマスター（v8完全版） ==========
class WerewolfGameV8:
    def __init__(self):
        self.players: List[WerewolfPlayerV8] = []
        self.day = 0
        self.events = []
        self.seer_revealed = False
        
        # [v8新機能] 層別跳躍統計
        self.total_base_leaps = 0
        self.total_core_leaps = 0
        self.total_upper_leaps = 0
        
    def log_event(self, message: str):
        self.events.append(f"  {message}")
        print(f"  {message}")
    
    # ========== [v8核心機能] 四層構造圧力計算関数群 ==========
    
    def survival_instinct_calculator(self, player: WerewolfPlayerV8) -> Callable:
        """BASE層: 生存本能（疑惑恐怖）"""
        def calc(context: dict) -> float:
            # 疑惑レベルが高いほど生存本能が高まる
            return min(1.0, player.suspicion_level / 10.0)
        return calc
    
    def risk_avoidance_calculator(self, player: WerewolfPlayerV8) -> Callable:
        """BASE層: リスク回避本能"""
        def calc(context: dict) -> float:
            accusers = sum(1 for p in self.players 
                          if p.alive and p.name != player.name 
                          and player.trust_map.get(p.name, 0.5) < 0.3)
            return min(1.0, accusers / 4.0)
        return calc
    
    def role_performance_calculator(self, player: WerewolfPlayerV8) -> Callable:
        """CORE層: 役割遂行圧力"""
        def calc(context: dict) -> float:
            if player.role == "WEREWOLF":
                werewolves = sum(1 for p in self.players if p.alive and p.role == "WEREWOLF")
                return max(0.0, 1.0 - werewolves / 2.0)
            else:
                return min(1.0, player.suspicion_level / 8.0)
        return calc
    
    def trust_system_calculator(self, player: WerewolfPlayerV8) -> Callable:
        """CORE層: 信頼システム圧力"""
        def calc(context: dict) -> float:
            allies = sum(1 for p in self.players 
                        if p.alive and player.trust_map.get(p.name, 0.5) > 0.7)
            return max(0.0, 1.0 - allies / 3.0)
        return calc
    
    def strategic_narrative_calculator(self, player: WerewolfPlayerV8) -> Callable:
        """UPPER層: 戦略的物語圧力"""
        def calc(context: dict) -> float:
            return min(1.0, self.day / 4.0)
        return calc
    
    def ideological_pressure_calculator(self, player: WerewolfPlayerV8) -> Callable:
        """UPPER層: 理念圧力"""
        def calc(context: dict) -> float:
            if player.persona == Persona.LEADER:
                return 0.7
            elif player.persona == Persona.DISRUPTOR:
                return 0.2
            else:
                return 0.4
        return calc
    
    def create_werewolf_pressure_v8(self, player: WerewolfPlayerV8) -> None:
        """[v8] 四層構造多次元意味圧の登録"""
        
        # BASE層
        player.pressure_system.register_dimension(
            name='survival_instinct',
            calculator=self.survival_instinct_calculator(player),
            layer=SSDLayer.BASE,
            weight=0.6,
            description='生存本能（疑惑恐怖）'
        )
        player.pressure_system.register_dimension(
            name='risk_avoidance',
            calculator=self.risk_avoidance_calculator(player),
            layer=SSDLayer.BASE,
            weight=0.4,
            description='リスク回避本能'
        )
        
        # CORE層
        player.pressure_system.register_dimension(
            name='role_performance',
            calculator=self.role_performance_calculator(player),
            layer=SSDLayer.CORE,
            weight=0.5,
            description='役割遂行圧力'
        )
        player.pressure_system.register_dimension(
            name='trust_system',
            calculator=self.trust_system_calculator(player),
            layer=SSDLayer.CORE,
            weight=0.5,
            description='信頼システム圧力'
        )
        
        # UPPER層
        player.pressure_system.register_dimension(
            name='strategic_narrative',
            calculator=self.strategic_narrative_calculator(player),
            layer=SSDLayer.UPPER,
            weight=0.6,
            description='戦略的物語圧力'
        )
        player.pressure_system.register_dimension(
            name='ideological_pressure',
            calculator=self.ideological_pressure_calculator(player),
            layer=SSDLayer.UPPER,
            weight=0.4,
            description='理念圧力'
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
        """ゲーム初期化（v8版）"""
        names = ["太郎", "次郎", "三郎", "四郎", "五郎"]
        roles = ["WEREWOLF", "WEREWOLF", "VILLAGER", "SEER", "VILLAGER"]
        
        print("=" * 70)
        print("SSD v8.0 層別E・κ統合版: 人狼ゲームAI")
        print("=" * 70)
        print("\n[初期配置]")
        
        for name, role in zip(names, roles):
            persona = self.assign_persona(role)
            
            # [v8] v4.0エンジン初期化
            params = SSDParametersV4()
            engine = SSDCoreEngineV4(params)
            
            # [v8] 層別初期状態
            if role == "WEREWOLF":
                state = SSDStateV4(
                    E_direct=50.0,
                    E_base=80.0,
                    E_core=60.0,
                    E_upper=40.0,
                    kappa_base=1.5,
                    kappa_core=1.0,
                    kappa_upper=0.5
                )
            elif role == "SEER":
                state = SSDStateV4(
                    E_direct=40.0,
                    E_base=50.0,
                    E_core=70.0,
                    E_upper=80.0,
                    kappa_base=1.2,
                    kappa_core=1.1,
                    kappa_upper=0.8
                )
            else:
                state = SSDStateV4(
                    E_direct=45.0,
                    E_base=60.0,
                    E_core=55.0,
                    E_upper=50.0,
                    kappa_base=1.3,
                    kappa_core=1.0,
                    kappa_upper=0.6
                )
            
            pressure_system = MultiDimensionalPressure()
            
            player = WerewolfPlayerV8(
                name=name, role=role, engine=engine, state=state,
                pressure_system=pressure_system, persona=persona
            )
            self.players.append(player)
            
            self.create_werewolf_pressure_v8(player)
            
            print(f"  {name}: {role} / {persona.value}")
            print(f"    E: base={state.E_base:.0f}, core={state.E_core:.0f}, "
                  f"upper={state.E_upper:.0f}, direct={state.E_direct:.0f}")
            print(f"    κ: base={state.kappa_base:.2f}, core={state.kappa_core:.2f}, "
                  f"upper={state.kappa_upper:.2f}")
        
        for p in self.players:
            p.trust_map = {other.name: 0.5 for other in self.players if other.name != p.name}
    
    def calculate_structural_power(self, player: WerewolfPlayerV8, 
                                    pressures: Dict[SSDLayer, float]) -> Dict[str, StructuralPower]:
        """
        [v8核心機能] 構造的影響力の計算
        
        理論: 構造的影響力 = Pressure × E × kappa × R
        最も影響力が高い層が行動を支配
        """
        R_values = {
            'BASE': 100.0,
            'CORE': 10.0,
            'UPPER': 1.0
        }
        
        powers = {}
        
        # BASE層
        p_base = pressures.get(SSDLayer.BASE, 0.0)
        power_base = (p_base * player.state.E_base * 
                     player.state.kappa_base * R_values['BASE'])
        powers['BASE'] = StructuralPower(
            layer_name='BASE',
            pressure=p_base,
            energy=player.state.E_base,
            kappa=player.state.kappa_base,
            R_value=R_values['BASE'],
            total_power=power_base
        )
        
        # CORE層
        p_core = pressures.get(SSDLayer.CORE, 0.0)
        power_core = (p_core * player.state.E_core * 
                     player.state.kappa_core * R_values['CORE'])
        powers['CORE'] = StructuralPower(
            layer_name='CORE',
            pressure=p_core,
            energy=player.state.E_core,
            kappa=player.state.kappa_core,
            R_value=R_values['CORE'],
            total_power=power_core
        )
        
        # UPPER層
        p_upper = pressures.get(SSDLayer.UPPER, 0.0)
        power_upper = (p_upper * player.state.E_upper * 
                      player.state.kappa_upper * R_values['UPPER'])
        powers['UPPER'] = StructuralPower(
            layer_name='UPPER',
            pressure=p_upper,
            energy=player.state.E_upper,
            kappa=player.state.kappa_upper,
            R_value=R_values['UPPER'],
            total_power=power_upper
        )
        
        return powers
    
    def query_strategy_db(self, player: WerewolfPlayerV8) -> Optional[GameStrategy]:
        """戦略DB参照（v8: 層別エネルギー消費）"""
        # [v8] CORE層エネルギー不足なら参照不可
        if player.state.E_core < 15.0:
            return None
        
        context = {
            'day': self.day,
            'role': player.role,
            'suspicion_level': player.suspicion_level,
            'werewolves_alive': sum(1 for p in self.players if p.alive and p.role == "WEREWOLF"),
            'villagers_alive': sum(1 for p in self.players if p.alive and p.role != "WEREWOLF"),
        }
        
        applicable = [s for s in STRATEGY_DB if s.condition(context)]
        if not applicable:
            return None
        
        best = max(applicable, key=lambda s: s.priority)
        
        # [v8] 指定された層からエネルギー消費
        if best.energy_cost_layer == "BASE":
            player.state.E_base = max(0, player.state.E_base - 15.0)
        elif best.energy_cost_layer == "CORE":
            player.state.E_core = max(0, player.state.E_core - 15.0)
        elif best.energy_cost_layer == "UPPER":
            player.state.E_upper = max(0, player.state.E_upper - 15.0)
        
        player.strategies_used.append(best.name)
        return best
    
    def run_day_phase(self):
        """1日フェーズの実行（v8版）"""
        self.day += 1
        print(f"\n{'='*70}")
        print(f"Day {self.day}")
        print(f"{'='*70}")
        
        alive_players = [p for p in self.players if p.alive]
        
        for player in alive_players:
            print(f"\n[{player.name}のターン] ({player.role} / {player.persona.value})")
            
            # [v8] 四層構造圧力計算
            context = {}
            pressures = player.pressure_system.calculate(context)
            
            print(f"  層別圧力:")
            for layer, pressure in pressures.items():
                if layer != SSDLayer.PHYSICAL:
                    print(f"    {layer.name:10s}: {pressure:.3f}")
            
            # [v8核心機能] 構造的影響力計算
            structural_powers = self.calculate_structural_power(player, pressures)
            
            print(f"\n  構造的影響力 (P×E×κ×R):")
            for layer_name, power in structural_powers.items():
                print(f"    {power}")
            
            # 支配的な層を判定
            dominant = max(structural_powers.items(), key=lambda x: x[1].total_power)
            print(f"\n  支配的層: {dominant[0]} (影響力={dominant[1].total_power:.1f})")
            
            # [v8] 戦略DB参照
            strategy = self.query_strategy_db(player)
            if strategy:
                print(f"  [戦略] {strategy.name}")
            
            # [v8核心機能] v4.0エンジン更新（層別圧力を投入）
            p_base = np.array([pressures.get(SSDLayer.BASE, 0.0), 0.0, 0.0])
            p_core = np.array([pressures.get(SSDLayer.CORE, 0.0), 0.0, 0.0])
            p_upper = np.array([pressures.get(SSDLayer.UPPER, 0.0), 0.0, 0.0])
            
            new_state = player.engine.step(player.state, p_base, p_core, p_upper, dt=1.0)
            
            # [v8] 層別相転移検出
            if new_state.is_critical_base:
                print(f"  [!] BASE層相転移! 本能的跳躍（パニック、逃走）")
                player.base_instinct_leaps += 1
                self.total_base_leaps += 1
            
            if new_state.is_critical_core:
                print(f"  [!] CORE層相転移! 規範的跳躍（ルール破壊）")
                player.core_normative_leaps += 1
                self.total_core_leaps += 1
            
            if new_state.is_critical_upper:
                print(f"  [!] UPPER層相転移! 理念的跳躍（革命、メタ戦略）")
                player.upper_ideological_leaps += 1
                self.total_upper_leaps += 1
            
            player.state = new_state
            player.statement_count += 1
            player.suspicion_level += random.uniform(-0.5, 1.0)
            player.suspicion_level = max(0.0, player.suspicion_level)
            
            print(f"\n  最終エネルギー:")
            print(f"    E_base={player.state.E_base:.1f}, "
                  f"E_core={player.state.E_core:.1f}, "
                  f"E_upper={player.state.E_upper:.1f}")
            print(f"  整合慣性:")
            print(f"    κ_base={player.state.kappa_base:.2f}, "
                  f"κ_core={player.state.kappa_core:.2f}, "
                  f"κ_upper={player.state.kappa_upper:.2f}")
    
    def print_final_statistics(self):
        """最終統計（v8版）"""
        print("\n" + "=" * 70)
        print("最終統計")
        print("=" * 70)
        
        print(f"\n[システム全体]")
        print(f"  総ターン数: {self.day}")
        print(f"  BASE層跳躍: {self.total_base_leaps}回 （本能的）")
        print(f"  CORE層跳躍: {self.total_core_leaps}回 （規範的）")
        print(f"  UPPER層跳躍: {self.total_upper_leaps}回 （理念的）")
        
        print(f"\n[プレイヤー別統計]")
        for p in self.players:
            print(f"\n  {p.name} ({p.role} / {p.persona.value}):")
            print(f"    発言: {p.statement_count}回")
            print(f"    戦略: {len(p.strategies_used)}回")
            print(f"    BASE跳躍: {p.base_instinct_leaps}回")
            print(f"    CORE跳躍: {p.core_normative_leaps}回")
            print(f"    UPPER跳躍: {p.upper_ideological_leaps}回")
            
            # [v8] 支配的不満層
            dominant_frustration = p.engine.get_dominant_frustration_layer(p.state)
            print(f"    支配的不満層: {dominant_frustration[0]} ({dominant_frustration[1]:.1f})")
            
            # [v8] エネルギー分布
            distribution = p.engine.get_layer_energy_distribution(p.state)
            print(f"    エネルギー分布:")
            for layer, ratio in distribution.items():
                print(f"      {layer}: {ratio*100:.1f}%")


# ========== メイン実行 ==========
if __name__ == "__main__":
    game = WerewolfGameV8()
    game.setup_game()
    
    # 3日分実行
    for _ in range(3):
        game.run_day_phase()
    
    game.print_final_statistics()
    
    print("\n" + "=" * 70)
    print("[完了] v8.0デモ完了")
    print("=" * 70)
    print("\n[成果] v8.0の理論的成果:")
    print("  1. E層別分離 -> 本能的不満と理念的不満を区別")
    print("  2. κ層別分離 -> 本能的学習と理念的学習を区別")
    print("  3. 構造的影響力モデル -> P×E×κ×Rで行動決定")
    print("  4. 異なるタイプの跳躍 -> BASE/CORE/UPPER層別に相転移")
