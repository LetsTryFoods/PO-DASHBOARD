import os
import pandas as pd
import re

# --- City Name Standardization ---
CITY_MAPPING = {
    # Ahmedabad
    'AHMEDABAD': 'Ahmedabad',
    # Ballabhgarh
    'BALLABHGARH': 'Ballabhgarh', 'BALLABHGRAH': 'Ballabhgarh', 'BHALLABHGRAH': 'Ballabhgarh',
    # Bangalore
    'BANGALORE': 'Bangalore', 'BANGLORE': 'Bangalore', 'BANGLORE (B3)': 'Bangalore',
    'BANGLORE (B4)': 'Bangalore', 'BANGLORE (MBI)': 'Bangalore', 'BANGLORE (MBL)': 'Bangalore',
    # Bilaspur
    'BILASPUR': 'Bilaspur', 'BILASPIUR': 'Bilaspur',
    # Bohrakalan
    'BOHRAKALAN': 'Bohrakalan',
    # Bhubaneswar
    'BHUVNESHAWAR': 'Bhubaneswar', 'BHUVNESHWAR': 'Bhubaneswar',
    # Chennai
    'CHENNAI': 'Chennai', 'CHENNAI (C5)': 'Chennai', 'CHENNIAI': 'Chennai',
    # Coimbatore
    'COIMBATORE': 'Coimbatore',
    # Delhi
    'DELHI': 'Delhi', 'DEHRADUN': 'Dehradun',
    # Gurgaon
    'GURGAON': 'Gurgaon', 'G7': 'Gurgaon',
    # Guwahati
    'GUWAHATI': 'Guwahati',
    # Ghaziabad
    'GAZIABAD': 'Ghaziabad', 'GHAZIABAD': 'Ghaziabad',
    # Hyderabad
    'HYDERABAD': 'Hyderabad', 'HYDERABAD (CHC)': 'Hyderabad', 'HYDERABAD (CHM)': 'Hyderabad',
    'HYDERABAD H3': 'Hyderabad', 'HYDERBAD': 'Hyderabad',
    # Jhajjar
    'JHAJJAR': 'Jhajjar', 'JHAJAR': 'Jhajjar', 'JHAJJAR2': 'Jhajjar', 'JHAJJHAR 2': 'Jhajjar',
    # Kolkata
    'KOLKATA': 'Kolkata',
    # Kundli
    'KUNDLI': 'Kundli',
    # Lucknow
    'LUCKNOW': 'Lucknow',
    # Mohali
    'MOHALI': 'Mohali',
    # Mumbai
    'MUMBAI': 'Mumbai', 'MUMBAI (M10)': 'Mumbai', 'MUMBAI (M11)': 'Mumbai', 'MUMBAI (M9)': 'Mumbai',
    # Noida
    'NOIDA': 'Noida', 'GAUTAM BUDH NAGAR': 'Noida',
    # Pune
    'PUNE': 'Pune',
    # Rajpura
    'RAJPUJRA': 'Rajpura', 'RAJPURA': 'Rajpura',
    # Visakhapatnam
    'VISHAKHAPATNAM': 'Visakhapatnam',
    # Unmapped but standardized from your list
    'BHOPAL': 'Bhopal', 'GOA': 'Goa', 'HAPUR': 'Hapur', 'INDORE': 'Indore', 'JAIPUR': 'Jaipur',
    'KERALA': 'Kerala', 'LUDHIANA': 'Ludhiana', 'LUHARI': 'Luhari', 'NAGPUR': 'Nagpur',
    'PATNA': 'Patna', 'RANCHI': 'Ranchi', 'SURAT': 'Surat', 'VARANASI': 'Varanasi',
    'VIJAYAWADA': 'Vijayawada'
}

def _standardize_city_name(city: str) -> str:
    """
    Cleans and standardizes a city name using the mapping.
    """
    if not isinstance(city, str):
        return city
    
    cleaned_city = city.strip()
    return CITY_MAPPING.get(cleaned_city.upper(), cleaned_city.title())

# --- SKU Name Standardization ---
def _standardize_sku_name(sku: str) -> str:
    """
    Cleans and standardizes a product (SKU) name by removing weight suffixes.
    It specifically excludes products containing 'Rusk' or 'Cookies' from cleaning.
    """
    if not isinstance(sku, str):
        return sku

    # If the name contains these keywords, return it without changes.
    exceptions = ['Rusk', 'Cookies']
    if any(exception in sku for exception in exceptions):
        return sku

    # Patterns to find and remove from the end of the string
    # This covers cases like " 150g", " 150 G", " 28", "(Pouch)" etc.
    patterns_to_remove = [
        re.compile(r'\s+\d+\s*g$', re.IGNORECASE),
        re.compile(r'\s+\d+\s*G$', re.IGNORECASE),
        re.compile(r'\s+\d+$'),
        re.compile(r'\s*\(Pouch\)$', re.IGNORECASE)
    ]
    
    cleaned_sku = sku
    for pattern in patterns_to_remove:
        cleaned_sku = pattern.sub('', cleaned_sku)
        
    return cleaned_sku.strip()


def _process_main_po_data() -> pd.DataFrame:
    """
    Fetches and processes PO data from multiple Google Sheet GIDs.
    """
    SHEET_ID = os.getenv("MAIN_PO_SHEET")
    SHEET_GIDS = {
        "Blinkit": os.getenv("GID_FOR_BLINKIT"),
        "Swiggy": os.getenv("GID_FOR_SWIGGY"),
        "Big Basket": os.getenv("GID_FOR_BIGBASKET"),
        "Flipkart": os.getenv("GID_FOR_FLIPKART"),
        "Zepto": os.getenv("GID_FOR_ZEPTO"),
    }
    SHEET_NAMES = ["Blinkit", "Swiggy", "Big Basket", "Flipkart", "Zepto"]

    all_data = []
    for sheet in SHEET_NAMES:
        gid = SHEET_GIDS.get(sheet)
        if not gid:
            print(f"Warning: GID for sheet '{sheet}' not found. Skipping.")
            continue
        
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        print(f"Processing sheet: {sheet}")

        try:
            if sheet == "Zepto":
                df_raw = pd.read_csv(csv_url, header=None)
                df_raw.drop(columns=[0], inplace=True)
                df_raw.columns = range(df_raw.shape[1])
                df_raw.drop(index=[0], inplace=True)
                df_raw = df_raw.iloc[:-2]
                df_fixed_part = df_raw.iloc[:, :4].copy()
                df_dynamic_part = df_raw.iloc[:, 4:].copy()
                df_fixed_part.drop(index=[1, 3], inplace=True)
                date_row, city_row, po_row = df_dynamic_part.iloc[0], df_dynamic_part.iloc[1], df_dynamic_part.iloc[2]
                df_dynamic_data = df_dynamic_part.iloc[3:].copy()
                df_fixed_data = df_fixed_part.iloc[1:].copy()
                merged_columns = [f"{date_row.get(col, '')} | {city_row.get(col, '')} | {po_row.get(col, '')}" for col in df_dynamic_part.columns]
                df_dynamic_data.columns = merged_columns
                df_fixed_data.columns = ['SKU Code', 'SKU', 'Grammage', 'Cases']
                id_vars = ['SKU Code', 'SKU', 'Grammage', 'Cases']
            else:
                df_raw = pd.read_csv(csv_url, header=None)
                df_raw.drop(index=[0], inplace=True)
                df_raw = df_raw.iloc[:-2]
                df_fixed_part = df_raw.iloc[:, :4].copy()
                df_dynamic_part = df_raw.iloc[:, 4:].copy()
                df_fixed_part.drop(index=[1, 3], inplace=True)
                date_row, city_row, po_row = df_dynamic_part.iloc[0], df_dynamic_part.iloc[1], df_dynamic_part.iloc[2]
                df_dynamic_data = df_dynamic_part.iloc[3:].copy()
                df_fixed_data = df_fixed_part.iloc[1:].copy()
                merged_columns = [f"{date_row.get(col, '')} | {city_row.get(col, '')} | {po_row.get(col, '')}" for col in df_dynamic_part.columns]
                df_dynamic_data.columns = merged_columns
                df_fixed_data.columns = ['Item Code', 'SKU', 'Grammage', 'Cases']
                id_vars = ['Item Code', 'SKU', 'Grammage', 'Cases']

            combined_df = pd.concat([df_fixed_data.reset_index(drop=True), df_dynamic_data.reset_index(drop=True)], axis=1)
            df_melted = combined_df.melt(id_vars=id_vars, var_name='MergedCol', value_name='Quantity')
            df_melted[['Date', 'City/Platform', 'PO Number']] = df_melted['MergedCol'].str.split(" \| ", expand=True)
            df_melted.drop(columns=['MergedCol'], inplace=True)
            df_melted = df_melted[~((df_melted['Date'] == '') & (df_melted['City/Platform'] == '') & (df_melted['PO Number'] == ''))]
            df_melted['City/Platform'] = df_melted['City/Platform'].replace('Ballbhgarh//Zepto', 'Ballabhgarh/Zepto')
            df_melted[['City', 'Platform']] = df_melted['City/Platform'].str.split("/", expand=True, n=1)
            df_melted['Platform']=sheet
            df_melted['City'] = df_melted['City'].apply(_standardize_city_name)
            df_melted['Date'] = pd.to_datetime(df_melted['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            df_melted['Quantity'] = pd.to_numeric(df_melted['Quantity'], errors='coerce')

            # ✨ NEW: Filter out rows with 0, negative, or invalid quantities ✨
            df_melted.dropna(subset=['Quantity'], inplace=True) # Remove rows with non-numeric quantities
            df_melted = df_melted[df_melted['Quantity'] > 0].copy() # Keep only rows with a quantity greater than 0

            if 'Item Code' in df_melted.columns:
                df_melted.rename(columns={'Item Code': 'SKU Code'}, inplace=True)
            final_df = df_melted[['SKU Code', 'SKU', 'City', 'Platform', 'Date', 'PO Number', 'Quantity']].copy()
            final_df.dropna(subset=['SKU Code', 'City', 'Platform', 'Date', 'PO Number'], inplace=True)
            final_df['PO Number'] = final_df['PO Number'].astype(str).str.strip()

            # Apply the SKU standardization function to the 'SKU' column
            if 'SKU' in final_df.columns:
                final_df['SKU'] = final_df['SKU'].apply(_standardize_sku_name)
            
            all_data.append(final_df)
        except Exception as e:
            print(f"❌ Error processing sheet '{sheet}': {e}")
            
    if not all_data:
        return pd.DataFrame()
    return pd.concat(all_data, ignore_index=True)


def _fetch_and_clean_po_details() -> pd.DataFrame:
    """
    Fetches and cleans the PO Details file from a specified Google Sheet.
    """
    sheet_id = os.getenv("SEC_PO_SHEET")
    gid = os.getenv("GID_SEC_PO")
    if not sheet_id or not gid:
        raise ValueError("SEC_PO_SHEET and GID_SEC_PO environment variables must be set.")
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        df_details = pd.read_csv(csv_url)
    except Exception as e:
        raise ConnectionError(f"Could not load PO Details from Google Sheets: {e}")

    df_details.rename(columns={'PO No.': 'PO Number', 'PO Value':'PO VALUE'}, inplace=True, errors='ignore')

    if 'PO Number' not in df_details.columns:
        raise ValueError("Critical Error: 'PO Number' column is missing in the PO Details file.")

    columns_to_keep = ['PO Number', 'DISPATCH DATE', 'APPOINTMENT DATE', 'LEAD TIME','PO VALUE', 'PO INVOICE']
    existing_columns_to_keep = [col for col in columns_to_keep if col in df_details.columns]
    
    df_cleaned = df_details[existing_columns_to_keep].copy()
    
    #   Convert date columns to datetime objects 
    for date_col in ['DISPATCH DATE', 'APPOINTMENT DATE']:
        if date_col in df_cleaned.columns:
            df_cleaned[date_col] = pd.to_datetime(df_cleaned[date_col], errors='coerce')

    df_cleaned['PO Number'] = df_cleaned['PO Number'].astype(str).str.strip()
    df_cleaned.drop_duplicates(subset=['PO Number'], inplace=True)
    
    return df_cleaned


def get_final_po_data() -> pd.DataFrame:
    """
    The main function to be called by the app. It orchestrates the entire
    data loading, processing, and merging pipeline.
    """
    print("Processing main PO sheets...")
    main_po_df = _process_main_po_data()
    if main_po_df.empty:
        print("Warning: Main PO data is empty. Returning an empty DataFrame.")
        return pd.DataFrame()

    print("Fetching PO details...")
    details_df = _fetch_and_clean_po_details()
    if details_df.empty:
        print("Warning: PO details sheet is empty. Returning data without details.")
        return main_po_df

    print("Merging data...")
    merged_df = pd.merge(
        main_po_df,
        details_df,
        on='PO Number',
        how='left'
    )
    
    print("✅ Data processing complete.")
    return merged_df

def format_df_for_display(df):
    """
    Creates a copy of the dataframe and formats date columns to 'YYYY-MM-DD' strings for clean display.
    """
    df_display = df.copy()
    for col in ['Date', 'DISPATCH DATE', 'APPOINTMENT DATE']:
        if col in df_display.columns and pd.api.types.is_datetime64_any_dtype(df_display[col]):
            df_display[col] = df_display[col].dt.strftime('%Y-%m-%d')
    return df_display