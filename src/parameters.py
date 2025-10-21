from pathlib import Path
import os

SRC_PATH = Path(__file__).absolute().parent
REPO_PATH = SRC_PATH.parent
DATA_PATH = REPO_PATH / "data"

if not DATA_PATH.exists() :
    os.makedirs(DATA_PATH, exist_ok=True)

GROUP_DATA_PATH = DATA_PATH / "groups.json"

IMG_EXTENSIONS = ["*.jpg", "*.jpeg", "*.png", "*.heic"]