#!/usr/bin/env python3
"""
Скрипт инициализации базы данных аукциона с тестовыми данными
"""

from app import app, db, User, Bidder, Seller, Lot, Auction, Bid
from datetime import date
from werkzeug.security import generate_password_hash


def init_database():
    """Инициализация базы данных с тестовыми данными аукциона"""

    with app.app_context():
        db.drop_all()
        db.create_all()

        print("Создание тестовых данных аукциона...")

        users_data = [
            {
                'username': 'admin',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'name': 'Администратор Аукциона',
                'is_active': True
            },
            {
                'username': 'seller',
                'password_hash': generate_password_hash('seller123'),
                'role': 'seller',
                'name': 'Иван Продавцов',
                'is_active': True
            }
        ]

        users = []
        for u in users_data:
            user = User(**u)
            db.session.add(user)
            users.append(user)
        db.session.commit()
        print("Пользователи созданы")

        bidders_data = [
            {'name': 'Алексей Покупателев', 'email': 'alex@mail.ru', 'phone': '+7 900 111-22-33', 'address': 'Москва, ул. Торговая, 1'},
            {'name': 'Мария Ставкина', 'email': 'maria@mail.ru', 'phone': '+7 900 222-33-44', 'address': 'Москва, ул. Аукционная, 5'},
            {'name': 'Пётр Торговцев', 'email': 'petr@mail.ru', 'phone': '+7 900 333-44-55', 'address': 'Москва, ул. Лотовая, 10'},
            {'name': 'Ольга Победителева', 'email': 'olga@mail.ru', 'phone': None, 'address': None},
        ]

        bidders = []
        for b in bidders_data:
            bidder = Bidder(**b)
            db.session.add(bidder)
            bidders.append(bidder)

        sellers_data = [
            {'name': 'Антиквариат и Ко'},
            {'name': 'Картинная галерея'},
            {'name': 'Частный аукционный дом'},
        ]
        sellers = []
        for s in sellers_data:
            seller = Seller(**s)
            db.session.add(seller)
            sellers.append(seller)

        lots_data = [
            {'name': 'Картина «Закат»', 'starting_price': '50 000 ₽', 'description': 'Масло, холст, 60×80 см', 'category': 'Живопись'},
            {'name': 'Серебряный сервиз', 'starting_price': '120 000 ₽', 'description': 'Россия, XIX век, 24 предмета', 'category': 'Антиквариат'},
            {'name': 'Часы настольные', 'starting_price': '35 000 ₽', 'description': 'Бронза, Франция, нач. XX в.', 'category': 'Антиквариат'},
            {'name': 'Коллекция монет', 'starting_price': '80 000 ₽', 'description': 'СССР, 50 монет', 'category': 'Нумизматика'},
        ]
        lots = []
        for l in lots_data:
            lot = Lot(**l)
            db.session.add(lot)
            lots.append(lot)

        db.session.commit()
        print("Участники, продавцы и лоты созданы")

        auctions_data = [
            {
                'date': date(2024, 1, 15),
                'location': 'Онлайн-платформа',
                'notes': 'Вечерние торги',
                'status': 'completed',
                'final_price': '75 000 ₽',
                'lot_id': lots[0].id,
                'seller_id': sellers[1].id,
                'winner_bidder_id': bidders[0].id,
                'bids': [{'bidder_id': bidders[0].id, 'amount': '75 000 ₽'}, {'bidder_id': bidders[1].id, 'amount': '70 000 ₽'}]
            },
            {
                'date': date(2024, 1, 15),
                'location': 'Зал №1',
                'notes': 'Дневная сессия',
                'status': 'completed',
                'final_price': '150 000 ₽',
                'lot_id': lots[1].id,
                'seller_id': sellers[0].id,
                'winner_bidder_id': bidders[1].id,
                'bids': [{'bidder_id': bidders[1].id, 'amount': '150 000 ₽'}, {'bidder_id': bidders[2].id, 'amount': '130 000 ₽'}]
            },
            {
                'date': date(2024, 1, 16),
                'location': 'Онлайн',
                'notes': 'Специальный аукцион',
                'status': 'active',
                'final_price': None,
                'lot_id': lots[2].id,
                'seller_id': sellers[2].id,
                'winner_bidder_id': None,
                'bids': [{'bidder_id': bidders[2].id, 'amount': '32 000 ₽'}]
            },
        ]

        for a in auctions_data:
            bids = a.pop('bids')
            auction = Auction(**a)
            db.session.add(auction)
            db.session.flush()
            for b in bids:
                db.session.add(Bid(auction_id=auction.id, bidder_id=b['bidder_id'], amount=b['amount']))

        db.session.commit()
        print("Аукционы и ставки созданы")

        print("\n=== ТЕСТОВЫЕ ДАННЫЕ АУКЦИОНА СОЗДАНЫ ===")
        print(f"Пользователей: {len(users)}")
        print(f"Участников торгов: {len(bidders)}")
        print(f"Продавцов: {len(sellers)}")
        print(f"Лотов: {len(lots)}")
        print(f"Аукционов: {len(auctions_data)}")
        print("\n=== ТЕСТОВЫЕ АККАУНТЫ ===")
        print("Администратор: admin / admin123 (полный доступ)")
        print("Продавец: seller / seller123 (лоты, аукционы, участники)")
        print("\nДля запуска: python app.py  или  из папки app: python -m app.app")


if __name__ == '__main__':
    init_database()
