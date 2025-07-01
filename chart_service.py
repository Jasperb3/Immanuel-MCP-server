"""
Chart Service - Core logic for interacting with immanuel-python
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

import immanuel
from immanuel import charts
from immanuel.const import chart as chart_const
from immanuel.const import names
from immanuel.tools import date, position

from .models import ChartRequest, ChartResponse, ChartSettings, Subject
from .utils import parse_coordinates, normalize_timezone

logger = logging.getLogger(__name__)


class ChartService:
    """Service for calculating and analyzing astrological charts"""

    def __init__(self, default_settings: Optional[ChartSettings] = None):
        self._cache: Dict[str, ChartResponse] = {}
        self._default_settings = default_settings or ChartSettings()
        self._setup_immanuel()

    def _setup_immanuel(self):
        """Configure immanuel-python settings"""
        # Set default settings
        immanuel.config.set(
            {
                "house_system": getattr(
                    chart_const,
                    self._default_settings.house_system.upper(),
                    chart_const.PLACIDUS,
                ),
                "angles": [chart_const.ASC, chart_const.DESC, chart_const.MC, chart_const.IC],
                "planets": list(chart_const.PLANETS),
                "points": [chart_const.NORTH_NODE, chart_const.SOUTH_NODE, chart_const.VERTEX],
                "asteroids": [],  # Will be added based on user request
            }
        )

    def _get_cache_key(self, subject: Subject, chart_type: str, settings: ChartSettings) -> str:
        """Generate cache key from request parameters"""
        key_data = {
            "datetime": subject.datetime,
            "lat": subject.latitude,
            "lon": subject.longitude,
            "tz": subject.timezone,
            "type": chart_type,
            "settings": settings.dict(),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def calculate_single_chart(
        self, subject: Subject, chart_type: str, settings: ChartSettings
    ) -> ChartResponse:
        """Calculate a single astrological chart"""

        # Check cache
        cache_key = self._get_cache_key(subject, chart_type, settings)
        if cache_key in self._cache:
            logger.info(f"Returning cached chart: {cache_key}")
            return self._cache[cache_key]

        # Parse coordinates
        lat, lat_dir = parse_coordinates(subject.latitude, "latitude")
        lon, lon_dir = parse_coordinates(subject.longitude, "longitude")

        # Create native datetime
        dt = datetime.fromisoformat(subject.datetime.replace("Z", "+00:00"))

        # Normalize timezone
        tz = normalize_timezone(subject.timezone) if subject.timezone else "UTC"

        # Configure immanuel for this chart
        config = self._prepare_config(settings)
        immanuel.config.set(config)

        # Create the subject
        native = immanuel.charts.Subject(date_time=dt, latitude=lat, longitude=lon, timezone=tz)

        # Calculate chart based on type
        chart = self._calculate_chart_by_type(native, chart_type)

        # Build response
        response = self._build_chart_response(chart, subject, chart_type, settings)

        # Cache result
        self._cache[cache_key] = response

        return response

    async def calculate_batch_charts(
        self, subjects: List[Subject], chart_type: str, settings: ChartSettings
    ) -> List[ChartResponse]:
        """Calculate multiple charts in batch"""
        tasks = [self.calculate_single_chart(subject, chart_type, settings) for subject in subjects]
        return await asyncio.gather(*tasks)

    def _prepare_config(self, settings: ChartSettings) -> Dict[str, Any]:
        """Prepare immanuel configuration from settings"""
        config = {
            "house_system": getattr(
                chart_const, settings.house_system.upper(), chart_const.PLACIDUS
            )
        }

        # Add extra objects if requested
        if settings.include_objects:
            asteroids = []
            for obj in settings.include_objects:
                if obj in ["CERES", "PALLAS", "JUNO", "VESTA"]:
                    asteroids.append(getattr(chart_const, obj))
                elif obj == "CHIRON":
                    asteroids.append(chart_const.CHIRON)
                elif obj == "LILITH":
                    config["points"] = list(chart_const.POINTS) + [chart_const.LILITH]

            if asteroids:
                config["asteroids"] = asteroids

        # Set aspects if specified
        if settings.aspects:
            aspect_list = []
            aspect_map = {
                "conjunction": chart_const.CONJUNCTION,
                "opposition": chart_const.OPPOSITION,
                "trine": chart_const.TRINE,
                "square": chart_const.SQUARE,
                "sextile": chart_const.SEXTILE,
                "quincunx": chart_const.QUINCUNX,
                "semisquare": chart_const.SEMISQUARE,
                "sesquiquadrate": chart_const.SESQUIQUADRATE,
            }
            for aspect in settings.aspects:
                if aspect in aspect_map:
                    aspect_list.append(aspect_map[aspect])

            if aspect_list:
                config["aspects"] = aspect_list

        return config

    def _calculate_chart_by_type(self, native: Any, chart_type: str) -> Any:
        """Calculate chart based on type"""
        if chart_type == "natal":
            return charts.Natal(native)
        elif chart_type == "solar_return":
            # For solar return, we need the current year
            year = datetime.now().year
            return charts.SolarReturn(native, year)
        elif chart_type == "progressed":
            # Secondary progressions to current date
            progressed_date = datetime.now()
            return charts.Progressed(native, progressed_date)
        else:
            # Default to natal
            return charts.Natal(native)

    def _build_chart_response(
        self,
        chart: Any,
        original_subject: Subject,
        chart_type: str,
        original_settings: ChartSettings,
    ) -> ChartResponse:
        """Build structured response from chart object"""

        # Extract objects (planets, points, etc.)
        objects = {}
        for obj in chart.objects.values():
            objects[obj.name] = {
                "longitude": obj.longitude,
                "latitude": obj.latitude if hasattr(obj, "latitude") else None,
                "speed": obj.speed if hasattr(obj, "speed") else None,
                "sign": obj.sign.name,
                "sign_longitude": obj.sign_longitude,
                "house": obj.house.number if hasattr(obj, "house") else None,
                "retrograde": obj.retrograde if hasattr(obj, "retrograde") else False,
                "dignities": self._get_dignities(obj) if hasattr(obj, "dignities") else {},
            }

        # Extract aspects
        aspects = []
        if hasattr(chart, "aspects"):
            for aspect in chart.aspects.values():
                aspects.append(
                    {
                        "first": aspect.first.name,
                        "second": aspect.second.name,
                        "type": aspect.type.name,
                        "orb": aspect.orb,
                        "applying": aspect.applying if hasattr(aspect, "applying") else None,
                        "exact": aspect.exact if hasattr(aspect, "exact") else None,
                    }
                )

        # Extract houses
        houses = {}
        if hasattr(chart, "houses"):
            for house in chart.houses.values():
                houses[f"house_{house.number}"] = {
                    "number": house.number,
                    "sign": house.sign.name,
                    "degree": house.longitude,
                    "objects": (
                        [obj.name for obj in house.objects] if hasattr(house, "objects") else []
                    ),
                }

        # Build metadata
        metadata = {
            "calculated_at": datetime.now().isoformat(),
            "chart_type": chart_type,
            "house_system": original_settings.house_system,
            "latitude": original_subject.latitude,
            "longitude": original_subject.longitude,
            "timezone_used": original_subject.timezone or "UTC",
            "immanuel_version": immanuel.__version__,
            "cache_key": self._get_cache_key(original_subject, chart_type, original_settings),
        }

        return ChartResponse(
            metadata=metadata,
            objects=objects,
            aspects=aspects,
            houses=houses,
            dignities={},  # Would be populated based on dignity calculations
        )

    def _get_dignities(self, obj: Any) -> Dict[str, Any]:
        """Extract dignity information for an object"""
        dignities = {}
        if hasattr(obj, "dignities"):
            if obj.dignities.ruler:
                dignities["ruler"] = obj.dignities.ruler.name
            if obj.dignities.exalted:
                dignities["exalted"] = obj.dignities.exalted.name
            if obj.dignities.detriment:
                dignities["detriment"] = obj.dignities.detriment.name
            if obj.dignities.fall:
                dignities["fall"] = obj.dignities.fall.name
        return dignities

    async def interpret_chart(
        self, chart_data: Dict[str, Any], interpretation_type: str
    ) -> Dict[str, Any]:
        """Provide interpretations of chart features"""
        interpretations = {}

        if interpretation_type in ["basic", "detailed", "aspects_only"]:
            # Interpret aspects
            aspect_interps = []
            for aspect in chart_data.get("aspects", []):
                interp = self._interpret_aspect(aspect)
                if interp:
                    aspect_interps.append(interp)
            interpretations["aspects"] = aspect_interps

        if interpretation_type in ["basic", "detailed", "houses_only"]:
            # Interpret house placements
            house_interps = []
            for obj_name, obj_data in chart_data.get("objects", {}).items():
                if obj_data.get("house"):
                    interp = self._interpret_house_placement(obj_name, obj_data)
                    if interp:
                        house_interps.append(interp)
            interpretations["houses"] = house_interps

        if interpretation_type == "detailed":
            # Add dignity interpretations
            dignity_interps = []
            for obj_name, obj_data in chart_data.get("objects", {}).items():
                if obj_data.get("dignities"):
                    interp = self._interpret_dignities(obj_name, obj_data["dignities"])
                    if interp:
                        dignity_interps.append(interp)
            interpretations["dignities"] = dignity_interps

        return interpretations

    def _interpret_aspect(self, aspect: Any) -> str:
        """Interpret a single aspect.

        The method accepts either a dictionary as returned in :class:`ChartResponse`
        or an aspect object from ``immanuel``. Handling both forms keeps the public
        ``interpret_chart`` and ``find_transits`` APIs flexible.
        """
        aspect_meanings = {
            "conjunction": "blending and intensification",
            "opposition": "tension and awareness through polarity",
            "trine": "harmony and easy flow",
            "square": "challenge and dynamic tension",
            "sextile": "opportunity and cooperation",
        }

        if isinstance(aspect, dict):
            aspect_type = str(aspect.get("type", "")).lower()
            first = aspect.get("first")
            second = aspect.get("second")
        else:
            aspect_type = getattr(getattr(aspect, "type", None), "name", None)
            if aspect_type:
                aspect_type = aspect_type.lower()
            first = getattr(getattr(aspect, "first", None), "name", None)
            second = getattr(getattr(aspect, "second", None), "name", None)

        meaning = aspect_meanings.get(aspect_type or "", "interaction")

        return f"This aspect indicates {meaning} between {first} and {second}."

    def _interpret_house_placement(
        self, obj_name: str, obj_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Interpret a house placement"""
        house_themes = {
            1: "self, identity, appearance",
            2: "resources, values, possessions",
            3: "communication, siblings, short trips",
            4: "home, family, roots",
            5: "creativity, romance, children",
            6: "health, work, service",
            7: "partnerships, relationships",
            8: "transformation, shared resources",
            9: "philosophy, higher education, travel",
            10: "career, reputation, public life",
            11: "friends, groups, aspirations",
            12: "spirituality, hidden matters, solitude",
        }

        house_num = obj_data["house"]
        themes = house_themes.get(house_num, "life experiences")

        return {
            "placement": f"{obj_name} in House {house_num}",
            "sign": obj_data["sign"],
            "themes": themes,
            "interpretation": f"{obj_name} expresses through {themes} in the sign of {obj_data['sign']}",
        }

    def _interpret_dignities(
        self, obj_name: str, dignities: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Interpret dignity status"""
        dignity_status = []
        if dignities.get("ruler"):
            dignity_status.append(f"rules {dignities['ruler']}")
        if dignities.get("exalted"):
            dignity_status.append(f"exalted in {dignities['exalted']}")
        if dignities.get("detriment"):
            dignity_status.append(f"in detriment in {dignities['detriment']}")
        if dignities.get("fall"):
            dignity_status.append(f"in fall in {dignities['fall']}")

        if dignity_status:
            return {
                "object": obj_name,
                "dignities": dignity_status,
                "interpretation": f"{obj_name} {', '.join(dignity_status)}",
            }

        return None

    async def compare_charts(
        self, chart1: Dict[str, Any], chart2: Dict[str, Any], comparison_type: str
    ) -> Dict[str, Any]:
        """Compare two charts"""
        if comparison_type == "synastry":
            return await self._calculate_synastry(chart1, chart2)
        elif comparison_type == "composite":
            return await self._calculate_composite(chart1, chart2)
        else:
            return {"error": f"Unknown comparison type: {comparison_type}"}

    async def _calculate_synastry(
        self, chart1: Dict[str, Any], chart2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate synastry aspects between two charts"""
        inter_aspects = []

        # Compare each object in chart1 with each in chart2
        for obj1_name, obj1_data in chart1.get("objects", {}).items():
            for obj2_name, obj2_data in chart2.get("objects", {}).items():
                # Calculate angle between objects
                angle = abs(obj1_data["longitude"] - obj2_data["longitude"])
                if angle > 180:
                    angle = 360 - angle

                # Check for aspects
                aspect_found = self._check_aspect(angle)
                if aspect_found:
                    inter_aspects.append(
                        {
                            "person1_object": obj1_name,
                            "person2_object": obj2_name,
                            "aspect": aspect_found["name"],
                            "orb": aspect_found["orb"],
                            "angle": angle,
                        }
                    )

        return {
            "type": "synastry",
            "inter_aspects": inter_aspects,
            "total_aspects": len(inter_aspects),
        }

    def _check_aspect(self, angle: float) -> Optional[Dict[str, Any]]:
        """Check if angle forms an aspect"""
        aspects = [
            {"name": "conjunction", "angle": 0, "orb": 8},
            {"name": "opposition", "angle": 180, "orb": 8},
            {"name": "trine", "angle": 120, "orb": 8},
            {"name": "square", "angle": 90, "orb": 8},
            {"name": "sextile", "angle": 60, "orb": 6},
        ]

        for aspect in aspects:
            orb = abs(angle - aspect["angle"])
            if orb <= aspect["orb"]:
                return {"name": aspect["name"], "orb": orb}

        return None

    async def _calculate_composite(
        self, chart1: Dict[str, Any], chart2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate composite chart"""
        composite_objects = {}

        # Calculate midpoints for all objects
        for obj_name in chart1.get("objects", {}):
            if obj_name in chart2.get("objects", {}):
                obj1 = chart1["objects"][obj_name]
                obj2 = chart2["objects"][obj_name]

                # Calculate midpoint
                long1 = obj1["longitude"]
                long2 = obj2["longitude"]

                # Handle angle wrap
                if abs(long1 - long2) > 180:
                    if long1 > long2:
                        long2 += 360
                    else:
                        long1 += 360

                midpoint = (long1 + long2) / 2
                if midpoint >= 360:
                    midpoint -= 360

                composite_objects[obj_name] = {
                    "longitude": midpoint,
                    "sign": self._get_sign_from_longitude(midpoint),
                }

        return {"type": "composite", "objects": composite_objects}

    def _get_sign_from_longitude(self, longitude: float) -> str:
        """Get zodiac sign from longitude"""
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
        return signs[sign_index]

    async def find_transits(
        self,
        natal_chart: Dict[str, Any],
        transit_date: str,
        aspect_orbs: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """Find transits to natal chart"""
        # Get natal subject from chart data
        natal_subject = charts.Subject(
            date_time=natal_chart["metadata"]["calculated_at"],
            latitude=natal_chart["metadata"]["latitude"],
            longitude=natal_chart["metadata"]["longitude"],
        )

        # Create natal and transit charts
        natal = charts.Natal(natal_subject)
        transit_chart = charts.Transits(
            latitude=natal_chart["metadata"]["latitude"],
            longitude=natal_chart["metadata"]["longitude"],
            date_time=transit_date,
        )

        # Calculate synastry between natal and transit charts
        synastry = charts.Natal(natal_subject, aspects_to=transit_chart)

        transits = []
        for aspect in synastry.aspects.values():
            transits.append(
                {
                    "transit_planet": aspect.second.name,
                    "natal_planet": aspect.first.name,
                    "aspect": aspect.type.name,
                    "orb": aspect.orb,
                    "exact_date": None,  # Not easily available
                    "interpretation": self._interpret_aspect(aspect),
                }
            )

        return transits

    async def get_ephemeris(
        self, start_date: str, end_date: str, objects: List[str], interval: str
    ) -> List[Dict[str, Any]]:
        """Get ephemeris data"""
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        if interval == "daily":
            delta = timedelta(days=1)
        elif interval == "hourly":
            delta = timedelta(hours=1)
        else:
            delta = timedelta(days=1)

        ephemeris_data = []
        current_date = start
        while current_date <= end:
            chart = charts.Transits(date_time=current_date)
            positions = {}
            for obj_name in objects:
                obj_const = getattr(chart_const, obj_name.upper(), None)
                if obj_const and obj_const in chart.objects:
                    positions[obj_name] = chart.objects[obj_const].longitude
            ephemeris_data.append({"date": current_date.isoformat(), "positions": positions})
            current_date += delta

        return ephemeris_data

    async def find_aspect_patterns(
        self, chart_data: Dict[str, Any], pattern_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Find aspect patterns in chart"""
        # The immanuel-python library automatically calculates chart shape,
        # which is a form of pattern detection. We can leverage that.

        chart_shape = chart_data.get("shape")
        if chart_shape:
            return [
                {
                    "pattern_name": chart_shape,
                    "involved_objects": [],  # Not directly available
                    "interpretation": f"The overall chart shape is a {chart_shape}.",
                }
            ]

        return []

    async def calculate_progressions(
        self, natal_chart: Dict[str, Any], progression_date: str, progression_type: str
    ) -> Dict[str, Any]:
        """Calculate progressed chart"""
        natal_subject = charts.Subject(
            date_time=natal_chart["metadata"]["calculated_at"],
            latitude=natal_chart["metadata"]["latitude"],
            longitude=natal_chart["metadata"]["longitude"],
        )

        progressed_chart = charts.Progressed(natal_subject, progression_date)

        return self._build_chart_response(
            progressed_chart, natal_subject, "progressed", ChartSettings()
        )

    async def get_moon_phases(
        self, start_date: str, end_date: str, timezone: str
    ) -> List[Dict[str, Any]]:
        """Get moon phases between dates"""
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        moon_phases = []
        current_date = start
        while current_date <= end:
            subject = charts.Subject(date_time=current_date, timezone=timezone)
            natal = charts.Natal(subject)
            moon_phases.append(
                {
                    "phase": natal.moon_phase.formatted,
                    "datetime": natal.native.date_time.datetime.isoformat(),
                    "sign": natal.objects[chart_const.MOON].sign.name,
                }
            )
            current_date += timedelta(days=1)  # Check daily for phase changes

        return moon_phases

    async def get_retrograde_periods(
        self, year: int, planets: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get retrograde periods for planets"""
        retrograde_periods = {planet: [] for planet in planets}

        # Immanuel-python doesn't have a direct function for this,
        # so we'll simulate by checking daily movement.

        for planet_name in planets:
            planet_const = getattr(chart_const, planet_name.upper(), None)
            if not planet_const:
                continue

            start_of_year = datetime(year, 1, 1)
            end_of_year = datetime(year, 12, 31)

            current_date = start_of_year
            is_retrograde = False
            period_start = None

            while current_date <= end_of_year:
                chart = charts.Transits(date_time=current_date)
                obj = chart.objects.get(planet_const)

                if obj and hasattr(obj, "movement") and obj.movement.retrograde:
                    if not is_retrograde:
                        is_retrograde = True
                        period_start = current_date
                elif is_retrograde:
                    is_retrograde = False
                    retrograde_periods[planet_name].append(
                        {
                            "start": period_start.isoformat(),
                            "end": (current_date - timedelta(days=1)).isoformat(),
                            "shadow_start": None,  # Not easily available
                            "shadow_end": None,  # Not easily available
                        }
                    )
                current_date += timedelta(days=1)

            # If still retrograde at year end
            if is_retrograde:
                retrograde_periods[planet_name].append(
                    {
                        "start": period_start.isoformat(),
                        "end": end_of_year.isoformat(),
                        "shadow_start": None,
                        "shadow_end": None,
                    }
                )

        return retrograde_periods
