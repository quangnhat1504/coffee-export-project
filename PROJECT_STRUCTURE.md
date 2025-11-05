# Vietnam Coffee Data Portal - Project Structure

## 📁 Cấu Trúc Thư Mục

```
coffee-export-project/
├── .env                    # Database credentials (KHÔNG commit!)
├── .env.example           # Template cho .env
├── .gitignore            # Git ignore rules
├── package.json          # Node.js dependencies & scripts
├── requirements.txt      # Python dependencies
├── README.md            # Tài liệu chi tiết
├── QUICK_START.md       # Hướng dẫn nhanh
│
├── collect_data/        # Data collection scripts
│   ├── sync_coffee.py   # Sync coffee data
│   ├── sync_weather.py  # Sync weather data
│   └── *.csv            # CSV data files
│
├── visualize/           # Data visualization notebooks
│   └── *.ipynb          # Jupyter notebooks
│
└── wed/                 # Main web application
    ├── api.py           # Flask API backend
    ├── index.html       # Main HTML page
    ├── script.js        # JavaScript logic
    ├── styles.css       # CSS styles
    └── *.py             # Other Python scripts
```

## 🔑 Files Quan Trọng

### `.env` - Database Configuration
```env
HOST="your-database-host.aivencloud.com"
USER="your-username"
PASSWORD="your-password"
PORT=19034
DB="defaultdb"
CA_CERT="..." # Optional SSL certificate
```

**⚠️ QUAN TRỌNG:** 
- File này chứa thông tin nhạy cảm
- ĐÃ được thêm vào `.gitignore`
- KHÔNG bao giờ commit lên Git!

### `package.json` - NPM Scripts
```json
{
  "scripts": {
    "install": "pip install -r requirements.txt",
    "dev": "npm run api",
    "api": "cd wed && python api.py",
    "check": "curl http://localhost:5000/api/health"
  }
}
```

### `requirements.txt` - Python Dependencies
```
flask>=2.3.0
flask-cors>=4.0.0
pandas>=2.0.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
python-dotenv>=1.0.0
```

## 🚀 Quick Commands

```bash
# Cài đặt tất cả dependencies
npm install

# Chạy development server
npm run dev

# Kiểm tra API status
npm run check
```

## 📊 Database Tables

- `coffee_export` - Export value, prices (2005-2024)
- `production` - Production data by year
- `export_country` - Export data by country
- `weather_data_monthly` - Weather data by province

## 🌐 API Endpoints

- `GET /api/health` - Health check
- `GET /api/export` - Coffee export data
- `GET /api/production` - Production data
- `GET /api/exports/top-countries?year=YYYY` - Top export countries
- `GET /api/weather/province/{province}?aggregate=recent12` - Weather data

## 🔒 Bảo Mật

1. ✅ `.env` đã được thêm vào `.gitignore`
2. ✅ Database credentials được lưu trong `.env`
3. ✅ `.env.example` cung cấp template không có credentials
4. ⚠️ Không bao giờ hardcode credentials trong code

## 📝 Notes

- Sử dụng `npm run dev` để chạy cả API và web server
- API chạy trên port 5000
- Website có thể mở trực tiếp file `wed/index.html` hoặc qua API server
- Database connection tự động load từ `.env`
