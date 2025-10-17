import os
import sys
import json
import shutil
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from pathlib import Path

SRC_PATH = Path(__file__).absolute()
REPO_PATH = SRC_PATH.parent
DATA_PATH = REPO_PATH / "data"
GROUP_DATA_PATH = DATA_PATH / "groups.json"

TO_SORT_FOLDER_NAME = "_to_sort"


#region OUTILS EXIF

def get_exif_data(image_path: Path) -> dict:
    """
    Extrait les métadonnées EXIF d'une image.
    """

    try:
        image = Image.open(image_path)
        exif_data = image._getexif() or {}
        exif = {}

        for tag, value in exif_data.items():
            decoded = TAGS.get(tag, tag)
        
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    gps_tag = GPSTAGS.get(t, t)
                    gps_data[gps_tag] = value[t]
                exif["GPSInfo"] = gps_data
        
            else:
                exif[decoded] = value
        
        return exif
    
    except Exception:
        return {}


def get_lat_lon(exif_data: dict) -> tuple[float|None, float|None]:
    """
    Retourne (lat, lon) si disponible.
    """
    
    gps_info = exif_data.get("GPSInfo", {})
    if not gps_info:
        return None, None

    def _convert_to_degrees(value: float) -> float:

        d, m, s = value
        return d[0] / d[1] + m[0] / (60 * m[1]) + s[0] / (3600 * s[1])

    lat = _convert_to_degrees(gps_info.get("GPSLatitude"))
    lon = _convert_to_degrees(gps_info.get("GPSLongitude"))
    
    if gps_info.get("GPSLatitudeRef") != "N":
        lat = -lat
    if gps_info.get("GPSLongitudeRef") != "E":
        lon = -lon

    return lat, lon


def get_photo_date(exif_data: dict) -> datetime:
    """
    Retourne la date de la photo (datetime).
    """

    date_str = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime")
    if not date_str:
        return None
    
    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")

# endregion


# region OUTILS GEO

def haversine(
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
    """
    Calcule la distance en km entre deux points GPS.
    """

    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

# endregion


# region TRI

def photo_is_in_group(
        photo_date: datetime, 
        photo_coords: tuple[float|None, float|None], 
        group: dict
    ) -> bool :

    if group["type"] == "date":
        debut = datetime.fromisoformat(group["debut"])
        fin = datetime.fromisoformat(group["fin"])
        
        return debut <= photo_date <= fin if photo_date else False

    elif group["type"] == "lieu":
        if not photo_coords:
            return False
        lat, lon = photo_coords
        dist = haversine(lat, lon, group["latitude"], group["longitude"])
        
        return dist <= group["rayon_km"]

    return False


def sort_photos(
        photos_path: Path, 
        output_path: Path,
        groups_data_path: Path=GROUP_DATA_PATH
    ) -> None :

    with open(groups_data_path, "r", encoding="utf-8") as f :
        groups_data = json.load(f)["groups"]

    not_sorted = output_path / TO_SORT_FOLDER_NAME
    os.makedirs(not_sorted, exist_ok=True)

    for file_path in photos_path.glob((".jpg", ".jpeg", ".png", ".heic")) :

        filename = file_path.name
        exif = get_exif_data(file_path)
        date = get_photo_date(exif)
        coords = get_lat_lon(exif)

        group = None
        for g in groups_data:
            if photo_is_in_group(date, coords, g):
                group = g
                break

        if not group:
            shutil.move(file_path, not_sorted / filename)
            continue

        # Dossier cible
        group_path = output_path / group["nom"]
        os.makedirs(group_path, exist_ok=True)

        # Si groupe lieu -> sous-dossier par mois
        if group["type"] == "lieu" and date:
            mois = date.strftime("%Y-%m")
            group_path = group_path / mois
            os.makedirs(group_path, exist_ok=True)

        shutil.move(file_path, group_path / filename)

