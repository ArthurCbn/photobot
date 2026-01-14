from pathlib import Path
import os

SRC_PATH = Path(__file__).absolute().parent.parent
REPO_PATH = SRC_PATH.parent
DATA_PATH = REPO_PATH / "data"

if not DATA_PATH.exists() :
    os.makedirs(DATA_PATH, exist_ok=True)

DRAWN_GROUP_DATA_PATH = DATA_PATH / "drawn_groups.json"
DATE_GROUP_DATA_PATH = DATA_PATH / "date_groups.csv"

IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".heic"]
VIDEO_EXTENSIONS = [".mp4"]