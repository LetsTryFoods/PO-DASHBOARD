# app.py

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Import only the main function from your processing module
from processing import get_final_po_data, format_df_for_display

# --- Page Configuration ---
st.set_page_config(page_title="PO Dashboard", layout="wide")
st.title("Purchase Orders Dashboard")

# --- Load Environment Variables ---
load_dotenv()

# --- Caching Data Loading ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_data():
    """
    A simple wrapper to call the main data processing function.
    This allows us to cache the results and handle errors gracefully in the UI.
    """
    try:
        df = get_final_po_data()
        # Ensure all potential date columns are converted to datetime
        for col in ['Date', 'DISPATCH DATE', 'APPOINTMENT DATE']:
             if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except (ValueError, ConnectionError) as e:
        st.error(f"An error occurred during data processing: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred. Please contact support.")
        print(f"Unexpected error in load_data: {e}")
        return None

# --- Caching function to convert DataFrame to CSV ---
@st.cache_data
def convert_df_to_csv(df):
    """
    Converts a DataFrame to a CSV string, which is essential for the download button.
    """
    return df.to_csv(index=False).encode('utf-8')


## --- Main Application Logic ---
final_data_df = load_data()

if final_data_df is not None:
    if not final_data_df.empty:
        st.success("Data loaded and processed successfully!")
        
        # --- Sidebar Filtering Logic ---
        st.sidebar.header("Filter Data")
        
        platforms = sorted(final_data_df['Platform'].dropna().unique())
        selected_platform = st.sidebar.multiselect("Platform", platforms, default=[])

        cities = sorted(final_data_df['City'].dropna().unique())
        selected_city = st.sidebar.multiselect("City", cities, default=[])

        products = sorted(final_data_df['SKU'].dropna().unique())
        selected_product = st.sidebar.multiselect("SKU", products, default=[])     

        st.sidebar.markdown("---")
        
        date_column_options = ['Date', 'DISPATCH DATE', 'APPOINTMENT DATE']
        available_date_columns = [col for col in date_column_options if col in final_data_df.columns and not final_data_df[col].isnull().all()]
        
        if available_date_columns:
            selected_date_column = st.sidebar.radio(
                "Choose a date column to filter by:",
                available_date_columns,
                key='date_column_selection'
            )

            min_date = final_data_df[selected_date_column].min().date()
            max_date = final_data_df[selected_date_column].max().date()

            selected_date_range = st.sidebar.date_input(
                f"Filter by {selected_date_column}",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key='date_range_selector'
            )
        else:
            st.sidebar.warning("No valid date columns found for filtering.")
            selected_date_column = None
            selected_date_range = ()

        # --- Apply Filters ---
        filtered_df = final_data_df.copy()

        if selected_date_column and len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
            filtered_df = filtered_df[
                (filtered_df[selected_date_column].dt.date >= start_date) &
                (filtered_df[selected_date_column].dt.date <= end_date)
            ]

        if selected_platform:
            filtered_df = filtered_df[filtered_df['Platform'].isin(selected_platform)]
        if selected_city:
            filtered_df = filtered_df[filtered_df['City'].isin(selected_city)]
        if selected_product:
            filtered_df = filtered_df[filtered_df['SKU'].isin(selected_product)]
        
        # --- Open POs Section ---
        st.header("Open POs Summary")
    
        current_date = pd.to_datetime('today').normalize()
    
        if 'APPOINTMENT DATE' in final_data_df.columns and pd.api.types.is_datetime64_any_dtype(final_data_df['APPOINTMENT DATE']):
            open_pos_df = final_data_df[
                final_data_df['APPOINTMENT DATE'] >= current_date
            ].copy()
    
            open_po_count = open_pos_df['PO Number'].nunique()
            open_po_quantity = int(open_pos_df['Quantity'].sum())
    
            col1_open, col2_open, col3_open = st.columns(3)
            col1_open.metric("Number of Open POs", f"{open_po_count:,}")
            col2_open.metric("Total Open Quantity", f"{open_po_quantity:,}")
            col3_open.metric("Total Open Value", "₹ N/A", help="PO value cannot be calculated without SKU price data.")
    
            with st.expander("View Details of Open Purchase Orders"):
                # ✨ CHANGED: Use the formatting function before displaying ✨
                st.dataframe(format_df_for_display(open_pos_df))
                
                csv_open_pos = convert_df_to_csv(open_pos_df)
                st.download_button(
                    label="Download Open POs as CSV",
                    data=csv_open_pos,
                    file_name='open_purchase_orders.csv',
                    mime='text/csv',
                    key='download-open-pos'
                )
        else:
            st.warning("Could not find 'APPOINTMENT DATE' data to calculate Open POs.")
    
        st.markdown("---")

        # --- Display Data Table ---
        st.header("Consolidated & Filtered Purchase Order Data")
        st.write(f"Displaying {len(filtered_df)} rows based on your filters.")

        csv_filtered_data = convert_df_to_csv(filtered_df)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv_filtered_data,
            file_name='filtered_purchase_orders.csv',
            mime='text/csv',
            key='download-filtered-data'
        )

        # ✨ CHANGED: Use the formatting function before displaying ✨
        st.dataframe(format_df_for_display(filtered_df))

    else:
        st.warning("The loaded data is empty after processing. Please check your data sources.")
else:
    st.info("Awaiting data load. If an error message is displayed above, please resolve it.")
