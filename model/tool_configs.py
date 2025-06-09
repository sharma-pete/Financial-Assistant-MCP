from model.schemas import (
    GetStockPriceParams,
    GetTotalPortfolioValueParams,
    GetInvestedSectorsParams,
    GetSectorHoldingsParams,
    CompareStocksParams,
    GetPortfolioSummaryParams
)

def get_tool_configs(portfolio_services):
    """Get tool configurations with portfolio services instance."""
    return {
        "get_stock_price": {
            "model": GetStockPriceParams,
            "method": portfolio_services.get_stock_price,
            "has_params": True
        },
        "get_total_portfolio_value": {
            "model": GetTotalPortfolioValueParams,
            "method": lambda *args: portfolio_services.get_total_portfolio_value(),
            "has_params": False
        },
        "get_invested_sectors": {
            "model": GetInvestedSectorsParams,
            "method": lambda *args: portfolio_services.get_invested_sectors(),
            "has_params": False
        },
        "get_sector_holdings": {
            "model": GetSectorHoldingsParams,
            "method": portfolio_services.get_sector_holdings,
            "has_params": True
        },
        "compare_stocks": {
            "model": CompareStocksParams,
            "method": portfolio_services.compare_stocks,
            "has_params": True
        },
        "get_portfolio_summary": {
            "model": GetPortfolioSummaryParams,
            "method": lambda *args: portfolio_services.get_portfolio_summary(),
            "has_params": False
        }
    } 