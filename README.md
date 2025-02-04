```markdown
# 智慧股市分析平台 📈

這是一個基於 Flask 和 Yahoo Finance API 的股票分析應用程式，提供市場指數、個股數據及技術分析圖表。

## 主要功能
✅ 台股加權指數即時查詢  
✅ 個股詳細資訊，包括成交量、市值、EPS、殖利率等  
✅ 股價走勢圖與成交量圖表  
✅ 熱門股票推薦與市場概況  

## 環境需求
- Python 3.x
- Flask
- yfinance
- Matplotlib
- Pandas
- NumPy

## 安裝與運行 🚀

1️⃣ **安裝相依套件**
```bash
pip install flask yfinance matplotlib pandas numpy
```

2️⃣ **運行應用程式**
```bash
python app.py
```

3️⃣ **訪問網站**
打開瀏覽器並輸入：
```
http://127.0.0.1:5000/
```

## 專案結構
```
📂 智慧股市分析平台
├── app.py                 # Flask 應用程式
├── templates/
│   ├── home.html          # 首頁
│   ├── stock.html         # 個股資訊頁
├── static/
│   ├── style.css          # 樣式表
├── README.md              # 本文件
```

## API 端點
📌 `GET /api/stock/<symbol>`  
返回指定股票的即時資訊，例如：
```json
{
    "symbol": "2330.TW",
    "name": "台積電",
    "current_price": 600.5,
    "market_cap": 155000000000,
    "pe_ratio": 15.3
}
```

## 未來開發計畫 🛠
- 增加技術指標分析，如 RSI、MACD
- 加入即時新聞爬取
- 增加用戶自訂股票關注列表

## 作者
💡 **Henry Huang**  
📧 聯絡方式：henry.curry1008@gmail.com
```
