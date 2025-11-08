"""
ブラックジャック with SSD (Refactored版)
SSDCoreEngine/HumanAgent統合版

元の実装: d:\\GitHub\\ssd_iroiro\\casino\\blackjack_ssd_ai.py
新アーキテクチャ: ssd_core_engine.py + ssd_human_module.py
"""

import sys
import os
import random
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

# 親ディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ssd_human_module import HumanAgent, HumanPressure

# ANSIカラーコード
class Colors:
    RESET = '\033[0m'
    TARO = '\033[96m'      # シアン（太郎）
    HANAKO = '\033[95m'    # マゼンタ（花子）
    SMITH = '\033[92m'     # 緑（スミス）
    DEALER = '\033[91m'    # 赤（ディーラー）


# ===== カード関連 =====
class Suit(Enum):
    """カードのスート"""
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


@dataclass
class Card:
    """カード1枚"""
    rank: int  # 1-13 (1=A, 11=J, 12=Q, 13=K)
    suit: Suit
    
    def get_value(self) -> int:
        """カードの値を返す（ブラックジャック用）"""
        if self.rank == 1:  # A
            return 11
        elif self.rank >= 10:  # 10, J, Q, K
            return 10
        else:
            return self.rank
    
    def __str__(self) -> str:
        rank_display = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
        rank_str = rank_display.get(self.rank, str(self.rank))
        return f"{rank_str}{self.suit.value}"


class Deck:
    """デッキ管理"""
    
    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self._initialize_deck()
    
    def _initialize_deck(self):
        """デッキ初期化"""
        self.cards = []
        for _ in range(self.num_decks):
            for suit in Suit:
                for rank in range(1, 14):
                    self.cards.append(Card(rank, suit))
        self.shuffle()
    
    def shuffle(self):
        """シャッフル"""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Card:
        """カードを1枚配る"""
        if len(self.cards) < 10:  # 残りが少なくなったら再シャッフル
            print("  [シャッフル]")
            self._initialize_deck()
        return self.cards.pop()
    
    def __len__(self) -> int:
        return len(self.cards)


# ===== ハンド関連 =====
@dataclass
class Hand:
    """プレイヤーまたはディーラーの手札"""
    cards: List[Card] = field(default_factory=list)
    bet: int = 0
    
    def add_card(self, card: Card):
        """カードを追加"""
        self.cards.append(card)
    
    def get_value(self) -> int:
        """手札の合計値を返す（エース調整込み）"""
        total = sum(card.get_value() for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 1)
        
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total
    
    def is_soft(self) -> bool:
        """ソフトハンドか（エースを11として使っている）"""
        total = sum(card.get_value() for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 1)
        return total <= 21 and aces > 0 and any(card.rank == 1 for card in self.cards)
    
    def is_blackjack(self) -> bool:
        """ブラックジャックか"""
        return len(self.cards) == 2 and self.get_value() == 21
    
    def is_bust(self) -> bool:
        """バーストか"""
        return self.get_value() > 21
    
    def __str__(self) -> str:
        cards_str = ' '.join(str(card) for card in self.cards)
        return f"{cards_str} ({self.get_value()})"


# ===== ディーラー =====
class Dealer:
    """ディーラー"""
    
    def __init__(self):
        self.hand = Hand()
    
    def should_hit(self) -> bool:
        """ヒットすべきか（17未満でヒット）"""
        return self.hand.get_value() < 17
    
    def get_upcard(self) -> Card:
        """アップカード（見えているカード）"""
        return self.hand.cards[0] if self.hand.cards else None
    
    def get_upcard_value(self) -> int:
        """アップカードの値"""
        upcard = self.get_upcard()
        return upcard.get_value() if upcard else 0
    
    def reset(self):
        """ハンドをリセット"""
        self.hand = Hand()


# ===== プレイヤー基底クラス =====
class PlayerBase:
    """プレイヤーの基底クラス"""
    
    def __init__(self, name: str, coins: int):
        self.name = name
        self.coins = coins
        self.hand = Hand()
        self.total_games = 0
        self.total_wins = 0
        self.total_losses = 0
        self.total_pushes = 0
        
        # プレイヤーごとの色
        self.color = self._get_player_color()
    
    def _get_player_color(self) -> str:
        """プレイヤー名に応じた色"""
        if '太郎' in self.name:
            return Colors.TARO
        elif '花子' in self.name:
            return Colors.HANAKO
        elif 'スミス' in self.name:
            return Colors.SMITH
        else:
            return Colors.RESET
    
    def place_bet(self) -> int:
        """ベット額を決定"""
        raise NotImplementedError
    
    def decide_action(self, dealer_upcard: Card, deck: Deck) -> str:
        """行動を決定（H=hit, S=stand）"""
        raise NotImplementedError
    
    def update_stats(self, result: str, payout: int):
        """統計更新"""
        self.total_games += 1
        if result == 'win' or result == 'blackjack':
            self.total_wins += 1
        elif result == 'loss':
            self.total_losses += 1
        elif result == 'push':
            self.total_pushes += 1
    
    def reset_hand(self):
        """ハンドをリセット"""
        self.hand = Hand()
    
    def get_win_rate(self) -> float:
        """勝率を計算"""
        if self.total_games == 0:
            return 0.0
        return self.total_wins / self.total_games * 100


# ===== SSD AIプレイヤー（Refactored版） =====
class SSDPlayerRefactored(PlayerBase):
    """SSD理論に基づくAIプレイヤー（HumanAgent使用）"""
    
    def __init__(self, name: str, personality: str, coins: int):
        super().__init__(name, coins)
        self.personality = personality
        
        # HumanAgent統合
        self.agent = HumanAgent()
        
        # 戦略スコア（κの代わり）
        self.strategy_scores = {
            'conservative': 0.5,  # 保守的
            'balanced': 0.5,      # バランス
            'aggressive': 0.3     # 攻撃的
        }
        
        # 性格パラメータ
        self.risk_tolerance = self._get_risk_tolerance()
        self.learning_speed = self._get_learning_speed()
        
        # 履歴
        self.last_strategy = None
        self.enable_dialogue = True
    
    def _get_risk_tolerance(self) -> float:
        """性格によるリスク許容度"""
        tolerance_map = {
            'cautious': 0.7,
            'balanced': 1.0,
            'aggressive': 1.3
        }
        return tolerance_map.get(self.personality, 1.0)
    
    def _get_learning_speed(self) -> float:
        """性格による学習速度"""
        speed_map = {
            'cautious': 0.8,
            'balanced': 1.0,
            'aggressive': 1.2
        }
        return speed_map.get(self.personality, 1.0)
    
    def place_bet(self) -> int:
        """SSDベースのベット額決定"""
        if self.coins < 10:
            return 10
        
        # E状態に応じたベット調整（Eが高い=探索的）
        E_mean = np.mean(self.agent.state.E)
        exploration_factor = 1.0 + E_mean * 0.5
        
        base_bet = 10
        max_bet = min(100, int(self.coins * 0.1))
        
        bet = int(base_bet * exploration_factor * self.risk_tolerance)
        bet = max(10, min(bet, max_bet))
        
        return bet
    
    def decide_action(self, dealer_upcard: Card, deck: Deck) -> str:
        """SSDベースの行動決定"""
        # 戦略選択（ソフトマックス）
        strategy_name = self._choose_strategy()
        self.last_strategy = strategy_name
        
        hand_value = self.hand.get_value()
        dealer_value = dealer_upcard.get_value()
        
        # 会話
        if self.enable_dialogue:
            self._speak_situation(hand_value, dealer_value, strategy_name)
        
        # 戦略に応じた閾値
        thresholds = {
            'conservative': 16,  # 16以下でヒット
            'balanced': 15,
            'aggressive': 17     # 17以下でヒット
        }
        threshold = thresholds.get(strategy_name, 15)
        
        # 行動決定
        if hand_value < threshold:
            action = 'H'
        elif hand_value >= 17:
            action = 'S'
        else:
            # 微妙な時はランダム（E状態で変動）
            E_mean = np.mean(self.agent.state.E)
            hit_prob = 0.5 + E_mean * 0.2
            action = 'H' if random.random() < hit_prob else 'S'
        
        if self.enable_dialogue:
            self._speak_action(action, hand_value)
        
        return action
    
    def _choose_strategy(self) -> str:
        """戦略選択（ソフトマックス）"""
        strategies = list(self.strategy_scores.keys())
        scores = np.array([self.strategy_scores[s] for s in strategies])
        
        # E状態で温度調整
        E_mean = np.mean(self.agent.state.E)
        T = 0.3 + E_mean * 0.5  # 温度
        
        if T > 0:
            exp_scores = np.exp(scores / T)
            probabilities = exp_scores / exp_scores.sum()
        else:
            probabilities = np.zeros(len(strategies))
            probabilities[np.argmax(scores)] = 1.0
        
        return np.random.choice(strategies, p=probabilities)
    
    def update_ssd(self, result: str, payout: int, bet: int):
        """SSD状態を更新"""
        if not self.last_strategy:
            return
        
        # 報酬計算
        profit = payout - bet
        reward = profit / bet if bet > 0 else 0
        
        # 意味圧として解釈
        if reward > 0:
            # 勝利: BASE圧力低下（安心）
            pressure = HumanPressure(base=-0.3, core=0.1, upper=0.0)
        elif reward < 0:
            # 敗北: BASE圧力上昇（脅威）
            pressure = HumanPressure(base=0.5, core=0.2, upper=0.1)
        else:
            # 引き分け: ニュートラル
            pressure = HumanPressure()
        
        # HumanAgentにステップ
        self.agent.step(pressure, dt=1.0)
        
        # 戦略スコア更新
        learning_rate = 0.1 * self.learning_speed
        if reward > 0:
            self.strategy_scores[self.last_strategy] += learning_rate * reward
        else:
            self.strategy_scores[self.last_strategy] -= learning_rate * abs(reward)
        
        # スコアの制約
        for strategy in self.strategy_scores:
            self.strategy_scores[strategy] = max(0.1, self.strategy_scores[strategy])
    
    def _speak_situation(self, hand_value: int, dealer_value: int, strategy: str):
        """状況に応じた独り言"""
        comments = {
            'cautious': [
                f"「{hand_value}か...ディーラーは{dealer_value}...慎重に...」",
                f"「うーん、{hand_value}...どうしよう」"
            ],
            'balanced': [
                f"「{hand_value} vs {dealer_value}...」",
                f"「{hand_value}だな」"
            ],
            'aggressive': [
                f"「{hand_value}！ディーラー{dealer_value}！攻めるぞ！」",
                f"「{hand_value}か、勝負だ！」"
            ]
        }
        
        personality_comments = comments.get(self.personality, comments['balanced'])
        if random.random() < 0.7:
            print(f"{self.color}{random.choice(personality_comments)}{Colors.RESET}")
    
    def _speak_action(self, action: str, hand_value: int):
        """行動決定時の独り言"""
        action_names = {'H': 'ヒット', 'S': 'スタンド'}
        action_name = action_names.get(action, action)
        
        comments = {
            'cautious': {
                'H': f"「慎重に1枚もらう...」",
                'S': f"「{hand_value}でストップ」"
            },
            'balanced': {
                'H': f"「もう1枚」",
                'S': f"「{hand_value}で止める」"
            },
            'aggressive': {
                'H': f"「もっといける！」",
                'S': f"「{hand_value}で勝負！」"
            }
        }
        
        personality_comments = comments.get(self.personality, comments['balanced'])
        comment = personality_comments.get(action, f"「{action_name}」")
        
        if random.random() < 0.7:
            print(f"{self.color}{comment}{Colors.RESET}")
    
    def update_stats(self, result: str, payout: int):
        """統計更新（親クラス + SSD更新）"""
        super().update_stats(result, payout)
        
        # SSD更新
        if self.hand.bet > 0:
            self.update_ssd(result, payout, self.hand.bet)


# ===== ランダムプレイヤー =====
class RandomPlayer(PlayerBase):
    """完全ランダムなプレイヤー"""
    
    def place_bet(self) -> int:
        """ランダムベット"""
        max_bet = min(100, self.coins)
        if max_bet < 10:
            return 10
        return random.randint(10, max_bet)
    
    def decide_action(self, dealer_upcard: Card, deck: Deck) -> str:
        """ランダム行動"""
        return random.choice(['H', 'S'])


# ===== テーブル（ゲーム進行管理） =====
class BlackjackTable:
    """ブラックジャックテーブル"""
    
    def __init__(self, players: List[PlayerBase]):
        self.players = players
        self.dealer = Dealer()
        self.deck = Deck(num_decks=6)
    
    def play_round(self, verbose: bool = True):
        """1ラウンドプレイ"""
        if verbose:
            print(f"\n{'='*60}")
            print("新しいラウンド")
            print(f"{'='*60}")
        
        # プレイヤーリセット
        for player in self.players:
            player.reset_hand()
        self.dealer.reset()
        
        # ベット
        active_players = []
        for player in self.players:
            if player.coins >= 10:
                bet = player.place_bet()
                player.hand.bet = bet
                player.coins -= bet
                active_players.append(player)
                if verbose:
                    print(f"{player.color}{player.name}: ベット ${bet}{Colors.RESET}")
        
        if not active_players:
            if verbose:
                print("全員の資金が不足しています")
            return
        
        # カード配布
        for _ in range(2):
            for player in active_players:
                player.hand.add_card(self.deck.deal_card())
            self.dealer.hand.add_card(self.deck.deal_card())
        
        # 初期状態表示
        if verbose:
            for player in active_players:
                print(f"{player.color}{player.name}: {player.hand}{Colors.RESET}")
            upcard = self.dealer.get_upcard()
            print(f"{Colors.DEALER}ディーラー: {upcard} ?{Colors.RESET}")
        
        # ブラックジャックチェック
        dealer_blackjack = self.dealer.hand.is_blackjack()
        
        # プレイヤーターン
        for player in active_players:
            if player.hand.is_blackjack():
                if verbose:
                    print(f"{player.color}{player.name}: ブラックジャック！{Colors.RESET}")
                continue
            
            if dealer_blackjack:
                continue
            
            self._player_turn(player, verbose)
        
        # ディーラーターン
        if not dealer_blackjack and any(not p.hand.is_bust() for p in active_players):
            self._dealer_turn(verbose)
        
        # 精算
        self._settle(active_players, verbose)
    
    def _player_turn(self, player: PlayerBase, verbose: bool):
        """プレイヤーのターン"""
        if verbose:
            print(f"\n{player.color}--- {player.name}のターン ---{Colors.RESET}")
        
        while not player.hand.is_bust():
            action = player.decide_action(self.dealer.get_upcard(), self.deck)
            
            if action == 'H':
                card = self.deck.deal_card()
                player.hand.add_card(card)
                if verbose:
                    print(f"{player.color}{player.name}: ヒット → {card} | {player.hand}{Colors.RESET}")
                
                if player.hand.is_bust():
                    if verbose:
                        print(f"{player.color}{player.name}: バースト！{Colors.RESET}")
                    break
            elif action == 'S':
                if verbose:
                    print(f"{player.color}{player.name}: スタンド{Colors.RESET}")
                break
    
    def _dealer_turn(self, verbose: bool):
        """ディーラーのターン"""
        if verbose:
            print(f"\n{Colors.DEALER}--- ディーラーのターン ---{Colors.RESET}")
            print(f"{Colors.DEALER}ディーラー: {self.dealer.hand}{Colors.RESET}")
        
        while self.dealer.should_hit():
            card = self.deck.deal_card()
            self.dealer.hand.add_card(card)
            if verbose:
                print(f"{Colors.DEALER}ディーラー: ヒット → {card} | {self.dealer.hand}{Colors.RESET}")
        
        if self.dealer.hand.is_bust():
            if verbose:
                print(f"{Colors.DEALER}ディーラー: バースト！{Colors.RESET}")
        else:
            if verbose:
                print(f"{Colors.DEALER}ディーラー: スタンド{Colors.RESET}")
    
    def _settle(self, players: List[PlayerBase], verbose: bool):
        """精算"""
        if verbose:
            print(f"\n{'='*60}")
            print("結果")
            print(f"{'='*60}")
        
        dealer_value = self.dealer.hand.get_value()
        dealer_blackjack = self.dealer.hand.is_blackjack()
        dealer_bust = self.dealer.hand.is_bust()
        
        for player in players:
            bet = player.hand.bet
            player_value = player.hand.get_value()
            player_blackjack = player.hand.is_blackjack()
            player_bust = player.hand.is_bust()
            
            # 結果判定
            if player_bust:
                result = 'loss'
                payout = 0
            elif player_blackjack and not dealer_blackjack:
                result = 'blackjack'
                payout = int(bet * 2.5)  # 3:2
            elif dealer_bust:
                result = 'win'
                payout = bet * 2
            elif player_value > dealer_value:
                result = 'win'
                payout = bet * 2
            elif player_value == dealer_value:
                result = 'push'
                payout = bet
            else:
                result = 'loss'
                payout = 0
            
            # コイン更新
            player.coins += payout
            profit = payout - bet
            
            # 統計更新
            player.update_stats(result, payout)
            
            # 結果表示
            if verbose:
                result_symbols = {
                    'blackjack': '🎉 ブラックジャック！',
                    'win': '✅ 勝利',
                    'push': '🤝 引き分け',
                    'loss': '❌ 敗北'
                }
                symbol = result_symbols.get(result, result)
                print(f"{player.color}{player.name}: {symbol} (${profit:+d}) | 残高: ${player.coins}{Colors.RESET}")


# ===== メイン処理 =====
def main():
    """メイン処理"""
    print("="*60)
    print("ブラックジャック with SSD AI (Refactored版)")
    print("="*60)
    
    # プレイヤー作成
    initial_coins = 1000
    players = [
        SSDPlayerRefactored("太郎", "cautious", initial_coins),
        SSDPlayerRefactored("花子", "aggressive", initial_coins),
        SSDPlayerRefactored("スミス", "balanced", initial_coins),
        RandomPlayer("ランダム君", initial_coins),
    ]
    
    # テーブル作成
    table = BlackjackTable(players)
    
    # ラウンド実行
    num_rounds = 10
    for round_num in range(1, num_rounds + 1):
        print(f"\n{'#'*60}")
        print(f"ラウンド {round_num}/{num_rounds}")
        print(f"{'#'*60}")
        table.play_round(verbose=True)
        
        # 破産チェック
        active = [p for p in players if p.coins >= 10]
        if len(active) == 0:
            print("\n全員破産しました！")
            break
    
    # 最終結果
    print(f"\n{'='*60}")
    print("最終結果")
    print(f"{'='*60}")
    
    players_sorted = sorted(players, key=lambda p: p.coins, reverse=True)
    for rank, player in enumerate(players_sorted, 1):
        win_rate = player.get_win_rate()
        print(f"{rank}位: {player.color}{player.name}{Colors.RESET} - "
              f"${player.coins} | "
              f"勝率 {win_rate:.1f}% ({player.total_wins}勝 {player.total_losses}敗 {player.total_pushes}分)")
        
        # SSDプレイヤーの場合はE状態も表示
        if isinstance(player, SSDPlayerRefactored):
            E_mean = np.mean(player.agent.state.E)
            print(f"  └ SSD状態: E平均={E_mean:.3f}, 戦略スコア={player.strategy_scores}")


if __name__ == "__main__":
    main()
