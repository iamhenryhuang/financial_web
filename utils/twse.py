import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import re

CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

# 配置選項
CONFIG = {
    'timeout': 20,  # 增加超時時間
    'retry_times': 3,  # 增加重試次數
    'cache_duration': 300,  # 縮短快取時間到5分鐘，獲取更新數據
}

# 請求標頭
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
}


def get_stock_from_yahoo(stock_code):
    """從 Yahoo Finance 獲取股票資料（備用方案）"""
    try:
        # 台股在 Yahoo Finance 的格式
        if not stock_code.endswith('.TW'):
            yahoo_symbol = f"{stock_code}.TW"
        else:
            yahoo_symbol = stock_code
            
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        
        resp = requests.get(url, timeout=CONFIG['timeout'], headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('chart') and data['chart'].get('result'):
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            
            # 基本股價資訊
            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('regularMarketPreviousClose', 0)
            open_price = meta.get('regularMarketOpen', 0)
            high_price = meta.get('regularMarketDayHigh', 0)
            low_price = meta.get('regularMarketDayLow', 0)
            volume = meta.get('regularMarketVolume', 0)
            
            stock_info = {
                '股票代碼': stock_code,
                '股票名稱': get_stock_name(stock_code),
                '即時股價': f"{current_price:.2f}" if current_price else "N/A",
                '收盤價': f"{current_price:.2f}" if current_price else "N/A",
                '開盤價': f"{open_price:.2f}" if open_price else "N/A",
                '最高價': f"{high_price:.2f}" if high_price else "N/A",
                '最低價': f"{low_price:.2f}" if low_price else "N/A",
                '成交量': f"{volume:,}" if volume else "N/A",
            }
            
            # 計算漲跌
            if previous_close and current_price and previous_close > 0:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                stock_info['漲跌價差'] = f"{change:+.2f}"
                stock_info['漲跌幅'] = f"{change_percent:+.2f}%"
            else:
                stock_info['漲跌價差'] = "N/A"
                stock_info['漲跌幅'] = "N/A"
            
            # 嘗試從 meta 資料中獲取更完整的資訊
            try:
                # 從 meta 中獲取開盤價
                if meta.get('regularMarketOpen'):
                    stock_info['開盤價'] = f"{meta['regularMarketOpen']:.2f}"
                
                # 如果 meta 中有昨收和當前價格，重新計算漲跌
                prev_close_meta = meta.get('regularMarketPreviousClose') or meta.get('previousClose') or meta.get('chartPreviousClose')
                current_price_meta = meta.get('regularMarketPrice')
                
                if prev_close_meta and current_price_meta and prev_close_meta > 0:
                    change = current_price_meta - prev_close_meta
                    change_percent = (change / prev_close_meta) * 100
                    
                    stock_info['漲跌價差'] = f"{change:+.2f}"
                    stock_info['漲跌幅'] = f"{change_percent:+.2f}%"
                    print(f"💹 計算漲跌: 目前價格={current_price_meta}, 昨收={prev_close_meta}, 漲跌={change:+.2f}")
                    
            except Exception as e:
                print(f"⚠️ 處理 meta 資料失敗: {e}")
            
            # 嘗試獲取更多資料（備用方案）
            try:
                # 從 quote 資料中獲取
                quote_url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={yahoo_symbol}"
                quote_resp = requests.get(quote_url, timeout=5, headers=HEADERS)
                
                if quote_resp.status_code == 200:
                    quote_data = quote_resp.json()
                    
                    if quote_data.get('quoteResponse') and quote_data['quoteResponse'].get('result'):
                        quote_result = quote_data['quoteResponse']['result'][0]
                        
                        # 更新開盤價等資料
                        if quote_result.get('regularMarketOpen') and stock_info.get('開盤價') == "N/A":
                            stock_info['開盤價'] = f"{quote_result['regularMarketOpen']:.2f}"
                        if quote_result.get('regularMarketChange') and stock_info.get('漲跌價差') == "N/A":
                            stock_info['漲跌價差'] = f"{quote_result['regularMarketChange']:+.2f}"
                        if quote_result.get('regularMarketChangePercent') and stock_info.get('漲跌幅') == "N/A":
                            stock_info['漲跌幅'] = f"{quote_result['regularMarketChangePercent']:+.2f}%"
                        
            except Exception as e:
                print(f"⚠️ 獲取 Quote 資料失敗: {e}")
            
            print(f"✅ Yahoo Finance 成功獲取 {stock_code} 資料")
            return stock_info
            
    except Exception as e:
        print(f"Yahoo Finance 獲取失敗: {e}")
        return None


def get_stock_from_twse_api(stock_code):
    """從證交所 API 獲取股票資料"""
    try:
        # 嘗試不同的證交所 API
        urls = [
            f"https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date={datetime.now().strftime('%Y%m%d')}&stockNo={stock_code}&response=json",
            f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={datetime.now().strftime('%Y%m%d')}&stockNo={stock_code}",
        ]
        
        for url in urls:
            try:
                print(f"嘗試證交所 API: {stock_code}")
                resp = requests.get(url, timeout=CONFIG['timeout'], headers=HEADERS)
                resp.raise_for_status()
                data = resp.json()
                
                if data.get('stat') == 'OK' and data.get('data'):
                    # 取最新一天的資料
                    latest_data = data['data'][-1]
                    fields = data.get('fields', [])
                    
                    stock_info = {
                        '股票代碼': stock_code,
                        '股票名稱': get_stock_name(stock_code),
                    }
                    
                    # 對應欄位
                    field_mapping = {
                        '日期': 0,
                        '成交股數': 1,
                        '成交金額': 2,
                        '開盤價': 3,
                        '最高價': 4,
                        '最低價': 5,
                        '收盤價': 6,
                        '漲跌價差': 7,
                        '成交筆數': 8
                    }
                    
                    for field_name, index in field_mapping.items():
                        if index < len(latest_data):
                            stock_info[field_name] = latest_data[index]
                    
                    # 計算漲跌幅
                    try:
                        close_price = float(stock_info.get('收盤價', '0').replace(',', ''))
                        change_str = stock_info.get('漲跌價差', '0')
                        if change_str and change_str != '--':
                            change = float(change_str.replace(',', ''))
                            if close_price > 0:
                                prev_close = close_price - change
                                if prev_close > 0:
                                    change_percent = (change / prev_close) * 100
                                    stock_info['漲跌幅'] = f"{change_percent:+.2f}%"
                    except:
                        stock_info['漲跌幅'] = "N/A"
                    
                    print(f"✅ 證交所 API 成功獲取 {stock_code} 資料")
                    return stock_info
                    
            except Exception as e:
                print(f"證交所 API 嘗試失敗: {e}")
                continue
                
        return None
        
    except Exception as e:
        print(f"證交所 API 整體失敗: {e}")
        return None


def get_stock_from_alternative_api(stock_code):
    """從其他金融 API 獲取資料"""
    try:
        # 嘗試 Fugle API (免費版)
        url = f"https://api.fugle.tw/realtime/v0.3/intraday/quote?symbolId={stock_code}"
        
        resp = requests.get(url, timeout=CONFIG['timeout'], headers=HEADERS)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data'):
                quote = data['data']
                stock_info = {
                    '股票代碼': stock_code,
                    '股票名稱': get_stock_name(stock_code),
                    '收盤價': f"{quote.get('price', 0):.2f}",
                    '開盤價': f"{quote.get('open', 0):.2f}",
                    '最高價': f"{quote.get('high', 0):.2f}",
                    '最低價': f"{quote.get('low', 0):.2f}",
                    '成交量': f"{quote.get('volume', 0):,}",
                    '漲跌價差': f"{quote.get('change', 0):+.2f}",
                    '漲跌幅': f"{quote.get('changePercent', 0):+.2f}%",
                }
                print(f"✅ 替代 API 成功獲取 {stock_code} 資料")
                return stock_info
                
    except Exception as e:
        print(f"替代 API 獲取失敗: {e}")
        
    return None


def get_stock_from_twse_realtime(stock_code):
    """從證交所即時報價獲取資料"""
    try:
        # 證交所即時報價 API
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_code}.tw"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://mis.twse.com.tw/',
            'Accept': 'application/json'
        }
        
        resp = requests.get(url, timeout=CONFIG['timeout'], headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('msgArray') and len(data['msgArray']) > 0:
            stock_data = data['msgArray'][0]
            
            # 獲取各項資料
            current_price = stock_data.get('z', '0')    # 目前價格
            open_price = stock_data.get('o', '0')       # 開盤價
            high_price = stock_data.get('h', '0')       # 最高價
            low_price = stock_data.get('l', '0')        # 最低價
            volume = stock_data.get('v', '0')           # 成交量
            name = stock_data.get('n', '')              # 股票名稱
            prev_close = stock_data.get('y', '0')       # 昨日收盤價
            
            stock_info = {
                '股票代碼': stock_code,
                '股票名稱': name if name else get_stock_name(stock_code),
                '即時股價': current_price if current_price != '0' else "N/A",
                '收盤價': current_price if current_price != '0' else "N/A",  # 即時股價也是收盤價
                '開盤價': open_price if open_price != '0' else "N/A",
                '最高價': high_price if high_price != '0' else "N/A",
                '最低價': low_price if low_price != '0' else "N/A",
                '成交量': f"{int(volume):,}" if volume and volume != '0' else "N/A",
            }
            
            # 計算漲跌資料
            try:
                if prev_close and prev_close != '0' and current_price and current_price != '0':
                    prev_val = float(prev_close)
                    curr_val = float(current_price)
                    
                    # 計算漲跌價差
                    change_val = curr_val - prev_val
                    stock_info['漲跌價差'] = f"{change_val:+.2f}"
                    
                    # 計算漲跌幅
                    if prev_val > 0:
                        change_percent = (change_val / prev_val) * 100
                        stock_info['漲跌幅'] = f"{change_percent:+.2f}%"
                    else:
                        stock_info['漲跌幅'] = "N/A"
                else:
                    stock_info['漲跌價差'] = "N/A"
                    stock_info['漲跌幅'] = "N/A"
                    
            except Exception as e:
                print(f"⚠️ 漲跌計算錯誤: {e}")
                stock_info['漲跌價差'] = "N/A"
                stock_info['漲跌幅'] = "N/A"
            
            print(f"✅ 證交所即時報價成功獲取 {stock_code} 資料")
            return stock_info
        else:
            print(f"❌ 證交所即時報價無資料: {stock_code}")
            return None
            
    except Exception as e:
        print(f"證交所即時報價獲取失敗: {e}")
        return None


def get_market_from_twse():
    """從證交所獲取大盤即時資訊"""
    try:
        # 證交所大盤即時資訊 - 使用寶島股價指數
        url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_FRMSA.tw|otc_FRMSA.tw"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://mis.twse.com.tw/',
            'Accept': 'application/json'
        }
        
        resp = requests.get(url, timeout=CONFIG['timeout'], headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('msgArray') and len(data['msgArray']) > 0:
            # 第一個是寶島股價指數
            market_data = data['msgArray'][0]
            
            current_index = market_data.get('z', '0')   # 目前指數
            prev_close = market_data.get('y', '0')      # 昨收指數
            name = market_data.get('n', '')             # 指數名稱
            
            try:
                if current_index and current_index not in ['0', '-'] and prev_close and prev_close not in ['0', '-']:
                    curr_val = float(current_index)
                    prev_val = float(prev_close)
                    
                    # 計算漲跌點數
                    change_val = curr_val - prev_val
                    
                    # 計算漲跌幅
                    change_percent = (change_val / prev_val) * 100 if prev_val > 0 else 0
                    
                    market_info = {
                        '指數': f"{curr_val:,.2f}",
                        '漲跌點數': f"{change_val:+.2f}",
                        '漲跌幅': f"{change_percent:+.2f}%",
                        '成交量': "N/A",  # 大盤通常不提供成交量
                        '更新時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        '指數名稱': name if name else "台股指數"
                    }
                    
                    print("✅ 證交所成功獲取大盤資料")
                    return market_info
                else:
                    print("❌ 證交所大盤指數資料無效")
                    return None
                    
            except ValueError as e:
                print(f"❌ 證交所大盤資料轉換錯誤: {e}")
                return None
        else:
            print("❌ 證交所大盤無資料")
            return None
            
    except Exception as e:
        print(f"證交所大盤獲取失敗: {e}")
        return None


def get_stock_basic_info(stock_code):
    """
    獲取個股基本資訊 - 多重資料來源
    :param stock_code: 股票代碼（支援任意長度）
    :return: dict 包含股票基本資訊
    """
    # 清理股票代碼，移除空格和非數字字符（保留字母）
    clean_code = re.sub(r'[^\w]', '', stock_code.strip())
    
    # 檢查快取
    cache_key = f"stock_basic_{clean_code}"
    cached_data = get_cache(cache_key)
    if cached_data:
        print(f"🔄 使用快取資料: {clean_code}")
        return cached_data
    
    print(f"🔍 開始獲取股票 {clean_code} 的即時資料...")
    
    # 多重資料來源策略 - 優先使用證交所
    data_sources = [
        ("證交所即時報價", lambda: get_stock_from_twse_realtime(clean_code)),
        ("Yahoo Finance", lambda: get_stock_from_yahoo(clean_code)),
        ("證交所 API", lambda: get_stock_from_twse_api(clean_code)),
        ("替代 API", lambda: get_stock_from_alternative_api(clean_code)),
    ]
    
    for source_name, get_data_func in data_sources:
        try:
            print(f"📡 嘗試 {source_name}...")
            stock_data = get_data_func()
            
            if stock_data and not stock_data.get('錯誤'):
                # 檢查是否有有效的股價資料
                realtime_price = stock_data.get('即時股價', 'N/A')
                close_price = stock_data.get('收盤價', 'N/A')
                
                # 如果股價資料有效（不是 "-", "N/A", "0" 或空值）
                if (realtime_price not in ['-', 'N/A', '0', '', None] or 
                    close_price not in ['-', 'N/A', '0', '', None]):
                    # 儲存快取
                    save_cache(cache_key, stock_data)
                    print(f"✅ 成功從 {source_name} 獲取資料並快取")
                    return stock_data
                else:
                    print(f"⚠️ {source_name} 回傳資料但股價無效: 即時股價={realtime_price}, 收盤價={close_price}")
            else:
                print(f"❌ {source_name} 資料不完整或有錯誤")
                
        except Exception as e:
            print(f"❌ {source_name} 發生異常: {e}")
            continue
    
    # 所有資料來源都失敗
    error_result = {
        '股票代碼': clean_code,
        '股票名稱': get_stock_name(clean_code),
        '錯誤': f'無法從任何資料來源獲取股票 {clean_code} 的資料'
    }
    print(f"❌ 所有資料來源都失敗: {clean_code}")
    return error_result


def get_stock_name_from_api(stock_code):
    """從 API 動態獲取股票名稱"""
    try:
        # 嘗試從證交所即時報價 API 獲取名稱
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_code}.tw"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://mis.twse.com.tw/',
            'Accept': 'application/json'
        }
        
        resp = requests.get(url, timeout=5, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('msgArray') and len(data['msgArray']) > 0:
                stock_data = data['msgArray'][0]
                name = stock_data.get('n', '').strip()
                if name:
                    return name
        
        # 嘗試從 Yahoo Finance 獲取名稱
        yahoo_symbol = f"{stock_code}.TW"
        yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        
        resp = requests.get(yahoo_url, timeout=5, headers=HEADERS)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('chart') and data['chart'].get('result'):
                result = data['chart']['result'][0]
                meta = result.get('meta', {})
                
                # 嘗試不同的名稱欄位
                name = (meta.get('longName') or 
                       meta.get('shortName') or 
                       meta.get('displayName'))
                
                if name:
                    # 清理名稱，移除多餘字符
                    name = name.replace('Taiwan Semiconductor Manufacturing Company Limited', '台積電')
                    name = name.replace('TAIWAN SEMICONDUCTOR MANUFACTUR', '台積電')
                    return name
        
    except Exception as e:
        print(f"⚠️ 無法從 API 獲取股票名稱 {stock_code}: {e}")
    
    return None


def get_stock_name(stock_code):
    """取得股票名稱 - 先嘗試 API，失敗則使用預設名稱"""
    # 先嘗試從 API 動態獲取
    api_name = get_stock_name_from_api(stock_code)
    if api_name:
        return api_name
    
    # 備用：常見股票的預設名稱（只保留最常見的）
    common_stocks = {
        '2330': '台積電',
        '2317': '鴻海', 
        '2454': '聯發科',
        '0050': '元大台灣50',
        '0056': '元大高股息',
        '006208': '富邦台50',
        '00878': '國泰永續高股息',
        '00919': '群益台灣精選高息',
    }
    
    return common_stocks.get(stock_code, stock_code)


def get_market_summary():
    """獲取大盤摘要資訊 - 改進版"""
    cache_key = "market_summary"
    cached_data = get_cache(cache_key)
    if cached_data:
        print("🔄 使用大盤快取資料")
        return cached_data
    
    print("📊 獲取大盤即時資料...")
    
    # 嘗試多個資料來源 - 優先使用證交所
    data_sources = [
        # 證交所官方即時資料
        ("證交所即時資料", get_market_from_twse),
        # Yahoo Finance - 台股指數
        ("Yahoo Finance TWII", lambda: get_market_from_yahoo("https://query1.finance.yahoo.com/v8/finance/chart/%5ETWII")),
        # Yahoo Finance - 台灣加權指數
        ("Yahoo Finance TSE", lambda: get_market_from_yahoo("https://query1.finance.yahoo.com/v8/finance/chart/^TWSE")),
        # 備用資料來源
        ("Yahoo Finance Alternative", lambda: get_market_from_yahoo("https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5ETWII")),
    ]
    
    for source_name, get_data_func in data_sources:
        try:
            print(f"📡 嘗試 {source_name}...")
            market_info = get_data_func()
            
            if market_info and not market_info.get('錯誤'):
                save_cache(cache_key, market_info)
                print(f"✅ 成功從 {source_name} 獲取大盤資料")
                return market_info
            else:
                print(f"❌ {source_name} 回應格式不正確")
                
        except Exception as e:
            print(f"❌ {source_name} 獲取失敗: {e}")
            continue
    
    # 所有資料來源都失敗，回傳模擬資料
    print("⚠️ 所有大盤資料來源都失敗，使用模擬資料")
    return {
        '指數': '18,500.00',
        '漲跌點數': '+125.50',
        '漲跌幅': '+0.68%',
        '成交量': '2,156,789,000',
        '更新時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '狀態': '模擬資料'
    }


def get_market_from_yahoo(url):
    """從 Yahoo Finance 獲取大盤資料的輔助函數"""
    try:
        resp = requests.get(url, timeout=CONFIG['timeout'], headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        
        market_info = None
        
        if 'chart' in data and data['chart'].get('result'):
            # Chart API 格式
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            
            current_price = meta.get('regularMarketPrice')
            previous_close = meta.get('regularMarketPreviousClose')
            volume = meta.get('regularMarketVolume', 0)
            
            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                
                market_info = {
                    '指數': f"{current_price:,.2f}",
                    '漲跌點數': f"{change:+.2f}",
                    '漲跌幅': f"{change_percent:+.2f}%",
                    '成交量': f"{volume:,}" if volume else "N/A",
                    '更新時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        elif 'quoteResponse' in data and data['quoteResponse'].get('result'):
            # Quote API 格式
            result = data['quoteResponse']['result'][0]
            
            current_price = result.get('regularMarketPrice')
            change = result.get('regularMarketChange')
            change_percent = result.get('regularMarketChangePercent')
            volume = result.get('regularMarketVolume', 0)
            
            if current_price:
                market_info = {
                    '指數': f"{current_price:,.2f}",
                    '漲跌點數': f"{change:+.2f}" if change else "N/A",
                    '漲跌幅': f"{change_percent:+.2f}%" if change_percent else "N/A",
                    '成交量': f"{volume:,}" if volume else "N/A",
                    '更新時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return market_info
        
    except Exception as e:
        print(f"Yahoo Finance 錯誤: {e}")
        return None


def get_cache(key):
    """獲取快取資料"""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 檢查快取是否過期
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time < timedelta(seconds=CONFIG['cache_duration']):
                return cache_data['data']
        except Exception as e:
            print(f"❌ 讀取快取失敗: {e}")
    return None


def save_cache(key, data):
    """儲存快取資料"""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 儲存快取失敗: {e}")


def search_stock(stock_code):
    """
    主要功能：搜尋單一股票的即時資料
    :param stock_code: 股票代碼（支援任意長度）
    :return: 股票資訊字典
    """
    # 清理股票代碼
    clean_code = stock_code.replace('.TW', '').replace('.tw', '').strip()
    
    print(f"\n🔍 === 搜尋股票：{clean_code} ===")
    stock_info = get_stock_basic_info(clean_code)
    
    if stock_info and not stock_info.get('錯誤'):
        print(f"\n✅ 找到股票：{stock_info.get('股票名稱', 'N/A')} ({clean_code})")
        print(f"💰 收盤價：{stock_info.get('收盤價', 'N/A')}")
        print(f"🔓 開盤價：{stock_info.get('開盤價', 'N/A')}")
        print(f"📈 漲跌：{stock_info.get('漲跌價差', 'N/A')} ({stock_info.get('漲跌幅', 'N/A')})")
        print(f"📊 成交量：{stock_info.get('成交量', 'N/A')}")
        if stock_info.get('成交金額'):
            print(f"💸 成交金額：{stock_info.get('成交金額', 'N/A')}")
        return stock_info
    else:
        error_msg = stock_info.get('錯誤', '未知錯誤') if stock_info else '無法找到股票'
        print(f"❌ {error_msg}")
        return None


def show_popular_stocks():
    """顯示熱門股票列表 - 包含 6 位數股票"""
    popular = ['2330', '0050', '0056', '00878', '00919', '006208', '2317', '2454']
    print("\n🔥 熱門股票：")
    for code in popular:
        name = get_stock_name(code)
        print(f"  {code} - {name}")


if __name__ == '__main__':
    print("🚀 === 台股即時查詢系統 === 🚀")
    print("📡 支援多重資料來源，獲取最新股價資訊")
    print("📋 支援任意長度股票代碼（4-6位數）")
    print("\n📋 指令說明：")
    print("  • 輸入股票代碼查詢即時資料（如：2330, 0050, 006208）")
    print("  • 'market' - 查看大盤即時資訊")
    print("  • 'popular' - 熱門股票列表") 
    print("  • 'quit' - 結束程式")
    
    while True:
        try:
            user_input = input("\n🔍 請輸入股票代碼: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 再見！")
                break
            elif user_input.lower() == 'market':
                market_info = get_market_summary()
                print(f"\n📊 大盤即時資訊：")
                for key, value in market_info.items():
                    if key not in ['錯誤', '狀態']:
                        print(f"  {key}：{value}")
                if market_info.get('錯誤'):
                    print(f"  ⚠️  {market_info['錯誤']}")
                if market_info.get('狀態'):
                    print(f"  ℹ️  {market_info['狀態']}")
            elif user_input.lower() == 'popular':
                show_popular_stocks()
            elif user_input:
                search_stock(user_input)
            else:
                print("❓ 請輸入有效的股票代碼")
                
        except KeyboardInterrupt:
            print("\n\n👋 程式已中斷，再見！")
            break
        except Exception as e:
            print(f"❌ 發生錯誤：{e}") 
