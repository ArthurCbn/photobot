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
        date_groups: list[dict],
        existing_groups: list[dict]
) -> list[dict] :

    groups = []

    # Date groups
    for g in date_groups :

        fid = g["id"]
        name = st.session_state.groups_dict.get(fid, f"Groupe_{fid}")
        new_group =  g | {"nom": name}
        groups.append(new_group)

    # Map groups
    for feature in ( drawn_groups.get("all_drawings", []) or [] ) :

        fid = feature_hash(feature)
        geom_type = feature["geometry"]["type"]
        coords = feature["geometry"]["coordinates"]
        props = feature.get("properties", {})
        name = st.session_state.groups_dict.get(fid, f"Groupe_{fid}")

        if geom_type == "Point" and "radius" in props:
            groups.append({
                "nom": name,
                "id": fid,
                "type": "circle",
                "latitude": coords[1],
                "longitude": coords[0],
                "rayon_km": props["radius"]/1000
            })
        elif geom_type in ("Polygon", "MultiPolygon"):
            groups.append({
                "nom": name,
                "id": fid,
                "type": "polygone",
                "coordinates": coords[0]
            })
    
    
    existing_ids = [g.get("id", None) for g in existing_groups]
    new_groups = [g for g in groups if g["id"] not in existing_ids]

    if not new_groups :
        st.warning("⚠️ pas de nouveau groupe...")
        return existing_groups
    
    with open(GROUP_DATA_PATH, "w", encoding="utf-8") as f:
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


@st.dialog(f"Nom du groupe")
def ask_group_name(idx: str) -> str :

    name = st.text_input("Entrez le nom du groupe", key=f"input_{idx}")
    if st.button("Valider", key=f"btn_{idx}") :
        if name.strip() :
            st.session_state.groups_dict[idx] = name
            st.success(f"✅ Groupe {name.strip()} créé !")
            st.rerun()


def groups_sidebar(existing_groups: list[dict]) -> None :

    st.sidebar.title("📂 Groupes existants")

    if len(existing_groups) == 0:
        st.sidebar.info("Aucun groupe enregistré pour le moment.")
    else:
        for g in existing_groups:
            nom = g.get("nom", "Sans nom")
            type_g = g.get("type", "inconnu")
            st.sidebar.markdown(f"**• {nom}** — _{type_g}_")


def create_date_group(
        start_date: datetime, 
        end_date: datetime,
        existing_groups: list[dict]
) -> None :
    """
    Crée un groupe de type 'date' dans le fichier groups.json
    basé sur les dates sélectionnées dans l'interface.
    """
    
    to_hash = f"Dates_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
    hash = hashlib.md5(to_hash.encode("utf-8")).hexdigest()

    existing_ids = [g.get("id") for g in existing_groups] + list(st.session_state.groups_dict.keys())
    if hash in existing_ids :
        st.warning("⚠️ Ce groupe de dates existe déjà.")
        return
    

    new_group = {
        "nom": None,
        "id": hash,
        "type": "date",
        "date_debut": start_date.strftime("%Y-%m-%d"),
        "date_fin": end_date.strftime("%Y-%m-%d"),
    }
    st.session_state.new_date_groups.append(new_group)

    ask_group_name(hash)

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

if "new_date_groups" not in st.session_state :
    st.session_state.new_date_groups = []

# endregion

groups_sidebar(existing_groups=st.session_state.existing_groups)

points = load_photos(photos_path)

min_date, max_date = get_min_max_dates(points)

col1, col2, col3 = st.columns(3, vertical_alignment="bottom")
start_date = col1.date_input("📅 Date début", min_value=min_date, max_value=max_date, value=min_date)
end_date = col2.date_input("📅 Date fin", min_value=min_date, max_value=max_date, value=max_date)

if col3.button("✅ Créer un groupe de date", use_container_width=True) :
    create_date_group(
        start_date=start_date,
        end_date=end_date,
        existing_groups=st.session_state.existing_groups
    )

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
        date_groups=st.session_state.new_date_groups,
        existing_groups=st.session_state.existing_groups
    )
    st.rerun()

# endregion