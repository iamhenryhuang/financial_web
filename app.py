import os
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, url_for
import yfinance as yf
from datetime import datetime, timedelta

app = Flask(__name__)

def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 獲取基本資訊
        stock_data = {
            'symbol': symbol,
            'name': info.get('longName', 'N/A'),
            'current_price': info.get('currentPrice', 'N/A'),
            'previous_close': info.get('previousClose', 'N/A'),
            'open': info.get('open', 'N/A'),
            'volume': info.get('volume', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A')
        }
        
        # 獲取歷史價格數據
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        hist = stock.history(start=start_date, end=end_date)

        if not hist.empty:
            stock_data['history'] = hist
            stock_data['chart_url'] = generate_stock_chart(hist, symbol)  # 產生股價圖
        else:
            stock_data['history'] = None
            stock_data['chart_url'] = None

        return stock_data, None
    except Exception as e:
        return None, str(e)

def generate_stock_chart(hist, symbol):
    """繪製近 30 天股價圖，儲存到 static 資料夾"""
    plt.figure(figsize=(10, 5))
    plt.plot(hist.index, hist["Close"], label="收盤價", color="blue", linewidth=2)
    plt.xlabel("日期")
    plt.ylabel("股價 (USD)")
    plt.title(f"{symbol} 近30天股價走勢")
    plt.legend()
    plt.grid(True)

    # 確保 static 資料夾存在
    if not os.path.exists("static"):
        os.makedirs("static")

    # 儲存圖片
    img_path = f"static/{symbol}.png"
    plt.savefig(img_path)
    plt.close()

    return url_for('static', filename=f"{symbol}.png")

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/stock', methods=['GET'])
def stock():
    symbol = request.args.get('symbol', '')
    if symbol:
        stock_data, error = get_stock_info(symbol)
        return render_template('stock.html', stock=stock_data, error=error)
    return render_template('stock.html')

if __name__ == '__main__':
    app.run(debug=True)