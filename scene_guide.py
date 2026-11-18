"""ガイド（楕円曲線と暗号のしくみの解説）

1ページ = (見出し, 本文, 図を描く関数) の組で、GUIDE_PAGES に順番に並べています。
ページを増やしたいときは、GUIDE_PAGES に1つ足すだけで OK です。
図がいらないページは、図を描く関数のところを None にします。
"""

import pygame

from settings import *
from ui import Scene, Button, draw_text, draw_text_block, draw_panel, draw_point, draw_dashed_line
from curve import EllipticCurve
from graph import Graph
from special_points import SPECIAL_POINTS


# ═════════ 図を描く関数（どれも screen と、描く場所 area を受け取る） ═════════

def figure_shapes(screen, area):
    """a, b を変えると曲線の形が変わる例"""
    graph = Graph(area, (-3, 3.5), (-4, 4))
    graph.draw_background(screen)
    examples = [((-1, 1), CURVE), ((-2, 0), COLOR_Q), ((0, 2), COLOR_P)]
    for i, ((a, b), color) in enumerate(examples):
        curve = EllipticCurve(a, b)
        graph.draw_curve(screen, curve, color, 3, show_label=False)
        draw_text(screen, curve.label(), (area[0] + 14, area[1] + 12 + i * 28), 20, color, True)


def figure_addition(screen, area):
    """P + Q の作図"""
    graph = Graph(area, (-2.5, 3.5), (-4, 4))
    graph.draw_background(screen)
    curve = EllipticCurve(-1, 1)
    graph.draw_curve(screen, curve)
    P = (-1.0, curve.y_at(-1.0))
    Q = (0.0, curve.y_at(0.0))
    graph.draw_addition(screen, P, curve.add(P, Q), 10)
    draw_point(screen, graph.to_screen(P), COLOR_P, 8, "P")
    draw_point(screen, graph.to_screen(Q), COLOR_Q, 8, "Q")
    draw_text(screen, "★ = 3つ目の交点", (area[0] + 14, area[1] + 44), 18, COLOR_STAR, True)


def figure_infinity(screen, area):
    """P + (−P) = O の作図（縦の直線）"""
    graph = Graph(area, (-2.5, 3.5), (-4, 4))
    graph.draw_background(screen)
    curve = EllipticCurve(-1, 1)
    graph.draw_curve(screen, curve)
    P = (1.0, curve.y_at(1.0))
    minus_P = (1.0, -P[1])
    graph.draw_addition(screen, P, curve.add(P, minus_P), 10)
    draw_point(screen, graph.to_screen(P), COLOR_P, 8, "P")
    draw_point(screen, graph.to_screen(minus_P), COLOR_Q, 8, "−P")


def figure_cycle(screen, area):
    """位数 7 の点: P, 2P, ..., 6P と回って 7P = O に戻る"""
    data = next(d for d in SPECIAL_POINTS if d["order"] == 7)
    curve = EllipticCurve(data["a"], data["b"])
    points = curve.multiples(data["point"], 6)
    graph = Graph(area)
    graph.fit(points, curve)
    graph.draw_background(screen)
    graph.draw_curve(screen, curve)
    for start, end in zip(points, points[1:]):
        draw_dashed_line(screen, (140, 140, 190), graph.to_screen(start), graph.to_screen(end), 1)
    for m, point in enumerate(points, 1):
        color = COLOR_P if m == 1 else COLOR_ANSWER
        draw_point(screen, graph.to_screen(point), color, 7, "P" if m == 1 else f"{m}P", 16)
    draw_text(screen, "7P = O（そしてまた P へ）", (area[0] + area[2] // 2, area[1] + area[3] - 34),
              18, COLOR_ANSWER, True, "center")


def figure_mod_p(screen, area):
    """mod 23 の世界の楕円曲線（点のつぶつぶ）"""
    p, a, b = 23, 1, 1
    cell = min(area[2], area[3]) / p     # 1マスの大きさ（図が描く場所に収まるように）
    left, bottom = area[0], area[1] + cell * p
    pygame.draw.rect(screen, GRAPH_BACKGROUND, (left, area[1], cell * p, cell * p))
    for i in range(p + 1):
        pygame.draw.line(screen, GRID, (left + i * cell, area[1]), (left + i * cell, bottom))
        pygame.draw.line(screen, GRID, (left, bottom - i * cell), (left + cell * p, bottom - i * cell))
    # y² と x³ + ax + b を 23 で割った余りが等しい (x, y) をすべて点で描く
    for x in range(p):
        for y in range(p):
            if (y * y - (x ** 3 + a * x + b)) % p == 0:
                center = (left + (x + 0.5) * cell, bottom - (y + 0.5) * cell)
                pygame.draw.circle(screen, CURVE, center, 6)
    draw_text(screen, "y² = x³ + x + 1  (mod 23)", (left, area[1] - 30), 18, CURVE, True)
    draw_text(screen, "0", (left, bottom + 4), 14, TEXT_SUB)
    draw_text(screen, "22", (left + cell * p, bottom + 4), 14, TEXT_SUB, anchor="topright")


def figure_bitcoin(screen, area):
    """ビットコインの曲線 y² = x³ + 7 を実数で描いたもの"""
    graph = Graph(area, (-3, 4), (-7, 7))
    graph.draw_background(screen)
    graph.draw_curve(screen, EllipticCurve(0, 7), COLOR_P)
    draw_text(screen, "ビットコインの曲線（実数で描いた場合）", (area[0] + 14, area[1] + 44), 17, TEXT_SUB)


# ═════════ ページの中身 ═════════

GUIDE_PAGES = [
    ("楕円曲線ってなに？",
     "楕円曲線とは、y² = x³ + ax + b という式で表される曲線のことです。\n\n"
     "名前に「楕円」とありますが、楕円（だ円）とは形がまったく違います。楕円の弧の長さを計算する研究から"
     "見つかったので、この名前が残っています。\n\n"
     "a と b を変えると、右の図のようにいろいろな形になります。1つにつながった形のときも、"
     "2つに分かれた形のときもあります。どれも上下（x 軸について）対称なのがポイントです。",
     figure_shapes),
    ("点の「足し算」",
     "楕円曲線の上の2点 P、Q に対して、次の手順で「P + Q」という新しい点を決めます。\n\n"
     "① P と Q を通る直線を引く\n"
     "② 直線は曲線と、もう1点（★）で交わる\n"
     "③ ★ を上下にひっくり返した点が P + Q\n\n"
     "P と P を足す（2P）ときは、P で曲線にふれる直線（接線）を使います。\n\n"
     "ふつうの足し算と同じく、順番を入れかえても答えは同じ（P + Q = Q + P）です。",
     figure_addition),
    ("無限遠点 O ―「0」の役割",
     "P と、P を上下反転した点（−P と書きます）を通る直線は真っすぐ縦になり、3つ目の交点がありません。\n\n"
     "そこで「縦の直線は、はるか上（無限のかなた）にある点 O で曲線と交わる」と考えます。"
     "これが無限遠点 O です。\n\n"
     "・P + (−P) = O\n・P + O = P\n\n"
     "つまり O は、ふつうの足し算の「0」と同じ役割をします。"
     "このように足し算のルールがそろったものを、数学では「群（ぐん）」と呼びます。",
     figure_infinity),
    ("くり返し足すと…（位数）",
     "P に P を足して 2P、さらに P を足して 3P、…とくり返すことを「P を k 倍する（kP）」といいます。\n\n"
     "ほとんどの点は、くり返すほど遠くへ飛んでいきます。ところが特別な点は、何回か足すと O に戻り、"
     "同じ点をぐるぐる回ります。戻るまでの回数をその点の「位数」といいます。\n\n"
     "右の図の点は位数 7。P → 2P → … → 6P と回り、7P = O になります。"
     "③ 暗号クイズでは、こうした点を使って出題しています。",
     figure_cycle),
    ("mod p の世界（豆知識）",
     "実際の暗号では、実数ではなく、素数 p で割った余り（0〜p−1 の整数）だけを使います。"
     "例えば mod 23 では 25 は 2 と同じ、−1 は 22 と同じです。\n\n"
     "すると曲線は、右の図のような「点のつぶつぶ」になります。それでもグラフで見た足し算と同じ公式で計算できます。\n\n"
     "点がバラバラに散らばっているので、グラフを眺めても kP から k を推理する手がかりがありません。"
     "これも暗号が破られにくい理由の1つです。",
     figure_mod_p),
    ("なぜ暗号に使えるの？",
     "P を k 回足した点 kP は、コンピュータならすぐに計算できます。\n\n"
     "ところが逆に「P と kP だけを見て k を当てる」のは、とてつもなく難しいことが知られています"
     "（楕円曲線の離散対数問題）。\n\n"
     "そこで k を「秘密鍵」、Q = kP を「公開鍵」として使うのが楕円曲線暗号です。"
     "実際には 77 けたほどの巨大な数が使われ、HTTPS の通信、スマホ、"
     "ビットコインの電子署名などで毎日使われています。右はビットコインで使われている曲線 y² = x³ + 7 です。",
     figure_bitcoin),
    ("公式まとめ（計算してみたい人へ）",
     "P = (x1, y1)、Q = (x2, y2) のとき\n\n"
     "■ 直線の傾き λ（ラムダ）\n"
     "　P ≠ Q のとき　λ = (y2 − y1) ÷ (x2 − x1)\n"
     "　P = Q のとき　λ = (3 × x1² + a) ÷ (2 × y1)　（接線の傾き）\n\n"
     "■ 答え P + Q = (x3, y3)\n"
     "　x3 = λ² − x1 − x2\n"
     "　y3 = λ × (x1 − x3) − y1\n\n"
     "■ 逆元　−(x, y) = (x, −y)\n\n"
     "このゲームの計算は、すべて curve.py の add() という関数でこの公式どおりに行っています。",
     None),
]


class GuideScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.page = 0
        self.buttons = [
            Button((60, 680, 180, 54), "← 前へ", self.turn_page, -1, size=20, key=pygame.K_LEFT),
            Button((250, 680, 180, 54), "次へ →", self.turn_page, +1, size=20, color=ACCENT, key=pygame.K_RIGHT),
            Button((1040, 680, 180, 54), "タイトルへ", app.goto, "title", size=20),
        ]

    def turn_page(self, amount):
        self.page = max(0, min(len(GUIDE_PAGES) - 1, self.page + amount))

    def draw(self, screen):
        screen.fill(BACKGROUND)
        title, body, figure = GUIDE_PAGES[self.page]
        self.draw_header(screen, f"ガイド {self.page + 1}/{len(GUIDE_PAGES)}　{title}")

        text_width = 560 if figure else 1120
        draw_panel(screen, (40, 95, text_width + 40, 565))
        draw_text_block(screen, body, (60, 115), text_width, 20, TEXT, line_gap=9)
        if figure:
            figure(screen, (680, 125, 560, 520))

        # 何ページ目かを示す丸
        for i in range(len(GUIDE_PAGES)):
            color = ACCENT if i == self.page else PANEL_EDGE
            pygame.draw.circle(screen, color, (SCREEN_WIDTH // 2 - 72 + i * 24, 707), 7)
        self.draw_buttons(screen)
