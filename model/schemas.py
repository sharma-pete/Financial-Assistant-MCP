from typing import List
from pydantic import BaseModel, Field

class GetStockPriceParams(BaseModel):
    """Parameters for getting stock prices."""
    tickers: List[str] = Field(description="List of stock ticker symbols")

class GetTotalPortfolioValueParams(BaseModel):
    """Parameters for getting total portfolio value."""
    pass

class GetInvestedSectorsParams(BaseModel):
    """Parameters for getting invested sectors."""
    pass

class GetSectorHoldingsParams(BaseModel):
    """Parameters for getting holdings for specific sectors."""
    sectors: List[str] = Field(description="List of sectors to get holdings for")

class CompareStocksParams(BaseModel):
    """Parameters for comparing two stocks."""
    stock1: str = Field(description="First stock ticker to compare")
    stock2: str = Field(description="Second stock ticker to compare")

class GetPortfolioSummaryParams(BaseModel):
    """Parameters for getting portfolio summary."""
    pass 

class PortfolioRiskMetricsParams(BaseModel):
    """Parameters for calculating portfolio risk metrics."""
    timeframe: str = Field(
        default="1y",
        description="Time period for risk calculation (e.g., '1y', '6m', '3m')"
    )

class SectorRotationParams(BaseModel):
    """Parameters for analyzing sector rotation."""
    lookback_period: str = Field(
        default="6m",
        description="Historical period to analyze (e.g., '1y', '6m')"
    )

class PerformanceAttributionParams(BaseModel):
    """Parameters for calculating performance attribution."""
    start_date: str = Field(description="Start date for attribution period (YYYY-MM-DD)")
    end_date: str = Field(description="End date for attribution period (YYYY-MM-DD)")

class PortfolioConcentrationParams(BaseModel):
    """Parameters for analyzing portfolio concentration."""
    pass

class PortfolioEfficiencyParams(BaseModel):
    """Parameters for calculating portfolio efficiency metrics."""
    timeframe: str = Field(
        default="1y",
        description="Time period for calculation (e.g., '1y', '6m', '3m')"
    )

class MarketCorrelationParams(BaseModel):
    """Parameters for analyzing market correlation."""
    timeframe: str = Field(
        default="1y",
        description="Time period for analysis (e.g., '1y', '6m', '3m')"
    )

class PortfolioMetricsParams(BaseModel):
    """Parameters for calculating comprehensive portfolio metrics."""
    pass 