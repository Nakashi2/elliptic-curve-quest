"""タイトル画面

背景では楕円曲線がゆっくり形を変え、その上を3つの点が走ります。
右側のボタンから各モードへ進みます。
"""

import math

import pygame

from settings import *
from ui import Scene, Button, draw_text, draw_text_block, draw_point, draw_glow
from curve import EllipticCurve
from graph import Graph


class TitleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.time = 0.0
        self.background_graph = Graph((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (-4.5, 6.5), (-6, 6))

        # 大きなボタン（上から順に、おすすめの遊ぶ順番）
        menu = [
            ("① グラフで体験しよう", "まずはここから：点の「足し算」を目で見る", "explore"),
            ("② グラフクイズ", "答えの点をクリックで当てよう", "graph_quiz"),
            ("③ 暗号クイズ：秘密の数 k を見破れ", "P を何倍したら Q になる？ 暗号のしくみを体験", "crypto_quiz"),
        ]
        for i, (label, sub_label, scene_name) in enumerate(menu):
            area = (700, 190 + i * 86, 520, 74)
            self.buttons.append(Button(area, label, app.goto, scene_name, size=23, sub_label=sub_label))

        # 小さなボタン
        y = 190 + 3 * 86 + 14
        self.buttons.append(Button((700, y, 166, 54), "ガイド", app.goto, "guide", size=20))
        self.buttons.append(Button((877, y, 166, 54), "ハイスコア", app.goto, "scores", size=20))
        self.buttons.append(Button((1054, y, 166, 54), "終了", app.quit, size=20))

    def handle_event(self, event):
        # タイトル画面で Esc を押したらゲームを終了する
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.quit()
            return True
        return super().handle_event(event)

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        screen.fill(BACKGROUND)

        # 背景: 時間とともに a, b が変わり、曲線の形がゆっくり変化する
        a = round(-2.2 + 1.4 * math.sin(self.time * 0.5), 2)
        b = round(1.2 + 0.9 * math.sin(self.time * 0.31 + 1), 2)
        curve = EllipticCurve(a, b)
        self.background_graph.draw_curve(screen, curve, (35, 70, 110), 4, show_label=False)

        # 曲線の上を走る3つの点
        points = self.background_graph.points_on_curve(curve, 20)
        if points:
            for i, color in enumerate((COLOR_P, COLOR_Q, COLOR_ANSWER)):
                index = int(self.time * 60 + i * len(points) / 3) % len(points)
                position = self.background_graph.to_screen(points[index])
                draw_glow(screen, color, position, 16, 60)
                draw_point(screen, position, color, 6)

        draw_text(screen, "楕円曲線クエスト", (80, 190), 64, TEXT, True)
        draw_text(screen, "～ 点たちの「足し算」で遊ぼう ～", (86, 272), 26, COLOR_P, True)
        draw_text_block(screen,
                        "曲線の上の2つの点を「足す」と、また曲線の上の点になる――\n"
                        "そんな不思議な足し算が、スマホやインターネットの暗号を支えています。\n"
                        "数学が専門でなくても大丈夫。グラフを見ながら遊んでみましょう！",
                        (86, 330), 560, 18, TEXT_SUB, line_gap=10)
        draw_text(screen, "y² = x³ + ax + b", (86, 480), 34, CURVE, True)
        draw_text(screen, "Esc: タイトルに戻る / 終了", (86, SCREEN_HEIGHT - 40), 15, TEXT_SUB)
        self.draw_buttons(screen)
