"""① グラフで体験しよう

曲線の上に点 P, Q を置き、足し算の作図をアニメーションで見る画面です。

モード:
    P + Q : 2点を通る直線を使う足し算
    2P    : P での接線を使う足し算（P + P）
    kP    : P を何回も足したとき、点がどう動くか

操作:
    ・曲線の上をクリック → 点を置く（ドラッグで動かせる）
    ・スライダー         → 曲線の a, b を変える
"""

import math

import pygame

from settings import *
from ui import Scene, Button, Slider, draw_text, draw_text_block, draw_point, draw_panel, draw_dashed_line
from curve import EllipticCurve, point_text
from graph import Graph, addition_step, addition_steps_text

MAX_K = 8   # kP モードで表示する最大の k


class ExploreScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.graph = Graph(GRAPH_AREA)
        self.curve = EllipticCurve(-1.0, 1.0)
        self.mode = "add"          # "add"（P+Q） / "double"（2P） / "multiple"（kP）
        self.P = None
        self.Q = None
        self.dragging = None       # ドラッグ中の点の名前 "P" か "Q"（していなければ None）
        self.animation_time = 0.0  # 作図アニメーションの経過時間
        self.k = 5

        x = PANEL_X
        self.sliders = [
            Slider((x + 10, 190, 370, 20), "a", -4, 3, 0.1, -1.0, self.change_a),
            Slider((x + 10, 262, 370, 20), "b", -3, 3, 0.1, 1.0, self.change_b),
        ]
        self.mode_buttons = [
            Button((x, 96, 125, 44), "P + Q", self.set_mode, "add", size=16),
            Button((x + 132, 96, 125, 44), "2P = P+P", self.set_mode, "double", size=16),
            Button((x + 264, 96, 125, 44), "kP 何回も", self.set_mode, "multiple", size=16),
        ]
        self.k_buttons = [
            Button((x + 250, 560, 50, 40), "−", self.change_k, -1),
            Button((x + 310, 560, 50, 40), "＋", self.change_k, +1),
        ]
        self.buttons = self.mode_buttons + [
            Button((x, 680, 190, 48), "点をリセット", self.reset_points, size=18),
            Button((x + 200, 680, 190, 48), "タイトルへ", app.goto, "title", size=18),
        ]
        self.place_first_points()

    # ─── 状態を変える処理 ───

    def set_mode(self, mode):
        self.mode = mode
        if mode == "add" and self.P is not None and self.Q is None:
            self.place_first_points()
        self.animation_time = 0.0

    def change_k(self, amount):
        self.k = max(2, min(MAX_K, self.k + amount))
        self.animation_time = 0.0

    def change_a(self, value):
        self.change_curve(EllipticCurve(value, self.curve.b))

    def change_b(self, value):
        self.change_curve(EllipticCurve(self.curve.a, value))

    def change_curve(self, new_curve):
        """曲線の形が変わったら、点も新しい曲線の上へ移す（同じ x のまま y を計算しなおす）"""
        self.curve = new_curve
        if self.P is not None:
            self.P = self.move_onto_curve(self.P)
        if self.Q is not None:
            self.Q = self.move_onto_curve(self.Q)
        self.animation_time = 10.0   # アニメーションは最後の状態で表示

    def move_onto_curve(self, point):
        x, y = point
        new_y = self.curve.y_at(x, 1 if y >= 0 else -1)
        if new_y is None:
            return None     # その x では曲線がなくなった
        return (x, new_y)

    def reset_points(self):
        self.P = None
        self.Q = None
        self.animation_time = 0.0

    def place_first_points(self):
        """最初に見せる P, Q を、曲線の左寄りと右寄りに置く"""
        points = [p for p in self.graph.points_on_curve(self.curve, 40) if p[1] > 0]
        if not points:
            return
        if self.P is None:
            self.P = min(points, key=lambda p: abs(p[0] + 0.8))   # x = -0.8 に一番近い点
        self.Q = min(points, key=lambda p: abs(p[0] - 1.0))       # x = 1.0 に一番近い点
        self.animation_time = 0.0

    def nearest_curve_point(self, mouse_position, max_distance=60):
        """マウスに一番近い曲線上の点（遠すぎるときは None）"""
        best = None
        best_distance = max_distance
        for point in self.graph.points_on_curve(self.curve):
            distance = math.dist(self.graph.to_screen(point), mouse_position)
            if distance < best_distance:
                best = point
                best_distance = distance
        return best

    # ─── 入力 ───

    def handle_event(self, event):
        if super().handle_event(event):
            return True
        if self.mode == "multiple":
            for button in self.k_buttons:
                if button.handle_event(event):
                    return True
        for slider in self.sliders:
            if slider.handle_event(event):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.graph.rect.collidepoint(event.pos):
            self.on_graph_click(event.pos)
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            point = self.nearest_curve_point(event.pos, 120)
            if point is not None:
                setattr(self, self.dragging, point)    # self.P か self.Q を書きかえる
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = None
            self.animation_time = 0.0                   # 指を離したらアニメーションを最初から
            return True
        return False

    def on_graph_click(self, mouse_position):
        names = ["P", "Q"] if self.mode == "add" else ["P"]

        # すでにある点の近くをクリック → その点をつかむ
        for name in names:
            point = getattr(self, name)
            if point is not None and math.dist(self.graph.to_screen(point), mouse_position) < 20:
                self.dragging = name
                return

        new_point = self.nearest_curve_point(mouse_position)
        if new_point is None:
            return
        # 置く点を決める: P がなければ P、次に Q、両方あればクリックに近いほうを動かす
        if self.P is None:
            target = "P"
        elif self.mode == "add" and self.Q is None:
            target = "Q"
        elif self.mode == "add":
            dist_p = math.dist(self.graph.to_screen(self.P), mouse_position)
            dist_q = math.dist(self.graph.to_screen(self.Q), mouse_position)
            target = "P" if dist_p < dist_q else "Q"
        else:
            target = "P"
        setattr(self, target, new_point)
        self.dragging = target

    def update(self, dt):
        if self.dragging:
            self.animation_time = 10.0   # ドラッグ中は作図の完成形を見せる
        else:
            self.animation_time += dt

    # ─── 描画 ───

    def current_addition(self):
        """いま表示する足し算の結果（点が足りないときなどは None）"""
        if self.curve.is_singular() or self.P is None:
            return None
        if self.mode == "add" and self.Q is not None:
            return self.curve.add(self.P, self.Q)
        if self.mode == "double":
            return self.curve.add(self.P, self.P)
        return None

    def draw(self, screen):
        screen.fill(BACKGROUND)
        self.draw_header(screen, "① グラフで体験しよう",
                         "曲線上をクリック・ドラッグして点を動かそう。スライダーで曲線の形も変えられます。")
        self.graph.draw_background(screen)
        self.graph.draw_curve(screen, self.curve)

        if self.curve.is_singular():
            draw_text(screen, "特異曲線（とがった点や交差がある）なので楕円曲線ではありません",
                      (self.graph.rect.centerx, self.graph.rect.bottom - 30), 18, BAD, True, "center")

        addition = self.current_addition()
        if addition is not None:
            label = "P+Q" if self.mode == "add" else "2P"
            self.graph.draw_addition(screen, self.P, addition, self.animation_time, label)
            if addition.result is not None and not self.graph.is_visible(addition.result) \
                    and self.animation_time > 2.2:
                draw_text(screen, f"答えの点は画面の外: {point_text(addition.result)}",
                          (self.graph.rect.centerx, self.graph.rect.bottom - 30), 18,
                          COLOR_ANSWER, True, "center")
        if self.mode == "multiple" and self.P is not None and not self.curve.is_singular():
            self.draw_multiples(screen)

        if self.P is not None:
            draw_point(screen, self.graph.to_screen(self.P), COLOR_P, 8, "P")
        if self.Q is not None and self.mode == "add":
            draw_point(screen, self.graph.to_screen(self.Q), COLOR_Q, 8, "Q")

        self.draw_side_panel(screen, addition)

    def draw_multiples(self, screen):
        """P, 2P, 3P, ... を 0.45 秒ごとに1つずつ表示する"""
        points = self.curve.multiples(self.P, self.k)
        shown = min(len(points), int(self.animation_time / 0.45) + 1)
        for i in range(1, shown):
            previous, point = points[i - 1], points[i]
            if previous is not None and point is not None:
                screen.set_clip(self.graph.rect)
                draw_dashed_line(screen, (110, 110, 160), self.graph.to_screen(previous),
                                 self.graph.to_screen(point), 1)
                screen.set_clip(None)
            if point is not None and self.graph.is_visible(point):
                color = COLOR_ANSWER if i == shown - 1 else (90, 170, 120)
                draw_point(screen, self.graph.to_screen(point), color, 7, f"{i + 1}P", 16)
        self.shown_multiples = points[:shown]

    def draw_side_panel(self, screen, addition):
        x = PANEL_X
        draw_panel(screen, (x - 15, 85, 425, 580))
        for button in self.mode_buttons:
            button.color = ACCENT if button.value == self.mode else BUTTON
        self.draw_buttons(screen)
        for slider in self.sliders:
            slider.draw(screen)
        y = 300

        if self.mode == "multiple":
            draw_text_block(screen,
                            "P を何回も足していくと（P, 2P, 3P, …）点は曲線上をあちこちへ飛び回ります。"
                            "kP は簡単に計算できても、kP から k を当てるのはとても難しい。"
                            "これが暗号の鍵になります（③ 暗号クイズで体験できます）。",
                            (x, y), PANEL_WIDTH, 16, TEXT_SUB)
            draw_text(screen, f"k = {self.k}", (x + 10, 568), 24, TEXT, True)
            for button in self.k_buttons:
                button.draw(screen)
            if self.P is None:
                draw_text(screen, "曲線をクリックして P を置こう", (x + 10, 420), 18, COLOR_P, True)
                return
            y = 420
            for i, point in enumerate(getattr(self, "shown_multiples", []), 1):
                draw_text(screen, f"{i:>2}P = {point_text(point)}", (x + 10, y), 15,
                          COLOR_P if i == 1 else COLOR_ANSWER)
                y += 17
            return

        if self.P is None or (self.mode == "add" and self.Q is None):
            missing = "P" if self.P is None else "Q"
            draw_text_block(screen, f"曲線の上をクリックして点 {missing} を置こう", (x, y), PANEL_WIDTH, 20, COLOR_P, True)
            return
        if addition is None:
            return

        # 作図の手順（今の段階を明るく表示）
        line_name = "P と Q を通る直線" if (self.mode == "add" and not addition.is_tangent) \
            else "P での接線（曲線にふれる直線）"
        step = addition_step(self.animation_time)
        for i, line in enumerate(addition_steps_text(addition, line_name)):
            if i == step:
                pygame.draw.rect(screen, (50, 58, 100), (x - 4, y - 4, 400, 30), border_radius=8)
            draw_text(screen, line, (x, y), 17, TEXT if i <= step else TEXT_DIM, i == step)
            y += 34

        y += 6
        draw_text(screen, f"P = {point_text(self.P)}", (x, y), 18, COLOR_P)
        if self.mode == "add":
            draw_text(screen, f"Q = {point_text(self.Q)}", (x, y + 26), 18, COLOR_Q)
        name = "P + Q" if self.mode == "add" else "2P"
        draw_text(screen, f"{name} = {point_text(addition.result)}", (x, y + 52), 18, COLOR_ANSWER, True)

        if self.mode == "add":
            tip = "試してみよう: Q を P の真上・真下に置くと？ P と Q を入れかえても答えは同じ？"
        else:
            tip = "試してみよう: P を x 軸の上（y = 0）に置くと？"
        draw_text_block(screen, tip, (x, y + 90), PANEL_WIDTH, 15, TEXT_SUB)
