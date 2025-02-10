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

def get_market_info():
    """獲取市場數據"""
    try:
        # 獲取台股指數
        twii = yf.Ticker('^TWII')
        twii_info = twii.info
        
        market_index = twii_info.get('regularMarketPrice', 'N/A')
        previous_close = twii_info.get('regularMarketPreviousClose', 0)
        
        # 計算漲跌幅
        if market_index != 'N/A' and previous_close:
            market_change = ((market_index - previous_close) / previous_close * 100)
        else:
            market_change = 0
            
        # 計算成交量（轉換為億元）
        market_volume = twii_info.get('regularMarketVolume', 'N/A')
        if market_volume != 'N/A':
            market_volume = f"{market_volume / 100000000:.2f}"
            
        # 獲取最新指數資料
        hist = twii.history(period='1d')
        if not hist.empty:
            market_index = hist['Close'].iloc[-1]
            market_volume = f"{hist['Volume'].iloc[-1] / 100000000:.2f}"
            
        return {
            'market_index': market_index,
            'market_change': market_change,
            'market_volume': market_volume
        }
    except Exception as e:
        print(f"Error getting market info: {e}")
        return {
            'market_index': 'N/A',
            'market_change': 0,
            'market_volume': 'N/A'
        }

def get_stock_info(symbol):
    """獲取個股資訊"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 檢查數值是否有效
        def validate_number(value):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
            return 'N/A'
        
        # 取得成交量
        hist = stock.history(period="1d")  # 只取最近 1 天數據
        if not hist.empty:
            volume = hist['Volume'].iloc[-1]  # 取得最新成交量
        else:
            volume = 'N/A'  # 無法獲取數據時回傳 N/A
        
        # 基本資訊
        stock_data = {
            'symbol': symbol,
            'name': info.get('longName', 'N/A'),
            'current_price': validate_number(info.get('currentPrice')),
            'previous_close': validate_number(info.get('previousClose')),
            'open': validate_number(info.get('open')),
            'volume': volume,  # 使用 history() 取得的成交量
            'market_cap': validate_number(info.get('marketCap')),
            'pe_ratio': validate_number(info.get('trailingPE')),
            'eps': validate_number(info.get('trailingEps')),
            'dividend_yield': validate_number(info.get('dividendYield')),
            'fifty_two_week_high': validate_number(info.get('fiftyTwoWeekHigh')),
            'fifty_two_week_low': validate_number(info.get('fiftyTwoWeekLow')),
            'avg_volume': validate_number(info.get('averageVolume')),
            'high_today': validate_number(info.get('dayHigh')),
            'low_today': validate_number(info.get('dayLow'))
        }
        
        # 獲取歷史數據
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        hist = stock.history(start=start_date, end=end_date)
        
        if not hist.empty:
            stock_data['history'] = hist
            
            # 生成圖表
            stock_data['price_chart_url'] = generate_price_chart(hist, symbol)
            stock_data['volume_chart_url'] = generate_volume_chart(hist, symbol)
            
            # 計算漲跌幅
            if isinstance(stock_data['current_price'], (int, float)) and isinstance(stock_data['previous_close'], (int, float)):
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
    plt.style.use('classic')
    
    # 設置中文字型
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False  # 正確顯示負號
    
    # 設置背景色和網格
    plt.rcParams['axes.facecolor'] = '#f8fafc'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 繪製K線圖
    plt.plot(hist.index, hist['Close'], label='收盤價', color='#2563eb', linewidth=2)
    plt.fill_between(hist.index, hist['Low'], hist['High'], color='#93c5fd', alpha=0.3)
    
    # 添加移動平均線
    ma5 = hist['Close'].rolling(window=5).mean()
    ma20 = hist['Close'].rolling(window=20).mean()
    plt.plot(hist.index, ma5, label='5日均線', color='#dc2626', linestyle='--', alpha=0.8)
    plt.plot(hist.index, ma20, label='20日均線', color='#16a34a', linestyle='--', alpha=0.8)
    
    plt.title(f'{symbol} Price Trend', fontsize=14, pad=20)  # 改用英文避免字型問題
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price', fontsize=12)
    plt.legend(loc='best', frameon=True)
    
    # 調整邊距
    plt.margins(x=0.01)
    
    # 確保 static 資料夾存在
    if not os.path.exists("static"):
        os.makedirs("static")
    
    img_path = f"static/{symbol}_price.png"
    plt.savefig(img_path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return url_for('static', filename=f"{symbol}_price.png")

def generate_volume_chart(hist, symbol):
    """生成成交量圖"""
    plt.figure(figsize=(12, 3))
    plt.style.use('classic')
    
    # 設置中文字型
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 設置背景色和網格
    plt.rcParams['axes.facecolor'] = '#f8fafc'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 根據漲跌標註顏色
    colors = ['#16a34a' if close_price > open_price else '#dc2626' 
              for close_price, open_price in zip(hist['Close'], hist['Open'])]
    
    plt.bar(hist.index, hist['Volume'], color=colors, alpha=0.7)
    
    # 添加成交量移動平均線
    volume_ma = hist['Volume'].rolling(window=5).mean()
    plt.plot(hist.index, volume_ma, color='#2563eb', linewidth=2, label='5MA Volume')
    
    plt.title(f'{symbol} Volume Analysis', fontsize=14, pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Volume', fontsize=12)
    plt.legend(loc='best', frameon=True)
    
    # 調整邊距
    plt.margins(x=0.01)
    
    img_path = f"static/{symbol}_volume.png"
    plt.savefig(img_path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return url_for('static', filename=f"{symbol}_volume.png")

@app.route('/')
def home():
    """首頁路由"""
    # 獲取市場概況
    market_info = get_market_info()
    
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
                'price_change': price_change,
                'volume': info.get('volume', 'N/A')
            })
        except Exception as e:
            print(f"Error getting stock info for {symbol}: {e}")
            continue
    
    return render_template('home.html',
                         now=datetime.now(),
                         market_index=market_info['market_index'],
                         market_change=market_info['market_change'],
                         market_volume=market_info['market_volume'],
                         popular_stocks=stocks_info)

@app.route('/stock', methods=['GET'])
def stock():
    """股票詳情頁面路由"""
    symbol = request.args.get('symbol', '')
    if symbol:
        stock_data, error = get_stock_info(symbol)
        return render_template('stock.html', 
                             stock=stock_data, 
                             error=error,
                             now=datetime.now())  # 添加 now 變數
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
