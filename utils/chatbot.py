#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單股票聊天機器人
"""

import re
from datetime import datetime
from .twse import get_stock_basic_info, get_market_summary, get_stock_name

class StockChatbot:
    """股票聊天機器人"""
    
    def __init__(self):
        # 股票代碼映射表
        self.stock_mapping = {
            '台積電': '2330',
            '鴻海': '2317',
            '聯發科': '2454',
            '台塑': '1301',
            '中華電': '2412',
            '富邦金': '2881',
            '國泰金': '2882',
            '台達電': '2308',
            '廣達': '2382',
            '元大台灣50': '0050',
            '元大高股息': '0056',
            '國泰永續高股息': '00878',
            '群益台灣精選高息': '00919',
            '富邦台50': '006208',
        }
        
        # 問候語回應
        self.greetings = [
            "您好！我是股票助手，可以幫您查詢股票資訊。",
            "歡迎使用股票查詢服務！請問有什麼可以幫您的嗎？",
            "Hi！我可以幫您查詢台股資訊，請告訴我您想了解的股票。"
        ]
        
        # 查詢類型的關鍵字
        self.query_keywords = {
            'price': ['收盤價', '股價', '價格', '多少錢', '多少', '現價'],
            'change': ['漲跌', '漲幅', '跌幅', '變化'],
            'volume': ['成交量', '交易量', '成交額'],
            'basic': ['資訊', '資料', '基本資料', '詳細'],
            'market': ['大盤', '加權指數', '台股', '市場']
        }
    
    def process_message(self, message):
        """處理用戶訊息"""
        try:
            message = message.strip()
            
            # 問候語檢測
            if self.is_greeting(message):
                return self.get_greeting_response()
            
            # 大盤查詢
            if self.is_market_query(message):
                return self.get_market_response()
            
            # 股票查詢
            stock_code, query_type = self.parse_stock_query(message)
            if stock_code:
                return self.get_stock_response(stock_code, query_type, message)
            
            # 無法識別的問題
            return self.get_help_response()
            
        except Exception as e:
            return f"抱歉，處理您的問題時發生錯誤：{str(e)}"
    
    def is_greeting(self, message):
        """檢測是否為問候語"""
        greetings = ['你好', '您好', 'hi', 'hello', '哈囉', '嗨', '早安', '午安', '晚安']
        return any(greeting in message.lower() for greeting in greetings)
    
    def is_market_query(self, message):
        """檢測是否為大盤查詢"""
        market_keywords = ['大盤', '加權指數', '台股指數', '市場', '整體']
        return any(keyword in message for keyword in market_keywords)
    
    def parse_stock_query(self, message):
        """解析股票查詢"""
        # 檢查是否包含股票代碼（數字）
        stock_code = None
        query_type = 'basic'
        
        # 先檢查股票名稱
        for stock_name, code in self.stock_mapping.items():
            if stock_name in message:
                stock_code = code
                break
        
        # 如果沒找到股票名稱，檢查數字代碼
        if not stock_code:
            code_match = re.search(r'\b(\d{4,6})\b', message)
            if code_match:
                stock_code = code_match.group(1)
        
        # 確定查詢類型
        if stock_code:
            for qtype, keywords in self.query_keywords.items():
                if any(keyword in message for keyword in keywords):
                    query_type = qtype
                    break
        
        return stock_code, query_type
    
    def get_greeting_response(self):
        """獲取問候回應"""
        import random
        return random.choice(self.greetings)
    
    def get_market_response(self):
        """獲取大盤資訊回應"""
        try:
            market_info = get_market_summary()
            
            if market_info and not market_info.get('錯誤'):
                response = "📊 大盤資訊：\n"
                response += f"• 加權指數：{market_info.get('指數', 'N/A')}\n"
                response += f"• 漲跌：{market_info.get('漲跌點數', 'N/A')}\n"
                response += f"• 漲跌幅：{market_info.get('漲跌幅', 'N/A')}\n"
                response += f"• 成交量：{market_info.get('成交量', 'N/A')}\n"
                response += f"• 更新時間：{market_info.get('更新時間', 'N/A')}"
                return response
            else:
                return "抱歉，目前無法獲取大盤資訊，請稍後再試。"
                
        except Exception as e:
            return f"獲取大盤資訊時發生錯誤：{str(e)}"
    
    def get_stock_response(self, stock_code, query_type, original_message):
        """獲取股票資訊回應"""
        try:
            stock_info = get_stock_basic_info(stock_code)
            
            if not stock_info or stock_info.get('錯誤'):
                return f"抱歉，無法找到股票代碼 {stock_code} 的資訊。請確認代碼是否正確。"
            
            stock_name = stock_info.get('股票名稱', stock_code)
            
            # 根據查詢類型回應
            if query_type == 'price':
                price = stock_info.get('收盤價', 'N/A')
                change = stock_info.get('漲跌價差', 'N/A')
                change_percent = stock_info.get('漲跌幅', 'N/A')
                
                response = f"📈 {stock_name} ({stock_code}) 價格資訊：\n"
                response += f"• 收盤價：{price}\n"
                response += f"• 漲跌：{change}\n"
                response += f"• 漲跌幅：{change_percent}"
                
            elif query_type == 'change':
                change = stock_info.get('漲跌價差', 'N/A')
                change_percent = stock_info.get('漲跌幅', 'N/A')
                
                response = f"📊 {stock_name} ({stock_code}) 漲跌資訊：\n"
                response += f"• 漲跌：{change}\n"
                response += f"• 漲跌幅：{change_percent}"
                
            elif query_type == 'volume':
                volume = stock_info.get('成交量', stock_info.get('成交股數', 'N/A'))
                amount = stock_info.get('成交金額', 'N/A')
                
                response = f"💰 {stock_name} ({stock_code}) 成交資訊：\n"
                response += f"• 成交量：{volume}\n"
                response += f"• 成交金額：{amount}"
                
            else:  # basic info
                response = f"📋 {stock_name} ({stock_code}) 基本資訊：\n"
                response += f"• 收盤價：{stock_info.get('收盤價', 'N/A')}\n"
                response += f"• 漲跌：{stock_info.get('漲跌價差', 'N/A')}\n"
                response += f"• 漲跌幅：{stock_info.get('漲跌幅', 'N/A')}\n"
                response += f"• 開盤價：{stock_info.get('開盤價', 'N/A')}\n"
                response += f"• 最高價：{stock_info.get('最高價', 'N/A')}\n"
                response += f"• 最低價：{stock_info.get('最低價', 'N/A')}\n"
                response += f"• 成交量：{stock_info.get('成交量', 'N/A')}"
            
            return response
            
        except Exception as e:
            return f"查詢股票資訊時發生錯誤：{str(e)}"
    
    def get_help_response(self):
        """獲取幫助回應"""
        return """🤖 我可以幫您查詢以下資訊：

📊 **大盤查詢**
• "大盤怎麼樣？"
• "加權指數多少？"

📈 **股票查詢**
• "台積電今天收盤多少？"
• "2330股價多少？"
• "鴻海漲跌幅如何？"
• "0050成交量多少？"

💡 **支援的股票**
台積電、鴻海、聯發科、台塑、中華電、富邦金、國泰金、台達電、廣達、元大台灣50、元大高股息等

您也可以直接輸入4-6位數的股票代碼進行查詢。"""

# 全域聊天機器人實例
chatbot = StockChatbot()

def process_chat_message(message):
    """處理聊天訊息的主要函數"""
    return chatbot.process_message(message) 