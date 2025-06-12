import sqlite3
from typing import List, Dict, Tuple, Union
import pandas as pd
from model.embeddings import IntentEmbeddings

class PortfolioServices:
    def __init__(self, db_path='portfolio.db'):
        """Initialize PortfolioServices with database path."""
        self.db_path = db_path
        self.embeddings = IntentEmbeddings()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)

    def get_stock_price(self, tickers: Union[str, List[str]]) -> Dict[str, float]:
        """
        Get the current price of one or multiple stocks.
        
        Args:
            tickers: Single ticker string or list of ticker symbols
            
        Returns:
            Dictionary mapping ticker symbols to their prices
        """
        if isinstance(tickers, str):
            tickers = [tickers]
            
        with self._get_connection() as conn:
            prices = {}
            for ticker in tickers:
                query = "SELECT Ticker, Close FROM portfolio WHERE Ticker = ?"
                result = pd.read_sql_query(query, conn, params=(ticker,))
                if not result.empty:
                    prices[ticker] = float(result['Close'].iloc[0])
                else:
                    prices[ticker] = None
            
        return prices

    def get_total_portfolio_value(self) -> float:
        """
        Calculate the total value of the portfolio.
        
        Returns:
            Total portfolio value
        """
        with self._get_connection() as conn:
            query = "SELECT SUM(Quantity * Close) as total_value FROM portfolio"
            result = pd.read_sql_query(query, conn)
            return float(result['total_value'].iloc[0])

    def get_invested_sectors(self) -> List[str]:
        """
        Get a list of all sectors in the portfolio.
        
        Returns:
            List of unique sectors
        """
        with self._get_connection() as conn:
            query = "SELECT DISTINCT Sector FROM portfolio ORDER BY Sector"
            result = pd.read_sql_query(query, conn)
            return result['Sector'].tolist()

    def get_sector_holdings(self, sectors: Union[str, List[str]]) -> Dict[str, Dict]:
        """
        Get holdings information for specified sectors with improved confidence handling.
        
        Args:
            sectors: Single sector string or list of sectors
            
        Returns:
            Dictionary with sector information including total value and stocks
        """
        if isinstance(sectors, str):
            sectors = [sectors]
            
        with self._get_connection() as conn:
            holdings = {}
            for sector in sectors:
                canonical_sector, similarity = self.embeddings.find_canonical_sector(sector)
                
                if similarity >= 0.3:
                    query = """
                        SELECT 
                            Ticker,
                            Quantity,
                            Close,
                            (Quantity * Close) as Value,
                            Weight
                        FROM portfolio 
                        WHERE Sector = ?
                    """
                    result = pd.read_sql_query(query, conn, params=(canonical_sector,))
                    
                    if not result.empty:
                        holdings[sector] = {
                            'total_value': float(result['Value'].sum()),
                            'stocks': result.to_dict('records'),
                            'weight': float(result['Weight'].sum()),
                            'matched_sector': canonical_sector,
                            'similarity': similarity,
                            'confidence': 'high'
                        }
                    else:
                        holdings[sector] = None
                
                elif similarity >= 0.15:
                    query = """
                        SELECT 
                            Ticker,
                            Quantity,
                            Close,
                            (Quantity * Close) as Value,
                            Weight
                        FROM portfolio 
                        WHERE Sector = ?
                    """
                    result = pd.read_sql_query(query, conn, params=(canonical_sector,))
                    
                    if not result.empty:
                        holdings[sector] = {
                            'total_value': float(result['Value'].sum()),
                            'stocks': result.to_dict('records'),
                            'weight': float(result['Weight'].sum()),
                            'matched_sector': canonical_sector,
                            'similarity': similarity,
                            'confidence': 'medium',
                            'suggestion': f"I assume you meant the {canonical_sector} sector. Here are the holdings:"
                        }
                    else:
                        holdings[sector] = None
                
                else:
                    top_sectors = self.embeddings.find_closest_sectors(sector, top_k=3)
                    suggestions = [s['canonical'] for s in top_sectors] if top_sectors else []
                    
                    holdings[sector] = {
                        'error': 'low_confidence',
                        'similarity': similarity,
                        'suggestions': suggestions,
                        'message': f"Could not confidently match '{sector}'. Did you mean one of these sectors: {', '.join(suggestions)}?"
                    }
                    
        return holdings

    def compare_stocks(self, stock1: str, stock2: str) -> Dict:
        """
        Compare two stocks in the portfolio.
        
        Args:
            stock1: First stock ticker
            stock2: Second stock ticker
            
        Returns:
            Dictionary containing comparison metrics
        """
        with self._get_connection() as conn:
            query = "SELECT * FROM portfolio WHERE Ticker IN (?, ?)"
            result = pd.read_sql_query(query, conn, params=(stock1, stock2))
            
            if len(result) != 2:
                return {"error": "One or both stocks not found in portfolio"}
            
            stock1_data = result[result['Ticker'] == stock1].iloc[0]
            stock2_data = result[result['Ticker'] == stock2].iloc[0]
            
            comparison = {
                'price_comparison': {
                    stock1: float(stock1_data['Close']),
                    stock2: float(stock2_data['Close']),
                    'difference': float(stock1_data['Close'] - stock2_data['Close'])
                },
                'sector_comparison': {
                    stock1: stock1_data['Sector'],
                    stock2: stock2_data['Sector']
                },
                'weight_comparison': {
                    stock1: float(stock1_data['Weight']),
                    stock2: float(stock2_data['Weight']),
                    'difference': float(stock1_data['Weight'] - stock2_data['Weight'])
                },
                'value_comparison': {
                    stock1: float(stock1_data['Quantity'] * stock1_data['Close']),
                    stock2: float(stock2_data['Quantity'] * stock2_data['Close'])
                }
            }
            
            return comparison

    def get_portfolio_summary(self) -> Dict:
        """
        Get a comprehensive summary of the portfolio.
        
        Returns:
            Dictionary containing portfolio metrics
        """
        with self._get_connection() as conn:
            total_value = self.get_total_portfolio_value()
            
            sector_query = """
                SELECT 
                    Sector,
                    SUM(Quantity * Close) as sector_value,
                    SUM(Weight) as sector_weight
                FROM portfolio 
                GROUP BY Sector
                ORDER BY sector_value DESC
            """
            sector_allocation = pd.read_sql_query(sector_query, conn)
            
            holdings_query = """
                SELECT 
                    Ticker,
                    Sector,
                    Quantity,
                    Close,
                    (Quantity * Close) as Value,
                    Weight
                FROM portfolio 
                ORDER BY Value DESC 
                LIMIT 5
            """
            top_holdings = pd.read_sql_query(holdings_query, conn)
            
            return {
                'total_value': total_value,
                'sector_allocation': sector_allocation.to_dict('records'),
                'top_holdings': top_holdings.to_dict('records')
            }
