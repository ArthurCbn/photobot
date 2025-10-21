import sys
from pathlib import Path
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from datetime import datetime
import json
import hashlib
from utils import get_exif_info
from parameters import (
    IMG_EXTENSIONS,
    GROUP_DATA_PATH,
)


assert len(sys.argv) > 1
photos_path = Path(sys.argv[1])


# region UTILS

def feature_hash(feature: dict) -> str:
    """
    Crée un hash unique pour une feature GeoJSON.
    """

    # On convertit la feature en string JSON trié pour que l'ordre des clés ne change rien
    feature_str = json.dumps(feature, sort_keys=True)
    return hashlib.md5(feature_str.encode("utf-8")).hexdigest()

# endregion


# region LOGIC

@st.cache_data
def load_photos(photos_path: Path) -> list[dict] :

    points = []
    for photo_path in set().union(*[set(photos_path.glob(ext)) for ext in IMG_EXTENSIONS]):
        filename = photo_path.name
        lat, lon, date = get_exif_info(photo_path)
        if lat and lon:
            points.append({"nom": filename, "lat": lat, "lon": lon, "date": date})
    
    return points


@st.cache_data
def filter_points(
    points: list[dict],
    start_date: datetime, 
    end_date: datetime) -> list[dict] :

    filtered_points = []
    for p in points:
        if not p["date"]:
            continue
        d = datetime.strptime(p["date"], "%Y:%m:%d %H:%M:%S")
        if start_date <= d.date() <= end_date:
            filtered_points.append(p)

    return filtered_points


@st.cache_data
def get_min_max_dates(points: list[dict]) -> tuple[datetime, datetime] :

    dates = [datetime.strptime(p["date"], "%Y:%m:%d %H:%M:%S") for p in points if p["date"]]
    min_date = min(dates) if dates else None
    max_date = max(dates) if dates else None

    return min_date, max_date


def export_groups(
        drawn_groups: dict,
        existing_groups: list[dict]
) -> list[dict] :

    groups = []
    for feature in drawn_groups.get("all_drawings", []):

        fid = feature_hash(feature)
        geom_type = feature["geometry"]["type"]
        coords = feature["geometry"]["coordinates"]
        props = feature.get("properties", {})
        nom = st.session_state.groups_dict.get(fid, f"Groupe_{fid}")

        if geom_type == "Point" and "radius" in props:
            groups.append({
                "nom": nom,
                "id": fid,
                "type": "circle",
                "latitude": coords[1],
                "longitude": coords[0],
                "rayon_km": props["radius"]/1000
            })
        elif geom_type in ("Polygon", "MultiPolygon"):
            groups.append({
                "nom": nom,
                "id": fid,
                "type": "polygone",
                "coordinates": coords[0]
            })
    
    
    existing_ids = [g.get("id", None) for g in existing_groups]
    
    with open(GROUP_DATA_PATH, "w", encoding="utf-8") as f:
        new_groups = [g for g in groups if g["id"] not in existing_ids]
        new_existing_groups = existing_groups + new_groups
        json.dump({"groups": new_existing_groups}, f, indent=2)
    
    st.success("✅ groups.json actualisé !")

    return new_existing_groups

# endregion


# region WIDGETS

@st.fragment
def render_map(
    filtered_points: list[dict],
    existing_groups: list[dict]
) -> None :

    if len(filtered_points) == 0 :
        return
    
    avg_lat = sum(p["lat"] for p in filtered_points) / len(filtered_points)
    avg_lon = sum(p["lon"] for p in filtered_points) / len(filtered_points)
    
    # After creating the map
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)

    # Existing groups
    if existing_groups:
        for g in existing_groups:
            nom = g.get("nom", "Sans nom")
            gtype = g.get("type", "")
            
            if gtype == "circle":
                folium.Circle(
                    location=[g["latitude"], g["longitude"]],
                    radius=g["rayon_km"] * 1000,
                    color="green",
                    fill=True,
                    fill_opacity=0.3,
                    popup=nom
                ).add_to(m)

            elif gtype == "polygone" and "coordinates" in g:
                coords = g["coordinates"]
                # Folium attend [lat, lon]
                coords_latlon = [(pt[1], pt[0]) for pt in coords]
                folium.Polygon(
                    locations=coords_latlon,
                    color="green",
                    fill=True,
                    fill_opacity=0.3,
                    popup=nom
                ).add_to(m)


    # Add photos
    for p in filtered_points:
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=4,
            color="blue",
            fill=True,
            fill_opacity=0.6,
            popup=f"{p['nom']}"
        ).add_to(m)

    # Add Draw plugin
    Draw(
        export=False,
        filename="data.geojson",
        position="topleft",
        draw_options={
            "polygon": True,
            "circle": True,
            "rectangle": True,
            "circlemarker": False,
            "polyline": False,
            "marker": False
        },
        edit_options={"edit": True}
    ).add_to(m)

    return m


@st.dialog(f"Nom du groupe pour la forme")
def ask_group_name(idx: int) :

    name = st.text_input("Entrez le nom du groupe", key=f"input_{idx}")
    if st.button("Valider", key=f"btn_{idx}") :
        if name.strip() :
            st.session_state.groups_dict[fid] = name
            st.success(f"✅ groupe {name.strip()} créé !")


def groups_sidebar(existing_groups: list[dict]) -> None :

    st.sidebar.title("📂 Groupes existants")

    if len(existing_groups) == 0:
        st.sidebar.info("Aucun groupe enregistré pour le moment.")
    else:
        for g in existing_groups:
            nom = g.get("nom", "Sans nom")
            type_g = g.get("type", "inconnu")
            st.sidebar.markdown(f"**• {nom}** — _{type_g}_")

# endregion


# region MAIN


# region |---| Init

if GROUP_DATA_PATH.exists():
    with open(GROUP_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        existing_groups = data.get("groups", [])
else:
    existing_groups = []

if "existing_groups" not in st.session_state :
    st.session_state.existing_groups = existing_groups


st.title("📸 Carte interactive des photos")
st.set_page_config(layout="wide")

if "groups_dict" not in st.session_state:
    st.session_state.groups_dict = {}  # id_feature -> nom

# endregion

groups_sidebar(existing_groups=st.session_state.existing_groups)

points = load_photos(photos_path)

min_date, max_date = get_min_max_dates(points)

col1, col2 = st.columns(2)
start_date = col1.date_input("📅 Date début", min_value=min_date, max_value=max_date, value=min_date)
end_date = col2.date_input("📅 Date fin", min_value=min_date, max_value=max_date, value=max_date)

filtered_points = filter_points(
    points=points, 
    start_date=start_date,
    end_date=end_date
)

map = render_map(
    filtered_points=filtered_points,
    existing_groups=st.session_state.existing_groups
)
drawn_groups = st_folium(map, width=1400, height=500, returned_objects=["all_drawings"])


if drawn_groups and drawn_groups.get("all_drawings"):

    for feature in drawn_groups["all_drawings"] :
        fid = feature_hash(feature)

        if fid not in st.session_state.groups_dict :
            ask_group_name(fid)

if st.button(label="Exporter les groupes") :
    st.session_state.existing_groups = export_groups(
        drawn_groups=drawn_groups,
        existing_groups=st.session_state.existing_groups
    )
    st.rerun()

# endregion