from pathlib import Path

SRC_PATH = Path(__file__).absolute().parent
REPO_PATH = SRC_PATH.parent
DATA_PATH = REPO_PATH / "data"

GROUP_DATA_PATH = DATA_PATH / "groups.json"

IMG_EXTENSIONS = ["*.jpg", "*.jpeg", "*.png", "*.heic"]