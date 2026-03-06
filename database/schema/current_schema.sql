-- Схема БД приложения «Аукцион»
-- Файл базы: data/auction.db (от корня проекта) или /app/data/auction.db в Docker

CREATE TABLE user (
	id INTEGER NOT NULL,
	username VARCHAR(80) NOT NULL,
	password_hash VARCHAR(120) NOT NULL,
	role VARCHAR(20) NOT NULL,
	name VARCHAR(100) NOT NULL,
	is_active BOOLEAN,
	PRIMARY KEY (id),
	UNIQUE (username)
);

CREATE TABLE bidder (
	id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	email VARCHAR(120) NOT NULL,
	phone VARCHAR(20),
	address VARCHAR(200),
	PRIMARY KEY (id)
);

CREATE TABLE seller (
	id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE lot (
	id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	starting_price VARCHAR(50) NOT NULL,
	description TEXT NOT NULL,
	category VARCHAR(100) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name)
);

CREATE TABLE auction (
	id INTEGER NOT NULL,
	date DATE NOT NULL,
	location VARCHAR(200) NOT NULL,
	notes TEXT NOT NULL,
	status VARCHAR(50) NOT NULL,
	final_price VARCHAR(50),
	lot_id INTEGER NOT NULL,
	seller_id INTEGER NOT NULL,
	winner_bidder_id INTEGER,
	PRIMARY KEY (id),
	FOREIGN KEY(lot_id) REFERENCES lot (id),
	FOREIGN KEY(seller_id) REFERENCES seller (id),
	FOREIGN KEY(winner_bidder_id) REFERENCES bidder (id)
);

CREATE TABLE bid (
	id INTEGER NOT NULL,
	auction_id INTEGER NOT NULL,
	bidder_id INTEGER NOT NULL,
	amount VARCHAR(50) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(auction_id) REFERENCES auction (id),
	FOREIGN KEY(bidder_id) REFERENCES bidder (id)
);
