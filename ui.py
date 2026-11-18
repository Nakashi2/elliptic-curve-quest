"""画面づくりの部品をまとめたファイル

    ・文字を書く        draw_text, draw_text_block
    ・図形を描く        draw_panel, draw_point, draw_star, draw_dashed_line, draw_arrow, draw_glow
    ・ボタン            Button
    ・スライダー        Slider
    ・画面の基本形      Scene（タイトル画面やクイズ画面は、これを元に作る）
"""

import math

import pygame

from settings import *  # 色や画面サイズなどの設定をすべて読み込む


# ═════════════════════ 文字 ═════════════════════

_font_cache = {}  # 一度読み込んだフォントを覚えておく場所


def get_font(size, bold=False):
    """指定した大きさの日本語フォントを返す"""
    key = (size, bold)
    if key not in _font_cache:
        path = None
        for name in FONT_NAMES:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                break
        _font_cache[key] = pygame.font.Font(path, size)
    return _font_cache[key]


def draw_text(screen, message, position, size=20, color=TEXT, bold=False, anchor="topleft"):
    """1行の文字を書く

    anchor は position が文字のどこを指すか。
      "topleft"（左上） / "center"（中心） / "topright"（右上） / "midleft"（左の真ん中）など
    """
    image = get_font(size, bold).render(str(message), True, color)
    rect = image.get_rect(**{anchor: position})
    screen.blit(image, rect)
    return rect


# 行の先頭に来てはいけない文字（「。」が行頭に来ないようにする）
NO_LINE_START = "、。，．）」』】・ー！？!?,.)"


def is_english(char):
    """半角の英字・数字か"""
    return char.isascii() and char.isalnum()


def wrap_text(message, size, width, bold=False):
    """長い文章を、幅 width に収まるように何行かに分ける"""
    font = get_font(size, bold)
    lines = []
    for paragraph in str(message).split("\n"):
        line = ""
        for char in paragraph:
            too_long = font.size(line + char)[0] > width
            if too_long and line and char not in NO_LINE_START:
                # 英単語（例: ECDH）の途中で切れそうなときだけ、直前の空白で折り返す
                in_word = is_english(char) and is_english(line[-1])
                space = line.rfind(" ")
                if in_word and space > len(line) // 2:
                    lines.append(line[:space])
                    line = line[space + 1:] + char
                else:
                    lines.append(line)
                    line = char.strip()
            else:
                line += char
        lines.append(line)
    return lines


def draw_text_block(screen, message, position, width, size=19, color=TEXT, bold=False, line_gap=6):
    """長い文章を折り返して書く。書き終わった位置の y 座標を返す"""
    x, y = position
    for line in wrap_text(message, size, width, bold):
        draw_text(screen, line, (x, y), size, color, bold)
        y += size + line_gap
    return y


# ═════════════════════ 図形 ═════════════════════

def draw_panel(screen, area, color=PANEL):
    """角の丸い四角（説明パネルなど）"""
    pygame.draw.rect(screen, color, area, border_radius=14)
    pygame.draw.rect(screen, PANEL_EDGE, area, 2, border_radius=14)


def draw_glow(screen, color, center, radius, alpha=90):
    """半透明の丸（点をぼんやり光らせる）"""
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, alpha), (radius, radius), radius)
    screen.blit(glow, (center[0] - radius, center[1] - radius))


def draw_point(screen, center, color, radius=7, label=None, label_size=18):
    """点（ふちどり付きの丸）と、その右上に名前を書く"""
    center = (int(center[0]), int(center[1]))
    pygame.draw.circle(screen, (10, 10, 20), center, radius + 2)
    pygame.draw.circle(screen, color, center, radius)
    if label:
        image = get_font(label_size, True).render(label, True, color)
        rect = image.get_rect(midbottom=(center[0] + 10, center[1] - radius - 1))
        # 文字が読みやすいよう、うしろに半透明の黒い四角を敷く
        back = pygame.Surface(rect.inflate(6, 2).size, pygame.SRCALPHA)
        back.fill((10, 12, 24, 170))
        screen.blit(back, rect.inflate(6, 2))
        screen.blit(image, rect)


def draw_star(screen, color, center, radius):
    """星形 ★（3つ目の交点の目印）"""
    cx, cy = center
    corners = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.45   # 外側と内側を交互に
        corners.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(screen, color, corners)


def draw_dashed_line(screen, color, start, end, width=2, dash=9, gap=6):
    """点線"""
    length = math.dist(start, end)
    if length < 1:
        return
    position = 0
    while position < length:
        a = position / length
        b = min(1.0, (position + dash) / length)
        p1 = (start[0] + (end[0] - start[0]) * a, start[1] + (end[1] - start[1]) * a)
        p2 = (start[0] + (end[0] - start[0]) * b, start[1] + (end[1] - start[1]) * b)
        pygame.draw.line(screen, color, p1, p2, width)
        position += dash + gap


def draw_arrow(screen, color, start, end, width=3, head=12):
    """矢印"""
    pygame.draw.line(screen, color, start, end, width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    left = (end[0] - head * math.cos(angle - 0.45), end[1] - head * math.sin(angle - 0.45))
    right = (end[0] - head * math.cos(angle + 0.45), end[1] - head * math.sin(angle + 0.45))
    pygame.draw.polygon(screen, color, [end, left, right])


def smooth(t):
    """0〜1 の値を、ゆっくり始まりゆっくり終わる動きに変える（アニメーション用）"""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ═════════════════════ ボタン ═════════════════════

class Button:
    """クリックできるボタン

    使い方:
        Button((左, 上, 幅, 高さ), "表示する文字", 押したときに呼ぶ関数, 関数に渡す値)
    例:
        Button((100, 100, 200, 50), "タイトルへ", app.goto, "title")
        → 押すと app.goto("title") が呼ばれる
    """

    def __init__(self, area, label, action, value=None, size=22, color=BUTTON,
                 sub_label=None, key=None, enabled=True):
        self.rect = pygame.Rect(area)
        self.label = label
        self.action = action        # 押したときに呼ぶ関数
        self.value = value          # 関数に渡す値（None なら何も渡さない）
        self.size = size
        self.color = color
        self.sub_label = sub_label  # ボタンの下段に小さく書く説明（なくてもよい）
        self.key = key              # キーボードでも押せるようにするキー（なくてもよい）
        self.enabled = enabled      # False なら灰色になり押せない

    def press(self):
        if self.value is None:
            self.action()
        else:
            self.action(self.value)

    def handle_event(self, event):
        """クリックやキー入力でボタンが押されたら True を返す"""
        if not self.enabled:
            return False
        clicked = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                   and self.rect.collidepoint(event.pos))
        key_pressed = (self.key is not None and event.type == pygame.KEYDOWN
                       and event.key == self.key)
        if clicked or key_pressed:
            self.press()
            return True
        return False

    def draw(self, screen):
        hover = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.color if self.enabled else (45, 48, 66)
        if hover:  # マウスが乗っていたら少し明るくする
            color = tuple(min(255, c + 35) for c in color)
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        edge = (200, 205, 255) if hover else PANEL_EDGE
        pygame.draw.rect(screen, edge, self.rect, 2, border_radius=12)

        text_color = TEXT if self.enabled else (110, 115, 135)
        if self.sub_label:
            draw_text(screen, self.label, (self.rect.x + 22, self.rect.centery - 2),
                      self.size, text_color, True, "bottomleft")
            draw_text(screen, self.sub_label, (self.rect.x + 24, self.rect.centery + 4), 16, TEXT_SUB)
        else:
            draw_text(screen, self.label, self.rect.center, self.size, text_color, True, "center")


# ═════════════════════ スライダー ═════════════════════

class Slider:
    """つまみを左右に動かして数を選ぶ部品

    値が変わるたびに on_change(新しい値) が呼ばれる。
    """

    def __init__(self, area, label, minimum, maximum, step, value, on_change):
        self.rect = pygame.Rect(area)
        self.label = label
        self.minimum = minimum
        self.maximum = maximum
        self.step = step          # 値の刻み（0.1 なら 0.1 ずつ変わる）
        self.value = value
        self.on_change = on_change
        self.dragging = False     # つまみをつかんでいる最中か

    def knob_x(self):
        ratio = (self.value - self.minimum) / (self.maximum - self.minimum)
        return self.rect.x + ratio * self.rect.width

    def set_value_from_mouse(self, mouse_x):
        ratio = (mouse_x - self.rect.x) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        value = self.minimum + ratio * (self.maximum - self.minimum)
        value = round(round(value / self.step) * self.step, 6)  # 刻みに合わせる
        if value != self.value:
            self.value = value
            self.on_change(value)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(20, 30).collidepoint(event.pos):
                self.dragging = True
                self.set_value_from_mouse(event.pos[0])
                return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_value_from_mouse(event.pos[0])
            return True
        if event.type == pygame.MOUSEBUTTONUP and self.dragging:
            self.dragging = False
            return True
        return False

    def draw(self, screen):
        draw_text(screen, f"{self.label} = {self.value:+.1f}", (self.rect.x, self.rect.y - 26), 19, TEXT, True)
        y = self.rect.centery
        pygame.draw.line(screen, AXIS, (self.rect.x, y), (self.rect.right, y), 4)
        knob = (int(self.knob_x()), y)
        pygame.draw.circle(screen, ACCENT, knob, 10)
        pygame.draw.circle(screen, WHITE, knob, 10, 2)


# ═════════════════════ 画面の基本形 ═════════════════════

class Scene:
    """1つの画面（タイトル画面・クイズ画面など）の基本形

    それぞれの画面は、このクラスを元に次の3つを書きかえて作る。
        handle_event(event) : クリックやキー入力が起きたときの処理
        update(dt)          : 時間を進める処理（dt は前回からの経過秒数）
        draw(screen)        : 画面に絵を描く処理
    """

    def __init__(self, app):
        self.app = app        # ゲーム本体（画面の切りかえ app.goto(...) に使う）
        self.buttons = []     # この画面にあるボタン

    def handle_event(self, event):
        # Esc キーでタイトル画面に戻る
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.goto("title")
            return True
        for button in self.buttons:
            if button.handle_event(event):
                return True
        return False

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

    def draw_buttons(self, screen):
        for button in self.buttons:
            button.draw(screen)

    def draw_header(self, screen, title, subtitle=None):
        """画面上部の見出し"""
        draw_text(screen, title, (40, 22), 30, TEXT, True)
        if subtitle:
            draw_text(screen, subtitle, (42, 60), 17, TEXT_SUB)
