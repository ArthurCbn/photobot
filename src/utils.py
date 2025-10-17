import exifread
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from math import radians, sin, cos, sqrt, atan2
from shapely.geometry import Point, Polygon


# region METADATA

def get_exif_info(image_path: Path):
    with open(image_path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    def get_value(tag):
        value = tags.get(tag)
        return value.values if value else None

    lat = get_value("GPS GPSLatitude")
    lat_ref = get_value("GPS GPSLatitudeRef")
    lon = get_value("GPS GPSLongitude")
    lon_ref = get_value("GPS GPSLongitudeRef")
    date_taken = tags.get("EXIF DateTimeOriginal")
    date_str = str(date_taken) if date_taken else None

    if not lat or not lon:
        return None, None, date_str

    def _convert(coord):
        d, m, s = coord
        return float(d.num)/float(d.den) + float(m.num)/float(m.den)/60 + float(s.num)/float(s.den)/3600

    lat = _convert(lat)
    lon = _convert(lon)

    if lat_ref != "N" :
        lat = -lat
    if lon_ref != "E" :
        lon = -lon
    return lat, lon, date_str



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
        polygon_points: list[list[float]],
    ) -> bool :

    poly = Polygon(g["coordinates"][0])  # coordinates est un MultiPolygon compatible
    pt = Point(lon, lat)
    
    return poly.contains(pt)

# endregion
