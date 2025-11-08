"""
人狼ゲーム v8.5 - Hybrid Engine Edition
========================================

SSD Theory v8.0 の完全実装を使った人狼ゲームシミュレーション

特徴:
- リファレンス実装 (ssd_subjective_society) と Nano実装 (nano_core_engine) の両方に対応
- エンジン切り替え可能（`--engine reference` or `--engine nano`）
- 理論検証モード（詳細ログ） vs プロダクションモード（高速実行）

役割:
- 村人（Villager）: 人狼を見つけ出す
- 人狼（Werewolf）: 村人のふりをして生き残る
- 占い師（Seer）: 夜に1人の正体を知る

心理ダイナミクス（v8理論）:
- 疑惑（Suspicion）: 他者の行動を観測→主観的解釈→疑惑の蓄積
- 恐怖（Fear）: 人狼の存在による BASE層への圧力
- 信頼（Trust）: 協力関係の構築 (CORE/UPPER層)
- 葛藤（Conflict）: 疑惑 vs 信頼の内的闘争
"""

import sys
import argparse
import time
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np


# ========================================
# 役割定義
# ========================================

class Role(Enum):
    """プレイヤーの役割"""
    VILLAGER = "villager"
    WEREWOLF = "werewolf"
    SEER = "seer"


class GamePhase(Enum):
    """ゲームフェーズ"""
    DAY_DISCUSSION = "day_discussion"
    DAY_VOTING = "day_voting"
    NIGHT_WEREWOLF = "night_werewolf"
    NIGHT_SEER = "night_seer"
    GAME_OVER = "game_over"


# ========================================
# 抽象エンジンインターフェース
# ========================================

class AbstractEngineAdapter:
    """エンジンの抽象インターフェース
    
    リファレンス実装とNano実装を統一的に扱う
    """
    
    def initialize_player(self, player_id: str) -> any:
        """プレイヤーの状態を初期化"""
        raise NotImplementedError
    
    def get_energy(self, player_state: any, layer: int) -> float:
        """指定層のエネルギーを取得"""
        raise NotImplementedError
    
    def get_kappa(self, player_state: any, layer: int) -> float:
        """指定層のκを取得"""
        raise NotImplementedError
    
    def apply_pressure(self, player_state: any, pressure: np.ndarray, dt: float):
        """圧力を適用（インプレース更新）"""
        raise NotImplementedError
    
    def step_society(
        self,
        player_states: List[any],
        external_pressures: List[np.ndarray],
        relationships: np.ndarray,
        dt: float
    ):
        """社会全体を1ステップ進める"""
        raise NotImplementedError
    
    def get_observable_signals(self, player_state: any) -> Dict[str, float]:
        """観測可能なシグナルを取得"""
        raise NotImplementedError


# ========================================
# リファレンス実装アダプター
# ========================================

class ReferenceEngineAdapter(AbstractEngineAdapter):
    """ssd_subjective_society のアダプター"""
    
    def __init__(self):
        sys.path.insert(0, '..')
        from ssd_human_module import HumanAgent, HumanPressure, HumanLayer
        from ssd_subjective_society import SubjectiveSociety, SignalGenerator
        
        self.HumanAgent = HumanAgent
        self.HumanPressure = HumanPressure
        self.HumanLayer = HumanLayer
        self.SubjectiveSociety = SubjectiveSociety
        self.SignalGenerator = SignalGenerator
        
        self.signal_generator = SignalGenerator()
        self.society = None
    
    def initialize_player(self, player_id: str):
        return self.HumanAgent(agent_id=player_id)
    
    def get_energy(self, player_state, layer: int) -> float:
        return player_state.state.E[layer]
    
    def get_kappa(self, player_state, layer: int) -> float:
        return player_state.state.kappa[layer]
    
    def apply_pressure(self, player_state, pressure: np.ndarray, dt: float):
        p = self.HumanPressure(
            physical=pressure[0],
            base=pressure[1],
            core=pressure[2],
            upper=pressure[3]
        )
        player_state.step(p, dt)
    
    def step_society(
        self,
        player_states: List,
        external_pressures: List[np.ndarray],
        relationships: np.ndarray,
        dt: float
    ):
        # SubjectiveSociety を初期化（初回のみ）
        if self.society is None:
            self.society = self.SubjectiveSociety(
                agents=player_states,
                initial_relationships=relationships
            )
        else:
            # 関係性を更新
            self.society.relationships.matrix = relationships
        
        # 外部圧力を各エージェントに適用してからステップ
        for i, agent in enumerate(player_states):
            if np.any(external_pressures[i] > 0):
                self.apply_pressure(agent, external_pressures[i], dt)
        
        # 社会的ステップ
        self.society.step(dt)
    
    def get_observable_signals(self, player_state) -> Dict[str, float]:
        signals = self.signal_generator.generate_signals(player_state)
        return {sig_type.value: intensity for sig_type, intensity in signals.items()}


# ========================================
# Nano実装アダプター
# ========================================

class NanoEngineAdapter(AbstractEngineAdapter):
    """nano_core_engine のアダプター"""
    
    def __init__(self):
        sys.path.insert(0, '..')
        from nano_core_engine import NanoCoreEngine, NanoState, NanoParams, Layer
        
        self.NanoCoreEngine = NanoCoreEngine
        self.NanoState = NanoState
        self.NanoParams = NanoParams
        self.Layer = Layer
        
        self.engine = NanoCoreEngine(NanoParams())
    
    def initialize_player(self, player_id: str):
        return self.NanoState()
    
    def get_energy(self, player_state, layer: int) -> float:
        return player_state.E[layer]
    
    def get_kappa(self, player_state, layer: int) -> float:
        return player_state.kappa[layer]
    
    def apply_pressure(self, player_state, pressure: np.ndarray, dt: float):
        self.engine.step_single(player_state, pressure, dt)
    
    def step_society(
        self,
        player_states: List,
        external_pressures: List[np.ndarray],
        relationships: np.ndarray,
        dt: float
    ):
        # 距離は全員近接として扱う
        distances = np.zeros((len(player_states), len(player_states)))
        
        self.engine.step_batch(
            player_states,
            external_pressures,
            relationships,
            distances,
            dt
        )
    
    def get_observable_signals(self, player_state) -> Dict[str, float]:
        signal_names = ["fear_expression", "anger_expression", "cooperative_act",
                       "aggressive_act", "verbal_ideology", "norm_violation", "norm_adherence"]
        return {name: player_state.visible_signals[i] 
                for i, name in enumerate(signal_names)}


# ========================================
# プレイヤークラス
# ========================================

class Player:
    """人狼ゲームのプレイヤー"""
    
    def __init__(self, player_id: str, role: Role, engine_adapter: AbstractEngineAdapter):
        self.player_id = player_id
        self.role = role
        self.is_alive = True
        self.engine = engine_adapter
        
        # エンジン状態
        self.state = engine_adapter.initialize_player(player_id)
        
        # ゲーム状態
        self.suspicion_levels = {}  # {player_id: suspicion_level}
        self.votes_received = 0
        self.last_statement = ""
    
    def get_psychological_state(self) -> Dict[str, float]:
        """心理状態を取得"""
        return {
            "E_base": self.engine.get_energy(self.state, 1),
            "E_core": self.engine.get_energy(self.state, 2),
            "E_upper": self.engine.get_energy(self.state, 3),
            "kappa_core": self.engine.get_kappa(self.state, 2)
        }
    
    def get_observable_behavior(self) -> Dict[str, float]:
        """観測可能な行動"""
        return self.engine.get_observable_signals(self.state)
    
    def calculate_suspicion(self, target_player: 'Player') -> float:
        """対象プレイヤーへの疑惑を計算
        
        観測可能な行動パターンから疑惑を推論
        """
        behavior = target_player.get_observable_behavior()
        
        # 疑わしい行動パターン
        suspicion = 0.0
        
        # 恐怖が強い → 人狼を知っている？
        suspicion += behavior.get("fear_expression", 0) * 0.3
        
        # 攻撃的 → 人狼の可能性
        suspicion += behavior.get("aggressive_act", 0) * 0.5
        
        # 協力的でない → 疑わしい
        suspicion -= behavior.get("cooperative_act", 0) * 0.2
        
        # 規範違反 → 疑わしい
        suspicion += behavior.get("norm_violation", 0) * 0.4
        
        return np.clip(suspicion, 0.0, 1.0)
    
    def decide_vote(self, alive_players: List['Player']) -> Optional['Player']:
        """投票先を決定"""
        if not self.is_alive:
            return None
        
        # 自分以外の生存者
        candidates = [p for p in alive_players if p.player_id != self.player_id and p.is_alive]
        
        if not candidates:
            return None
        
        # 疑惑レベルを更新
        for candidate in candidates:
            self.suspicion_levels[candidate.player_id] = self.calculate_suspicion(candidate)
        
        # 最も疑わしいプレイヤーに投票
        most_suspicious = max(candidates, key=lambda p: self.suspicion_levels.get(p.player_id, 0))
        
        return most_suspicious


# ========================================
# ゲームマスター
# ========================================

class WerewolfGame:
    """人狼ゲームマスター"""
    
    def __init__(
        self,
        num_players: int = 7,
        num_werewolves: int = 2,
        engine_type: str = "nano",
        verbose: bool = True
    ):
        self.num_players = num_players
        self.num_werewolves = num_werewolves
        self.verbose = verbose
        self.phase = GamePhase.DAY_DISCUSSION
        self.day_count = 1
        
        # エンジンアダプター選択
        if engine_type == "reference":
            print("[Engine] リファレンス実装 (ssd_subjective_society)")
            self.engine = ReferenceEngineAdapter()
        else:
            print("[Engine] Nano実装 (nano_core_engine)")
            self.engine = NanoEngineAdapter()
        
        # プレイヤー初期化
        self.players: List[Player] = []
        self._initialize_players()
        
        # 関係性マトリクス（初期は中立）
        self.relationships = np.zeros((num_players, num_players))
    
    def _initialize_players(self):
        """プレイヤーを初期化"""
        # 役割を割り当て
        roles = [Role.WEREWOLF] * self.num_werewolves
        roles += [Role.SEER]
        roles += [Role.VILLAGER] * (self.num_players - self.num_werewolves - 1)
        np.random.shuffle(roles)
        
        # プレイヤー作成
        for i, role in enumerate(roles):
            player = Player(f"Player_{i}", role, self.engine)
            self.players.append(player)
            
            if self.verbose:
                print(f"  {player.player_id}: {role.value}")
    
    def get_alive_players(self) -> List[Player]:
        """生存プレイヤーのリスト"""
        return [p for p in self.players if p.is_alive]
    
    def check_game_over(self) -> Tuple[bool, str]:
        """ゲーム終了判定"""
        alive = self.get_alive_players()
        werewolves_alive = sum(1 for p in alive if p.role == Role.WEREWOLF)
        villagers_alive = len(alive) - werewolves_alive
        
        if werewolves_alive == 0:
            return True, "村人陣営の勝利！"
        elif werewolves_alive >= villagers_alive:
            return True, "人狼陣営の勝利！"
        else:
            return False, ""
    
    def day_discussion(self):
        """昼フェーズ: 議論"""
        print(f"\n{'='*60}")
        print(f"  Day {self.day_count} - 議論フェーズ")
        print(f"{'='*60}")
        
        alive = self.get_alive_players()
        
        # 各プレイヤーの心理状態を観測
        if self.verbose:
            print("\n[観測可能な行動]")
            for player in alive:
                behavior = player.get_observable_behavior()
                significant = {k: v for k, v in behavior.items() if v > 0.1}
                if significant:
                    print(f"  {player.player_id}: {significant}")
        
        # 疑惑の蓄積（心理的圧力として計算）
        external_pressures = []
        for i, observer in enumerate(alive):
            # 人狼の存在による恐怖（BASE層）
            fear_pressure = 5.0 if observer.role != Role.WEREWOLF else 0.0
            
            # 疑惑による葛藤（CORE層）
            total_suspicion = sum(observer.suspicion_levels.values())
            conflict_pressure = total_suspicion * 2.0
            
            pressure = np.array([0.0, fear_pressure, conflict_pressure, 0.0])
            external_pressures.append(pressure)
        
        # 関係性を更新（疑惑 → 関係性の悪化）
        for i, player_i in enumerate(alive):
            for j, player_j in enumerate(alive):
                if i != j:
                    suspicion = player_i.suspicion_levels.get(player_j.player_id, 0)
                    self.relationships[i, j] = 0.5 - suspicion  # 疑惑が高いと関係悪化
        
        # 社会的ダイナミクス実行
        alive_states = [p.state for p in alive]
        self.engine.step_society(alive_states, external_pressures, self.relationships, dt=0.1)
    
    def day_voting(self):
        """昼フェーズ: 投票"""
        print(f"\n{'='*60}")
        print(f"  Day {self.day_count} - 投票フェーズ")
        print(f"{'='*60}")
        
        alive = self.get_alive_players()
        
        # 投票集計
        votes = {}
        for voter in alive:
            target = voter.decide_vote(alive)
            if target:
                votes[voter.player_id] = target.player_id
                target.votes_received += 1
                
                if self.verbose:
                    suspicion = voter.suspicion_levels.get(target.player_id, 0)
                    print(f"  {voter.player_id} → {target.player_id} (疑惑: {suspicion:.2f})")
        
        # 最多得票者を処刑
        if alive:
            executed = max(alive, key=lambda p: p.votes_received)
            executed.is_alive = False
            
            print(f"\n[処刑] {executed.player_id} (役割: {executed.role.value})")
            
            # 全員の得票数をリセット
            for player in self.players:
                player.votes_received = 0
    
    def night_werewolf(self):
        """夜フェーズ: 人狼の襲撃"""
        print(f"\n{'='*60}")
        print(f"  Night {self.day_count} - 人狼フェーズ")
        print(f"{'='*60}")
        
        werewolves = [p for p in self.get_alive_players() if p.role == Role.WEREWOLF]
        villagers = [p for p in self.get_alive_players() if p.role != Role.WEREWOLF]
        
        if werewolves and villagers:
            # 最も疑っていない村人を襲撃（ランダム）
            target = np.random.choice(villagers)
            target.is_alive = False
            
            print(f"[襲撃] {target.player_id} (役割: {target.role.value})")
    
    def night_seer(self):
        """夜フェーズ: 占い師の占い"""
        seers = [p for p in self.get_alive_players() if p.role == Role.SEER]
        
        if seers and self.verbose:
            seer = seers[0]
            alive = self.get_alive_players()
            candidates = [p for p in alive if p.player_id != seer.player_id]
            
            if candidates:
                target = np.random.choice(candidates)
                print(f"[占い] {seer.player_id} → {target.player_id}: {target.role.value}")
                
                # 占い結果に基づいて疑惑を更新
                if target.role == Role.WEREWOLF:
                    seer.suspicion_levels[target.player_id] = 1.0
                else:
                    seer.suspicion_levels[target.player_id] = 0.0
    
    def run(self, max_days: int = 10):
        """ゲーム実行"""
        print(f"\n{'='*60}")
        print(f"  人狼ゲーム v8.5 開始")
        print(f"  プレイヤー: {self.num_players}人")
        print(f"  人狼: {self.num_werewolves}人")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        while self.day_count <= max_days:
            # 昼フェーズ
            self.day_discussion()
            self.day_voting()
            
            # ゲーム終了判定
            game_over, result = self.check_game_over()
            if game_over:
                print(f"\n{'='*60}")
                print(f"  {result}")
                print(f"{'='*60}")
                break
            
            # 夜フェーズ
            self.night_werewolf()
            self.night_seer()
            
            # ゲーム終了判定
            game_over, result = self.check_game_over()
            if game_over:
                print(f"\n{'='*60}")
                print(f"  {result}")
                print(f"{'='*60}")
                break
            
            self.day_count += 1
        
        elapsed = time.time() - start_time
        print(f"\n実行時間: {elapsed:.3f}秒")
        print(f"Day数: {self.day_count}")


# ========================================
# メイン
# ========================================

def main():
    parser = argparse.ArgumentParser(description="人狼ゲーム v8.5 - Hybrid Engine Edition")
    parser.add_argument(
        "--engine",
        choices=["reference", "nano"],
        default="nano",
        help="使用するエンジン (reference: 理論検証用, nano: 高速実行用)"
    )
    parser.add_argument(
        "--players",
        type=int,
        default=7,
        help="プレイヤー数"
    )
    parser.add_argument(
        "--werewolves",
        type=int,
        default=2,
        help="人狼の数"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細ログを表示"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="両エンジンのベンチマーク比較"
    )
    
    args = parser.parse_args()
    
    if args.benchmark:
        print("="*60)
        print("  ベンチマーク: リファレンス vs Nano")
        print("="*60)
        
        for engine_type in ["reference", "nano"]:
            print(f"\n[{engine_type.upper()}]")
            game = WerewolfGame(
                num_players=args.players,
                num_werewolves=args.werewolves,
                engine_type=engine_type,
                verbose=False
            )
            game.run()
    else:
        game = WerewolfGame(
            num_players=args.players,
            num_werewolves=args.werewolves,
            engine_type=args.engine,
            verbose=args.verbose
        )
        game.run()


if __name__ == "__main__":
    main()
