
import time
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

from combo_mining import create_basket


# --------------------------------------------------
# 1. PREPARE TRAINING AND TESTING DATA
# --------------------------------------------------

def split_transactions(df, train_ratio=0.80):

    data = df.copy()

    # Use the date column created during preprocessing
    if "Date" in data.columns:
        date_column = "Date"
    elif "InvoiceDate" in data.columns:
        date_column = "InvoiceDate"
    else:
        raise ValueError("Dataset must contain Date or InvoiceDate.")

    data[date_column] = pd.to_datetime(
        data[date_column], errors="coerce"
    )

    data = data.dropna(subset=[date_column, "InvoiceNo"])

    # Find the date of each invoice
    invoice_dates = (
        data.groupby("InvoiceNo")[date_column]
        .min()
        .sort_values()
    )

    if len(invoice_dates) < 2:
        raise ValueError("Not enough invoices to split the dataset.")

    # Chronological 80:20 split
    split_position = int(len(invoice_dates) * train_ratio)
    split_position = max(1, min(split_position, len(invoice_dates) - 1))

    training_invoices = invoice_dates.index[:split_position]
    testing_invoices = invoice_dates.index[split_position:]

    train_df = data[data["InvoiceNo"].isin(training_invoices)].copy()
    test_df = data[data["InvoiceNo"].isin(testing_invoices)].copy()

    return train_df, test_df


# --------------------------------------------------
# 2. CREATE TEST BASKET USING TRAINING PRODUCTS
# --------------------------------------------------



def create_test_basket(test_df, product_columns):

    required = ["InvoiceNo", "Description"]

    for column in required:
        if column not in test_df.columns:
            raise ValueError(f"Missing column: {column}")

    data = test_df[required].copy()

    data["Description"] = (
        data["Description"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    data = data.drop_duplicates(
        ["InvoiceNo", "Description"]
    )

    basket = pd.crosstab(
        data["InvoiceNo"],
        data["Description"]
    )

    # Keep only products selected from training data
    basket = basket.reindex(
        columns=product_columns,
        fill_value=0
    )

    # Remove invoices containing none of the selected products
    basket = basket.loc[basket.any(axis=1)]

    return basket.astype(bool)



# --------------------------------------------------
# 3. GENERATE ASSOCIATION RULES
# --------------------------------------------------

def generate_rules(basket, min_support, min_confidence):

    itemsets = apriori(
        basket,
        min_support=min_support,
        use_colnames=True,
        max_len=3,
        low_memory=True
    )

    if itemsets.empty:
        return itemsets, pd.DataFrame()

    # Association rules need singleton and larger itemsets
    rules = association_rules(
        itemsets,
        metric="confidence",
        min_threshold=min_confidence
    )

    # Keep positive associations
    rules = rules[rules["lift"] > 1].copy()

    return itemsets, rules


# --------------------------------------------------
# 4. EVALUATE RULES ON UNSEEN TEST DATA
# --------------------------------------------------

def evaluate_test_rules(rules, test_basket):

    if rules.empty or test_basket.empty:
        return pd.DataFrame(), 0.0, 0.0

    total_transactions = len(test_basket)

    results = []
    covered_transactions = set()

    for _, rule in rules.iterrows():

        antecedents = rule["antecedents"]
        consequents = rule["consequents"]

        # Transactions containing antecedent
        antecedent_mask = test_basket[list(antecedents)].all(axis=1)

        # Transactions containing consequent
        consequent_mask = test_basket[list(consequents)].all(axis=1)

        # Transactions containing both
        both_mask = antecedent_mask & consequent_mask

        antecedent_count = int(antecedent_mask.sum())
        both_count = int(both_mask.sum())
        consequent_count = int(consequent_mask.sum())

        support = both_count / total_transactions

        confidence = (
            both_count / antecedent_count
            if antecedent_count > 0 else 0
        )

        consequent_support = consequent_count / total_transactions

        lift = (
            confidence / consequent_support
            if consequent_support > 0 else 0
        )

        # Track transactions covered by at least one rule
        covered_transactions.update(
            test_basket.index[antecedent_mask].tolist()
        )

        results.append({
            "Products Bought First": ", ".join(sorted(antecedents)),
            "Products Recommended": ", ".join(sorted(consequents)),
            "Test Support": support,
            "Test Confidence": confidence,
            "Test Lift": lift,
            "Transactions Containing Both": both_count,
            "Transactions Containing Antecedent": antecedent_count
        })

    results_df = pd.DataFrame(results)

    coverage = len(covered_transactions) / total_transactions

    average_confidence = results_df["Test Confidence"].mean()

    return results_df, coverage, average_confidence


# --------------------------------------------------
# 5. RUN ONE COMPLETE APRIORI EXPERIMENT
# --------------------------------------------------

def run_experiment(train_df, test_df, min_support, min_confidence):

    start_time = time.perf_counter()

    # Create basket from training data only
    train_basket = create_basket(train_df, max_products=100)

    if train_basket.empty:
        raise ValueError("Training basket is empty.")

    # Create testing basket with the same product columns
    test_basket = create_test_basket(
        test_df,
        train_basket.columns
    )

    # Generate frequent itemsets and rules
    itemsets, rules = generate_rules(
        train_basket,
        min_support,
        min_confidence
    )

    mining_time = time.perf_counter() - start_time

    # Evaluate rules on testing data
    test_results, coverage, average_confidence = evaluate_test_rules(
        rules,
        test_basket
    )

    if test_results.empty:
        average_test_lift = 0
        average_test_support = 0
    else:
        average_test_lift = test_results["Test Lift"].mean()
        average_test_support = test_results["Test Support"].mean()

    summary = {
        "Minimum Support": min_support,
        "Minimum Confidence": min_confidence,
        "Training Transactions": len(train_basket),
        "Testing Transactions": len(test_basket),
        "Frequent Itemsets": len(itemsets),
        "Association Rules": len(rules),
        "Average Training Confidence": (
            rules["confidence"].mean() if not rules.empty else 0
        ),
        "Average Training Lift": (
            rules["lift"].mean() if not rules.empty else 0
        ),
        "Average Test Support": average_test_support,
        "Average Test Confidence": average_confidence,
        "Average Test Lift": average_test_lift,
        "Rule Coverage": coverage,
        "Execution Time (seconds)": mining_time
    }

    return {
        "summary": summary,
        "rules": rules,
        "test_results": test_results,
        "itemsets": itemsets
    }


# --------------------------------------------------
# 6. COMPARE DIFFERENT THRESHOLDS
# --------------------------------------------------

def compare_thresholds(train_df, test_df):

    experiments = [
        (0.01, 0.30),
        (0.02, 0.40),
        (0.03, 0.50),
        (0.05, 0.60)
    ]

    comparison_results = []

    for support, confidence in experiments:

        result = run_experiment(
            train_df,
            test_df,
            support,
            confidence
        )

        comparison_results.append(result["summary"])

    return pd.DataFrame(comparison_results)


# --------------------------------------------------
# 7. MAIN EVALUATION FUNCTION
# --------------------------------------------------

def run_apriori_evaluation(df):

    train_df, test_df = split_transactions(df)

    # Run the main experiment
    main_result = run_experiment(
        train_df,
        test_df,
        min_support=0.01,
        min_confidence=0.30
    )

    # Compare different thresholds
    comparison = compare_thresholds(train_df, test_df)

    return {
        "main_result": main_result,
        "comparison": comparison,
        "training_data": train_df,
        "testing_data": test_df
    }
