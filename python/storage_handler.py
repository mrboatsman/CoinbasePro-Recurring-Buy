import os
import sqlite3
from datetime import datetime


class Order:
    order_id: str = None
    fiat_cost: float = None
    amount_coins: float = None
    fiat_currency: str = None
    crypt_currency: str = None
    price: float = None
    timestamp: datetime = None

    def __init__(self, order_id, fiat_cost, amount_coins, fiat_currency,
                 crypt_currency, price, timestamp):
        self.order_id: str = order_id
        self.fiat_cost: float = fiat_cost
        self.amount_coins: float = amount_coins
        self.fiat_currency: str = fiat_currency
        self.crypt_currency: str = crypt_currency
        self.price: float = price
        self.timestamp: datetime = timestamp


class Orders:
    order_list = list()

    def __init__(self, order: Order):
        self.order_list.append(order)


class Storage:
    orders: Orders = None

    def __init__(self):
        self.storage_path = '/storage/database.db'

        if not os.path.exists(self.storage_path):
            con = sqlite3.connect(self.storage_path)
            cur = con.cursor()
            cur.execute('''CREATE TABLE dca_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_id TEXT NOT NULL,
                            fiat_cost REAL,
                            "size" REAL,
                            fiat_currency TEXT,
                            crypt_currency TEXT,
                            price REAL,
                            "timestamp" timestamp);
                      ''')

            cur.execute('''
                CREATE TABLE last_synced (
                    sync_date timestamp NOT NULL
                );
            ''')
            con.commit()
            con.close()

        con = sqlite3.connect(self.storage_path)

        self.db_handler = con

    @property
    def handler(self):
        return self.db_handler

    def __del__(self):
        self.db_handler.close()
        pass

    def insert_order(self, order: Order):
        cursor = self.db_handler.cursor()
        exists = cursor.execute('''
            select order_id from dca_history 
            where order_id = ?''', [order.order_id]).fetchone()

        if not exists:
            cursor.execute('''
                INSERT INTO dca_history
                    (order_id, fiat_cost, "size", fiat_currency, crypt_currency, price, "timestamp")
                    VALUES(?, ?, ?, ?, ?, ?, ?);
            ''', (order.order_id,
                  float(order.fiat_cost),
                  float(order.amount_coins),
                  order.fiat_currency,
                  order.crypt_currency,
                  0,
                  order.timestamp))
            self.db_handler.commit()

    def synced(self):
        cursor = self.db_handler.cursor()
        synced_date = None
        sync_data = cursor.execute('''
                    select sync_date from last_synced limit 1
                    ''')
        for sync_date in sync_data:
            synced_date = sync_date[0]

        return synced_date

    def update_sync(self):
        cursor = self.db_handler.cursor()
        cursor.execute('''DELETE FROM last_synced WHERE last_synced.rowid=1''')
        self.db_handler.commit()
        cursor.execute('''
        INSERT INTO last_synced (sync_date)
        VALUES (?);''', [datetime.utcnow()])
        self.db_handler.commit()

    def get_history(self):
        cursor = self.db_handler.cursor()
        my_data = cursor.execute('''
            SELECT * from dca_history dh order by "timestamp"
        ''')
        orders = list()

        for order in my_data:
            orders.append(Order(order_id=order[1],
                                fiat_cost=order[2],
                                amount_coins=order[3],
                                fiat_currency=order[4],
                                crypt_currency=order[5],
                                price=order[6],
                                timestamp=order[7]))
        cursor.close()

        return orders

