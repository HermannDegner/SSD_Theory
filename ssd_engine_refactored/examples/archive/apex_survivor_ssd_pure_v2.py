"""
【APEX SURVIVOR - SSD Pure Theoretical版 v2】

元の実装との対比:
- 元: 複雑な意味圧計算（逆転圧力、排除ライン、多重葛藤）
- Pure版: κとEのみで同等の判断を実現

核心的な違い:
1位以外全員死亡 → 「本気で勝ちに行く」ロジックが必須
- 逆転可能性計算（remaining rounds × 100 vs score gap）
- HP1の命がけボーナス（+30%）
- 1位は守り、下位は攻め
"""

import sys
from pathlib import Path

# パス設定（ssd_engine_refactored を追加）
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

import random
import numpy as np
from ssd_human_module import HumanAgent, HumanPressure, HumanLayer


# ===== ゲーム設定 =====
class GameConfig:
    """APEX SURVIVOR ゲームルール"""
    CHOICES = {
        1: {'score': 10, 'crash_rate': 0.05},
        2: {'score': 20, 'crash_rate': 0.10},
        3: {'score': 30, 'crash_rate': 0.15},
        4: {'score': 40, 'crash_rate': 0.20},
        5: {'score': 50, 'crash_rate': 0.25},
        6: {'score': 60, 'crash_rate': 0.35},
        7: {'score': 70, 'crash_rate': 0.45},
        8: {'score': 80, 'crash_rate': 0.55},
        9: {'score': 90, 'crash_rate': 0.65},
        10: {'score': 100, 'crash_rate': 0.75}
    }
    
    STARTING_HP = 3
    MAX_HP = 5
    HP_PURCHASE_COST = 20
    
    ROUNDS_PER_SET = 5
    TOTAL_SETS = 5


# ===== プレイヤークラス（v2: 戦略的計算強化版） =====
class ApexPlayerV2:
    """APEX SURVIVOR プレイヤー（v2: 本気で勝ちに行く版）
    
    v1との違い:
    - 逆転可能性の精密計算
    - HP1命がけボーナス（+30%）考慮
    - 1位=守り、下位=攻め の明確な戦略
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
        
        # HumanAgent（Pure Theoretical版の核心）
        self.agent = HumanAgent()
        self._initialize_personality()
    
    def _initialize_personality(self):
        """性格別κ初期化
        
        APEX SURVIVORの解釈:
        - BASE: 生存本能（クラッシュ恐怖）
        - CORE: 勝利欲求（1位以外は死）
        - UPPER: 戦略的思考（逆転計算）
        """
        if self.personality == 'cautious':
            self.agent.state.kappa[HumanLayer.BASE.value] = 0.8  # 強い生存本能
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.3
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.4
        elif self.personality == 'aggressive':
            self.agent.state.kappa[HumanLayer.BASE.value] = 0.2
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.9  # 強い勝利欲求
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.6
        else:  # balanced
            self.agent.state.kappa[HumanLayer.BASE.value] = 0.5
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.5
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.8  # 強い戦略性
    
    def on_round_start(self):
        """ラウンド開始（E自然減衰）"""
        if self.is_alive:
            self.agent.step(HumanPressure(), dt=1.0)
    
    def make_choice(self, current_rank: int, leader_score: int, round_num: int, 
                    total_rounds: int, alive_count: int, current_set: int, total_sets: int) -> int:
        """選択決定（戦略的計算 + κ構造）
        
        元の実装の核心ロジック:
        1. 逆転可能性判定（reversal_pressure）
        2. HP1命がけボーナス（+30%）
        3. 順位別戦略（1位=守り、下位=攻め）
        4. 最終ラウンド/最終セット補正
        """
        if not self.is_alive:
            return 1
        
        # === 1. κ構造の参照 ===
        kappa_BASE = self.agent.state.kappa[HumanLayer.BASE.value]
        kappa_CORE = self.agent.state.kappa[HumanLayer.CORE.value]
        kappa_UPPER = self.agent.state.kappa[HumanLayer.UPPER.value]
        kappa_sum = kappa_BASE + kappa_CORE + kappa_UPPER
        
        if kappa_sum < 0.01:
            kappa_sum = 1.0
        
        w_BASE = kappa_BASE / kappa_sum
        w_CORE = kappa_CORE / kappa_sum
        w_UPPER = kappa_UPPER / kappa_sum
        
        # === 2. 戦略的状況分析 ===
        score_gap = leader_score - self.score if current_rank > 1 else 0
        remaining_rounds = total_rounds - round_num
        remaining_sets = total_sets - current_set + 1
        
        # HP1命がけボーナス（元の実装の重要ポイント）
        hp1_bonus = 1.3 if self.hp == 1 else 1.0
        
        # 今セットでの最大獲得可能点数
        max_gain_this_set = int(100 * remaining_rounds * hp1_bonus)
        
        # 逆転可能性
        reversal_possible = (score_gap <= max_gain_this_set)
        reversal_urgency = min(score_gap / (max_gain_this_set + 1), 1.0) if reversal_possible else 1.0
        
        # === 3. 順位別の戦略マルチプライヤ ===
        if current_rank == 1:
            # 【1位: 守りに徹する】
            strategic_mult = 0.5 - min(score_gap / 300.0, 0.2)  # 0.3～0.5（リード大=超安全）
        
        elif current_rank <= 3:
            # 【2-3位: 逆転可能なら攻める】
            if reversal_possible:
                strategic_mult = 1.0 + reversal_urgency * 0.8  # 1.0～1.8
            else:
                # 逆転不可能でも次セットがあるなら希望
                if remaining_sets > 1:
                    strategic_mult = 0.9  # 次セットで巻き返し
                else:
                    strategic_mult = 0.6  # 諦めモード
        
        else:
            # 【4-7位: 背水の陣】
            if reversal_possible:
                strategic_mult = 1.3 + reversal_urgency * 1.2  # 1.3～2.5（全力攻撃）
            else:
                if remaining_sets > 1:
                    strategic_mult = 0.8  # まだチャンスあり
                else:
                    strategic_mult = 0.4  # 完全に諦め
        
        # === 4. 最終局面の極限補正 ===
        is_final_moment = (round_num == total_rounds and current_set == total_sets)
        
        if is_final_moment:
            if current_rank == 1:
                strategic_mult *= 0.4  # 絶対に守る（1を選びたい）
            elif current_rank <= 3:
                strategic_mult *= 1.8  # 最後の賭け
            else:
                strategic_mult *= 2.5  # 奇跡を信じて全力
        
        # === 5. 性格別の基本選択値（κ解釈フィルター） ===
        if self.personality == 'cautious':
            # κ_BASEを「安全マージン」として解釈
            base_value = 2.0 + w_BASE * 4.0  # 2-6
        elif self.personality == 'aggressive':
            # κ_COREを「勝利への執念」として解釈
            base_value = 6.0 + w_CORE * 4.0  # 6-10
        else:  # balanced
            # κ_UPPERを「最適戦略探索」として解釈
            base_value = 4.0 + w_UPPER * 4.0  # 4-8
        
        # === 6. HP危機による恐怖抑制 ===
        hp_ratio = self.hp / GameConfig.MAX_HP
        
        if hp_ratio <= 0.2:  # HP=1/5
            hp_fear = 0.5  # 強烈な恐怖
        elif hp_ratio <= 0.4:  # HP=2/5
            hp_fear = 0.7  # 警戒
        elif hp_ratio <= 0.6:  # HP=3/5
            hp_fear = 0.9  # やや慎重
        else:
            hp_fear = 1.0  # 余裕
        
        # === 7. 終盤戦の圧力（alive_count少ない=緊張MAX） ===
        endgame_pressure = 1.0
        if alive_count <= 3:
            if current_rank == 1:
                endgame_pressure = 0.7  # 守りが極大化
            else:
                endgame_pressure = 1.5  # 攻めが極大化
        
        # === 8. 最終選択値計算 ===
        final_value = base_value * strategic_mult * hp_fear * endgame_pressure
        
        # 1-10に丸める
        choice = max(1, min(10, int(final_value + 0.5)))
        
        self.choice_history.append(choice)
        return choice
    
    def process_result(self, choice: int, crashed: bool, score_gained: int):
        """結果処理とSSD学習"""
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
        
        # SSD学習
        self._update_ssd(choice, crashed, score_gained)
    
    def _update_ssd(self, choice: int, crashed: bool, score_gained: int):
        """SSD学習（性格別のHumanPressure設計）"""
        
        # リスクレベル分析
        crash_rate = GameConfig.CHOICES[choice]['crash_rate']
        is_high_risk = (choice >= 7)
        is_safe = (choice <= 3)
        
        # 【性格別の学習パターン】
        if self.personality == 'cautious':
            # 慎重派: クラッシュに過剰反応
            if crashed:
                pressure = HumanPressure(
                    base=4.0,   # 強烈な生存恐怖
                    core=0.5,
                    upper=0.2
                )
            elif not crashed and is_high_risk:
                pressure = HumanPressure(
                    base=-2.0,  # 「リスク取って成功した」を生存層で学習
                    core=1.0,
                    upper=0.5
                )
            else:
                pressure = HumanPressure(
                    base=-1.0,  # 安全成功を強化
                    core=0.3,
                    upper=0.1
                )
        
        elif self.personality == 'aggressive':
            # 攻撃派: 勝利への執念で学習
            if crashed:
                pressure = HumanPressure(
                    base=1.5,   # 生存恐怖は弱い
                    core=3.0,   # 「勝てなかった」が圧力
                    upper=0.5
                )
            elif not crashed and is_high_risk:
                pressure = HumanPressure(
                    base=0.0,
                    core=-3.0,  # 「ハイリスクで勝った」を順位層で強化
                    upper=1.0
                )
            else:
                pressure = HumanPressure(
                    base=0.0,
                    core=-1.0,  # 勝利を評価
                    upper=0.3
                )
        
        else:  # balanced
            # バランス派: 戦略的学習
            reward = score_gained / 100.0
            risk = crash_rate
            
            if crashed:
                pressure = HumanPressure(
                    base=2.0,         # 中程度の恐怖
                    core=1.5,         # 失点の圧力
                    upper=risk * 3.0  # リスク計算を学習
                )
            else:
                pressure = HumanPressure(
                    base=-1.0,
                    core=-reward * 2.0,         # 報酬を評価
                    upper=-risk * reward * 1.5  # リスク・リターン比を学習
                )
        
        # SSD更新
        self.agent.step(pressure, dt=1.0)
    
    def decide_hp_purchase(self) -> int:
        """HP購入判断（元の実装の精密ロジックを簡略化）"""
        if self.score < GameConfig.HP_PURCHASE_COST:
            return 0  # 購入不可
        
        current_hp = self.hp
        max_affordable = self.score // GameConfig.HP_PURCHASE_COST
        max_needed = GameConfig.MAX_HP - current_hp
        max_purchasable = min(max_affordable, max_needed)
        
        if max_purchasable <= 0:
            return 0
        
        # κ構造で判断
        kappa_BASE = self.agent.state.kappa[HumanLayer.BASE.value]
        kappa_CORE = self.agent.state.kappa[HumanLayer.CORE.value]
        
        hp_ratio = current_hp / GameConfig.MAX_HP
        
        # 生存本能 vs 勝利欲求
        if hp_ratio <= 0.4:  # HP危機
            # κ_BASE高い → HP購入優先
            if kappa_BASE > 0.5:
                return min(2, max_purchasable)
            else:
                return min(1, max_purchasable)
        elif kappa_CORE > 0.7:  # 攻撃的
            # スコア優先（HP購入しない）
            return 0
        else:
            # バランス
            return min(1, max_purchasable) if random.random() < 0.5 else 0
    
    def reset_set_score(self):
        """セット終了時のリセット"""
        self.score = 0


# ===== ゲーム進行関数 =====
def play_round(players: list, round_num: int, total_rounds: int, current_set: int, total_sets: int):
    """1ラウンドの実行"""
    alive_players = [p for p in players if p.is_alive]
    
    if len(alive_players) == 0:
        return
    
    # ラウンド開始処理
    for p in alive_players:
        p.on_round_start()
    
    # 順位計算
    sorted_players = sorted(alive_players, key=lambda x: x.score, reverse=True)
    ranks = {p.name: i+1 for i, p in enumerate(sorted_players)}
    leader_score = sorted_players[0].score if sorted_players else 0
    
    print(f"\n{'='*60}")
    print(f"🎲 ラウンド {round_num}/{total_rounds}")
    print(f"{'='*60}")
    
    # 選択
    choices = []
    for p in alive_players:
        rank = ranks[p.name]
        choice = p.make_choice(rank, leader_score, round_num, total_rounds, 
                              len(alive_players), current_set, total_sets)
        crash_rate = GameConfig.CHOICES[choice]['crash_rate']
        print(f"{p.name}: 選択={choice} (HP={p.hp}, Score={p.score}, クラッシュ率={int(crash_rate*100)}%)")
        choices.append((p, choice))
    
    # 結果判定
    print(f"\n{'-'*60}")
    print(f"📊 結果")
    print(f"{'-'*60}")
    
    for p, choice in choices:
        crashed = random.random() < GameConfig.CHOICES[choice]['crash_rate']
        score_gained = 0 if crashed else GameConfig.CHOICES[choice]['score']
        
        p.process_result(choice, crashed, score_gained)
        
        if crashed:
            status = f"💥 CRASH! HP={p.hp}"
            if not p.is_alive:
                status += " (脱落)"
        else:
            status = f"✅ 成功! +{score_gained}pt (Total={p.score})"
        
        print(f"{p.name}: {status}")


def play_set(players: list, set_num: int, total_sets: int):
    """1セットの実行"""
    print(f"\n{'#'*60}")
    print(f"🎯 セット {set_num}/{total_sets}")
    print(f"{'#'*60}")
    
    for round_num in range(1, GameConfig.ROUNDS_PER_SET + 1):
        play_round(players, round_num, GameConfig.ROUNDS_PER_SET, set_num, total_sets)
    
    # HP購入フェーズ
    print(f"\n{'='*60}")
    print(f"💊 HP購入フェーズ")
    print(f"{'='*60}")
    
    for p in players:
        if not p.is_alive:
            continue
        
        purchase = p.decide_hp_purchase()
        if purchase > 0:
            cost = purchase * GameConfig.HP_PURCHASE_COST
            p.hp += purchase
            p.score -= cost
            p.total_score -= cost
            print(f"{p.name}: HP +{purchase} (Cost={cost}, HP={p.hp})")
        else:
            print(f"{p.name}: 見送り")
    
    # セットスコアリセット
    for p in players:
        p.reset_set_score()


def print_final_results(players: list):
    """最終結果表示"""
    print(f"\n\n{'='*60}")
    print(f"🏆 最終結果")
    print(f"{'='*60}\n")
    
    sorted_players = sorted(players, key=lambda x: x.total_score, reverse=True)
    
    for rank, p in enumerate(sorted_players, 1):
        status = "🏆 生存" if rank == 1 else "💀 脱落"
        crash_rate = (sum(p.crash_history) / len(p.crash_history) * 100) if p.crash_history else 0
        
        kappa_BASE = p.agent.state.kappa[HumanLayer.BASE.value]
        kappa_CORE = p.agent.state.kappa[HumanLayer.CORE.value]
        kappa_UPPER = p.agent.state.kappa[HumanLayer.UPPER.value]
        
        E_BASE = p.agent.state.E[HumanLayer.BASE.value]
        E_CORE = p.agent.state.E[HumanLayer.CORE.value]
        E_UPPER = p.agent.state.E[HumanLayer.UPPER.value]
        
        # κ構造の解釈
        if kappa_BASE > max(kappa_CORE, kappa_UPPER):
            tendency = "生存志向（BASE優勢）"
        elif kappa_CORE > max(kappa_BASE, kappa_UPPER):
            tendency = "勝利志向（CORE優勢）"
        else:
            tendency = "戦略志向（UPPER優勢）"
        
        print(f"{rank}位: {p.name} - {status}")
        print(f"  Total Score: {p.total_score}")
        print(f"  HP: {p.hp}")
        print(f"  Crash率: {len([c for c in p.crash_history if c==1])}/{len(p.crash_history)} ({crash_rate:.1f}%)")
        print(f"  SSD状態: κ: BASE={kappa_BASE:.2f}, CORE={kappa_CORE:.2f}, UPPER={kappa_UPPER:.2f} | E: BASE={E_BASE:.2f}, CORE={E_CORE:.2f}, UPPER={E_UPPER:.2f} | {tendency}")
        print()
    
    winner = sorted_players[0]
    print(f"{'='*60}")
    print(f"👑 WINNER: {winner.name}")
    print(f"{'='*60}\n")
    print(f"頂点に立った者のみが生き残った...")


def main():
    """メイン関数"""
    print("""
============================================================
🎮 APEX SURVIVOR - SSD Pure Theoretical版 v2
============================================================

v1からの改善:
- 元の実装の戦略的計算を再現
- 逆転可能性の精密判定
- HP1命がけボーナス（+30%）実装
- 1位=守り、下位=攻め の明確化
- 最終局面での極限状況シミュレーション

「1位以外全員死亡」という極限ルール下で
SSD理論がどう機能するかを検証
""")
    
    # プレイヤー作成（7人）
    players = [
        ApexPlayerV2("太郎", "cautious", "red"),
        ApexPlayerV2("花子", "balanced", "green"),
        ApexPlayerV2("スミス", "balanced", "blue"),
        ApexPlayerV2("田中", "cautious", "yellow"),
        ApexPlayerV2("佐藤", "aggressive", "magenta"),
        ApexPlayerV2("鈴木", "balanced", "cyan"),
        ApexPlayerV2("高橋", "aggressive", "white")
    ]
    
    # 5セット実行
    for set_num in range(1, GameConfig.TOTAL_SETS + 1):
        play_set(players, set_num, GameConfig.TOTAL_SETS)
    
    # 最終結果
    print_final_results(players)


if __name__ == "__main__":
    main()
