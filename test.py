"""
Test suite for Immanuel MCP Server
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from immanuel_mcp.models import Subject, ChartSettings, ChartRequest
from immanuel_mcp.chart_service import ChartService
from immanuel_mcp.utils import (
    parse_coordinates,
    normalize_timezone,
    zodiac_position_to_string,
    calculate_orb,
    format_aspect_string
)


class TestUtils:
    """Test utility functions"""
    
    def test_parse_coordinates_decimal(self):
        """Test parsing decimal coordinates"""
        # Latitude
        lat, dir = parse_coordinates("34.05N", "latitude")
        assert lat == 34.05
        assert dir == "N"
        
        lat, dir = parse_coordinates("-34.05", "latitude")
        assert lat == -34.05
        assert dir == "S"
        
        # Longitude
        lon, dir = parse_coordinates("118.24W", "longitude")
        assert lon == 118.24
        assert dir == "W"
        
        lon, dir = parse_coordinates("-118.24", "longitude")
        assert lon == -118.24
        assert dir == "W"
    
    def test_parse_coordinates_dms(self):
        """Test parsing DMS format coordinates"""
        lat, dir = parse_coordinates("34N03'00\"", "latitude")
        assert abs(lat - 34.05) < 0.01
        assert dir == "N"
    
    def test_parse_coordinates_invalid(self):
        """Test invalid coordinate handling"""
        with pytest.raises(ValueError):
            parse_coordinates("91N", "latitude")  # Out of range
        
        with pytest.raises(ValueError):
            parse_coordinates("181W", "longitude")  # Out of range
    
    def test_normalize_timezone(self):
        """Test timezone normalization"""
        assert normalize_timezone("America/Los_Angeles") == "America/Los_Angeles"
        assert normalize_timezone("PST") == "America/Los_Angeles"
        assert normalize_timezone("UTC") == "UTC"
        assert normalize_timezone(None) == "UTC"
        assert normalize_timezone("invalid") == "UTC"  # Fallback
    
    def test_zodiac_position_to_string(self):
        """Test zodiac position formatting"""
        assert zodiac_position_to_string(15.5) == "15°30' Aries"
        assert zodiac_position_to_string(45.25) == "15°15' Taurus"
        assert zodiac_position_to_string(280.0) == "10°00' Capricorn"
    
    def test_calculate_orb(self):
        """Test orb calculation"""
        # Exact conjunction
        assert calculate_orb(10, 10, 0) == 0
        
        # Close conjunction
        assert calculate_orb(10, 12, 0) == 2
        
        # Opposition
        assert calculate_orb(10, 190, 180) == 0
        
        # Trine with orb
        assert abs(calculate_orb(10, 132, 120) - 2) < 0.1
    
    def test_format_aspect_string(self):
        """Test aspect string formatting"""
        result = format_aspect_string("Sun", "conjunction", "Moon", 2.5, True)
        assert "☉ ☌ ☽" in result
        assert "2°30'" in result
        assert "applying" in result


class TestModels:
    """Test Pydantic models"""
    
    def test_subject_validation(self):
        """Test Subject model validation"""
        # Valid subject
        subject = Subject(
            datetime="2000-01-01T10:00:00",
            latitude="34.05N",
            longitude="118.24W",
            timezone="America/Los_Angeles"
        )
        assert subject.datetime == "2000-01-01T10:00:00"
        
        # Invalid datetime
        with pytest.raises(ValueError):
            Subject(
                datetime="invalid",
                latitude="34.05N",
                longitude="118.24W"
            )
        
        # Invalid coordinates
        with pytest.raises(ValueError):
            Subject(
                datetime="2000-01-01T10:00:00",
                latitude="91N",  # Out of range
                longitude="118.24W"
            )
    
    def test_chart_settings_validation(self):
        """Test ChartSettings validation"""
        # Valid settings
        settings = ChartSettings(
            house_system="placidus",
            include_objects=["CERES", "CHIRON"]
        )
        assert settings.house_system == "placidus"
        assert "CERES" in settings.include_objects
        
        # Invalid house system
        with pytest.raises(ValueError):
            ChartSettings(house_system="invalid")
        
        # Invalid object
        with pytest.raises(ValueError):
            ChartSettings(include_objects=["INVALID_OBJECT"])
    
    def test_chart_request_validation(self):
        """Test ChartRequest validation"""
        subject = Subject(
            datetime="2000-01-01T10:00:00",
            latitude="34.05N",
            longitude="118.24W"
        )
        
        # Valid natal chart request
        request = ChartRequest(
            subjects=[subject],
            chart_type="natal"
        )
        assert len(request.subjects) == 1
        
        # Synastry requires 2 subjects
        with pytest.raises(ValueError):
            ChartRequest(
                subjects=[subject],
                chart_type="synastry"
            )
        
        # Valid synastry request
        subject2 = Subject(
            datetime="1990-05-15T14:30:00",
            latitude="40.71N",
            longitude="74.00W"
        )
        request = ChartRequest(
            subjects=[subject, subject2],
            chart_type="synastry"
        )
        assert len(request.subjects) == 2


class TestChartService:
    """Test ChartService functionality"""
    
    @pytest.fixture
    def chart_service(self):
        """Create ChartService instance"""
        return ChartService()
    
    @pytest.fixture
    def sample_subject(self):
        """Create sample subject"""
        return Subject(
            datetime="2000-01-01T10:00:00",
            latitude="34.05N",
            longitude="118.24W",
            timezone="America/Los_Angeles"
        )
    
    @pytest.mark.asyncio
    async def test_calculate_single_chart(self, chart_service, sample_subject):
        """Test single chart calculation"""
        with patch('immanuel.charts.Natal') as mock_natal:
            # Mock the chart object
            mock_chart = Mock()
            mock_chart.objects = {
                'sun': Mock(
                    name='Sun',
                    longitude=280.5,
                    sign=Mock(name='Capricorn'),
                    sign_longitude=10.5,
                    house=Mock(number=10),
                    speed=1.019,
                    retrograde=False
                )
            }
            mock_chart.aspects = {}
            mock_chart.houses = {
                1: Mock(
                    number=1,
                    sign=Mock(name='Aries'),
                    longitude=15.0,
                    objects=[]
                )
            }
            mock_natal.return_value = mock_chart
            
            # Calculate chart
            settings = ChartSettings()
            result = await chart_service.calculate_single_chart(
                subject=sample_subject,
                chart_type="natal",
                settings=settings
            )
            
            # Verify result
            assert result.metadata['chart_type'] == 'natal'
            assert 'Sun' in result.objects
            assert result.objects['Sun']['sign'] == 'Capricorn'
            assert result.objects['Sun']['house'] == 10
    
    @pytest.mark.asyncio
    async def test_batch_calculate_charts(self, chart_service, sample_subject):
        """Test batch chart calculation"""
        subjects = [sample_subject, sample_subject]  # Two identical for simplicity
        settings = ChartSettings()
        
        with patch.object(chart_service, 'calculate_single_chart') as mock_calc:
            mock_calc.return_value = Mock(dict=lambda: {"test": "data"})
            
            results = await chart_service.calculate_batch_charts(
                subjects=subjects,
                chart_type="natal",
                settings=settings
            )
            
            assert len(results) == 2
            assert mock_calc.call_count == 2
    
    @pytest.mark.asyncio
    async def test_interpret_chart(self, chart_service):
        """Test chart interpretation"""
        chart_data = {
            'objects': {
                'Sun': {
                    'longitude': 280.5,
                    'sign': 'Capricorn',
                    'house': 10
                },
                'Moon': {
                    'longitude': 40.0,
                    'sign': 'Taurus',
                    'house': 2
                }
            },
            'aspects': [
                {
                    'first': 'Sun',
                    'second': 'Moon',
                    'type': 'trine',
                    'orb': 2.5,
                    'applying': True
                }
            ]
        }
        
        interpretation = await chart_service.interpret_chart(
            chart_data=chart_data,
            interpretation_type='basic'
        )
        
        assert 'aspects' in interpretation
        assert 'houses' in interpretation
        assert len(interpretation['aspects']) > 0
        assert len(interpretation['houses']) > 0
    
    @pytest.mark.asyncio
    async def test_compare_charts_synastry(self, chart_service):
        """Test synastry comparison"""
        chart1 = {
            'objects': {
                'Sun': {'longitude': 10.0},
                'Moon': {'longitude': 40.0}
            }
        }
        
        chart2 = {
            'objects': {
                'Sun': {'longitude': 130.0},
                'Venus': {'longitude': 10.0}
            }
        }
        
        comparison = await chart_service.compare_charts(
            chart1=chart1,
            chart2=chart2,
            comparison_type='synastry'
        )
        
        assert comparison['type'] == 'synastry'
        assert 'inter_aspects' in comparison
        # Should find Sun1 trine Sun2 (120 degrees)
        assert any(
            asp['aspect'] == 'trine' 
            for asp in comparison['inter_aspects']
        )
    
    def test_cache_key_generation(self, chart_service, sample_subject):
        """Test cache key generation"""
        settings = ChartSettings()
        
        key1 = chart_service._get_cache_key(sample_subject, "natal", settings)
        key2 = chart_service._get_cache_key(sample_subject, "natal", settings)
        
        # Same inputs should generate same key
        assert key1 == key2
        
        # Different chart type should generate different key
        key3 = chart_service._get_cache_key(sample_subject, "solar_return", settings)
        assert key1 != key3
    
    def test_check_aspect(self, chart_service):
        """Test aspect checking"""
        # Exact conjunction
        aspect = chart_service._check_aspect(0)
        assert aspect['name'] == 'conjunction'
        assert aspect['orb'] == 0
        
        # Trine with orb
        aspect = chart_service._check_aspect(118)  # 2 degree orb
        assert aspect['name'] == 'trine'
        assert aspect['orb'] == 2
        
        # No aspect
        aspect = chart_service._check_aspect(45)
        assert aspect is None


@pytest.mark.asyncio
class TestMCPIntegration:
    """Test MCP server integration"""
    
    async def test_calculate_chart_tool(self):
        """Test the calculate_chart MCP tool"""
        from immanuel_mcp.main import calculate_chart
        
        with patch('immanuel_mcp.main.chart_service') as mock_service:
            mock_service.calculate_single_chart = AsyncMock(
                return_value=Mock(dict=lambda: {"test": "result"})
            )
            
            args = Mock(
                datetime="2000-01-01T10:00:00",
                latitude="34.05N",
                longitude="118.24W",
                timezone="America/Los_Angeles",
                chart_type="natal",
                house_system="placidus",
                include_objects=None
            )
            
            result = await calculate_chart(args)
            
            assert result == {"test": "result"}
            mock_service.calculate_single_chart.assert_called_once()
    
    async def test_get_chart_info_tool(self):
        """Test the get_chart_info MCP tool"""
        from immanuel_mcp.main import get_chart_info
        
        result = await get_chart_info()
        
        assert 'chart_types' in result
        assert 'house_systems' in result
        assert 'objects' in result
        assert 'aspects' in result
        assert 'natal' in result['chart_types']
        assert 'placidus' in result['house_systems']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])