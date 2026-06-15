import os, sys, shutil, zipfile, subprocess, tempfile, logging
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - Update - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Update")

BASE = Path(__file__).resolve().parent
UPSTREAM_REPO = os.environ.get("UPSTREAM_REPO", "https://github.com/IamElite/sp")
UPSTREAM_BRANCH = os.environ.get("UPSTREAM_BRANCH", "main")
SKIP = {".git", "__pycache__", ".env", "update.py", "SyntaxRealm.sh"}
BACKUP_DIR = BASE / ".backup"


def _safe_cleanup(path: Path):
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink(missing_ok=True)


def _replace_tree(src: Path, dst_base: Path):
    for item in src.iterdir():
        if item.name in SKIP:
            continue
        dst = dst_base / item.name
        if dst.exists():
            backup = BACKUP_DIR / item.name
            _safe_cleanup(backup)
            shutil.move(str(dst), str(backup))
        if item.is_dir():
            shutil.copytree(str(item), str(dst), dirs_exist_ok=True)
        else:
            shutil.copy2(str(item), str(dst))

    if BACKUP_DIR.exists():
        shutil.rmtree(str(BACKUP_DIR), ignore_errors=True)


def _install_apt():
    aptfile = BASE / "Aptfile"
    if not aptfile.exists():
        return
    pkgs = [
        l.strip()
        for l in aptfile.read_text().splitlines()
        if l.strip() and not l.startswith("#")
    ]
    if not pkgs:
        return
    logger.info("Installing system packages: %s", pkgs)
    subprocess.check_call(["apt-get", "update", "-qq"], timeout=60)
    subprocess.check_call(["apt-get", "install", "-y", "-qq"] + pkgs, timeout=120)


def _install_pip():
    req = BASE / "requirements.txt"
    if not req.exists():
        return
    logger.info("Installing Python dependencies...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(req),
            "--quiet",
            "--no-input",
        ],
        timeout=120,
    )


def _fetch_zip(client: httpx.Client) -> bytes:
    clean = UPSTREAM_REPO.rstrip("/")
    if clean.endswith(".git"):
        clean = clean[:-4]
    zip_url = f"{clean}/archive/refs/heads/{UPSTREAM_BRANCH}.zip"
    logger.info("Fetching: %s", zip_url)
    r = client.get(zip_url, follow_redirects=True, timeout=30)
    r.raise_for_status()
    return r.content


def main():
    repo = os.environ.get("UPSTREAM_REPO", "")
    if not repo:
        logger.info("UPSTREAM_REPO not set — skipping update")
        return

    logger.info("Checking for updates...")

    try:
        with httpx.Client() as client:
            zip_data = _fetch_zip(client)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            zip_path = tmp_path / "update.zip"
            zip_path.write_bytes(zip_data)

            extract_dir = tmp_path / "extracted"
            extract_dir.mkdir()

            with zipfile.ZipFile(str(zip_path)) as z:
                z.extractall(str(extract_dir))

            entries = list(extract_dir.iterdir())
            if not entries:
                raise ValueError("Empty archive — nothing to update")

            _replace_tree(entries[0], BASE)

        _install_apt()
        _install_pip()
        logger.info("Update applied successfully!")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning("Branch %s not found (404) — check UPSTREAM_REPO / UPSTREAM_BRANCH", UPSTREAM_BRANCH)
        else:
            logger.error("HTTP %s fetching update", e.response.status_code)
    except httpx.RequestError as e:
        logger.error("Network error fetching update: %s", e)
    except Exception as e:
        logger.error("Update failed: %s", e)
        if BACKUP_DIR.exists():
            logger.info("Restoring previous files from backup...")
            for item in BACKUP_DIR.iterdir():
                dst = BASE / item.name
                _safe_cleanup(dst)
                shutil.move(str(item), str(dst))
            shutil.rmtree(str(BACKUP_DIR), ignore_errors=True)
            logger.info("Restore complete")


if __name__ == "__main__":
    main()
