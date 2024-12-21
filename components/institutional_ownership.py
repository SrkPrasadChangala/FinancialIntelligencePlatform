import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from models import Company, Institution, Holding
from utils.sec_data import SecDataExtractor

def render_institutional_ownership():
    st.title("Institutional Ownership Analysis")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Company View", "Institution View", "Update Data"])
    
    with tab1:
        render_company_view()
    
    with tab2:
        render_institution_view()
        
    with tab3:
        render_data_update()

def render_company_view():
    st.header("Company Holdings")
    
    # Company search
    companies = Company.get_all()
    if not companies:
        st.warning("No company data available. Please update the database using the 'Update Data' tab.")
        return
        
    company_names = {f"{c['name']} ({c['ticker']})": c['id'] for c in companies}
    selected_company = st.selectbox(
        "Select a company",
        options=list(company_names.keys())
    )
    
    if selected_company:
        company_id = company_names[selected_company]
        
        # Date range for analysis
        col1, col2 = st.columns(2)
        with col1:
            from_date = st.date_input(
                "From date",
                value=datetime.now() - timedelta(days=365)
            )
        with col2:
            to_date = st.date_input("To date", value=datetime.now())
            
        # Get ownership changes
        changes = Holding.get_ownership_changes(company_id, from_date, to_date)
        
        if changes:
            st.subheader("Ownership Changes")
            
            # Create a line chart of total shares held over time
            df_changes = pd.DataFrame(changes)
            fig = go.Figure()
            
            # Add trace for total shares
            fig.add_trace(go.Scatter(
                x=df_changes['filing_date'],
                y=df_changes['shares_held'],
                mode='lines+markers',
                name='Shares Held'
            ))
            
            fig.update_layout(
                title=f"Institutional Ownership Over Time",
                xaxis_title="Filing Date",
                yaxis_title="Shares Held",
                showlegend=True
            )
            
            st.plotly_chart(fig)
            
            # Display detailed changes
            st.subheader("Latest Institutional Holdings")
            for change in changes:
                with st.expander(f"{change['institution_name']} (CIK: {change['cik']})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Shares Held", f"{change['shares_held']:,}")
                    with col2:
                        st.metric("Value (USD)", f"${change['value_usd']:,.2f}")
                    with col3:
                        share_change = change['shares_change']
                        delta_color = "normal" if share_change >= 0 else "inverse"
                        st.metric("Change in Shares", f"{abs(share_change):,}", 
                                f"{share_change:,}", delta_color=delta_color)
        else:
            st.info("No ownership data available for the selected date range.")

def render_institution_view():
    st.header("Institution Portfolio")
    
    # Institution search
    institutions = Institution.get_all()
    if not institutions:
        st.warning("No institution data available. Please update the database using the 'Update Data' tab.")
        return
        
    institution_names = {f"{i['name']} (CIK: {i['cik']})": i['id'] for i in institutions}
    selected_institution = st.selectbox(
        "Select an institution",
        options=list(institution_names.keys())
    )
    
    if selected_institution:
        institution_id = institution_names[selected_institution]
        holdings = Holding.get_by_institution(institution_id)
        
        if holdings:
            # Create a treemap of holdings
            df_holdings = pd.DataFrame(holdings)
            fig = go.Figure(go.Treemap(
                labels=df_holdings['company_name'],
                parents=[''] * len(df_holdings),
                values=df_holdings['value_usd'],
                textinfo="label+value",
                hovertemplate="<b>%{label}</b><br>Value: $%{value:,.2f}<extra></extra>"
            ))
            
            fig.update_layout(
                title="Portfolio Composition",
                width=800,
                height=500
            )
            
            st.plotly_chart(fig)
            
            # Display detailed holdings
            st.subheader("Detailed Holdings")
            for holding in holdings:
                with st.expander(f"{holding['company_name']} ({holding['ticker']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Shares Held", f"{holding['shares_held']:,}")
                    with col2:
                        st.metric("Value (USD)", f"${holding['value_usd']:,.2f}")
        else:
            st.info("No holdings data available for this institution.")

def render_data_update():
    st.header("Update 13F Filing Data")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start date",
            value=datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input("End date", value=datetime.now())
    
    if st.button("Update Data"):
        with st.spinner("Fetching and processing 13F filings..."):
            sec_data = SecDataExtractor()
            processed_count = sec_data.update_institutional_ownership(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            st.success(f"Successfully processed {processed_count} 13F filings.")
