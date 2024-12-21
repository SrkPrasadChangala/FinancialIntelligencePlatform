import os
from datetime import datetime
from sec_api import QueryApi
from database import Database
from models import Institution, Company, Holding

class SecDataExtractor:
    def __init__(self):
        self.api = QueryApi(api_key=os.getenv('SEC_API_KEY'))

    def fetch_13f_filings(self, start_date: str, end_date: str = None):
        """
        Fetch 13F filings from SEC EDGAR database for a given date range.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format (defaults to today)
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        query = {
            "query": {
                "query_string": {
                    "query": "formType:\"13F-HR\" AND NOT formType:\"13F-HR/A\""
                }
            },
            "from": start_date,
            "to": end_date,
            "size": 100
        }

        try:
            response = self.api.get_filings(query)
            return response.get('filings', [])
        except Exception as e:
            print(f"Error fetching 13F filings: {str(e)}")
            return []

    def process_13f_filing(self, filing):
        """Process a single 13F filing and store the data."""
        try:
            # Extract institution information
            institution = Institution.create(
                cik=filing.get('cik'),
                name=filing.get('companyName')
            )

            if not institution:
                return False

            # Process holdings from the filing
            holdings = filing.get('holdings', [])
            filing_date = datetime.strptime(filing.get('filedAt'), '%Y-%m-%d')
            quarter = (filing_date.month - 1) // 3 + 1
            year = filing_date.year

            for holding in holdings:
                # Create or get company
                company = Company.create(
                    ticker=holding.get('cusip'),  # Using CUSIP as ticker temporarily
                    name=holding.get('nameOfIssuer')
                )

                if company:
                    # Create holding record
                    Holding.create(
                        institution_id=institution['id'],
                        company_id=company['id'],
                        shares_held=holding.get('shares', 0),
                        value_usd=holding.get('value', 0),
                        filing_date=filing_date,
                        quarter=quarter,
                        year=year
                    )

            return True
        except Exception as e:
            print(f"Error processing 13F filing: {str(e)}")
            return False

    def update_institutional_ownership(self, start_date: str, end_date: str = None):
        """
        Update institutional ownership data for the given date range.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format (defaults to today)
        """
        filings = self.fetch_13f_filings(start_date, end_date)
        processed_count = 0

        for filing in filings:
            if self.process_13f_filing(filing):
                processed_count += 1

        return processed_count
