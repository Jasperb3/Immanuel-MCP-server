#!/usr/bin/env python3
"""
CLI tool for testing Immanuel MCP Server functionality
"""

import asyncio
import json
import argparse
from datetime import datetime
from typing import Any, Dict, Optional

from immanuel_mcp.chart_service import ChartService
from immanuel_mcp.models import Subject, ChartSettings
from immanuel_mcp.utils import zodiac_position_to_string, format_aspect_string


class ImmanuelCLI:
    """Command-line interface for Immanuel MCP"""

    def __init__(self):
        self.chart_service = ChartService()

    async def calculate_natal_chart(
        self,
        datetime_str: str,
        latitude: str,
        longitude: str,
        timezone: Optional[str] = None,
        house_system: str = "placidus",
    ) -> Dict[str, Any]:
        """Calculate a natal chart"""
        subject = Subject(
            datetime=datetime_str, latitude=latitude, longitude=longitude, timezone=timezone
        )

        settings = ChartSettings(house_system=house_system)

        result = await self.chart_service.calculate_single_chart(
            subject=subject, chart_type="natal", settings=settings
        )

        return result.dict()

    def format_chart_output(self, chart_data: Dict[str, Any]) -> str:
        """Format chart data for display"""
        output = []

        # Header
        output.append("=" * 60)
        output.append("ASTROLOGICAL CHART")
        output.append("=" * 60)

        # Metadata
        meta = chart_data.get("metadata", {})
        output.append(f"\nCalculated: {meta.get('calculated_at', 'Unknown')}")
        output.append(f"Chart Type: {meta.get('chart_type', 'Unknown')}")
        output.append(f"House System: {meta.get('house_system', 'Unknown')}")
        output.append(f"Timezone: {meta.get('timezone_used', 'Unknown')}")

        # Planetary Positions
        output.append("\n" + "-" * 60)
        output.append("PLANETARY POSITIONS")
        output.append("-" * 60)
        output.append(f"{'Planet':<12} {'Sign':<12} {'Degree':<15} {'House':<8} {'Retro':<6}")
        output.append("-" * 60)

        objects = chart_data.get("objects", {})
        for obj_name, obj_data in objects.items():
            sign = obj_data.get("sign", "Unknown")
            degree = zodiac_position_to_string(obj_data.get("longitude", 0))
            house = obj_data.get("house", "-")
            retro = "R" if obj_data.get("retrograde", False) else ""

            output.append(f"{obj_name:<12} {sign:<12} {degree:<15} {house:<8} {retro:<6}")

        # Houses
        output.append("\n" + "-" * 60)
        output.append("HOUSE CUSPS")
        output.append("-" * 60)
        output.append(f"{'House':<10} {'Sign':<12} {'Degree':<15}")
        output.append("-" * 60)

        houses = chart_data.get("houses", {})
        for house_key in sorted(houses.keys()):
            house_data = houses[house_key]
            house_num = house_data.get("number", 0)
            sign = house_data.get("sign", "Unknown")
            degree = zodiac_position_to_string(house_data.get("degree", 0))

            output.append(f"House {house_num:<4} {sign:<12} {degree:<15}")

        # Aspects
        aspects = chart_data.get("aspects", [])
        if aspects:
            output.append("\n" + "-" * 60)
            output.append("ASPECTS")
            output.append("-" * 60)

            for aspect in aspects:
                aspect_str = format_aspect_string(
                    aspect["first"],
                    aspect["type"],
                    aspect["second"],
                    aspect["orb"],
                    aspect.get("applying"),
                )
                output.append(aspect_str)

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    async def run_example(self):
        """Run an example chart calculation"""
        print("Calculating example natal chart...")
        print("Birth Data: January 1, 2000, 10:00 AM")
        print("Location: Los Angeles, CA (34.05N, 118.24W)")
        print()

        chart_data = await self.calculate_natal_chart(
            datetime_str="2000-01-01T10:00:00",
            latitude="34.05N",
            longitude="118.24W",
            timezone="America/Los_Angeles",
        )

        print(self.format_chart_output(chart_data))

        # Also save to JSON
        with open("example_chart.json", "w") as f:
            json.dump(chart_data, f, indent=2)

        print("\nFull chart data saved to: example_chart.json")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Immanuel MCP CLI - Calculate astrological charts")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Example command
    example_parser = subparsers.add_parser("example", help="Run example chart calculation")

    # Calculate command
    calc_parser = subparsers.add_parser("calculate", help="Calculate a natal chart")
    calc_parser.add_argument(
        "--datetime", required=True, help="Birth datetime in ISO format (e.g., 2000-01-01T10:00:00)"
    )
    calc_parser.add_argument("--latitude", required=True, help="Latitude (e.g., 34.05N or -34.05)")
    calc_parser.add_argument(
        "--longitude", required=True, help="Longitude (e.g., 118.24W or -118.24)"
    )
    calc_parser.add_argument("--timezone", help="Timezone (e.g., America/Los_Angeles)")
    calc_parser.add_argument(
        "--house-system", default="placidus", help="House system (default: placidus)"
    )
    calc_parser.add_argument(
        "--output", choices=["text", "json"], default="text", help="Output format"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run basic functionality tests")

    args = parser.parse_args()

    cli = ImmanuelCLI()

    if args.command == "example":
        await cli.run_example()

    elif args.command == "calculate":
        chart_data = await cli.calculate_natal_chart(
            datetime_str=args.datetime,
            latitude=args.latitude,
            longitude=args.longitude,
            timezone=args.timezone,
            house_system=args.house_system,
        )

        if args.output == "json":
            print(json.dumps(chart_data, indent=2))
        else:
            print(cli.format_chart_output(chart_data))

    elif args.command == "test":
        print("Running basic tests...")

        # Test coordinate parsing
        from immanuel_mcp.utils import parse_coordinates

        print("\nTesting coordinate parsing:")
        lat, dir = parse_coordinates("34.05N", "latitude")
        print(f"  34.05N -> {lat}° {dir}")

        lon, dir = parse_coordinates("118.24W", "longitude")
        print(f"  118.24W -> {lon}° {dir}")

        # Test timezone normalization
        from immanuel_mcp.utils import normalize_timezone

        print("\nTesting timezone normalization:")
        print(f"  PST -> {normalize_timezone('PST')}")
        print(f"  UTC-8 -> {normalize_timezone('UTC-8')}")

        print("\nBasic tests completed!")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
