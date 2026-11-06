
import pandas as pd


def create_strategy_report(rules):
    """
    Convert association rules into practical business suggestions.

    The input comes from format_rules(), which uses:
    Support, Confidence and Lift.
    """

    recommendations = []

    if rules is None or rules.empty:
        return recommendations

    for _, row in rules.iterrows():

        # Read the correctly capitalised column names
        products_bought = row["Products Bought First"]
        products_recommended = row["Products Recommended"]

        support = float(row["Support"])
        confidence = float(row["Confidence"])
        lift = float(row["Lift"])

        # Decide the type of business strategy
        if confidence >= 0.60 and lift >= 2:

            strategy = "Combo Offer"

            action = (
                f"Create a special combo containing "
                f"{products_bought} and {products_recommended}. "
                "Offer a small discount when customers buy them together."
            )

            reason = (
                "Customers who purchase the first product or products "
                "frequently also purchase the recommended product."
            )

        elif lift >= 1.5:

            strategy = "Cross-Selling"

            action = (
                f"When customers purchase {products_bought}, "
                f"recommend {products_recommended} at checkout."
            )

            reason = (
                "The products have a stronger purchasing relationship "
                "than would be expected from their individual popularity."
            )

            """elif confidence >= 0.40:

            strategy = "Product Placement"

            action = (
                f"Consider placing {products_recommended} "
                f"near {products_bought} in the store."
            )

            reason = (
                "Customers buying the first product show a useful tendency "
                "to purchase the recommended product as well."
            )"""

        else:

            strategy = "Product Recommendation"

            action = (
                f"Display {products_recommended} as a suggested product "
                f"when promoting {products_bought}."
            )

            reason = (
                "The historical transactions show a purchasing relationship "
                "that may be worth testing."
            )

        # Prepare a simple explanation for the store manager
        observation = (
            f"In {support * 100:.2f}% of all analysed orders, "
            f"both product groups appeared together. "
            f"Among orders containing {products_bought}, "
            f"{confidence * 100:.2f}% also contained "
            f"{products_recommended}."
        )

        measurement = (
            "Compare the number of combo purchases, total sales revenue "
            "and average order value before and after the promotion."
        )

        recommendations.append({

            "Strategy": strategy,

            "Products": (
                f"{products_bought} + {products_recommended}"
            ),

            "What the data shows": observation,

            "Suggested action": action,

            "Why try it": reason,

            "How to measure success": measurement,

            "Orders containing both (%)": round(
                support * 100, 2
            ),

            "Buying likelihood (%)": round(
                confidence * 100, 2
            ),

            "Lift": round(lift, 2)

        })

    return recommendations


def get_strategy_summary(recommendations):
    """
    Count the different types of business suggestions.
    """

    if not recommendations:
        return {
            "total_suggestions": 0,
            "combo_offers": 0,
            "cross_selling": 0,
            "product_placement": 0,
            "other_recommendations": 0
        }

    total = len(recommendations)

    combo_offers = sum(
        1 for item in recommendations
        if item["Strategy"] == "Combo Offer"
    )

    cross_selling = sum(
        1 for item in recommendations
        if item["Strategy"] == "Cross-Selling"
    )

    product_placement = sum(
        1 for item in recommendations
        if item["Strategy"] == "Product Placement"
    )

    other = sum(
        1 for item in recommendations
        if item["Strategy"] == "Product Recommendation"
    )

    return {
        "total_suggestions": total,
        "combo_offers": combo_offers,
        "cross_selling": cross_selling,
        "product_placement": product_placement,
        "other_recommendations": other
    }
