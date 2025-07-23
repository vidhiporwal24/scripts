#!/usr/bin/env python3
"""
Enhanced Google API Comparison Script
Better organized output with key metrics and side-by-side comparison
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
import pygeohash as pgh
import argparse

class EnhancedAPIComparison:
    def __init__(self, directions_key: str, routes_key: str):
        self.directions_key = directions_key
        self.routes_key = routes_key
        
    def geohash_to_coords(self, geohash: str):
        """Convert geohash to lat/lng"""
        try:
            return pgh.decode(geohash)
        except:
            return None, None
    
    def call_directions_api(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float):
        """Call Google Directions API with timing"""
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            'key': self.directions_key,
            'origin': f"{origin_lat},{origin_lng}",
            'destination': f"{dest_lat},{dest_lng}",
            'language': 'en-US'
        }
        
        start_time = time.time()
        try:
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            response.raise_for_status()
            result = response.json()
            result['_response_time_ms'] = round(response_time * 1000, 2)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            return {"error": str(e), "_response_time_ms": round(response_time * 1000, 2)}
    
    def call_routes_api(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float):
        """Call Google Routes API with timing"""
        url = f"https://routes.googleapis.com/directions/v2:computeRoutes?key={self.routes_key}"
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
        
        start_time = time.time()
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response_time = time.time() - start_time
            response.raise_for_status()
            result = response.json()
            result['_response_time_ms'] = round(response_time * 1000, 2)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            return {"error": str(e), "_response_time_ms": round(response_time * 1000, 2)}
    
    def extract_key_metrics(self, directions_resp, routes_resp):
        """Extract key comparable metrics from both APIs"""
        metrics = {}
        
        # Directions API metrics
        try:
            if 'routes' in directions_resp and directions_resp['routes']:
                route = directions_resp['routes'][0]
                if 'legs' in route and route['legs']:
                    leg = route['legs'][0]
                    metrics['directions_distance_text'] = leg.get('distance', {}).get('text', '')
                    metrics['directions_distance_meters'] = leg.get('distance', {}).get('value', 0)
                    metrics['directions_duration_text'] = leg.get('duration', {}).get('text', '')
                    metrics['directions_duration_seconds'] = leg.get('duration', {}).get('value', 0)
                    metrics['directions_start_address'] = leg.get('start_address', '')
                    metrics['directions_end_address'] = leg.get('end_address', '')
            
            metrics['directions_status'] = directions_resp.get('status', 'UNKNOWN')
            metrics['directions_response_time_ms'] = directions_resp.get('_response_time_ms', 0)
            metrics['directions_has_error'] = 'error' in directions_resp
            
        except Exception as e:
            metrics['directions_extraction_error'] = str(e)
        
        # Routes API metrics
        try:
            if 'routes' in routes_resp and routes_resp['routes']:
                route = routes_resp['routes'][0]
                metrics['routes_distance_meters'] = route.get('distanceMeters', 0)
                metrics['routes_duration'] = route.get('duration', '')
                
                if 'legs' in route and route['legs']:
                    leg = route['legs'][0]
                    metrics['routes_leg_distance_meters'] = leg.get('distanceMeters', 0)
                    metrics['routes_leg_duration'] = leg.get('duration', '')
                    
                    # Polyline
                    if 'polyline' in route:
                        metrics['routes_has_polyline'] = True
                        metrics['routes_polyline_type'] = 'encoded_polyline' if 'encodedPolyline' in route['polyline'] else 'geo_json'
                    else:
                        metrics['routes_has_polyline'] = False
                        
            metrics['routes_response_time_ms'] = routes_resp.get('_response_time_ms', 0)
            metrics['routes_has_error'] = 'error' in routes_resp
            
        except Exception as e:
            metrics['routes_extraction_error'] = str(e)
        
                    # Comparison metrics (only differences in absolute units, no percentages)
            try:
                if metrics.get('directions_distance_meters', 0) > 0 and metrics.get('routes_distance_meters', 0) > 0:
                    dir_dist = metrics['directions_distance_meters']
                    routes_dist = metrics['routes_distance_meters']
                    metrics['distance_difference_meters'] = abs(dir_dist - routes_dist)
                
                if metrics.get('directions_duration_seconds', 0) > 0 and metrics.get('routes_duration'):
                    # Convert routes duration (like "123s") to seconds
                    routes_duration_str = metrics['routes_duration']
                    if routes_duration_str.endswith('s'):
                        routes_duration_sec = float(routes_duration_str[:-1])
                        dir_duration = metrics['directions_duration_seconds']
                        metrics['duration_difference_seconds'] = abs(dir_duration - routes_duration_sec)
                
                # Response time comparison
                dir_time = metrics.get('directions_response_time_ms', 0)
                routes_time = metrics.get('routes_response_time_ms', 0)
                if dir_time > 0 and routes_time > 0:
                    metrics['response_time_difference_ms'] = abs(dir_time - routes_time)
                    metrics['faster_api'] = 'directions' if dir_time < routes_time else 'routes'
                    
            except Exception as e:
                metrics['comparison_error'] = str(e)
            
        return metrics
    
    def flatten_dict(self, d, parent_key='', sep='_'):
        """Flatten nested dictionary for CSV output"""
        items = []
        if isinstance(d, dict):
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(self.flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    if v and isinstance(v[0], dict):
                        for i, item in enumerate(v):
                            items.extend(self.flatten_dict(item, f"{new_key}{sep}{i}", sep=sep).items())
                    else:
                        items.append((new_key, json.dumps(v)))
                else:
                    items.append((new_key, v))
        return dict(items)
    
    def process_pairs(self, input_file: str, output_file: str = None):
        """Process geohash pairs and call both APIs"""
        
        # Read input file
        if input_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file)
        
        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"enhanced_comparison_{timestamp}.csv"
        
        results = []
        
        print(f"Processing {len(df)} geohash pairs...")
        
        for index, row in df.iterrows():
            print(f"Processing pair {index + 1}/{len(df)}")
            
            # Get geohashes - flexible column names
            cx_geohash = row.get('CX_GH', row.get('customer_geohash', row.get('cx_geohash', '')))
            rx_geohash = row.get('RX_GH', row.get('restaurant_geohash', row.get('rx_geohash', '')))
            
            if not cx_geohash or not rx_geohash:
                print(f"Warning: Missing geohash data in row {index + 1}")
                continue
            
            # Convert to coordinates
            cx_lat, cx_lng = self.geohash_to_coords(cx_geohash)
            rx_lat, rx_lng = self.geohash_to_coords(rx_geohash)
            
            if None in [cx_lat, cx_lng, rx_lat, rx_lng]:
                print(f"Warning: Invalid geohash data in row {index + 1}")
                continue
            
            # Call APIs
            directions_resp = self.call_directions_api(cx_lat, cx_lng, rx_lat, rx_lng)
            routes_resp = self.call_routes_api(cx_lat, cx_lng, rx_lat, rx_lng)
            
            # Extract key metrics for comparison
            key_metrics = self.extract_key_metrics(directions_resp, routes_resp)
            
            # Create result row with organized structure
            result = {
                # Basic info
                'pair_index': index + 1,
                'cx_geohash': cx_geohash,
                'rx_geohash': rx_geohash,
                'cx_lat': cx_lat,
                'cx_lng': cx_lng,
                'rx_lat': rx_lat,
                'rx_lng': rx_lng,
            }
            
            # Add key metrics first for easy comparison
            result.update(key_metrics)
            
            # Add full API responses (flattened)
            directions_flat = self.flatten_dict(directions_resp, 'directions_full')
            routes_flat = self.flatten_dict(routes_resp, 'routes_full')
            
            result.update(directions_flat)
            result.update(routes_flat)
            
            results.append(result)
            
            # Rate limiting
            time.sleep(0.1)
        
        # Save results
        if results:
            results_df = pd.DataFrame(results)
            
            # Remove redundant columns and organize better
            cols_to_remove = [
                # Remove duplicate response time columns
                'directions_full__response_time_ms', 'routes_full__response_time_ms',
                # Remove percentage columns (keeping only absolute differences)
                'distance_difference_percent', 'duration_difference_percent',
                # Remove timestamp as requested
                'timestamp',
                # Remove response time columns as requested
                'directions_response_time_ms', 'routes_response_time_ms'
            ]
            
            # Remove redundant columns
            for col in cols_to_remove:
                if col in results_df.columns:
                    results_df = results_df.drop(columns=[col])
            
            # Organize columns for better readability
            basic_cols = ['pair_index', 'cx_geohash', 'rx_geohash', 'cx_lat', 'cx_lng', 'rx_lat', 'rx_lng']
            comparison_cols = [col for col in results_df.columns if any(x in col for x in ['distance_difference', 'duration_difference', 'response_time_difference', 'faster_api'])]
            key_metric_cols = [col for col in results_df.columns if col.startswith(('directions_', 'routes_')) and not col.startswith(('directions_full', 'routes_full')) and col not in basic_cols]
            
            # Group related comparison fields side by side
            side_by_side_groups = [
                # Distance comparison
                ['directions_distance_text', 'routes_distance_meters', 'directions_distance_meters'],
                # Duration comparison  
                ['directions_duration_text', 'routes_duration', 'directions_duration_seconds'],
                # Polyline comparison
                ['directions_full_routes_0_overview_polyline_points', 'routes_full_routes_0_legs_0_polyline_encodedPolyline'],
                # Leg distance comparison
                ['directions_full_routes_0_legs_0_distance_text', 'routes_full_routes_0_legs_0_distanceMeters', 'directions_full_routes_0_legs_0_distance_value'],
                # Leg duration comparison
                ['directions_full_routes_0_legs_0_duration_text', 'routes_full_routes_0_legs_0_duration', 'directions_full_routes_0_legs_0_duration_value'],
            ]
            
            # Create ordered side-by-side columns
            side_by_side_cols = []
            for group in side_by_side_groups:
                for col in group:
                    if col in results_df.columns:
                        side_by_side_cols.append(col)
            
            # Remove side-by-side columns from other categories to avoid duplicates
            key_metric_cols = [col for col in key_metric_cols if col not in side_by_side_cols]
            full_response_cols = [col for col in results_df.columns if col.startswith(('directions_full', 'routes_full')) and col not in side_by_side_cols]
            
            # Reorder columns with side-by-side groupings
            ordered_cols = basic_cols + comparison_cols + side_by_side_cols + key_metric_cols + full_response_cols
            available_cols = [col for col in ordered_cols if col in results_df.columns]
            results_df = results_df.reindex(columns=available_cols)
            
            results_df.to_csv(output_file, index=False)
            
            # Also create Excel with multiple sheets
            excel_file = output_file.replace('.csv', '.xlsx')
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # Summary sheet with key metrics only  
                summary_cols = basic_cols + comparison_cols + side_by_side_cols + key_metric_cols
                available_summary_cols = [col for col in summary_cols if col in results_df.columns]
                summary_df = results_df[available_summary_cols]
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Full data sheet
                results_df.to_excel(writer, sheet_name='Full_Data', index=False)
                
                # Comparison stats (only for numeric columns)
                stats_data = []
                for col in comparison_cols:
                    if col in results_df.columns and pd.api.types.is_numeric_dtype(results_df[col]):
                        stats_data.append({
                            'Metric': col,
                            'Mean': results_df[col].mean(),
                            'Max': results_df[col].max(),
                            'Min': results_df[col].min(),
                            'Std': results_df[col].std()
                        })
                
                if stats_data:
                    stats_df = pd.DataFrame(stats_data)
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            print(f"\n✅ Results saved to:")
            print(f"  📄 CSV (all data): {output_file}")
            print(f"  📊 Excel (organized): {excel_file}")
            print(f"📈 Processed {len(results)} pairs successfully")
            print(f"📋 Total columns: {len(results_df.columns)}")
            
            # Show summary statistics
            if comparison_cols:
                print(f"\n🔍 Comparison Summary:")
                for col in comparison_cols[:5]:  # Show first 5 comparison metrics
                    if col in results_df.columns and pd.api.types.is_numeric_dtype(results_df[col]) and results_df[col].notna().any():
                        avg_val = results_df[col].mean()
                        print(f"  {col}: avg = {avg_val:.2f}")
        else:
            print("❌ No valid results to save")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Google APIs Comparison')
    parser.add_argument('--input', '-i', required=True, help='Input CSV/Excel file')
    parser.add_argument('--output', '-o', help='Output CSV file')
    parser.add_argument('--directions-key', required=True, help='Directions API key')
    parser.add_argument('--routes-key', required=True, help='Routes API key')
    
    args = parser.parse_args()
    
    comparison = EnhancedAPIComparison(args.directions_key, args.routes_key)
    comparison.process_pairs(args.input, args.output)

if __name__ == "__main__":
    main() 