import streamlit as st
from models import Portfolio, User
from utils import get_stock_data, get_stock_info, format_number

def render_trading():
    st.subheader("Trade Stocks")
    
    symbol = st.text_input("Enter Stock Symbol").upper()
    if not symbol:
        return
    
    info = get_stock_info(symbol)
    if not info:
        st.error("Invalid symbol")
        return
    
    # Display stock info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", format_number(info['price']))
    with col2:
        st.metric("Change", f"{info['change']:.2f}%")
    with col3:
        st.metric("Volume", format_number(info['volume']))
    
    # Trading form
    with st.form(key='trade_form'):
        col1, col2 = st.columns(2)
        with col1:
            action = st.selectbox("Action", ["BUY", "SELL"])
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=1)
        
        current_price = get_stock_data(symbol).iloc[-1]['Close']
        total_cost = current_price * quantity
        
        st.write(f"Total {action} Amount: {format_number(total_cost)}")
        
        submitted = st.form_submit_button("Place Order")
        
        if submitted:
            user_id = st.session_state.user_id
            balance = User.get_balance(user_id)
            
            if action == "BUY":
                if total_cost > balance:
                    st.error("Insufficient funds")
                    return
                
                User.update_balance(user_id, balance - total_cost)
                Portfolio.update_position(user_id, symbol, quantity, current_price, "BUY")
                st.success(f"Successfully bought {quantity} shares of {symbol}")
                
            else:  # SELL
                holdings = Portfolio.get_holdings(user_id)
                current_position = next((h for h in holdings if h['symbol'] == symbol), None)
                
                if not current_position or current_position['quantity'] < quantity:
                    st.error("Insufficient shares to sell")
                    return
                
                User.update_balance(user_id, balance + total_cost)
                Portfolio.update_position(user_id, symbol, quantity, current_price, "SELL")
                st.success(f"Successfully sold {quantity} shares of {symbol}")
