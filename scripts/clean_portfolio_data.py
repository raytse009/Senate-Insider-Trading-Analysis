import pandas as pd
import re


def clean_amount_ranges():
    print("🧹 Opening scoped baseline dataset...")
    df = pd.read_csv("scoped_portfolio_disclosures.csv")

    print(f"📊 Scoped Rows to Process: {len(df)}")

    # Clean explicit missing values
    df = df.dropna(subset=['Ticker', 'Amount Range', 'Type'])
    df['Type'] = df['Type'].astype(str).str.strip().str.upper()

    def parse_amounts(amount_str):
        if pd.isna(amount_str):
            return 0, 0, 0

        clean_str = str(amount_str).replace('$', '').replace(',', '').lower().strip()

        if 'over' in clean_str or 'more than' in clean_str:
            numbers = [int(s) for s in re.findall(r'\d+', clean_str)]
            low = numbers[0] if numbers else 0
            high = low * 2
            return low, high, (low + high) / 2

        numbers = [int(s) for s in re.findall(r'\d+', clean_str)]
        if len(numbers) == 2:
            low, high = numbers[0], numbers[1]
            return low, high, (low + high) / 2
        elif len(numbers) == 1:
            return numbers[0], numbers[0], numbers[0]
        else:
            return 0, 0, 0

    print("🧮 Converting string brackets to numeric metrics...")
    bounds = df['Amount Range'].apply(parse_amounts)
    df['Min Amount'] = [b[0] for b in bounds]
    df['Max Amount'] = [b[1] for b in bounds]
    df['Midpoint Amount'] = [b[2] for b in bounds]

    # Process Transaction Date
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='mixed', errors='coerce')
    df = df.dropna(subset=['Transaction Date'])

    print("\n" + "=" * 50)
    print("✨ DATA CLEANING COMPLETED SUCCESSFULLY")
    print("=" * 50)
    print(f"• Final Valid Scoped Rows Saved: {len(df):,}")
    print(f"• Financial Column Generated:    [Midpoint Amount]")
    print("=" * 50)

    df.to_csv("cleaned_portfolio_final.csv", index=False)
    print("📁 Production file exported successfully: 'cleaned_portfolio_final.csv'\n")


if __name__ == "__main__":
    clean_amount_ranges()