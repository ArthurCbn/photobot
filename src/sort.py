import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from parameters import (
    GROUP_DATA_PATH,
    TO_SORT_FOLDER_NAME,
    IMG_EXTENSIONS
)
from utils import (
    get_exif_data,
    get_lat_lon,
    get_photo_date,
    haversine,
    is_in_polygon,
)


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

    elif group["type"] == "circle":
        if not photo_coords:
            return False
        lat, lon = photo_coords
        dist = haversine(lat, lon, group["latitude"], group["longitude"])
        
        return dist <= group["rayon_km"]
    
    elif group["type"] == "polygone" :
        if not photo_coords:
            return False
        lat, lon = photo_coords

        return is_in_polygon(lat, lon, group["coordinates"])

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

    for file_path in set().union(*[set(photos_path.glob(extension)) for extension in IMG_EXTENSIONS]) :

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

