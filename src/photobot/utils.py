import exifread
from pathlib import Path
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2, log, tan, pi
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import exiftool
import re


def parse_date_from_stem(stem: str) -> datetime|None :
    date_str = None
    
    pattern = r"^\d{4}-\d{2}-\d{2} \d{2}\.\d{2}\.\d{2}.*"
    if re.match(pattern, stem) :
        date_str = stem[:19]
        date_str = date_str.replace(".", ":")
        date_str = date_str.replace("-", ":")
    
    date = None
    if date_str:
        try :
            date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except :
            pass
    
    return date


# region METADATA

# region |---| JPG

def get_jpg_metadata(image_path: Path) -> tuple[float|None, float|None, datetime|None] :
    with open(image_path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    def get_value(tag, tags=tags):
        value = tags.get(tag)
        return value.values if value else None

    lat = get_value("GPS GPSLatitude")
    lat_ref = get_value("GPS GPSLatitudeRef")
    lon = get_value("GPS GPSLongitude")
    lon_ref = get_value("GPS GPSLongitudeRef")

    date = parse_date_from_stem(image_path.stem)
    if date is None :
        date_taken = tags.get("EXIF DateTimeOriginal")
        date_str = str(date_taken).strip() if date_taken else None
    
        date = None
        if date_str :
            date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")

    if not lat or not lon:
        return None, None, date

    def _convert(coord):
        d, m, s = coord
        return float(d.num)/float(d.den) + float(m.num)/float(m.den)/60 + float(s.num)/float(s.den)/3600

    lat = _convert(lat)
    lon = _convert(lon)

    if lat_ref != "N" :
        lat = -lat
    if lon_ref != "E" :
        lon = -lon

    return lat, lon, date

# endregion

# region |---| MP4

def get_mp4_metadata(path: Path) -> tuple[float|None, float|None, datetime|None]:
    """
    Extrait latitude, longitude et datetime d'une vidéo en utilisant ExifTool.
    Fonction robuste et standardisée.
    """

    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata(str(path))[0]

    lat = metadata.get("Composite:GPSLatitude")
    lon = metadata.get("Composite:GPSLongitude")
    
    date = parse_date_from_stem(path.stem)

    if date :
        return lat, lon, date

    date_str = (
        metadata.get("QuickTime:CreationDate")
        or metadata.get("QuickTime:CreateDate")
        or metadata.get("EXIF:DateTimeOriginal")
        or metadata.get("QuickTime:ContentCreateDate")
    )
    # ExifTool renvoie souvent un format : "2022:03:18 14:22:05Z"
    date_str = date_str.replace("Z", "+00:00")

    if date_str:
        try :
            date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except : # Year 0 for instance
            pass 

    return lat, lon, date

# endregion

# endregion


# region GEO

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


def is_in_polygon(
        lat: float,
        lon: float,
        polygon_points: list[float],
    ) -> bool :

    poly = Polygon(polygon_points)  # coordinates est un MultiPolygon compatible
    pt = Point(lon, lat)
    
    return poly.contains(pt)


def polygon_area_km2(coords: tuple[float, float]) -> float :

    # Conversion lat/lon -> WebMercator (en mètres)
    def _lonlat_to_mercator(
            lon: float, 
            lat: float
    ) -> tuple[float, float] :

        R = 6378137  # rayon sphère WGS84
        x = R * radians(lon)
        y = R * log(tan(pi/4 + radians(lat)/2))

        return x, y


    poly = Polygon([(lon, lat) for lon, lat in coords])

    # reprojection vers WebMercator
    poly_merc = transform(
        lambda x, y: _lonlat_to_mercator(x, y),
        poly
    )

    return poly_merc.area / 1_000_000  # m² -> km²


def circle_area_km2(rayon_km: float) -> float :
    return pi * rayon_km**2


def date_duration_days(
        date1: str,
        date2: str
) -> float :

    try :
        d1 = datetime.strptime(date1, "%Y-%m-%d %H.%M.%S")
    except :
        d1 = datetime.strptime(date1, "%Y-%m-%d")
    try :
        d2 = datetime.strptime(date2, "%Y-%m-%d %H.%M.%S")
    except :
        d2 = datetime.strptime(date2, "%Y-%m-%d")

    return (d2 - d1).days


def sort_groups(groups: list[dict]) -> list[dict] :

    def key(g: dict) -> tuple[int, float] :

        if g["type"] == "date":
            return (0, date_duration_days(g["date_debut"], g["date_fin"]))
        
        if g["type"] == "polygone":
            return (1, polygon_area_km2(g["coordinates"]))
        
        if g["type"] == "circle":
            return (1, circle_area_km2(g["rayon_km"]))
        
        return (2, 0)

    return sorted(groups, key=key)

# endregion
