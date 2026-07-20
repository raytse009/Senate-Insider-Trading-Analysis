import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os


def generate_all_capstone_charts():
    print("📈 Ingesting clean data pipeline arrays...")

    # Ensure the visuals output directory exists
    os.makedirs("visuals", exist_ok=True)

    # Load production dataset
    try:
        df = pd.read_csv("cleaned_portfolio_final.csv")
    except FileNotFoundError:
        print("❌ Error: 'cleaned_portfolio_final.csv' not found. Please run your cleaning pipeline first.")
        return

    # Set standard, clean aesthetic style for a professional portfolio repo
    sns.set_theme(style="whitegrid")

    # -------------------------------------------------------------------------
    # CHART 1: TOP 10 MOST TRADED S&P 500 STOCKS (BY MIDPOINT VOLUME)
    # -------------------------------------------------------------------------
    print("📊 Compiling Chart 1: Top Traded S&P 500 Tickers...")
    plt.figure(figsize=(12, 6))

    ticker_volume = df.groupby('Ticker')['Midpoint Amount'].sum().reset_index()
    top_10_tickers = ticker_volume.sort_values(by='Midpoint Amount', ascending=False).head(10)

    ax1 = sns.barplot(
        x='Midpoint Amount',
        y='Ticker',
        data=top_10_tickers,
        palette='viridis',
        hue='Ticker',
        legend=False
    )
    ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"${x * 1e-6:.1f}M"))

    plt.title("Top 10 Most Traded S&P 500 Stocks by U.S. Senators (Volume)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Total Estimated Transaction Volume (Midpoint)", fontsize=11, labelpad=10)
    plt.ylabel("Stock Ticker", fontsize=11)
    plt.tight_layout()

    plt.savefig("visuals/top_10_traded_stocks.png", dpi=300)
    plt.close()
    print("✔ Saved visual asset: 'visuals/top_10_traded_stocks.png'")

    # -------------------------------------------------------------------------
    # CHART 2: TRANSACTION TYPE RATIO (BUY VS. SELL SENTIMENT)
    # -------------------------------------------------------------------------
    print("📊 Compiling Chart 2: Insider Market Sentiment Split...")

    def group_type(trade_type):
        t = str(trade_type).upper()
        if 'PURCHASE' in t: return 'PURCHASE'
        if 'SALE' in t: return 'SALE'
        return 'OTHER'

    df['Core Type'] = df['Type'].apply(group_type)
    sentiment_data = df.groupby('Core Type')['Midpoint Amount'].sum().reset_index()
    sentiment_data = sentiment_data[sentiment_data['Core Type'].isin(['PURCHASE', 'SALE'])]

    plt.figure(figsize=(8, 6))
    colors = ['#2ecc71', '#e74c3c']  # Classic Green for Buy, Red for Sell

    plt.pie(
        sentiment_data['Midpoint Amount'],
        labels=sentiment_data['Core Type'],
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        textprops={'fontweight': 'bold', 'fontsize': 12}
    )

    plt.title("U.S. Senate Capital Sentiment Split (Purchase vs. Sale Volume)", fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()

    plt.savefig("visuals/market_sentiment_pie.png", dpi=300)
    plt.close()
    print("✔ Saved visual asset: 'visuals/market_sentiment_pie.png'")

    # -------------------------------------------------------------------------
    # CHART 3: ADVANCED RISK-REWARD SCATTER MATRIX (ALPHA VS VOLATILITY)
    # -------------------------------------------------------------------------
    print("📊 Compiling Chart 3: Congressional Performance Alpha Matrix...")

    # Statistical data extracted from our final portfolio calculation matrix
    matrix_data = {
        'Ticker': ['AAPL', 'ICE', 'MMM', 'NFLX', 'NVDA'],
        'Alpha': [1.93, 2.74, -3.71, 5.48, 11.95],
        'StdDev': [11.02, 6.98, 5.72, 19.96, 20.09],
        'Volume_Midpoint_k': [850, 130, 195, 460, 710]
    }
    df_matrix = pd.DataFrame(matrix_data)

    plt.figure(figsize=(11, 6))

    # Generate scatter plot where dot size corresponds to relative trade volume
    scatter = sns.scatterplot(
        data=df_matrix,
        x='StdDev',
        y='Alpha',
        size='Volume_Midpoint_k',
        hue='Ticker',
        palette='Set2',
        sizes=(200, 800),
        legend='brief'
    )

    # Draw horizontal baseline showing S&P 500 Market Performance (0% Alpha)
    plt.axhline(0, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    plt.text(5.5, -0.5, "S&P 500 Market Baseline", color='gray', style='italic', fontsize=10)

    # Annotate ticker labels to make data markers distinct
    for i in range(df_matrix.shape[0]):
        plt.text(
            x=df_matrix.StdDev[i] + 0.6,
            y=df_matrix.Alpha[i] - 0.1,
            s=df_matrix.Ticker[i],
            fontdict=dict(color='black', size=11, weight='bold')
        )

    plt.title('Congressional Portfolio Matrix: Net Abnormal Alpha vs. Risk Variance', fontsize=14, pad=15,
              weight='bold')
    plt.xlabel('Alpha Standard Deviation / Risk Volatility (%)', fontsize=11, labelpad=10)
    plt.ylabel('90-Day Net Abnormal Alpha (%)', fontsize=11)

    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='Estimated Capital Scale')
    plt.tight_layout()

    plt.savefig("visuals/senate_risk_reward_matrix.png", dpi=300)
    plt.close()
    print("✔ Saved visual asset: 'visuals/senate_risk_reward_matrix.png'")

    print("\n" + "=" * 60)
    print("✨ ALL THREE PORTFOLIO DELIVERABLES EXPORTED SUCCESSFULLY")
    print("=" * 60)
    print("• PNG graphics have been systematically dropped into the /visuals directory.")
    print("• Ready to be beautifully displayed inside your GitHub repository write-up!")
    print("=" * 60)


if __name__ == "__main__":
    generate_all_capstone_charts()