from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "photobot"
APP_AUTHOR = "ArthurCabon"

# region |---| Base directories

DATA_PATH = Path(user_data_dir(APP_NAME, APP_AUTHOR))
DATA_PATH.mkdir(parents=True, exist_ok=True)

DRAWN_GROUP_DATA_PATH = DATA_PATH / "drawn_groups.json"
DATE_GROUP_DATA_PATH = DATA_PATH / "date_groups.csv"

IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".heic"]
VIDEO_EXTENSIONS = [".mp4"]