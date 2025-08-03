# Directions vs Routes API Response Comparison

This script compares the responses from Google Directions API and Google Routes API for geohash pairs, providing detailed analysis and metrics.

## Prerequisites

1. **Python 3.7 or higher**
2. **Google Cloud API Keys**:
   - Directions API key (Google Maps JavaScript API)
   - Routes API key (Routes API v2)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/vidhiporwal24/scripts.git
   cd scripts
   ```

2. Install required dependencies:
   ```bash
   pip install pandas requests pygeohash openpyxl
   ```

## How to Run

### Basic Usage

```bash
python directions_vs_routes_response_comparison.py \
  --input your_geohash_data.csv \
  --directions-key YOUR_DIRECTIONS_API_KEY \
  --routes-key YOUR_ROUTES_API_KEY \
  --output comparison_results.csv
```

### Input File Format

Your input file (CSV or Excel) should contain geohash columns with one of these naming conventions:
- `CX_GH` and `RX_GH` (customer and restaurant geohashes)
- `customer_geohash` and `restaurant_geohash`
- `cx_geohash` and `rx_geohash`

Example CSV:
```csv
CX_GH,RX_GH
9q8yy9mur,9q8yy9mvr
9q8zzb1kp,9q8zzb2mp
```

### Command Line Arguments

- `--input`, `-i`: Path to input CSV/Excel file (required)
- `--directions-key`: Your Google Directions API key (required)
- `--routes-key`: Your Google Routes API key (required) 
- `--output`, `-o`: Output CSV filename (optional, auto-generated if not provided)

### Example

```bash
python directions_vs_routes_response_comparison.py \
  --input geohash_pairs.xlsx \
  --directions-key AIzaSyD... \
  --routes-key AIzaSyR... \
  --output my_comparison_results.csv
```

## Output

The script generates two files:
1. **CSV file**: Complete comparison data with all metrics
2. **Excel file**: Organized into multiple sheets:
   - `Summary`: Key comparison metrics
   - `Full_Data`: Complete API responses
   - `Statistics`: Statistical summary of differences

## Reference Data

For sample data format and expected results, refer to: [Google Sheets Reference](https://docs.google.com/spreadsheets/d/1ZhVsT1fh1YFh4EZBj0UtQBFRQYlJ1ucOyWAOpokblDo/edit?gid=526652294#gid=526652294)

## Key Metrics Compared

- **Distance**: Meters and formatted text
- **Duration**: Seconds and formatted text  
- **Response Time**: API call performance
- **Polylines**: Route geometry data
- **Addresses**: Start/end address information
- **Status**: API response status codes

The script provides absolute differences between APIs for quantitative comparison.