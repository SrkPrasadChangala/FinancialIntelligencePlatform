import yfinance as yf
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from typing import Dict, List, Tuple, Optional

class CompanyMatcher:
    def __init__(self):
        self.company_data: Dict[str, dict] = {}
        self.keywords: Dict[str, str] = {}
        self._initialize_data()

    def _initialize_data(self):
        """Initialize company data from S&P 500 companies"""
        # Start with S&P 100 companies for quick initialization
        sp100_symbols = [
            "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "BRK-B", "JPM",
            "JNJ", "V", "PG", "XOM", "MA", "HD", "CVX", "BAC", "KO", "PFE",
            "ABBV", "WMT", "AVGO", "PEP", "LLY", "MRK", "TMO"
        ]

        for symbol in sp100_symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if info:
                    company_name = info.get('longName', '')
                    if company_name:
                        self.company_data[symbol] = {
                            'name': company_name,
                            'keywords': self._generate_keywords(company_name, symbol)
                        }
                        
                        # Add keywords mapping
                        for keyword in self.company_data[symbol]['keywords']:
                            self.keywords[keyword.lower()] = symbol
            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")

    def _generate_keywords(self, company_name: str, symbol: str) -> List[str]:
        """Generate keywords for a company"""
        keywords = set()
        
        # Add the symbol
        keywords.add(symbol)
        
        # Add the full company name
        keywords.add(company_name)
        
        # Add name without common corporate suffixes
        name_without_suffix = re.sub(r'\s+(Inc\.?|Corp\.?|Ltd\.?|Group|Corporation|Limited)$', '', company_name, flags=re.IGNORECASE)
        keywords.add(name_without_suffix)
        
        # Add first word (usually the main company name)
        first_word = company_name.split()[0]
        keywords.add(first_word)
        
        return list(keywords)

    def match_company(self, query: str, threshold: int = 80) -> Optional[Tuple[str, str, int]]:
        """
        Match a company name or symbol to its ticker symbol
        Returns: Tuple of (symbol, company_name, match_score) or None if no match found
        """
        query = query.strip()
        
        # Check for exact symbol match first
        if query.upper() in self.company_data:
            return (query.upper(), self.company_data[query.upper()]['name'], 100)
        
        # Check for exact keyword match (case insensitive)
        query_lower = query.lower()
        if query_lower in self.keywords:
            symbol = self.keywords[query_lower]
            return (symbol, self.company_data[symbol]['name'], 100)
        
        # Try fuzzy matching
        best_match = None
        highest_score = 0
        
        for symbol, data in self.company_data.items():
            # Check symbol match
            symbol_score = fuzz.ratio(query.upper(), symbol)
            
            # Check company name match
            name_score = fuzz.partial_ratio(query.lower(), data['name'].lower())
            
            # Check keyword matches
            keyword_scores = [fuzz.partial_ratio(query.lower(), k.lower()) for k in data['keywords']]
            best_keyword_score = max(keyword_scores) if keyword_scores else 0
            
            # Use the highest score among symbol, name, and keywords
            score = max(symbol_score, name_score, best_keyword_score)
            
            if score > highest_score:
                highest_score = score
                best_match = (symbol, data['name'], score)
        
        if best_match and best_match[2] >= threshold:
            return best_match
            
        return None

    def search_companies(self, query: str, limit: int = 5, threshold: int = 60) -> List[Tuple[str, str, int]]:
        """
        Search for companies matching the query
        Returns: List of (symbol, company_name, match_score) tuples
        """
        matches = []
        for symbol, data in self.company_data.items():
            score = max(
                fuzz.ratio(query.upper(), symbol),
                fuzz.partial_ratio(query.lower(), data['name'].lower()),
                max(fuzz.partial_ratio(query.lower(), k.lower()) for k in data['keywords'])
            )
            if score >= threshold:
                matches.append((symbol, data['name'], score))
        
        # Sort by score descending and return top matches
        return sorted(matches, key=lambda x: x[2], reverse=True)[:limit]
