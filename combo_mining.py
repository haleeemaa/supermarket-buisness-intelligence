
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules


def create_basket(df, max_products=100):
    """
    Create a basket:
    Each row represents an invoice.
    Each column represents a product.
    True means the product was purchased in that invoice.
    """

    if df.empty:
        return pd.DataFrame()

    # Select the most frequently purchased products
    top_products = (
        df.groupby("Description")["Quantity"]
        .sum()
        .nlargest(max_products)
        .index
    )

    filtered = df[df["Description"].isin(top_products)]

    # Remove duplicate products within the same invoice
    filtered = filtered.drop_duplicates(
        subset=["InvoiceNo", "Description"]
    )

    basket = pd.crosstab(
        filtered["InvoiceNo"],
        filtered["Description"]
    )

    return basket.astype(bool)


def find_frequent_itemsets(
    basket,
    min_support=0.01,
    max_len=3
):
    """
    Find frequent itemsets using Apriori.

    IMPORTANT:
    Keep single products here because association_rules()
    needs their support values to calculate rules.
    """

    if basket.empty:
        return pd.DataFrame(
            columns=["support", "itemsets"]
        )

    itemsets = apriori(
        basket.astype(bool),
        min_support=min_support,
        use_colnames=True,
        max_len=max_len,
        low_memory=True
    )

    return itemsets.sort_values(
        by="support",
        ascending=False
    ).reset_index(drop=True)


def find_rules(itemsets, min_confidence=0.30):
    """
    Generate association rules from frequent itemsets.
    """

    if itemsets.empty:
        return pd.DataFrame()

    # Only combinations containing at least two products
    multi_itemsets = itemsets[
        itemsets["itemsets"].apply(lambda x: len(x) >= 2)
    ]

    if multi_itemsets.empty:
        return pd.DataFrame()

    rules = association_rules(
        itemsets,
        metric="confidence",
        min_threshold=min_confidence
    )

    if rules.empty:
        return pd.DataFrame()

    rules = rules[
        rules["lift"] > 1
    ].copy()

    if rules.empty:
        return pd.DataFrame()

    required_columns = [
        "antecedents",
        "consequents",
        "support",
        "confidence",
        "lift"
    ]

    rules = rules[required_columns]

    return rules.sort_values(
        by=["lift", "confidence"],
        ascending=False
    ).reset_index(drop=True)


def format_rules(rules):
    """
    Convert technical association rules into readable product names.
    """

    if rules.empty:
        return pd.DataFrame(
            columns=[
                "Products Bought First",
                "Products Recommended",
                "Support",
                "Confidence",
                "Lift"
            ]
        )

    formatted = pd.DataFrame()

    formatted["Products Bought First"] = rules[
        "antecedents"
    ].apply(lambda x: ", ".join(sorted(x)))

    formatted["Products Recommended"] = rules[
        "consequents"
    ].apply(lambda x: ", ".join(sorted(x)))

    formatted["Support"] = rules["support"]
    formatted["Confidence"] = rules["confidence"]
    formatted["Lift"] = rules["lift"]

    return formatted.reset_index(drop=True)


def format_combinations(itemsets):
    """
    Display only combinations containing two or more products.
    """

    if itemsets.empty:
        return pd.DataFrame(
            columns=["Product Combination", "Support"]
        )

    combinations = itemsets[
        itemsets["itemsets"].apply(lambda x: len(x) >= 2)
    ].copy()

    if combinations.empty:
        return pd.DataFrame(
            columns=["Product Combination", "Support"]
        )

    result = pd.DataFrame()

    result["Product Combination"] = combinations[
        "itemsets"
    ].apply(lambda x: " + ".join(sorted(x)))

    result["Support"] = combinations["support"]

    return result.sort_values(
        by="Support",
        ascending=False
    ).reset_index(drop=True)
