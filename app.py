
import streamlit as st
import pandas as pd

from data_processing import (
    load_and_clean_data,
    get_sales_summary,
    get_product_sales,
    get_monthly_sales,
    get_country_sales,
    get_daily_sales
)

from combo_mining import (
    create_basket,
    find_frequent_itemsets,
    find_rules,
    format_rules,
    format_combinations
)

from strategies import (
    create_strategy_report,
    get_strategy_summary
)


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Supermarket Business Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# 2. CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #10141e;
    color: #f1f5f9;
}

[data-testid="stSidebar"] {
    background-color: #171e2b;
}

[data-testid="stMetric"] {
    background-color: #1c2636;
    border: 1px solid #344155;
    padding: 18px;
    border-radius: 12px;
}

[data-testid="stMetricLabel"] {
    color: #aab7ca;
}

[data-testid="stMetricValue"] {
    color: #ffffff;
}

h1, h2, h3 {
    color: #f8fafc;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #344155;
    border-radius: 10px;
}

.stButton > button {
    background-color: #2d8c75;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 8px 18px;
}

.stButton > button:hover {
    background-color: #246d5d;
    color: white;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. TITLE
# ==========================================

st.title("🛒 Supermarket Business Intelligence")

st.markdown(
    "Understand your sales. Discover customer buying patterns. "
    "Make smarter business decisions."
)

st.divider()


# ==========================================
# 4. SIDEBAR
# ==========================================

st.sidebar.title("🛒 Store Manager")

st.sidebar.caption("BUSINESS ANALYTICS PLATFORM")

uploaded_file = st.sidebar.file_uploader(
    "Upload your retail dataset",
    type=["xlsx", "xls", "csv"]
)

st.sidebar.divider()


# ==========================================
# 5. DATASET UPLOAD
# ==========================================

if uploaded_file is None:

    st.subheader("Welcome to your business dashboard")

    st.write(
        "Upload your Online Retail dataset to begin "
        "analysing transactions and discovering useful business insights."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📊 Sales Analysis")
        st.write(
            "Track revenue, orders, sales trends and customer activity."
        )

    with col2:
        st.markdown("### 🛍️ Basket Analysis")
        st.write(
            "Discover which products customers frequently purchase together."
        )

    with col3:
        st.markdown("### 💡 Business Strategies")
        st.write(
            "Generate combo offers and cross-selling recommendations."
        )

    st.info(
        "Upload your Excel or CSV dataset using the sidebar to continue."
    )

    st.stop()


# ==========================================
# 6. LOAD AND CLEAN DATA
# ==========================================

@st.cache_data(show_spinner=False)
def process_dataset(file_bytes, file_name):

    import io

    file_object = io.BytesIO(file_bytes)
    file_object.name = file_name

    return load_and_clean_data(file_object)


try:

    with st.spinner("Loading and cleaning your dataset..."):

        df = process_dataset(
            uploaded_file.getvalue(),
            uploaded_file.name
        )

except Exception as error:

    st.error(f"Dataset loading failed: {error}")
    st.stop()


if df.empty:

    st.error("The uploaded dataset contains no valid transactions.")
    st.stop()


# ==========================================
# 7. SIDEBAR FILTERS
# ==========================================

st.sidebar.subheader("Analysis Filters")

countries = sorted(
    df["Country"].dropna().unique().tolist()
)

selected_countries = st.sidebar.multiselect(
    "Select countries",
    options=countries,
    default=countries
)

min_date = df["InvoiceDate"].min().date()
max_date = df["InvoiceDate"].max().date()

selected_dates = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)


filtered_df = df[
    df["Country"].isin(selected_countries)
].copy()


if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:

    start_date, end_date = selected_dates

    filtered_df = filtered_df[
        (filtered_df["InvoiceDate"].dt.date >= start_date)
        & (filtered_df["InvoiceDate"].dt.date <= end_date)
    ]


if filtered_df.empty:

    st.warning(
        "No transactions found for the selected filters."
    )

    st.stop()


st.sidebar.caption(
    f"{len(filtered_df):,} transaction records selected"
)


# ==========================================
# 8. NAVIGATION
# ==========================================

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Overview",
        "Sales Analysis",
        "Product Performance",
        "Products Bought Together",
        "Business Suggestions",
        "Download Reports"
    ]
)


# ==========================================
# 9. OVERVIEW DASHBOARD
# ==========================================

if page == "Overview":

    st.header("Business Overview")

    summary = get_sales_summary(filtered_df)

    st.caption(
        "A quick view of your store's overall performance."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Revenue",
        f"£{summary['total_revenue']:,.2f}"
    )

    col2.metric(
        "Total Orders",
        f"{summary['total_orders']:,}"
    )

    col3.metric(
        "Products Sold",
        f"{summary['total_products_sold']:,.0f}"
    )

    col4.metric(
        "Unique Customers",
        f"{summary['unique_customers']:,}"
    )

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Monthly Revenue")

        monthly = get_monthly_sales(filtered_df)

        if not monthly.empty:

            chart_data = monthly.set_index("Month")["Revenue"]

            st.line_chart(chart_data)

    with col2:

        st.subheader("Top Selling Products")

        products = get_product_sales(filtered_df)

        top_products = products.head(10)

        st.bar_chart(
            top_products.set_index("Description")["Quantity_Sold"]
        )

    st.divider()

    st.subheader("Store Insights")

    product_data = get_product_sales(filtered_df)

    if not product_data.empty:

        best_product = product_data.iloc[0]

        st.success(
            f"Your highest-revenue product is "
            f"{best_product['Description']}, "
            f"generating £{best_product['Revenue']:,.2f}."
        )

    st.info(
        "Use the navigation menu to explore detailed sales analysis, "
        "product combinations and business suggestions."
    )


# ==========================================
# 10. SALES ANALYSIS
# ==========================================

elif page == "Sales Analysis":

    st.header("Sales Analysis")

    summary = get_sales_summary(filtered_df)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Revenue",
        f"£{summary['total_revenue']:,.2f}"
    )

    col2.metric(
        "Average Order Value",
        f"£{summary['average_order_value']:,.2f}"
    )

    col3.metric(
        "Total Orders",
        f"{summary['total_orders']:,}"
    )

    st.divider()

    st.subheader("Monthly Revenue Trend")

    monthly = get_monthly_sales(filtered_df)

    if not monthly.empty:
        st.line_chart(
            monthly.set_index("Month")["Revenue"]
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Sales by Day of Week")

        daily = get_daily_sales(filtered_df)

        if not daily.empty:
            st.bar_chart(
                daily.set_index("Day")["Revenue"]
            )

    with col2:

        st.subheader("Orders by Day of Week")

        if not daily.empty:
            st.bar_chart(
                daily.set_index("Day")["Orders"]
            )

    st.divider()

    st.subheader("Country-wise Performance")

    country_data = get_country_sales(filtered_df)

    st.dataframe(
        country_data,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 11. PRODUCT PERFORMANCE
# ==========================================

elif page == "Product Performance":

    st.header("Product Performance")

    st.write(
        "Identify which products contribute most to sales "
        "and which products have lower sales."
    )

    product_data = get_product_sales(filtered_df)

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Top 10 Products by Revenue")

        top_revenue = product_data.head(10)

        st.bar_chart(
            top_revenue.set_index("Description")["Revenue"]
        )

    with col2:

        st.subheader("Top 10 Products by Quantity")

        top_quantity = product_data.sort_values(
            "Quantity_Sold",
            ascending=False
        ).head(10)

        st.bar_chart(
            top_quantity.set_index("Description")["Quantity_Sold"]
        )

    st.divider()

    st.subheader("Complete Product Performance")

    st.dataframe(
        product_data,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Lowest Selling Products")

    lowest_products = product_data.sort_values(
        "Quantity_Sold",
        ascending=True
    ).head(10)

    st.dataframe(
        lowest_products,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 12. PRODUCTS BOUGHT TOGETHER
# ==========================================

elif page == "Products Bought Together":

    st.header("🛍️ Products Bought Together")

    st.write(
        "Discover which products customers frequently "
        "purchase in the same shopping order."
    )

    st.info(
        "These findings can help identify potential combo offers "
        "and cross-selling opportunities."
    )

    st.subheader("Analysis Settings")

    col1, col2, col3 = st.columns(3)

    with col1:

        min_support = st.slider(
            "Minimum support",
            min_value=0.001,
            max_value=0.10,
            value=0.01,
            step=0.001,
            format="%.3f"
        )

    with col2:

        min_confidence = st.slider(
            "Minimum confidence",
            min_value=0.10,
            max_value=1.00,
            value=0.30,
            step=0.05
        )

    with col3:

        max_products = st.selectbox(
            "Products to analyse",
            [50, 100, 150, 200],
            index=1
        )

    st.caption(
        "Lower support and confidence values may reveal more results. "
        "Larger product selections may take longer to process."
    )

    if st.button("Analyse Shopping Baskets", type="primary"):

        with st.spinner(
            "Analysing customer shopping baskets. Please wait..."
        ):

            try:

                basket = create_basket(
                    filtered_df,
                    max_products=max_products
                )

                if basket.empty:

                    st.warning("No shopping baskets could be created.")

                else:

                    itemsets = find_frequent_itemsets(
                        basket,
                        min_support=min_support,
                        max_len=3
                    )

                    if itemsets.empty:

                        st.warning(
                            "No frequent products or combinations were found. "
                            "Try lowering the minimum support."
                        )

                    else:

                        # Frequently purchased combinations
                        combinations = format_combinations(itemsets)

                        st.subheader("Frequently Purchased Combinations")

                        if combinations.empty:

                            st.info(
                                "No combinations of multiple products were found. "
                                "Try lowering the minimum support."
                            )

                        else:

                            # IMPORTANT: Column name is Support, not support
                            combinations["Orders containing combination (%)"] = (
                                combinations["Support"] * 100
                            ).round(2)

                            st.dataframe(
                                combinations[
                                    [
                                        "Product Combination",
                                        "Orders containing combination (%)"
                                    ]
                                ],
                                use_container_width=True,
                                hide_index=True
                            )

                            csv = combinations.to_csv(
                                index=False
                            ).encode("utf-8")

                            st.download_button(
                                "Download Product Combinations",
                                csv,
                                "product_combinations.csv",
                                "text/csv"
                            )

                        # Association rules
                        rules = find_rules(
                            itemsets,
                            min_confidence=min_confidence
                        )

                        st.divider()

                        st.subheader("Product Recommendations")

                        if rules.empty:

                            st.warning(
                                "No recommendations meet the selected settings. "
                                "Try lowering minimum confidence or support."
                            )

                        else:

                            formatted_rules = format_rules(rules)

                            display_rules = formatted_rules.copy()

                            # IMPORTANT: Use the actual capitalised column names
                            display_rules["Orders containing both (%)"] = (
                                display_rules["Support"] * 100
                            ).round(2)

                            display_rules["Buying likelihood (%)"] = (
                                display_rules["Confidence"] * 100
                            ).round(2)

                            st.dataframe(
                                display_rules[
                                    [
                                        "Products Bought First",
                                        "Products Recommended",
                                        "Orders containing both (%)",
                                        "Buying likelihood (%)",
                                        "Lift"
                                    ]
                                ],
                                use_container_width=True,
                                hide_index=True
                            )

                            rules_csv = formatted_rules.to_csv(
                                index=False
                            ).encode("utf-8")

                            st.download_button(
                                "Download Association Rules",
                                rules_csv,
                                "association_rules.csv",
                                "text/csv"
                            )

                        with st.expander("Understand these results"):

                            st.markdown("""
                            **Support:** The proportion of all analysed
                            orders containing the product combination.

                            **Confidence:** Among orders containing the first
                            product or products, the proportion that also contain
                            the recommended product or products.

                            **Lift:** How much more often the products appear
                            together compared with what would be expected if
                            their purchases were independent.

                            - Lift greater than 1: Positive association.
                            - Lift equal to 1: No association.
                            - Lift below 1: Negative association.
                            """)

            except Exception as error:

                st.error(
                    f"Basket analysis failed: {error}"
                )


# ==========================================
# 13. BUSINESS SUGGESTIONS
# ==========================================

elif page == "Business Suggestions":

    st.header("💡 Business Suggestions")

    st.write(
        "Turn customer buying patterns into practical "
        "business opportunities."
    )

    st.info(
        "Suggestions are based on historical purchase patterns. "
        "Test promotions before investing heavily in them."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        min_support = st.slider(
            "Minimum support",
            0.001,
            0.10,
            0.01,
            0.001,
            format="%.3f",
            key="strategy_support"
        )

    with col2:

        min_confidence = st.slider(
            "Minimum confidence",
            0.10,
            1.00,
            0.30,
            0.05,
            key="strategy_confidence"
        )

    with col3:

        max_products = st.selectbox(
            "Products to analyse",
            [50, 100, 150, 200],
            index=1,
            key="strategy_products"
        )

    if st.button(
        "Generate Business Suggestions",
        type="primary"
    ):

        with st.spinner("Generating business suggestions..."):

            try:

                basket = create_basket(
                    filtered_df,
                    max_products=max_products
                )

                itemsets = find_frequent_itemsets(
                    basket,
                    min_support=min_support,
                    max_len=3
                )

                rules = find_rules(
                    itemsets,
                    min_confidence=min_confidence
                )

                formatted_rules = format_rules(rules)

                recommendations = create_strategy_report(
                    formatted_rules
                )

                if not recommendations:

                    st.warning(
                        "No suggestions were generated. "
                        "Try lowering the analysis settings."
                    )

                else:

                    strategy_summary = get_strategy_summary(
                        recommendations
                    )

                    st.subheader("Business Opportunity Overview")

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Total Suggestions",
                        strategy_summary["total_suggestions"]
                    )

                    col2.metric(
                        "Combo Offers",
                        strategy_summary["combo_offers"]
                    )

                    col3.metric(
                        "Cross-Selling",
                        strategy_summary["cross_selling"]
                    )

                    col4.metric(
                        "Product Placement",
                        strategy_summary["product_placement"]
                    )

                    st.divider()

                    st.subheader("Recommended Business Actions")

                    for index, item in enumerate(
                        recommendations,
                        start=1
                    ):

                        with st.expander(
                            f"{index}. {item['Strategy']} — {item['Products']}",
                            expanded=(index == 1)
                        ):

                            st.write(
                                "**What the data shows:** "
                                + item["What the data shows"]
                            )

                            st.success(
                                "**Suggested action:** "
                                + item["Suggested action"]
                            )

                            st.write(
                                "**Why try it?** "
                                + item["Why try it"]
                            )

                            st.write(
                                "**How to measure success:** "
                                + item["How to measure success"]
                            )

                            col1, col2, col3 = st.columns(3)

                            col1.metric(
                                "Support",
                                f"{item['Orders containing both (%)']}%"
                            )

                            col2.metric(
                                "Confidence",
                                f"{item['Buying likelihood (%)']}%"
                            )

                            col3.metric(
                                "Lift",
                                item["Lift"]
                            )

                    report = pd.DataFrame(recommendations)

                    report_csv = report.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        "Download Business Strategy Report",
                        report_csv,
                        "business_strategy_report.csv",
                        "text/csv"
                    )

            except Exception as error:

                st.error(
                    f"Unable to generate suggestions: {error}"
                )


# ==========================================
# 14. DOWNLOAD REPORTS
# ==========================================

elif page == "Download Reports":

    st.header("📥 Download Business Reports")

    st.write(
        "Download your analysed data for further examination "
        "or presentation."
    )

    product_data = get_product_sales(filtered_df)

    monthly_data = get_monthly_sales(filtered_df)

    country_data = get_country_sales(filtered_df)

    st.subheader("Available Reports")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### Product Performance")

        st.write(
            "Product-wise quantities sold, revenue and order counts."
        )

        st.download_button(
            "Download Product Report",
            product_data.to_csv(index=False).encode("utf-8"),
            "product_performance.csv",
            "text/csv"
        )

        st.markdown("### Monthly Sales")

        st.write(
            "Monthly revenue, order counts and quantities sold."
        )

        st.download_button(
            "Download Monthly Sales",
            monthly_data.to_csv(index=False).encode("utf-8"),
            "monthly_sales.csv",
            "text/csv"
        )

    with col2:

        st.markdown("### Country-wise Sales")

        st.write(
            "Revenue and order performance by country."
        )

        st.download_button(
            "Download Country Report",
            country_data.to_csv(index=False).encode("utf-8"),
            "country_sales.csv",
            "text/csv"
        )

        st.markdown("### Cleaned Transaction Data")

        st.write(
            "Download the cleaned transaction records."
        )

        st.download_button(
            "Download Cleaned Dataset",
            filtered_df.to_csv(index=False).encode("utf-8"),
            "cleaned_retail_data.csv",
            "text/csv"
        )


# ==========================================
# 15. FOOTER
# ==========================================

st.sidebar.divider()

st.sidebar.caption(
    "Supermarket Business Intelligence"
)

st.sidebar.caption(
    "Retail Analytics | Market Basket Analysis | Apriori"
)

st.caption(
    "Supermarket Business Intelligence Assistant | "
    "Academic Data Mining Project"
)
