"""③ 暗号クイズ：秘密の数 k を見破れ

点 P と、P を k 回足した点 Q（= kP）が示されます。k はいくつ？ というクイズです（全5問）。

暗号とのつながり:
    楕円曲線暗号では、k が「秘密鍵」、Q = kP が「公開鍵」です。
    P と Q は誰でも見られますが、そこから k を求めるのはとても難しい。
    これがこのクイズで体験できることです。

ヒント（総当たり）:
    ボタンを押すたびに 2P, 3P, 4P, ... と1つずつ計算して見せます。
    Q と重なれば k が分かりますが、1回押すごとに得点が 15 点減ります（最低 10 点）。
    これは、暗号を破るために k を 1 から順に全部試す「総当たり攻撃」と同じです。

得点:
    正解すると「100 − 15 × ヒントの回数」点（最低 10 点）。不正解は 0 点。
"""

import math
import random

import pygame

from settings import *
from ui import Scene, Button, draw_text, draw_text_block, draw_point, draw_panel, draw_glow, draw_dashed_line
from curve import EllipticCurve
from graph import Graph
from special_points import SPECIAL_POINTS

# 何問目でどの位数の点を使うか（後の問題ほど位数が大きく、k の候補が増えて難しい）
ORDER_RANGE_OF_QUESTION = [(5, 6), (6, 7), (7, 8), (8, 9), (9, 10)]
QUESTION_COUNT = len(ORDER_RANGE_OF_QUESTION)

FULL_SCORE = 100     # ヒントなしで正解したときの得点
HINT_COST = 15       # ヒント1回で減る得点
MIN_SCORE = 10       # 正解したときの最低点
ANSWER_CHOICES = [2, 3, 4, 5, 6, 7, 8, 9]   # 答えのボタン
MAX_HINT_K = 9       # ヒントで何倍まで計算して見せるか

TRIVIA = [
    "本物の楕円曲線暗号では、k は 77 けたほどの巨大な数です。1秒に1兆回足し算できても、"
    "総当たりで k を見つけるには宇宙の年齢よりはるかに長い時間がかかります。",
    "ビットコインの電子署名には y² = x³ + 7 という楕円曲線が使われています（mod p の世界で）。",
    "ブラウザのアドレス欄の鍵マーク（HTTPS）の通信でも、楕円曲線を使った鍵の交換（ECDH）が毎日使われています。",
    "暗号で使うのは実数ではなく「素数 p で割った余り」の世界の楕円曲線です。点がバラバラに散らばるので、"
    "このクイズのようにグラフから k を推理することもできません。",
    "kP の計算には「2倍をくり返す」近道があります（ダブル・アンド・アッド法）。k が 77 けたでも"
    "数百回の計算で済みますが、Q から k へ逆にたどる近道は見つかっていません。",
    "このクイズの点のように、有理数の座標を持つ点が O に戻るまでの回数（位数）は、"
    "1〜10 と 12 のどれかしかないことが証明されています（メイザーの定理）。",
]


class CryptoQuizScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.graph = Graph(GRAPH_AREA)
        self.question_number = 0
        self.total_score = 0
        self.correct_count = 0
        self.total_hints = 0
        self.next_question()

    # ═════════ 問題をつくる ═════════

    def next_question(self):
        if self.question_number == QUESTION_COUNT:
            self.app.goto("result", mode="crypto_quiz", score=self.total_score,
                          detail=f"{self.correct_count}/{QUESTION_COUNT}問",
                          lines=[f"{self.correct_count} / {QUESTION_COUNT} 問正解",
                                 f"総当たりの計算回数: 合計 {self.total_hints} 回"])
            return
        low, high = ORDER_RANGE_OF_QUESTION[self.question_number]
        self.question_number += 1

        # ① 位数が範囲内の「特別な点」を1つ選ぶ
        candidates = [data for data in SPECIAL_POINTS if low <= data["order"] <= high]
        data = random.choice(candidates)
        self.curve = EllipticCurve(data["a"], data["b"])
        self.order = data["order"]

        # ② 出発点 P を決める。元の点を m 倍した点を使うと、毎回ちがう問題になる。
        #    （m と位数が「互いに素」なら、P の位数も変わらない）
        usable_m = [m for m in range(1, self.order) if math.gcd(m, self.order) == 1]
        m = random.choice(usable_m)
        self.P = self.curve.multiples(data["point"], m)[-1]

        # ③ 秘密の数 k を決めて、Q = kP を計算する
        self.k = random.randint(2, min(MAX_HINT_K, self.order - 1))
        self.chain = self.curve.multiples(self.P, self.order)   # [P, 2P, ..., (位数)P = O]
        self.Q = self.chain[self.k - 1]

        # ④ すべての点が見えるようにグラフの範囲を合わせる（最後の O は除く）
        self.graph.fit(self.chain[:-1], self.curve)

        self.shown = 1               # 何倍まで計算して見せたか（1 なら P だけ）
        self.phase = "question"      # "question"（解答中） → "answer"（答え合わせ）
        self.animation_time = 10.0   # 作図アニメーションの経過時間
        self.make_buttons()

    def make_buttons(self):
        x = PANEL_X
        self.buttons = [Button((x + 200, 680, 190, 48), "タイトルへ", self.app.goto, "title", size=18)]
        if self.phase == "question":
            can_hint = self.shown < min(MAX_HINT_K, self.order)
            self.hint_button = Button((x, 300, 390, 60), "総当たりで次を計算する", self.use_hint,
                                      size=20, sub_label=f"−{HINT_COST}点　いま {self.shown}P まで計算済み",
                                      key=pygame.K_h, enabled=can_hint)
            self.buttons.append(self.hint_button)
            for i, k in enumerate(ANSWER_CHOICES):
                area = (x + (i % 4) * 100, 470 + (i // 4) * 62, 90, 52)
                self.buttons.append(Button(area, str(k), self.answer, k, size=24, key=pygame.K_0 + k))
        else:
            label = "次の問題へ" if self.question_number < QUESTION_COUNT else "結果を見る"
            self.buttons.append(Button((x, 610, 390, 54), label, self.next_question,
                                       color=ACCENT, key=pygame.K_RETURN))

    # ═════════ 操作 ═════════

    def current_score(self):
        """今このまま正解したときにもらえる得点"""
        return max(MIN_SCORE, FULL_SCORE - HINT_COST * (self.shown - 1))

    def use_hint(self):
        """次の倍数を1つ計算して見せる"""
        self.shown += 1
        self.total_hints += 1
        self.animation_time = 0.0
        self.make_buttons()

    def answer(self, k):
        if self.phase != "question":
            return
        self.is_correct = (k == self.k)
        if self.is_correct:
            self.gained = self.current_score()
            self.total_score += self.gained
            self.correct_count += 1
        else:
            self.gained = 0
        self.answered_k = k
        self.trivia = random.choice(TRIVIA)
        self.phase = "answer"
        self.make_buttons()

    def update(self, dt):
        self.animation_time += dt

    # ═════════ 描画 ═════════

    def label_of(self, m):
        """m 倍の点につける名前。Q と同じ点なら「= Q」も付ける"""
        return f"{m}P = Q" if m == self.k else f"{m}P"

    def draw(self, screen):
        screen.fill(BACKGROUND)
        self.draw_header(screen, f"③ 暗号クイズ　第 {self.question_number}/{QUESTION_COUNT} 問",
                         "Q は P を何倍した点？ ヒントを使うと分かりやすくなるけれど、得点は下がります。")
        draw_text(screen, f"SCORE {self.total_score}", (SCREEN_WIDTH - 40, 22), 28, COLOR_P, True, "topright")

        self.graph.draw_background(screen)
        self.graph.draw_curve(screen, self.curve)

        # Q（公開鍵）を先に描く。あとで kP が重なると「= Q」の名前で上書きされる
        q_position = self.graph.to_screen(self.Q)
        draw_glow(screen, COLOR_Q, q_position, 20, 70)
        q_found = self.phase == "answer" or self.shown > self.k or \
            (self.shown == self.k and self.animation_time > 2.2)
        draw_point(screen, q_position, COLOR_Q, 9, None if q_found else "Q = kP")

        if self.phase == "question":
            self.draw_hint_points(screen)
        else:
            self.draw_whole_cycle(screen)

        draw_point(screen, self.graph.to_screen(self.P), COLOR_P, 8, "P")
        self.draw_side_panel(screen)

    def draw_hint_points(self, screen):
        """ヒントで計算した 2P, 3P, ... を描く。最後の1つは作図アニメーションつき"""
        for m in range(2, self.shown):
            point = self.chain[m - 1]
            if point is not None:
                draw_point(screen, self.graph.to_screen(point), (90, 170, 120), 7, self.label_of(m), 16)
        if self.shown >= 2:
            previous = self.chain[self.shown - 2]          # (shown − 1)P
            addition = self.curve.add(previous, self.P)    # (shown − 1)P + P = shown・P
            self.graph.draw_addition(screen, previous, addition, self.animation_time,
                                     self.label_of(self.shown))

    def draw_whole_cycle(self, screen):
        """答え合わせ: P, 2P, 3P, ... を点線でつないで、一周して O に戻る様子を見せる"""
        points = self.chain[:-1]    # 最後の O を除く
        screen.set_clip(self.graph.rect)
        for start, end in zip(points, points[1:]):
            draw_dashed_line(screen, (120, 120, 170), self.graph.to_screen(start), self.graph.to_screen(end), 1)
        screen.set_clip(None)
        for m, point in enumerate(points, 1):
            if m >= 2:
                color = COLOR_ANSWER if m == self.k else (90, 170, 120)
                draw_point(screen, self.graph.to_screen(point), color, 8 if m == self.k else 6,
                           self.label_of(m), 18 if m == self.k else 15)
        draw_text(screen, f"{self.order}P = O（無限遠点）→ また P にもどる", (self.graph.rect.centerx, self.graph.rect.bottom - 34),
                  18, COLOR_ANSWER, True, "center")

    def hint_message(self):
        """ヒントを使ったあとに表示する一言"""
        if self.shown == 1:
            return "まだ何も計算していません。図から推理するか、総当たりで計算しよう。"
        if self.animation_time < 2.2:
            return f"{self.shown}P を計算中…（{self.shown - 1}P と P を通る直線 → ★ → 反転）"
        if self.chain[self.shown - 1] is None:
            return f"{self.shown}P = O に戻ってしまった！ Q はもう通り過ぎています。"
        if self.shown == self.k:
            return f"{self.shown}P が Q と重なった！"
        if self.shown > self.k:
            return f"{self.shown}P まで計算しました（Q はもう見つかっています）。"
        return f"{self.shown}P を計算した。まだ Q ではない…"

    def draw_side_panel(self, screen):
        x = PANEL_X
        width = PANEL_WIDTH - 10
        draw_panel(screen, (x - 15, 90, 425, 575))
        draw_text(screen, "秘密の数 k を見破れ！", (x, 106), 26, TEXT, True)

        if self.phase == "question":
            y = draw_text_block(screen, "Q は、P を k 回足した点です（Q = kP）。k はいくつ？",
                                (x, 148), width, 18, TEXT)
            draw_text_block(screen, "暗号では P と Q は公開され、k は「秘密鍵」。k を当てられたら暗号は破られます。",
                            (x, y + 4), width, 15, TEXT_SUB)
            draw_text(screen, "この問題の得点", (x, 262), 17, TEXT_SUB)
            draw_text(screen, f"{self.current_score()} 点", (x + 380, 254), 30, COLOR_P, True, "topright")
            draw_text_block(screen, self.hint_message(), (x, 372), width, 16, COLOR_LINE)
            draw_text(screen, "k = ?  （答えをクリック、または数字キー）", (x, 440), 17, TEXT, True)
        else:
            if self.is_correct:
                draw_text(screen, f"正解！ +{self.gained}点", (x, 150), 28, GOOD, True)
            else:
                draw_text(screen, f"ざんねん…（k = {self.answered_k} ではない）", (x, 150), 22, BAD, True)
            y = 196
            draw_text(screen, f"答え: k = {self.k}（Q = {self.k}P）", (x, y), 22, COLOR_ANSWER, True)
            y = draw_text_block(screen,
                                f"P を足し続けると {self.order} 回で O に戻り、同じ点をぐるぐる回ります"
                                f"（P の「位数」は {self.order}）。",
                                (x, y + 40), width, 16, TEXT)
            if self.k == self.order - 1:
                y = draw_text_block(screen, f"気づいた？ Q は P の真上か真下（Q = −P）。"
                                            f"−P は {self.order - 1}P と同じなので k = 位数 − 1 です。",
                                    (x, y + 6), width, 16, COLOR_P)
            y += 14
            box_top = y
            pygame.draw.rect(screen, (40, 46, 82), (x - 6, box_top - 6, 402, 200), border_radius=10)
            draw_text(screen, "豆知識", (x, y), 16, ACCENT, True)
            draw_text_block(screen, self.trivia, (x, y + 26), width - 10, 16, TEXT)
        self.draw_buttons(screen)
