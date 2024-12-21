import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import User, Portfolio, Watchlist
from database import Database
from utils import get_stock_data, get_stock_info
from utils.sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize database
try:
    Database.initialize()
    Database.create_tables()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {str(e)}")
    raise

# Create default user
try:
    User.create('demo', 'demo123')
    logger.info("Default user created or already exists")
except Exception as e:
    if 'duplicate key value' not in str(e).lower():
        logger.error(f"Error creating default user: {str(e)}")

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.authenticate(data['username'], data['password'])
    if user:
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'balance': float(user['balance'])
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    try:
        user = User.create(data['username'], data['password'])
        if user:
            return jsonify({'message': 'Registration successful'})
        return jsonify({'error': 'Registration failed'}), 400
    except Exception:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/api/portfolio/<int:user_id>')
def get_portfolio(user_id):
    holdings = Portfolio.get_holdings(user_id)
    return jsonify(holdings)

@app.route('/api/watchlist/<int:user_id>')
def get_watchlist(user_id):
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

@app.route('/api/watchlist/<int:user_id>', methods=['POST'])
def add_to_watchlist(user_id):
    data = request.get_json()
    symbol = data['symbol'].upper()
    if get_stock_info(symbol):
        Watchlist.add_symbol(user_id, symbol)
        return jsonify({'message': 'Symbol added to watchlist'})
    return jsonify({'error': 'Invalid symbol'}), 400

@app.route('/api/watchlist/<int:user_id>/<symbol>', methods=['DELETE'])
def remove_from_watchlist(user_id, symbol):
    Watchlist.remove_symbol(user_id, symbol.upper())
    return jsonify({'message': 'Symbol removed from watchlist'})

@app.route('/api/trade', methods=['POST'])
def trade():
    data = request.get_json()
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

@app.route('/api/sentiment/<symbol>')
def get_sentiment(symbol):
    analyzer = SentimentAnalyzer()
    sentiment = analyzer.get_composite_sentiment(symbol.upper())
    return jsonify(sentiment)

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
