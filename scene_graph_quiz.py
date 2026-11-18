"""② グラフクイズ

曲線上の点 P, Q が示され、答えの点を候補 A〜D から選ぶクイズです（全10問）。

問題の種類:
    add     : P + Q はどれ？
    double  : 2P（= P + P）はどれ？
    neg     : −P（P の逆元）はどれ？
    inverse : P + Q はどれ？（Q が P の真下にある → 答えは O）

得点:
    基本点 100（ヒントを使うと 50）＋ スピードボーナス（20秒以内なら残り秒数×3）
    連続正解すると「コンボ倍率」がかかる（1.0, 1.2, 1.4, ... 最大 2.0 倍）
"""

import math
import random
import time

import pygame

from settings import *
from ui import Scene, Button, draw_text, draw_text_block, draw_point, draw_panel, draw_glow, draw_dashed_line, smooth
from curve import EllipticCurve
from graph import Graph, addition_step, addition_steps_text

QUESTION_COUNT = 10
LETTERS = "ABCD"

# 出題に使う曲線 (a, b)。どれもグラフの範囲にきれいに収まるもの
QUIZ_CURVES = [(-1, 1), (-2, 2), (-1, 0), (0, 1), (-3, 3), (-2, 1), (1, 1), (-4, 3), (0, 2)]

# 問題の種類（同じものを複数書くと、その種類が出やすくなる）
KINDS = ["add", "add", "add", "double", "double", "neg", "inverse"]

QUESTION_TEXT = {
    "add": "P + Q はどれ？",
    "double": "2P（= P + P）はどれ？",
    "neg": "−P（P の逆元）はどれ？",
    "inverse": "P + Q はどれ？",
}
GUIDE_TEXT = {
    "add": "P と Q を「足した」点を探そう。",
    "double": "P に P 自身を「足した」点を探そう。",
    "neg": "足すと O（無限遠点）になる相手、つまり P の逆元を探そう。",
    "inverse": "Q は P の真下（または真上）にあります。P と Q を通る直線を想像してみよう。",
}
EXPLANATION = {
    "add": "P と Q を通る直線は、曲線ともう1点（★）で交わります。★ を上下にひっくり返した点が P + Q です。",
    "double": "P + P のときは、P で曲線にふれる「接線」を使います。接線と曲線の交点 ★ を上下反転した点が 2P です。",
    "neg": "−P は P を上下にひっくり返した（x 軸で折り返した）点です。P + (−P) を計算すると O（無限遠点）になります。",
    "inverse": "Q = −P なので、P と Q を通る直線は真っすぐ縦。3つ目の交点がないので、答えは「無限遠点 O」。"
               "O は足し算の「0」の役割をする特別な点です。",
}


class GraphQuestion:
    """1問分のデータ"""

    def __init__(self, kind, curve, P, Q, addition, choices, answer_index):
        self.kind = kind                  # 問題の種類
        self.curve = curve                # 曲線
        self.P = P
        self.Q = Q                        # neg の問題では、Q は答え（−P）を表す
        self.addition = addition          # 足し算の結果（作図用）
        self.choices = choices            # 選択肢の点のリスト（O は None）
        self.answer_index = answer_index  # 正解は choices の何番目か


def make_question(graph):
    """ランダムに1問つくる（条件に合わなければ、合うまで作り直す）"""
    while True:
        a, b = random.choice(QUIZ_CURVES)
        curve = EllipticCurve(a, b)
        points = graph.points_on_curve(curve, 40)
        question = try_make_question(random.choice(KINDS), curve, points, graph)
        if question is not None:
            return question


def try_make_question(kind, curve, points, graph):
    """1問つくってみる。見づらい問題（点が重なる、画面からはみ出す等）になったら None を返す"""
    P = random.choice(points)
    Q = None

    if kind == "add":
        Q = random.choice(points)
        if graph.pixel_distance(P, Q) < 90:
            return None
        addition = curve.add(P, Q)
    elif kind == "double":
        if graph.pixel_distance(P, (P[0], 0)) < 25:    # x 軸に近すぎる点はさける
            return None
        addition = curve.add(P, P)
    else:  # "neg" と "inverse": Q は P を上下反転した点
        Q = (P[0], -P[1])
        if graph.pixel_distance(P, Q) < 80:
            return None
        addition = curve.add(P, Q)

    # 正解と、最初に入れておく選択肢
    if kind in ("add", "double"):
        if addition.is_vertical:
            return None
        if not graph.is_visible(addition.result, 25) or not graph.is_visible(addition.third, 25):
            return None
        answer = addition.result
        choices = [addition.result, addition.third]    # ★ は「ひっかけ」の選択肢
    elif kind == "neg":
        answer = Q
        choices = [Q]
    else:
        answer = None                                   # 答えは O
        choices = []

    # 残りの選択肢を、曲線上のランダムな点でうめる
    if kind == "neg" or Q is None:
        given_points = [P]      # neg の Q は答えそのものなので、よける対象にしない
    else:
        given_points = [P, Q]
    needed = 3 if kind == "inverse" else 4
    for _ in range(300):
        if len(choices) >= needed:
            break
        candidate = random.choice(points)
        far_from_choices = all(graph.pixel_distance(candidate, c) > 60 for c in choices)
        far_from_given = all(graph.pixel_distance(candidate, g) > 50 for g in given_points)
        if far_from_choices and far_from_given:
            choices.append(candidate)
    if len(choices) < needed:
        return None
    # 正解や ★ が P, Q と重なって見づらい問題はやめる
    for choice in choices:
        if any(graph.pixel_distance(choice, g) < 40 for g in given_points):
            return None

    random.shuffle(choices)
    if kind == "inverse":
        choices.append(None)    # 4番目の選択肢は「O（無限遠点）」
    return GraphQuestion(kind, curve, P, Q, addition, choices, choices.index(answer))


class GraphQuizScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.graph = Graph(GRAPH_AREA)
        self.question_number = 0
        self.score = 0
        self.correct_count = 0
        self.combo = 0
        self.next_question()

    # ─── 進行 ───

    def next_question(self):
        if self.question_number == QUESTION_COUNT:
            stars = "★" * (self.correct_count // 2) + "☆" * (5 - self.correct_count // 2)
            self.app.goto("result", mode="graph_quiz", score=self.score,
                          detail=f"{self.correct_count}/{QUESTION_COUNT}問",
                          lines=[f"{self.correct_count} / {QUESTION_COUNT} 問正解", stars])
            return
        self.question_number += 1
        self.question = make_question(self.graph)
        self.phase = "question"     # "question"（解答中） → "answer"（答え合わせ）
        self.used_hint = False
        self.chosen = None          # 選んだ選択肢の番号
        self.time = 0.0             # アニメーション用の時間
        self.start_time = time.monotonic()
        self.message = ""
        self.make_buttons()

    def make_buttons(self):
        x = PANEL_X
        self.buttons = [Button((x + 200, 680, 190, 48), "タイトルへ", self.app.goto, "title", size=18)]
        if self.phase == "question":
            for i, choice in enumerate(self.question.choices):
                if choice is None:   # 「O」の選択肢は横長のボタン
                    area, label = (x, 476, 390, 48), f"{LETTERS[i]}: O（無限遠点）"
                else:
                    area, label = (x + i * 100, 420, 90, 48), LETTERS[i]
                self.buttons.append(Button(area, label, self.answer, i, key=pygame.K_a + i))
            if self.question.kind != "neg":
                self.buttons.append(Button((x, 540, 390, 46), "ヒント：直線を表示（得点半分）",
                                           self.show_hint, size=18, key=pygame.K_h))
        else:
            label = "次の問題へ" if self.question_number < QUESTION_COUNT else "結果を見る"
            self.buttons.append(Button((x, 610, 390, 54), label, self.next_question,
                                       color=ACCENT, key=pygame.K_RETURN))

    def show_hint(self):
        self.used_hint = True
        self.time = 0.0

    def answer(self, index):
        if self.phase != "question":
            return
        self.chosen = index
        question = self.question
        if index == question.answer_index:
            self.combo += 1
            self.correct_count += 1
            base = 50 if self.used_hint else 100
            seconds = time.monotonic() - self.start_time
            speed_bonus = max(0, int(20 - seconds)) * 3
            combo_rate = min(1 + 0.2 * (self.combo - 1), 2.0)
            gained = int((base + speed_bonus) * combo_rate)
            self.score += gained
            self.message = f"正解！ +{gained}点"
        else:
            self.combo = 0
            picked = question.choices[index]
            picked_star = not question.addition.is_vertical and picked == question.addition.third
            if picked_star:
                self.message = "おしい！それは ★（3つ目の交点）。最後にひっくり返そう"
            else:
                self.message = "ざんねん…"
        self.phase = "answer"
        self.time = 0.0
        self.make_buttons()

    # ─── 入力・時間 ───

    def handle_event(self, event):
        if super().handle_event(event):
            return True
        # グラフ上の候補の丸を直接クリックしても答えられる
        if self.phase == "question" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, choice in enumerate(self.question.choices):
                if choice is not None and math.dist(self.graph.to_screen(choice), event.pos) < 22:
                    self.answer(i)
                    return True
        return False

    def update(self, dt):
        self.time += dt

    # ─── 描画 ───

    def draw(self, screen):
        screen.fill(BACKGROUND)
        question = self.question
        graph = self.graph
        self.draw_header(screen, f"② グラフクイズ　第 {self.question_number}/{QUESTION_COUNT} 問",
                         "答えだと思う点（A〜D）をクリック。キーボードの A〜D でも答えられます。")
        draw_text(screen, f"SCORE {self.score}", (SCREEN_WIDTH - 40, 22), 28, COLOR_P, True, "topright")
        if self.combo >= 2:
            draw_text(screen, f"{self.combo} COMBO!", (SCREEN_WIDTH - 40, 58), 18, COLOR_Q, True, "topright")

        graph.draw_background(screen)
        graph.draw_curve(screen, question.curve)

        if self.phase == "question" and self.used_hint:
            graph.draw_addition(screen, question.P, question.addition, min(self.time, 1.2))
        if self.phase == "answer":
            self.draw_solution(screen)

        self.draw_choices(screen)
        draw_point(screen, graph.to_screen(question.P), COLOR_P, 8, "P")
        if question.Q is not None and question.kind != "neg":
            draw_point(screen, graph.to_screen(question.Q), COLOR_Q, 8, "Q")
        self.draw_side_panel(screen)

    def draw_choices(self, screen):
        """候補 A〜D の丸"""
        for i, choice in enumerate(self.question.choices):
            if choice is None:
                continue
            position = self.graph.to_screen(choice)
            color = (200, 200, 230)
            if self.phase == "answer":
                if i == self.question.answer_index:
                    color = GOOD
                elif i == self.chosen:
                    color = BAD
                else:
                    color = (110, 110, 140)
            elif math.dist(position, pygame.mouse.get_pos()) < 22:
                draw_glow(screen, WHITE, position, 20, 60)
            pygame.draw.circle(screen, (10, 10, 20), position, 15)
            pygame.draw.circle(screen, color, position, 15, 3)
            draw_text(screen, LETTERS[i], position, 17, color, True, "center")

    def draw_solution(self, screen):
        """答え合わせの作図アニメーション"""
        question = self.question
        if question.kind == "neg":
            # P から −P へ点線を伸ばす
            start = self.graph.to_screen(question.P)
            end = self.graph.to_screen(question.Q)
            move = smooth(self.time / 0.8)
            draw_dashed_line(screen, WHITE, start, (end[0], start[1] + (end[1] - start[1]) * move))
            if move >= 1:
                draw_point(screen, end, COLOR_ANSWER, 9, "−P")
        else:
            label = "2P" if question.kind == "double" else "P+Q"
            self.graph.draw_addition(screen, question.P, question.addition, self.time, label)

    def draw_side_panel(self, screen):
        question = self.question
        x = PANEL_X
        draw_panel(screen, (x - 15, 90, 425, 575))
        draw_text(screen, QUESTION_TEXT[question.kind], (x, 110), 28, TEXT, True)
        y = 160

        if self.phase == "question":
            y = draw_text_block(screen, GUIDE_TEXT[question.kind], (x, y), PANEL_WIDTH - 10, 18, TEXT_SUB)
            draw_text_block(screen, "ルール: ① 2点を通る直線を引く → ② 曲線との3つ目の交点を探す → "
                                    "③ それを上下にひっくり返す", (x, y + 10), PANEL_WIDTH - 10, 17, COLOR_P)
            if self.used_hint:
                draw_text(screen, "ヒント表示中（得点半分）", (x, 596), 16, COLOR_LINE)
        else:
            color = GOOD if self.chosen == question.answer_index else BAD
            draw_text_block(screen, self.message, (x, y), PANEL_WIDTH - 10, 24, color, True)
            y = draw_text_block(screen, EXPLANATION[question.kind], (x, y + 70), PANEL_WIDTH - 10, 18, TEXT, line_gap=8)
            if question.kind != "neg":
                line_name = "P での接線" if question.kind == "double" else "P と Q を通る直線"
                step = addition_step(self.time)
                y += 10
                for i, line in enumerate(addition_steps_text(question.addition, line_name)):
                    draw_text(screen, line, (x, y), 16, TEXT if i <= step else TEXT_DIM, i == step)
                    y += 24
        self.draw_buttons(screen)
