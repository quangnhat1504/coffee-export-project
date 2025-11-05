# ✅ Final Project Structure - Vietnam Coffee Data Portal

## 📂 Cấu Trúc Cuối Cùng

```
coffee-export-project/
├── .env                      # Database credentials (GIT IGNORED)
├── .env.example             # Template for credentials
├── .gitignore              # Git ignore rules
├── package.json            # NPM scripts and dependencies
├── requirements.txt        # Python dependencies
├── README.md              # Full documentation
├── QUICK_START.md         # Quick start guide
│
├── collect_data/          # Data collection scripts
│   ├── sync_coffee.py
│   ├── sync_weather.py
│   └── *.csv
│
├── visualize/             # Jupyter notebooks
│   └── *.ipynb
│
└── web/                   # Main web application
    ├── backend/           # Flask API
    │   └── api.py
    ├── scripts/           # Utility scripts
    │   ├── create_production_by_province.py
    │   └── update_news.py
    ├── static/            # Static files
    │   ├── css/
    │   │   ├── styles.css
    │   │   └── contact-modern.css
    │   └── js/
    │       └── script.js
    └── templates/         # HTML templates
        ├── index.html
        └── news_content.html
```

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/ttung05/coffee-export-project.git
cd coffee-export-project

# 2. Install dependencies
npm install

# 3. Configure database (if needed)
# Edit .env file with your credentials

# 4. Run development server
npm run dev
```

## 📝 Thay Đổi Chính

### Đổi tên folder
- ✅ `wed/` → `web/` (tên chuẩn hơn)

### Files đã xóa
- ❌ `styles_temp.css` - File backup không dùng
- ❌ Các file test cũ
- ❌ PowerShell scripts cũ (thay bằng npm scripts)

### Cấu trúc mới
- ✅ `web/backend/` - Backend API
- ✅ `web/scripts/` - Utility scripts
- ✅ `web/static/` - CSS + JS
- ✅ `web/templates/` - HTML files

## 🔑 NPM Scripts

```bash
npm install      # Install all dependencies (Python + Node.js)
npm run dev      # Start development server
npm run api      # Start API only
npm run check    # Check API health
```

## 🌐 Endpoints

- **Website:** http://localhost:5000 (or open `web/templates/index.html`)
- **API:** http://localhost:5000/api/*
- **Health Check:** http://localhost:5000/api/health

## 📊 Database

- **Provider:** Aiven MySQL
- **Tables:** coffee_export, production, export_country, weather_data_monthly
- **Config:** Stored in `.env` file

## 🔒 Security

- ✅ `.env` file is git-ignored
- ✅ Database credentials are NOT in code
- ✅ Use `.env.example` as template

## 📚 Documentation

- `README.md` - Full project documentation
- `QUICK_START.md` - Quick start guide
- `PROJECT_STRUCTURE.md` - Detailed structure explanation

---

**Last Updated:** November 5, 2025  
**Status:** ✅ Production Ready
