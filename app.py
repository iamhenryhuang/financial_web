from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, AnonymousUserMixin
from datetime import datetime
from utils.twse import get_stock_basic_info, get_market_summary, get_stock_name
from utils.chatbot import process_chat_message

from models import db, User, Watchlist, SearchHistory, PriceAlert
from forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm, WatchlistForm, PriceAlertForm
import os
import secrets

app = Flask(__name__)

# 全域配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///stock_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化擴展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '請先登入以訪問此頁面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

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
            # 記錄搜尋歷史
            try:
                search_history = SearchHistory(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    stock_code=stock_code,
                    stock_name=stock_info.get('股票名稱'),
                    search_price=stock_info.get('即時股價', stock_info.get('收盤價')),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:500]
                )
                db.session.add(search_history)
                db.session.commit()
            except:
                # 記錄失敗不影響主要功能
                pass
            
            # 檢查是否在自選股中
            in_watchlist = False
            if current_user.is_authenticated:
                in_watchlist = db.session.query(Watchlist).filter_by(
                    user_id=current_user.id, 
                    stock_code=stock_code
                ).first() is not None
            
            return render_template('stock.html',
                                 stock_code=stock_code,
                                 stock_info=stock_info,
                                 error=None,
                                 in_watchlist=in_watchlist,
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


# === 會員系統路由 ===

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登入頁面"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'歡迎回來，{user.username}！', 'success')
            
            # 重導向到原本要訪問的頁面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('用戶名或密碼錯誤', 'danger')
    
    return render_template('auth/login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """註冊頁面"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('註冊成功！請登入您的帳戶', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """登出"""
    username = current_user.username
    logout_user()
    flash(f'{username}，您已成功登出', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """會員控制台"""
    # 獲取用戶自選股
    watchlist = db.session.query(Watchlist).filter_by(user_id=current_user.id).order_by(Watchlist.created_at.desc()).all()
    
    # 獲取最近搜尋記錄
    recent_searches = db.session.query(SearchHistory).filter_by(user_id=current_user.id).order_by(SearchHistory.created_at.desc()).limit(10).all()
    
    # 獲取會員功能
    features = current_user.get_membership_features()
    
    return render_template('member/dashboard.html', 
                         watchlist=watchlist,
                         recent_searches=recent_searches,
                         features=features,
                         current_time=datetime.now())


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """個人資料"""
    form = ProfileForm(current_user.email)
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.email = form.email.data
        db.session.commit()
        flash('個人資料已更新', 'success')
        return redirect(url_for('profile'))
    
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        form.email.data = current_user.email
    
    return render_template('member/profile.html', form=form)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密碼"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('密碼已成功修改', 'success')
            return redirect(url_for('profile'))
        else:
            flash('目前密碼不正確', 'danger')
    
    return render_template('member/change_password.html', form=form)


@app.route('/watchlist')
@login_required
def watchlist():
    """自選股列表"""
    watchlist_items = db.session.query(Watchlist).filter_by(user_id=current_user.id).order_by(Watchlist.created_at.desc()).all()
    
    # 獲取即時股價
    for item in watchlist_items:
        try:
            stock_info = get_stock_basic_info(item.stock_code)
            if stock_info and not stock_info.get('錯誤'):
                item.current_price = stock_info.get('即時股價', stock_info.get('收盤價'))
                item.change = stock_info.get('漲跌價差')
                item.change_percent = stock_info.get('漲跌幅')
        except:
            item.current_price = 'N/A'
            item.change = 'N/A'
            item.change_percent = 'N/A'
    
    features = current_user.get_membership_features()
    return render_template('member/watchlist.html', 
                         watchlist=watchlist_items,
                         features=features,
                         current_time=datetime.now())


@app.route('/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    """加入自選股"""
    stock_code = request.form.get('stock_code', '').strip().upper()
    notes = request.form.get('notes', '').strip()
    
    if not stock_code:
        flash('請輸入股票代號', 'warning')
        return redirect(url_for('watchlist'))
    
    # 檢查會員限制
    features = current_user.get_membership_features()
    if features.get('watchlist_limit'):
        current_count = db.session.query(Watchlist).filter_by(user_id=current_user.id).count()
        if current_count >= features['watchlist_limit']:
            flash(f'您的會員等級最多只能添加 {features["watchlist_limit"]} 支自選股', 'warning')
            return redirect(url_for('watchlist'))
    
    # 檢查是否已存在
    existing = db.session.query(Watchlist).filter_by(user_id=current_user.id, stock_code=stock_code).first()
    if existing:
        flash('此股票已在您的自選股中', 'info')
        return redirect(url_for('watchlist'))
    
    # 獲取股票資訊
    stock_info = get_stock_basic_info(stock_code)
    if not stock_info or stock_info.get('錯誤'):
        flash('無法找到此股票代號', 'danger')
        return redirect(url_for('watchlist'))
    
    # 加入自選股
    watchlist_item = Watchlist(
        user_id=current_user.id,
        stock_code=stock_code,
        stock_name=stock_info.get('股票名稱'),
        added_price=stock_info.get('即時股價', stock_info.get('收盤價')),
        notes=notes
    )
    
    db.session.add(watchlist_item)
    db.session.commit()
    
    flash(f'已將 {stock_code} {stock_info.get("股票名稱", "")} 加入自選股', 'success')
    return redirect(url_for('watchlist'))


@app.route('/watchlist/remove/<int:item_id>')
@login_required
def remove_from_watchlist(item_id):
    """移除自選股"""
    item = db.session.query(Watchlist).filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        stock_name = f"{item.stock_code} {item.stock_name or ''}"
        db.session.delete(item)
        db.session.commit()
        flash(f'已移除自選股：{stock_name}', 'success')
    else:
        flash('找不到此自選股項目', 'warning')
    
    return redirect(url_for('watchlist'))


# === 聊天機器人功能 ===

@app.route('/chatbot')
def chatbot_page():
    """聊天機器人頁面"""
    return render_template('chatbot.html', current_time=datetime.now())


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API: 聊天機器人對話"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': '請提供訊息內容',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                'success': False,
                'error': '訊息不能為空',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # 處理聊天訊息
        bot_response = process_chat_message(user_message)
        
        return jsonify({
            'success': True,
            'data': {
                'user_message': user_message,
                'bot_response': bot_response,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


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
    # 確保資料夾存在
    os.makedirs('static', exist_ok=True)
    
    print("🚀 台股財經網站啟動中...")
    print("📊 支援即時股價查詢")
    print("👤 會員系統已整合")
    print("🌐 網址: http://127.0.0.1:5000")
    
    # 確保資料庫表存在
    with app.app_context():
        try:
            db.create_all()
            print("✅ 資料庫已初始化")
        except Exception as e:
            print(f"❌ 資料庫初始化錯誤: {e}")
    
    #app.run(debug=True, host='127.0.0.1', port=5000)
    app.run()
    
