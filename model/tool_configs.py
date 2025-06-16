from model.schemas import (
    GetStockPriceParams,
    GetTotalPortfolioValueParams,
    GetInvestedSectorsParams,
    GetSectorHoldingsParams,
    CompareStocksParams,
    GetPortfolioSummaryParams,
    PortfolioRiskMetricsParams,
    SectorRotationParams,
    PerformanceAttributionParams,
    PortfolioConcentrationParams,
    PortfolioEfficiencyParams,
    MarketCorrelationParams,
    PortfolioMetricsParams
)

def get_tool_configs(portfolio_services, portfolio_analytics):
    """Get tool configurations with portfolio services and analytics instances."""
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
        },
        "calculate_portfolio_risk_metrics": {
            "model": PortfolioRiskMetricsParams,
            "method": portfolio_analytics.calculate_portfolio_risk_metrics,
            "has_params": True
        },
        "analyze_sector_rotation": {
            "model": SectorRotationParams,
            "method": portfolio_analytics.analyze_sector_rotation,
            "has_params": True
        },
        "calculate_performance_attribution": {
            "model": PerformanceAttributionParams,
            "method": portfolio_analytics.calculate_performance_attribution,
            "has_params": True
        },
        "analyze_portfolio_concentration": {
            "model": PortfolioConcentrationParams,
            "method": lambda *args: portfolio_analytics.analyze_portfolio_concentration(),
            "has_params": False
        },
        "calculate_portfolio_efficiency": {
            "model": PortfolioEfficiencyParams,
            "method": portfolio_analytics.calculate_portfolio_efficiency,
            "has_params": True
        },
        "analyze_market_correlation": {
            "model": MarketCorrelationParams,
            "method": portfolio_analytics.analyze_market_correlation,
            "has_params": True
        },
        "calculate_portfolio_metrics": {
            "model": PortfolioMetricsParams,
            "method": lambda *args: portfolio_analytics.calculate_portfolio_metrics(),
            "has_params": False
        }
    } 