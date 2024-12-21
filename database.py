import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

class Database:
    _connection_pool = None

    @classmethod
    def initialize(cls):
        if not cls._connection_pool:
            cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.getenv('PGHOST'),
                database=os.getenv('PGDATABASE'),
                user=os.getenv('PGUSER'),
                password=os.getenv('PGPASSWORD'),
                port=os.getenv('PGPORT')
            )

    @classmethod
    def get_connection(cls):
        if not cls._connection_pool:
            cls.initialize()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        cls._connection_pool.putconn(connection)

    @classmethod
    def execute_query(cls, query, parameters=None):
        conn = cls.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, parameters)
                conn.commit()
                try:
                    return cur.fetchall()
                except psycopg2.ProgrammingError:
                    return None
        finally:
            cls.return_connection(conn)

    @classmethod
    def create_tables(cls):
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            balance DECIMAL(15,2) DEFAULT 100000.00
        );
        """
        
        portfolio_table = """
        CREATE TABLE IF NOT EXISTS portfolio (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            symbol VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL,
            average_price DECIMAL(10,2) NOT NULL
        );
        """
        
        watchlist_table = """
        CREATE TABLE IF NOT EXISTS watchlist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            symbol VARCHAR(10) NOT NULL,
            UNIQUE(user_id, symbol)
        );
        """
        
        transactions_table = """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            symbol VARCHAR(10) NOT NULL,
            quantity INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            transaction_type VARCHAR(4) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cls.execute_query(users_table)
        cls.execute_query(portfolio_table)
        cls.execute_query(watchlist_table)
        cls.execute_query(transactions_table)
