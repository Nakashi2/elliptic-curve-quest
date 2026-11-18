"""楕円曲線クエスト ― グラフを見ながら楕円曲線の「点の足し算」で遊ぶゲーム

起動方法:
    python main.py              （このフォルダの中で実行）
    または VSCode でこのファイルを開いて、右上の ▶ ボタンを押す

ゲームのしくみ:
    pygame のゲームは「入力を受けとる → 時間を進める → 画面を描く」を
    1秒間に60回くり返して動いています（run() の中の while ループ）。
    いま表示している画面（Scene）は self.scene に入っていて、
    goto("画面の名前") で別の画面に切りかえます。
"""

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WINDOW_TITLE
from scene_title import TitleScene
from scene_explore import ExploreScene
from scene_graph_quiz import GraphQuizScene
from scene_crypto_quiz import CryptoQuizScene
from scene_guide import GuideScene
from scene_result import ResultScene, ScoresScene

# 画面の名前と、その画面を作るクラスの対応表
SCENES = {
    "title": TitleScene,              # タイトル
    "explore": ExploreScene,          # ① グラフで体験
    "graph_quiz": GraphQuizScene,     # ② グラフクイズ
    "crypto_quiz": CryptoQuizScene,   # ③ 暗号クイズ
    "guide": GuideScene,              # ガイド
    "result": ResultScene,            # クイズの結果
    "scores": ScoresScene,            # ハイスコア
}


class App:
    """ゲーム本体"""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = TitleScene(self)

    def goto(self, scene_name, **details):
        """画面を切りかえる。details は画面に渡す情報（結果画面の得点など）"""
        self.scene = SCENES[scene_name](self, **details)

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000      # 前回からの経過時間（秒）

            # ① 入力を受けとる
            for event in pygame.event.get():
                if event.type == pygame.QUIT:     # ウィンドウの×ボタン
                    self.running = False
                else:
                    self.scene.handle_event(event)

            # ② 時間を進める
            self.scene.update(dt)

            # ③ 画面を描く
            self.scene.draw(self.screen)
            pygame.display.flip()                 # 描いた絵を実際に表示する

        pygame.quit()


if __name__ == "__main__":
    App().run()
