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