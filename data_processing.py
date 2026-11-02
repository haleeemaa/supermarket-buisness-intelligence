
import pandas as pd


# ==========================================
# 1. LOAD AND CLEAN DATASET
# ==========================================

def load_and_clean_data(uploaded_file):

    """
    Loads and cleans the UCI Online Retail dataset.
    """

    # Read uploaded file
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)

    elif file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    else:
        raise ValueError(
            "Please upload an Excel or CSV file."
        )

    # Remove spaces from column names
    df.columns = df.columns.str.strip()
    # Standardise column names for Online Retail I and II

    df.columns = df.columns.astype(str).str.strip()

    column_mapping = {
    "Invoice": "InvoiceNo",
    "Price": "UnitPrice",
    "Customer ID": "CustomerID"
    }

    df = df.rename(columns=column_mapping)
    # Check required columns
    required_columns = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Convert columns into correct data types
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)

    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="coerce"
    )

    df["UnitPrice"] = pd.to_numeric(
        df["UnitPrice"],
        errors="coerce"
    )

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        errors="coerce"
    )

    # Remove rows with missing important information
    df = df.dropna(
        subset=[
            "InvoiceNo",
            "Description",
            "Quantity",
            "UnitPrice",
            "InvoiceDate"
        ]
    )

    # Remove cancelled transactions
    df = df[
        ~df["InvoiceNo"].str.startswith("C", na=False)
    ]

    # Remove invalid quantities and prices
    df = df[
        (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
    ]

    # Clean product descriptions
    df["Description"] = (
        df["Description"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Remove empty descriptions
    df = df[
        df["Description"] != ""
    ]

    # Calculate revenue for each transaction row
    df["Revenue"] = (
        df["Quantity"] * df["UnitPrice"]
    )

    # Extract date information
    df["Date"] = df["InvoiceDate"].dt.date

    df["Month"] = (
        df["InvoiceDate"]
        .dt.to_period("M")
        .astype(str)
    )

    df["Year"] = df["InvoiceDate"].dt.year

    df["Day"] = df["InvoiceDate"].dt.day_name()

    # Sort records by date
    df = df.sort_values(
        by="InvoiceDate"
    )

    df = df.reset_index(drop=True)

    return df


# ==========================================
# 2. OVERALL SALES SUMMARY
# ==========================================

def get_sales_summary(df):

    total_revenue = df["Revenue"].sum()

    total_orders = df["InvoiceNo"].nunique()

    unique_products = df["Description"].nunique()

    total_products_sold = df["Quantity"].sum()

    unique_customers = df["CustomerID"].nunique()

    average_order_value = (
        total_revenue / total_orders
        if total_orders > 0
        else 0
    )

    return {

        "total_revenue": total_revenue,

        "total_orders": total_orders,

        "unique_products": unique_products,

        "total_products_sold": total_products_sold,

        "unique_customers": unique_customers,

        "average_order_value": average_order_value

    }


# ==========================================
# 3. PRODUCT PERFORMANCE
# ==========================================

def get_product_sales(df):

    product_sales = (

        df.groupby("Description")

        .agg(

            Quantity_Sold=(
                "Quantity",
                "sum"
            ),

            Revenue=(
                "Revenue",
                "sum"
            ),

            Number_of_Orders=(
                "InvoiceNo",
                "nunique"
            )

        )

        .reset_index()

    )

    product_sales = product_sales.sort_values(
        by="Revenue",
        ascending=False
    )

    return product_sales


# ==========================================
# 4. MONTHLY SALES ANALYSIS
# ==========================================

def get_monthly_sales(df):

    monthly_sales = (

        df.groupby("Month")

        .agg(

            Revenue=(
                "Revenue",
                "sum"
            ),

            Orders=(
                "InvoiceNo",
                "nunique"
            ),

            Quantity_Sold=(
                "Quantity",
                "sum"
            )

        )

        .reset_index()

    )

    return monthly_sales


# ==========================================
# 5. COUNTRY-WISE SALES ANALYSIS
# ==========================================

def get_country_sales(df):

    country_sales = (

        df.groupby("Country")

        .agg(

            Revenue=(
                "Revenue",
                "sum"
            ),

            Orders=(
                "InvoiceNo",
                "nunique"
            )

        )

        .reset_index()

    )

    country_sales = country_sales.sort_values(
        by="Revenue",
        ascending=False
    )

    return country_sales


# ==========================================
# 6. DAILY SALES ANALYSIS
# ==========================================

def get_daily_sales(df):

    daily_sales = (

        df.groupby("Day")

        .agg(

            Revenue=(
                "Revenue",
                "sum"
            ),

            Orders=(
                "InvoiceNo",
                "nunique"
            )

        )

        .reset_index()

    )

    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    daily_sales["Day"] = pd.Categorical(
        daily_sales["Day"],
        categories=day_order,
        ordered=True
    )

    daily_sales = daily_sales.sort_values(
        "Day"
    )

    return daily_sales
