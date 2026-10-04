## Problem Statement - QuantDB

Financial markets generate large volumes of structured data, including security information, historical market prices, trading volumes, orders, trades, portfolio positions, and strategy performance. Efficiently storing, managing, retrieving, and analyzing this data is essential for quantitative research and algorithmic trading.

However, conventional approaches that rely on scattered spreadsheets, CSV files, or independent analytical scripts make it difficult to maintain data consistency, efficiently retrieve historical information, track simulated trading activities, and evaluate trading strategies in an integrated manner. They also provide limited support for database-level operations such as constraints, normalization, indexing, transactions, concurrency control, and query optimization.

To address these challenges, *QuantDB* proposes a database-driven market data and algorithmic trading research platform that provides a centralized and structured system for managing financial market data and simulated trading activities.

The system will store and manage entities such as users, exchanges, securities, historical market data, orders, trades, portfolios, positions, trading strategies, and backtesting results using a relational database. It will provide meaningful SQL-based data retrieval and analysis through joins, aggregate functions, subqueries, views, and indexes, while demonstrating transaction management, constraints, triggers, stored procedures, and query optimization.

A user-friendly application interface will allow users to retrieve market information, analyze trading data, manage simulated orders and portfolios, execute historical backtests, and generate performance and risk reports. The analytical layer will further support quantitative metrics such as returns, volatility, Sharpe ratio, maximum drawdown, and basic market-microstructure analysis.

The primary objective of QuantDB is therefore to demonstrate how *database management principles can be applied to a realistic quantitative-finance problem*, while providing an integrated platform for market-data management, simulated trading, strategy evaluation, and quantitative analysis.