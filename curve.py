"""実数の楕円曲線 y² = x³ + ax + b の計算をまとめたファイル

このファイルは画面表示（pygame）を一切使わない「計算だけ」の部分です。

点の表し方:
    ・ふつうの点は (x, y) というタプル        例: (3, 8)
    ・無限遠点 O は None                      （足し算の「0」の役割をする特別な点）
"""

import math


def is_close(u, v):
    """2つの数がほぼ等しいか（コンピュータの小数計算の小さな誤差を許す）"""
    return math.isclose(u, v, rel_tol=1e-7, abs_tol=1e-7)


def number_text(value):
    """数を見やすい文字にする。整数なら小数点なし（3.0 → '3'）、それ以外は小数2けた"""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def point_text(point):
    """点を文字にする。例: (3, 8)、無限遠点なら 'O'"""
    if point is None:
        return "O（無限遠点）"
    # 小数の誤差（7.9999999 など）は丸めてから表示する
    x, y = (round(v, 6) for v in point)
    return f"({number_text(x)}, {number_text(y)})"


class AddResult:
    """足し算 P + Q の答えと、作図に必要な情報をまとめたもの"""

    def __init__(self, result, third=None, slope=None, is_tangent=False):
        self.result = result            # 答えの点 P + Q（O のときは None）
        self.third = third              # 直線と曲線の「3つ目の交点 ★」
        self.slope = slope              # 直線の傾き λ
        self.is_tangent = is_tangent    # 接線を使ったか（P = Q のとき True）
        self.is_vertical = slope is None  # 縦の直線か（このとき答えは O）


class EllipticCurve:
    """楕円曲線 y² = x³ + ax + b"""

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self._shape_cache = {}  # 曲線の形の計算結果を覚えておく場所（毎回計算すると遅いため）

    # ─── 基本 ───

    def right_side(self, x):
        """右辺 x³ + ax + b の値"""
        return x ** 3 + self.a * x + self.b

    def y_at(self, x, sign=1):
        """x に対応する y を返す（sign が正なら上側、負なら下側）。点がなければ None"""
        value = self.right_side(x)
        if value < 0:
            return None
        return math.copysign(math.sqrt(value), sign)

    def is_singular(self):
        """とがった点や交差がある「特異曲線」か（そのときは楕円曲線と呼ばない）"""
        return abs(4 * self.a ** 3 + 27 * self.b ** 2) < 0.05

    def label(self):
        """画面に表示する式。例: 'y² = x³ − 43x + 166'"""
        text = "y² = x³"
        if self.a != 0:
            sign = "+" if self.a > 0 else "−"
            number = "" if abs(self.a) == 1 else number_text(abs(self.a))
            text += f" {sign} {number}x"
        if self.b != 0:
            sign = "+" if self.b > 0 else "−"
            text += f" {sign} {number_text(abs(self.b))}"
        return text

    # ─── 点の足し算（このゲームの主役） ───

    def add(self, P, Q):
        """P + Q を計算する

        手順（グラフで見ると）:
          ① P と Q を通る直線を引く（P = Q のときは P での接線）
          ② 直線と曲線の 3つ目の交点 ★ を求める
          ③ ★ を上下にひっくり返した点が P + Q
        """
        if P is None:          # O + Q = Q（O は「0」の役割）
            return AddResult(Q)
        if Q is None:          # P + O = P
            return AddResult(P)

        x1, y1 = P
        x2, y2 = Q
        if is_close(x1, x2):
            if is_close(y1, -y2):
                # P の真上・真下に Q がある → 直線が縦になる → 答えは O
                return AddResult(None)
            # P と Q が同じ点 → 接線の傾き
            slope = (3 * x1 * x1 + self.a) / (2 * y1)
            is_tangent = True
        else:
            # P と Q を通る直線の傾き
            slope = (y2 - y1) / (x2 - x1)
            is_tangent = False

        x3 = slope * slope - x1 - x2        # 3つ目の交点の x 座標
        y_third = y1 + slope * (x3 - x1)    # 直線の式に x3 を入れた y 座標（★）
        third = (x3, y_third)
        result = (x3, -y_third)             # 上下にひっくり返す
        return AddResult(result, third, slope, is_tangent)

    def multiples(self, P, count):
        """[P, 2P, 3P, ..., count×P] のリストを返す（O の場所は None になる）"""
        points = [P]
        while len(points) < count:
            points.append(self.add(points[-1], P).result)
        return points

    # ─── グラフを描くための計算 ───

    def real_roots(self):
        """右辺 x³ + ax + b = 0 となる x（曲線が x 軸と交わる場所）をすべて求める

        3次式のグラフは、山と谷（傾きが 0 の場所）で区切ると各区間で単調になる。
        各区間の両端で符号が変われば、その間に根が1つあるので「二分法」で探す。
        """
        bound = 1 + max(abs(self.a), abs(self.b))   # 根は必ずこの範囲に入る
        edges = [-bound]
        if self.a < 0:                               # 山と谷がある場合
            top = math.sqrt(-self.a / 3)
            edges += [-top, top]
        edges.append(bound)

        roots = []
        for left, right in zip(edges, edges[1:]):
            if self.right_side(left) * self.right_side(right) > 0:
                continue                             # この区間に根はない
            for _ in range(100):                     # 二分法: 区間を半分にしていく
                middle = (left + right) / 2
                if self.right_side(left) * self.right_side(middle) <= 0:
                    right = middle
                else:
                    left = middle
            roots.append((left + right) / 2)
        return roots

    def shape(self, x_min, x_max, samples=700):
        """曲線を「折れ線のリスト」として返す（グラフに描くため）

        曲線が2つに分かれている場合は折れ線が2本になる。
        """
        key = (x_min, x_max)
        if key in self._shape_cache:
            return self._shape_cache[key]

        # 調べる x を並べる。x 軸と交わる場所の近くは曲線が急なので細かく調べる
        width = x_max - x_min
        xs = [x_min + width * i / samples for i in range(samples + 1)]
        roots = [r for r in self.real_roots() if x_min < r < x_max]
        for r in roots:
            xs.append(r)
            for step in (1e-6, 1e-5, 1e-4, 1e-3, 4e-3):
                xs += [r - step * width, r + step * width]
        xs.sort()

        # 右辺が 0 以上の x が続く区間ごとに、曲線の一続きの部分ができる
        pieces = []
        current = []
        for x in xs:
            value = 0.0 if x in roots else self.right_side(x)
            if value >= 0:
                current.append((x, math.sqrt(value)))
            elif current:
                pieces.append(current)
                current = []
        if current:
            pieces.append(current)

        # 下半分（右から左へ）と上半分（左から右へ）をつないで1本の折れ線にする
        lines = []
        for piece in pieces:
            lower = [(x, -y) for x, y in reversed(piece)]
            upper = [(x, y) for x, y in piece]
            lines.append(lower + upper)

        self._shape_cache[key] = lines
        return lines
