"""
人狼ゲーム v10.2: 圧力システム統合版
Werewolf Game v10.2: Pressure System Integration

【Phase 10.2.2a - 圧力システム統合】
構造化記憶の解釈結果をSSDの圧力システム経由でHumanAgentに入力:
1. HumanAgentの内包 ✓
2. 創発的シグナル生成 ✓
3. 正確な因果学習 ✓
4. 圧力システム統合 ✓ ← NEW!

作成日: 2025年11月7日
バージョン: 10.2 (Pressure System Integrated)
"""

import numpy as np
import sys
import os
from typing import List, Dict, Tuple, Optional
import time

# 親ディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ssd_memory_structure import (
    StructuredMemoryStore,
    Concept,
    cosine_similarity
)

# SSDコアモジュールのインポート
from ssd_human_module import HumanAgent, HumanLayer, HumanPressure


class PlayerV10PressureIntegrated:
    """
    v10.2プレイヤー: 圧力システム完全統合
    
    【統合アーキテクチャ】
    観測 → 構造化記憶 → 意味圧 → HumanAgent → E蓄積 → 疑惑
    """
    
    def __init__(self, 
                 player_id: int,
                 name: str,
                 role: str,
                 max_clusters: int = 30):
        self.player_id = player_id
        self.name = name
        self.role = role
        self.is_alive = True
        
        # SSDコアエンジン
        self.agent = HumanAgent(agent_id=str(player_id))
        
        # 構造化記憶システム
        self.structured_memory = StructuredMemoryStore(
            max_clusters=max_clusters,
            cluster_threshold=0.35,
            min_concept_size=3
        )
        
        self.learned_concepts: List[Concept] = []
        
        # ゲーム固有の状態
        self.observation_history: Dict[int, List[np.ndarray]] = {}
        
        # 統計
        self.games_played = 0
        self.times_executed = 0
        self.times_survived = 0
        
        # 説明可能性（圧力情報も記録）
        self.last_decision_explanation: Dict = {}
        
        # 人狼の罪悪感
        self._internal_guilt = 0.0
    
    def observe_player(self, 
                      target_id: int,
                      target_signals: np.ndarray,
                      current_time: float) -> float:
        """
        他プレイヤーを観測
        
        【Phase 10.2.2a改善】
        構造化記憶 → 意味圧 → HumanAgent.step() → E蓄積
        """
        # 1. 構造化記憶による解釈
        kappa = self.agent.state.kappa
        pressure_interpretation = self.structured_memory.interpret_with_structure(
            signal=target_signals,
            kappa=kappa,
            use_concepts=True
        )
        
        # 2. 意味圧に変換 ← NEW!
        meaning_pressure = HumanPressure(
            physical=0.0,
            base=pressure_interpretation[1],      # BASE層（生存脅威）
            core=pressure_interpretation[2],      # CORE層（規範的違和感）
            upper=pressure_interpretation[3]      # UPPER層（理念的不一致）
        )
        
        # 3. HumanAgentに圧力を入力 ← CHANGED!
        # これによりE（未処理圧）が蓄積される
        self.agent.step(meaning_pressure, dt=0.1)
        
        # 4. 疑惑レベルはE_BASEから取得 ← CHANGED!
        suspicion = self.agent.state.E[HumanLayer.BASE.value]
        
        # CORE層の葛藤も考慮（社会的違和感）
        suspicion += 0.3 * self.agent.state.E[HumanLayer.CORE.value]
        
        suspicion = np.clip(suspicion, 0.0, 1.0)
        
        # 観測履歴に記録
        if target_id not in self.observation_history:
            self.observation_history[target_id] = []
        self.observation_history[target_id].append(target_signals.copy())
        
        # 説明用に記録（意味圧も含める）
        activated_concepts = [
            c for c in self.learned_concepts
            if c.matches(target_signals)
        ]
        
        self.last_decision_explanation[target_id] = {
            'suspicion': suspicion,
            'E_state': self.agent.state.E.copy(),
            'meaning_pressure': meaning_pressure,  # ← NEW!
            'pressure_interpretation': pressure_interpretation.copy(),
            'primary_concept': activated_concepts[0].name if activated_concepts else None
        }
        
        return suspicion
    
    def explain_suspicion(self, target_id: int) -> str:
        """
        疑惑の理由を説明（圧力情報も含む）
        
        【Phase 10.2.2a改善】
        概念 → 意味圧 → E蓄積 の流れを説明
        """
        if target_id not in self.last_decision_explanation:
            return "観測データなし"
        
        info = self.last_decision_explanation[target_id]
        suspicion = info['suspicion']
        primary_concept = info['primary_concept']
        E = info['E_state']
        pressure = info['meaning_pressure']
        
        if primary_concept:
            explanation = f"疑惑 {suspicion:.2f}: '{primary_concept}' → " \
                         f"意味圧(BASE={pressure.base:.2f}) → E_BASE={E[1]:.2f}"
        else:
            explanation = f"疑惑 {suspicion:.2f}: 新規 → " \
                         f"意味圧(BASE={pressure.base:.2f}) → E_BASE={E[1]:.2f}"
        
        return explanation
    
    def generate_signals(self) -> np.ndarray:
        """
        シグナルを創発的に生成
        
        【変更なし】v10.1と同じ
        """
        signals = np.zeros(7)
        E = self.agent.state.E
        kappa = self.agent.state.kappa
        
        # 基本シグナル
        signals[0] = E[0] * 0.3  # 姿勢
        signals[1] = E[1] * 0.4 + E[2] * 0.2  # 表情
        signals[2] = E[0] * 0.2 + E[1] * 0.3  # 音声
        
        # 社会的シグナル
        if E[2] > 0.5:
            signals[3] += 0.3 * E[2]  # 攻撃性
            signals[4] += 0.4 * E[2]  # 防御性
        else:
            signals[5] += 0.5 * (1.0 - E[2])  # 協調性
        
        signals[6] = E[3] * 0.4  # 理念的発言
        
        # ノイズ
        avg_kappa = np.mean(kappa)
        noise_level = 0.1 * (1.0 - avg_kappa)
        signals += np.random.randn(7) * noise_level
        
        return np.clip(signals, 0.0, 1.0)
    
    def decide_vote(self, alive_players: List[int]) -> int:
        """
        投票先を決定
        
        【Phase 10.2.2a改善】
        E_BASEが最も高い対象に投票
        """
        candidates = [p for p in alive_players if p != self.player_id]
        if not candidates:
            return -1
        
        # 各候補への疑惑を計算
        suspicions = {}
        for pid in candidates:
            if pid in self.last_decision_explanation:
                # 最近の疑惑レベル（E_BASEベース）
                suspicions[pid] = self.last_decision_explanation[pid]['suspicion']
            else:
                suspicions[pid] = 0.0
        
        return max(suspicions.items(), key=lambda x: x[1])[0] if suspicions else np.random.choice(candidates)
    
    def learn_from_outcome(self, 
                          outcome: str,
                          executed_player_id: Optional[int] = None,
                          executed_player_role: Optional[str] = None,
                          current_time: float = 0.0):
        """
        ゲーム結果から学習
        
        【変更なし】v10.1と同じ
        """
        if outcome == 'executed':
            my_signals = self.generate_signals()
            self.structured_memory.add_memory(
                signal=my_signals,
                layer=1,
                outcome=-0.8,
                timestamp=current_time
            )
            self.agent.state.kappa[1] = min(1.0, self.agent.state.kappa[1] + 0.2)
            self.times_executed += 1
        
        elif outcome == 'survived':
            if executed_player_id is not None and executed_player_role is not None:
                if executed_player_id in self.observation_history and self.observation_history[executed_player_id]:
                    executed_signals = self.observation_history[executed_player_id][-1]
                    
                    if executed_player_role == 'werewolf':
                        self.structured_memory.add_memory(
                            signal=executed_signals,
                            layer=1,
                            outcome=+0.9,
                            timestamp=current_time
                        )
                        self.agent.state.kappa[2] = min(1.0, self.agent.state.kappa[2] + 0.1)
                    else:
                        self.structured_memory.add_memory(
                            signal=executed_signals,
                            layer=2,
                            outcome=-0.7,
                            timestamp=current_time
                        )
                        self.agent.state.kappa[2] = max(0.1, self.agent.state.kappa[2] - 0.05)
            
            self.times_survived += 1
        
        elif outcome == 'won':
            self.agent.state.kappa = np.minimum(1.0, self.agent.state.kappa + 0.1)
        
        elif outcome == 'lost':
            self.agent.state.kappa = np.minimum(1.0, self.agent.state.kappa + 0.03)
        
        self.games_played += 1
        
        if self.games_played % 2 == 0:
            self.learned_concepts = self.structured_memory.extract_concepts()
    
    def update_internal_state(self, dt: float = 1.0):
        """
        内部状態の更新
        
        【変更なし】v10.1と同じ
        """
        if self.role == 'werewolf' and self.is_alive:
            guilt = HumanPressure(
                physical=0.0,
                base=0.0,
                core=0.05 * dt,
                upper=0.02 * dt
            )
            self.agent.step(guilt, dt=dt)
            self._internal_guilt += 0.05 * dt
        else:
            neutral = HumanPressure()
            self.agent.step(neutral, dt=dt)
    
    def get_learning_stats(self) -> Dict:
        """学習統計"""
        mem_stats = self.structured_memory.get_statistics()
        
        return {
            'games_played': self.games_played,
            'times_executed': self.times_executed,
            'survival_rate': self.times_survived / max(1, self.games_played),
            'n_concepts': mem_stats['n_concepts'],
            'E': self.agent.state.E.copy(),
            'kappa': self.agent.state.kappa.copy(),
            'internal_guilt': self._internal_guilt if self.role == 'werewolf' else 0.0,
            'top_concepts': mem_stats['concepts']
        }


class WerewolfGameV10PressureIntegrated:
    """人狼ゲーム v10.2 圧力システム統合版"""
    
    def __init__(self, num_players: int = 7, num_werewolves: int = 2):
        self.num_players = num_players
        self.num_werewolves = num_werewolves
        
        self.players: Dict[int, PlayerV10PressureIntegrated] = {}
        self._initialize_players()
        
        self.day_count = 0
        self.game_log: List[str] = []
        self.current_time = 0.0
    
    def _initialize_players(self):
        """プレイヤー初期化"""
        roles = ['werewolf'] * self.num_werewolves + \
                ['villager'] * (self.num_players - self.num_werewolves)
        np.random.shuffle(roles)
        
        for i in range(self.num_players):
            player = PlayerV10PressureIntegrated(
                player_id=i,
                name=f"Player{i}",
                role=roles[i]
            )
            self.players[i] = player
    
    def get_alive_players(self) -> List[int]:
        return [p for p, player in self.players.items() if player.is_alive]
    
    def get_alive_werewolves(self) -> List[int]:
        return [p for p, player in self.players.items() 
                if player.is_alive and player.role == 'werewolf']
    
    def check_game_end(self) -> Optional[str]:
        werewolves = self.get_alive_werewolves()
        villagers = [p for p, player in self.players.items() 
                    if player.is_alive and player.role == 'villager']
        
        if len(werewolves) == 0:
            return 'villager_win'
        elif len(werewolves) >= len(villagers):
            return 'werewolf_win'
        return None
    
    def day_phase(self, verbose: bool = True):
        """昼フェーズ"""
        self.day_count += 1
        alive = self.get_alive_players()
        
        self.game_log.append(f"\n=== Day {self.day_count} ===")
        self.game_log.append(f"生存者: {len(alive)}人")
        
        # 内部状態更新
        for pid in alive:
            self.players[pid].update_internal_state(dt=1.0)
        
        # シグナル生成
        signals_map = {pid: self.players[pid].generate_signals() for pid in alive}
        
        # 観測（圧力システム経由）
        for observer_id in alive:
            for target_id in alive:
                if target_id != observer_id:
                    self.players[observer_id].observe_player(
                        target_id, signals_map[target_id], self.current_time
                    )
        
        # 投票
        votes: Dict[int, int] = {}
        vote_details: List[str] = []
        
        for voter_id in alive:
            target = self.players[voter_id].decide_vote(alive)
            if target != -1:
                votes[target] = votes.get(target, 0) + 1
                explanation = self.players[voter_id].explain_suspicion(target)
                vote_details.append(
                    f"  {self.players[voter_id].name} → {self.players[target].name}: {explanation}"
                )
        
        # 処刑
        if votes:
            executed_id = max(votes.items(), key=lambda x: x[1])[0]
            executed = self.players[executed_id]
            executed_role = executed.role
            executed.is_alive = False
            
            self.game_log.append(f"投票結果: {executed.name} ({executed_role}) 処刑")
            
            if verbose:
                self.game_log.append("\n投票詳細:")
                for detail in vote_details[:5]:
                    self.game_log.append(detail)
            
            # 学習
            executed.learn_from_outcome('executed', current_time=self.current_time)
            
            for pid in alive:
                if pid != executed_id:
                    self.players[pid].learn_from_outcome(
                        'survived',
                        executed_player_id=executed_id,
                        executed_player_role=executed_role,
                        current_time=self.current_time
                    )
        
        self.current_time += 1.0
    
    def play_game(self, max_days: int = 10, verbose: bool = True) -> str:
        """ゲームをプレイ"""
        self.game_log.clear()
        self.game_log.append("=" * 60)
        self.game_log.append("人狼ゲーム v10.2 (圧力システム統合版)")
        self.game_log.append("=" * 60)
        
        for day in range(max_days):
            self.day_phase(verbose=verbose)
            
            result = self.check_game_end()
            if result:
                self.game_log.append(f"\n{'='*60}")
                self.game_log.append(f"ゲーム終了: {result}")
                self.game_log.append(f"{'='*60}")
                
                for player in self.players.values():
                    outcome = 'won' if (
                        (player.role == 'werewolf' and result == 'werewolf_win') or
                        (player.role == 'villager' and result == 'villager_win')
                    ) else 'lost'
                    player.learn_from_outcome(outcome, current_time=self.current_time)
                
                if verbose:
                    for log in self.game_log:
                        print(log)
                
                return result
        
        if verbose:
            for log in self.game_log:
                print(log)
        return 'villager_win'


def demo_pressure_integrated():
    """圧力システム統合版デモ"""
    print("="*70)
    print("人狼ゲーム v10.2 - 圧力システム統合版")
    print("="*70)
    print("\n[Phase 10.2.2a: 圧力システム統合]")
    print("- HumanAgent内包（E/κの力学）")
    print("- 創発的シグナル生成")
    print("- 正確な因果学習")
    print("- 圧力システム統合 <- NEW!")
    print("\n[アーキテクチャ]")
    print("観測 -> 構造化記憶 -> 意味圧 -> HumanAgent -> E蓄積 -> 疑惑")
    print()
    
    game = WerewolfGameV10PressureIntegrated(num_players=7, num_werewolves=2)
    result = game.play_game(verbose=True)
    
    print("\n" + "="*70)
    print("学習統計（圧力システム統合版）")
    print("="*70)
    
    for pid, player in game.players.items():
        stats = player.get_learning_stats()
        print(f"\n{player.name} ({player.role}):")
        print(f"  E: {stats['E']}")
        print(f"  κ: {stats['kappa']}")
        print(f"  概念: {stats['n_concepts']}個")
        
        if player.role == 'werewolf':
            print(f"  罪悪感: {stats['internal_guilt']:.3f}")
        
        if stats['top_concepts']:
            print(f"  主要概念: {stats['top_concepts'][0][0]}")


if __name__ == "__main__":
    demo_pressure_integrated()
    
    print("\n\n" + "="*70)
    print("Phase 10.2.2a 完了: 圧力システム統合")
    print("="*70)
    print("\n- 構造化記憶 -> 意味圧 -> HumanAgent")
    print("- E蓄積による疑惑レベル計算")
    print("- 説明可能性の向上（圧力情報含む）")
    print("\nSSD理論の完全統合達成！")
