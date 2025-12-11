import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from photobot.parameters import (
    GROUP_DATA_PATH,
    IMG_EXTENSIONS,
    VIDEO_EXTENSIONS
)
from photobot.utils import (
    get_jpg_metadata,
    get_mp4_metadata,
    haversine,
    is_in_polygon,
    sort_groups,
)


# region TRI

def media_is_in_group(
        media_date: datetime, 
        media_coords: tuple[float|None, float|None], 
        group: dict
    ) -> bool :

    if group["type"] == "date":
        debut = datetime.fromisoformat(group["debut"])
        fin = datetime.fromisoformat(group["fin"])
        
        return debut <= media_date <= fin if media_date else False

    if not media_coords :
        return False

    lat, lon = media_coords
    if (lat is None) or (lon is None)  :
        return False

    if group["type"] == "circle":
        dist = haversine(lat, lon, group["latitude"], group["longitude"])
        return dist <= group["rayon_km"]
    
    if group["type"] == "polygone" :
        return is_in_polygon(lat, lon, group["coordinates"])

    return False


def sort_medias(
        medias_path: Path, 
        output_path: Path,
        groups_data_path: Path=GROUP_DATA_PATH
    ) -> None :

    with open(groups_data_path, "r", encoding="utf-8") as f :
        groups_data = sort_groups(json.load(f)["groups"])

    for file_path in set().union(*[medias_path.glob(f"*{suffix}") for suffix in IMG_EXTENSIONS + VIDEO_EXTENSIONS]) :

        filename = file_path.name
        suffix = file_path.suffix

        if suffix in IMG_EXTENSIONS :
            lat, lon, date = get_jpg_metadata(file_path)
        elif suffix in VIDEO_EXTENSIONS :
            lat, lon, date = get_mp4_metadata(file_path)
        
        coords = (lat, lon)

        group = None
        for g in groups_data:
            if media_is_in_group(date, coords, g):
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

