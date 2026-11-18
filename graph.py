"""楕円曲線のグラフを描くファイル

数学の座標 (x, y) と、画面上の位置（ピクセル）を対応させ、
方眼・曲線・足し算の作図アニメーションを描きます。

※ 数学では上が y の正の向きですが、画面では下に行くほど数字が大きくなります。
   その変換は to_screen() の中で行っています。
"""

import math
import time

import pygame

from settings import *
from ui import draw_text, draw_point, draw_star, draw_dashed_line, draw_arrow, draw_glow, smooth


def nice_step(span):
    """目盛りの間かくを 1, 2, 5, 10, 20, 50, ... のようなきりのよい数にする"""
    rough = span / 10
    power = 10 ** math.floor(math.log10(rough))
    for multiple in (1, 2, 5, 10):
        if rough <= multiple * power:
            return multiple * power
    return 10 * power


class Graph:
    """グラフを描く場所と、表示する範囲を管理する"""

    def __init__(self, area, x_range=(-3.5, 4.5), y_range=(-5.0, 5.0)):
        self.rect = pygame.Rect(area)          # 画面上の場所
        self.x_min, self.x_max = x_range       # 表示する x の範囲
        self.y_min, self.y_max = y_range       # 表示する y の範囲

    # ─── 座標の変換 ───

    def to_screen(self, point):
        """数学の座標 (x, y) → 画面上の位置 (ピクセル)"""
        x, y = point
        sx = self.rect.left + (x - self.x_min) / (self.x_max - self.x_min) * self.rect.width
        sy = self.rect.bottom - (y - self.y_min) / (self.y_max - self.y_min) * self.rect.height
        # とても遠い点は描画でエラーになるので、ほどほどの範囲に収める
        return (max(-10000, min(10000, sx)), max(-10000, min(10000, sy)))

    def is_visible(self, point, margin=0):
        """点がグラフの中に見えているか（margin はふちからの余白ピクセル）"""
        if point is None:
            return False
        inner = self.rect.inflate(-2 * margin, -2 * margin)
        return inner.collidepoint(self.to_screen(point))

    def pixel_distance(self, p, q):
        """2点の、画面上での距離（ピクセル）"""
        return math.dist(self.to_screen(p), self.to_screen(q))

    def fit(self, points, curve):
        """指定した点と、曲線の左端がすべて見えるように表示範囲を決める"""
        xs = [p[0] for p in points] + curve.real_roots()
        x_margin = (max(xs) - min(xs)) * 0.15
        self.x_min = min(xs) - x_margin
        self.x_max = max(xs) + x_margin
        top = max(abs(p[1]) for p in points) * 1.25   # 上下対称にする
        self.y_min, self.y_max = -top, top

    # ─── 描画 ───

    def draw_background(self, screen):
        """背景・方眼・軸・目盛りの数字"""
        pygame.draw.rect(screen, GRAPH_BACKGROUND, self.rect, border_radius=12)
        screen.set_clip(self.rect)   # これ以降、グラフの枠の外には描かない

        step = nice_step(self.x_max - self.x_min)
        x = math.ceil(self.x_min / step) * step
        while x <= self.x_max:
            top, bottom = self.to_screen((x, self.y_max)), self.to_screen((x, self.y_min))
            is_axis = abs(x) < step / 2
            pygame.draw.line(screen, AXIS if is_axis else GRID, top, bottom, 2 if is_axis else 1)
            if not is_axis:
                draw_text(screen, f"{x:g}", (top[0], self.to_screen((0, 0))[1] + 4), 14, TEXT_SUB, anchor="midtop")
            x += step

        step = nice_step(self.y_max - self.y_min)
        y = math.ceil(self.y_min / step) * step
        while y <= self.y_max:
            left, right = self.to_screen((self.x_min, y)), self.to_screen((self.x_max, y))
            is_axis = abs(y) < step / 2
            pygame.draw.line(screen, AXIS if is_axis else GRID, left, right, 2 if is_axis else 1)
            if not is_axis:
                draw_text(screen, f"{y:g}", (self.to_screen((0, 0))[0] - 5, left[1]), 14, TEXT_SUB, anchor="midright")
            y += step

        screen.set_clip(None)        # 描く範囲の制限を元に戻す
        pygame.draw.rect(screen, PANEL_EDGE, self.rect, 2, border_radius=12)

    def draw_curve(self, screen, curve, color=CURVE, width=3, show_label=True):
        """楕円曲線を描く"""
        screen.set_clip(self.rect)
        limit = 4 * max(abs(self.y_min), abs(self.y_max))   # 画面よりずっと外の部分は描かない
        margin = (self.x_max - self.x_min) * 0.05
        for line in curve.shape(self.x_min - margin, self.x_max + margin):
            visible_part = []
            for point in line:
                if abs(point[1]) <= limit:
                    visible_part.append(self.to_screen(point))
                else:
                    if len(visible_part) >= 2:
                        pygame.draw.lines(screen, color, False, visible_part, width)
                    visible_part = []
            if len(visible_part) >= 2:
                pygame.draw.lines(screen, color, False, visible_part, width)
        screen.set_clip(None)
        if show_label:
            draw_text(screen, curve.label(), (self.rect.x + 16, self.rect.y + 12), 24, color, True)

    def points_on_curve(self, curve, margin=0):
        """グラフの中に見えている曲線上の点のリスト（クリックで点を選ぶときなどに使う）"""
        result = []
        for line in curve.shape(self.x_min, self.x_max):
            result += [p for p in line if self.is_visible(p, margin)]
        return result

    def line_ends(self, point, slope):
        """point を通る傾き slope の直線の、グラフの外まで届く両端"""
        x1, y1 = point
        x_margin = (self.x_max - self.x_min) * 0.2
        y_margin = (self.y_max - self.y_min) * 0.2
        left, right = self.x_min - x_margin, self.x_max + x_margin
        if abs(slope) > 1e-12:
            # 急な直線は、上下のはしを超えたところで止める
            x_at_bottom = x1 + (self.y_min - y_margin - y1) / slope
            x_at_top = x1 + (self.y_max + y_margin - y1) / slope
            left = max(left, min(x_at_bottom, x_at_top))
            right = min(right, max(x_at_bottom, x_at_top))
        return (left, y1 + slope * (left - x1)), (right, y1 + slope * (right - x1))

    def draw_addition(self, screen, start, add_result, t, answer_label="P+Q"):
        """足し算の作図を、時刻 t（秒）まで進めたところまで描く

            0.0〜0.8秒 : 直線が伸びる
            0.8秒〜    : 3つ目の交点 ★ が光る
            1.6秒〜    : ★ から上下反転した場所へ点線が伸びる
            2.2秒〜    : 答えの点が現れる
        start は直線が通る点（P など）。
        """
        pulse = 1 + 0.15 * math.sin(time.time() * 6)   # 点を脈打たせる
        start_s = self.to_screen(start)

        if add_result.is_vertical:
            # 縦の直線 → 答えは O（無限遠点）
            x = start[0]
            top = self.to_screen((x, self.y_max * 2))
            bottom = self.to_screen((x, self.y_min * 2))
            grow = smooth(t / 0.8)
            screen.set_clip(self.rect)
            pygame.draw.line(screen, COLOR_LINE, start_s,
                             (top[0], start_s[1] + (top[1] - start_s[1]) * grow), 3)
            pygame.draw.line(screen, COLOR_LINE, start_s,
                             (bottom[0], start_s[1] + (bottom[1] - start_s[1]) * grow), 3)
            screen.set_clip(None)
            if t > 0.9:
                tip = (start_s[0], self.rect.y + 14)
                draw_arrow(screen, COLOR_LINE, (tip[0], self.rect.y + 70), tip, 3)
                anchor, offset = ("topleft", 14) if tip[0] < self.rect.centerx else ("topright", -14)
                draw_text(screen, "O（無限遠点）へ！", (tip[0] + offset, self.rect.y + 10), 20,
                          COLOR_LINE, True, anchor)
            return

        # ① 直線が start から両側へ伸びる
        end1, end2 = self.line_ends(start, add_result.slope)
        grow = smooth(t / 0.8)
        p1 = (start[0] + (end1[0] - start[0]) * grow, start[1] + (end1[1] - start[1]) * grow)
        p2 = (start[0] + (end2[0] - start[0]) * grow, start[1] + (end2[1] - start[1]) * grow)
        screen.set_clip(self.rect)
        pygame.draw.line(screen, COLOR_LINE, self.to_screen(p1), self.to_screen(p2), 3)

        # ② 3つ目の交点 ★
        star_s = self.to_screen(add_result.third)
        if t > 0.8:
            draw_glow(screen, COLOR_STAR, star_s, int(18 * pulse), 60)
            draw_star(screen, COLOR_STAR, star_s, 13)

        # ③ 上下にひっくり返す
        answer_s = self.to_screen(add_result.result)
        if t > 1.6:
            move = smooth((t - 1.6) / 0.6)
            moving = (star_s[0], star_s[1] + (answer_s[1] - star_s[1]) * move)
            draw_dashed_line(screen, WHITE, star_s, moving, 2)
        screen.set_clip(None)

        # ④ 答えの点
        if t > 2.2:
            draw_glow(screen, COLOR_ANSWER, answer_s, int(22 * pulse), 70)
            draw_point(screen, answer_s, COLOR_ANSWER, 9, answer_label)


def addition_step(t):
    """作図アニメーションが今どの段階か（0〜3）。説明文の強調に使う"""
    if t < 0.8:
        return 0
    if t < 1.6:
        return 1
    if t < 2.2:
        return 2
    return 3


def addition_steps_text(add_result, line_name="P と Q を通る直線"):
    """作図の手順の説明文（4行）"""
    if add_result.is_vertical:
        return ["① 2点を通る直線を引くと、真っすぐ縦になる",
                "② 縦の直線は、曲線ともう1点では交わらない",
                "③ このときの答えは「無限遠点 O」",
                "④ O は足し算の「0」の役割をする点"]
    return [f"① {line_name}を引く",
            "② 直線が曲線ともう1点で交わる（★）",
            "③ ★ を上下にひっくり返す（x 軸で折り返す）",
            "④ それが答えの点！"]
