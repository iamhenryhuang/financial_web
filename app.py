import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, render_template, request, url_for, jsonify
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 基本資訊
        stock_data = {
            'symbol': symbol,
            'name': info.get('longName', 'N/A'),
            'current_price': info.get('currentPrice', 'N/A'),
            'previous_close': info.get('previousClose', 'N/A'),
            'open': info.get('open', 'N/A'),
            'volume': info.get('volume', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'eps': info.get('trailingEps', 'N/A'),
            'dividend_yield': info.get('dividendYield', 'N/A'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            'avg_volume': info.get('averageVolume', 'N/A'),
            'high_today': info.get('dayHigh', 'N/A'),
            'low_today': info.get('dayLow', 'N/A')
        }
        
        # 獲取歷史數據
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 改為90天
        hist = stock.history(start=start_date, end=end_date)
        
        if not hist.empty:
            stock_data['history'] = hist
            
            # 生成圖表
            stock_data['price_chart_url'] = generate_price_chart(hist, symbol)
            stock_data['volume_chart_url'] = generate_volume_chart(hist, symbol)
            
            # 計算漲跌幅
            if stock_data['current_price'] != 'N/A' and stock_data['previous_close'] != 'N/A':
                stock_data['price_change'] = ((stock_data['current_price'] - stock_data['previous_close']) / 
                                            stock_data['previous_close'] * 100)
            else:
                stock_data['price_change'] = 'N/A'
            
            # 計算移動平均線
            stock_data['ma5'] = hist['Close'].rolling(window=5).mean().iloc[-1]
            stock_data['ma20'] = hist['Close'].rolling(window=20).mean().iloc[-1]
            stock_data['ma60'] = hist['Close'].rolling(window=60).mean().iloc[-1]
            
        else:
            stock_data['history'] = None
        
        return stock_data, None
        
    except Exception as e:
        return None, str(e)

def generate_price_chart(hist, symbol):
    """生成價格走勢圖"""
    plt.figure(figsize=(12, 6))
    
    # 繪製K線圖
    plt.plot(hist.index, hist['Close'], label='Closing Price', color='#2563eb', linewidth=2)
    plt.fill_between(hist.index, hist['Low'], hist['High'], color='#93c5fd', alpha=0.3)
    
    # 添加移動平均線
    ma5 = hist['Close'].rolling(window=5).mean()
    ma20 = hist['Close'].rolling(window=20).mean()
    plt.plot(hist.index, ma5, label='5MA', color='#dc2626', linestyle='--', alpha=0.8)
    plt.plot(hist.index, ma20, label='20MA', color='#16a34a', linestyle='--', alpha=0.8)
    
    plt.title(f'{symbol} Price Trend Chart')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 確保 static 資料夾存在
    if not os.path.exists("static"):
        os.makedirs("static")
    
    img_path = f"static/{symbol}_price.png"
    plt.savefig(img_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return url_for('static', filename=f"{symbol}_price.png")

def generate_volume_chart(hist, symbol):
    """生成成交量圖"""
    plt.figure(figsize=(12, 3))
    
    # 根據漲跌標註顏色
    colors = ['#16a34a' if close_price > open_price else '#dc2626' 
              for close_price, open_price in zip(hist['Close'], hist['Open'])]
    
    plt.bar(hist.index, hist['Volume'], color=colors, alpha=0.7)
    plt.title(f'{symbol} Trading Volume Chart')
    plt.xlabel('Date')
    plt.ylabel('Trading Volume')
    plt.grid(True, alpha=0.3)
    
    img_path = f"static/{symbol}_volume.png"
    plt.savefig(img_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return url_for('static', filename=f"{symbol}_volume.png")

@app.route('/')
def home():
    # 獲取熱門股票資訊
    popular_stocks = ['2330.TW', '2317.TW', '2454.TW', '3706.TW', '2308.TW']
    stocks_info = []
    
    for symbol in popular_stocks:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            current_price = info.get('currentPrice', 'N/A')
            previous_close = info.get('previousClose', 'N/A')
            
            if current_price != 'N/A' and previous_close != 'N/A':
                price_change = ((current_price - previous_close) / previous_close * 100)
            else:
                price_change = 'N/A'
                
            stocks_info.append({
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'current_price': current_price,
                'price_change': price_change
            })
        except:
            continue
            
    return render_template('home.html', popular_stocks=stocks_info)

@app.route('/stock', methods=['GET'])
def stock():
    symbol = request.args.get('symbol', '')
    if symbol:
        stock_data, error = get_stock_info(symbol)
        return render_template('stock.html', stock=stock_data, error=error)
    return render_template('stock.html')

@app.route('/api/stock/<symbol>')
def stock_api(symbol):
    """API端點用於獲取股票即時資訊"""
    stock_data, error = get_stock_info(symbol)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(stock_data)

if __name__ == '__main__':
    app.run(debug=True)
