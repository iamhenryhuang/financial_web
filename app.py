from flask import Flask, render_template, request, jsonify, url_for, redirect
from datetime import datetime
from utils.twse import get_stock_basic_info, get_market_summary, get_stock_name
import os

app = Flask(__name__)

# 全域配置
app.config['SECRET_KEY'] = 'your-secret-key-here'

@app.route('/')
def home():
    """首頁 - 股票搜尋和大盤資訊"""
    try:
        # 獲取大盤摘要
        market_info = get_market_summary()
        
        # 熱門股票列表
        popular_stocks = [
            {'code': '2330', 'name': '台積電'},
            {'code': '0050', 'name': '元大台灣50'},
            {'code': '0056', 'name': '元大高股息'},
            {'code': '006208', 'name': '富邦台50'},
            {'code': '00878', 'name': '國泰永續高股息'},
            {'code': '00919', 'name': '群益台灣精選高息'},
            {'code': '2317', 'name': '鴻海'},
            {'code': '2454', 'name': '聯發科'}
        ]
        
        return render_template('home.html', 
                             market_info=market_info,
                             popular_stocks=popular_stocks,
                             current_time=datetime.now())
        
    except Exception as e:
        print(f"首頁錯誤: {e}")
        return render_template('home.html', 
                             market_info={'錯誤': '無法載入大盤資訊'},
                             popular_stocks=[],
                             current_time=datetime.now())


@app.route('/stock')
def stock_page():
    """個股頁面"""
    stock_code = request.args.get('code', '').strip()
    
    if not stock_code:
        return render_template('stock.html', 
                             stock_code='',
                             stock_info=None,
                             error='請輸入股票代碼')
    
    try:
        # 獲取股票資訊
        stock_info = get_stock_basic_info(stock_code)
        
        if stock_info and not stock_info.get('錯誤'):
            return render_template('stock.html',
                                 stock_code=stock_code,
                                 stock_info=stock_info,
                                 error=None,
                                 current_time=datetime.now())
        else:
            error_msg = stock_info.get('錯誤', '無法找到股票資料') if stock_info else '無法找到股票資料'
            return render_template('stock.html',
                                 stock_code=stock_code,
                                 stock_info=None,
                                 error=error_msg)
            
    except Exception as e:
        print(f"股票頁面錯誤: {e}")
        return render_template('stock.html',
                             stock_code=stock_code,
                             stock_info=None,
                             error=f'系統錯誤: {str(e)}')


@app.route('/search')
def search_redirect():
    """搜尋重導向"""
    stock_code = request.args.get('q', '').strip()
    if stock_code:
        return redirect(url_for('stock_page', code=stock_code))
    return redirect(url_for('home'))


# === API 端點 ===

@app.route('/api/stock/<stock_code>')
def api_stock(stock_code):
    """API: 獲取個股資訊"""
    try:
        stock_info = get_stock_basic_info(stock_code)
        
        if stock_info and not stock_info.get('錯誤'):
            return jsonify({
                'success': True,
                'data': stock_info,
                'timestamp': datetime.now().isoformat()
            })
        else:
            error_msg = stock_info.get('錯誤', '無法找到股票資料') if stock_info else '無法找到股票資料'
            return jsonify({
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/market')
def api_market():
    """API: 獲取大盤資訊"""
    try:
        market_info = get_market_summary()
        
        return jsonify({
            'success': True,
            'data': market_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/popular')
def api_popular():
    """API: 獲取熱門股票清單"""
    try:
        popular_codes = ['2330', '0050', '0056', '2317', '2454', '2882', '2412', '00878']
        popular_stocks = []
        
        for code in popular_codes:
            try:
                stock_info = get_stock_basic_info(code)
                if stock_info and not stock_info.get('錯誤'):
                    popular_stocks.append({
                        'code': code,
                        'name': stock_info.get('股票名稱', get_stock_name(code)),
                        'price': stock_info.get('收盤價', 'N/A'),
                        'change': stock_info.get('漲跌價差', 'N/A'),
                        'change_percent': stock_info.get('漲跌幅', 'N/A')
                    })
            except:
                # 如果個別股票失敗，跳過
                continue
        
        return jsonify({
            'success': True,
            'data': popular_stocks,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# === 錯誤處理 ===

@app.errorhandler(404)
def not_found(error):
    """404 錯誤頁面"""
    return render_template('error.html', 
                         error_code=404,
                         error_message='頁面不存在'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 錯誤頁面"""
    return render_template('error.html',
                         error_code=500,
                         error_message='伺服器內部錯誤'), 500


# === 模板過濾器 ===

@app.template_filter('format_number')
def format_number(value):
    """格式化數字顯示"""
    try:
        if value and value != 'N/A':
            # 移除逗號並轉換為浮點數
            num = float(str(value).replace(',', ''))
            return f"{num:,.0f}"
        return value
    except:
        return value


@app.template_filter('format_price')
def format_price(value):
    """格式化價格顯示"""
    try:
        if value and value != 'N/A':
            num = float(str(value).replace(',', ''))
            return f"{num:.2f}"
        return value
    except:
        return value


@app.template_filter('change_class')
def change_class(value):
    """根據漲跌返回 CSS 類別"""
    try:
        if value and value != 'N/A':
            if value.startswith('+'):
                return 'text-success'  # 綠色 (上漲)
            elif value.startswith('-'):
                return 'text-danger'   # 紅色 (下跌)
        return 'text-muted'  # 灰色 (無變化)
    except:
        return 'text-muted'


if __name__ == '__main__':
    # 確保 static 資料夾存在
    os.makedirs('static', exist_ok=True)
    
    print("🚀 台股財經網站啟動中...")
    print("📊 支援即時股價查詢")
    print("🌐 網址: http://127.0.0.1:5000")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
