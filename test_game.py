"""ゲームが正しく動くかを自動で確かめるテスト

実行方法:  python test_game.py
最後に「すべてのテストに合格しました」と出れば OK です。
（ウィンドウは開きません。画面を出さずに pygame を動かしています）
"""

import os
import random

os.environ["SDL_VIDEODRIVER"] = "dummy"   # 画面を出さずに pygame を動かす設定

import pygame

from curve import EllipticCurve, is_close
from special_points import SPECIAL_POINTS
import main
import scene_result


def same_point(p, q):
    if p is None or q is None:
        return p is None and q is None
    return is_close(p[0], q[0]) and is_close(p[1], q[1])


def test_addition_rules():
    """足し算のルール（交換法則・結合法則・逆元）が成り立つか"""
    curve = EllipticCurve(-1, 1)
    xs = [-1.2, -0.5, 0.3, 1.1, 1.7, 2.4]
    points = [(x, curve.y_at(x, s)) for x in xs for s in (1, -1)]
    for P in points:
        for Q in points:
            assert same_point(curve.add(P, Q).result, curve.add(Q, P).result)          # P+Q = Q+P
            for R in points[:4]:
                left = curve.add(curve.add(P, Q).result, R).result
                right = curve.add(P, curve.add(Q, R).result).result
                if left is not None and abs(left[0]) < 1e6:
                    assert same_point(left, right)                                    # (P+Q)+R = P+(Q+R)
        assert curve.add(P, (P[0], -P[1])).result is None                             # P + (−P) = O
    print("OK: 足し算のルール")


def test_special_points():
    """special_points.py の点が、書かれた位数でちょうど O に戻るか"""
    for data in SPECIAL_POINTS:
        curve = EllipticCurve(data["a"], data["b"])
        x, y = data["point"]
        assert y * y == x ** 3 + data["a"] * x + data["b"], "点が曲線上にない"
        chain = curve.multiples(data["point"], data["order"])
        assert all(p is not None for p in chain[:-1]), "途中で O になってしまった"
        assert chain[-1] is None, f"{data['order']} 回で O に戻らない"
    print("OK: 特別な点の位数")


def run_frames(app, count=5, dt=0.5):
    for _ in range(count):
        app.scene.update(dt)
        app.scene.draw(app.screen)


def test_all_screens():
    """すべての画面が、エラーなく表示・操作できるか"""
    scene_result.SCORE_FILE = scene_result.Path(os.devnull)   # テストではスコアを保存しない
    app = main.App()
    for name in ("title", "explore", "graph_quiz", "crypto_quiz", "guide", "scores"):
        app.goto(name)
        run_frames(app)

    # ① 体験: 全モード、いろいろな曲線
    app.goto("explore")
    scene = app.scene
    for a in (-4, -2, -1, 0, 1, 3):
        for b in (-3, -1, 0, 1, 3):
            scene.change_curve(EllipticCurve(a, b))
            for mode in ("add", "double", "multiple"):
                scene.set_mode(mode)
                run_frames(app, 2, 1.5)

    # ② グラフクイズ: 10問すべて答えて結果画面まで進む
    app.goto("graph_quiz")
    for _ in range(10):
        scene = app.scene
        scene.answer(scene.question.answer_index)
        run_frames(app, 3)
        scene.next_question()
    assert type(app.scene).__name__ == "ResultScene"
    assert app.scene.score > 0

    # ③ 暗号クイズ: ヒントを何回か使い、答えを確かめながら5問進む
    for _ in range(20):
        app.goto("crypto_quiz")
        for _ in range(5):
            scene = app.scene
            assert same_point(scene.Q, scene.curve.multiples(scene.P, scene.k)[-1]), "Q が kP になっていない"
            for _ in range(random.randint(0, 9)):
                if scene.hint_button.enabled:
                    scene.hint_button.press()
                    run_frames(app, 3, 1.0)
            scene.answer(scene.k)
            assert scene.is_correct and scene.gained >= 10
            run_frames(app, 2)
            scene.next_question()
        assert type(app.scene).__name__ == "ResultScene"

    # ガイド: 全ページ
    app.goto("guide")
    for _ in range(10):
        app.scene.turn_page(1)
        run_frames(app, 1)
    pygame.quit()
    print("OK: すべての画面")


if __name__ == "__main__":
    test_addition_rules()
    test_special_points()
    test_all_screens()
    print("すべてのテストに合格しました")
