"""結果画面とハイスコア画面

ハイスコアは、このフォルダの scores.json というファイルに保存されます。
中身はこのような形です（モードごとに上位5件）:
    {"graph_quiz": [{"name": "たろう", "score": 1200, "detail": "9/10問", "date": "2026-11-18"}, ...],
     "crypto_quiz": [...]}
"""

import json
from datetime import date
from pathlib import Path

import pygame

from settings import *
from ui import Scene, Button, draw_text, draw_panel

SCORE_FILE = Path(__file__).with_name("scores.json")
RANKING_SIZE = 5
MODE_NAMES = {"graph_quiz": "② グラフクイズ", "crypto_quiz": "③ 暗号クイズ"}


# ═════════ ハイスコアの読み書き ═════════

def load_scores():
    """保存されているハイスコアを読む（ファイルがなければ空）"""
    try:
        return json.loads(SCORE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def is_high_score(mode, score):
    """この得点がランキング（上位5件）に入るか"""
    ranking = load_scores().get(mode, [])
    if score <= 0:
        return False
    return len(ranking) < RANKING_SIZE or score > min(entry["score"] for entry in ranking)


def save_score(mode, name, score, detail):
    """ハイスコアを書きこむ"""
    scores = load_scores()
    ranking = scores.setdefault(mode, [])
    ranking.append({"name": name or "ななし", "score": score, "detail": detail,
                    "date": date.today().isoformat()})
    ranking.sort(key=lambda entry: entry["score"], reverse=True)   # 得点の高い順に並べる
    del ranking[RANKING_SIZE:]                                     # 6位以下は消す
    try:
        SCORE_FILE.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass   # 保存できなくてもゲームは続ける


# ═════════ 結果画面 ═════════

class ResultScene(Scene):
    """クイズの結果を表示し、ハイスコアなら名前を入力してもらう"""

    def __init__(self, app, mode, score, detail, lines):
        super().__init__(app)
        self.mode = mode          # "graph_quiz" または "crypto_quiz"
        self.score = score
        self.detail = detail      # ランキングに一緒に表示する一言（例: "8/10問"）
        self.lines = lines        # 得点の下に表示する文のリスト
        self.time = 0.0
        self.name = ""            # 入力中の名前
        self.composing = ""       # 日本語入力で変換中の文字
        self.needs_name = is_high_score(mode, score)
        self.saved = False

        self.buttons = [
            Button((340, 620, 280, 60), "もう一度", self.leave, mode, color=ACCENT),
            Button((660, 620, 280, 60), "タイトルへ", self.leave, "title"),
        ]
        if self.needs_name:
            self.buttons.append(Button((790, 470, 150, 54), "登録", self.save, size=20, color=ACCENT))
            pygame.key.start_text_input()     # キーボードからの文字入力（日本語入力も）を受けつける

    def leave(self, scene_name):
        pygame.key.stop_text_input()
        self.app.goto(scene_name)

    def save(self):
        if self.saved:
            return
        save_score(self.mode, self.name.strip()[:12], self.score, self.detail)
        self.saved = True
        pygame.key.stop_text_input()
        self.buttons = [b for b in self.buttons if b.label != "登録"]

    def handle_event(self, event):
        if self.needs_name and not self.saved:
            if event.type == pygame.TEXTINPUT:          # 文字が確定した
                self.name = (self.name + event.text)[:12]
                return True
            if event.type == pygame.TEXTEDITING:        # 日本語の変換中
                self.composing = event.text
                return True
            if event.type == pygame.KEYDOWN and not self.composing:
                if event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                    return True
                if event.key == pygame.K_RETURN:
                    self.save()
                    return True
        return super().handle_event(event)

    def update(self, dt):
        self.time += dt

    def draw(self, screen):
        screen.fill(BACKGROUND)
        center = SCREEN_WIDTH // 2
        draw_text(screen, f"{MODE_NAMES[self.mode]}　結果", (center, 90), 34, TEXT, True, "center")

        # 得点が 0 から数え上がっていく演出（1.2秒）
        progress = min(1.0, self.time / 1.2)
        draw_text(screen, f"{int(self.score * progress)} 点", (center, 200), 80, COLOR_P, True, "center")

        y = 290
        for line in self.lines:
            draw_text(screen, line, (center, y), 26, TEXT, True, "center")
            y += 44

        if self.needs_name:
            if self.saved:
                draw_text(screen, "ハイスコアに登録しました！", (center, 490), 24, GOOD, True, "center")
            else:
                draw_text(screen, "★ ハイスコア入り！ 名前を入力して Enter（日本語入力もOK）",
                          (center, 430), 20, COLOR_Q, True, "center")
                box = pygame.Rect(400, 470, 380, 54)
                pygame.draw.rect(screen, GRAPH_BACKGROUND, box, border_radius=10)
                pygame.draw.rect(screen, ACCENT, box, 2, border_radius=10)
                cursor = "|" if int(self.time * 2) % 2 == 0 else ""
                if self.name or self.composing:
                    draw_text(screen, self.name + self.composing + cursor, (box.x + 14, box.centery), 24, TEXT, True, "midleft")
                else:
                    draw_text(screen, "ななし" + cursor, (box.x + 14, box.centery), 24, TEXT_SUB, True, "midleft")
        self.draw_buttons(screen)


# ═════════ ハイスコア画面 ═════════

class ScoresScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [Button((490, 650, 300, 56), "タイトルへ", app.goto, "title", size=20)]

    def draw(self, screen):
        screen.fill(BACKGROUND)
        self.draw_header(screen, "ハイスコア")
        scores = load_scores()
        for column, (mode, title) in enumerate(MODE_NAMES.items()):
            x = 80 + column * 580
            draw_panel(screen, (x - 20, 100, 540, 520))
            draw_text(screen, title, (x, 120), 24, COLOR_P, True)
            ranking = scores.get(mode, [])
            if not ranking:
                draw_text(screen, "まだ記録がありません", (x, 180), 20, TEXT_SUB)
            for rank, entry in enumerate(ranking, 1):
                y = 180 + (rank - 1) * 80
                draw_text(screen, f"{rank}. {entry['name']}", (x, y), 24, TEXT, True)
                draw_text(screen, f"{entry['score']} 点", (x + 490, y), 24, COLOR_P, True, "topright")
                draw_text(screen, f"{entry['detail']}　{entry['date']}", (x + 30, y + 34), 16, TEXT_SUB)
        self.draw_buttons(screen)
