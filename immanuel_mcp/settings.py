"""
Settings - Configuration management for Immanuel MCP Server
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class ServerSettings(BaseSettings):
    """Server configuration settings"""

    # Server settings
    server_name: str = Field(default="immanuel-mcp", env="IMMANUEL_SERVER_NAME")
    server_version: str = Field(default="0.1.0", env="IMMANUEL_SERVER_VERSION")
    log_level: str = Field(default="INFO", env="IMMANUEL_LOG_LEVEL")

    # Cache settings
    enable_cache: bool = Field(default=True, env="IMMANUEL_ENABLE_CACHE")
    cache_max_size: int = Field(default=1000, env="IMMANUEL_CACHE_MAX_SIZE")
    cache_ttl_seconds: int = Field(default=3600, env="IMMANUEL_CACHE_TTL")

    # Ephemeris settings
    ephemeris_path: Path = Field(
        default=Path.home() / ".immanuel" / "ephemeris", env="IMMANUEL_EPHEMERIS_PATH"
    )
    auto_download_ephemeris: bool = Field(default=False, env="IMMANUEL_AUTO_DOWNLOAD_EPHEMERIS")

    # Default calculation settings
    default_house_system: str = Field(default="placidus", env="IMMANUEL_DEFAULT_HOUSE_SYSTEM")
    default_orb_conjunction: float = Field(default=8.0, env="IMMANUEL_ORB_CONJUNCTION")
    default_orb_opposition: float = Field(default=8.0, env="IMMANUEL_ORB_OPPOSITION")
    default_orb_trine: float = Field(default=8.0, env="IMMANUEL_ORB_TRINE")
    default_orb_square: float = Field(default=8.0, env="IMMANUEL_ORB_SQUARE")
    default_orb_sextile: float = Field(default=6.0, env="IMMANUEL_ORB_SEXTILE")
    default_orb_minor: float = Field(default=3.0, env="IMMANUEL_ORB_MINOR")

    # Objects to include by default
    default_planets: List[str] = Field(
        default=[
            "SUN",
            "MOON",
            "MERCURY",
            "VENUS",
            "MARS",
            "JUPITER",
            "SATURN",
            "URANUS",
            "NEPTUNE",
            "PLUTO",
        ],
        env="IMMANUEL_DEFAULT_PLANETS",
    )
    default_points: List[str] = Field(
        default=["ASC", "MC", "NORTH_NODE", "SOUTH_NODE"], env="IMMANUEL_DEFAULT_POINTS"
    )
    default_asteroids: List[str] = Field(default=[], env="IMMANUEL_DEFAULT_ASTEROIDS")

    # Timezone database settings
    timezone_database: str = Field(default="pytz", env="IMMANUEL_TIMEZONE_DB")
    fallback_timezone: str = Field(default="UTC", env="IMMANUEL_FALLBACK_TIMEZONE")

    # Interpretation settings
    enable_interpretations: bool = Field(default=True, env="IMMANUEL_ENABLE_INTERPRETATIONS")
    interpretation_style: str = Field(default="modern", env="IMMANUEL_INTERPRETATION_STYLE")

    # Performance settings
    max_batch_size: int = Field(default=100, env="IMMANUEL_MAX_BATCH_SIZE")
    calculation_timeout: int = Field(default=30, env="IMMANUEL_CALCULATION_TIMEOUT")

    # Security settings
    allow_future_dates: bool = Field(default=True, env="IMMANUEL_ALLOW_FUTURE_DATES")
    max_year_range: int = Field(default=200, env="IMMANUEL_MAX_YEAR_RANGE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @field_validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

    @field_validator("default_house_system")
    def validate_house_system(cls, v):
        valid_systems = [
            "placidus",
            "koch",
            "whole_sign",
            "equal",
            "campanus",
            "regiomontanus",
            "porphyry",
            "morinus",
            "alcabitus",
        ]
        if v.lower() not in valid_systems:
            raise ValueError(f"Invalid house system: {v}")
        return v.lower()

    @field_validator("interpretation_style")
    def validate_interpretation_style(cls, v):
        valid_styles = ["traditional", "modern", "psychological", "evolutionary"]
        if v.lower() not in valid_styles:
            raise ValueError(f"Invalid interpretation style: {v}")
        return v.lower()

    @field_validator("ephemeris_path")
    def validate_ephemeris_path(cls, v):
        """Ensure ephemeris directory exists"""
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v

    def get_default_orbs(self) -> Dict[str, float]:
        """Get default aspect orbs"""
        return {
            "conjunction": self.default_orb_conjunction,
            "opposition": self.default_orb_opposition,
            "trine": self.default_orb_trine,
            "square": self.default_orb_square,
            "sextile": self.default_orb_sextile,
            "quincunx": self.default_orb_minor,
            "semisquare": self.default_orb_minor,
            "sesquiquadrate": self.default_orb_minor,
            "semisextile": self.default_orb_minor,
            "quintile": self.default_orb_minor,
            "biquintile": self.default_orb_minor,
        }

    def get_all_default_objects(self) -> List[str]:
        """Get all default objects to include in charts"""
        return self.default_planets + self.default_points + self.default_asteroids

    def to_immanuel_config(self) -> Dict[str, Any]:
        """Convert settings to immanuel-python configuration format"""
        from immanuel.const import chart as chart_const

        config = {
            "house_system": getattr(chart_const, self.default_house_system.upper()),
            "angles": [],
            "planets": [],
            "points": [],
            "asteroids": [],
        }

        # Map object names to immanuel constants
        for planet in self.default_planets:
            if hasattr(chart_const, planet):
                config["planets"].append(getattr(chart_const, planet))

        for point in self.default_points:
            if point in ["ASC", "DESC", "MC", "IC"]:
                config["angles"].append(getattr(chart_const, point))
            elif hasattr(chart_const, point):
                config["points"].append(getattr(chart_const, point))

        for asteroid in self.default_asteroids:
            if hasattr(chart_const, asteroid):
                config["asteroids"].append(getattr(chart_const, asteroid))

        return config


class InterpretationSettings(BaseSettings):
    """Settings for astrological interpretations"""

    # Aspect interpretations
    aspect_interpretations: Dict[str, Dict[str, str]] = Field(
        default={
            "conjunction": {
                "keyword": "Fusion",
                "description": "Blending and intensification of energies",
                "traditional": "Unity of purpose and expression",
                "modern": "Integration and synthesis of planetary principles",
                "psychological": "Merged psychological functions",
            },
            "opposition": {
                "keyword": "Awareness",
                "description": "Tension and balance through polarity",
                "traditional": "Conflict requiring resolution",
                "modern": "Complementary opposites seeking integration",
                "psychological": "Projection and relationship dynamics",
            },
            "trine": {
                "keyword": "Harmony",
                "description": "Easy flow and natural talent",
                "traditional": "Benefic aspect bringing fortune",
                "modern": "Natural abilities and opportunities",
                "psychological": "Integrated and flowing psychological energies",
            },
            "square": {
                "keyword": "Challenge",
                "description": "Dynamic tension requiring action",
                "traditional": "Obstacle and difficulty",
                "modern": "Growth through challenge and effort",
                "psychological": "Internal conflict driving development",
            },
            "sextile": {
                "keyword": "Opportunity",
                "description": "Potential requiring activation",
                "traditional": "Minor benefic aspect",
                "modern": "Talents that develop through use",
                "psychological": "Cooperative psychological functions",
            },
        }
    )

    # House interpretations
    house_keywords: Dict[int, Dict[str, str]] = Field(
        default={
            1: {"keyword": "Identity", "domains": "Self, appearance, first impressions, vitality"},
            2: {"keyword": "Resources", "domains": "Values, possessions, money, self-worth"},
            3: {"keyword": "Communication", "domains": "Thinking, learning, siblings, short trips"},
            4: {"keyword": "Foundation", "domains": "Home, family, roots, emotional security"},
            5: {"keyword": "Creativity", "domains": "Self-expression, romance, children, pleasure"},
            6: {"keyword": "Service", "domains": "Work, health, daily routines, service"},
            7: {"keyword": "Partnership", "domains": "Relationships, marriage, open enemies"},
            8: {"keyword": "Transformation", "domains": "Shared resources, death/rebirth, occult"},
            9: {"keyword": "Expansion", "domains": "Philosophy, higher education, travel, beliefs"},
            10: {"keyword": "Achievement", "domains": "Career, reputation, public life, authority"},
            11: {"keyword": "Community", "domains": "Friends, groups, hopes, social causes"},
            12: {
                "keyword": "Transcendence",
                "domains": "Spirituality, hidden things, isolation, service",
            },
        }
    )

    # Dignity interpretations
    dignity_interpretations: Dict[str, str] = Field(
        default={
            "domicile": "Planet in its home sign - full strength and authentic expression",
            "exaltation": "Planet in honored position - elevated and refined expression",
            "detriment": "Planet in opposite of home - challenged but growth-oriented",
            "fall": "Planet in opposite of exaltation - humbled but teaching important lessons",
            "peregrine": "Planet without essential dignity - wandering but adaptable",
        }
    )

    def get_aspect_interpretation(self, aspect: str, style: str = "modern") -> Dict[str, str]:
        """Get interpretation for an aspect"""
        if aspect in self.aspect_interpretations:
            interp = self.aspect_interpretations[aspect].copy()
            interp["style_specific"] = interp.get(style, interp["description"])
            return interp
        return {
            "keyword": aspect.title(),
            "description": f"Aspect creating a {aspect} relationship",
            "style_specific": f"{aspect} aspect between planets",
        }

    def get_house_interpretation(self, house_number: int) -> Dict[str, str]:
        """Get interpretation for a house"""
        if house_number in self.house_keywords:
            return self.house_keywords[house_number]
        return {
            "keyword": f"House {house_number}",
            "domains": f"Life areas related to house {house_number}",
        }


# Global settings instance
settings = ServerSettings()
interpretation_settings = InterpretationSettings()


def get_settings() -> ServerSettings:
    """Get current server settings"""
    return settings


def get_interpretation_settings() -> InterpretationSettings:
    """Get interpretation settings"""
    return interpretation_settings


def update_settings(**kwargs) -> ServerSettings:
    """Update settings with new values"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings
