"""사이트 그림(Codex 원본)의 배경을 지워 public/art/에 투명 webp로 낸다.

사용법 (커플툰 폴더에서):
    python site/tools/make_art.py hero-v1 start-v1 ...   # images/작업중/사이트/<이름>.png
    python site/tools/make_art.py --stickers stickers-v1  # 스티커 시트를 낱장으로 나눈다
    python site/tools/make_art.py --holes bye-v1          # 갇힌 흰 덩어리 지도 (BG_HOLES 고르기)
    python site/tools/make_art.py --og                    # 공유 미리보기 public/og.jpg (hero.webp + 로고)

- 원본: images/작업중/사이트/<이름>.png (Codex가 그린 흰 바탕 그림. site/ 바깥)
- 바탕 지우기: 가장자리에서 이어진 흰 픽셀을 투명하게 (rgba() 설명). 스티커 시트는 회색 바탕을 같은 방식으로 지운다
- 결과: site/public/art/<이름에서 -vN 뺀 것>.webp (투명, 둘레를 잘라내고 긴 변 MAX_SIDE 이하)
- 스티커: 마스크를 덩어리로 나눠 site/public/art/sticker-<STICKERS 이름>.webp
그림 자체는 고치지 않는다. 배경만 투명하게 바꾸고 크기를 줄인다.
"""
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SITE = Path(__file__).resolve().parent.parent
ROOT = SITE.parent
SRC = ROOT / "images" / "작업중" / "사이트"
OUT = SITE / "public" / "art"
MAX_SIDE = 1100
STICKER_SIDE = 260
# 스티커 시트 낱장 이름 (왼쪽 위부터 줄 순서, prompts.md "stickers"와 같은 순서)
STICKERS = ["heart-pink", "heart-blue", "paw-pink", "paw-blue", "bone", "star", "rainbow", "cloud", "ball"]


BG_MIN = 248      # 바탕 흰색: RGB 가장 작은 값이 이 이상 (재어 보니 바탕 252~255, 멍이 털 크림색은 241 안팎)
EDGE_BAND = 2     # 바탕과 맞닿은 이 폭(px)만 흰색을 빼서 반투명으로 (외곽선 안티에일리어싱)
# 테두리에 안 닿은 흰 덩어리 중 실제로 바탕인 곳(팔·몸 사이로 보이는 바탕)을 그림마다 점 하나로 짚는다.
# 크기로 자동 판단하면 댕이 흰 앞머리·꼬리 끝·신발 밑창까지 지워져서 손으로 고른다 (2026-11-26 사용자 지적).
# 갇힌 흰 덩어리 지도: python site/tools/make_art.py --holes 이름
BG_HOLES = {
    "bye-v1": [(592, 406), (638, 772), (615, 1067), (874, 444)],  # 둘 사이 어깨·다리 사이, 댕이 머리와 든 손 사이
    "hero-v1": [(847, 933)],  # 댕이 두 다리 사이
    "start-v1": [(493, 564)],  # 허리에 짚은 팔과 몸 사이
    "episodes-v1": [(774, 596)],  # 멍이 팔과 댕이 손(폰) 사이
}
SPECK_MAX = 150   # 이보다 작은 갇힌 흰 조각이 바탕에서 SPECK_NEAR px 안이면 바탕으로 (동작선 사이·외곽선 안티에일리어싱 틈)
SPECK_NEAR = 6    # 눈 하이라이트·이빨처럼 얼굴 안쪽 흰 점은 바탕에서 멀어서 남는다


def rgba(src, grey=False):
    """흰 바탕 지우기: 그림 가장자리에서 이어진 흰 픽셀(바탕)을 투명하게.
    AI 마스크(BiRefNet)는 흰 털·흰 신발을 바탕과 헷갈려 덩어리를 남기거나 지워서 쓰지 않는다 (2026-11-26).
    """
    from scipy import ndimage
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    mn = a.min(axis=2)
    if grey:
        # 스티커 시트: 회색 바탕(약 #9A9A9A). 스티커 둘레는 흰 테두리라 회색과 섞이지 않는다
        white = (a.max(axis=2) - mn < 12) & (mn > 110) & (a.max(axis=2) < 175)
    else:
        white = mn >= BG_MIN
    lab, n = ndimage.label(white)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, edge[edge > 0])
    seeds = [] if grey else BG_HOLES.get(src.stem, [])
    for x, y in seeds:
        if not white[y, x]:
            sys.exit(f"{src.name} ({x}, {y})는 흰 바탕이 아니에요")
        bg |= lab == lab[y, x]
    if not grey:
        sizes = ndimage.sum(white, lab, range(1, n + 1))
        near = ndimage.binary_dilation(bg, iterations=SPECK_NEAR)
        small = np.zeros(n + 1, bool)
        small[1:] = sizes < SPECK_MAX
        touched = np.zeros(n + 1, bool)
        touched[np.unique(lab[near & white & ~bg])] = True
        specks = small & touched
        specks[0] = False
        bg |= specks[lab]
        print(f"  {src.name}: 바탕 옆 작은 흰 조각 {int(specks.sum())}개 지움")
    band = np.zeros_like(bg) if grey else ndimage.binary_dilation(bg, iterations=EDGE_BAND) & ~bg
    alpha = np.full(mn.shape, 255.0)
    alpha[bg] = 0
    # 띠 안: 흰색 위에 그린 것으로 보고 흰색을 뺀다 (color to alpha)
    k = (255 - mn[band]) / 255
    alpha[band] = k * 255
    rgb = a.copy()
    kk = np.clip(k, 1e-3, 1)[:, None]
    rgb[band] = np.clip((a[band] - 255 * (1 - kk)) / kk, 0, 255)
    out = np.dstack([rgb, alpha]).round().astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def save(im, path, side):
    im = im.crop(im.getbbox())
    im.thumbnail((side, side), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", quality=88, method=6)
    print(path.relative_to(SITE), im.size)


def stickers(name):
    src = SRC / f"{name}.png"
    im = rgba(src, grey=True)
    a = np.asarray(im.getchannel("A")) > 128
    # 덩어리 나누기 (4방향 flood fill)
    h, w = a.shape
    seen = np.zeros_like(a)
    boxes = []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if a[y, x] and not seen[y, x]:
                stack = [(y, x)]
                seen[y, x] = True
                y0 = y1 = y
                x0 = x1 = x
                n = 0
                while stack:
                    cy, cx = stack.pop()
                    n += 1
                    y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and a[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                if n > (h * w) * 0.002:
                    boxes.append((x0, y0, x1 + 1, y1 + 1))
    rows = sorted(boxes, key=lambda b: (b[1] + b[3]) / 2)
    # 같은 줄끼리 모아 왼쪽부터
    lines, cur = [], []
    for b in rows:
        if cur and (b[1] + b[3]) / 2 - (cur[-1][1] + cur[-1][3]) / 2 > h * 0.12:
            lines.append(cur)
            cur = []
        cur.append(b)
    if cur:
        lines.append(cur)
    order = [b for line in lines for b in sorted(line, key=lambda b: b[0])]
    for old in OUT.glob("sticker-*.webp"):
        old.unlink()
    if len(order) != len(STICKERS):
        sys.exit(f"스티커가 {len(order)}개 나왔어요 ({len(STICKERS)}개여야 해요)")
    for name, b in zip(STICKERS, order):
        pad = 6
        box = (max(b[0] - pad, 0), max(b[1] - pad, 0), min(b[2] + pad, w), min(b[3] + pad, h))
        save(im.crop(box), OUT / f"sticker-{name}.webp", STICKER_SIDE)


def og():
    """공유 미리보기 1200×630: 파스텔 바탕 + 로고(fonts/ 도현) + hero 누끼."""
    from PIL import ImageDraw, ImageFilter, ImageFont
    W, H = 1200, 630
    bg = Image.new("RGB", (W, H), "#FFF6FA")
    blobs = Image.new("RGB", (W, H), "#FFF6FA")
    d = ImageDraw.Draw(blobs)
    for (x, y, r, c) in [(150, 120, 330, "#FFD9E6"), (1050, 90, 320, "#D7E6FF"),
                         (900, 560, 340, "#E9DCFF"), (200, 600, 300, "#FFF1C4")]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)
    bg = blobs.filter(ImageFilter.GaussianBlur(90))
    hero = Image.open(OUT / "hero.webp").convert("RGBA")
    hero.thumbnail((600, 600), Image.LANCZOS)
    bg = bg.convert("RGBA")
    bg.alpha_composite(hero, (W - hero.width - 30, (H - hero.height) // 2))
    font = ImageFont.truetype(str(ROOT / "fonts" / "DoHyeon-Regular.ttf"), 190)
    d = ImageDraw.Draw(bg)
    x = 70
    for ch, col in zip("멍댕툰", ["#4F6E93", "#B9486B", "#2B2140"]):
        d.text((x, 150), ch, font=font, fill=col, stroke_width=10, stroke_fill="#FFFFFF")
        x += d.textlength(ch, font=font)
    small = ImageFont.truetype(str(ROOT / "fonts" / "DoHyeon-Regular.ttf"), 52)
    d.rounded_rectangle((76, 390, 76 + d.textlength("게이커플툰", font=small) + 56, 470), radius=40, fill="#2B2140")
    d.text((104, 400), "게이커플툰", font=small, fill="#FFFFFF")
    out = SITE / "public" / "og.jpg"
    bg.convert("RGB").save(out, "JPEG", quality=86, optimize=True)
    print(out.relative_to(SITE), bg.size)


def holes(name):
    """테두리에 안 닿은 흰 덩어리마다 번호와 안쪽 점을 찍어 보여 준다 (BG_HOLES 고르기용)."""
    from scipy import ndimage
    from PIL import ImageDraw
    src = SRC / f"{name}.png"
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(int)
    white = a.min(axis=2) >= BG_MIN
    lab, n = ndimage.label(white)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    sizes = ndimage.sum(white, lab, range(1, n + 1))
    v = np.asarray(im).copy()
    v[np.isin(lab, list(edge - {0}))] = (60, 60, 60)
    out = Image.fromarray(v)
    d = ImageDraw.Draw(out)
    for i, s in enumerate(sizes, 1):
        if i in edge or s < 500:
            continue
        ys, xs = np.nonzero(lab == i)
        x, y = int(xs[len(xs) // 2]), int(ys[len(ys) // 2])
        d.text((x, y), str(i), fill=(255, 0, 0), stroke_width=3, stroke_fill=(255, 255, 255), font_size=36)
        print(i, (x, y), int(s))
    dst = src.with_name(f"{name}-holes.png")
    out.save(dst)
    print(dst)


def main():
    args = sys.argv[1:]
    if args and args[0] == "--holes":
        holes(args[1])
        return
    if args == ["--og"]:
        og()
        return
    if args and args[0] == "--stickers":
        stickers(args[1])
        return
    for name in args:
        save(rgba(SRC / f"{name}.png"), OUT / (re.sub(r"-v\d+$", "", name) + ".webp"), MAX_SIDE)


if __name__ == "__main__":
    main()
