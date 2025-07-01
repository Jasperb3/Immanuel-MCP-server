"""
Utilities - Helper functions for coordinate parsing, timezone handling, etc.
"""

import re
import pytz
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union
from functools import lru_cache


def parse_coordinates(coord_str: str, coord_type: str) -> Tuple[float, str]:
    """
    Parse coordinate string into decimal degrees and direction.

    Supports formats:
    - "32.72N" or "32.72S" for latitude
    - "117.16W" or "117.16E" for longitude
    - "-32.72" (negative for S/W)
    - "32N43'12\"" (degrees, minutes, seconds)

    Args:
        coord_str: Coordinate string to parse
        coord_type: Either 'latitude' or 'longitude'

    Returns:
        Tuple of (decimal_degrees, direction)
    """
    coord_str = coord_str.strip()

    # Check for decimal degrees with direction letter
    if coord_str[-1] in "NSEW":
        direction = coord_str[-1]
        value_str = coord_str[:-1]

        # Check if it's simple decimal
        if "." in value_str and value_str.replace(".", "").replace("-", "").isdigit():
            value = float(value_str)
        else:
            # Try to parse DMS format
            value = parse_dms(value_str)

        # Apply direction
        if direction in "SW":
            value = -abs(value)
        else:
            value = abs(value)

    else:
        # Plain decimal degrees
        value = float(coord_str)
        if coord_type == "latitude":
            direction = "N" if value >= 0 else "S"
        else:
            direction = "E" if value >= 0 else "W"

    # Validate ranges
    if coord_type == "latitude" and not -90 <= value <= 90:
        raise ValueError(f"Latitude must be between -90 and 90: {value}")
    elif coord_type == "longitude" and not -180 <= value <= 180:
        raise ValueError(f"Longitude must be between -180 and 180: {value}")

    return value, direction


def parse_dms(dms_str: str) -> float:
    """
    Parse degrees, minutes, seconds format to decimal degrees.

    Formats supported:
    - "32°43'12\""
    - "32 43 12"
    - "32d43m12s"
    - "32:43:12"
    """
    # Remove common symbols and replace with spaces
    cleaned = re.sub(r"[°\'\"dmsh:]+", " ", dms_str)
    parts = cleaned.split()

    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        deg, min = map(float, parts)
        return deg + min / 60
    elif len(parts) == 3:
        deg, min, sec = map(float, parts)
        return deg + min / 60 + sec / 3600
    else:
        raise ValueError(f"Cannot parse DMS format: {dms_str}")


def normalize_timezone(tz_str: Optional[str]) -> str:
    """
    Normalize timezone string to a valid pytz timezone.

    Args:
        tz_str: Timezone string (e.g., "America/Los_Angeles", "PST", "UTC-8")

    Returns:
        Valid pytz timezone string
    """
    if not tz_str:
        return "UTC"

    # Direct match
    if tz_str in pytz.all_timezones:
        return tz_str

    # Common abbreviations
    tz_abbrev_map = {
        "PST": "America/Los_Angeles",
        "PDT": "America/Los_Angeles",
        "MST": "America/Denver",
        "MDT": "America/Denver",
        "CST": "America/Chicago",
        "CDT": "America/Chicago",
        "EST": "America/New_York",
        "EDT": "America/New_York",
        "GMT": "UTC",
        "BST": "Europe/London",
        "CET": "Europe/Paris",
        "CEST": "Europe/Paris",
    }

    if tz_str.upper() in tz_abbrev_map:
        return tz_abbrev_map[tz_str.upper()]

    # Try to find partial match
    tz_lower = tz_str.lower()
    for tz in pytz.all_timezones:
        if tz_lower in tz.lower():
            return tz

    # UTC offset format (e.g., "UTC-8", "+05:30")
    offset_match = re.match(r"UTC?([+-]\d{1,2}):?(\d{2})?", tz_str, re.IGNORECASE)
    if offset_match:
        hours = int(offset_match.group(1))
        minutes = int(offset_match.group(2) or 0)

        # Find timezone with matching offset
        # This is approximate as DST can change offsets
        target_offset = hours * 60 + (minutes if hours >= 0 else -minutes)

        now = datetime.now()
        for tz in pytz.all_timezones:
            try:
                tz_obj = pytz.timezone(tz)
                offset = tz_obj.utcoffset(now).total_seconds() / 60
                if abs(offset - target_offset * 60) < 30:  # Within 30 minutes
                    return tz
            except:
                continue

    # Default to UTC if nothing matches
    return "UTC"


def validate_timezone(tz_str: str) -> bool:
    """Check if timezone string is valid."""
    try:
        normalized = normalize_timezone(tz_str)
        return normalized in pytz.all_timezones
    except:
        return False


@lru_cache(maxsize=1000)
def calculate_cache_key(data: str) -> str:
    """
    Calculate a cache key from JSON-serializable data.

    Args:
        data: JSON string of the data to cache

    Returns:
        SHA256 hash hex string
    """
    return hashlib.sha256(data.encode()).hexdigest()


def format_decimal_to_dms(decimal: float, coord_type: str) -> str:
    """
    Format decimal degrees to degrees, minutes, seconds string.

    Args:
        decimal: Decimal degrees value
        coord_type: 'latitude' or 'longitude'

    Returns:
        Formatted string like "32°43'12\"N"
    """
    direction = ""
    if coord_type == "latitude":
        direction = "N" if decimal >= 0 else "S"
    else:
        direction = "E" if decimal >= 0 else "W"

    decimal = abs(decimal)
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = int((decimal - degrees - minutes / 60) * 3600)

    return f"{degrees}°{minutes:02d}'{seconds:02d}\"{direction}"


def zodiac_position_to_string(longitude: float) -> str:
    """
    Convert ecliptic longitude to zodiac position string.

    Args:
        longitude: Ecliptic longitude in degrees (0-360)

    Returns:
        String like "15°30' Aries"
    """
    signs = [
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
    ]

    sign_index = int(longitude / 30)
    degrees_in_sign = longitude % 30
    degrees = int(degrees_in_sign)
    minutes = int((degrees_in_sign - degrees) * 60)

    return f"{degrees}°{minutes:02d}' {signs[sign_index]}"


def aspect_symbol(aspect_name: str) -> str:
    """Get the astrological symbol for an aspect."""
    symbols = {
        "conjunction": "☌",
        "opposition": "☍",
        "trine": "△",
        "square": "□",
        "sextile": "⚹",
        "quincunx": "⚻",
        "semisquare": "∠",
        "sesquiquadrate": "⚼",
        "semisextile": "⚺",
        "quintile": "Q",
        "biquintile": "bQ",
    }
    return symbols.get(aspect_name.lower(), aspect_name)


def planet_symbol(planet_name: str) -> str:
    """Get the astrological symbol for a planet."""
    symbols = {
        "sun": "☉",
        "moon": "☽",
        "mercury": "☿",
        "venus": "♀",
        "mars": "♂",
        "jupiter": "♃",
        "saturn": "♄",
        "uranus": "♅",
        "neptune": "♆",
        "pluto": "♇",
        "north_node": "☊",
        "south_node": "☋",
        "chiron": "⚷",
        "lilith": "⚸",
        "ceres": "⚳",
        "pallas": "⚴",
        "juno": "⚵",
        "vesta": "⚶",
    }
    return symbols.get(planet_name.lower(), planet_name)


def sign_symbol(sign_name: str) -> str:
    """Get the astrological symbol for a zodiac sign."""
    symbols = {
        "aries": "♈",
        "taurus": "♉",
        "gemini": "♊",
        "cancer": "♋",
        "leo": "♌",
        "virgo": "♍",
        "libra": "♎",
        "scorpio": "♏",
        "sagittarius": "♐",
        "capricorn": "♑",
        "aquarius": "♒",
        "pisces": "♓",
    }
    return symbols.get(sign_name.lower(), sign_name)


def calculate_orb(angle1: float, angle2: float, aspect_angle: float) -> float:
    """
    Calculate the orb (difference) between actual angle and exact aspect angle.

    Args:
        angle1: First object's longitude
        angle2: Second object's longitude
        aspect_angle: Exact angle for the aspect (0, 60, 90, 120, 180)

    Returns:
        Orb in degrees
    """
    # Calculate the angular distance
    distance = abs(angle1 - angle2)
    if distance > 180:
        distance = 360 - distance

    # Calculate orb from exact aspect
    orb = abs(distance - aspect_angle)

    return orb


def is_applying_aspect(
    obj1_longitude: float,
    obj1_speed: float,
    obj2_longitude: float,
    obj2_speed: float,
    aspect_angle: float,
) -> bool:
    """
    Determine if an aspect is applying (getting closer) or separating.

    Args:
        obj1_longitude: First object's longitude
        obj1_speed: First object's daily motion
        obj2_longitude: Second object's longitude
        obj2_speed: Second object's daily motion
        aspect_angle: Exact angle for the aspect

    Returns:
        True if applying, False if separating
    """
    # Current angular distance
    current_distance = abs(obj1_longitude - obj2_longitude)
    if current_distance > 180:
        current_distance = 360 - current_distance

    # Future positions (simplified - 1 day ahead)
    future_obj1 = obj1_longitude + obj1_speed
    future_obj2 = obj2_longitude + obj2_speed

    # Future angular distance
    future_distance = abs(future_obj1 - future_obj2)
    if future_distance > 180:
        future_distance = 360 - future_distance

    # Current and future orbs
    current_orb = abs(current_distance - aspect_angle)
    future_orb = abs(future_distance - aspect_angle)

    # Applying if future orb is smaller
    return future_orb < current_orb


def format_aspect_string(
    obj1: str, aspect: str, obj2: str, orb: float, applying: Optional[bool] = None
) -> str:
    """
    Format an aspect as a readable string.

    Args:
        obj1: First object name
        aspect: Aspect name
        obj2: Second object name
        orb: Orb in degrees
        applying: Whether aspect is applying

    Returns:
        Formatted string like "Sun ☌ Moon (2°30' applying)"
    """
    obj1_sym = planet_symbol(obj1)
    obj2_sym = planet_symbol(obj2)
    aspect_sym = aspect_symbol(aspect)

    orb_deg = int(orb)
    orb_min = int((orb - orb_deg) * 60)

    result = f"{obj1_sym} {aspect_sym} {obj2_sym} ({orb_deg}°{orb_min:02d}'"

    if applying is not None:
        result += " applying" if applying else " separating"

    result += ")"

    return result


class ChartDataValidator:
    """Validate chart data structure"""

    @staticmethod
    def validate_chart_data(data: Dict[str, Any]) -> bool:
        """Check if chart data has required structure."""
        required_keys = ["metadata", "objects"]

        # Check top-level keys
        for key in required_keys:
            if key not in data:
                return False

        # Check objects structure
        if not isinstance(data["objects"], dict):
            return False

        # Check each object has required fields
        for obj_name, obj_data in data["objects"].items():
            if not isinstance(obj_data, dict):
                return False

            required_obj_keys = ["longitude", "sign"]
            for key in required_obj_keys:
                if key not in obj_data:
                    return False

        return True

    @staticmethod
    def validate_natal_data(data: Dict[str, Any]) -> bool:
        """Validate natal chart data specifically."""
        if not ChartDataValidator.validate_chart_data(data):
            return False

        # Check for houses
        if "houses" not in data:
            return False

        # Validate house structure
        for house_key, house_data in data.get("houses", {}).items():
            if not isinstance(house_data, dict):
                return False
            if "number" not in house_data or "sign" not in house_data:
                return False

        return True


def interpolate_positions(start_pos: float, end_pos: float, fraction: float) -> float:
    """
    Interpolate between two zodiac positions.

    Args:
        start_pos: Starting longitude (0-360)
        end_pos: Ending longitude (0-360)
        fraction: Fraction of the way from start to end (0-1)

    Returns:
        Interpolated longitude
    """
    # Handle zodiac wraparound
    diff = end_pos - start_pos

    # If the difference is more than 180°, go the other way
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360

    # Interpolate
    result = start_pos + (diff * fraction)

    # Normalize to 0-360
    while result < 0:
        result += 360
    while result >= 360:
        result -= 360

    return result
