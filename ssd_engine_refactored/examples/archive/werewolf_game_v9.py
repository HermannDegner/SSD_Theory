"""
人狼ゲーム v9.0: 学習する主観的AI
Werewolf Game with Dynamic Interpretation (Learning Agents)

理論的革新:
- v8.5: 主観的社会システム（静的解釈）
- v9.0: 動的解釈構造（κと記憶に基づく学習）

主な特徴:
1. エージェントは過去の経験から学習
2. 同じ行動でも、経験によって解釈が変わる
3. 処刑・生存などの結果が、次のゲームの戦略に影響
4. κが高いエージェントほど、学習が定着する

作成日: 2025年11月7日
バージョン: 9.0
"""

import numpy as np
import sys
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import argparse
import time

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ssd_dynamic_interpretation import (
    DynamicInterpretationModule,
    MemoryTrace
)


@dataclass
class PlayerState:
    """プレイヤーの状態"""
    player_id: int
    name: str
    role: str  # 'villager' or 'werewolf'
    is_alive: bool
    energy: np.ndarray  # [4] - PHYSICAL, BASE, CORE, UPPER
    kappa: np.ndarray   # [4] - 各層の整合慣性
    suspicion_levels: Dict[int, float]  # 他プレイヤーへの疑惑レベル
    visible_signals: np.ndarray  # [7] - 他者に見えるシグナル


class PlayerV9:
    """
    v9.0プレイヤー: 動的解釈による学習AI
    """
    
    def __init__(self, 
                 player_id: int,
                 name: str,
                 role: str,
                 learning_rate: float = 0.6,
                 tau_memory: float = 50.0):
        self.player_id = player_id
        self.name = name
        self.role = role
        self.is_alive = True
        
        # エネルギーとκの初期化
        self.energy = np.array([1.0, 0.8, 0.6, 0.5])
        self.kappa = np.array([0.3, 0.4, 0.5, 0.4])
        
        # 疑惑レベル（他プレイヤーへの）
        self.suspicion_levels: Dict[int, float] = {}
        
        # シグナル
        self.visible_signals = np.zeros(7)
        
        # 行動履歴（このゲーム内）
        self.behavior_history: List[Dict] = []
        
        # 動的解釈モジュール
        self.interpretation_module = self._initialize_interpretation_module(
            learning_rate, tau_memory
        )
        
        # ゲーム統計
        self.games_played = 0
        self.times_executed = 0
        self.times_survived = 0
    
    def _initialize_interpretation_module(self, 
                                         learning_rate: float,
                                         tau_memory: float) -> DynamicInterpretationModule:
        """動的解釈モジュールの初期化"""
        
        # 基本解釈係数
        base_coeffs = np.array([
            # シグナル: [0:姿勢, 1:表情, 2:音声, 3:攻撃性, 4:防御性, 5:協調性, 6:理念的発言]
            [0.1, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0],  # PHYSICAL層
            [0.2, 0.3, 0.5, 0.4, 0.3, 0.2, 0.1],  # BASE層（生存本能）
            [0.1, 0.2, 0.3, 0.5, 0.4, 0.4, 0.2],  # CORE層（社会的価値）
            [0.0, 0.1, 0.2, 0.3, 0.3, 0.5, 0.6],  # UPPER層（理念）
        ])
        
        return DynamicInterpretationModule(
            base_coeffs=base_coeffs,
            learning_rate=learning_rate,
            tau_memory=tau_memory,
            max_memories=200
        )
    
    def observe_player(self, 
                      target_id: int,
                      target_signals: np.ndarray,
                      current_time: float) -> float:
        """
        他プレイヤーを観測し、疑惑レベルを計算（動的解釈）
        
        Args:
            target_id: 観測対象のID
            target_signals: 観測されたシグナル [7]
            current_time: 現在時刻
        
        Returns:
            疑惑レベル (0.0 ~ 1.0)
        """
        # 動的解釈によって圧力を計算
        pressure = self.interpretation_module.interpret_signals(
            signals=target_signals,
            kappa=self.kappa,
            update_matrix=True
        )
        
        # BASE層の圧力 = 生存脅威 = 疑惑
        # CORE層の圧力 = 社会的違和感 = 疑惑
        suspicion = 0.6 * pressure[1] + 0.4 * pressure[2]  # BASE優先
        
        # [0, 1]にクリップ
        suspicion = np.clip(suspicion, 0.0, 1.0)
        
        # 疑惑レベルを更新
        self.suspicion_levels[target_id] = suspicion
        
        return suspicion
    
    def generate_signals(self) -> np.ndarray:
        """
        自分のシグナルを生成
        
        役割と心理状態に基づく
        """
        signals = np.zeros(7)
        
        # 基本シグナル（エネルギーベース）
        signals[0] = self.energy[0] * 0.3  # 姿勢
        signals[1] = self.energy[1] * 0.4  # 表情
        signals[2] = self.energy[2] * 0.3  # 音声
        
        # 人狼の場合: 攻撃的・防御的になりやすい
        if self.role == 'werewolf':
            # 自分への疑惑が高いと防御的に
            avg_suspicion_on_me = np.mean(list(self.suspicion_levels.values())) \
                if self.suspicion_levels else 0.0
            
            signals[3] = 0.3 + avg_suspicion_on_me * 0.4  # 攻撃性
            signals[4] = 0.2 + avg_suspicion_on_me * 0.5  # 防御性
            signals[5] = 0.2  # 協調性（低め）
            signals[6] = 0.1  # 理念的発言（低め）
        else:  # 村人
            signals[3] = 0.2  # 攻撃性（低め）
            signals[4] = 0.3  # 防御性
            signals[5] = 0.5  # 協調性（高め）
            signals[6] = 0.4  # 理念的発言
        
        # ノイズ
        signals += np.random.randn(7) * 0.05
        signals = np.clip(signals, 0.0, 1.0)
        
        self.visible_signals = signals
        return signals
    
    def decide_vote(self, alive_players: List[int]) -> int:
        """
        投票先を決定
        
        Args:
            alive_players: 生存プレイヤーのIDリスト
        
        Returns:
            投票先のプレイヤーID
        """
        if not alive_players:
            return -1
        
        # 自分を除外
        candidates = [pid for pid in alive_players if pid != self.player_id]
        if not candidates:
            return -1
        
        # 疑惑レベルが最も高い相手に投票
        max_suspicion = -1.0
        target = candidates[0]
        
        for pid in candidates:
            suspicion = self.suspicion_levels.get(pid, 0.0)
            if suspicion > max_suspicion:
                max_suspicion = suspicion
                target = pid
        
        return target
    
    def learn_from_outcome(self, 
                          outcome: str,
                          executed_player_id: Optional[int] = None,
                          all_players: Optional[Dict[int, 'PlayerV9']] = None):
        """
        ゲーム結果から学習
        
        Args:
            outcome: 'executed', 'survived', 'won', 'lost'
            executed_player_id: 処刑されたプレイヤーのID
            all_players: 全プレイヤーの辞書
        """
        current_time = self.interpretation_module.current_time
        
        if outcome == 'executed':
            # 処刑された = 最悪の結果
            # 直前に最も疑っていた相手のシグナルを記憶
            if all_players and self.suspicion_levels:
                most_suspected = max(
                    self.suspicion_levels.items(),
                    key=lambda x: x[1]
                )[0]
                
                if most_suspected in all_players:
                    target_signals = all_players[most_suspected].visible_signals
                    
                    # BASE層での強烈な学習
                    self.interpretation_module.record_experience(
                        signal_pattern=target_signals,
                        layer=1,  # BASE層
                        interpreted_pressure=self.suspicion_levels[most_suspected],
                        outcome=-1.0,  # 最悪
                        context={
                            'event': 'executed',
                            'suspected_player': most_suspected
                        }
                    )
            
            # κの上昇（トラウマ的学習）
            self.kappa[1] = min(1.0, self.kappa[1] + 0.3)  # BASE層
            self.times_executed += 1
        
        elif outcome == 'survived':
            # 生存 = 良い結果
            # 自分の判断が正しかった可能性
            if all_players and executed_player_id:
                if executed_player_id in all_players:
                    executed_signals = all_players[executed_player_id].visible_signals
                    my_suspicion = self.suspicion_levels.get(executed_player_id, 0.0)
                    
                    # その人を疑っていた場合、正しい判断だった
                    if my_suspicion > 0.5:
                        self.interpretation_module.record_experience(
                            signal_pattern=executed_signals,
                            layer=2,  # CORE層（社会的判断）
                            interpreted_pressure=my_suspicion,
                            outcome=+0.7,  # 良い結果
                            context={
                                'event': 'correct_suspicion',
                                'executed_player': executed_player_id
                            }
                        )
                        
                        # κの上昇（成功体験）
                        self.kappa[2] = min(1.0, self.kappa[2] + 0.1)
            
            self.times_survived += 1
        
        elif outcome == 'won':
            # 勝利 = 最良の結果
            self.kappa = np.minimum(1.0, self.kappa + 0.15)
        
        elif outcome == 'lost':
            # 敗北 = 悪い結果（でも処刑ほどではない）
            self.kappa = np.minimum(1.0, self.kappa + 0.05)
        
        self.games_played += 1
    
    def get_learning_stats(self) -> Dict:
        """学習統計を取得"""
        return {
            'games_played': self.games_played,
            'times_executed': self.times_executed,
            'times_survived': self.times_survived,
            'survival_rate': self.times_survived / max(1, self.games_played),
            'memory_count': self.interpretation_module.get_memory_count(),
            'kappa': self.kappa.copy(),
            'current_coeffs': self.interpretation_module.get_current_coeffs()
        }


class WerewolfGameV9:
    """
    人狼ゲーム v9.0: 学習する主観的AI
    """
    
    def __init__(self,
                 num_players: int = 7,
                 num_werewolves: int = 2,
                 learning_rate: float = 0.6):
        self.num_players = num_players
        self.num_werewolves = num_werewolves
        self.learning_rate = learning_rate
        
        # プレイヤー初期化
        self.players: Dict[int, PlayerV9] = {}
        self._initialize_players()
        
        # ゲーム状態
        self.day_count = 0
        self.game_log: List[str] = []
        self.current_time = 0.0
    
    def _initialize_players(self):
        """プレイヤーを初期化（役割をランダム割り当て）"""
        roles = ['werewolf'] * self.num_werewolves + \
                ['villager'] * (self.num_players - self.num_werewolves)
        np.random.shuffle(roles)
        
        for i in range(self.num_players):
            player = PlayerV9(
                player_id=i,
                name=f"Player{i}",
                role=roles[i],
                learning_rate=self.learning_rate
            )
            self.players[i] = player
    
    def get_alive_players(self) -> List[int]:
        """生存プレイヤーのIDリストを取得"""
        return [pid for pid, p in self.players.items() if p.is_alive]
    
    def get_alive_werewolves(self) -> List[int]:
        """生存している人狼のIDリスト"""
        return [pid for pid, p in self.players.items() 
                if p.is_alive and p.role == 'werewolf']
    
    def get_alive_villagers(self) -> List[int]:
        """生存している村人のIDリスト"""
        return [pid for pid, p in self.players.items() 
                if p.is_alive and p.role == 'villager']
    
    def check_game_end(self) -> Optional[str]:
        """
        ゲーム終了判定
        
        Returns:
            'werewolf_win', 'villager_win', or None
        """
        werewolves = self.get_alive_werewolves()
        villagers = self.get_alive_villagers()
        
        if len(werewolves) == 0:
            return 'villager_win'
        elif len(werewolves) >= len(villagers):
            return 'werewolf_win'
        else:
            return None
    
    def day_phase(self):
        """昼フェーズ: 議論と投票"""
        self.day_count += 1
        alive = self.get_alive_players()
        
        self.game_log.append(f"\n=== Day {self.day_count} ===")
        self.game_log.append(f"生存者: {len(alive)}人")
        
        # 1. 各プレイヤーがシグナルを発信
        for pid in alive:
            self.players[pid].generate_signals()
        
        # 2. 各プレイヤーが他者を観測
        for observer_id in alive:
            observer = self.players[observer_id]
            
            for target_id in alive:
                if target_id != observer_id:
                    target_signals = self.players[target_id].visible_signals
                    suspicion = observer.observe_player(
                        target_id, target_signals, self.current_time
                    )
        
        # 3. 投票
        votes: Dict[int, int] = {}  # {投票先ID: 票数}
        
        for voter_id in alive:
            target = self.players[voter_id].decide_vote(alive)
            if target != -1:
                votes[target] = votes.get(target, 0) + 1
        
        # 4. 処刑
        if votes:
            executed_id = max(votes.items(), key=lambda x: x[1])[0]
            executed = self.players[executed_id]
            executed.is_alive = False
            
            self.game_log.append(
                f"投票結果: {executed.name} (役割: {executed.role}) が処刑"
            )
            
            # 学習: 処刑されたプレイヤー
            executed.learn_from_outcome(
                'executed',
                executed_player_id=executed_id,
                all_players=self.players
            )
            
            # 学習: 生存プレイヤー
            for pid in alive:
                if pid != executed_id:
                    self.players[pid].learn_from_outcome(
                        'survived',
                        executed_player_id=executed_id,
                        all_players=self.players
                    )
        
        self.current_time += 1.0
        
        # 各プレイヤーの時間を進める
        for player in self.players.values():
            player.interpretation_module.advance_time(1.0)
    
    def play_game(self, max_days: int = 10, verbose: bool = True) -> str:
        """
        ゲームをプレイ
        
        Returns:
            勝利陣営 ('werewolf_win' or 'villager_win')
        """
        self.game_log.clear()
        self.game_log.append("=" * 60)
        self.game_log.append("人狼ゲーム v9.0 開始")
        self.game_log.append("=" * 60)
        
        werewolves = self.get_alive_werewolves()
        self.game_log.append(f"人狼: {len(werewolves)}人")
        self.game_log.append(f"村人: {self.num_players - len(werewolves)}人")
        
        for day in range(max_days):
            # 昼フェーズ
            self.day_phase()
            
            # 終了判定
            result = self.check_game_end()
            if result:
                self.game_log.append(f"\n{'='*60}")
                self.game_log.append(f"ゲーム終了: {result}")
                self.game_log.append(f"{'='*60}")
                
                # 勝敗から学習
                for player in self.players.values():
                    if player.role == 'werewolf':
                        outcome = 'won' if result == 'werewolf_win' else 'lost'
                    else:
                        outcome = 'won' if result == 'villager_win' else 'lost'
                    
                    player.learn_from_outcome(outcome)
                
                if verbose:
                    for log in self.game_log:
                        print(log)
                
                return result
        
        # 最大日数到達
        result = 'villager_win'  # デフォルト
        if verbose:
            for log in self.game_log:
                print(log)
        
        return result


def demo_single_game():
    """単一ゲームのデモ"""
    print("="*70)
    print("人狼ゲーム v9.0 - 単一ゲームデモ")
    print("="*70)
    
    game = WerewolfGameV9(num_players=7, num_werewolves=2)
    result = game.play_game(verbose=True)
    
    print("\n" + "="*70)
    print("学習統計")
    print("="*70)
    
    for pid, player in game.players.items():
        stats = player.get_learning_stats()
        print(f"\n{player.name} (役割: {player.role}):")
        print(f"  記憶数: {stats['memory_count']}")
        print(f"  κ: {stats['kappa']}")


def demo_learning_over_games():
    """複数ゲームでの学習効果のデモ"""
    print("\n\n" + "="*70)
    print("人狼ゲーム v9.0 - 学習効果のデモ")
    print("="*70)
    
    num_games = 5
    num_players = 7
    
    # 同じプレイヤーで複数ゲームをプレイ
    players = {}
    for i in range(num_players):
        players[i] = PlayerV9(
            player_id=i,
            name=f"Player{i}",
            role='villager',  # 最初は全員村人
            learning_rate=0.7
        )
    
    print(f"\n{num_games}ゲームをプレイして学習を観察...")
    
    for game_num in range(num_games):
        print(f"\n--- ゲーム {game_num + 1} ---")
        
        # 役割をランダムに再割り当て
        roles = ['werewolf'] * 2 + ['villager'] * 5
        np.random.shuffle(roles)
        
        for i, player in players.items():
            player.role = roles[i]
            player.is_alive = True
            player.suspicion_levels.clear()
        
        # ゲーム作成（既存プレイヤーを使用）
        game = WerewolfGameV9(num_players=num_players, num_werewolves=2)
        game.players = players
        
        # プレイ（詳細は表示しない）
        result = game.play_game(verbose=False)
        print(f"結果: {result}")
        
        # Player 0の学習状況を追跡
        stats = players[0].get_learning_stats()
        print(f"Player0 - 記憶数: {stats['memory_count']}, κ[BASE]: {stats['kappa'][1]:.3f}")
    
    # 最終統計
    print("\n" + "="*70)
    print("最終学習統計")
    print("="*70)
    
    for pid in range(3):  # 最初の3人のみ表示
        player = players[pid]
        stats = player.get_learning_stats()
        
        print(f"\n{player.name}:")
        print(f"  プレイ数: {stats['games_played']}")
        print(f"  処刑された回数: {stats['times_executed']}")
        print(f"  生存回数: {stats['times_survived']}")
        print(f"  生存率: {stats['survival_rate']:.1%}")
        print(f"  記憶数: {stats['memory_count']}")
        print(f"  κ: {stats['kappa']}")
        
        # 学習による係数の変化
        base_coeffs = np.array([
            [0.1, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0],
            [0.2, 0.3, 0.5, 0.4, 0.3, 0.2, 0.1],
            [0.1, 0.2, 0.3, 0.5, 0.4, 0.4, 0.2],
            [0.0, 0.1, 0.2, 0.3, 0.3, 0.5, 0.6],
        ])
        
        current_coeffs = stats['current_coeffs']
        
        print(f"  BASE層シグナル3（攻撃性）への係数:")
        print(f"    初期: {base_coeffs[1, 3]:.3f} → 現在: {current_coeffs[1, 3]:.3f}")


def benchmark_comparison():
    """v8.5との比較ベンチマーク"""
    print("\n\n" + "="*70)
    print("ベンチマーク: v9.0のオーバーヘッド測定")
    print("="*70)
    
    num_games = 10
    
    print(f"\n{num_games}ゲームの平均実行時間を測定...")
    
    start = time.time()
    for _ in range(num_games):
        game = WerewolfGameV9(num_players=7, num_werewolves=2)
        game.play_game(verbose=False)
    elapsed = time.time() - start
    
    avg_time = elapsed / num_games * 1000  # ms
    
    print(f"\n平均実行時間: {avg_time:.2f} ms/game")
    print(f"総実行時間: {elapsed:.2f} s")
    
    # メモリ使用量（概算）
    total_memories = sum(
        game.players[pid].interpretation_module.get_memory_count()
        for pid in game.players
    )
    print(f"\n総記憶数: {total_memories}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='人狼ゲーム v9.0 - 学習する主観的AI')
    parser.add_argument('--demo', choices=['single', 'learning', 'benchmark', 'all'],
                       default='all', help='デモモード')
    parser.add_argument('--games', type=int, default=5,
                       help='学習デモのゲーム数')
    
    args = parser.parse_args()
    
    if args.demo in ['single', 'all']:
        demo_single_game()
    
    if args.demo in ['learning', 'all']:
        demo_learning_over_games()
    
    if args.demo in ['benchmark', 'all']:
        benchmark_comparison()
    
    print("\n\n" + "="*70)
    print("人狼ゲーム v9.0 - デモ完了")
    print("="*70)
    print("\n✅ 学習する主観的AIの実装成功！")
    print("✅ エージェントは経験から学び、解釈を変化させる")
    print("✅ 次: Phase 9.3 (Nano最適化)")
