from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import redis

app = Flask(__name__)
# База данных аукциона: DATA_DIR для Docker (/app/data), иначе ./data от корня проекта
_data_dir = os.environ.get('DATA_DIR')
if not _data_dir:
    _data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(_data_dir, exist_ok=True)
_db_path = os.path.join(_data_dir, 'auction.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///' + _db_path.replace('\\', '/'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'auction-secret-key')

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

db = SQLAlchemy(app)
CORS(app)

# Модели данных аукциона
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' или 'seller'
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Bidder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    bids = db.relationship('Bid', backref='bidder', lazy=True)

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    auctions = db.relationship('Auction', backref='seller', lazy=True)

class Lot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    starting_price = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    auctions = db.relationship('Auction', backref='lot', lazy=True)

class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # completed, active, cancelled
    final_price = db.Column(db.String(50), nullable=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('lot.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    winner_bidder_id = db.Column(db.Integer, db.ForeignKey('bidder.id'), nullable=True)
    bids = db.relationship('Bid', backref='auction', lazy=True)
    winner = db.relationship('Bidder', foreign_keys=[winner_bidder_id])

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auction.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('bidder.id'), nullable=False)
    amount = db.Column(db.String(50), nullable=False)

# Декораторы для аутентификации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Доступ запрещён. Требуются права администратора.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def seller_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['admin', 'seller']:
            flash('Доступ запрещён.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Создание таблиц и пользователей по умолчанию (если их ещё нет)
with app.app_context():
    try:
        db.create_all()
        print("Database tables created (auction.db)")
        # Если в БД нет пользователей — создаём admin и seller (как в init_db.py)
        if User.query.count() == 0:
            for u in [
                {'username': 'admin', 'password_hash': generate_password_hash('admin123'), 'role': 'admin', 'name': 'Администратор антикварного аукциона', 'is_active': True},
                {'username': 'seller', 'password_hash': generate_password_hash('seller123'), 'role': 'seller', 'name': 'Иван Продавцов', 'is_active': True},
            ]:
                db.session.add(User(**u))
            db.session.commit()
            print("Созданы пользователи по умолчанию: admin / admin123, seller / seller123")
    except Exception as e:
        print(f"Database creation skipped: {e}")

# Маршруты аутентификации
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, is_active=True).first()

        if user and check_password_hash(user.password_hash, password):
            try:
                redis_client.incr('successful_logins')
            except Exception:
                pass
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = user.name
            flash(f'Добро пожаловать, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            try:
                redis_client.incr('failed_logins')
            except Exception:
                pass
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

# Главная страница (лендинг)
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    visit_count = redis_client.incr('page_visits')

    html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Антикварный аукцион — Торговая площадка</title>
        <style>
            body {{
                font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
                margin: 0;
                padding: 40px 20px;
                background:
                    radial-gradient(1000px 600px at 12% 8%, rgba(176, 141, 87, 0.12), transparent 60%),
                    radial-gradient(900px 600px at 90% 18%, rgba(47, 93, 80, 0.10), transparent 55%),
                    linear-gradient(165deg, #f6f1e7 0%, #efe4d3 48%, #eadcc8 100%);
                color: #1f1a14;
                min-height: 100vh;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                text-align: center;
            }}
            h1 {{
                font-size: 2.2em;
                font-weight: 750;
                margin-bottom: 10px;
                color: #5b1f2b;
            }}
            .counter {{
                background: linear-gradient(180deg, rgba(255, 250, 241, 0.96), rgba(247, 239, 223, 0.92));
                border: 1px solid #e2d3bf;
                padding: 32px;
                border-radius: 14px;
                margin: 24px 0;
                box-shadow: 0 18px 50px rgba(31, 26, 20, 0.14);
            }}
            .counter h2 {{
                color: #4a3a2b;
                font-size: 1.1em;
                font-weight: 500;
                margin-bottom: 8px;
            }}
            .counter .num {{
                font-size: 48px;
                font-weight: 700;
                color: #5b1f2b;
                margin: 16px 0;
            }}
            .login-btn {{
                display: inline-block;
                background: linear-gradient(180deg, rgba(47, 93, 80, 0.98), rgba(35, 72, 62, 0.98));
                color: #fffaf1;
                padding: 14px 28px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                margin-top: 20px;
                transition: background 0.2s;
            }}
            .login-btn:hover {{
                background: linear-gradient(180deg, rgba(55, 112, 96, 0.98), rgba(47, 93, 80, 0.98));
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔨 Приложение аукциона</h1>
            <p>Цифровой сервис для управления участниками, лотами и аукционами</p>
            <div class="counter">
                <h2>Счётчик посещений панели</h2>
                <p class="num">{visit_count}</p>
                <p style="color: #344054;">Главная страница панели управления аукционом</p>
            </div>
            <a href="/login" class="login-btn">Войти в систему</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

# API участников торгов (bidders)
@app.route('/api/bidders', methods=['GET', 'POST'])
@seller_or_admin_required
def bidders():
    if request.method == 'GET':
        bidders_list = Bidder.query.all()
        return jsonify([{
            'id': b.id,
            'name': b.name,
            'email': b.email,
            'phone': b.phone,
            'address': b.address or ''
        } for b in bidders_list])

    elif request.method == 'POST':
        data = request.json
        bidder = Bidder(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address')
        )
        db.session.add(bidder)
        db.session.commit()
        return jsonify({'message': 'Bidder added successfully'})

# API продавцов
@app.route('/api/sellers', methods=['GET', 'POST'])
@admin_required
def sellers():
    if request.method == 'GET':
        sellers_list = Seller.query.all()
        return jsonify([{'id': s.id, 'name': s.name} for s in sellers_list])

    elif request.method == 'POST':
        data = request.json
        seller = Seller(name=data['name'])
        db.session.add(seller)
        db.session.commit()
        return jsonify({'message': 'Seller added successfully'})

# API лотов
@app.route('/api/lots', methods=['GET', 'POST'])
@seller_or_admin_required
def lots():
    if request.method == 'GET':
        lots_list = Lot.query.all()
        return jsonify([{
            'id': l.id,
            'name': l.name,
            'starting_price': l.starting_price,
            'description': l.description,
            'category': l.category
        } for l in lots_list])

    elif request.method == 'POST':
        data = request.json
        lot = Lot(
            name=data['name'],
            starting_price=data['starting_price'],
            description=data['description'],
            category=data['category']
        )
        db.session.add(lot)
        db.session.commit()
        return jsonify({'message': 'Lot added successfully'})

# API аукционов
@app.route('/api/auctions', methods=['GET', 'POST'])
@seller_or_admin_required
def auctions():
    if request.method == 'GET':
        auctions_list = Auction.query.all()
        return jsonify([{
            'id': a.id,
            'date': a.date.isoformat(),
            'location': a.location,
            'notes': a.notes,
            'status': a.status,
            'final_price': a.final_price or '',
            'lot_name': a.lot.name,
            'seller_name': a.seller.name,
            'winner_name': a.winner.name if a.winner_bidder_id and a.winner else '',
            'bids_count': len(a.bids)
        } for a in auctions_list])

    elif request.method == 'POST':
        data = request.json
        auction = Auction(
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            location=data['location'],
            notes=data['notes'],
            status=data.get('status', 'active'),
            final_price=data.get('final_price'),
            lot_id=data['lot_id'],
            seller_id=data['seller_id'],
            winner_bidder_id=data.get('winner_bidder_id')
        )
        db.session.add(auction)
        db.session.flush()
        for bid_data in data.get('bids', []):
            bid = Bid(
                auction_id=auction.id,
                bidder_id=bid_data['bidder_id'],
                amount=bid_data['amount']
            )
            db.session.add(bid)
        db.session.commit()
        return jsonify({'message': 'Auction added successfully'})

# Аналитика: количество аукционов по дате
@app.route('/api/auctions/count-by-date', methods=['POST'])
@seller_or_admin_required
def count_auctions_by_date():
    data = request.json
    target_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    count = Auction.query.filter_by(date=target_date).count()
    return jsonify({'date': target_date.isoformat(), 'count': count})

# Аналитика: количество лотов по категории
@app.route('/api/lots/count-by-category', methods=['POST'])
@seller_or_admin_required
def count_lots_by_category():
    data = request.json
    category = data['category']
    count = Lot.query.filter_by(category=category).count()
    return jsonify({'category': category, 'count': count})

# Детали лота (категория, описание)
@app.route('/api/lots/<int:lot_id>/details')
@seller_or_admin_required
def get_lot_details(lot_id):
    lot = Lot.query.get_or_404(lot_id)
    return jsonify({
        'name': lot.name,
        'category': lot.category,
        'description': lot.description
    })

@app.route('/api/statistics')
@seller_or_admin_required
def get_statistics():
    from utils import get_statistics
    return jsonify(get_statistics())

@app.route('/api/popular-categories')
@seller_or_admin_required
def get_popular_categories():
    from utils import get_popular_categories
    return jsonify(get_popular_categories())

@app.route('/api/popular-lots')
@seller_or_admin_required
def get_popular_lots():
    from utils import get_popular_lots
    return jsonify(get_popular_lots())

@app.route('/api/search-bidders')
@seller_or_admin_required
def search_bidders():
    from utils import search_bidders
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    bidders_list = search_bidders(query)
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'email': b.email,
        'address': b.address or ''
    } for b in bidders_list])

@app.route('/api/bidder/<int:bidder_id>/history')
@seller_or_admin_required
def get_bidder_history(bidder_id):
    from utils import get_bidder_history
    auctions_list = get_bidder_history(bidder_id)
    return jsonify([{
        'id': a.id,
        'date': a.date.isoformat(),
        'location': a.location,
        'lot_name': a.lot.name,
        'status': a.status,
        'final_price': a.final_price or ''
    } for a in auctions_list])

@app.route('/api/visit-stats')
@login_required
def get_visit_stats():
    try:
        total_visits = redis_client.get('page_visits') or 0
        return jsonify({
            'total_visits': int(total_visits),
            'message': 'Статистика посещений главной страницы'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
