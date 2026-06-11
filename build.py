from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent
SOURCE_STATIC_DIR = ROOT / "static"
PUBLIC_DIR = ROOT / "public"
TARGET_STATIC_DIR = PUBLIC_DIR / "static"


def copy_static_assets() -> None:
    if TARGET_STATIC_DIR.exists():
        shutil.rmtree(TARGET_STATIC_DIR)

    TARGET_STATIC_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE_STATIC_DIR, TARGET_STATIC_DIR)


if __name__ == "__main__":
    copy_static_assets()
