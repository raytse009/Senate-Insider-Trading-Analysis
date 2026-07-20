import pandas as pd
import yfinance as yf
import numpy as np


def run_price_correlation():
    print("📖 Loading cleaned production dataset...")
    df = pd.read_csv("cleaned_portfolio_final.csv")

    # Filter for Purchases to measure investment performance cleanly
    df_buys = df[df['Type'].astype(str).str.upper().str.contains('PURCHASE')].copy()

    if df_buys.empty:
        print("⚠️ No direct Purchase records found to correlate performance against.")
        return

    # Isolate the top 5 most heavily traded stocks from your visual analysis
    top_tickers = df_buys.groupby('Ticker')['Midpoint Amount'].sum().sort_values(ascending=False).head(5).index.tolist()
    print(f"🎯 Target Focus Group (Top 5 Tickers by Volume): {top_tickers}")

    # Filter dataset down to just these focus tickers
    df_focus = df_buys[df_buys['Ticker'].isin(top_tickers)].copy()
    print(f"📊 Rows matching focus criteria: {len(df_focus)}")

    # Standardize dates to datetime64[ns]
    df_focus['Transaction Date'] = pd.to_datetime(df_focus['Transaction Date'])

    trade_prices = []
    future_prices = []
    spy_returns = []

    print("⚡ Fetching historical market data and calculating market alpha...")

    # Pre-fetch S&P 500 data benchmark (SPY). Make its index timezone-naive to match our data.
    spy = yf.Ticker("SPY")
    spy_hist = spy.history(start=df_focus['Transaction Date'].min() - pd.Timedelta(days=10),
                           end=df_focus['Transaction Date'].max() + pd.Timedelta(days=110))
    if spy_hist.index.tz is not None:
        spy_hist.index = spy_hist.index.tz_localize(None)

    # Loop over every single trade execution
    for idx, row in df_focus.iterrows():
        ticker = row['Ticker']
        t_date = row['Transaction Date']
        f_date = t_date + pd.Timedelta(days=90)

        try:
            stock = yf.Ticker(ticker)
            stock_hist = stock.history(start=t_date - pd.Timedelta(days=10), end=f_date + pd.Timedelta(days=10))

            if stock_hist.empty:
                trade_prices.append(np.nan)
                future_prices.append(np.nan)
                spy_returns.append(np.nan)
                continue

            # Strip timezones from the stock history index to ensure a clean match
            if stock_hist.index.tz is not None:
                stock_hist.index = stock_hist.index.tz_localize(None)

            # Use look-back matching to find the closest valid trading day closing price
            stock_t = stock_hist.asof(t_date)
            stock_f = stock_hist.asof(f_date)

            spy_t = spy_hist.asof(t_date)
            spy_f = spy_hist.asof(f_date)

            # Safely extract close prices from the Series objects
            p_trade = stock_t['Close'] if isinstance(stock_t, pd.Series) or hasattr(stock_t, '__getitem__') else np.nan
            p_future = stock_f['Close'] if isinstance(stock_f, pd.Series) or hasattr(stock_f, '__getitem__') else np.nan
            s_trade = spy_t['Close'] if isinstance(spy_t, pd.Series) or hasattr(spy_t, '__getitem__') else np.nan
            s_future = spy_f['Close'] if isinstance(spy_f, pd.Series) or hasattr(spy_f, '__getitem__') else np.nan

            if not np.isnan([p_trade, p_future, s_trade, s_future]).any():
                trade_prices.append(p_trade)
                future_prices.append(p_future)
                spy_ret = (s_future - s_trade) / s_trade
                spy_returns.append(spy_ret)
            else:
                trade_prices.append(np.nan)
                future_prices.append(np.nan)
                spy_returns.append(np.nan)

        except Exception as e:
            # Print the error if an unexpected problem occurs during processing
            print(f"❌ Error matching ticker {ticker} on row {idx}: {e}")
            trade_prices.append(np.nan)
            future_prices.append(np.nan)
            spy_returns.append(np.nan)

    # Inject calculations into the dataframe
    df_focus['Stock Price at Trade'] = trade_prices
    df_focus['Stock Price 90D Later'] = future_prices
    df_focus['Market (SPY) 90D Return'] = spy_returns

    # Drop rows where look-ups failed
    df_focus = df_focus.dropna(subset=['Stock Price at Trade', 'Stock Price 90D Later'])

    if df_focus.empty:
        print("\n❌ All rows dropped after data alignment. Check terminal error log outputs.")
        return

    df_focus['Stock 90D Return'] = (df_focus['Stock Price 90D Later'] - df_focus['Stock Price at Trade']) / df_focus[
        'Stock Price at Trade']
    df_focus['Abnormal Alpha Return'] = df_focus['Stock 90D Return'] - df_focus['Market (SPY) 90D Return']

    print("\n" + "=" * 60)
    print("🏆 INSIDER INVESTMENT OVER-PERFORMANCE (90-DAY WINDOW)")
    print("=" * 60)

    # Aggregate calculations
    summary = df_focus.groupby('Ticker').agg(
        Total_Trades=('Ticker', 'count'),
        Avg_Stock_Return=('Stock 90D Return', lambda x: f"{x.mean() * 100:.2f}%"),
        Avg_Market_Return=('Market (SPY) 90D Return', lambda x: f"{x.mean() * 100:.2f}%"),
        Net_Abnormal_Alpha=('Abnormal Alpha Return', lambda x: f"{x.mean() * 100:+.2f}%"),
        # Measures consistency: tighter dispersion indicates reliable outperformance
        Alpha_Std_Dev=('Abnormal Alpha Return', lambda x: f"{x.std() * 100:.2f}%" if len(x) > 1 else "0.00%")
    ).reset_index()

    print(summary.to_string(index=False))
    print("=" * 60)

    df_focus.to_csv("insider_price_correlation.csv", index=False)
    print("📁 Mathematical matrix cached to: 'insider_price_correlation.csv'\n")


if __name__ == "__main__":
    run_price_correlation()