import streamlit as st
from models import Portfolio
from utils import get_stock_data, format_number, calculate_portfolio_value

def render_portfolio(user_id):
    st.subheader("Portfolio Overview")
    
    holdings = Portfolio.get_holdings(user_id)
    if not holdings:
        st.info("Your portfolio is empty. Start trading to build your portfolio!")
        return

    total_value = calculate_portfolio_value(holdings)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Portfolio Value", format_number(total_value))
    
    # Portfolio table
    data = []
    for holding in holdings:
        current_price = get_stock_data(holding['symbol']).iloc[-1]['Close']
        position_value = current_price * holding['quantity']
        unrealized_pl = (current_price - holding['average_price']) * holding['quantity']
        
        data.append({
            "Symbol": holding['symbol'],
            "Shares": holding['quantity'],
            "Avg Price": format_number(holding['average_price']),
            "Current Price": format_number(current_price),
            "Value": format_number(position_value),
            "Unrealized P/L": format_number(unrealized_pl)
        })
    
    st.dataframe(data)
