import exifread
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from math import radians, sin, cos, sqrt, atan2
from shapely.geometry import Point, Polygon


# region METADATA

def get_exif_info(image_path: Path) -> tuple[float|None, float|None, datetime] :
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

    if date_str :
        date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    else :
        date_str = date

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

    return lat, lon, date

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

# endregion
