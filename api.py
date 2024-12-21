import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import User, Portfolio, Watchlist
import os
from database import Database
from utils import get_stock_data, get_stock_info
from utils.sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend/build')
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://0.0.0.0:3000"]}})

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Initialize database
try:
    Database.initialize()
    Database.create_tables()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

# Create default user
def create_default_user():
    try:
        # Create a default demo account
        User.create('demo', 'demo123')
        print("Default user created successfully")
    except Exception as e:
        if 'duplicate key value' not in str(e).lower():
            print(f"Error creating default user: {e}")

# Create default user
create_default_user()

@app.route('/')
def health_check():
    try:
        # Test database connection
        Database.execute_query("SELECT 1")
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    try:
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        app.logger.error(f"Error serving static files: {str(e)}")
        return jsonify({'error': 'Not found'}), 404


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        user = User.authenticate(data['username'], data['password'])
        if user:
            return jsonify({
                'id': user['id'],
                'username': user['username'],
                'balance': float(user['balance'])
            })
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    try:
        user = User.create(data['username'], data['password'])
        if user:
            return jsonify({'message': 'Registration successful'})
        return jsonify({'error': 'Registration failed'}), 400
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        if 'duplicate key value' in str(e).lower():
            return jsonify({'error': 'Username already exists'}), 400
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/portfolio/<int:user_id>')
def get_portfolio(user_id):
    try:
        holdings = Portfolio.get_holdings(user_id)
        return jsonify(holdings)
    except Exception as e:
        logger.error(f"Get portfolio failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve portfolio'}), 500

@app.route('/api/watchlist/<int:user_id>')
def get_watchlist(user_id):
    try:
        symbols = Watchlist.get_symbols(user_id)
        watchlist_data = []
        for symbol in symbols:
            info = get_stock_info(symbol)
            if info:
                data = get_stock_data(symbol)
                if data is not None and not data.empty:
                    current_price = data.iloc[-1]['Close']
                    watchlist_data.append({
                        'symbol': symbol,
                        'name': info['name'],
                        'price': current_price,
                        'change': info['change'],
                        'volume': info['volume'],
                        'marketCap': info['market_cap']
                    })
        return jsonify(watchlist_data)
    except Exception as e:
        logger.error(f"Get watchlist failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve watchlist'}), 500

@app.route('/api/watchlist/<int:user_id>', methods=['POST'])
def add_to_watchlist(user_id):
    data = request.get_json()
    try:
        symbol = data['symbol'].upper()
        if get_stock_info(symbol):
            Watchlist.add_symbol(user_id, symbol)
            return jsonify({'message': 'Symbol added to watchlist'})
        return jsonify({'error': 'Invalid symbol'}), 400
    except Exception as e:
        logger.error(f"Add to watchlist failed: {str(e)}")
        return jsonify({'error': 'Failed to add symbol to watchlist'}), 500

@app.route('/api/watchlist/<int:user_id>/<symbol>', methods=['DELETE'])
def remove_from_watchlist(user_id, symbol):
    try:
        Watchlist.remove_symbol(user_id, symbol.upper())
        return jsonify({'message': 'Symbol removed from watchlist'})
    except Exception as e:
        logger.error(f"Remove from watchlist failed: {str(e)}")
        return jsonify({'error': 'Failed to remove symbol from watchlist'}), 500

@app.route('/api/trade', methods=['POST'])
def trade():
    data = request.get_json()
    try:
        user_id = data['userId']
        symbol = data['symbol'].upper()
        quantity = data['quantity']
        action = data['action']

        info = get_stock_info(symbol)
        if not info:
            return jsonify({'error': 'Invalid symbol'}), 400

        current_price = float(info['price'])
        total_cost = current_price * quantity

        user = User.get_by_id(user_id)
        balance = float(user['balance'])

        if action == 'BUY':
            if total_cost > balance:
                return jsonify({'error': 'Insufficient funds'}), 400
            User.update_balance(user_id, balance - total_cost)
            Portfolio.update_position(user_id, symbol, quantity, current_price, 'BUY')
            return jsonify({'message': f'Successfully bought {quantity} shares of {symbol}'})
        else:  # SELL
            holdings = Portfolio.get_holdings(user_id)
            current_position = next((h for h in holdings if h['symbol'] == symbol), None)
            if not current_position or current_position['quantity'] < quantity:
                return jsonify({'error': 'Insufficient shares to sell'}), 400
            User.update_balance(user_id, balance + total_cost)
            Portfolio.update_position(user_id, symbol, quantity, current_price, 'SELL')
            return jsonify({'message': f'Successfully sold {quantity} shares of {symbol}'})
    except Exception as e:
        logger.error(f"Trade failed: {str(e)}")
        return jsonify({'error': 'Trade failed'}), 500


@app.route('/api/sentiment/<symbol>')
def get_sentiment(symbol):
    try:
        analyzer = SentimentAnalyzer()
        sentiment = analyzer.get_composite_sentiment(symbol.upper())
        return jsonify(sentiment)
    except Exception as e:
        logger.error(f"Get sentiment failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve sentiment'}), 500

if __name__ == '__main__':
    try:
        logger.info("Starting Flask API server on port 3001...")
        app.run(
            host='0.0.0.0',
            port=3001,
            debug=True,
            use_reloader=True
        )
    except Exception as e:
        logger.error(f"Failed to start Flask API: {str(e)}")
        raise