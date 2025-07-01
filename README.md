# Immanuel MCP Server

A powerful Model Context Protocol (MCP) server for astrological chart calculations, designed specifically for Claude Desktop. This server exposes the comprehensive functionality of the [immanuel-python](https://github.com/theriftlab/immanuel-python) library through an easy-to-use MCP interface.

## 🌟 Features

### Core Capabilities
- **Natal Charts**: Complete birth chart calculations with planets, houses, and aspects
- **Multiple Chart Types**: Solar returns, lunar returns, progressions, solar arc directions
- **Relationship Analysis**: Synastry, composite, and Davison charts
- **Transit Tracking**: Current and future planetary transits to natal positions
- **Batch Processing**: Calculate multiple charts efficiently in one request
- **Caching System**: Smart caching based on input parameters for improved performance

### Advanced Features
- **Aspect Pattern Detection**: Find Grand Trines, T-Squares, Yods, and other configurations
- **Ephemeris Data**: Planetary positions over time ranges
- **Moon Phases**: Precise timing and zodiac positions of lunar phases
- **Retrograde Periods**: Track retrograde and shadow periods for all planets
- **Chart Interpretation**: Basic to detailed interpretations of chart features
- **Custom Orbs**: Configure aspect orbs for personalized analysis

### Technical Features
- **Multiple House Systems**: Placidus, Koch, Whole Sign, Equal, and more
- **Extended Objects**: Asteroids (Ceres, Pallas, Juno, Vesta), Chiron, Lilith
- **Flexible Coordinate Formats**: Supports decimal and DMS formats
- **Timezone Intelligence**: Automatic timezone resolution and validation
- **Comprehensive Validation**: Input validation with helpful error messages

## 📋 Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management
- Claude Desktop application

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/immanuel-mcp.git
cd immanuel-mcp
```

### 2. Set Up Environment with uv

```bash
# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 3. Install Swiss Ephemeris Data

The immanuel-python library requires Swiss Ephemeris data files:

```bash
# Create data directory
mkdir -p ~/.immanuel/ephemeris

# Download ephemeris files (you'll need at least these)
cd ~/.immanuel/ephemeris
wget https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
wget https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1
```

### 4. Configure Claude Desktop

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "immanuel": {
      "command": "uv",
      "args": ["run", "python", "-m", "immanuel_mcp.main"],
      "cwd": "/path/to/immanuel-mcp"
    }
  }
}
```

## 🎯 Usage Examples

Once configured, you can use these commands in Claude Desktop:

### Calculate a Natal Chart

```
Calculate a natal chart for January 1, 2000 at 10:00 AM in Los Angeles (34.05N, 118.24W)
```

### Find Current Transits

```
Show me the current transits to my natal Sun at 15 degrees Aries
```

### Compare Two Charts

```
Compare these two birth charts for relationship compatibility:
- Person 1: March 15, 1990, 2:30 PM, New York (40.71N, 74.00W)
- Person 2: July 22, 1988, 6:45 AM, London (51.51N, 0.13W)
```

### Track Moon Phases

```
Find all moon phases for the next month with their zodiac positions
```

### Batch Calculations

```
Calculate natal charts for these family members:
- Mom: June 1, 1960, 8:00 AM, Chicago
- Dad: October 15, 1958, 3:30 PM, Boston  
- Sister: April 20, 1985, 11:45 PM, Seattle
```

## 🛠️ Available Tools

### Core Chart Calculations

#### `calculate_chart`
Calculate a single astrological chart with comprehensive data.

**Parameters:**
- `datetime`: ISO format datetime (e.g., "2000-01-01T10:00:00")
- `latitude`: Latitude in format "32.72N" or "-32.72"
- `longitude`: Longitude in format "117.16W" or "-117.16"
- `timezone`: Optional timezone (e.g., "America/Los_Angeles")
- `chart_type`: Type of chart (natal, solar_return, progressed, etc.)
- `house_system`: House system to use (placidus, koch, whole_sign, etc.)
- `include_objects`: Additional objects like asteroids

#### `batch_calculate_charts`
Calculate multiple charts efficiently in one request.

**Parameters:**
- `subjects`: List of subjects with datetime, location, and timezone
- `chart_type`: Chart type for all subjects
- `settings`: Shared settings for all charts

### Analysis Tools

#### `interpret_chart`
Provide interpretations of chart features including aspects, houses, and dignities.

**Parameters:**
- `chart_data`: Previously calculated chart data
- `interpretation_type`: Level of detail (basic, detailed, aspects_only, houses_only)

#### `compare_charts`
Compare two charts for relationship analysis.

**Parameters:**
- `chart1`: First person's chart data
- `chart2`: Second person's chart data
- `comparison_type`: Type of comparison (synastry, composite, davison)

#### `find_aspect_patterns`
Identify significant aspect patterns like Grand Trines and T-Squares.

**Parameters:**
- `chart_data`: Chart to analyze
- `pattern_types`: Specific patterns to find

### Timing Tools

#### `find_transits`
Calculate current or future transits to a natal chart.

**Parameters:**
- `natal_chart`: Natal chart data
- `transit_date`: Date for transits (defaults to now)
- `aspect_orbs`: Custom orbs for aspects

#### `calculate_progressions`
Calculate progressed charts using various techniques.

**Parameters:**
- `natal_chart`: Natal chart data
- `progression_date`: Date to progress to
- `progression_type`: Type (secondary, solar_arc, tertiary)

#### `get_moon_phases`
Get moon phases between dates with exact times and positions.

**Parameters:**
- `start_date`: Start date for search
- `end_date`: End date for search
- `timezone`: Timezone for phase times

### Reference Tools

#### `get_ephemeris`
Get planetary positions over time.

**Parameters:**
- `start_date`: Start date
- `end_date`: End date
- `objects`: Objects to include
- `interval`: Data interval (daily, weekly, monthly)

#### `get_retrograde_periods`
Find retrograde periods for planets.

**Parameters:**
- `year`: Year to check
- `planets`: Planets to check

#### `get_chart_info`
Get information about available options.

**Returns:** Available chart types, house systems, objects, aspects, and dignities

## 📊 Response Format

All responses follow a consistent JSON structure:

```json
{
  "metadata": {
    "calculated_at": "2024-01-01T12:00:00Z",
    "chart_type": "natal",
    "house_system": "placidus",
    "timezone_used": "America/Los_Angeles",
    "cache_key": "sha256_hash"
  },
  "objects": {
    "Sun": {
      "longitude": 280.5,
      "sign": "Capricorn",
      "sign_longitude": 10.5,
      "house": 10,
      "speed": 1.019,
      "retrograde": false
    }
  },
  "aspects": [
    {
      "first": "Sun",
      "second": "Moon",
      "type": "trine",
      "orb": 2.3,
      "applying": true
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
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=immanuel_mcp

# Run specific test file
uv run pytest tests/test_server.py
```

## 🔧 Development

### Project Structure

```
immanuel_mcp/
├── __init__.py
├── main.py              # MCP server entry point
├── chart_service.py     # Core chart calculation logic
├── models.py           # Pydantic data models
├── utils.py            # Helper utilities
├── settings.py         # Configuration management
└── tests/
    ├── test_server.py
    ├── test_chart_service.py
    └── test_utils.py
```

### Code Style

The project uses:
- `black` for code formatting
- `ruff` for linting
- `mypy` for type checking

Format and lint code:

```bash
uv run black .
uv run ruff check .
uv run mypy .
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [immanuel-python](https://github.com/theriftlab/immanuel-python) for the excellent astrology library
- [Swiss Ephemeris](https://www.astro.com/swisseph/) for planetary calculations
- [MCP](https://modelcontextprotocol.io/) for the protocol specification
- The astrology community for domain knowledge and testing

## 📚 Resources

- [Immanuel Python Documentation](https://github.com/theriftlab/immanuel-python/wiki)
- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Swiss Ephemeris Documentation](https://www.astro.com/swisseph/swephprg.htm)
- [Astrology Basics](https://cafeastrology.com/astrology-basics)

## ⚠️ Disclaimer

This software is for educational and entertainment purposes. Astrological calculations are based on astronomical data and traditional interpretive frameworks. Users should apply their own judgment when using astrological information for decision-making.