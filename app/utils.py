"""
Утилиты для приложения аукциона
"""

from datetime import date
from app import db, Bidder, Seller, Lot, Auction, Bid


def get_statistics():
    """Общая статистика системы аукциона"""
    return {
        'total_bidders': Bidder.query.count(),
        'total_sellers': Seller.query.count(),
        'total_lots': Lot.query.count(),
        'total_auctions': Auction.query.count(),
        'auctions_today': Auction.query.filter_by(date=date.today()).count(),
        'auctions_this_week': Auction.query.filter(
            Auction.date >= date.today().replace(day=date.today().day - 7)
        ).count()
    }


def get_popular_categories(limit=5):
    """Самые частые категории лотов"""
    from sqlalchemy import func
    popular = db.session.query(
        Lot.category,
        func.count(Lot.category).label('count')
    ).group_by(Lot.category).order_by(
        func.count(Lot.category).desc()
    ).limit(limit).all()
    return [{'category': c[0], 'count': c[1]} for c in popular]


def get_popular_lots(limit=5):
    """Самые участвующие в аукционах лоты"""
    from sqlalchemy import func
    popular = db.session.query(
        Lot.name,
        func.count(Auction.id).label('count')
    ).join(Auction).group_by(Lot.name).order_by(
        func.count(Auction.id).desc()
    ).limit(limit).all()
    return [{'lot': l[0], 'count': l[1]} for l in popular]


def search_bidders(query):
    """Поиск участников по имени, email или адресу"""
    from sqlalchemy import or_
    return Bidder.query.filter(
        or_(
            Bidder.name.contains(query),
            Bidder.email.contains(query),
            Bidder.address.contains(query)
        )
    ).all()


def get_bidder_history(bidder_id):
    """История участия в аукционах (где участвовал ставками)"""
    return Auction.query.join(Bid).filter(
        Bid.bidder_id == bidder_id
    ).order_by(Auction.date.desc()).all()


def get_seller_auctions(seller_id, start_date, end_date):
    """Аукционы продавца за период"""
    return Auction.query.filter(
        Auction.seller_id == seller_id,
        Auction.date >= start_date,
        Auction.date <= end_date
    ).order_by(Auction.date).all()


def validate_bidder_data(data):
    """Валидация данных участника"""
    errors = []
    if not data.get('name') or len(data['name'].strip()) < 2:
        errors.append('Имя должно содержать минимум 2 символа')
    if not data.get('email') or '@' not in data.get('email', ''):
        errors.append('Нужен корректный email')
    return errors


def validate_lot_data(data):
    """Валидация данных лота"""
    errors = []
    if not data.get('name') or len(data['name'].strip()) < 2:
        errors.append('Название лота должно содержать минимум 2 символа')
    if not data.get('starting_price') or len(data['starting_price'].strip()) < 1:
        errors.append('Укажите стартовую цену')
    if not data.get('description') or len(data['description'].strip()) < 5:
        errors.append('Описание должно содержать минимум 5 символов')
    if not data.get('category') or len(data['category'].strip()) < 2:
        errors.append('Укажите категорию лота')
    return errors
