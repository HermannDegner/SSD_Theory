"""
【APEX SURVIVOR - SSD Pure Theoretical版 v3】

v2の構造的矛盾を解決:
- v2: 戦略ロジック（strategic_mult）が外部でハードコード → SSD力学のバイパス
- v3: 状況認識を意味圧（HumanPressure）に変換 → E/κの内部力学から行動が創発

理論的整合性:
1. make_choice = 状況を層別HumanPressureに変換して入力
2. agent.step() = E（未処理圧）を更新
3. 選択決定 = E/κのバランスから創発的に決定

「1位以外全員死亡」という極限状況で
SSDエージェントの内部状態（E/κ）から行動が創発することを実証
"""

import sys
from pathlib import Path

# パス設定
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
    
    # セット順位ボーナス（逆転可能性を高める）
    SET_RANK_BONUS = {
        1: 50,   # 1位: +50pts（大きな逆転チャンス）
        2: 30,   # 2位: +30pts
        3: 15,   # 3位: +15pts
        # 4位以下: 0pts
    }


# ===== プレイヤークラス（v3: 完全なSSD理論整合版） =====
class ApexPlayerV3:
    """APEX SURVIVOR プレイヤー（v3: E/κから行動が創発）
    
    v2からの根本的変更:
    - make_choice: 戦略計算を廃止 → 状況認識を意味圧に変換
    - 行動決定: E/κのバランスから創発的に選択
    - 理論的整合性: HumanAgentの内部力学が行動を完全に駆動
    """
    
    def __init__(self, name: str, personality: str, color: str):
        self.name = name
        self.personality = personality
        self.color = color
        
        # ゲーム状態
        self.hp = GameConfig.STARTING_HP
        self.score = 0  # 累計スコア（total_scoreと統一）
        self.total_score = 0  # 後方互換性のため残すが、scoreと同義
        self.is_alive = True
        self.choice_history = []
        self.crash_history = []
        
        # 脱落情報
        self.elimination_set = None  # 脱落したセット番号
        self.elimination_round = None  # 脱落したラウンド番号
        
        # HumanAgent（Pure Theoretical版の核心）
        self.agent = HumanAgent()
        self._initialize_personality()
    
    def _initialize_personality(self):
        """性格別κ初期化
        
        APEX SURVIVORの解釈:
        - BASE: 生存本能（クラッシュ恐怖） ← 本能的、最初から高い
        - CORE: 勝利欲求（1位以外は死） ← 後天的、ゲーム経験で成長
        - UPPER: 戦略的思考（状況分析） ← 後天的、学習で成長
        
        【重要】死の恐怖は根源的意味圧
        - 生存本能（BASE κ）は生まれつき刻まれている
        - 進化的に確立された価値 → 初期値10-15
        - これにより、HP=1での生存圧が確実に優勢になる
        """
        if self.personality == 'cautious':
            # 慎重派: 生存本能が特に強い
            self.agent.state.kappa[HumanLayer.BASE.value] = 15.0  # 根源的生存本能（進化的刻印）
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.3   # 勝利欲求は控えめ
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.4  # 戦略性も低め
        elif self.personality == 'aggressive':
            # 攻撃派: 生存本能は標準、勝利欲求が強い
            self.agent.state.kappa[HumanLayer.BASE.value] = 10.0  # 根源的生存本能（標準）
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.9   # 強い勝利欲求
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.6  # 中程度の戦略性
        else:  # balanced
            # バランス派: 生存本能は標準、戦略性重視
            self.agent.state.kappa[HumanLayer.BASE.value] = 12.0  # 根源的生存本能（やや強め）
            self.agent.state.kappa[HumanLayer.CORE.value] = 0.5   # 標準的勝利欲求
            self.agent.state.kappa[HumanLayer.UPPER.value] = 0.8  # 強い戦略性
    
    def on_round_start(self):
        """ラウンド開始（E自然減衰）"""
        if self.is_alive:
            self.agent.step(HumanPressure(), dt=1.0)
    
    def make_choice(self, current_rank: int, leader_score: int, round_num: int, 
                    total_rounds: int, alive_count: int, current_set: int, total_sets: int) -> int:
        """選択決定（SSD理論完全整合版）
        
        【理論的プロセス】
        1. 状況認識 → 層別HumanPressureに変換
        2. agent.step(pressure) → E更新
        3. E/κバランスから選択が創発
        
        v2との違い:
        - v2: strategic_mult計算 → 外部ロジックで選択
        - v3: 状況→意味圧変換 → E/κから選択が創発
        """
        if not self.is_alive:
            return 1
        
        # ===== STEP 1: 状況認識を層別意味圧に変換 =====
        pressure = HumanPressure()
        
        # 【BASE層: 生存圧力（非線形）】
        # HP減少による恐怖は指数関数的に増大
        # HP=1: 次のクラッシュ=即死 → 圧倒的恐怖
        # HP=2: 2回の猶予 → まだ余裕
        # HP=3: 3回の猶予 → 通常レベル
        if self.hp == 1:
            # 【HP=1: 即死圏】次のクラッシュ=ゲームオーバー
            # 「優勝以外死」より「今死ぬ」方が強烈な恐怖
            pressure.base += 400.0  # 即死恐怖（×8倍増）← ×2倍に強化
            pressure.upper += 50.0  # 「絶対にリスク回避」戦略
            pressure.core -= 150.0  # 勝利欲求を完全抑制（×3倍増）
        elif self.hp == 2:
            # 【HP=2: 警戒圏】あと1回クラッシュでHP=1（即死圏）
            pressure.base += 80.0  # 強い警戒
            pressure.upper += 20.0  # リスク計算
            pressure.core -= 30.0  # 勝利欲求を軽く抑制
        elif self.hp == 3:
            # 【HP=3: 通常圏】初期値、まだ余裕
            pressure.base += 20.0  # 軽い警戒
        # HP=4-5: 圧力なし（十分な余裕）
        
        # 【CORE層: 勝利圧力】
        # 「1位以外全員死亡」という極限ルールによる勝利要求
        if current_rank > 1:
            # 【2-7位: 「このまま終わったら自分は死ぬ」絶対的恐怖】
            score_gap = leader_score - self.score
            remaining_rounds = total_rounds - round_num
            remaining_sets = total_sets - current_set + 1
            
            # HP1なら命がけボーナス考慮
            hp1_bonus = 1.3 if self.hp == 1 else 1.0
            max_gain_rounds = int(100 * remaining_rounds * hp1_bonus)
            
            # セット順位ボーナスも逆転要素（1位なら+50pts）
            max_set_bonus = GameConfig.SET_RANK_BONUS.get(1, 0)
            max_gain = max_gain_rounds + max_set_bonus
            
            # 【セットボーナスの価値を意味圧化】
            # 残りセット数 × 1位ボーナス50pts = 獲得可能なボーナス総額
            potential_set_bonuses = remaining_sets * max_set_bonus
            # ボーナスの価値 = 総額の1/3を意味圧に変換（50pt→16.7圧）
            bonus_value_pressure = potential_set_bonuses / 3.0
            
            # スコア差が大きいほど絶望的（差×3の意味圧 + ボーナス価値）
            gap_pressure = min(400.0, score_gap * 3.0 - bonus_value_pressure)
            
            # 逆転可能性判定（セットボーナス込み）
            if score_gap <= max_gain:
                # 逆転可能 → 「勝つために全力で攻めなければ死ぬ」
                urgency = score_gap / (max_gain + 1)
                
                # 【HP1ボーナスの意味圧化】
                # HP=1時は+30%獲得可能 → ハイリスク・ハイリターンの価値
                # この「命がけで逆転可能」という希望を意味圧に変換
                hp1_hope_pressure = 0.0
                if self.hp == 1:
                    # 30%ボーナス = 残りラウンド数 × 30pts相当の希望
                    hp1_hope_value = remaining_rounds * 30
                    hp1_hope_pressure = hp1_hope_value / 2.0  # 希望を意味圧に変換
                
                if current_rank <= 3:
                    # 2-3位: まだ逆転可能性がある
                    pressure.core += 200.0 + gap_pressure + hp1_hope_pressure  # 「勝たなければ死」
                    pressure.upper += 100.0  # 戦略的判断「どう逆転するか」
                else:
                    # 4-7位: 背水の陣「もう博打しかない」
                    pressure.core += 350.0 + gap_pressure + hp1_hope_pressure  # 絶望的な勝利欲求
                    pressure.upper += 150.0  # 「どうリスク取るか」
            else:
                # 逆転不可能 → 「このままだと100%死ぬ」という絶望
                if remaining_sets > 1:
                    # 次セットに期待「今セットは捨ててHPだけ守る」
                    pressure.core -= 50.0  # 勝利欲求一時停止
                    pressure.upper -= 30.0  # 理念的挫折
                    pressure.base += 150.0  # 「次のチャンスまで生き延びろ」
                else:
                    # 完全に絶望 → 「どうせ死ぬなら生き延びることだけ考える」
                    pressure.core -= 100.0  # 勝利欲求の完全喪失
                    pressure.upper -= 80.0  # 理念的崩壊
                    pressure.base += 250.0  # 「もう生きることしか...」
        
        elif current_rank == 1:
            # 【1位: 「追ってくる2位に逆転される恐怖」】
            # 自分が1位なので leader_score == self.score
            # 問題: 2位のスコアが不明 → 最悪ケースを想定
            
            remaining_rounds = total_rounds - round_num
            remaining_sets = total_sets - current_set + 1
            
            # 【2位の最大追い上げ可能性を計算】
            # 2位が全ラウンドで100pt獲得 + セットボーナス最大化
            second_max_gain_per_round = 100
            second_max_set_bonus = GameConfig.SET_RANK_BONUS.get(1, 0)  # 1位ボーナス=50pt
            
            # 2位がHP=1で命がけ戦略を取る可能性（+30%ボーナス）
            second_hp1_potential = int(second_max_gain_per_round * 0.3)  # 30pt/ラウンド
            
            # 2位の最大追い上げ = 通常獲得 + HP1ボーナス + セットボーナス
            second_total_max_gain = (second_max_gain_per_round + second_hp1_potential) * remaining_rounds
            second_total_max_gain += second_max_set_bonus * min(remaining_sets, remaining_rounds // 5 + 1)
            
            # 【1位のリード防衛に必要な獲得量】
            # 自分が現在のリードを維持するために必要な獲得
            # （2位の追い上げに対抗する必要がある）
            
            # 【HP1ボーナスの意味圧化（1位の場合）】
            # HP=1なら命がけで+30%獲得 → リードを大きく広げられる
            hp1_lead_expansion = 0.0
            if self.hp == 1 and remaining_rounds > 0:
                # 命がけで稼げる追加ポイントの価値
                hp1_extra_value = remaining_rounds * 30  # 30pts/ラウンド
                hp1_lead_expansion = hp1_extra_value / 3.0  # リード拡大価値を意味圧化
            
            # 【リードの大きさによる意味圧調整】
            # 注: leader_score == self.scoreなので、ここでは推定不可
            # 代わりに、残りラウンドでの2位の追い上げ可能性に基づく恐怖を設定
            
            # 逆転可能性 = 残りラウンド数が多いほど高い
            overtake_risk = min(1.0, second_total_max_gain / 200.0)  # 0.0-1.0にスケール
            
            if remaining_rounds <= 1:
                # ほぼ確定 → 「逃げ切り確実」だが油断禁物
                pressure.core += 100.0 + hp1_lead_expansion * 0.5
                pressure.upper += 30.0
                pressure.base += 30.0
            elif remaining_rounds <= 3:
                # 終盤 → 「2位の追い上げに警戒」
                base_pressure = 150.0 + overtake_risk * 100.0  # 逆転リスクに応じて増加
                pressure.core += base_pressure + hp1_lead_expansion
                pressure.upper += 60.0 + overtake_risk * 40.0
                pressure.base += 50.0 + overtake_risk * 30.0
            else:
                # 序盤-中盤 → 「まだまだ油断できない」
                base_pressure = 200.0 + overtake_risk * 200.0  # 逆転リスクに応じて大幅増加
                pressure.core += base_pressure + hp1_lead_expansion
                pressure.upper += 100.0 + overtake_risk * 50.0
                pressure.base += 80.0 + overtake_risk * 40.0
        
        # 【セット内順位による意味圧（ボーナス獲得への希望/焦燥）】
        # セット終盤（ラウンド4-5）でセット内順位が確定に近づく
        rounds_left_in_set = total_rounds - round_num
        if rounds_left_in_set <= 1:  # セット終盤
            # 生存者の中でのセット内順位を推定（仮：総合順位と近い）
            if current_rank <= 3:
                # 1-3位圏内 → ボーナス獲得可能性あり
                potential_bonus = GameConfig.SET_RANK_BONUS.get(current_rank, 0)
                if potential_bonus > 0:
                    # ボーナス獲得への希望 → CORE圧を追加（「この順位を守る/上げる」）
                    bonus_hope_pressure = potential_bonus / 2.0  # 50pt→25圧, 30pt→15圧
                    pressure.core += bonus_hope_pressure
                    pressure.upper += bonus_hope_pressure * 0.5  # 戦略的計算
        
        # 【UPPER層: 戦略的認識】
        # 最終局面の認識
        is_final_moment = (round_num == total_rounds and current_set == total_sets)
        
        if is_final_moment:
            if current_rank == 1:
                pressure.base += 80.0  # 「絶対に守る」という理念
                pressure.upper += 60.0  # 戦略的確信（安全策）
            elif current_rank <= 3:
                pressure.core += 150.0  # 「最後の賭け」理念（極限の勝利欲求）
                pressure.upper += 80.0  # 戦略的決断（攻め）
            else:
                pressure.core += 200.0  # 「奇跡を信じる」理念（狂気）
                pressure.upper += 120.0  # 戦略的絶望（全力）
        
        # 終盤戦の圧力（alive_count少ない）
        if alive_count <= 3:
            if current_rank == 1:
                pressure.base += 40.0  # 守りが極大化
            else:
                pressure.core += 70.0  # 攻めが極大化
        
        # ===== STEP 2: 意味圧をHumanAgentに入力（E更新） =====
        self.agent.step(pressure, dt=1.0)
        
        # ===== STEP 3: E/κバランスから選択を創発 =====
        E_BASE = self.agent.state.E[HumanLayer.BASE.value]
        E_CORE = self.agent.state.E[HumanLayer.CORE.value]
        E_UPPER = self.agent.state.E[HumanLayer.UPPER.value]
        
        kappa_BASE = self.agent.state.kappa[HumanLayer.BASE.value]
        kappa_CORE = self.agent.state.kappa[HumanLayer.CORE.value]
        kappa_UPPER = self.agent.state.kappa[HumanLayer.UPPER.value]
        
        # E > κ の層は「行動要求」
        # E < κ の層は「行動抑制」
        
        action_BASE = max(0, E_BASE - kappa_BASE)  # 生存行動要求（安全志向）
        action_CORE = max(0, E_CORE - kappa_CORE)  # 勝利行動要求（攻撃志向）
        action_UPPER = max(0, E_UPPER - kappa_UPPER)  # 戦略行動要求（計算志向）
        
        # 抑制（E < κ）
        suppress_BASE = max(0, kappa_BASE - E_BASE)  # 生存抑制（リスク許容）
        suppress_CORE = max(0, kappa_CORE - E_CORE)  # 勝利抑制（守り）
        
        # 【性格別の解釈フィルター】
        if self.personality == 'cautious':
            # 慎重派: BASE層の声を重視
            safety_drive = action_BASE * 2.0 - action_CORE * 0.5
            
            if safety_drive > 5.0:
                choice_value = 1.5  # 超安全
            elif safety_drive > 2.0:
                choice_value = 3.0  # 安全
            elif action_CORE > action_BASE:
                # COREがBASEを上回った（勝ちたい > 生きたい）
                choice_value = 5.0 + action_CORE * 0.5  # 5-8
            else:
                choice_value = 4.0  # デフォルト
        
        elif self.personality == 'aggressive':
            # 攻撃派: CORE層の声を重視
            attack_drive = action_CORE * 2.0 - action_BASE * 0.5
            
            if attack_drive > 10.0:
                choice_value = 10.0  # 全力攻撃
            elif attack_drive > 5.0:
                choice_value = 8.0 + attack_drive * 0.2  # 8-10
            elif action_BASE > action_CORE * 2.0:
                # BASEがCOREを圧倒（生存恐怖 >> 勝利欲求）
                choice_value = 3.0 + action_BASE * 0.3  # 3-6
            else:
                choice_value = 7.0  # デフォルト
        
        else:  # balanced
            # バランス派: UPPER層の戦略的計算を重視
            strategic_ratio = action_CORE / (action_BASE + 1.0)
            
            if strategic_ratio > 2.0:
                # CORE >> BASE → 攻めるべき
                choice_value = 6.0 + action_CORE * 0.4  # 6-10
            elif strategic_ratio < 0.5:
                # BASE >> CORE → 守るべき
                choice_value = 2.0 + action_BASE * 0.3  # 2-5
            else:
                # バランス → UPPER層の判断
                choice_value = 5.0 + action_UPPER * 0.5  # 5-7
        
        # 最終選択（1-10に丸める）
        choice = max(1, min(10, int(choice_value + 0.5)))
        
        # 【理論改善により外部制限を削除】
        # 以前: BASE κ=0.2-0.8 → HP=1時の400圧力が成長で吸収 → 外部制限が必要
        # 改善後: BASE κ=10-15（本能的死の恐怖）→ E/κから自然に創発
        # if self.hp == 1:
        #     choice = min(choice, 5)
        # elif self.hp == 2:
        #     choice = min(choice, 7)
        
        self.choice_history.append(choice)
        return choice
    
    def process_result(self, choice: int, crashed: bool, score_gained: int, 
                      current_set: int = None, current_round: int = None):
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
                # 脱落情報を記録
                if current_set is not None:
                    self.elimination_set = current_set
                if current_round is not None:
                    self.elimination_round = current_round
        else:
            self.crash_history.append(0)
        
        # SSD学習
        self._update_ssd(choice, crashed, score_gained)
    
    def _update_ssd(self, choice: int, crashed: bool, score_gained: int):
        """SSD学習（性格別の主観的解釈）
        
        roulette_ssd_pure.pyと同様の高度な主観的学習:
        - 同じ結果（crash/success）を異なる層で解釈
        - 性格別の意味圧設計
        - APEX SURVIVORの極限状況を反映（強烈な意味圧）
        - HP状態による学習圧の非線形増幅
        """
        
        crash_rate = GameConfig.CHOICES[choice]['crash_rate']
        is_high_risk = (choice >= 7)
        is_safe = (choice <= 3)
        
        # 【HP状態による学習圧の増幅率（非線形）】
        # HP=1でクラッシュ → 即死 → 圧倒的トラウマ
        # HP=2でクラッシュ → HP=1へ（即死圏突入）→ 強い恐怖
        # HP=3以上 → 通常学習
        if crashed:
            if self.hp == 0:  # クラッシュで死亡した
                hp_fear_multiplier = 5.0  # 死の記憶（最大トラウマ）
            elif self.hp == 1:  # HP=2→1（即死圏突入）
                hp_fear_multiplier = 3.0  # 「次は死」という恐怖
            elif self.hp == 2:  # HP=3→2（警戒圏突入）
                hp_fear_multiplier = 1.5  # 警戒レベル上昇
            else:
                hp_fear_multiplier = 1.0  # 通常
        else:
            hp_fear_multiplier = 1.0  # 成功時は通常
        
        # 【性格別の学習パターン】
        if self.personality == 'cautious':
            # 慎重派: クラッシュを生存層で強く学習
            if crashed:
                pressure = HumanPressure(
                    base=80.0 * hp_fear_multiplier,   # HP状態で非線形増幅（最大400）
                    core=10.0 * hp_fear_multiplier,
                    upper=5.0 * hp_fear_multiplier
                )
            elif not crashed and is_high_risk:
                pressure = HumanPressure(
                    base=-30.0,  # 「リスク取って成功」を生存層で強く評価
                    core=20.0,   # 勝利にも貢献
                    upper=10.0
                )
            else:
                pressure = HumanPressure(
                    base=-20.0,  # 安全成功を強化
                    core=8.0,
                    upper=3.0
                )
        
        elif self.personality == 'aggressive':
            # 攻撃派: 成功/失敗を勝利層で強く学習
            if crashed:
                pressure = HumanPressure(
                    base=20.0 * hp_fear_multiplier,   # HP状態で非線形増幅
                    core=60.0 * hp_fear_multiplier,   # 「勝てなかった」が強烈な圧力
                    upper=10.0 * hp_fear_multiplier
                )
            elif not crashed and is_high_risk:
                pressure = HumanPressure(
                    base=0.0,
                    core=-60.0,  # 「ハイリスクで勝った」を強く強化
                    upper=20.0
                )
            else:
                pressure = HumanPressure(
                    base=0.0,
                    core=-25.0,  # 勝利を評価
                    upper=10.0
                )
        
        else:  # balanced
            # バランス派: 戦略層で学習
            reward = score_gained / 100.0
            risk = crash_rate
            
            if crashed:
                pressure = HumanPressure(
                    base=40.0 * hp_fear_multiplier,   # HP状態で非線形増幅
                    core=35.0 * hp_fear_multiplier,
                    upper=risk * 60.0 * hp_fear_multiplier  # リスク計算を強く学習
                )
            else:
                pressure = HumanPressure(
                    base=-15.0,
                    core=-reward * 35.0,
                    upper=-risk * reward * 40.0  # リスク・リターン比を学習
                )
        
        # SSD更新
        self.agent.step(pressure, dt=1.0)
    
    def decide_hp_purchase(self) -> int:
        """HP購入判断（HP状態とスコア状況から決定）
        
        E/κバランスは行動選択で使うが、HP購入は
        「HP低い=買う価値が高い」という客観的判断
        
        注: 累計スコア(total_score)から購入
        （score == total_scoreだが、意図を明確にするためtotal_score使用）
        """
        if self.total_score < GameConfig.HP_PURCHASE_COST:
            return 0
        
        current_hp = self.hp
        max_affordable = self.total_score // GameConfig.HP_PURCHASE_COST
        max_needed = GameConfig.MAX_HP - current_hp
        max_purchasable = min(max_affordable, max_needed)
        
        if max_purchasable <= 0:
            return 0
        
        # 【HP状態ベースの購入判断】
        # HP=1: 即死圏 → 絶対に買う（2個まで）
        # HP=2: 警戒圏 → 余裕あれば買う（1-2個）
        # HP=3: 通常圏 → スコアに余裕あれば買う（1個）
        # HP=4-5: 買わない
        
        if current_hp == 1:
            # 即死圏：最優先でHP回復（2個まで）
            return min(2, max_purchasable)
        elif current_hp == 2:
            # 警戒圏：スコアに余裕あれば購入
            if self.total_score >= GameConfig.HP_PURCHASE_COST * 3:  # 60pts以上
                return min(2, max_purchasable)
            elif self.total_score >= GameConfig.HP_PURCHASE_COST * 2:  # 40pts以上
                return min(1, max_purchasable)
            else:
                return 0
        elif current_hp == 3:
            # 通常圏：大きな余裕があれば1個購入
            if self.total_score >= GameConfig.HP_PURCHASE_COST * 5:  # 100pts以上
                return min(1, max_purchasable)
            else:
                return 0
        else:
            # HP=4-5: 購入不要
            return 0
    
    def reset_set_score(self):
        """セット終了時のリセット
        
        注: APEX SURVIVORは全セット累計で競うゲーム
        セットごとのリセットは不要（HPのみ継続）
        """
        pass  # スコアはリセットしない（累計で競う）


# ===== ゲーム進行関数 =====
def play_round(players: list, round_num: int, total_rounds: int, current_set: int, total_sets: int):
    """1ラウンドの実行
    
    重要: 順位計算は**生存者のみ**で行う
    - 死者は順位から除外
    - トップが死ねば2位が新トップに
    - スコア差・逆転可能性も生存者基準で計算
    """
    alive_players = [p for p in players if p.is_alive]
    
    if len(alive_players) == 0:
        return
    
    # ラウンド開始処理
    for p in alive_players:
        p.on_round_start()
    
    # 【重要】順位計算: 生存者のみでソート
    # トップが死んだら2位が新トップ、スコア差も生存者間で計算
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
        
        # E/κ状態表示（デバッグ用）
        E_BASE = p.agent.state.E[HumanLayer.BASE.value]
        E_CORE = p.agent.state.E[HumanLayer.CORE.value]
        E_UPPER = p.agent.state.E[HumanLayer.UPPER.value]
        
        print(f"{p.name}: 選択={choice} (HP={p.hp}, Score={p.score}, Crash率={int(crash_rate*100)}%) | E: B={E_BASE:.1f} C={E_CORE:.1f} U={E_UPPER:.1f}")
        choices.append((p, choice))
    
    # 結果判定
    print(f"\n{'-'*60}")
    print(f"📊 結果")
    print(f"{'-'*60}")
    
    for p, choice in choices:
        crashed = random.random() < GameConfig.CHOICES[choice]['crash_rate']
        score_gained = 0 if crashed else GameConfig.CHOICES[choice]['score']
        
        p.process_result(choice, crashed, score_gained, current_set, round_num)
        
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
    
    # セット順位ボーナス付与
    print(f"\n{'='*60}")
    print(f"🏆 セット{set_num}結果 - 順位ボーナス")
    print(f"{'='*60}")
    
    # 【重要】生存者のみで順位計算してボーナス配布
    alive_players = [p for p in players if p.is_alive]
    sorted_players = sorted(alive_players, key=lambda x: x.score, reverse=True)
    
    for rank, p in enumerate(sorted_players, 1):
        bonus = GameConfig.SET_RANK_BONUS.get(rank, 0)
        if bonus > 0:
            p.score += bonus
            p.total_score += bonus
            print(f"{rank}位: {p.name} - セットスコア: {p.score}pts (+{bonus}pts ボーナス) | 累計: {p.total_score}pts")
        else:
            print(f"{rank}位: {p.name} - セットスコア: {p.score}pts | 累計: {p.total_score}pts")
    
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
            before_score = p.score
            p.hp += purchase
            p.score -= cost
            p.total_score -= cost
            print(f"{p.name}: HP +{purchase} (Cost={cost}pts, {before_score}pts→{p.score}pts, HP={p.hp})")
        else:
            print(f"{p.name}: 見送り (Score={p.score}pts, HP={p.hp})")
    
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
        # 生存判定と状態表示
        if rank == 1 and p.is_alive:
            status = "🏆 生存"
        else:
            if p.is_alive:
                # 最終的に生存しているが1位ではない
                status = "💀 敗北（生存）"
            elif p.elimination_set is not None:
                # 途中脱落
                status = f"💀 途中脱落（セット{p.elimination_set}-R{p.elimination_round}）"
            else:
                # 脱落（情報なし）
                status = "💀 脱落"
        
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
    
    # 真の勝者: 生存している最高得点者
    alive_players = [p for p in sorted_players if p.is_alive]
    if alive_players:
        winner = alive_players[0]
        print(f"{'='*60}")
        print(f"👑 WINNER: {winner.name}")
        print(f"{'='*60}\n")
        print(f"E/κの内部力学から行動が創発し、頂点に立った...")
    else:
        print(f"{'='*60}")
        print(f"💀 全滅: 生存者なし")
        print(f"{'='*60}\n")
        print(f"極限状況が全員を破壊した...")


def main():
    """メイン関数"""
    print("""
============================================================
🎮 APEX SURVIVOR - SSD Pure Theoretical版 v3
============================================================

v2からの根本的改善:
【構造的矛盾の解決】
- v2: strategic_mult（外部ロジック）が行動を支配
- v3: 状況→意味圧変換 → E/κから行動が創発

【理論的整合性】
1. make_choice = 状況認識を層別HumanPressureに変換
2. agent.step(pressure) = E（未処理圧）を更新
3. 選択決定 = E/κバランスから創発的に決定

「1位以外全員死亡」という極限状況で
HumanAgentの内部状態（E/κ）から
行動が完全に創発することを実証
""")
    
    # プレイヤー作成（7人）
    players = [
        ApexPlayerV3("太郎", "cautious", "red"),
        ApexPlayerV3("花子", "balanced", "green"),
        ApexPlayerV3("スミス", "balanced", "blue"),
        ApexPlayerV3("田中", "cautious", "yellow"),
        ApexPlayerV3("佐藤", "aggressive", "magenta"),
        ApexPlayerV3("鈴木", "balanced", "cyan"),
        ApexPlayerV3("高橋", "aggressive", "white")
    ]
    
    # 5セット実行
    for set_num in range(1, GameConfig.TOTAL_SETS + 1):
        play_set(players, set_num, GameConfig.TOTAL_SETS)
    
    # 最終結果
    print_final_results(players)


if __name__ == "__main__":
    main()
