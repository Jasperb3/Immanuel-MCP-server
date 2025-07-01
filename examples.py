"""
Example usage scripts for Immanuel MCP Server

This file demonstrates various ways to use the MCP server functionality.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from immanuel_mcp.chart_service import ChartService
from immanuel_mcp.models import Subject, ChartSettings


class AstrologyExamples:
    """Example usage of the Immanuel MCP Server"""
    
    def __init__(self):
        self.chart_service = ChartService()
    
    async def example_natal_chart(self):
        """Example: Calculate a basic natal chart"""
        print("\n=== EXAMPLE 1: Basic Natal Chart ===")
        
        # Create a subject (person)
        subject = Subject(
            datetime="1990-06-15T14:30:00",
            latitude="40.7128N",
            longitude="74.0060W",
            timezone="America/New_York",
            name="John Doe"
        )
        
        # Calculate natal chart
        chart = await self.chart_service.calculate_single_chart(
            subject=subject,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        # Display key information
        print(f"Chart calculated for: {subject.name}")
        print(f"Birth datetime: {subject.datetime}")
        print(f"Location: {subject.latitude}, {subject.longitude}")
        
        # Show Sun, Moon, and Ascendant
        objects = chart.objects
        if 'Sun' in objects:
            sun = objects['Sun']
            print(f"\nSun: {sun['sign']} at {sun['sign_longitude']:.2f}°")
            print(f"  House: {sun.get('house', 'Unknown')}")
        
        if 'Moon' in objects:
            moon = objects['Moon']
            print(f"\nMoon: {moon['sign']} at {moon['sign_longitude']:.2f}°")
            print(f"  House: {moon.get('house', 'Unknown')}")
        
        if 'ASC' in objects:
            asc = objects['ASC']
            print(f"\nAscendant: {asc['sign']} at {asc['sign_longitude']:.2f}°")
        
        return chart
    
    async def example_with_asteroids(self):
        """Example: Chart with additional asteroids"""
        print("\n=== EXAMPLE 2: Chart with Asteroids ===")
        
        subject = Subject(
            datetime="1985-03-21T09:15:00",
            latitude="51.5074N",
            longitude="0.1278W",
            timezone="Europe/London",
            name="Jane Smith"
        )
        
        # Include asteroids in the chart
        settings = ChartSettings(
            include_objects=["CERES", "PALLAS", "JUNO", "VESTA", "CHIRON", "LILITH"]
        )
        
        chart = await self.chart_service.calculate_single_chart(
            subject=subject,
            chart_type="natal",
            settings=settings
        )
        
        # Display asteroid positions
        print(f"Chart with asteroids for: {subject.name}")
        
        asteroids = ["CERES", "PALLAS", "JUNO", "VESTA", "CHIRON", "LILITH"]
        for asteroid in asteroids:
            if asteroid in chart.objects:
                obj = chart.objects[asteroid]
                print(f"{asteroid}: {obj['sign']} at {obj['sign_longitude']:.2f}°")
        
        return chart
    
    async def example_synastry(self):
        """Example: Relationship compatibility (Synastry)"""
        print("\n=== EXAMPLE 3: Synastry (Relationship) Chart ===")
        
        # First person
        person1 = Subject(
            datetime="1988-07-22T06:45:00",
            latitude="51.5074N",
            longitude="0.1278W",
            timezone="Europe/London",
            name="Partner 1"
        )
        
        # Second person
        person2 = Subject(
            datetime="1990-03-15T14:30:00",
            latitude="40.7128N",
            longitude="74.0060W",
            timezone="America/New_York",
            name="Partner 2"
        )
        
        # Calculate both natal charts
        chart1 = await self.chart_service.calculate_single_chart(
            subject=person1,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        chart2 = await self.chart_service.calculate_single_chart(
            subject=person2,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        # Compare charts
        comparison = await self.chart_service.compare_charts(
            chart1=chart1.dict(),
            chart2=chart2.dict(),
            comparison_type="synastry"
        )
        
        print(f"Synastry between {person1.name} and {person2.name}")
        print(f"Total inter-aspects found: {comparison['total_aspects']}")
        
        # Show some key aspects
        for aspect in comparison['inter_aspects'][:5]:  # First 5 aspects
            print(f"  {aspect['person1_object']} - {aspect['person2_object']}: "
                  f"{aspect['aspect']} (orb: {aspect['orb']:.1f}°)")
        
        return comparison
    
    async def example_batch_family_charts(self):
        """Example: Calculate charts for a whole family"""
        print("\n=== EXAMPLE 4: Batch Family Charts ===")
        
        family = [
            Subject(
                datetime="1960-06-01T08:00:00",
                latitude="41.8781N",
                longitude="87.6298W",
                timezone="America/Chicago",
                name="Mother"
            ),
            Subject(
                datetime="1958-10-15T15:30:00",
                latitude="42.3601N",
                longitude="71.0589W",
                timezone="America/New_York",
                name="Father"
            ),
            Subject(
                datetime="1985-04-20T23:45:00",
                latitude="47.6062N",
                longitude="122.3321W",
                timezone="America/Los_Angeles",
                name="Child 1"
            ),
            Subject(
                datetime="1988-09-12T07:20:00",
                latitude="47.6062N",
                longitude="122.3321W",
                timezone="America/Los_Angeles",
                name="Child 2"
            )
        ]
        
        # Calculate all charts at once
        charts = await self.chart_service.calculate_batch_charts(
            subjects=family,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        print("Family Chart Summary:")
        for i, chart in enumerate(charts):
            subject = family[i]
            sun = chart.objects.get('Sun', {})
            moon = chart.objects.get('Moon', {})
            
            print(f"\n{subject.name}:")
            print(f"  Sun: {sun.get('sign', 'Unknown')}")
            print(f"  Moon: {moon.get('sign', 'Unknown')}")
        
        return charts
    
    async def example_current_transits(self):
        """Example: Current planetary transits"""
        print("\n=== EXAMPLE 5: Current Transits ===")
        
        # Natal chart to check transits against
        natal_subject = Subject(
            datetime="1980-12-25T10:00:00",
            latitude="34.0522N",
            longitude="118.2437W",
            timezone="America/Los_Angeles",
            name="Transit Example"
        )
        
        natal_chart = await self.chart_service.calculate_single_chart(
            subject=natal_subject,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        # Find current transits
        transits = await self.chart_service.find_transits(
            natal_chart=natal_chart.dict(),
            transit_date=datetime.now().isoformat()
        )
        
        print(f"Current transits for {natal_subject.name}:")
        for transit in transits[:5]:  # Show first 5 transits
            print(f"  Transit {transit['transit_planet']} "
                  f"{transit['aspect']} Natal {transit['natal_planet']}")
            print(f"    Orb: {transit['orb']:.1f}°")
            print(f"    Exact: {transit['exact_date']}")
        
        return transits
    
    async def example_moon_phases(self):
        """Example: Moon phases for the current month"""
        print("\n=== EXAMPLE 6: Moon Phases ===")
        
        # Get moon phases for the next 30 days
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        phases = await self.chart_service.get_moon_phases(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            timezone="UTC"
        )
        
        print(f"Moon phases from {start_date.date()} to {end_date.date()}:")
        for phase in phases:
            print(f"  {phase['phase'].title()}: {phase['datetime']}")
            print(f"    Moon in {phase['sign']}")
        
        return phases
    
    async def example_progressions(self):
        """Example: Secondary progressions"""
        print("\n=== EXAMPLE 7: Secondary Progressions ===")
        
        natal_subject = Subject(
            datetime="1975-05-10T16:30:00",
            latitude="37.7749N",
            longitude="122.4194W",
            timezone="America/Los_Angeles",
            name="Progression Example"
        )
        
        natal_chart = await self.chart_service.calculate_single_chart(
            subject=natal_subject,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        # Calculate progressions for current date
        progression_date = datetime.now().isoformat()
        
        progressions = await self.chart_service.calculate_progressions(
            natal_chart=natal_chart.dict(),
            progression_date=progression_date,
            progression_type="secondary"
        )
        
        print(f"Secondary progressions for {natal_subject.name}")
        print(f"Progressed to: {progression_date}")
        
        # Show progressed Sun and Moon
        prog_objects = progressions.get('objects', {})
        if 'Sun' in prog_objects:
            print(f"  Progressed Sun: {prog_objects['Sun'].get('sign', 'Unknown')}")
        if 'Moon' in prog_objects:
            print(f"  Progressed Moon: {prog_objects['Moon'].get('sign', 'Unknown')}")
        
        return progressions
    
    async def example_chart_patterns(self):
        """Example: Finding aspect patterns"""
        print("\n=== EXAMPLE 8: Aspect Patterns ===")
        
        # Chart that might have patterns
        subject = Subject(
            datetime="1992-08-29T12:00:00",
            latitude="40.7128N",
            longitude="74.0060W",
            timezone="America/New_York",
            name="Pattern Example"
        )
        
        chart = await self.chart_service.calculate_single_chart(
            subject=subject,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        # Find patterns
        patterns = await self.chart_service.find_aspect_patterns(
            chart_data=chart.dict(),
            pattern_types=["grand_trine", "t_square", "yod", "grand_cross"]
        )
        
        print(f"Aspect patterns in chart:")
        if patterns:
            for pattern in patterns:
                print(f"  {pattern['type'].title()}: "
                      f"{', '.join(pattern['planets'])}")
        else:
            print("  No major aspect patterns found")
        
        return patterns
    
    async def example_interpretations(self):
        """Example: Chart interpretations"""
        print("\n=== EXAMPLE 9: Chart Interpretations ===")
        
        subject = Subject(
            datetime="1995-11-11T11:11:00",
            latitude="48.8566N",
            longitude="2.3522E",
            timezone="Europe/Paris",
            name="Interpretation Example"
        )
        
        chart = await self.chart_service.calculate_single_chart(
            subject=subject,
            chart_type="natal",
            settings=ChartSettings()
        )
        
        # Get interpretations
        interpretations = await self.chart_service.interpret_chart(
            chart_data=chart.dict(),
            interpretation_type="basic"
        )
        
        print(f"Basic interpretations for {subject.name}:")
        
        # Show some aspect interpretations
        if 'aspects' in interpretations:
            print("\nKey Aspects:")
            for interp in interpretations['aspects'][:3]:  # First 3
                print(f"  {interp['aspect']}")
                print(f"    {interp['meaning']}")
        
        # Show some house interpretations
        if 'houses' in interpretations:
            print("\nPlanetary Houses:")
            for interp in interpretations['houses'][:3]:  # First 3
                print(f"  {interp['placement']}")
                print(f"    {interp['interpretation']}")
        
        return interpretations


async def run_all_examples():
    """Run all examples"""
    examples = AstrologyExamples()
    
    print("IMMANUEL MCP SERVER - EXAMPLE USAGE")
    print("=" * 50)
    
    # Run each example
    await examples.example_natal_chart()
    await examples.example_with_asteroids()
    await examples.example_synastry()
    await examples.example_batch_family_charts()
    await examples.example_current_transits()
    await examples.example_moon_phases()
    await examples.example_progressions()
    await examples.example_chart_patterns()
    await examples.example_interpretations()
    
    print("\n" + "=" * 50)
    print("All examples completed!")


async def interactive_example():
    """Interactive example where user can input their own data"""
    print("IMMANUEL MCP - INTERACTIVE CHART CALCULATOR")
    print("=" * 50)
    
    # Get user input
    print("\nEnter birth information:")
    
    date_str = input("Birth date (YYYY-MM-DD): ")
    time_str = input("Birth time (HH:MM in 24hr format): ")
    datetime_str = f"{date_str}T{time_str}:00"
    
    lat_str = input("Latitude (e.g., 40.7128N or 40.7128): ")
    lon_str = input("Longitude (e.g., 74.0060W or -74.0060): ")
    
    timezone = input("Timezone (e.g., America/New_York, or press Enter for UTC): ")
    if not timezone:
        timezone = "UTC"
    
    name = input("Name (optional): ")
    
    # Create subject and calculate chart
    subject = Subject(
        datetime=datetime_str,
        latitude=lat_str,
        longitude=lon_str,
        timezone=timezone,
        name=name or "Chart"
    )
    
    service = ChartService()
    
    print("\nCalculating chart...")
    chart = await service.calculate_single_chart(
        subject=subject,
        chart_type="natal",
        settings=ChartSettings()
    )
    
    # Display results
    print(f"\n{'=' * 50}")
    print(f"NATAL CHART FOR: {subject.name}")
    print(f"{'=' * 50}")
    print(f"Birth: {subject.datetime} {subject.timezone}")
    print(f"Location: {subject.latitude}, {subject.longitude}")
    
    # Planets
    print(f"\n{'PLANETARY POSITIONS':^50}")
    print(f"{'-' * 50}")
    
    for obj_name, obj_data in chart.objects.items():
        if obj_name in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                        'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
            sign = obj_data['sign']
            deg = obj_data['sign_longitude']
            house = obj_data.get('house', '-')
            retro = 'R' if obj_data.get('retrograde') else ''
            
            print(f"{obj_name:<10} {sign:<12} {deg:>6.2f}° "
                  f"House {house:<3} {retro}")
    
    # Major aspects
    print(f"\n{'MAJOR ASPECTS':^50}")
    print(f"{'-' * 50}")
    
    major_aspects = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
    shown = 0
    for aspect in chart.aspects:
        if aspect['type'].lower() in major_aspects and shown < 10:
            print(f"{aspect['first']:<10} {aspect['type']:<12} "
                  f"{aspect['second']:<10} orb: {aspect['orb']:.1f}°")
            shown += 1
    
    # Save option
    save = input("\nSave full chart data to JSON? (y/n): ")
    if save.lower() == 'y':
        filename = f"chart_{name or 'output'}_{date_str}.json"
        with open(filename, 'w') as f:
            json.dump(chart.dict(), f, indent=2)
        print(f"Chart saved to: {filename}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_example())
    else:
        asyncio.run(run_all_examples())