# ☕ Vietnam Coffee Export Data Analysis Project

## 📊 Tổng Quan / Overview

Dự án này cung cấp một hệ thống phân tích dữ liệu toàn diện cho ngành xuất khẩu cà phê Việt Nam, bao gồm thu thập dữ liệu tự động, xử lý ETL, quản lý cơ sở dữ liệu, trực quan hóa và dashboard web hiện đại.

This project provides a comprehensive data analysis system for Vietnam's coffee export industry, including automated data collection, ETL processing, database management, visualization, and a modern web dashboard.

---

## 🌟 Tính Năng Chính / Key Features

- ☁️ **Thu thập dữ liệu tự động** - Automated data collection from multiple sources
- 🔄 **Pipeline ETL hoàn chỉnh** - Complete ETL pipeline for data processing
- 💾 **Quản lý cơ sở dữ liệu MySQL** - MySQL database management with normalized schema
- 📈 **Trực quan hóa dữ liệu** - Interactive charts and time series analysis
- 🌐 **Dashboard web hiện đại** - Modern, responsive web interface
- 🔌 **Tích hợp API World Bank WITS** - World Bank WITS API integration

---

## 📁 Cấu Trúc Dự Án / Project Structure

```
coffee-export-project/
│
├── 📂 collect_data/                    # Thu thập & Xử lý dữ liệu / Data Collection
│   ├── 📄 Data_coffee.csv              # Dữ liệu cà phê chính / Main coffee data
│   ├── 📄 Thi_phan_3_thi_truong_chinh.csv  # Dữ liệu thị phần / Market share data
│   ├── 🐍 sync_coffee.py               # Script đồng bộ database / DB sync script
│   ├── 📓 main_coffee.ipynb            # Notebook xử lý dữ liệu / Data processing
│   ├── 📓 export_api.ipynb             # Tích hợp WITS API / WITS API integration
│   └── 📓 beautiful_soup_4_demo.ipynb  # Demo web scraping
│
├── 📂 visualize/                       # Trực quan hóa / Visualization
│   ├── 📓 Time_Series.ipynb            # Phân tích chuỗi thời gian / Time series
│   ├── 📓 pair_plot.ipynb              # Phân tích tương quan / Correlation
│   ├── 📓 scatterplot_production.ipynb # Biểu đồ sản xuất / Production charts
│   └── 📓 nhat.ipynb                   # Phân tích bổ sung / Additional analysis
│
├── 📂 web/                             # Dashboard Web
│   ├── 🌐 index.html                   # Trang dashboard chính / Main dashboard
│   ├── ⚙️ script.js                    # Chức năng tương tác / Interactive features
│   └── 🎨 styles.css                   # Giao diện / Styling
│
├── 📄 requirements.txt                 # Dependencies Python
└── 📖 README.md                        # File này / This file
```

---

## 🛠️ Công Nghệ Sử Dụng / Technology Stack

### Backend & Xử lý dữ liệu / Backend & Data Processing
- **Python 3.x** - Ngôn ngữ lập trình chính / Main programming language
- **Pandas** - Xử lý và phân tích dữ liệu / Data manipulation and analysis
- **SQLAlchemy** - ORM cho database / Database ORM
- **PyMySQL** - MySQL connector
- **BeautifulSoup4** - Web scraping
- **Selenium** - Dynamic web scraping
- **Requests** - HTTP library

### Trực quan hóa / Visualization
- **Matplotlib** - Biểu đồ tĩnh / Static charts
- **Seaborn** - Biểu đồ thống kê / Statistical visualizations
- **Plotly** - Biểu đồ tương tác / Interactive charts

### Frontend
- **HTML5/CSS3** - Cấu trúc và giao diện / Structure and styling
- **JavaScript (ES6+)** - Tương tác động / Dynamic interactions
- **Chart.js** - Biểu đồ dữ liệu / Data visualization
- **D3.js** - Trực quan hóa nâng cao / Advanced visualizations

### Database
- **MySQL 5.7+** - Quản lý cơ sở dữ liệu quan hệ / Relational database management

---

## 📋 Yêu Cầu Hệ Thống / Prerequisites

- ✅ Python 3.7 trở lên / Python 3.7 or higher
- ✅ MySQL Server 5.7 trở lên / MySQL Server 5.7 or higher
- ✅ pip (Python package manager)
- ✅ Trình duyệt hiện đại / Modern web browser (Chrome, Firefox, Edge)
- ✅ Jupyter Notebook (tùy chọn / optional)

---

## 🚀 Cài Đặt / Installation

### 1️⃣ Clone Repository
```bash
git clone <repository-url>
cd coffee-export-project
```

### 2️⃣ Cài đặt Python Dependencies / Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Hoặc cài đặt từng package / Or install individually:**
```bash
pip install pandas>=1.5.0 pymysql>=1.0.0 sqlalchemy>=2.0.0
pip install beautifulsoup4>=4.11.0 selenium>=4.0.0 requests>=2.28.0
pip install matplotlib>=3.5.0 seaborn>=0.12.0 plotly>=5.0.0
pip install jupyter>=1.0.0 ipykernel>=6.0.0 notebook>=6.4.0
```

### 3️⃣ Cấu hình Database / Database Configuration

**Tạo database MySQL / Create MySQL database:**
```sql
CREATE DATABASE coffee_export_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Cấu hình kết nối trong `sync_coffee.py` / Configure connection:**
```python
# Cập nhật thông tin kết nối / Update connection info
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "your_username"
DB_PASSWORD = "your_password"
DB_NAME = "coffee_export_db"
```

---

## 💾 Cấu Trúc Database / Database Schema

### 📊 Bảng `coffee_long` (Dữ liệu thô dạng long format / Raw data in long format)
```sql
CREATE TABLE coffee_long (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  hang_muc VARCHAR(255) NOT NULL,
  year INT NOT NULL,
  value DECIMAL(16,2),
  UNIQUE KEY uq_coffee_long (hang_muc, year)
) CHARACTER SET utf8mb4;
```

### 🌡️ Bảng `weather` (Dữ liệu khí hậu / Climate data)
```sql
CREATE TABLE weather (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  temperature DECIMAL(5,2),      -- Nhiệt độ trung bình (°C) / Avg temperature
  humidity DECIMAL(5,2),          -- Độ ẩm trung bình (%) / Avg humidity
  rainfall DECIMAL(10,2),         -- Lượng mưa (mm) / Rainfall
  UNIQUE KEY uq_weather_year (year)
) CHARACTER SET utf8mb4;
```

### 🌱 Bảng `production` (Sản xuất / Production)
```sql
CREATE TABLE production (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  area_thousand_ha DECIMAL(10,1),    -- Diện tích (nghìn ha) / Area (thousand ha)
  output_tons DECIMAL(14,2),          -- Sản lượng (tấn) / Output (tons)
  export_tons DECIMAL(14,2),          -- Xuất khẩu (tấn) / Export (tons)
  UNIQUE KEY uq_prod_year (year)
) CHARACTER SET utf8mb4;
```

### 💰 Bảng `coffee_export` (Xuất khẩu & Giá / Export & Prices)
```sql
CREATE TABLE coffee_export (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  export_value_million_usd DECIMAL(16,2),  -- Giá trị XK (triệu USD) / Export value
  price_world_usd_per_ton DECIMAL(12,2),   -- Giá thế giới (USD/tấn) / World price
  price_vn_usd_per_ton DECIMAL(12,2),      -- Giá VN (USD/tấn) / VN price
  UNIQUE KEY uq_trade_year (year)
) CHARACTER SET utf8mb4;
```

### 🌍 Bảng `market_trade` (Thị trường xuất khẩu / Export markets)
```sql
CREATE TABLE market_trade (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  year INT NOT NULL,
  country VARCHAR(100) NOT NULL,
  trade_value_thousand_usd DECIMAL(16,2),  -- Giá trị (nghìn USD) / Value (thousand USD)
  quantity_tons DECIMAL(14,2),             -- Khối lượng (tấn) / Quantity (tons)
  UNIQUE KEY uq_market (year, country)
) CHARACTER SET utf8mb4;
```

---

## 💻 Hướng Dẫn Sử Dụng / Usage Guide

### 🔄 Đồng bộ dữ liệu vào Database / Sync Data to Database

**Chạy script đồng bộ / Run sync script:**
```bash
python collect_data/sync_coffee.py
```

**Script sẽ thực hiện / Script will:**
1. ✅ Đọc file CSV từ thư mục `collect_data/` / Read CSV files
2. ✅ Chuyển đổi dữ liệu từ wide format sang long format / Transform wide to long format
3. ✅ Tạo/cập nhật các bảng trong database / Create/update database tables
4. ✅ Upsert dữ liệu vào MySQL (xử lý duplicate) / Upsert data (handle duplicates)
5. ✅ Tạo các bảng phân tích từ `coffee_long` / Create analysis tables

**Output mẫu / Sample output:**
```
✓ Đã đọc 17 dòng từ Data_coffee.csv / Read 17 rows from Data_coffee.csv
✓ Chuyển đổi sang long format: 340 records / Transformed to long format: 340 records
✓ Đã tạo bảng coffee_long / Created table coffee_long
✓ Đã insert 340 records / Inserted 340 records
✓ Đã tạo bảng production, coffee_export, weather, market_trade
✓ Hoàn thành đồng bộ! / Sync completed!
```

### 📓 Sử dụng Jupyter Notebooks / Using Jupyter Notebooks

**Khởi động Jupyter / Start Jupyter:**
```bash
jupyter notebook
```

**Các notebook chính / Main notebooks:**

1. **`collect_data/main_coffee.ipynb`**
   - Xử lý dữ liệu cà phê / Coffee data processing
   - Kết nối database / Database connection
   - Thực thi SQL queries / Execute SQL queries

2. **`collect_data/export_api.ipynb`**
   - Thu thập dữ liệu từ World Bank WITS API / Fetch data from WITS API
   - Dữ liệu xuất khẩu theo quốc gia / Export data by country
   - Mã HS: 090111 (Coffee, not roasted)

3. **`visualize/Time_Series.ipynb`**
   - Phân tích chuỗi thời gian / Time series analysis
   - Xu hướng sản xuất và xuất khẩu / Production and export trends

4. **`visualize/pair_plot.ipynb`**
   - Ma trận tương quan / Correlation matrix
   - Phân tích mối quan hệ giữa các biến / Analyze relationships

5. **`visualize/scatterplot_production.ipynb`**
   - Biểu đồ phân tán sản xuất / Production scatter plots
   - Mối quan hệ diện tích - sản lượng / Area-output relationship

### 🌐 Sử dụng Web Dashboard / Using Web Dashboard

**Mở dashboard / Open dashboard:**
```bash
# Mở trực tiếp file / Open file directly
open web/index.html

# Hoặc sử dụng local server / Or use local server
python -m http.server 8000
# Truy cập / Access: http://localhost:8000/web/
```

**Các tính năng dashboard / Dashboard features:**
- 📊 **Market Overview**: Giá cà phê real-time / Real-time coffee prices
- 📈 **Production Stats**: Thống kê sản xuất / Production statistics
- 🌡️ **Climate Impact**: Ảnh hưởng khí hậu / Climate impact analysis
- 🤖 **AI Forecasts**: Dự báo xu hướng / Trend predictions
- 🗺️ **Export Markets**: Thị trường xuất khẩu / Export market distribution

---

## 📊 Nguồn Dữ Liệu / Data Sources

### 1. Dữ liệu nội bộ / Internal Data (CSV files)
- **`Data_coffee.csv`**:
  - Diện tích trồng (2005-2024) / Cultivation area
  - Sản lượng sản xuất / Production output
  - Sản lượng xuất khẩu / Export volume
  - Giá cà phê VN và thế giới / VN and world coffee prices
  - Dữ liệu khí hậu / Climate data (temperature, humidity, rainfall)

- **`Thi_phan_3_thi_truong_chinh.csv`**:
  - Thị phần xuất khẩu theo quốc gia / Export market share by country
  - Giá trị và khối lượng xuất khẩu / Export value and quantity

### 2. World Bank WITS API
- Dữ liệu thương mại quốc tế / International trade data
- Mã HS: 090111 (Coffee, not roasted, not decaffeinated)
- Quốc gia / Country: Vietnam (VNM)
- Thời gian / Period: 2005-2024

**Ví dụ API call / API call example:**
```python
url = f"https://wits.worldbank.org/trade/comtrade/en/country/VNM/year/{year}/tradeflow/Exports/partner/ALL/product/090111"
```

---

## 🔄 Data Pipeline Flow

```
┌─────────────────┐
│   CSV Files     │
│  (Wide Format)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Cleaning   │
│ & Validation    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Wide → Long     │
│ Transformation  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MySQL Database  │
│ (Normalized)    │
└────────┬────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
    ┌────────┐    ┌─────────┐    ┌──────────┐
    │ Charts │    │ Reports │    │ Web UI   │
    └────────┘    └─────────┘    └──────────┘
```

### Chi tiết các bước / Pipeline Steps:

**1. Extract (Trích xuất / Extraction)**
```python
df = pd.read_csv("Data_coffee.csv", encoding="utf-8")
```

**2. Transform (Chuyển đổi / Transformation)**
```python
# Wide → Long format
long_df = df.melt(
    id_vars=["Hang_muc"],
    value_vars=year_cols,
    var_name="year",
    value_name="value"
)

# Clean data
long_df["year"] = pd.to_numeric(long_df["year"], errors="coerce")
long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
long_df = long_df.dropna(subset=["year"])
```

**3. Load (Nạp dữ liệu / Loading)**
```python
# Upsert với xử lý duplicate / Upsert with duplicate handling
upsert_sql = """
INSERT INTO coffee_long (hang_muc, year, value)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE value = VALUES(value)
"""
```

**4. Analyze (Phân tích / Analysis)**
```python
# Tạo bảng phân tích / Create analysis tables
INSERT INTO production (year, area_thousand_ha, output_tons, export_tons)
SELECT year,
       MAX(CASE WHEN hang_muc LIKE 'Area%' THEN value END),
       MAX(CASE WHEN hang_muc LIKE 'San luong ca phe san xuat%' THEN value END),
       MAX(CASE WHEN hang_muc LIKE 'San luong ca phe xuat khau%' THEN value END)
FROM coffee_long
GROUP BY year
```

---

## 📚 Tài Liệu Tham Khảo / References

### Documentation
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Data Sources
- [World Bank WITS](https://wits.worldbank.org/)
- [Vietnam Coffee Association](http://www.vicofa.org.vn/)
- [ICO - International Coffee Organization](https://www.ico.org/)

---

## 🤝 Đóng Góp / Contributing

Chúng tôi hoan nghênh mọi đóng góp! / Contributions are welcome!

### Cách đóng góp / How to contribute:

1. **Fork repository**
2. **Tạo branch mới / Create new branch:**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit changes:**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to branch:**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Mở Pull Request / Open Pull Request**

---

## 📄 Giấy Phép / License

Dự án này được phân phối dưới giấy phép MIT License.

This project is distributed under the MIT License.

---

## 👥 Tác Giả / Authors

- **Đặng Quang Nhật** - *Initial work*
- **Phạm Minh Tiến** - *Initial work*
- **Nguyễn Thái Hưng** - *Initial work*
- **Phan Tuấn Hưng** - *Initial work*
- **Trương Công Phúc** - *Initial work*
---

## 🙏 Lời Cảm Ơn / Acknowledgments

- 🌟 Vietnam Coffee Association (VICOFA)
- 🌟 World Bank WITS Database
- 🌟 Open-source community
- 🌟 All contributors and supporters

---

## 📞 Liên Hệ / Contact

- **Email**: your-email@example.com
- **GitHub**: https://github.com/your-username/coffee-export-project

---

## 📊 Thống Kê Dự Án / Project Stats

- **Lines of Code**: ~5,000+
- **Data Points**: 340+ records (2005-2024)
- **Database Tables**: 5 tables
- **Visualizations**: 10+ charts
- **Languages**: Python, JavaScript, SQL, HTML/CSS

---

## ⚠️ Lưu Ý Quan Trọng / Important Notes

> **Disclaimer**: Dự án này phục vụ mục đích nghiên cứu và giáo dục. Dữ liệu nên được xác minh với nguồn chính thức trước khi sử dụng cho quyết định kinh doanh.

> **Note**: This project is for educational and research purposes. Data accuracy should be verified with official sources before making business decisions.

---

**⭐ Nếu dự án hữu ích, hãy cho chúng tôi một star trên GitHub!**

**⭐ If you find this project useful, please give us a star on GitHub!**

---

*Last Updated: November 2025 | Version: 1.0.0*
