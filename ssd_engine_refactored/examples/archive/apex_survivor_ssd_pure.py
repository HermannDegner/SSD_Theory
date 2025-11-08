"""
APEX SURVIVOR with SSD Pure Theoretical版

【頂点に立つ者だけが生き残る - SSD理論による究極の意思決定】

ゲーム概要:
- 5ラウンド × 5セット = 25ラウンドのデスゲーム
- 各ラウンドで1-10の数字を選択
- 高い数字 = 高リターン + 高クラッシュ率
- クラッシュでHP-1、HP=0で脱落
- **最終順位1位のプレイヤーのみ生存**

SSD Pure Theoretical版の特徴:
1. HumanAgent + HumanPressureを使用（ssd_human_module.py）
2. κ（整合慣性）のみで学習、strategy辞書廃止
3. E（未処理圧）を層別参照（BASE/CORE/UPPER）
4. 時間経過でE自然減衰
5. 性格別の解釈フィルター（同じκでも異なる行動）

意味圧の種類:
- BASE層: 生存圧力（HP欠損、クラッシュリスク）
- CORE層: 順位圧力（1位以外全員死亡のプレッシャー）
- UPPER層: 探索圧力（未知の戦略への挑戦）

理論的証明:
- 学習すべきパターンあり（安全圏探索、リスクテイキングのタイミング）
- κ構造が収束 → 各プレイヤーが独自の戦略を確立
- ただし「1位以外死ぬ」という極限状況でSSD理論がどう機能するか？
"""

import sys
import os
import random
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# 親ディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ssd_human_module import HumanAgent, HumanPressure, HumanLayer


# ===== カラー定義 =====
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


# ===== ゲーム設定 =====
@dataclass
class GameConfig:
    """ゲーム設定"""
    # 選択値: スコア, クラッシュ率
    CHOICES = {
        1: {'score': 10, 'crash_rate': 0.02},
        2: {'score': 20, 'crash_rate': 0.04},
        3: {'score': 30, 'crash_rate': 0.08},
        4: {'score': 40, 'crash_rate': 0.12},
        5: {'score': 50, 'crash_rate': 0.16},
        6: {'score': 60, 'crash_rate': 0.25},
        7: {'score': 70, 'crash_rate': 0.35},
        8: {'score': 80, 'crash_rate': 0.45},
        9: {'score': 90, 'crash_rate': 0.55},
        10: {'score': 100, 'crash_rate': 0.65}
    }
    
    STARTING_HP = 3
    MAX_HP = 5
    HP_PURCHASE_COST = 20
    
    ROUNDS_PER_SET = 5
    TOTAL_SETS = 5


# ===== プレイヤークラス（Pure Theoretical版） =====
class ApexPlayerPure:
    """APEX SURVIVOR プレイヤー（Pure Theoretical版）
    
    理論的整合性:
    - κのみで学習（strategy辞書廃止）
    - E層別参照（BASE=生存、CORE=順位、UPPER=探索）
    - κを行動決定に使用（重み付け平均で選択値決定）
    - 性格別の解釈フィルター
    """
    
    def __init__(self, name: str, personality: str, color: str):
        self.name = name
        self.personality = personality
        self.color = color
        
        # ゲーム状態
        self.hp = GameConfig.STARTING_HP
        self.score = 0
        self.total_score = 0
        self.is_alive = True
        self.choice_history = []
        self.crash_history = []
        
        # HumanAgent統合（これが唯一の学習システム）
        self.agent = HumanAgent()
        self._initialize_personality()
    
    def _initialize_personality(self):
        """性格に応じたκの初期値設定
        
        BASE: 生存本能（リスク回避）
        CORE: 順位意識（勝利欲求）
        UPPER: 探索欲求（未知への挑戦）
        """
        if self.personality == 'cautious':
            # 慎重: 生存重視
            self.agent.state.kappa[HumanLayer.BASE.value] = 0.7  # 高い生存本能
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.4
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.2
        elif self.personality == 'aggressive':
            # 攻撃的: 順位重視
            self.agent.state.kappa[HumanLayer.BASE.value] = 0.3
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.8  # 高い勝利欲求
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.5
        else:  # balanced
            # バランス: 探索重視
            self.agent.state.kappa[HumanLayer.BASE.value] = 0.5
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.5
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.7  # 高い探索欲求
    
    def on_round_start(self):
        """ラウンド開始時の処理（E自然減衰）"""
        if not self.is_alive:
            return
        # ゼロ圧力でstep()を呼ぶことで、βによるE減衰を発動
        self.agent.step(HumanPressure(), dt=1.0)
    
    def make_choice(self, current_rank: int, leader_score: int, round_num: int, total_rounds: int) -> int:
        """選択を行う（κとE構造に基づく）
        
        理論的解釈:
        - κ_BASE高い → 低リスク選択（生存優先）
        - κ_CORE高い → 高リスク選択（順位逆転狙い）
        - κ_UPPER高い → 中リスク選択（バランス探索）
        - E_BASE高い → さらにリスク回避
        - E_CORE高い → さらにリスクテイク
        """
        if not self.is_alive:
            return 1
        
        # κ（整合慣性）の層別参照
        kappa_BASE = self.agent.state.kappa[HumanLayer.BASE.value]
        kappa_CORE = self.agent.state.kappa[HumanLayer.CORE.value]
        kappa_UPPER = self.agent.state.kappa[HumanLayer.UPPER.value]
        
        # E（未処理圧）の層別参照
        E_BASE = self.agent.state.E[HumanLayer.BASE.value]   # 生存プレッシャー
        E_CORE = self.agent.state.E[HumanLayer.CORE.value]   # 順位プレッシャー
        E_UPPER = self.agent.state.E[HumanLayer.UPPER.value] # 探索プレッシャー
        
        # κの構造から選択傾向を推定
        kappa_total = kappa_BASE + kappa_CORE + kappa_UPPER
        if kappa_total == 0:
            kappa_total = 1.0
        
        weight_BASE = kappa_BASE / kappa_total   # 生存志向
        weight_CORE = kappa_CORE / kappa_total   # 順位志向
        weight_UPPER = kappa_UPPER / kappa_total # 探索志向
        
        # 【性格別の解釈フィルター】
        if self.personality == 'cautious':
            # 慎重派: κ_BASEを「安全マージン」として解釈
            # 高いκ_BASE → より低い選択値
            base_choice = 1.0 + weight_BASE * 3.0  # 1-4
            core_factor = 1.0 + weight_CORE * 2.0  # 順位劣勢なら上げる
            upper_factor = 1.0 + weight_UPPER * 1.0
            
            # E補正
            if E_BASE > 1.0:  # HP欠損
                base_choice -= 1.0  # さらに安全に
            if E_CORE > 2.0:  # 順位劣勢
                core_factor += 0.5
            
            choice_value = base_choice * core_factor * upper_factor
        
        elif self.personality == 'aggressive':
            # 攻撃派: κ_COREを「逆転への執念」として解釈
            # 高いκ_CORE → より高い選択値
            base_choice = 5.0 + weight_CORE * 5.0  # 5-10
            safety_factor = weight_BASE * 0.5  # 生存本能が抑制
            explore_factor = 1.0 + weight_UPPER * 0.5
            
            # E補正
            if E_CORE > 2.0:  # 順位劣勢
                base_choice += 1.0  # さらに攻撃的に
            if E_BASE > 2.0:  # HP危機
                safety_factor += 0.3  # 少し抑制
            
            choice_value = base_choice * (1.0 - safety_factor * 0.3) * explore_factor
        
        else:  # balanced
            # バランス派: κ_UPPERを「最適解探索」として解釈
            # 状況に応じて5-7を中心に探索
            base_choice = 5.0 + weight_UPPER * 2.0
            rank_factor = (current_rank - 1) / 6.0  # 順位が下なら上げる
            hp_factor = (GameConfig.STARTING_HP - self.hp) / GameConfig.STARTING_HP
            
            # E補正
            if E_CORE > 2.0:
                rank_factor += 0.3
            if E_BASE > 1.0:
                hp_factor += 0.2
            
            choice_value = base_choice + rank_factor * 3.0 - hp_factor * 2.0
        
        # 最終選択値（1-10に制約）
        choice = int(np.clip(choice_value, 1, 10))
        
        # 履歴記録
        self.choice_history.append(choice)
        
        return choice
    
    def process_result(self, choice: int, crashed: bool, score_gained: int):
        """結果処理とSSD更新"""
        if not self.is_alive:
            return
        
        # スコア更新
        if not crashed:
            self.score += score_gained
            self.total_score += score_gained
        
        # HP更新
        if crashed:
            self.hp -= 1
            self.crash_history.append(1)
            if self.hp <= 0:
                self.is_alive = False
        else:
            self.crash_history.append(0)
        
        # SSD更新（性格別のHumanPressure設計）
        self._update_ssd(choice, crashed, score_gained)
    
    def _update_ssd(self, choice: int, crashed: bool, score_gained: int):
        """SSD状態を更新（性格別の学習）
        
        重要: 同じ結果でも、性格によって受け取る教訓が異なる
        - cautious: クラッシュを「生存脅威」として強く学習
        - aggressive: 成功を「順位逆転の手段」として強く学習
        - balanced: 結果を「データポイント」として中立的に学習
        """
        
        # リスクレベル判定
        is_low_risk = choice <= 4
        is_medium_risk = 5 <= choice <= 7
        is_high_risk = choice >= 8
        
        # 報酬計算（正規化）
        reward = score_gained / 100.0 if not crashed else -1.0
        
        # 【性格別の解釈フィルター】
        if self.personality == 'cautious':
            # 慎重派: クラッシュへの恐怖が強い
            if crashed:
                # クラッシュ → BASE超強化（生存脅威）
                pressure = HumanPressure(
                    base=3.0,      # 強い生存圧力
                    core=-0.5 * abs(reward),
                    upper=-0.2 * abs(reward)
                )
            else:
                if is_low_risk:
                    # 低リスク成功 → BASE強化（正しい選択）
                    pressure = HumanPressure(
                        base=1.5 * reward,
                        core=0.2 * reward,
                        upper=0.1 * reward
                    )
                else:
                    # 高リスク成功 → CORE微増（でも怖い）
                    pressure = HumanPressure(
                        base=-0.3 * reward,  # 不安
                        core=0.8 * reward,
                        upper=0.3 * reward
                    )
        
        elif self.personality == 'aggressive':
            # 攻撃派: 逆転への執念が強い
            if crashed:
                # クラッシュ → CORE減少だがUPPER増（"次は成功する"）
                pressure = HumanPressure(
                    base=0.5,  # 生存意識は低い
                    core=-0.4 * abs(reward),
                    upper=1.0  # 再挑戦欲求
                )
            else:
                if is_high_risk:
                    # 高リスク成功 → CORE超強化（逆転の手段）
                    pressure = HumanPressure(
                        base=-0.2 * reward,
                        core=2.0 * reward,  # 強い順位意識
                        upper=0.5 * reward
                    )
                else:
                    # 低リスク成功 → 物足りない
                    pressure = HumanPressure(
                        base=0.3 * reward,
                        core=0.5 * reward,
                        upper=0.2 * reward
                    )
        
        else:  # balanced
            # バランス派: データ収集として中立的に学習
            if crashed:
                # クラッシュ → UPPER増（"この選択値は危険"という学習）
                risk_level = choice / 10.0
                pressure = HumanPressure(
                    base=0.8 * risk_level,
                    core=0.3,
                    upper=1.2 * risk_level  # 探索的学習
                )
            else:
                # 成功 → UPPER強化（"この選択値は有効"）
                risk_level = choice / 10.0
                score_factor = score_gained / 100.0
                pressure = HumanPressure(
                    base=0.3 * score_factor,
                    core=0.6 * score_factor,
                    upper=1.0 * score_factor * risk_level
                )
        
        # HumanAgentにステップ
        self.agent.step(pressure, dt=1.0)
    
    def decide_hp_purchase(self, rank: int) -> int:
        """HP購入判断（κとEに基づく）"""
        if not self.is_alive:
            return 0
        
        cost_per_hp = GameConfig.HP_PURCHASE_COST
        max_purchasable = min(
            self.score // cost_per_hp,
            GameConfig.MAX_HP - self.hp
        )
        
        if max_purchasable <= 0:
            return 0
        
        # κ平均値
        avg_kappa = np.mean(self.agent.state.kappa)
        
        # E_BASE（生存圧力）が高いほど購入意欲
        E_BASE = self.agent.state.E[HumanLayer.BASE.value]
        purchase_pressure = E_BASE
        
        # HP欠損度
        hp_ratio = self.hp / GameConfig.STARTING_HP
        if hp_ratio < 0.5:
            purchase_pressure += 2.0
        
        # 順位が悪い場合は購入を抑制（スコアで逆転狙い）
        if rank > 3:
            purchase_pressure *= 0.5
        
        # κと比較
        if purchase_pressure > avg_kappa * 2.0:
            return max_purchasable  # 全購入
        elif purchase_pressure > avg_kappa:
            return max(1, max_purchasable // 2)  # 半分購入
        else:
            return 0  # 見送り
    
    def reset_set_score(self):
        """セットスコアをリセット"""
        self.score = 0
    
    def get_state_summary(self) -> str:
        """状態サマリー"""
        kappa = self.agent.state.kappa
        E = self.agent.state.E
        
        # 優勢な層を判定
        dominant_layer = None
        max_kappa = max(kappa)
        if kappa[HumanLayer.BASE.value] == max_kappa:
            dominant_layer = "生存志向（BASE優勢）"
        elif kappa[HumanLayer.CORE.value] == max_kappa:
            dominant_layer = "順位志向（CORE優勢）"
        else:
            dominant_layer = "探索志向（UPPER優勢）"
        
        return (
            f"κ: BASE={kappa[HumanLayer.BASE.value]:.2f}, "
            f"CORE={kappa[HumanLayer.CORE.value]:.2f}, "
            f"UPPER={kappa[HumanLayer.UPPER.value]:.2f} | "
            f"E: BASE={E[HumanLayer.BASE.value]:.2f}, "
            f"CORE={E[HumanLayer.CORE.value]:.2f}, "
            f"UPPER={E[HumanLayer.UPPER.value]:.2f} | "
            f"{dominant_layer}"
        )


# ===== ゲーム進行 =====
def play_round(players: List[ApexPlayerPure], round_num: int, total_rounds: int) -> Dict:
    """1ラウンドを実行"""
    print(f"\n{'='*60}")
    print(f"🎲 ラウンド {round_num}/{total_rounds}")
    print(f"{'='*60}")
    
    # ラウンド開始処理（E減衰）
    for player in players:
        player.on_round_start()
    
    # 順位とスコア差を計算
    alive_players = [p for p in players if p.is_alive]
    if not alive_players:
        return {'all_dead': True}
    
    sorted_players = sorted(alive_players, key=lambda p: p.total_score, reverse=True)
    leader_score = sorted_players[0].total_score
    
    # 各プレイヤーの選択
    choices = {}
    for player in alive_players:
        current_rank = sorted_players.index(player) + 1
        choice = player.make_choice(current_rank, leader_score, round_num, total_rounds)
        choices[player.name] = choice
        
        print(f"{player.color}{player.name}{Colors.RESET}: "
              f"選択={choice} (HP={player.hp}, Score={player.total_score})")
    
    # クラッシュ判定と結果処理
    print(f"\n{'─'*60}")
    print("📊 結果")
    print(f"{'─'*60}")
    
    for player in alive_players:
        choice = choices[player.name]
        config = GameConfig.CHOICES[choice]
        crash_rate = config['crash_rate']
        score = config['score']
        
        crashed = random.random() < crash_rate
        player.process_result(choice, crashed, score)
        
        if crashed:
            print(f"{player.color}{player.name}{Colors.RESET}: "
                  f"💥 CRASH! HP={player.hp} ({'+HP' if player.hp > 0 else '脱落'})")
        else:
            print(f"{player.color}{player.name}{Colors.RESET}: "
                  f"✅ 成功! +{score}pt (Total={player.total_score})")
    
    return {'all_dead': len([p for p in players if p.is_alive]) == 0}


def play_set(players: List[ApexPlayerPure], set_num: int) -> bool:
    """1セット（5ラウンド）を実行"""
    print(f"\n{'#'*60}")
    print(f"🎯 セット {set_num}/{GameConfig.TOTAL_SETS}")
    print(f"{'#'*60}")
    
    for round_num in range(1, GameConfig.ROUNDS_PER_SET + 1):
        result = play_round(players, round_num, GameConfig.ROUNDS_PER_SET)
        if result.get('all_dead'):
            print("\n⚠️ 全員脱落！ゲーム終了")
            return True
    
    # HP購入フェーズ
    print(f"\n{'='*60}")
    print("💊 HP購入フェーズ")
    print(f"{'='*60}")
    
    alive_players = [p for p in players if p.is_alive]
    sorted_players = sorted(alive_players, key=lambda p: p.total_score, reverse=True)
    
    for player in alive_players:
        rank = sorted_players.index(player) + 1
        purchase = player.decide_hp_purchase(rank)
        
        if purchase > 0:
            cost = purchase * GameConfig.HP_PURCHASE_COST
            player.score -= cost
            player.total_score -= cost
            player.hp += purchase
            print(f"{player.color}{player.name}{Colors.RESET}: "
                  f"HP +{purchase} (Cost={cost}, HP={player.hp})")
        else:
            print(f"{player.color}{player.name}{Colors.RESET}: 見送り")
    
    # セットスコアリセット
    for player in players:
        player.reset_set_score()
    
    return False


def main():
    """メイン関数"""
    print(f"{Colors.BOLD}")
    print("="*60)
    print("🎮 APEX SURVIVOR - SSD Pure Theoretical版")
    print("="*60)
    print(f"{Colors.RESET}")
    print("頂点に立つ者だけが生き残る")
    print("1位以外全員死亡のデスゲーム")
    print()
    
    # プレイヤー初期化
    players = [
        ApexPlayerPure("太郎", "cautious", Colors.RED),
        ApexPlayerPure("花子", "aggressive", Colors.MAGENTA),
        ApexPlayerPure("スミス", "balanced", Colors.CYAN),
        ApexPlayerPure("田中", "cautious", Colors.GREEN),
        ApexPlayerPure("佐藤", "aggressive", Colors.YELLOW),
        ApexPlayerPure("鈴木", "balanced", Colors.BLUE),
        ApexPlayerPure("高橋", "balanced", Colors.WHITE),
    ]
    
    # ゲーム実行
    for set_num in range(1, GameConfig.TOTAL_SETS + 1):
        game_over = play_set(players, set_num)
        if game_over:
            break
    
    # 最終結果
    print(f"\n{Colors.BOLD}")
    print("="*60)
    print("🏆 最終結果")
    print("="*60)
    print(f"{Colors.RESET}")
    
    alive_players = [p for p in players if p.is_alive]
    all_players = sorted(players, key=lambda p: (p.is_alive, p.total_score), reverse=True)
    
    for i, player in enumerate(all_players, 1):
        status = "🏆 生存" if player.is_alive else "💀 脱落"
        print(f"\n{i}位: {player.color}{player.name}{Colors.RESET} - {status}")
        print(f"  Total Score: {player.total_score}")
        print(f"  HP: {player.hp}")
        print(f"  Crash率: {sum(player.crash_history)}/{len(player.crash_history)} "
              f"({sum(player.crash_history)/len(player.crash_history)*100:.1f}%)")
        print(f"  SSD状態: {player.get_state_summary()}")
    
    # 勝者発表
    if alive_players:
        winner = max(alive_players, key=lambda p: p.total_score)
        print(f"\n{Colors.BOLD}{Colors.GREEN}")
        print("="*60)
        print(f"👑 WINNER: {winner.name}")
        print("="*60)
        print(f"{Colors.RESET}")
        print("頂点に立った者のみが生き残った...")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}")
        print("="*60)
        print("⚰️ 全員脱落...")
        print("="*60)
        print(f"{Colors.RESET}")


if __name__ == "__main__":
    main()
