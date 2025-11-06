"""
Flask API for Vietnam Coffee Data Portal
Optimized with caching and compression for better performance
"""
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request, render_template, send_from_directory, make_response
from flask_cors import CORS
from flask_caching import Cache
from flask_compress import Compress
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import sys
import traceback
from functools import wraps
from typing import Optional, Dict, List, Any, Tuple

# Import utility modules
try:
    from utils import (
        interpolate_time_series,
        calculate_growth_stats,
        format_dataframe_rows,
        safe_float,
        calculate_percentage
    )
    from db_utils import (
        create_database_engine,
        check_connection,
        get_db_connection
    )
except ImportError:
    # Fallback for relative imports
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from utils import (
        interpolate_time_series,
        calculate_growth_stats,
        format_dataframe_rows,
        safe_float,
        calculate_percentage
    )
    from db_utils import (
        create_database_engine,
        check_connection,
        get_db_connection
    )

# Import weather prediction service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../model'))
try:
    from predict_weather import WeatherPredictor
    WEATHER_PREDICTION_AVAILABLE = True
    weather_predictor = WeatherPredictor(
        model_dir=os.path.join(os.path.dirname(__file__), '../model/saved_models')
    )
except ImportError as e:
    WEATHER_PREDICTION_AVAILABLE = False
    weather_predictor = None
    print(f"⚠ Weather prediction not available: {e}")

# Set UTF-8 encoding for stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables - find .env in project root
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
if not os.path.exists(env_path):
    # If running from project root, try current directory
    env_path = '.env'
load_dotenv(dotenv_path=env_path)
print(f"📁 Loading .env from: {os.path.abspath(env_path)}")

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

# Enable CORS for all API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configure Caching (Simple in-memory cache)
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default
cache = Cache(app)

# Enable Response Compression
compress = Compress()
compress.init_app(app)

# Configure CORS to allow all origins (important for local development)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Database connection
DB_HOST = os.getenv('HOST')
DB_USER = os.getenv('USER')
DB_PASSWORD = os.getenv('PASSWORD')
DB_PORT = os.getenv('PORT', '19034')
DB_NAME = os.getenv('DB', 'defaultdb')
CA_CERT = os.getenv('CA_CERT')

# Global engine variable
engine: Optional[Engine] = None

# Initialize database connection
if not all([DB_HOST, DB_USER, DB_PASSWORD]):
    print("⚠️ Missing required database credentials in .env file")
else:
    try:
        engine = create_database_engine(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            ca_cert=CA_CERT
        )
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        engine = None

# Province name mapping (database -> display)
PROVINCE_NAMES = {
    'DakLak': 'Dak Lak',
    'GiaLai': 'Gia Lai',
    'DakNong': 'Dak Nong',
    'KonTum': 'Kon Tum',
    'LamDong': 'Lam Dong'
}

# ============================================================================
# ERROR HANDLERS & HELPER FUNCTIONS
# ============================================================================

def check_database_connection() -> Tuple[bool, str]:
    """Check if database is connected and available"""
    return check_connection(engine)

def safe_db_operation(operation_func):
    """Decorator to safely execute database operations with error handling"""
    def wrapper(*args, **kwargs):
        try:
            # Check database connection first
            is_connected, message = check_database_connection()
            if not is_connected:
                return jsonify({
                    'error': 'Database connection unavailable',
                    'details': message,
                    'success': False
                }), 503
            
            # Execute the operation
            return operation_func(*args, **kwargs)
        except OperationalError as e:
            print(f"❌ Database operational error in {operation_func.__name__}: {e}")
            return jsonify({
                'error': 'Database operational error',
                'details': str(e),
                'success': False
            }), 503
        except SQLAlchemyError as e:
            print(f"❌ SQLAlchemy error in {operation_func.__name__}: {e}")
            return jsonify({
                'error': 'Database query error',
                'details': str(e),
                'success': False
            }), 500
        except Exception as e:
            print(f"❌ Unexpected error in {operation_func.__name__}: {e}")
            traceback.print_exc()
            return jsonify({
                'error': 'Internal server error',
                'details': str(e),
                'success': False
            }), 500
    wrapper.__name__ = operation_func.__name__
    return wrapper

# Global error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist',
        'success': False
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'success': False
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"❌ Unhandled exception: {e}")
    traceback.print_exc()
    return jsonify({
        'error': 'Unexpected error',
        'message': str(e),
        'success': False
    }), 500

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main dashboard page"""
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/news')
def news():
    """Redirect to news section on main page"""
    from flask import redirect, url_for
    return redirect('/#news', code=302)

@app.route('/debug-daily-prices')
def debug_daily_prices():
    """Debug page for daily prices chart"""
    response = make_response(render_template('debug_daily_prices.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint - always returns even if DB is down"""
    db_status = "unknown"
    db_message = "Not checked"
    
    if engine is None:
        db_status = "disconnected"
        db_message = "Database engine not initialized"
    else:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            db_status = "connected"
            db_message = "Database operational"
        except Exception as e:
            db_status = "error"
            db_message = str(e)[:100]
    
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'api': 'running',
        'database': db_status,
        'message': db_message,
        'timestamp': datetime.now().isoformat()
    }), 200 if db_status == 'connected' else 503


@app.route('/api/weather/province/<province>', methods=['GET'])
@cache.cached(timeout=600, query_string=True)  # Cache for 10 minutes
@safe_db_operation
def get_weather_by_province(province):
    """
    Get weather data for a specific province
    Query params:
    - year: Filter by specific year (optional)
    - aggregate: 'yearly' or 'monthly' (default: monthly)
    """
    
    # Validate province
    if province not in PROVINCE_NAMES:
        return jsonify({'error': 'Invalid province'}), 400
    
    year = request.args.get('year', type=int)
    aggregate = request.args.get('aggregate', 'monthly')
    limit = request.args.get('limit', type=int)  # New: limit for recent months
    
    try:
        if aggregate == 'recent12':
            # Get last 12 months
            query = text("""
            SELECT year, month, 
                   temperature_mean, 
                   precipitation_sum, 
                   humidity_mean
            FROM weather_data_monthly
            WHERE province = :province
            ORDER BY year DESC, month DESC
            LIMIT 12
            """)
            with engine.connect() as conn:
                df = pd.read_sql(query, conn, params={'province': province})
            # Reverse to get chronological order
            df = df.iloc[::-1].reset_index(drop=True)
            
        elif aggregate == 'yearly' and year:
            # Get monthly data for specific year
            query = text("""
            SELECT year, month, 
                   temperature_mean, 
                   precipitation_sum, 
                   humidity_mean
            FROM weather_data_monthly
            WHERE province = :province AND year = :year
            ORDER BY month
            """)
            with engine.connect() as conn:
                df = pd.read_sql(query, conn, params={'province': province, 'year': year})
            
        elif aggregate == 'yearly':
            # Get yearly averages/sums
            query = text("""
            SELECT year,
                   AVG(temperature_mean) as temperature_mean,
                   SUM(precipitation_sum) as precipitation_sum,
                   AVG(humidity_mean) as humidity_mean
            FROM weather_data_monthly
            WHERE province = :province
            GROUP BY year
            ORDER BY year
            """)
            with engine.connect() as conn:
                df = pd.read_sql(query, conn, params={'province': province})
            
        else:
            # Get all monthly data (default)
            query = text("""
            SELECT year, month,
                   temperature_mean,
                   precipitation_sum,
                   humidity_mean
            FROM weather_data_monthly
            WHERE province = :province
            ORDER BY year, month
            """)
            with engine.connect() as conn:
                df = pd.read_sql(query, conn, params={'province': province})
        
        # Calculate statistics
        stats = {
            'temperature': {
                'current': float(df['temperature_mean'].iloc[-1]) if len(df) > 0 else None,
                'avg': float(df['temperature_mean'].mean()),
                'min': float(df['temperature_mean'].min()),
                'max': float(df['temperature_mean'].max()),
                'change_pct': float(
                    ((df['temperature_mean'].iloc[-1] - df['temperature_mean'].mean()) / 
                     df['temperature_mean'].mean() * 100)
                ) if len(df) > 0 else 0
            },
            'precipitation': {
                'current': float(df['precipitation_sum'].iloc[-1]) if len(df) > 0 else None,
                'avg': float(df['precipitation_sum'].mean()),
                'min': float(df['precipitation_sum'].min()),
                'max': float(df['precipitation_sum'].max()),
                'change_pct': float(
                    ((df['precipitation_sum'].iloc[-1] - df['precipitation_sum'].mean()) / 
                     df['precipitation_sum'].mean() * 100)
                ) if len(df) > 0 else 0
            },
            'humidity': {
                'current': float(df['humidity_mean'].iloc[-1]) if len(df) > 0 else None,
                'avg': float(df['humidity_mean'].mean()),
                'min': float(df['humidity_mean'].min()),
                'max': float(df['humidity_mean'].max()),
                'change_pct': float(
                    ((df['humidity_mean'].iloc[-1] - df['humidity_mean'].mean()) / 
                     df['humidity_mean'].mean() * 100)
                ) if len(df) > 0 else 0
            }
        }
        
        # Convert DataFrame to records
        data = df.to_dict('records')
        
        return jsonify({
            'province': province,
            'province_display': PROVINCE_NAMES[province],
            'data': data,
            'stats': stats,
            'count': len(data),
            'updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather/provinces', methods=['GET'])
def get_all_provinces():
    """Get list of available provinces"""
    return jsonify({
        'provinces': [
            {'value': k, 'label': v} for k, v in PROVINCE_NAMES.items()
        ]
    })


@app.route('/api/weather/summary', methods=['GET'])
def get_weather_summary():
    """Get weather summary for all provinces"""
    try:
        query = """
        SELECT province,
               AVG(temperature_mean) as avg_temp,
               AVG(precipitation_sum) as avg_precip,
               AVG(humidity_mean) as avg_humidity,
               COUNT(*) as record_count
        FROM weather_data_monthly
        GROUP BY province
        """
        df = pd.read_sql(query, engine)
        
        summary = []
        for _, row in df.iterrows():
            summary.append({
                'province': row['province'],
                'province_display': PROVINCE_NAMES.get(row['province'], row['province']),
                'avg_temperature': float(row['avg_temp']),
                'avg_precipitation': float(row['avg_precip']),
                'avg_humidity': float(row['avg_humidity']),
                'record_count': int(row['record_count'])
            })
        
        return jsonify({
            'summary': summary,
            'updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/exports/top-countries', methods=['GET'])
@cache.cached(timeout=600, query_string=True)  # Cache for 10 minutes
@safe_db_operation
def get_top_export_countries():
    """
    Get top 9 importing countries by year
    Query params:
    - year: Filter by specific year (default: latest year)
    Uses time series forecasting for years beyond available data
    """
    year = request.args.get('year', type=int)
    is_forecast = False
    
    try:
        # Get the latest available year from database
        query = text("SELECT MAX(year) as max_year FROM export_country")
        with engine.connect() as conn:
            result = conn.execute(query).fetchone()
            max_available_year = result[0] if result[0] else 2023
        
        # If no year specified, use latest available
        if not year:
            year = max_available_year
        
        # Check if we need to forecast (year > max_available_year)
        if year > max_available_year:
            is_forecast = True
            # Use time series forecasting for future years
            df = forecast_export_data(year, max_available_year)
        else:
            # Get historical data
            query = text("""
                SELECT partner as country, 
                       quantity as export_volume, 
                       trade_value_1000usd as export_value
                FROM export_country
                WHERE year = :year
                ORDER BY quantity DESC
            """)
            
            with engine.connect() as conn:
                df = pd.read_sql(query, conn, params={'year': year})
            
            # Filter out 'World' (aggregate row)
            df = df[df['country'] != 'World'].copy()
        
        if len(df) == 0:
            return jsonify({
                'year': year,
                'countries': [],
                'others': {'percentage': 0, 'volume': 0},
                'total': 0,
                'is_forecast': is_forecast,
                'message': 'No data found for this year'
            })
        
        # Calculate total volume
        total_volume = df['export_volume'].sum()
        
        # Get top 9 (changed from top 5)
        top9 = df.head(9).copy()
        top9['percentage'] = (top9['export_volume'] / total_volume * 100).round(1)
        
        # Calculate others
        others_volume = df.iloc[9:]['export_volume'].sum() if len(df) > 9 else 0
        others_percentage = (others_volume / total_volume * 100).round(1) if total_volume > 0 else 0
        
        # Format response (keep original unit from database: tons)
        countries = []
        for _, row in top9.iterrows():
            countries.append({
                'name': row['country'],
                'volume': float(row['export_volume']),  # Already in tons from database
                'value': float(row['export_value']) if pd.notna(row['export_value']) else 0,
                'percentage': float(row['percentage'])
            })
        
        return jsonify({
            'year': year,
            'countries': countries,
            'others': {
                'percentage': float(others_percentage),
                'volume': float(others_volume)  # Already in tons from database
            },
            'total': float(total_volume),  # Already in tons from database
            'is_forecast': is_forecast,
            'forecast_method': 'exponential_smoothing' if is_forecast else 'actual_data',
            'updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def forecast_export_data(target_year, max_available_year):
    """
    Forecast export data for future years using time series methods
    Uses exponential smoothing for trend extrapolation
    """
    try:
        # Get ALL historical data for better time series analysis
        query = text("""
            SELECT year, partner as country, 
                   quantity as export_volume, 
                   trade_value_1000usd as export_value
            FROM export_country
            WHERE partner != 'World'
            ORDER BY year, quantity DESC
        """)
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        # Calculate how many years to forecast
        years_ahead = target_year - max_available_year
        
        # Get unique countries from most recent year
        latest_countries = df[df['year'] == max_available_year]['country'].unique()
        
        country_forecasts = []
        
        for country in latest_countries:
            country_data = df[df['country'] == country].copy()
            country_data = country_data.sort_values('year')
            
            if len(country_data) >= 3:  # Need at least 3 points for time series
                # Create time series
                ts_data = country_data.set_index('year')['export_volume']
                
                # Fill missing years with professional interpolation
                all_years = range(ts_data.index.min(), max_available_year + 1)
                ts_data = ts_data.reindex(all_years)
                
                # Use polynomial interpolation for better trend capture
                ts_data = ts_data.interpolate(method='polynomial', order=2, limit_direction='both')
                
                # Handle any remaining NaN at edges with backward fill
                ts_data = ts_data.bfill()
                
                # Apply exponential smoothing (alpha=0.3 for moderate smoothing)
                forecasted_volume = exponential_smoothing_forecast(
                    ts_data.values, 
                    years_ahead, 
                    alpha=0.3
                )
                
                # Ensure non-negative
                forecasted_volume = max(0, forecasted_volume)
                
                # Forecast value based on price trend
                latest_value = country_data['export_value'].iloc[-1]
                if pd.notna(latest_value) and ts_data.iloc[-1] > 0:
                    # Calculate price per kg from recent data
                    recent_data = country_data.tail(3)  # Last 3 years
                    prices = recent_data['export_value'] / recent_data['export_volume']
                    avg_price = prices.mean()
                    
                    # Forecast value with trend adjustment
                    forecasted_value = forecasted_volume * avg_price
                else:
                    forecasted_value = 0
                
                country_forecasts.append({
                    'country': country,
                    'export_volume': forecasted_volume,
                    'export_value': forecasted_value
                })
        
        # Create DataFrame from forecasts
        forecast_df = pd.DataFrame(country_forecasts)
        forecast_df = forecast_df.sort_values('export_volume', ascending=False)
        
        return forecast_df
        
    except Exception as e:
        print(f"Forecast error: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['country', 'export_volume', 'export_value'])


def exponential_smoothing_forecast(series, steps, alpha=0.3):
    """
    Exponential smoothing with Holt's linear trend method
    series: array of historical values
    steps: number of periods to forecast
    alpha: smoothing parameter (0-1)
    """
    if len(series) < 2:
        return series[-1] if len(series) > 0 else 0
    
    # Initialize level and trend
    level = series[0]
    trend = (series[-1] - series[0]) / (len(series) - 1)
    
    beta = 0.1  # Trend smoothing parameter
    
    # Apply exponential smoothing to historical data
    for value in series[1:]:
        last_level = level
        level = alpha * value + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
    
    # Forecast future values
    forecast = level + steps * trend
    
    return forecast


@app.route('/api/exports/years', methods=['GET'])
def get_available_years():
    """Get list of available years in export data"""
    try:
        query = text("""
            SELECT DISTINCT year 
            FROM export_country 
            ORDER BY year DESC
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            years = [row[0] for row in result]
        
        return jsonify({
            'years': years,
            'count': len(years)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/production', methods=['GET'])
# @cache.cached(timeout=300)  # Cache disabled for testing
@safe_db_operation
def get_production_data():
    """
    Get production data with missing data handling via interpolation
    Returns: year, area_thousand_ha, output_tons, export_tons
    """
    try:
        # Fetch all production data
        query = text("""
        SELECT year, area_thousand_ha, output_tons, export_tons
        FROM production
        ORDER BY year ASC
        """)
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        
        # Professional missing data handling with polynomial interpolation
        numeric_cols = ['area_thousand_ha', 'output_tons', 'export_tons']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # Apply interpolation using utility function
        for col in numeric_cols:
            df[col] = interpolate_time_series(df, col, method='polynomial', order=2)
        
        # Convert to tons for display (output and export) - ROUND TO 2 DECIMALS
        df['output_million_tons'] = (df['output_tons'] / 1000000).round(2)
        df['export_million_tons'] = (df['export_tons'] / 1000000).round(2)

        # Calculate yield (tons per hectare) - ROUND TO 2 DECIMALS
        # Handle division by zero and NaN values safely
        df['yield_tons_per_ha'] = df.apply(
            lambda row: round(row['output_tons'] / (row['area_thousand_ha'] * 1000), 2) 
            if pd.notna(row['output_tons']) and pd.notna(row['area_thousand_ha']) 
            and row['area_thousand_ha'] > 0 and row['output_tons'] > 0 
            else None, 
            axis=1
        )
        # Replace None with NaN for consistency
        df['yield_tons_per_ha'] = df['yield_tons_per_ha'].replace([None], pd.NA)

        # Also round area and output for frontend display
        df['output_tons'] = df['output_tons'].round(2)
        df['area_thousand_ha'] = df['area_thousand_ha'].round(2)
        
        # Ensure no NaN values in critical columns by filling with interpolated values if needed
        if df['yield_tons_per_ha'].isna().any():
            # Try to interpolate yield if there are missing values
            df['yield_tons_per_ha'] = interpolate_time_series(df, 'yield_tons_per_ha', method='polynomial', order=2)

        # Convert to list of dicts and replace NaN/None with None for JSON serialization
        data = df.to_dict('records')
        # Replace NaN values with None for proper JSON serialization
        for record in data:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'years': df['year'].tolist(),
            'metadata': {
                'columns': {
                    'year': 'Year',
                    'area_thousand_ha': 'Cultivated Area (thousand hectares)',
                    'output_tons': 'Production (tons)',
                    'export_tons': 'Export (tons)',
                    'output_million_tons': 'Production (million tons)',
                    'export_million_tons': 'Export (million tons)',
                    'yield_tons_per_ha': 'Yield (tons/ha)'
                },
                'interpolated': True,
                'method': 'linear'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/production/province/<province>', methods=['GET'])
def get_production_by_province(province):
    """
    Get production data for a specific province with missing data handling via interpolation
    Based on scatterplot_production.ipynb method
    Returns: year, area_thousand_ha, output_tons, export_tons, yield_tons_per_ha
    """
    
    # Validate province
    if province not in PROVINCE_NAMES:
        return jsonify({'error': 'Invalid province'}), 400
    
    try:
        # Fetch provincial production data
        query = text("""
        SELECT year, area_thousand_ha, output_tons, export_tons
        FROM production_by_province
        WHERE province = :province
        ORDER BY year ASC
        """)
        
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={'province': province})
        
        if df.empty:
            return jsonify({'error': 'No data found for this province'}), 404
        
        # Handle missing data using interpolation
        numeric_cols = ['area_thousand_ha', 'output_tons', 'export_tons']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        # Use utility function for interpolation
        for col in numeric_cols:
            df[col] = interpolate_time_series(df, col, method='linear')
        
        # Convert to display units
        df['output_million_tons'] = (df['output_tons'] / 1000000).round(2)
        df['export_million_tons'] = (df['export_tons'] / 1000000).round(2)
        
        # Calculate yield (tons per hectare)
        df['yield_tons_per_ha'] = (df['output_tons'] / (df['area_thousand_ha'] * 1000)).round(2)
        
        # Convert to list of dicts
        data = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'province': province,
            'province_display': PROVINCE_NAMES[province],
            'data': data,
            'count': len(data),
            'years': df['year'].tolist(),
            'metadata': {
                'interpolated': True,
                'method': 'linear',
                'columns': {
                    'year': 'Year',
                    'area_thousand_ha': 'Cultivated Area (thousand hectares)',
                    'output_tons': 'Production (tons)',
                    'export_tons': 'Export (tons)',
                    'output_million_tons': 'Production (million tons)',
                    'export_million_tons': 'Export (million tons)',
                    'yield_tons_per_ha': 'Yield (tons/ha)'
                }
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/export', methods=['GET'])
@cache.cached(timeout=300)  # Cache for 5 minutes
@safe_db_operation
def get_export_data():
    """
    Get coffee export data with time series interpolation for missing values
    Returns: export value, world price, VN price
    """
    try:
        # First get only actual data (non-null values) to find latest year with real data
        query_actual = text("""
            SELECT 
                year,
                export_value_million_usd,
                price_world_usd_per_ton,
                price_vn_usd_per_ton
            FROM coffee_export
            WHERE export_value_million_usd IS NOT NULL 
               OR price_world_usd_per_ton IS NOT NULL 
               OR price_vn_usd_per_ton IS NOT NULL
            ORDER BY year DESC
            LIMIT 1
        """)
        
        with engine.connect() as conn:
            latest_actual = conn.execute(query_actual).fetchone()
        
        # Now get all data for time series
        query = text("""
            SELECT 
                year,
                export_value_million_usd,
                price_world_usd_per_ton,
                price_vn_usd_per_ton
            FROM coffee_export
            ORDER BY year
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            data = result.fetchall()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No export data found'
            }), 404
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data, columns=['year', 'export_value_million_usd', 
                                         'price_world_usd_per_ton', 'price_vn_usd_per_ton'])
        
        # Convert numeric columns to proper numeric types
        numeric_columns = ['export_value_million_usd', 'price_world_usd_per_ton', 'price_vn_usd_per_ton']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Professional missing data handling
        has_missing = df[numeric_columns].isnull().any().any()
        
        if has_missing:
            for col in numeric_columns:
                df[col] = interpolate_time_series(df, col, method='polynomial', order=2)
        
        # Convert to dict for JSON response using utility function
        export_data = format_dataframe_rows(df, numeric_columns)
        
        return jsonify({
            'success': True,
            'count': len(export_data),
            'data': export_data,
            'metadata': {
                'interpolated': bool(has_missing),
                'method': 'linear + backward fill for leading NaNs' if has_missing else 'none',
                'latest_actual_year': int(latest_actual[0]) if latest_actual else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export-performance', methods=['GET'])
@cache.cached(timeout=300)  # Cache for 5 minutes
@safe_db_operation
def get_export_performance():
    """
    Get comprehensive export performance data from export_performance table
    Returns: year, area, production, export volume, export value, world price, VN price
    """
    try:
        query = text("""
            SELECT 
                year,
                area_thousand_ha,
                production_tons,
                export_tons,
                export_value_million_usd,
                price_world_usd_per_ton,
                price_vn_usd_per_ton
            FROM export_performance
            WHERE year >= 2005 AND year <= 2024
            ORDER BY year
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            data = result.fetchall()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No export performance data found'
            }), 404
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data, columns=[
            'year', 'area_thousand_ha', 'production_tons', 'export_tons',
            'export_value_million_usd', 'price_world_usd_per_ton', 'price_vn_usd_per_ton'
        ])
        
        # Convert numeric columns to proper numeric types
        numeric_columns = ['area_thousand_ha', 'production_tons', 'export_tons',
                          'export_value_million_usd', 'price_world_usd_per_ton', 
                          'price_vn_usd_per_ton']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Professional missing data handling using utility function
        df_interpolated = df.copy()
        for col in numeric_columns:
            df_interpolated[col] = interpolate_time_series(df_interpolated, col, method='polynomial', order=2)
        
        # Calculate statistics using utility function
        latest_data = df_interpolated.iloc[-1]
        
        stats = {
            'area': calculate_growth_stats(df_interpolated['area_thousand_ha'], latest_data['area_thousand_ha']),
            'production': {
                **calculate_growth_stats(df_interpolated['production_tons'], latest_data['production_tons']),
                'total': float(df_interpolated['production_tons'].sum())
            },
            'export_volume': {
                **calculate_growth_stats(df_interpolated['export_tons'], latest_data['export_tons']),
                'total': float(df_interpolated['export_tons'].sum())
            },
            'export_value': {
                **calculate_growth_stats(df_interpolated['export_value_million_usd'], latest_data['export_value_million_usd']),
                'total': float(df_interpolated['export_value_million_usd'].sum())
            },
            'world_price': calculate_growth_stats(df_interpolated['price_world_usd_per_ton'], latest_data['price_world_usd_per_ton']),
            'vn_price': calculate_growth_stats(df_interpolated['price_vn_usd_per_ton'], latest_data['price_vn_usd_per_ton'])
        }
        
        # Format data for response using utility function
        formatted_data = format_dataframe_rows(df_interpolated, numeric_columns)
        
        return jsonify({
            'success': True,
            'data': formatted_data,
            'stats': stats,
            'metadata': {
                'years': len(formatted_data),
                'source': 'export_performance table',
                'period': f"{df['year'].min():.0f}-{df['year'].max():.0f}"
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error in get_export_performance: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# DAILY COFFEE PRICES API
# ============================================================================

@app.route('/api/daily-coffee-prices', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_daily_coffee_prices():
    """Get daily coffee prices for the last 7 days by region"""
    try:
        days = request.args.get('days', 7, type=int)
        
        # Validate days parameter
        if days < 1 or days > 365:
            days = 7
        
        # Query to get last N days of data (using CURRENT_DATE instead of MAX to avoid future dates)
        query = f"""
        SELECT 
            date,
            region,
            price_vnd_per_kg
        FROM daily_coffee_prices
        WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL {days} DAY)
          AND date <= CURRENT_DATE
        ORDER BY date ASC, region ASC
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return jsonify({
                'success': False,
                'error': 'No data available'
            }), 404
        
        # Convert date to string for JSON serialization
        df['date'] = df['date'].astype(str)
        
        # Prepare data for Chart.js
        dates = sorted(df['date'].unique().tolist())
        regions = sorted(df['region'].unique().tolist())
        
        # Create datasets for each region
        datasets = []
        region_colors = {
            'DakLak': {'border': '#E29A2E', 'bg': 'rgba(226, 154, 46, 0.1)'},
            'DakNong': {'border': '#35B390', 'bg': 'rgba(53, 179, 144, 0.1)'},
            'GiaLai': {'border': '#B25127', 'bg': 'rgba(178, 81, 39, 0.1)'},
            'LamDong': {'border': '#8B4513', 'bg': 'rgba(139, 69, 19, 0.1)'}
        }
        
        for region in regions:
            region_data = df[df['region'] == region].sort_values('date')
            prices = region_data['price_vnd_per_kg'].tolist()
            
            color = region_colors.get(region, {'border': '#666', 'bg': 'rgba(102, 102, 102, 0.1)'})
            
            datasets.append({
                'label': region,
                'data': prices,
                'borderColor': color['border'],
                'backgroundColor': color['bg'],
                'borderWidth': 2.5,
                'tension': 0.5,  # Increased for smoother curves
                'fill': True,
                'pointRadius': 3,
                'pointHoverRadius': 6,
                'pointBackgroundColor': color['border'],
                'pointBorderColor': '#fff',
                'pointBorderWidth': 2
            })
        
        # Calculate statistics
        latest_date = df['date'].max()
        latest_prices = df[df['date'] == latest_date].set_index('region')['price_vnd_per_kg'].to_dict()
        
        # Calculate price changes
        if len(dates) >= 2:
            previous_date = dates[-2]
            previous_prices = df[df['date'] == previous_date].set_index('region')['price_vnd_per_kg'].to_dict()
            price_changes = {}
            for region in regions:
                if region in latest_prices and region in previous_prices:
                    change = latest_prices[region] - previous_prices[region]
                    percent_change = (change / previous_prices[region] * 100) if previous_prices[region] > 0 else 0
                    price_changes[region] = {
                        'change': int(change),
                        'percent': round(percent_change, 2)
                    }
        else:
            price_changes = {}
        
        return jsonify({
            'success': True,
            'data': {
                'labels': dates,
                'datasets': datasets,
                'latest_prices': latest_prices,
                'price_changes': price_changes,
                'date_range': {
                    'start': dates[0] if dates else None,
                    'end': dates[-1] if dates else None
                },
                'total_records': len(df)
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error in get_daily_coffee_prices: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n🚀 Vietnam Coffee Data Portal")
    print(f"📍 Web Interface: http://localhost:5000")
    print(f"📍 API Endpoint:  http://localhost:5000/api/")
    print(f"✨ Press CTRL+C to stop\n")
    
    try:
        app.run(
            debug=False, 
            host='0.0.0.0', 
            port=5000,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        traceback.print_exc()

