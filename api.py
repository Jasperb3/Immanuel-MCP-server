"""
FastAPI HTTP wrapper for Immanuel MCP Server

This provides a REST API interface to the MCP functionality,
useful for testing and integration with non-MCP clients.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from immanuel_mcp.chart_service import ChartService
from immanuel_mcp.models import (
    Subject,
    ChartSettings,
    ChartRequest,
    ChartResponse,
    InterpretationRequest,
    ComparisonRequest,
    TransitRequest,
)
from immanuel_mcp.settings import get_settings


# Initialize FastAPI app
app = FastAPI(
    title="Immanuel MCP API",
    description="REST API for astrological chart calculations",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chart service
chart_service = ChartService()
settings = get_settings()


# Request/Response models for API
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ChartCalculationRequest(BaseModel):
    datetime: str = Field(..., example="2000-01-01T10:00:00")
    latitude: str = Field(..., example="34.05N")
    longitude: str = Field(..., example="118.24W")
    timezone: Optional[str] = Field(None, example="America/Los_Angeles")
    chart_type: str = Field(default="natal", example="natal")
    house_system: str = Field(default="placidus", example="placidus")
    include_objects: Optional[List[str]] = Field(None, example=["CERES", "CHIRON"])
    name: Optional[str] = Field(None, example="John Doe")


class BatchChartRequest(BaseModel):
    subjects: List[ChartCalculationRequest]
    chart_type: str = Field(default="natal")
    settings: Optional[Dict[str, Any]] = None


class InterpretationAPIRequest(BaseModel):
    chart_data: Dict[str, Any]
    interpretation_type: str = Field(default="basic")


class ComparisonAPIRequest(BaseModel):
    chart1: Dict[str, Any]
    chart2: Dict[str, Any]
    comparison_type: str = Field(default="synastry")


class TransitAPIRequest(BaseModel):
    natal_chart: Dict[str, Any]
    transit_date: Optional[str] = None
    aspect_orbs: Optional[Dict[str, float]] = None


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="ok", version=settings.server_version, timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="ok", version=settings.server_version, timestamp=datetime.now().isoformat()
    )


@app.get("/schema")
async def get_schema():
    """Get JSON schema for request/response formats"""
    return {
        "chart_request": ChartRequest.schema(),
        "chart_response": ChartResponse.schema(),
        "interpretation_request": InterpretationRequest.schema(),
        "comparison_request": ComparisonRequest.schema(),
        "transit_request": TransitRequest.schema(),
    }


@app.get("/version")
async def get_version():
    """Get version information"""
    return {
        "server_version": settings.server_version,
        "immanuel_version": "1.0.0",  # Would get from immanuel.__version__
        "api_version": "0.1.0",
    }


@app.get("/info")
async def get_info():
    """Get information about available options"""
    return {
        "chart_types": [
            "natal",
            "solar_return",
            "lunar_return",
            "progressed",
            "solar_arc",
            "synastry",
            "composite",
            "davison",
        ],
        "house_systems": [
            "placidus",
            "koch",
            "whole_sign",
            "equal",
            "campanus",
            "regiomontanus",
            "porphyry",
            "morinus",
            "alcabitus",
        ],
        "objects": {
            "planets": [
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
            "points": ["ASC", "MC", "NORTH_NODE", "SOUTH_NODE", "VERTEX", "PART_OF_FORTUNE"],
            "asteroids": ["CERES", "PALLAS", "JUNO", "VESTA", "CHIRON"],
            "other": ["LILITH", "SELENA"],
        },
        "aspects": [
            "conjunction",
            "opposition",
            "trine",
            "square",
            "sextile",
            "quincunx",
            "semisquare",
            "sesquiquadrate",
            "semisextile",
            "quintile",
            "biquintile",
        ],
        "interpretation_types": [
            "basic",
            "detailed",
            "aspects_only",
            "houses_only",
            "dignities_only",
        ],
        "comparison_types": ["synastry", "composite", "davison"],
        "progression_types": ["secondary", "solar_arc", "tertiary", "minor"],
    }


@app.post("/chart", response_model=Dict[str, Any])
async def calculate_chart(request: ChartCalculationRequest):
    """Calculate a single astrological chart"""
    try:
        subject = Subject(
            datetime=request.datetime,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone,
            name=request.name,
        )

        settings = ChartSettings(
            house_system=request.house_system, include_objects=request.include_objects or []
        )

        result = await chart_service.calculate_single_chart(
            subject=subject, chart_type=request.chart_type, settings=settings
        )

        return result.dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/batch", response_model=Dict[str, Any])
async def calculate_batch(request: BatchChartRequest):
    """Calculate multiple charts in batch"""
    try:
        subjects = []
        for subj_data in request.subjects:
            subjects.append(
                Subject(
                    datetime=subj_data.datetime,
                    latitude=subj_data.latitude,
                    longitude=subj_data.longitude,
                    timezone=subj_data.timezone,
                    name=subj_data.name,
                )
            )

        settings = ChartSettings(**request.settings) if request.settings else ChartSettings()

        results = await chart_service.calculate_batch_charts(
            subjects=subjects, chart_type=request.chart_type, settings=settings
        )

        return {"charts": [r.dict() for r in results], "count": len(results), "status": "success"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch calculation error: {str(e)}")


@app.post("/interpret", response_model=Dict[str, Any])
async def interpret_chart(request: InterpretationAPIRequest):
    """Get interpretations for a calculated chart"""
    try:
        interpretation = await chart_service.interpret_chart(
            chart_data=request.chart_data, interpretation_type=request.interpretation_type
        )

        return {
            "interpretation": interpretation,
            "type": request.interpretation_type,
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interpretation error: {str(e)}")


@app.post("/compare", response_model=Dict[str, Any])
async def compare_charts(request: ComparisonAPIRequest):
    """Compare two charts (synastry, composite, etc.)"""
    try:
        comparison = await chart_service.compare_charts(
            chart1=request.chart1, chart2=request.chart2, comparison_type=request.comparison_type
        )

        return {"comparison": comparison, "type": request.comparison_type, "status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@app.post("/transits", response_model=Dict[str, Any])
async def find_transits(request: TransitAPIRequest):
    """Find transits to a natal chart"""
    try:
        transit_date = request.transit_date or datetime.now().isoformat()

        transits = await chart_service.find_transits(
            natal_chart=request.natal_chart,
            transit_date=transit_date,
            aspect_orbs=request.aspect_orbs,
        )

        return {"transits": transits, "transit_date": transit_date, "status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transit calculation error: {str(e)}")


@app.get("/ephemeris")
async def get_ephemeris(
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format"),
    objects: Optional[str] = Query(None, description="Comma-separated list of objects"),
    interval: str = Query("daily", description="Interval: daily, weekly, monthly"),
):
    """Get ephemeris data for a date range"""
    try:
        object_list = objects.split(",") if objects else None

        ephemeris = await chart_service.get_ephemeris(
            start_date=start_date, end_date=end_date, objects=object_list, interval=interval
        )

        return {
            "ephemeris": ephemeris,
            "period": f"{start_date} to {end_date}",
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ephemeris error: {str(e)}")


@app.get("/moon-phases")
async def get_moon_phases(
    start_date: str = Query(..., description="Start date for moon phase search"),
    end_date: str = Query(..., description="End date for moon phase search"),
    timezone: str = Query("UTC", description="Timezone for phase times"),
):
    """Get moon phases between dates"""
    try:
        phases = await chart_service.get_moon_phases(
            start_date=start_date, end_date=end_date, timezone=timezone
        )

        return {
            "moon_phases": phases,
            "period": f"{start_date} to {end_date}",
            "timezone": timezone,
            "status": "success",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moon phase error: {str(e)}")


@app.get("/retrogrades/{year}")
async def get_retrogrades(
    year: int, planets: Optional[str] = Query(None, description="Comma-separated list of planets")
):
    """Get retrograde periods for a year"""
    try:
        planet_list = planets.split(",") if planets else ["MERCURY", "VENUS", "MARS"]

        retrogrades = await chart_service.get_retrograde_periods(year=year, planets=planet_list)

        return {"retrograde_periods": retrogrades, "year": year, "status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrograde calculation error: {str(e)}")


# WebSocket endpoint for real-time calculations (optional)
from fastapi import WebSocket, WebSocketDisconnect


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chart calculations"""
    await websocket.accept()
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Process based on message type
            if data.get("type") == "calculate":
                # Calculate chart
                subject = Subject(**data["subject"])
                settings = ChartSettings(**data.get("settings", {}))

                result = await chart_service.calculate_single_chart(
                    subject=subject, chart_type=data.get("chart_type", "natal"), settings=settings
                )

                # Send result
                await websocket.send_json({"type": "chart_result", "data": result.dict()})

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI server
    uvicorn.run("immanuel_mcp.api:app", host="0.0.0.0", port=8000, reload=True)
