"""
SSD Social Dynamics - 社会的相互作用モジュール
===============================================

Phase 4機能: エージェント間の社会的カップリング

機能:
1. エネルギー伝播（zeta係数）
2. κ伝播（xi係数）
3. 競合抑制（omega係数）
4. 関係性マトリクス（協力/競争）

原典理論:
https://github.com/HermannDegner/Structural-Subjectivity-Dynamics
→ Human_Module/人間モジュール　コア.md
   「基層構造の内部における二重性: 個体維持 vs 社会維持」
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

from ssd_human_module import HumanAgent, HumanParams, HumanPressure, HumanLayer


class RelationType(Enum):
    """関係性タイプ"""
    COOPERATION = 1    # 協力関係
    NEUTRAL = 0        # 中立
    COMPETITION = -1   # 競争関係


@dataclass
class SocialCouplingParams:
    """
    社会的カップリングパラメータ
    
    原典の「社会維持の原理」に基づく
    """
    # エネルギー伝播係数（zeta）
    zeta_physical: float = 0.02   # 物理層（疲労の伝染は弱い）
    zeta_base: float = 0.08       # 基層（感情の伝染は強い）
    zeta_core: float = 0.05       # 中核層（規範の伝播は中程度）
    zeta_upper: float = 0.03      # 上層（理念の伝播は弱い）
    
    # κ伝播係数（xi）
    xi_physical: float = 0.01     # 物理層（身体技術の伝達は遅い）
    xi_base: float = 0.04         # 基層（本能的学習は中速）
    xi_core: float = 0.06         # 中核層（規範学習は速い）
    xi_upper: float = 0.05        # 上層（理念学習は速い）
    
    # 競合抑制係数（omega、負値）
    omega_physical: float = -0.01  # 物理層（競合は弱い）
    omega_base: float = -0.06      # 基層（本能的競合は強い）
    omega_core: float = -0.03      # 中核層（規範的競合は中程度）
    omega_upper: float = -0.02     # 上層（理念的競合は弱い）
    
    # 協力閾値
    cooperation_threshold: float = 0.5   # relation > 0.5で協力
    competition_threshold: float = -0.5  # relation < -0.5で競争


@dataclass
class RelationshipMatrix:
    """
    関係性マトリクス
    
    agents[i]のagents[j]に対する関係性
    値域: [-1.0, 1.0]
    - 1.0: 完全な協力
    - 0.0: 中立
    - -1.0: 完全な競争
    """
    matrix: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    
    def __post_init__(self):
        """対角成分を0にする（自己との関係は無し）"""
        np.fill_diagonal(self.matrix, 0.0)
    
    @classmethod
    def create_random(cls, num_agents: int, cooperation_bias: float = 0.0):
        """
        ランダム関係性マトリクスの生成
        
        Args:
            num_agents: エージェント数
            cooperation_bias: 協力バイアス（-1.0〜1.0）
        """
        matrix = np.random.uniform(-1.0, 1.0, (num_agents, num_agents))
        matrix += cooperation_bias
        matrix = np.clip(matrix, -1.0, 1.0)
        np.fill_diagonal(matrix, 0.0)
        return cls(matrix=matrix)
    
    @classmethod
    def create_cooperative(cls, num_agents: int):
        """完全協力関係"""
        matrix = np.ones((num_agents, num_agents))
        np.fill_diagonal(matrix, 0.0)
        return cls(matrix=matrix)
    
    @classmethod
    def create_competitive(cls, num_agents: int):
        """完全競争関係"""
        matrix = -np.ones((num_agents, num_agents))
        np.fill_diagonal(matrix, 0.0)
        return cls(matrix=matrix)
    
    def get_relation(self, i: int, j: int) -> float:
        """i→jの関係性を取得"""
        return self.matrix[i, j]
    
    def set_relation(self, i: int, j: int, value: float):
        """i→jの関係性を設定"""
        self.matrix[i, j] = np.clip(value, -1.0, 1.0)


class Society:
    """
    社会システム（多エージェント）
    
    Phase 4機能を実装したエージェント集団のシミュレーター
    """
    
    def __init__(
        self,
        num_agents: int = 10,
        human_params: Optional[HumanParams] = None,
        social_params: Optional[SocialCouplingParams] = None,
        relationships: Optional[RelationshipMatrix] = None
    ):
        self.num_agents = num_agents
        self.social_params = social_params or SocialCouplingParams()
        
        # エージェント生成
        self.agents: List[HumanAgent] = []
        for i in range(num_agents):
            agent = HumanAgent(
                params=human_params or HumanParams(),
                agent_id=f"Agent_{i}"
            )
            self.agents.append(agent)
        
        # 関係性マトリクス
        if relationships is None:
            self.relationships = RelationshipMatrix.create_random(num_agents)
        else:
            self.relationships = relationships
        
        # 時間
        self.t = 0.0
    
    def _compute_social_coupling_for_agent(
        self,
        agent_idx: int
    ) -> Dict[str, np.ndarray]:
        """
        特定エージェントへの社会的カップリングを計算
        
        Returns:
            {
                'energy_coupling': 各層へのエネルギー影響（4次元）,
                'kappa_coupling': 各層へのκ影響（4次元）
            }
        """
        agent = self.agents[agent_idx]
        
        # 各層へのカップリング
        energy_coupling = np.zeros(4)
        kappa_coupling = np.zeros(4)
        
        # 全ての他エージェントからの影響を集計
        for other_idx in range(self.num_agents):
            if other_idx == agent_idx:
                continue
            
            other_agent = self.agents[other_idx]
            relation = self.relationships.get_relation(agent_idx, other_idx)
            
            # 関係性タイプ判定
            if relation > self.social_params.cooperation_threshold:
                relation_type = RelationType.COOPERATION
                relation_factor = relation  # 正の係数
            elif relation < self.social_params.competition_threshold:
                relation_type = RelationType.COMPETITION
                relation_factor = abs(relation)  # 負の関係を正に変換
            else:
                relation_type = RelationType.NEUTRAL
                relation_factor = 0.0
            
            if relation_type == RelationType.NEUTRAL:
                continue
            
            # 各層のカップリング計算
            for layer_idx in range(4):
                # エネルギー伝播
                E_self = agent.state.E[layer_idx]
                E_other = other_agent.state.E[layer_idx]
                
                # κ伝播
                kappa_self = agent.state.kappa[layer_idx]
                kappa_other = other_agent.state.kappa[layer_idx]
                
                # 層別係数
                if layer_idx == HumanLayer.PHYSICAL.value:
                    zeta = self.social_params.zeta_physical
                    xi = self.social_params.xi_physical
                    omega = self.social_params.omega_physical
                elif layer_idx == HumanLayer.BASE.value:
                    zeta = self.social_params.zeta_base
                    xi = self.social_params.xi_base
                    omega = self.social_params.omega_base
                elif layer_idx == HumanLayer.CORE.value:
                    zeta = self.social_params.zeta_core
                    xi = self.social_params.xi_core
                    omega = self.social_params.omega_core
                else:  # UPPER
                    zeta = self.social_params.zeta_upper
                    xi = self.social_params.xi_upper
                    omega = self.social_params.omega_upper
                
                # 協力関係の場合
                if relation_type == RelationType.COOPERATION:
                    # エネルギー伝播（差分に比例）
                    delta_E = (E_other - E_self) * zeta * relation_factor
                    energy_coupling[layer_idx] += delta_E
                    
                    # κ伝播（高い方が低い方を引き上げる）
                    if kappa_other > kappa_self:
                        delta_kappa = (kappa_other - kappa_self) * xi * relation_factor
                        kappa_coupling[layer_idx] += delta_kappa
                
                # 競争関係の場合
                elif relation_type == RelationType.COMPETITION:
                    # 競合抑制（相手のエネルギーが自分を抑制）
                    suppression = omega * E_other * relation_factor
                    energy_coupling[layer_idx] += suppression
        
        return {
            'energy_coupling': energy_coupling,
            'kappa_coupling': kappa_coupling
        }
    
    def step(self, pressures: Optional[List[HumanPressure]] = None, dt: float = 0.1):
        """
        社会全体の1ステップ更新
        
        Args:
            pressures: 各エージェントへの外部圧力（Noneの場合はゼロ圧力）
            dt: 時間刻み
        """
        if pressures is None:
            pressures = [HumanPressure() for _ in range(self.num_agents)]
        
        # 各エージェントの社会的カップリングを計算
        social_couplings = []
        for i in range(self.num_agents):
            coupling = self._compute_social_coupling_for_agent(i)
            social_couplings.append(coupling)
        
        # 各エージェントを更新（社会的カップリングを反映）
        for i, agent in enumerate(self.agents):
            # 基本ステップ
            agent.step(pressures[i], dt=dt)
            
            # 社会的カップリングを状態に加算
            coupling = social_couplings[i]
            agent.state.E += coupling['energy_coupling'] * dt
            agent.state.kappa += coupling['kappa_coupling'] * dt
            
            # κの範囲制約
            kappa_min = np.array([
                agent.params.kappa_min_physical,
                agent.params.kappa_min_base,
                agent.params.kappa_min_core,
                agent.params.kappa_min_upper
            ])
            agent.state.kappa = np.maximum(kappa_min, agent.state.kappa)
        
        self.t += dt
    
    def get_social_network_state(self) -> Dict:
        """
        社会ネットワークの状態を取得
        
        Returns:
            エージェント状態と関係性の辞書
        """
        agent_states = []
        for agent in self.agents:
            agent_states.append(agent.get_psychological_state())
        
        return {
            "time": self.t,
            "num_agents": self.num_agents,
            "agents": agent_states,
            "relationships": self.relationships.matrix.tolist()
        }
    
    def get_dominant_layers_distribution(self) -> Dict[str, int]:
        """
        支配層の分布を取得
        
        Returns:
            各層が支配的なエージェントの数
        """
        distribution = {
            "PHYSICAL": 0,
            "BASE": 0,
            "CORE": 0,
            "UPPER": 0
        }
        
        for agent in self.agents:
            dominant = agent.get_dominant_layer()
            distribution[dominant.name] += 1
        
        return distribution
    
    def visualize_network(self):
        """
        社会ネットワークの可視化（簡易版）
        
        Note: 本格的な可視化にはnetworkx/matplotlibが必要
        """
        print("\n=== Social Network State ===")
        print(f"Time: {self.t:.1f}")
        print(f"Agents: {self.num_agents}")
        print("\nDominant Layers:")
        dist = self.get_dominant_layers_distribution()
        for layer, count in dist.items():
            print(f"  {layer}: {count} agents")
        
        print("\nRelationship Matrix (sample):")
        print(self.relationships.matrix[:5, :5])  # 最初の5x5のみ表示
        
        print("\nAgent States (sample):")
        for i in range(min(3, self.num_agents)):
            print(f"\n{self.agents[i]}")


# ============================================================================
# シナリオヘルパー
# ============================================================================

def create_fear_contagion_scenario(num_agents: int = 5) -> Society:
    """
    恐怖伝染シナリオ
    
    1人のエージェントが高いE_baseを持ち、他に伝播する
    """
    society = Society(
        num_agents=num_agents,
        relationships=RelationshipMatrix.create_cooperative(num_agents)
    )
    
    # Agent_0に高い恐怖（E_base）を設定
    society.agents[0].state.E[HumanLayer.BASE.value] = 150.0
    
    return society


def create_ideology_conflict_scenario(num_agents: int = 6) -> Society:
    """
    イデオロギー対立シナリオ
    
    グループA（3人）とグループB（3人）が競争関係
    """
    society = Society(num_agents=num_agents)
    
    # グループ内は協力、グループ間は競争
    for i in range(3):
        for j in range(3):
            # グループA内部
            society.relationships.set_relation(i, j, 0.8)
            # グループB内部
            society.relationships.set_relation(i+3, j+3, 0.8)
            # A→B競争
            society.relationships.set_relation(i, j+3, -0.9)
            # B→A競争
            society.relationships.set_relation(i+3, j, -0.9)
    
    # 各グループに異なる理念エネルギー
    for i in range(3):
        society.agents[i].state.E[HumanLayer.UPPER.value] = 50.0
        society.agents[i+3].state.E[HumanLayer.UPPER.value] = 45.0
    
    return society


def create_norm_propagation_scenario(num_agents: int = 7) -> Society:
    """
    規範伝播シナリオ
    
    1人の「模範エージェント」が高いκ_coreを持ち、他に伝播
    """
    society = Society(
        num_agents=num_agents,
        relationships=RelationshipMatrix.create_cooperative(num_agents)
    )
    
    # Agent_0を模範として設定（高いκ_core）
    society.agents[0].state.kappa[HumanLayer.CORE.value] = 1.8
    
    return society
