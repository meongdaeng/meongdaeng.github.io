"""사이트 회차 목록 자동 갱신: 데이터를 다시 만들고, 바뀌었으면 데이터 파일만 커밋해 푸시한다.

윈도우 작업 스케줄러 "멍댕툰 사이트 갱신"이 매일 17:40에 창 없이 돌린다 (꺼져 있었으면 켠 뒤 바로).
손으로 돌릴 때 (커플툰 폴더 어디서든):
    python site/tools/auto_update.py

순서
1. 인사이트 기다리기: 17:30 "멍댕툰 인사이트"가 insights/게시물.csv(인스타 링크)를 새로 쓴 뒤에 돌아야
   새 회차에 링크가 붙는다. 컴퓨터를 늦게 켜면 두 작업이 같이 시작되므로, 오늘 17:30 이후 게시물.csv가
   갱신됐고 인사이트 작업이 돌고 있지 않을 때까지 30초마다 확인하며 기다린다. 20분이 지나면 있는 자료로 진행한다.
2. tools/build_data.py로 src/data/site.json, public/covers/, public/profile.jpg를 다시 만든다.
3. 그 데이터 파일만 커밋한다 (사이트 세션이 고치던 다른 파일은 건드리지 않는다). 바뀐 게 없으면 끝.
4. origin(main)에 푸시한다. 키는 저장소 설정 core.sshCommand의 배포 키. GitHub Actions가 배포한다.

기록: %LOCALAPPDATA%\\meongdaeng\\site-update.log (site/ 밖. 공개되지 않는다)
"""
import datetime as dt
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
ROOT = SITE.parent
POSTS = ROOT / "insights" / "게시물.csv"
INSIGHTS_TASK = "멍댕툰 인사이트"
INSIGHTS_AT = dt.time(17, 30)
WAIT_STEP = 30          # 초
WAIT_MAX = 20 * 60      # 초
DATA_PATHS = ["src/data/site.json", "public/covers", "public/profile.jpg"]
LOG = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "meongdaeng" / "site-update.log"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(msg):
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    if sys.stdout:
        print(line)


def run(args, cwd=SITE, check=True):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", creationflags=NO_WINDOW)
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args))} 실패 ({p.returncode}): {p.stderr.strip() or p.stdout.strip()}")
    return p


def insights_running():
    p = run(["schtasks", "/query", "/tn", INSIGHTS_TASK, "/fo", "csv", "/nh"], check=False)
    return p.returncode == 0 and ("Running" in p.stdout or "실행 중" in p.stdout)


def insights_done_today():
    now = dt.datetime.now()
    since = dt.datetime.combine(now.date(), INSIGHTS_AT)
    if now < since:
        return True  # 17:30 전에 손으로 돌리면 오늘 몫은 아직이니 기다리지 않는다
    return POSTS.exists() and dt.datetime.fromtimestamp(POSTS.stat().st_mtime) >= since


def wait_for_insights():
    waited = 0
    while waited < WAIT_MAX:
        if insights_done_today() and not insights_running():
            if waited:
                log(f"인사이트 끝난 것 확인 ({waited}초 기다림)")
            return
        time.sleep(WAIT_STEP)
        waited += WAIT_STEP
    log(f"인사이트를 {WAIT_MAX // 60}분 기다렸지만 오늘 게시물.csv가 없다. 있는 자료로 진행 (새 회차 링크는 다음 날 채워진다)")


def main():
    log(f"시작 (기록 {LOG})")
    wait_for_insights()
    p = run([sys.executable.replace("pythonw.exe", "python.exe"), "-X", "utf8", str(SITE / "tools" / "build_data.py")], cwd=ROOT)
    for line in (p.stdout or "").strip().splitlines()[-3:]:
        log(f"  build_data: {line}")
    run([GIT, "add", "--", *DATA_PATHS])
    changed = run([GIT, "diff", "--cached", "--name-only", "--", *DATA_PATHS]).stdout.split()
    if not changed:
        log("바뀐 것 없음. 끝")
        return
    log(f"바뀐 파일 {len(changed)}개: {', '.join(changed[:6])}{' …' if len(changed) > 6 else ''}")
    msg = (f"회차 목록 자동 갱신 ({dt.date.today():%Y-%m-%d})\n\n"
           "tools/auto_update.py가 episodes/README.md·insights/게시물.csv에서 다시 만든 데이터.\n")
    run([GIT, "commit", "-q", "-m", msg, "--", *DATA_PATHS])
    run([GIT, "push", "-q", "origin", "main"])
    log("커밋·푸시 끝. GitHub Actions가 배포한다")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("오류:\n" + traceback.format_exc())
        sys.exit(1)
