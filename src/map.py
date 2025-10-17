import sys
from pathlib import Path
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from parameters import IMG_EXTENSIONS
from datetime import datetime
import json
from utils import get_exif_info


assert len(sys.argv) > 1
photos_path = Path(sys.argv[1])


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

# endregion


# region WIDGETS

@st.fragment
def render_map(filtered_points) :

    if len(filtered_points) == 0 :
        return
    
    avg_lat = sum(p["lat"] for p in filtered_points) / len(filtered_points)
    avg_lon = sum(p["lon"] for p in filtered_points) / len(filtered_points)
    
    # After creating the map
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)

    # Add points
    for p in filtered_points:
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=4,
            color="blue",
            fill=True,
            fill_opacity=0.6,
            popup=f"{p['nom']}<br>{p['date']}"
        ).add_to(m)

    # Add Draw plugin
    Draw(
        export=True,  # allows exporting drawn shapes
        filename="data.geojson",
        position="topleft",
        draw_options={
            "polyline": True,
            "polygon": True,
            "circle": True,
            "rectangle": True,
            "marker": True,
            "circlemarker": True,
        },
        edit_options={"edit": True}
    ).add_to(m)

    # Display map
    st_folium(m, width=1400, height=500, returned_objects=[])

# endregion


# region MAIN

st.title("📸 Carte interactive des photos")
st.set_page_config(layout="wide")

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

render_map(filtered_points)

# endregion
