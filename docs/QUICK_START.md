# 🚀 Hướng Dẫn Nhanh - Vietnam Coffee Data Portal

## 📋 Yêu Cầu Hệ Thống

- **Node.js** >= 16.x (khuyến nghị v18 hoặc v20)
- **Python** >= 3.8
- **npm** hoặc **yarn**

## ⚡ Cài Đặt và Chạy (3 Bước)

### 1️⃣ Cài đặt dependencies

```bash
npm install
```

Lệnh này sẽ tự động:
- ✅ Cài đặt Node.js dependencies
- ✅ Cài đặt Python packages (Flask, pandas, SQLAlchemy, etc.)
- ✅ Kiểm tra Python environment

### 2️⃣ Cấu hình Database (Chỉ lần đầu)

File `.env` đã có sẵn với thông tin database. Nếu cần thay đổi, chỉnh sửa file `.env`:

```env
HOST="your-database-host.aivencloud.com"
USER="your-username"
PASSWORD="your-password"
PORT=19034
DB="defaultdb"
```

> ⚠️ **LƯU Ý:** File `.env` chứa thông tin nhạy cảm, **KHÔNG** commit lên Git!

### 3️⃣ Chạy Development Server

```bash
npm run dev
```

Website sẽ tự động:
- 🚀 Khởi động Flask API server trên `http://localhost:5000`
- 🌐 Mở website trên trình duyệt mặc định
- 🔄 API tự động kết nối với database

## 📦 Các Lệnh Khác

### Chỉ khởi động API (không mở browser)
```bash
npm run api
```

### Kiểm tra trạng thái API
```bash
npm run check
```

## 🌐 Địa chỉ truy cập

- **Website:** http://localhost:5000 (hoặc mở trực tiếp `wed/index.html`)
- **API Backend:** http://localhost:5000
- **API Health Check:** http://localhost:5000/api/health

## 📋 Các API Endpoints

| Endpoint | Mô tả |
|----------|-------|
| `/api/health` | Kiểm tra trạng thái API |
| `/api/weather/province/<province>` | Dữ liệu thời tiết theo tỉnh |
| `/api/production` | Dữ liệu sản xuất cà phê |
| `/api/coffee_export` | Dữ liệu xuất khẩu |
| `/api/export_country` | Xuất khẩu theo quốc gia |
| `/api/production/province` | Sản xuất theo tỉnh |

## 🔧 Xử Lý Lỗi

### Lỗi: "Missing required database credentials"
➡️ Kiểm tra file `.env` đã được tạo và có đầy đủ thông tin chưa

### Lỗi: "Python not found" hoặc "pip not found"
➡️ Cài đặt Python từ [python.org](https://python.org) hoặc sử dụng Anaconda

### Lỗi: Port 5000 đã được sử dụng

```powershell
# Tìm process đang chiếm port
Get-NetTCPConnection -LocalPort 5000 | Select-Object -Property OwningProcess

# Kill process
Stop-Process -Id <PID> -Force
```

### Lỗi: Module not found

```bash
# Cài đặt lại Python dependencies
pip install -r requirements.txt
```

## 📚 Tài Liệu Chi Tiết

Xem [README.md](README.md) để biết thêm thông tin về:
- Cấu trúc project
- API endpoints đầy đủ
- Database schema
- Development workflow

## ✅ Kiểm tra setup

Chạy script kiểm tra tự động:
```powershell
python setup_check.py
```

Script này sẽ kiểm tra:
- ✅ Python version
- ✅ Dependencies
- ✅ Database connection
- ✅ Environment variables
- ✅ CSV files
- ✅ Project structure

## 📝 Ghi chú

- API đã được cấu hình để tự động fallback từ SSL sang non-SSL nếu cần
- Frontend mặc định chạy trên port 8081 (thay vì 8080) để tránh xung đột
- Tất cả đường dẫn file đã được portable hóa (không còn hard-coded paths)
- Dự án có thể chạy trên bất kỳ máy nào có Python 3.8+ và Node.js

## 🎯 Các tính năng chính

1. **Weather Data Visualization** - Dữ liệu thời tiết 5 tỉnh trồng cà phê
2. **Production Analysis** - Phân tích sản xuất và xuất khẩu
3. **Export Statistics** - Thống kê xuất khẩu theo quốc gia
4. **Interactive Charts** - Biểu đồ tương tác với Chart.js
5. **Time Series Forecasting** - Dự báo xuất khẩu

---

**Cập nhật:** $(Get-Date -Format "yyyy-MM-dd HH:mm")  
**Trạng thái:** ✅ API đang chạy thành công