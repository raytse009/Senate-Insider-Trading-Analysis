import requests
import pandas as pd
import urllib.request
import re

HOUSE_API_URL = "https://raw.githubusercontent.com/timothycarambat/house-stock-watcher-data/master/data/all_transactions.json"
SENATE_API_URL = "https://raw.githubusercontent.com/timothycarambat/senate-stock-watcher-data/master/aggregate/all_transactions.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def run_scoped_data_pipeline():
    print("🚀 Booting Capstone Data Retrieval Pipeline...")

    # ---- STEP 1: FETCH ACTIVE S&P 500 CONSTRAINTS ----
    print("🌐 Fetching dynamic S&P 500 validation index from Wikipedia...")
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html_content = urllib.request.urlopen(req).read().decode('utf-8')

        tickers = re.findall(r'<td><a [^>]*rel="nofollow"[^>]*>([A-Z\.]+)</a[^>]*>', html_content)
        if not tickers:
            tickers = re.findall(r'class="external text"[^>]*>([A-Z\.]+)</a[^>]*>', html_content)

        sp500_universe = set(sym.replace('.', '-').strip().upper() for sym in tickers if len(sym) <= 5)

        if len(sp500_universe) < 400:
            raise ValueError("Ticker list extraction returned incomplete results.")

        print(f"✔ Successfully cached {len(sp500_universe)} target S&P 500 tickers.")
    except Exception as e:
        print(f"❌ Failed to parse S&P 500 index matrix: {e}")
        return None

    # ---- STEP 2: DOWNLOAD PUBLIC SOURCE DATA VIA CDN MIRRORS ----
    # Fix for House Extraction (parsing multi-line text blocks)
    try:
        print("📥 Requesting House disclosure repository...")
        response = requests.get(HOUSE_API_URL, headers=HEADERS, timeout=15)

        # Try a safe fallback if the file is stacked sequentially
        try:
            df_house = pd.DataFrame(response.json())
        except Exception:
            # This line handles the "Extra data" bug by reading objects sequentially
            import json
            raw_text = response.text.strip()

            # If the file format uses newline delimiters, split and load them
            lines = raw_text.split('\n')
            records = []
            for line in lines:
                if line.strip():
                    try:
                        # Handle individual array extractions or dictionary elements
                        obj = json.loads(line.strip())
                        if isinstance(obj, list):
                            records.extend(obj)
                        else:
                            records.append(obj)
                    except json.JSONDecodeError:
                        continue
            df_house = pd.DataFrame(records)

        print(f"✔ Successfully bypassed JSON bug! Downloaded {len(df_house)} raw House records.")
    except Exception as e:
        print(f"⚠️ House repository error or empty response: {e}")
        df_house = pd.DataFrame()

    try:
        print("📥 Requesting Senate disclosure repository...")
        response = requests.get(SENATE_API_URL, headers=HEADERS, timeout=15)
        df_senate = pd.DataFrame(response.json())
        print(f"✔ Downloaded {len(df_senate)} raw Senate records.")
    except Exception as e:
        print(f"⚠️ Senate repository error or empty response: {e}")
        df_senate = pd.DataFrame()

    # ---- STEP 3: CONSOLIDATE & MAP TO TARGET SCHEMA ----
    mapped_blocks = []

    if not df_house.empty:
        house_mapped = pd.DataFrame({
            'Ticker': df_house.get('ticker', None),
            'Asset Name': df_house.get('asset_description', None),
            'Transaction Date': df_house.get('transaction_date', None),
            'Disclosure Date': df_house.get('disclosure_date', None),
            'Type': df_house.get('type', None),
            'Amount Range': df_house.get('amount', None),
            'Insider Title': 'Representative'
        })
        mapped_blocks.append(house_mapped)

    if not df_senate.empty:
        senate_mapped = pd.DataFrame({
            'Ticker': df_senate.get('ticker', None),
            'Asset Name': df_senate.get('asset_description', None),
            'Transaction Date': df_senate.get('transaction_date', None),
            # Fill with Transaction Date as a fallback proxy since disclosure is omitted in this repo
            'Disclosure Date': df_senate.get('transaction_date', None),
            'Type': df_senate.get('type', None),
            'Amount Range': df_senate.get('amount', None),
            'Insider Title': 'Senator'
        })
        mapped_blocks.append(senate_mapped)

    if not mapped_blocks:
        print("❌ Pipeline Critical Error: Zero source records available.")
        return None

    raw_combined = pd.concat(mapped_blocks, ignore_index=True)
    total_downloaded = len(raw_combined)

    # ---- STEP 4: APPLY SCOPE FILTER CONSTRAINT ----
    print("🧹 Cleaning Phase: Stripping transactions outside the S&P 500 index universe...")
    raw_combined['Ticker'] = raw_combined['Ticker'].astype(str).str.strip().str.upper().str.replace('.', '-',
                                                                                                    regex=False)
    scoped_df = raw_combined[raw_combined['Ticker'].isin(sp500_universe)].copy()

    # ---- STEP 5: OUTPUT PIPELINE SUMMARY METRICS ----
    dropped_rows = total_downloaded - len(scoped_df)
    print("\n" + "=" * 50)
    print("✨ DATA RETRIEVAL PIPELINE METRICS")
    print("=" * 50)
    print(f"• Total Raw Database Records Downloaded:  {total_downloaded:,}")
    print(f"• Out-of-Scope Rows Removed:              {dropped_rows:,}")
    print(f"• Preserved Scoped Core Dataset Rows:     {len(scoped_df):,}")
    print("=" * 50)

    scoped_df.to_csv("scoped_portfolio_disclosures.csv", index=False)
    print("📁 Data structured and cached to local environment: 'scoped_portfolio_disclosures.csv'\n")
    return scoped_df


# ---- THE MAIN ENTRY POINT FUNCTION ----
def main():
    # This explicit call forces Python to run the function and flush text to the console
    run_scoped_data_pipeline()


if __name__ == "__main__":
    main()