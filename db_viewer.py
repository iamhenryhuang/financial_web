#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料庫查看工具
用於查看用戶註冊資料和會員系統狀態
"""

import sqlite3
import os
from datetime import datetime

def connect_db():
    """連接資料庫"""
    db_path = os.path.join('instance', 'stock_app.db')
    if not os.path.exists(db_path):
        print(f"❌ 資料庫檔案不存在: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 讓結果可以用欄位名稱存取
        return conn
    except Exception as e:
        print(f"❌ 連接資料庫失敗: {e}")
        return None

def show_tables():
    """顯示所有資料表"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📊 資料庫表格清單:")
        print("-" * 40)
        for table in tables:
            print(f"  • {table[0]}")
        print()
        
    except Exception as e:
        print(f"❌ 查詢表格失敗: {e}")
    finally:
        conn.close()

def show_users():
    """顯示用戶資料"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.execute("""
            SELECT id, username, email, full_name, phone, membership_level, 
                   is_active, created_at, last_login
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        
        print("👥 用戶列表:")
        print("-" * 80)
        if not users:
            print("  尚無註冊用戶")
        else:
            print(f"{'ID':<4} {'用戶名':<15} {'電子信箱':<25} {'真實姓名':<12} {'會員等級':<10} {'狀態':<6} {'註冊時間'}")
            print("-" * 80)
            for user in users:
                status = "✅啟用" if user['is_active'] else "❌停用"
                created = datetime.fromisoformat(user['created_at']).strftime('%m-%d %H:%M') if user['created_at'] else 'N/A'
                print(f"{user['id']:<4} {user['username']:<15} {user['email']:<25} {user['full_name'] or 'N/A':<12} {user['membership_level']:<10} {status:<6} {created}")
        print()
        
    except Exception as e:
        print(f"❌ 查詢用戶失敗: {e}")
    finally:
        conn.close()

def show_watchlists():
    """顯示自選股資料"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.execute("""
            SELECT w.id, u.username, w.stock_code, w.stock_name, 
                   w.added_price, w.notes, w.created_at
            FROM watchlists w
            JOIN users u ON w.user_id = u.id
            ORDER BY w.created_at DESC
            LIMIT 20
        """)
        watchlists = cursor.fetchall()
        
        print("⭐ 自選股列表 (最近20筆):")
        print("-" * 70)
        if not watchlists:
            print("  尚無自選股資料")
        else:
            print(f"{'ID':<4} {'用戶':<12} {'代號':<8} {'名稱':<15} {'加入價格':<10} {'時間'}")
            print("-" * 70)
            for item in watchlists:
                created = datetime.fromisoformat(item['created_at']).strftime('%m-%d %H:%M') if item['created_at'] else 'N/A'
                price = f"{item['added_price']:.2f}" if item['added_price'] else 'N/A'
                print(f"{item['id']:<4} {item['username']:<12} {item['stock_code']:<8} {item['stock_name'] or 'N/A':<15} {price:<10} {created}")
        print()
        
    except Exception as e:
        print(f"❌ 查詢自選股失敗: {e}")
    finally:
        conn.close()

def show_search_history():
    """顯示搜尋歷史"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        cursor = conn.execute("""
            SELECT s.id, u.username, s.stock_code, s.stock_name, 
                   s.search_price, s.ip_address, s.created_at
            FROM search_history s
            LEFT JOIN users u ON s.user_id = u.id
            ORDER BY s.created_at DESC
            LIMIT 15
        """)
        searches = cursor.fetchall()
        
        print("🔍 搜尋歷史 (最近15筆):")
        print("-" * 75)
        if not searches:
            print("  尚無搜尋記錄")
        else:
            print(f"{'ID':<4} {'用戶':<12} {'代號':<8} {'名稱':<15} {'搜尋價格':<10} {'IP':<15} {'時間'}")
            print("-" * 75)
            for search in searches:
                created = datetime.fromisoformat(search['created_at']).strftime('%m-%d %H:%M') if search['created_at'] else 'N/A'
                price = f"{search['search_price']:.2f}" if search['search_price'] else 'N/A'
                username = search['username'] or '匿名'
                ip = search['ip_address'] or 'N/A'
                print(f"{search['id']:<4} {username:<12} {search['stock_code']:<8} {search['stock_name'] or 'N/A':<15} {price:<10} {ip:<15} {created}")
        print()
        
    except Exception as e:
        print(f"❌ 查詢搜尋歷史失敗: {e}")
    finally:
        conn.close()

def show_user_details(username):
    """顯示特定用戶的詳細資訊"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        # 查詢用戶基本資料
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ 找不到用戶: {username}")
            return
        
        print(f"👤 用戶詳細資料: {username}")
        print("-" * 50)
        print(f"ID: {user['id']}")
        print(f"用戶名: {user['username']}")
        print(f"電子信箱: {user['email']}")
        print(f"真實姓名: {user['full_name'] or 'N/A'}")
        print(f"電話: {user['phone'] or 'N/A'}")
        print(f"會員等級: {user['membership_level']}")
        print(f"狀態: {'啟用' if user['is_active'] else '停用'}")
        print(f"註冊時間: {user['created_at']}")
        print(f"最後登入: {user['last_login'] or '尚未登入'}")
        
        # 查詢自選股數量
        cursor = conn.execute("SELECT COUNT(*) as count FROM watchlists WHERE user_id = ?", (user['id'],))
        watchlist_count = cursor.fetchone()['count']
        
        # 查詢搜尋次數
        cursor = conn.execute("SELECT COUNT(*) as count FROM search_history WHERE user_id = ?", (user['id'],))
        search_count = cursor.fetchone()['count']
        
        print(f"自選股數量: {watchlist_count}")
        print(f"搜尋次數: {search_count}")
        print()
        
    except Exception as e:
        print(f"❌ 查詢用戶詳情失敗: {e}")
    finally:
        conn.close()

def main():
    """主程式"""
    print("🗄️  台股財經網站 - 資料庫查看工具")
    print("=" * 50)
    
    while True:
        print("\n選擇操作：")
        print("1. 顯示所有資料表")
        print("2. 顯示用戶列表")
        print("3. 顯示自選股")
        print("4. 顯示搜尋歷史")
        print("5. 查看特定用戶詳情")
        print("0. 離開")
        
        choice = input("\n請輸入選項 (0-5): ").strip()
        
        if choice == '0':
            print("👋 再見！")
            break
        elif choice == '1':
            show_tables()
        elif choice == '2':
            show_users()
        elif choice == '3':
            show_watchlists()
        elif choice == '4':
            show_search_history()
        elif choice == '5':
            username = input("請輸入用戶名: ").strip()
            if username:
                show_user_details(username)
            else:
                print("❌ 請輸入有效的用戶名")
        else:
            print("❌ 無效的選項，請重新選擇")

if __name__ == "__main__":
    main() 