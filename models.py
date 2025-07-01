"""
Data Models - Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class Subject(BaseModel):
    """Represents a person or event for chart calculation"""
    datetime: str = Field(..., description="ISO format datetime")
    latitude: str = Field(..., description="Latitude (e.g., '32.72N' or '-32.72')")
    longitude: str = Field(..., description="Longitude (e.g., '117.16W' or '-117.16')")
    timezone: Optional[str] = Field(None, description="Timezone name (e.g., 'America/Los_Angeles')")
    name: Optional[str] = Field(None, description="Name of person or event")
    
    @validator('datetime')
    def validate_datetime(cls, v):
        try:
            # Try parsing ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid datetime format: {v}")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        # Accept formats like "32.72N", "-32.72", "32N43"
        try:
            if v[-1] in 'NS':
                lat = float(v[:-1])
                if not -90 <= lat <= 90:
                    raise ValueError
            else:
                lat = float(v)
                if not -90 <= lat <= 90:
                    raise ValueError
            return v
        except:
            raise ValueError(f"Invalid latitude: {v}")
    
    @validator('longitude')
    def validate_longitude(cls, v):
        # Accept formats like "117.16W", "-117.16", "117W09"
        try:
            if v[-1] in 'EW':
                lon = float(v[:-1])
                if not -180 <= lon <= 180:
                    raise ValueError
            else:
                lon = float(v)
                if not -180 <= lon <= 180:
                    raise ValueError
            return v
        except:
            raise ValueError(f"Invalid longitude: {v}")


class ChartSettings(BaseModel):
    """Configuration settings for chart calculation"""
    locale: str = Field(default="en_US", description="Locale for names and formatting")
    house_system: str = Field(default="placidus", description="House system to use")
    include_objects: List[str] = Field(default_factory=list, description="Additional objects to include")
    aspects: Optional[List[str]] = Field(None, description="Aspects to calculate")
    orbs: Optional[Dict[str, float]] = Field(None, description="Custom aspect orbs")
    
    @validator('house_system')
    def validate_house_system(cls, v):
        valid_systems = [
            'placidus', 'koch', 'whole_sign', 'equal', 'campanus',
            'regiomontanus', 'porphyry', 'morinus', 'alcabitus'
        ]
        if v.lower() not in valid_systems:
            raise ValueError(f"Invalid house system: {v}")
        return v.lower()
    
    @validator('include_objects')
    def validate_objects(cls, v):
        valid_objects = [
            'CERES', 'PALLAS', 'JUNO', 'VESTA', 'CHIRON',
            'LILITH', 'SELENA', 'ERIS', 'SEDNA'
        ]
        for obj in v:
            if obj.upper() not in valid_objects:
                raise ValueError(f"Invalid object: {obj}")
        return [obj.upper() for obj in v]


class ChartRequest(BaseModel):
    """Request for chart calculation"""
    subjects: List[Subject] = Field(..., description="One or more subjects for calculation")
    chart_type: str = Field(default="natal", description="Type of chart to calculate")
    settings: Optional[ChartSettings] = Field(default_factory=ChartSettings, description="Chart settings")
    
    @validator('chart_type')
    def validate_chart_type(cls, v):
        valid_types = [
            'natal', 'solar_return', 'lunar_return', 'progressed',
            'solar_arc', 'synastry', 'composite', 'davison', 'transit'
        ]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid chart type: {v}")
        return v.lower()
    
    @validator('subjects')
    def validate_subjects(cls, v, values):
        chart_type = values.get('chart_type', 'natal')
        if chart_type in ['synastry', 'composite', 'davison'] and len(v) != 2:
            raise ValueError(f"Chart type {chart_type} requires exactly 2 subjects")
        elif chart_type not in ['synastry', 'composite', 'davison'] and len(v) < 1:
            raise ValueError("At least one subject required")
        return v


class ObjectData(BaseModel):
    """Data for a celestial object"""
    longitude: float = Field(..., description="Ecliptic longitude in degrees")
    latitude: Optional[float] = Field(None, description="Ecliptic latitude in degrees")
    speed: Optional[float] = Field(None, description="Daily motion in degrees")
    sign: str = Field(..., description="Zodiac sign")
    sign_longitude: float = Field(..., description="Degrees within sign")
    house: Optional[int] = Field(None, description="House number (1-12)")
    retrograde: bool = Field(default=False, description="Whether object is retrograde")
    dignities: Dict[str, Any] = Field(default_factory=dict, description="Dignity information")


class AspectData(BaseModel):
    """Data for an aspect between two objects"""
    first: str = Field(..., description="First object name")
    second: str = Field(..., description="Second object name")
    type: str = Field(..., description="Aspect type")
    orb: float = Field(..., description="Orb in degrees")
    applying: Optional[bool] = Field(None, description="Whether aspect is applying")
    exact: Optional[datetime] = Field(None, description="When aspect becomes exact")


class HouseData(BaseModel):
    """Data for a house"""
    number: int = Field(..., ge=1, le=12, description="House number")
    sign: str = Field(..., description="Sign on house cusp")
    degree: float = Field(..., description="Degree of house cusp")
    objects: List[str] = Field(default_factory=list, description="Objects in this house")


class ChartResponse(BaseModel):
    """Response containing calculated chart data"""
    metadata: Dict[str, Any] = Field(..., description="Metadata about calculation")
    objects: Dict[str, Dict[str, Any]] = Field(..., description="Celestial objects data")
    aspects: List[Dict[str, Any]] = Field(default_factory=list, description="Aspects between objects")
    houses: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="House data")
    dignities: Dict[str, Any] = Field(default_factory=dict, description="Dignity information")
    
    class Config:
        schema_extra = {
            "example": {
                "metadata": {
                    "calculated_at": "2024-01-01T12:00:00Z",
                    "chart_type": "natal",
                    "house_system": "placidus",
                    "timezone_used": "America/Los_Angeles",
                    "immanuel_version": "1.0.0"
                },
                "objects": {
                    "Sun": {
                        "longitude": 280.5,
                        "sign": "Capricorn",
                        "sign_longitude": 10.5,
                        "house": 10,
                        "speed": 1.019
                    }
                },
                "aspects": [
                    {
                        "first": "Sun",
                        "second": "Moon",
                        "type": "trine",
                        "orb": 2.3,
                        "applying": True
                    }
                ],
                "houses": {
                    "house_1": {
                        "number": 1,
                        "sign": "Aries",
                        "degree": 15.0,
                        "objects": ["Mars"]
                    }
                }
            }
        }


class InterpretationRequest(BaseModel):
    """Request for chart interpretation"""
    chart_data: Dict[str, Any] = Field(..., description="Previously calculated chart data")
    interpretation_type: str = Field(default="basic", description="Type of interpretation")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    
    @validator('interpretation_type')
    def validate_interpretation_type(cls, v):
        valid_types = ['basic', 'detailed', 'aspects_only', 'houses_only', 'dignities_only']
        if v not in valid_types:
            raise ValueError(f"Invalid interpretation type: {v}")
        return v


class ComparisonRequest(BaseModel):
    """Request for chart comparison"""
    chart1: Dict[str, Any] = Field(..., description="First chart data")
    chart2: Dict[str, Any] = Field(..., description="Second chart data")
    comparison_type: str = Field(default="synastry", description="Type of comparison")
    
    @validator('comparison_type')
    def validate_comparison_type(cls, v):
        valid_types = ['synastry', 'composite', 'davison']
        if v not in valid_types:
            raise ValueError(f"Invalid comparison type: {v}")
        return v


class TransitRequest(BaseModel):
    """Request for transit calculations"""
    natal_chart: Dict[str, Any] = Field(..., description="Natal chart data")
    transit_date: Optional[str] = Field(None, description="Date for transits (defaults to now)")
    aspect_orbs: Optional[Dict[str, float]] = Field(None, description="Custom orbs for transit aspects")
    include_planets: Optional[List[str]] = Field(None, description="Which planets to include in transits")


class EphemerisRequest(BaseModel):
    """Request for ephemeris data"""
    start_date: str = Field(..., description="Start date in ISO format")
    end_date: str = Field(..., description="End date in ISO format")
    objects: Optional[List[str]] = Field(None, description="Objects to include")
    interval: str = Field(default="daily", description="Data interval")
    
    @validator('interval')
    def validate_interval(cls, v):
        valid_intervals = ['daily', 'weekly', 'monthly']
        if v not in valid_intervals:
            raise ValueError(f"Invalid interval: {v}")
        return v


class PatternRequest(BaseModel):
    """Request for aspect pattern detection"""
    chart_data: Dict[str, Any] = Field(..., description="Chart data to analyze")
    pattern_types: Optional[List[str]] = Field(None, description="Specific patterns to find")
    
    @validator('pattern_types')
    def validate_pattern_types(cls, v):
        if v is None:
            return None
        
        valid_patterns = [
            'grand_trine', 't_square', 'grand_cross', 'yod',
            'kite', 'mystic_rectangle', 'star_of_david'
        ]
        for pattern in v:
            if pattern not in valid_patterns:
                raise ValueError(f"Invalid pattern type: {pattern}")
        return v


class ProgressionRequest(BaseModel):
    """Request for progression calculations"""
    natal_chart: Dict[str, Any] = Field(..., description="Natal chart data")
    progression_date: str = Field(..., description="Date to progress to")
    progression_type: str = Field(default="secondary", description="Type of progression")
    
    @validator('progression_type')
    def validate_progression_type(cls, v):
        valid_types = ['secondary', 'solar_arc', 'tertiary', 'minor']
        if v not in valid_types:
            raise ValueError(f"Invalid progression type: {v}")
        return v


class MoonPhaseRequest(BaseModel):
    """Request for moon phase data"""
    start_date: str = Field(..., description="Start date for search")
    end_date: str = Field(..., description="End date for search")
    timezone: str = Field(default="UTC", description="Timezone for phase times")
    include_eclipses: bool = Field(default=False, description="Include eclipse information")


class RetrogradeRequest(BaseModel):
    """Request for retrograde period data"""
    year: int = Field(..., description="Year to check")
    planets: Optional[List[str]] = Field(None, description="Planets to check")
    include_shadow: bool = Field(default=True, description="Include shadow periods")
    
    @validator('year')
    def validate_year(cls, v):
        if v < 1900 or v > 2100:
            raise ValueError(f"Year must be between 1900 and 2100")
        return v