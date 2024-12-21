import streamlit as st
from models import Watchlist
from utils import get_stock_data, get_stock_info, format_number, format_change

def render_watchlist(user_id):
    st.subheader("Watchlist")
    
    # Add new symbol
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input("Add symbol to watchlist", key="new_symbol").upper()
    with col2:
        if st.button("Add"):
            if new_symbol:
                if get_stock_info(new_symbol):
                    Watchlist.add_symbol(user_id, new_symbol)
                    st.success(f"Added {new_symbol} to watchlist")
                else:
                    st.error("Invalid symbol")

    # Display watchlist
    symbols = Watchlist.get_symbols(user_id)
    if not symbols:
        st.info("Your watchlist is empty. Add symbols to track them!")
        return

    watchlist_data = []
    for symbol in symbols:
        info = get_stock_info(symbol)
        if info:
            data = get_stock_data(symbol)
            if data is not None and not data.empty:
                current_price = data.iloc[-1]['Close']
                watchlist_data.append({
                    "Symbol": symbol,
                    "Name": info['name'],
                    "Price": format_number(current_price),
                    "Change": format_change(info['change']),
                    "Volume": format_number(info['volume']),
                    "Market Cap": format_number(info['market_cap'])
                })
    
    for item in watchlist_data:
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1:
            st.write(f"**{item['Symbol']}**")
        with col2:
            st.write(item['Name'])
        with col3:
            st.write(item['Price'])
        with col4:
            if st.button("Remove", key=f"remove_{item['Symbol']}"):
                Watchlist.remove_symbol(user_id, item['Symbol'])
                st.rerun()
