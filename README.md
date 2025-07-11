# 台股財經網站

一個現代化的台股即時查詢系統，提供股票價格查詢、大盤資訊、會員系統和 REST API 服務。

## 🚀 功能特色

- **即時股價查詢**：支援台股個股、ETF 查詢
- **大盤資訊**：顯示市場概況和指數資料
- **會員系統**：三層會員制度（免費/付費/VIP）
- **自選股管理**：會員專屬自選股功能
- **搜尋歷史**：自動記錄查詢歷史
- **現代化介面**：使用 Bootstrap 5 響應式設計
- **REST API**：提供 JSON 格式的資料接口
- **多重資料來源**：Yahoo Finance API 為主，確保資料穩定性
- **智能快取**：5分鐘快取機制，提升查詢效能

## 📱 介面預覽

### 首頁
- 股票搜尋功能
- 大盤指數資訊
- 熱門股票快速連結

### 個股頁面
- 完整股票資訊展示
- 即時價格和漲跌幅
- 交易量和基本資料
- 加入自選股功能（會員專屬）

### 會員系統
- **登入/註冊**：安全的用戶認證
- **會員控制台**：個人化儀表板
- **自選股管理**：即時價格追蹤
- **個人資料**：資料編輯和會員狀態
- **搜尋歷史**：查詢記錄管理

## 🛠 技術架構

- **後端**：Python Flask + Flask-Login + Flask-SQLAlchemy
- **前端**：Bootstrap 5 + JavaScript
- **資料庫**：SQLite + SQLAlchemy 2.0
- **資料來源**：Yahoo Finance API
- **快取系統**：檔案快取（5分鐘）
- **樣式**：自定義 CSS + Bootstrap Icons

## 📂 專案結構

```
financial_web/
├── app.py                 # Flask 主應用程式
├── models.py              # 資料庫模型
├── forms.py               # 表單類別
├── db_viewer.py           # 資料庫查看工具
├── utils/
│   └── twse.py           # 股票資料抓取模組
├── templates/
│   ├── home.html         # 首頁模板
│   ├── stock.html        # 個股頁面模板
│   ├── auth/
│   │   ├── login.html    # 登入頁面
│   │   └── register.html # 註冊頁面
│   ├── member/
│   │   ├── dashboard.html # 會員控制台
│   │   ├── watchlist.html # 自選股管理
│   │   ├── profile.html   # 個人資料
│   │   └── change_password.html # 修改密碼
│   └── error.html        # 錯誤頁面模板
├── static/
│   └── style.css         # 自定義樣式
├── cache/                # 快取資料夾
├── instance/             # 資料庫檔案
└── README.md             # 說明文件
```

## 🚀 快速開始

### 1. 安裝相依套件

```bash
pip install flask flask-sqlalchemy flask-login flask-wtf wtforms email-validator requests pandas werkzeug
```

### 2. 初始化資料庫

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 3. 啟動應用程式

```bash
python app.py
```

### 4. 開啟瀏覽器
```
http://127.0.0.1:5000
```
---

**免責聲明**：本系統提供的股價資訊僅供參考，不構成投資建議。投資有風險，請謹慎評估後做出決策。 
