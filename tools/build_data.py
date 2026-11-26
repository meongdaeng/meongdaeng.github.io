"""사이트에 쓸 데이터(src/data/site.json)와 그림(public/)을 작업 공간 원천 파일에서 만든다.

사용법 (커플툰 폴더에서):
    python site/tools/build_data.py

읽는 곳 (모두 site/ 바깥. 여기서 고르는 것만 site/ 안으로 들어간다):
- episodes/README.md 회차 목록: 상태가 "업로드"이고 업로드 순서가 있는 회차만. 번호·제목·업로드 순서·날짜만 가져간다.
- episodes/NNN-제목/slides/01.png: 올린 회차의 표지. 줄여서 public/covers/NNN.jpg로.
- insights/게시물.csv (운영 세션의 scripts/insights.py가 쓴다): 그 회차 "게시글"의 permalink만. 숫자는 가져가지 않는다.
- 프로필.md: 인스타 이름 칸·소개, 인스타·유튜브 주소.
- images/프로필/프로필-1080.png: 파비콘·공유 미리보기용 프로필 그림.
- 회차 caption.md "## 스레드" 칸의 "올릴 장: 01~NN" 줄 (콘티 세션이 쓴다): 올린 회차의 그 범위 장을
  1080×1350 그대로 public/threads/NNN/01.jpg …로. 스레드 API가 공개 주소에서 이미지를 가져가기 때문이다
  (운영 세션의 scripts/threads.py가 https://meongdaengtoon.com/threads/… 를 쓴다). 사이트 화면에는 링크하지 않는다.
- images/스레드/끝장.png: 스레드 공통 끝장. 있으면 public/threads/end.jpg로.
사이트 꾸밈 그림(public/art/)은 이 스크립트가 아니라 make_art.py가 만든다.

안 올린 회차는 표지·제목 모두 넣지 않고, 목록에서 빠진 회차의 표지 파일은 지운다.
바뀐 것이 없으면 파일을 다시 쓰지 않는다 (git에 변경이 안 생기게).
"""
import csv
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image

SITE = Path(__file__).resolve().parent.parent
ROOT = SITE.parent
EPISODES = ROOT / "episodes"
POSTS = ROOT / "insights" / "게시물.csv"
PROFILE_MD = ROOT / "프로필.md"
PROFILE_IMG = ROOT / "images" / "프로필" / "프로필-1080.png"
THREADS_END = ROOT / "images" / "스레드" / "끝장.png"

DATA = SITE / "src" / "data" / "site.json"
PUBLIC = SITE / "public"
COVERS = PUBLIC / "covers"
THREADS = PUBLIC / "threads"

COVER_W = 540      # 1080×1350 → 540×675 (카드 표지)
PROFILE_W = 320
JPEG_Q = 82
THREADS_Q = 92     # 스레드 장: 글씨가 뭉개지지 않게 높은 화질, 색 줄이기(4:2:0) 없이

ROW = re.compile(r"^\|\s*\[(\d{3})\]\(([^/]+)/storyboard\.md\)\s*\|(.*)\|\s*$")


def write_if_changed(path, data):
    if path.exists() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


def jpeg(src, width):
    im = Image.open(src).convert("RGB")
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
    return buf.getvalue()


def jpeg_full(src):
    im = Image.open(src).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=THREADS_Q, subsampling=0, optimize=True)
    return buf.getvalue()


def threads_range(folder):
    """caption.md "## 스레드" 칸의 "올릴 장: 01~05" → (1, 5). 칸이나 줄이 없으면 None."""
    cap = EPISODES / folder / "caption.md"
    if not cap.exists():
        return None
    text = cap.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.search(r"^## 스레드\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    r = m and re.search(r"올릴 장\s*[:：]?\s*(\d+)\s*[~∼-]\s*(\d+)", m.group(1))
    return (int(r.group(1)), int(r.group(2))) if r else None


def threads_images(eps):
    """올린 회차의 스레드 장과 공통 끝장을 public/threads/에 쓰고, 범위에서 빠진 파일은 지운다."""
    changed, keep, notes = [], set(), []
    for e in eps:
        rng = threads_range(e["folder"])
        if not rng:
            continue
        first, last = rng
        for i in range(first, last + 1):
            src = EPISODES / e["folder"] / "slides" / f"{i:02d}.png"
            if not src.exists():
                notes.append(f"{e['num']} {i:02d}장 원본 없음")
                continue
            dst = THREADS / e["num"] / f"{i:02d}.jpg"
            keep.add(dst)
            if write_if_changed(dst, jpeg_full(src)):
                changed.append(dst)
        notes.append(f"{e['num']} {first:02d}~{last:02d}")
    if THREADS_END.exists():
        dst = THREADS / "end.jpg"
        keep.add(dst)
        if write_if_changed(dst, jpeg_full(THREADS_END)):
            changed.append(dst)
    else:
        notes.append("끝장 없음(건너뜀)")
    if THREADS.exists():
        for f in THREADS.rglob("*"):
            if f.is_file() and f not in keep:
                f.unlink()
                changed.append(f)
        for d in sorted((d for d in THREADS.rglob("*") if d.is_dir()), reverse=True):
            if not any(d.iterdir()):
                d.rmdir()
    return changed, notes


def uploaded_episodes():
    rows = []
    for line in (EPISODES / "README.md").read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        num, folder, rest = m.groups()
        cells = [c.strip() for c in rest.split("|")]
        # 제목 | 소재 | 상태 | 장수 | 업로드 순서 | 업로드 날짜 | 메모
        title, _, status, _, order, day = cells[:6]
        if not status.startswith("업로드") or not order:
            continue
        title = re.sub(r"\s*\(가제\)\s*", " ", title).strip()
        rows.append({"num": num, "folder": folder, "title": title,
                     "order": int(order), "date": day})
    rows.sort(key=lambda r: r["order"])
    return rows


def permalinks():
    if not POSTS.exists():
        return {}
    links = {}
    with POSTS.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("종류") == "게시글" and r.get("permalink"):
                links[r["회차"]] = r["permalink"]
    return links


def code_block_after(text, heading):
    m = re.search(re.escape(heading) + r"\s*\n+```\n(.*?)\n```", text, re.S)
    return m.group(1).strip() if m else ""


def profile():
    t = PROFILE_MD.read_text(encoding="utf-8")
    insta = t.split("## 유튜브")[0]
    yt = t.split("## 유튜브")[1]
    youtube_url = re.search(r"채널 주소:\s*(https://\S+)", yt).group(1)
    handle = re.search(r"핸들:\s*`(@[^`]+)`", yt).group(1)
    insta_url = re.search(r"인스타그램 →\s*(https://\S+)", yt).group(1)
    return {
        "name": code_block_after(insta, "### 이름 칸"),
        "bio": code_block_after(insta, "### 소개").splitlines(),
        "instagram": {"url": insta_url, "handle": "@" + insta_url.rstrip("/").rsplit("/", 1)[1]},
        "youtube": {"url": youtube_url, "handle": handle},
    }


def main():
    eps = uploaded_episodes()
    links = permalinks()
    changed = []

    out = []
    for e in eps:
        cover = COVERS / f"{e['num']}.jpg"
        src = EPISODES / e["folder"] / "slides" / "01.png"
        if not src.exists():
            sys.exit(f"표지가 없어요: {src}")
        if write_if_changed(cover, jpeg(src, COVER_W)):
            changed.append(cover)
        out.append({
            "num": e["num"], "title": e["title"], "order": e["order"], "date": e["date"],
            "cover": f"covers/{e['num']}.jpg",
            "link": links.get(e["folder"]),
        })

    keep = {f"{e['num']}.jpg" for e in eps}
    for f in COVERS.glob("*.jpg"):
        if f.name not in keep:
            f.unlink()
            changed.append(f)

    if write_if_changed(PUBLIC / "profile.jpg", jpeg(PROFILE_IMG, PROFILE_W)):
        changed.append(PUBLIC / "profile.jpg")

    t_changed, t_notes = threads_images(eps)
    changed += t_changed

    data = {"profile": profile(), "start": "000", "episodes": out}
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if write_if_changed(DATA, text.encode("utf-8")):
        changed.append(DATA)

    missing = [e["num"] for e in out if not e["link"]]
    print(f"스레드 이미지: {', '.join(t_notes) if t_notes else '스레드 칸 있는 회차 없음'}")
    print(f"올린 회차 {len(out)}편, 바뀐 파일 {len(changed)}개")
    if missing:
        print("게시글 링크가 아직 없는 회차 (프로필 링크로 대신함):", ", ".join(missing))


if __name__ == "__main__":
    main()
