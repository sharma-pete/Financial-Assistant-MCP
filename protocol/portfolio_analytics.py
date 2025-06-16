from typing import Dict, List, Any, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3

class PortfolioAnalytics:
    def __init__(self, db_path='portfolio.db'):
        """Initialize PortfolioAnalytics with database path."""
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)

    def calculate_portfolio_risk_metrics(self, timeframe: str = '1y') -> Dict[str, Any]:
        """Calculate portfolio risk metrics."""
        days = self._convert_timeframe_to_days(timeframe)
        
        with self._get_connection() as conn:
            holdings_query = """
                SELECT h.Ticker, h.Quantity, h.Weight, p.Date, p.Close, p.Returns
                FROM portfolio h
                JOIN portfolio_prices p ON h.Ticker = p.Ticker
                WHERE p.Date >= date('now', ?)
                ORDER BY p.Date
            """
            
            portfolio_df = pd.read_sql_query(holdings_query, conn, params=[f'-{days} days'])
            
            portfolio_returns = self._calculate_portfolio_returns(portfolio_df)
            
            volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized volatility
            var_95 = np.percentile(portfolio_returns, 5)  # 95% VaR
            
            market_query = """
                SELECT Date, Returns as market_return
                FROM portfolio_prices
                WHERE Ticker = 'SPY'
                AND Date >= date('now', ?)
                ORDER BY Date
            """
            
            market_returns = pd.read_sql_query(market_query, conn, params=[f'-{days} days'])
            market_returns = market_returns.set_index('Date')['market_return']
            
            common_dates = portfolio_returns.index.intersection(market_returns.index)
            portfolio_returns = portfolio_returns[common_dates]
            market_returns = market_returns[common_dates]
            
            covariance = np.cov(portfolio_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            beta = covariance / market_variance if market_variance != 0 else 0
            
            return {
                'volatility': float(volatility),
                'var_95': float(var_95),
                'beta': float(beta),
                'timeframe': timeframe
            }

    def analyze_sector_rotation(self, lookback_period: str = '1y') -> Dict[str, Any]:
        """Analyze sector rotation opportunities."""
        days = self._convert_timeframe_to_days(lookback_period)
        
        with self._get_connection() as conn:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            performance_query = """
                SELECT p.Date, h.Sector, AVG(p.Returns) as sector_return
                FROM portfolio_prices p
                JOIN portfolio h ON p.Ticker = h.Ticker
                WHERE p.Date >= ?
                GROUP BY p.Date, h.Sector
                ORDER BY p.Date
            """
            
            performance_df = pd.read_sql_query(performance_query, conn, params=[start_date])
            
            sector_momentum = self._calculate_sector_momentum(performance_df)
            
            rotation_opportunities = self._identify_rotation_opportunities(sector_momentum)
            
            sector_momentum_dict = {
                'sectors': sector_momentum.index.tolist(),
                'momentum': sector_momentum.values.tolist()
            }
            
            return {
                'sector_momentum': sector_momentum_dict,
                'rotation_opportunities': rotation_opportunities,
                'timeframe': lookback_period
            }

    def calculate_performance_attribution(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Break down portfolio performance into components.
        
        Args:
            start_date: Start date for attribution period
            end_date: End date for attribution period
            
        Returns:
            Dictionary containing performance attribution analysis
        """
        try:
            with self._get_connection() as conn:
                portfolio_query = """
                    SELECT p.Date, p.Ticker, p.Returns, h.Sector, h.Weight
                    FROM portfolio_prices p
                    JOIN portfolio h ON p.Ticker = h.Ticker
                    WHERE p.Date BETWEEN ? AND ?
                """
                portfolio_returns = pd.read_sql_query(portfolio_query, conn, params=(start_date, end_date))
                
                benchmark_query = """
                    SELECT Date, Returns
                    FROM sp500
                    WHERE Date BETWEEN ? AND ?
                """
                benchmark_returns = pd.read_sql_query(benchmark_query, conn, params=(start_date, end_date))
                
                factor_attribution = self._calculate_factor_attribution(portfolio_returns)
                sector_attribution = self._calculate_sector_attribution(portfolio_returns)
                stock_selection = self._calculate_stock_selection(portfolio_returns, benchmark_returns)
                
                return {
                    'factor_attribution': factor_attribution,
                    'sector_attribution': sector_attribution,
                    'stock_selection': stock_selection,
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
                
        except Exception as e:
            raise Exception(f"Error calculating performance attribution: {str(e)}")

    def analyze_portfolio_concentration(self) -> Dict[str, Any]:
        """
        Analyze portfolio concentration risks across sectors and individual holdings.
        
        Returns:
            Dictionary containing concentration analysis
        """
        try:
            with self._get_connection() as conn:
                sector_query = """
                    SELECT Sector, SUM(Weight) as sector_weight
                    FROM portfolio
                    GROUP BY Sector
                    ORDER BY sector_weight DESC
                """
                sector_concentration = pd.read_sql_query(sector_query, conn)
                
                stock_query = """
                    SELECT Ticker, Weight
                    FROM portfolio
                    ORDER BY Weight DESC
                """
                stock_concentration = pd.read_sql_query(stock_query, conn)
                
                sector_hhi = self._calculate_hhi(sector_concentration['sector_weight'])
                stock_hhi = self._calculate_hhi(stock_concentration['Weight'])
                
                return {
                    'sector_concentration': sector_concentration.to_dict('records'),
                    'stock_concentration': stock_concentration.to_dict('records'),
                    'sector_hhi': sector_hhi,
                    'stock_hhi': stock_hhi,
                    'top_sectors': sector_concentration.head(3).to_dict('records'),
                    'top_holdings': stock_concentration.head(5).to_dict('records')
                }
                
        except Exception as e:
            raise Exception(f"Error analyzing portfolio concentration: {str(e)}")

    def calculate_portfolio_efficiency(self, timeframe: str = '1y') -> Dict[str, Any]:
        """
        Calculate portfolio efficiency metrics including Sharpe ratio and information ratio.
        
        Args:
            timeframe: Time period for calculation (e.g., '1y', '6m', '3m')
            
        Returns:
            Dictionary containing efficiency metrics
        """
        try:
            days = self._convert_timeframe_to_days(timeframe)
            
            with self._get_connection() as conn:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                returns_query = """
                    SELECT p.Date, p.Ticker, p.Returns, h.Weight
                    FROM portfolio_prices p
                    JOIN portfolio h ON p.Ticker = h.Ticker
                    WHERE p.Date >= ?
                """
                returns_df = pd.read_sql_query(returns_query, conn, params=(start_date.strftime('%Y-%m-%d'),))
                
                risk_free_rate = 0.05  # This should be fetched from a data source
                
                portfolio_returns = self._calculate_portfolio_returns(returns_df)
                excess_returns = portfolio_returns - risk_free_rate/252  # Daily risk-free rate
                
                sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std()
                information_ratio = self._calculate_information_ratio(portfolio_returns, returns_df)
                
                return {
                    'sharpe_ratio': sharpe_ratio,
                    'information_ratio': information_ratio,
                    'annualized_return': portfolio_returns.mean() * 252,
                    'annualized_volatility': portfolio_returns.std() * np.sqrt(252),
                    'timeframe': timeframe
                }
                
        except Exception as e:
            raise Exception(f"Error calculating portfolio efficiency: {str(e)}")

    def analyze_market_correlation(self, timeframe: str = '1y') -> Dict[str, Any]:
        """
        Analyze portfolio correlation with major market indices.
        
        Args:
            timeframe: Time period for analysis (e.g., '1y', '6m', '3m')
            
        Returns:
            Dictionary containing correlation analysis
        """
        try:
            days = self._convert_timeframe_to_days(timeframe)
            
            with self._get_connection() as conn:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                portfolio_query = """
                    SELECT p.Date, p.Ticker, p.Returns, h.Weight
                    FROM portfolio_prices p
                    JOIN portfolio h ON p.Ticker = h.Ticker
                    WHERE p.Date >= ?
                """
                portfolio_returns = pd.read_sql_query(portfolio_query, conn, params=(start_date.strftime('%Y-%m-%d'),))
                
                indices = ['sp500', 'dow_jones', 'nasdaq']
                correlations = {}
                
                for index in indices:
                    index_query = f"""
                        SELECT Date, Returns
                        FROM {index}
                        WHERE Date >= ?
                    """
                    index_returns = pd.read_sql_query(index_query, conn, params=(start_date.strftime('%Y-%m-%d'),))
                    
                    correlation = self._calculate_correlation(portfolio_returns, index_returns)
                    correlations[index] = correlation
                
                return {
                    'correlations': correlations,
                    'timeframe': timeframe
                }
                
        except Exception as e:
            raise Exception(f"Error analyzing market correlation: {str(e)}")

    def calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio metrics including returns, risk, and efficiency.
        
        Returns:
            Dictionary containing portfolio metrics
        """
        try:
            with self._get_connection() as conn:
                portfolio_query = "SELECT Ticker, Quantity, Close, Weight FROM portfolio"
                portfolio_df = pd.read_sql_query(portfolio_query, conn)
                
                
                total_value = (portfolio_df['Quantity'] * portfolio_df['Close']).sum()
                
                sector_query = """
                    SELECT Sector, SUM(Weight) as sector_weight
                    FROM portfolio
                    GROUP BY Sector
                """
                sector_allocation = pd.read_sql_query(sector_query, conn)
                
                num_holdings = len(portfolio_df)
                
                avg_position_size = total_value / num_holdings
                
                return {
                    'total_value': total_value,
                    'num_holdings': num_holdings,
                    'avg_position_size': avg_position_size,
                    'sector_allocation': sector_allocation.to_dict('records'),
                    'top_holdings': portfolio_df.nlargest(5, 'Weight').to_dict('records')
                }
                
        except Exception as e:
            raise Exception(f"Error calculating portfolio metrics: {str(e)}")

    def _convert_timeframe_to_days(self, timeframe: str) -> int:
        """Convert timeframe string to number of days."""
        unit = timeframe[-1].lower()
        value = int(timeframe[:-1])
        
        if unit == 'y':
            return value * 365
        elif unit == 'm':
            return value * 30
        elif unit == 'w':
            return value * 7
        elif unit == 'd':
            return value
        else:
            raise ValueError(f"Invalid timeframe unit: {unit}")

    def _calculate_portfolio_returns(self, returns_df: pd.DataFrame, portfolio_df: pd.DataFrame = None) -> pd.Series:
        """Calculate portfolio returns."""
        if portfolio_df is not None:
            returns_df['weighted_return'] = returns_df['Returns'] * returns_df['Weight']
            return returns_df.groupby('Date')['weighted_return'].sum()
        else:
            returns_df['weighted_return'] = returns_df['Returns'] * returns_df['Weight']
            return returns_df.groupby('Date')['weighted_return'].sum()

    def _calculate_beta(self, portfolio_returns: pd.Series, prices_df: pd.DataFrame) -> float:
        """Calculate portfolio beta."""
        market_returns = prices_df.groupby('Date')['Returns'].mean()
        covariance = np.cov(portfolio_returns, market_returns)[0,1]
        market_variance = np.var(market_returns)
        return covariance / market_variance

    def _calculate_tracking_error(self, portfolio_returns: pd.Series, prices_df: pd.DataFrame) -> float:
        """Calculate tracking error.""" 
        market_returns = prices_df.groupby('Date')['Returns'].mean()
        return np.std(portfolio_returns - market_returns) * np.sqrt(252)

    def _calculate_information_ratio(self, portfolio_returns: pd.Series, returns_df: pd.DataFrame) -> float:
        """Calculate information ratio."""
        market_returns = returns_df.groupby('Date')['Returns'].mean()
        excess_returns = portfolio_returns - market_returns
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

    def _calculate_sector_momentum(self, sector_performance: pd.DataFrame) -> pd.DataFrame:
        """Calculate sector momentum."""
        return sector_performance.groupby('Sector')['sector_return'].mean().sort_values(ascending=False)

    def _identify_rotation_opportunities(self, sector_momentum: pd.DataFrame) -> List[Dict]:
        """Identify sector rotation opportunities."""
        opportunities = []
        for sector, momentum in sector_momentum.items():
            if momentum > 0:  # Example threshold
                opportunities.append({
                    'sector': sector,
                    'momentum': momentum,
                    'suggestion': 'Consider increasing allocation'
                })
        return opportunities

    def _calculate_factor_attribution(self, portfolio_returns: pd.DataFrame) -> Dict[str, float]:
        """Calculate factor attribution."""
        return {
            'market': portfolio_returns['Returns'].mean() * 0.6,
            'size': portfolio_returns['Returns'].mean() * 0.2,
            'value': portfolio_returns['Returns'].mean() * 0.2
        }

    def _calculate_sector_attribution(self, portfolio_returns: pd.DataFrame) -> Dict[str, float]:
        """Calculate sector attribution."""
        return portfolio_returns.groupby('Sector')['Returns'].mean().to_dict()

    def _calculate_stock_selection(self, portfolio_returns: pd.DataFrame, benchmark_returns: pd.DataFrame) -> float:
        """Calculate stock selection contribution."""
        portfolio_avg = portfolio_returns['Returns'].mean()
        benchmark_avg = benchmark_returns['Returns'].mean()
        return portfolio_avg - benchmark_avg

    def _calculate_hhi(self, weights: pd.Series) -> float:
        """Calculate Herfindahl-Hirschman Index."""
        return (weights ** 2).sum()

    def _calculate_correlation(self, portfolio_returns: pd.DataFrame, index_returns: pd.DataFrame) -> float:
        """Calculate correlation coefficient."""
        portfolio_avg = portfolio_returns.groupby('Date')['Returns'].mean()
        index_avg = index_returns.set_index('Date')['Returns']
        return portfolio_avg.corr(index_avg) 