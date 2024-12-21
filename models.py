from database import Database
from datetime import datetime
import hashlib

class User:
    @staticmethod
    def create(username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = """
        INSERT INTO users (username, password_hash)
        VALUES (%s, %s) RETURNING id, username, balance
        """
        result = Database.execute_query(query, (username, password_hash))
        return result[0] if result else None

    @staticmethod
    def authenticate(username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = """
        SELECT id, username, balance
        FROM users
        WHERE username = %s AND password_hash = %s
        """
        result = Database.execute_query(query, (username, password_hash))
        return result[0] if result else None

    @staticmethod
    def get_balance(user_id):
        query = "SELECT balance FROM users WHERE id = %s"
        result = Database.execute_query(query, (user_id,))
        return float(result[0]['balance']) if result else 0.0

    @staticmethod
    def update_balance(user_id, new_balance):
        query = "UPDATE users SET balance = %s WHERE id = %s"
        Database.execute_query(query, (new_balance, user_id))

class Portfolio:
    @staticmethod
    def get_holdings(user_id):
        query = """
        SELECT symbol, quantity, average_price
        FROM portfolio
        WHERE user_id = %s
        """
        return Database.execute_query(query, (user_id,))

    @staticmethod
    def update_position(user_id, symbol, quantity, price, transaction_type):
        # First, record the transaction
        transaction_query = """
        INSERT INTO transactions (user_id, symbol, quantity, price, transaction_type)
        VALUES (%s, %s, %s, %s, %s)
        """
        Database.execute_query(transaction_query, (user_id, symbol, quantity, price, transaction_type))

        # Then update the portfolio
        existing_query = """
        SELECT quantity, average_price FROM portfolio
        WHERE user_id = %s AND symbol = %s
        """
        existing = Database.execute_query(existing_query, (user_id, symbol))

        if existing:
            current_qty = existing[0]['quantity']
            current_avg_price = float(existing[0]['average_price'])

            if transaction_type == 'BUY':
                new_qty = current_qty + quantity
                new_avg_price = ((current_qty * current_avg_price) + (quantity * price)) / new_qty
            else:  # SELL
                new_qty = current_qty - quantity
                new_avg_price = current_avg_price if new_qty > 0 else 0

            if new_qty > 0:
                update_query = """
                UPDATE portfolio 
                SET quantity = %s, average_price = %s
                WHERE user_id = %s AND symbol = %s
                """
                Database.execute_query(update_query, (new_qty, new_avg_price, user_id, symbol))
            else:
                delete_query = """
                DELETE FROM portfolio
                WHERE user_id = %s AND symbol = %s
                """
                Database.execute_query(delete_query, (user_id, symbol))
        elif transaction_type == 'BUY':
            insert_query = """
            INSERT INTO portfolio (user_id, symbol, quantity, average_price)
            VALUES (%s, %s, %s, %s)
            """
            Database.execute_query(insert_query, (user_id, symbol, quantity, price))

class Watchlist:
    @staticmethod
    def get_symbols(user_id):
        query = "SELECT symbol FROM watchlist WHERE user_id = %s"
        result = Database.execute_query(query, (user_id,))
        return [item['symbol'] for item in result] if result else []

    @staticmethod
    def add_symbol(user_id, symbol):
        query = """
        INSERT INTO watchlist (user_id, symbol)
        VALUES (%s, %s)
        ON CONFLICT (user_id, symbol) DO NOTHING
        """
        Database.execute_query(query, (user_id, symbol))

    @staticmethod
    def remove_symbol(user_id, symbol):
        query = "DELETE FROM watchlist WHERE user_id = %s AND symbol = %s"
        Database.execute_query(query, (user_id, symbol))
