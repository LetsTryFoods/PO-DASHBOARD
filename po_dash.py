# app.py

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Import only the main function from your processing module
from processing import get_final_po_data

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
        # Assuming get_final_po_data is defined elsewhere and returns a DataFrame
        df = get_final_po_data()
        # Ensure 'APPOINTMENT DATE' is datetime
        if 'APPOINTMENT DATE' in df.columns:
            df['APPOINTMENT DATE'] = pd.to_datetime(df['APPOINTMENT DATE'])
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
    The output is encoded to UTF-8.
    """
    return df.to_csv(index=False).encode('utf-8')


# --- Main Application Logic ---
final_data_df = load_data()

if final_data_df is not None:
    if not final_data_df.empty:
        st.success("Data loaded and processed successfully!")
        
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
                st.dataframe(open_pos_df)
                
                csv_open_pos = convert_df_to_csv(open_pos_df)
                st.download_button(
                    label="Download Open POs as CSV",
                    data=csv_open_pos,
                    file_name='open_purchase_orders.csv',
                    mime='text/csv',
                    key='download-open-pos'
                )
        else:
            st.warning("Could not find 'APPOINTMENT DATE' data or it's not in a date format to calculate Open POs.")
    
        st.markdown("---")

        # --- Display Data Table ---
        st.header("Consolidated Purchase Order Data")
        
        csv_all_data = convert_df_to_csv(final_data_df)
        st.download_button(
             label="Download All Data as CSV",
             data=csv_all_data,
             file_name='consolidated_purchase_orders.csv',
             mime='text/csv',
             key='download-all-data'
        )
        
        st.dataframe(final_data_df)

        # --- Sidebar Filtering Logic ---
        st.sidebar.header("Filter Data")
        
        # Filter by Platform
        platforms = sorted(final_data_df['Platform'].dropna().unique())
        selected_platform = st.sidebar.multiselect("Platform", platforms, default=[])

        # Filter by City
        cities = sorted(final_data_df['City'].dropna().unique())
        selected_city = st.sidebar.multiselect("City", cities, default=[])

        # ✨ NEW: Filter by SKU
        products = sorted(final_data_df['SKU'].dropna().unique())
        print(products)
        selected_product = st.sidebar.multiselect("SKU", products, default=[])     

        # --- Filtered View Logic ---
        # Start with a copy of the original dataframe
        filtered_df = final_data_df.copy()

        # Apply filters only if a selection has been made in the corresponding multiselect
        if selected_platform:
            filtered_df = filtered_df[filtered_df['Platform'].isin(selected_platform)]
        if selected_city:
            filtered_df = filtered_df[filtered_df['City'].isin(selected_city)]
        if selected_product:
            filtered_df = filtered_df[filtered_df['SKU'].isin(selected_product)]
        
        # ✨ NEW: Display the filtered view only if at least one filter is active
        if selected_platform or selected_city or selected_product:
            st.markdown("---")
            st.header("Filtered View")
            st.write(f"Showing {len(filtered_df)} rows based on your selection.")

            csv_filtered_data = convert_df_to_csv(filtered_df)
            st.download_button(
                label="Download Filtered Data as CSV",
                data=csv_filtered_data,
                file_name='filtered_purchase_orders.csv',
                mime='text/csv',
                key='download-filtered-data'
            )

            st.dataframe(filtered_df)

    else:
        st.warning("The loaded data is empty after processing. Please check your data sources.")
else:
    st.info("Awaiting data load. If an error message is displayed above, please resolve it.")
