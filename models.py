from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """用戶模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # 用戶資料
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # 會員等級 (free, premium, vip)
    membership_level = db.Column(db.String(20), default='free', nullable=False)
    
    # 時間戳記
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # 是否啟用
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # 關聯
    watchlists = db.relationship('Watchlist', backref='user', lazy=True, cascade='all, delete-orphan')
    search_history = db.relationship('SearchHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """設置密碼"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """檢查密碼"""
        return check_password_hash(self.password_hash, password)
    
    def is_premium(self):
        """檢查是否為付費會員"""
        return self.membership_level in ['premium', 'vip']
    
    def is_vip(self):
        """檢查是否為 VIP 會員"""
        return self.membership_level == 'vip'
    
    def get_membership_features(self):
        """取得會員功能"""
        features = {
            'basic_search': True,
            'daily_limit': 50 if self.membership_level == 'free' else None,
            'watchlist_limit': 10 if self.membership_level == 'free' else None,
            'history_days': 7 if self.membership_level == 'free' else None,
        }
        
        if self.is_premium():
            features.update({
                'advanced_analysis': True,
                'export_data': True,
                'price_alerts': True,
                'daily_limit': 500,
                'watchlist_limit': 100,
                'history_days': 365,
            })
        
        if self.is_vip():
            features.update({
                'api_access': True,
                'priority_support': True,
                'custom_indicators': True,
                'daily_limit': None,
                'watchlist_limit': None,
                'history_days': None,
            })
        
        return features
    
    def __repr__(self):
        return f'<User {self.username}>'


class Watchlist(db.Model):
    """自選股模型"""
    __tablename__ = 'watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(100))
    
    # 加入時的價格
    added_price = db.Column(db.Float)
    
    # 備註
    notes = db.Column(db.Text)
    
    # 時間戳記
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 複合索引
    __table_args__ = (
        db.Index('idx_user_stock', 'user_id', 'stock_code'),
        db.UniqueConstraint('user_id', 'stock_code', name='unique_user_stock'),
    )
    
    def __repr__(self):
        return f'<Watchlist {self.user_id}:{self.stock_code}>'


class SearchHistory(db.Model):
    """搜尋歷史模型"""
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 允許匿名搜尋
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(100))
    
    # 搜尋時的價格資訊
    search_price = db.Column(db.Float)
    
    # IP 和 User Agent (用於匿名用戶分析)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # 時間戳記
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
        db.Index('idx_stock_created', 'stock_code', 'created_at'),
    )
    
    def __repr__(self):
        return f'<SearchHistory {self.user_id}:{self.stock_code}>'


class PriceAlert(db.Model):
    """價格提醒模型 (付費會員功能)"""
    __tablename__ = 'price_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_code = db.Column(db.String(10), nullable=False)
    stock_name = db.Column(db.String(100))
    
    # 提醒條件
    alert_type = db.Column(db.String(20), nullable=False)  # 'above', 'below', 'change_percent'
    target_price = db.Column(db.Float, nullable=False)
    
    # 狀態
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_triggered = db.Column(db.Boolean, default=False, nullable=False)
    triggered_at = db.Column(db.DateTime)
    
    # 備註
    notes = db.Column(db.Text)
    
    # 時間戳記
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = db.relationship('User', backref='price_alerts')
    
    # 索引
    __table_args__ = (
        db.Index('idx_user_active', 'user_id', 'is_active'),
        db.Index('idx_stock_active', 'stock_code', 'is_active'),
    )
    
    def __repr__(self):
        return f'<PriceAlert {self.user_id}:{self.stock_code}@{self.target_price}>' 