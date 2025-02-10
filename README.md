# 智慧股市分析平台

## 專案描述
這是一個基於 Flask 和 Yahoo Finance API 的股票分析應用程式，提供市場指數、個股數據及技術分析圖表。

我們的功能包含：
- 台股加權指數即時查詢
- 個股詳細資訊，包括成交量、市值、EPS、殖利率等
- 股價走勢圖與成交量圖表
- 熱門股票推薦與市場概況

## 快速開始
### 1. 下載專案
```bash
git clone https://github.com/your-repo/stock-analysis.git
```

### 2. 安裝環境需求
請確保安裝以下套件：
```bash
pip install flask yfinance matplotlib pandas numpy
```

### 3. 啟動應用程式
進入專案目錄：
```bash
cd stock-analysis
```
啟動 Flask 伺服器：
```bash
python app.py
```

開啟瀏覽器並前往：http://127.0.0.1:5000/

## 專案結構
```
📂 智慧股市分析平台
├── app.py                 # Flask 應用程式主程式
├── templates/             # HTML 模板檔案
│   ├── home.html          # 首頁
│   ├── stock.html         # 個股資訊頁面
├── static/                # 靜態檔案 (CSS, JS, 圖片等)
│   ├── style.css          # 樣式表
├── README.md              # 本文件
```

## API 端點
我們提供 RESTful API，讓使用者查詢股票資訊。

### `GET /api/stock/<symbol>`
回應格式：
```json
{
    "symbol": "2330.TW",
    "name": "台積電",
    "current_price": 600.5,
    "market_cap": 155000000000,
    "pe_ratio": 15.3
}
```

## 開發計畫
- 增加技術指標分析，如 RSI、MACD
- 加入即時新聞爬取
- 增加用戶自訂股票關注列表
