"""
This script uses vega-lite to create a heatmap of the trade data.
"""

import pandas, altair, numpy

from load_baci import load_from_baci_dump, baci_file


def main():
    dataframe = load_from_baci_dump(baci_file, 440791)

    # --- 1) Compute "largest countries" by total quantity (exports + imports) ---
    export_totals = (
        dataframe.groupby("exporter_name", as_index=False)["quantity"]
        .sum()
        .rename(columns={"exporter_name": "country", "quantity": "export_quantity"})
    )

    import_totals = (
        dataframe.groupby("importer_name", as_index=False)["quantity"]
        .sum()
        .rename(columns={"importer_name": "country", "quantity": "import_quantity"})
    )

    country_totals = export_totals.merge(
        import_totals, on="country", how="outer"
    ).fillna(0.0)
    country_totals["total_quantity"] = (
        country_totals["export_quantity"] + country_totals["import_quantity"]
    )

    # Rank countries by total quantity (1 = largest)
    country_totals = country_totals.sort_values(
        "total_quantity", ascending=False
    ).reset_index(drop=True)
    country_totals["rank_total"] = numpy.arange(1, len(country_totals) + 1)

    # Attach ranks back to each row for exporter and importer
    dataframe_with_ranks = (
        dataframe.merge(
            country_totals[["country", "rank_total"]],
            left_on="exporter_name",
            right_on="country",
            how="left",
        )
        .rename(columns={"rank_total": "exporter_rank"})
        .drop(columns=["country"])
    )

    dataframe_with_ranks = (
        dataframe_with_ranks.merge(
            country_totals[["country", "rank_total"]],
            left_on="importer_name",
            right_on="country",
            how="left",
        )
        .rename(columns={"rank_total": "importer_rank"})
        .drop(columns=["country"])
    )

    # --- 2) Slider parameter for Top N ---
    max_n = int(min(50, len(country_totals)))  # adjust if you want a bigger max
    top_n = altair.param(
        name="top_n",
        value=min(20, max_n),
        bind=altair.binding_range(min=5, max=max_n, step=1, name="Top N countries: "),
    )

    # --- 3) Heatmap: exporter (X) × importer (Y), color = sum(quantity) ---
    heatmap = (
        altair.Chart(dataframe_with_ranks)
        .add_params(top_n)
        .transform_filter(
            (altair.datum.exporter_rank <= top_n)
            & (altair.datum.importer_rank <= top_n)
        )
        .transform_aggregate(
            quantity_sum="sum(quantity)", groupby=["exporter_name", "importer_name"]
        )
        .mark_rect()
        .encode(
            x=altair.X("exporter_name:N", sort="-x", title="Exporter country"),
            y=altair.Y("importer_name:N", sort="-x", title="Importer country"),
            color=altair.Color("quantity_sum:Q", title="Quantity (sum)"),
            tooltip=[
                altair.Tooltip("exporter_name:N", title="Exporter"),
                altair.Tooltip("importer_name:N", title="Importer"),
                altair.Tooltip("quantity_sum:Q", title="Quantity (sum)", format=",.3f"),
            ],
        )
        .properties(
            width=800,
            height=800,
            title="Exporter → Importer heatmap (filtered by Top-N total quantity)",
        )
    )

    heatmap.save("trade_heatmap_topn.html")
    print("Saved trade_heatmap_topn.html — open it in your browser.")


if __name__ == "__main__":
    main()
