import streamlit as st
from database import Database
from models import User
from components import portfolio, watchlist, trading, charts
from components import portfolio, trading, watchlist, sp100_view

# Initialize the database
Database.initialize()
Database.create_tables()
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

# Page configuration
st.set_page_config(
    page_title="Stock Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

def main():
    if st.session_state.user_id is None:
        show_login_page()
    else:
        show_trading_platform()

def show_login_page():
    st.title("Welcome to Stock Trading Platform")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                user = User.authenticate(username, password)
                if user:
                    st.session_state.user_id = user['id']
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if len(new_username) < 3 or len(new_password) < 6:
                    st.error("Username must be at least 3 characters and password at least 6 characters")
                else:
                    try:
                        user = User.create(new_username, new_password)
                        if user:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Registration failed")
                    except Exception as e:
                        st.error("Username already exists")

def show_trading_platform():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Portfolio", "Trading", "Watchlist", "S&P 100"])
    
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()
    
    if page == "Portfolio":
        portfolio.render_portfolio(st.session_state.user_id)
    elif page == "Trading":
        trading.render_trading()
    elif page == "Watchlist":
        watchlist.render_watchlist(st.session_state.user_id)
    else:  # S&P 100
        sp100_view.render_sp100_view()

if __name__ == "__main__":
    main()
