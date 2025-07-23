#!/usr/bin/env python3
"""
Google Directions API vs Routes API Comparison Script

This script reads geohash pairs from CSV/Excel, converts them to lat/lng coordinates,
calls both Google Directions API and Routes API, and saves all response fields to CSV.
"""

import pandas as pd
import requests
import json
import csv
import time
from typing import Dict, Any, Tuple, List
import argparse
import os
from datetime import datetime
import pygeohash as pgh

class GoogleAPIComparison:
    def __init__(self, directions_api_key: str, routes_api_key: str):
        """
        Initialize the API comparison tool
        
        Args:
            directions_api_key: API key for Google Directions API
            routes_api_key: API key for Google Routes API
        """
        self.directions_api_key = directions_api_key
        self.routes_api_key = routes_api_key
        self.directions_base_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.routes_base_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        
    def geohash_to_coordinates(self, geohash: str) -> Tuple[float, float]:
        """
        Convert geohash to latitude and longitude coordinates
        
        Args:
            geohash: The geohash string
            
        Returns:
            Tuple of (latitude, longitude)
        """
        try:
            lat, lng = pgh.decode(geohash)
            return lat, lng
        except Exception as e:
            print(f"Error decoding geohash {geohash}: {e}")
            return None, None
    
    def call_directions_api(self, origin_lat: float, origin_lng: float, 
                          dest_lat: float, dest_lng: float) -> Dict[str, Any]:
        """
        Call Google Directions API
        
        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            
        Returns:
            API response as dictionary
        """
        params = {
            'key': self.directions_api_key,
            'origin': f"{origin_lat},{origin_lng}",
            'destination': f"{dest_lat},{dest_lng}",
            'language': 'en-US'
        }
        
        try:
            response = requests.get(self.directions_base_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Directions API: {e}")
            return {"error": str(e)}
    
    def call_routes_api(self, origin_lat: float, origin_lng: float, 
                       dest_lat: float, dest_lng: float) -> Dict[str, Any]:
        """
        Call Google Routes API
        
        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            
        Returns:
            API response as dictionary
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-FieldMask': '*'
        }
        
        payload = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin_lat,
                        "longitude": origin_lng
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": dest_lat,
                        "longitude": dest_lng
                    }
                }
            },
            "languageCode": "en-US"
        }
        
        try:
            response = requests.post(
                f"{self.routes_base_url}?key={self.routes_api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Routes API: {e}")
            return {"error": str(e)}
    
    def flatten_json(self, data: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """
        Flatten nested JSON for CSV output
        
        Args:
            data: Dictionary to flatten
            prefix: Prefix for keys
            
        Returns:
            Flattened dictionary
        """
        flattened = {}
        
        if not isinstance(data, dict):
            return {prefix: data}
            
        for key, value in data.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self.flatten_json(value, new_key))
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    for i, item in enumerate(value):
                        flattened.update(self.flatten_json(item, f"{new_key}_{i}"))
                else:
                    flattened[new_key] = json.dumps(value)
            else:
                flattened[new_key] = value
                
        return flattened
    
    def process_geohash_pairs(self, input_file: str, output_file: str = None) -> None:
        """
        Process geohash pairs from CSV/Excel file and call both APIs
        
        Args:
            input_file: Path to input CSV/Excel file
            output_file: Path to output CSV file (optional)
        """
        # Read input file
        if input_file.endswith('.xlsx') or input_file.endswith('.xls'):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file)
        
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/Users/vidhi.porwal/Desktop/api_comparison_results_{timestamp}.csv"
        
        results = []
        
        print(f"Processing {len(df)} geohash pairs...")
        
        for index, row in df.iterrows():
            print(f"Processing pair {index + 1}/{len(df)}")
            
            # Extract geohashes (adjust column names as needed)
            customer_geohash = row.get('customer_geohash', row.get('cx_geohash', row.get('CX_GH', '')))
            restaurant_geohash = row.get('restaurant_geohash', row.get('rx_geohash', row.get('RX_GH', '')))
            
            if not customer_geohash or not restaurant_geohash:
                print(f"Warning: Missing geohash data in row {index + 1}")
                continue
            
            # Convert geohashes to coordinates
            origin_lat, origin_lng = self.geohash_to_coordinates(customer_geohash)
            dest_lat, dest_lng = self.geohash_to_coordinates(restaurant_geohash)
            
            if None in [origin_lat, origin_lng, dest_lat, dest_lng]:
                print(f"Warning: Invalid geohash data in row {index + 1}")
                continue
            
            # Generate the actual URLs and request bodies used
            directions_url = f"https://maps.googleapis.com/maps/api/directions/json?key={self.directions_api_key}&origin={origin_lat},{origin_lng}&destination={dest_lat},{dest_lng}&language=en-US"
            
            routes_request_body = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": origin_lat,
                            "longitude": origin_lng
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": dest_lat,
                            "longitude": dest_lng
                        }
                    }
                },
                "languageCode": "en-US"
            }
            
            # Call both APIs
            directions_response = self.call_directions_api(origin_lat, origin_lng, dest_lat, dest_lng)
            routes_response = self.call_routes_api(origin_lat, origin_lng, dest_lat, dest_lng)
            
            # Prepare result row
            result_row = {
                'pair_index': index + 1,
                'customer_geohash': customer_geohash,
                'restaurant_geohash': restaurant_geohash,
                'customer_lat': origin_lat,
                'customer_lng': origin_lng,
                'destination_lat': dest_lat,
                'destination_lng': dest_lng,
                'directions_api_url': directions_url,
                'routes_api_request_body': json.dumps(routes_request_body, indent=2),
                'directions_api_response': json.dumps(directions_response, indent=2),
                'routes_api_response': json.dumps(routes_response, indent=2),
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(result_row)
            
            # Add delay to respect API rate limits
            time.sleep(0.1)
        
        # Save results to CSV and Excel
        if results:
            results_df = pd.DataFrame(results)
            results_df.to_csv(output_file, index=False)
            
            # Also save as Excel
            excel_file = output_file.replace('.csv', '.xlsx')
            results_df.to_excel(excel_file, index=False)
            
            print(f"Results saved to:")
            print(f"  CSV: {output_file}")
            print(f"  Excel: {excel_file}")
            print(f"Processed {len(results)} pairs successfully")
        else:
            print("No valid results to save")

def create_sample_data():
    """Create a sample CSV file with geohash pairs for testing"""
    sample_data = [
        {
            'customer_geohash': 'tub3xru',  # Approx: 26.4692, 80.3030
            'restaurant_geohash': 'tub6xru'  # Approx: 26.4732, 80.3515
        },
        {
            'customer_geohash': 'tub3xre',
            'restaurant_geohash': 'tub6xre'
        }
    ]
    
    df = pd.DataFrame(sample_data)
    df.to_csv('sample_geohash_pairs.csv', index=False)
    print("Sample data created: sample_geohash_pairs.csv")

def main():
    """Main function to run the API comparison"""
    parser = argparse.ArgumentParser(description='Compare Google Directions API vs Routes API')
    parser.add_argument('--input', '-i', required=True, help='Input CSV/Excel file with geohash pairs')
    parser.add_argument('--output', '-o', help='Output CSV file (optional)')
    parser.add_argument('--directions-key', required=True, help='Google Directions API key')
    parser.add_argument('--routes-key', required=True, help='Google Routes API key')
    parser.add_argument('--create-sample', action='store_true', help='Create sample data file')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_data()
        return
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found")
        return
    
    # Initialize comparison tool
    comparison = GoogleAPIComparison(args.directions_key, args.routes_key)
    
    # Process the geohash pairs
    comparison.process_geohash_pairs(args.input, args.output)

if __name__ == "__main__":
    main() 