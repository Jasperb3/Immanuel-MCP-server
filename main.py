#!/usr/bin/env python3
"""
Immanuel MCP Server - Main Entry Point
A Model Context Protocol server for astrological chart calculations using immanuel-python
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp import Server, Tool
from mcp.server.stdio import stdio_server
from pydantic import BaseModel, Field

from .chart_service import ChartService
from .models import ChartRequest, ChartResponse, ChartSettings, Subject
from .utils import parse_coordinates, validate_timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server instance
app = Server("immanuel-mcp")
chart_service = ChartService()

# Tool definitions for MCP
class CalculateChartArgs(BaseModel):
    """Arguments for calculating an astrological chart"""
    datetime: str = Field(description="ISO format datetime (e.g., '2000-01-01T10:00:00')")
    latitude: str = Field(description="Latitude in format '32.72N' or '-32.72'")
    longitude: str = Field(description="Longitude in format '117.16W' or '-117.16'")
    timezone: Optional[str] = Field(default=None, description="Timezone (e.g., 'America/Los_Angeles')")
    chart_type: str = Field(default="natal", description="Chart type: natal, solar_return, progressed, synastry, composite")
    house_system: str = Field(default="placidus", description="House system: placidus, koch, whole_sign, equal, etc.")
    include_objects: Optional[List[str]] = Field(default=None, description="Additional objects: CERES, LILITH, etc.")

class BatchCalculateArgs(BaseModel):
    """Arguments for batch chart calculations"""
    subjects: List[Dict[str, Any]] = Field(description="List of subjects with datetime, latitude, longitude, timezone")
    chart_type: str = Field(default="natal", description="Chart type for all subjects")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Shared settings for all charts")

class InterpretChartArgs(BaseModel):
    """Arguments for interpreting chart aspects"""
    chart_data: Dict[str, Any] = Field(description="Previously calculated chart data")
    interpretation_type: str = Field(default="basic", description="Type: basic, detailed, aspects_only, houses_only")

class CompareChartsArgs(BaseModel):
    """Arguments for comparing two charts (synastry)"""
    chart1: Dict[str, Any] = Field(description="First person's chart data")
    chart2: Dict[str, Any] = Field(description="Second person's chart data")
    comparison_type: str = Field(default="synastry", description="Type: synastry, composite, davison")

class FindTransitsArgs(BaseModel):
    """Arguments for finding current transits"""
    natal_chart: Dict[str, Any] = Field(description="Natal chart data")
    transit_date: Optional[str] = Field(default=None, description="Date for transits (defaults to now)")
    aspect_orbs: Optional[Dict[str, float]] = Field(default=None, description="Custom orbs for aspects")

# Register tools
@app.tool()
async def calculate_chart(args: CalculateChartArgs) -> Dict[str, Any]:
    """
    Calculate a single astrological chart with comprehensive data including
    planetary positions, aspects, houses, and dignities.
    """
    try:
        # Parse coordinates
        lat, lat_dir = parse_coordinates(args.latitude, 'latitude')
        lon, lon_dir = parse_coordinates(args.longitude, 'longitude')
        
        # Create subject
        subject = Subject(
            datetime=args.datetime,
            latitude=args.latitude,
            longitude=args.longitude,
            timezone=args.timezone
        )
        
        # Create settings
        settings = ChartSettings(
            house_system=args.house_system,
            include_objects=args.include_objects or []
        )
        
        # Calculate chart
        result = await chart_service.calculate_single_chart(
            subject=subject,
            chart_type=args.chart_type,
            settings=settings
        )
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Error calculating chart: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def batch_calculate_charts(args: BatchCalculateArgs) -> Dict[str, Any]:
    """
    Calculate multiple charts in batch with optimized processing.
    Useful for analyzing groups, events, or time series.
    """
    try:
        subjects = [Subject(**subj) for subj in args.subjects]
        settings = ChartSettings(**args.settings) if args.settings else ChartSettings()
        
        results = await chart_service.calculate_batch_charts(
            subjects=subjects,
            chart_type=args.chart_type,
            settings=settings
        )
        
        return {
            "charts": [r.dict() for r in results],
            "count": len(results),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in batch calculation: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def interpret_chart(args: InterpretChartArgs) -> Dict[str, Any]:
    """
    Provide interpretations of chart features including aspect meanings,
    house placements, and dignity analysis.
    """
    try:
        interpretation = await chart_service.interpret_chart(
            chart_data=args.chart_data,
            interpretation_type=args.interpretation_type
        )
        
        return {
            "interpretation": interpretation,
            "type": args.interpretation_type,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error interpreting chart: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def compare_charts(args: CompareChartsArgs) -> Dict[str, Any]:
    """
    Compare two charts for relationship analysis (synastry),
    composite charts, or other comparison methods.
    """
    try:
        comparison = await chart_service.compare_charts(
            chart1=args.chart1,
            chart2=args.chart2,
            comparison_type=args.comparison_type
        )
        
        return {
            "comparison": comparison,
            "type": args.comparison_type,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error comparing charts: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def find_transits(args: FindTransitsArgs) -> Dict[str, Any]:
    """
    Calculate current or future transits to a natal chart,
    showing planetary influences and timing.
    """
    try:
        transit_date = args.transit_date or datetime.now().isoformat()
        
        transits = await chart_service.find_transits(
            natal_chart=args.natal_chart,
            transit_date=transit_date,
            aspect_orbs=args.aspect_orbs
        )
        
        return {
            "transits": transits,
            "transit_date": transit_date,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error finding transits: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def get_ephemeris(
    start_date: str = Field(description="Start date in ISO format"),
    end_date: str = Field(description="End date in ISO format"),
    objects: Optional[List[str]] = Field(default=None, description="Objects to include (default: main planets)"),
    interval: str = Field(default="daily", description="Interval: daily, weekly, monthly")
) -> Dict[str, Any]:
    """
    Get ephemeris data showing planetary positions over time.
    Useful for tracking planetary movements and patterns.
    """
    try:
        ephemeris = await chart_service.get_ephemeris(
            start_date=start_date,
            end_date=end_date,
            objects=objects or ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN"],
            interval=interval
        )
        
        return {
            "ephemeris": ephemeris,
            "period": f"{start_date} to {end_date}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting ephemeris: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def find_aspect_patterns(
    chart_data: Dict[str, Any] = Field(description="Chart data to analyze"),
    pattern_types: Optional[List[str]] = Field(default=None, description="Patterns to find: grand_trine, t_square, yod, etc.")
) -> Dict[str, Any]:
    """
    Identify significant aspect patterns in a chart such as
    Grand Trines, T-Squares, Yods, and other configurations.
    """
    try:
        patterns = await chart_service.find_aspect_patterns(
            chart_data=chart_data,
            pattern_types=pattern_types
        )
        
        return {
            "patterns": patterns,
            "count": len(patterns),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error finding patterns: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def calculate_progressions(
    natal_chart: Dict[str, Any] = Field(description="Natal chart data"),
    progression_date: str = Field(description="Date to progress to"),
    progression_type: str = Field(default="secondary", description="Type: secondary, solar_arc, tertiary")
) -> Dict[str, Any]:
    """
    Calculate progressed charts showing symbolic movement of planets
    over time using various progression techniques.
    """
    try:
        progressions = await chart_service.calculate_progressions(
            natal_chart=natal_chart,
            progression_date=progression_date,
            progression_type=progression_type
        )
        
        return {
            "progressions": progressions,
            "progression_date": progression_date,
            "type": progression_type,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error calculating progressions: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def get_moon_phases(
    start_date: str = Field(description="Start date for moon phase search"),
    end_date: str = Field(description="End date for moon phase search"),
    timezone: Optional[str] = Field(default="UTC", description="Timezone for phase times")
) -> Dict[str, Any]:
    """
    Get moon phases (new, first quarter, full, last quarter) between dates
    with exact times and zodiac positions.
    """
    try:
        phases = await chart_service.get_moon_phases(
            start_date=start_date,
            end_date=end_date,
            timezone=timezone
        )
        
        return {
            "moon_phases": phases,
            "period": f"{start_date} to {end_date}",
            "timezone": timezone,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting moon phases: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def get_retrograde_periods(
    year: int = Field(description="Year to check for retrogrades"),
    planets: Optional[List[str]] = Field(default=None, description="Planets to check (default: Mercury, Venus, Mars)")
) -> Dict[str, Any]:
    """
    Find retrograde periods for specified planets in a given year,
    including shadow periods and stations.
    """
    try:
        retrogrades = await chart_service.get_retrograde_periods(
            year=year,
            planets=planets or ["MERCURY", "VENUS", "MARS"]
        )
        
        return {
            "retrograde_periods": retrogrades,
            "year": year,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting retrogrades: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

@app.tool()
async def get_chart_info() -> Dict[str, Any]:
    """
    Get information about available chart types, house systems,
    objects, and other configuration options.
    """
    return {
        "chart_types": [
            "natal", "solar_return", "lunar_return", "progressed",
            "solar_arc", "synastry", "composite", "davison"
        ],
        "house_systems": [
            "placidus", "koch", "whole_sign", "equal", "campanus",
            "regiomontanus", "porphyry", "morinus", "alcabitus"
        ],
        "objects": {
            "planets": ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO"],
            "points": ["ASC", "MC", "NORTH_NODE", "SOUTH_NODE", "VERTEX", "PART_OF_FORTUNE"],
            "asteroids": ["CERES", "PALLAS", "JUNO", "VESTA", "CHIRON"],
            "other": ["LILITH", "SELENA"]
        },
        "aspects": [
            "conjunction", "opposition", "trine", "square", "sextile",
            "quincunx", "semisquare", "sesquiquadrate", "semisextile",
            "quintile", "biquintile"
        ],
        "dignities": ["rulership", "exaltation", "detriment", "fall"],
        "status": "success"
    }

async def main():
    """Run the MCP server"""
    logger.info("Starting Immanuel MCP Server...")
    
    # Run the stdio server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())