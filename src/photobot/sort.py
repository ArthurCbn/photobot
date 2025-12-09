import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from photobot.parameters import (
    GROUP_DATA_PATH,
    IMG_EXTENSIONS
)
from photobot.utils import (
    get_exif_info,
    haversine,
    is_in_polygon,
    sort_groups,
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
        groups_data = sort_groups(json.load(f)["groups"])

    for file_path in set().union(*[set(photos_path.glob(extension)) for extension in IMG_EXTENSIONS]) :

        filename = file_path.name
        lat, lon, date = get_exif_info(file_path)
        coords = (lat, lon)

        group = None
        for g in groups_data:
            if photo_is_in_group(date, coords, g):
                group = g
                break

        if not group:
            continue

        if date:
            year = date.strftime("%Y")
            year_path = output_path / year
        else:
            year_path = output_path / "inconnue"

        os.makedirs(year_path, exist_ok=True)

        # Dossier cible
        group_path = year_path / group["nom"]
        os.makedirs(group_path, exist_ok=True)

        # Si groupe lieu -> sous-dossier par mois
        if group["type"] != "date" and date:
            mois = date.strftime("%m")
            group_path = group_path / mois
            os.makedirs(group_path, exist_ok=True)

        shutil.move(file_path, group_path / filename)

