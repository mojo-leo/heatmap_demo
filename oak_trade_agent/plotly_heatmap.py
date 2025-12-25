#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses plotly to create a heatmap of the trade data.
"""

# Built-in modules
import webbrowser
from functools import cached_property

# Third-party modules
import plotly.graph_objects as go
import pandas

# Internal modules
from oak_trade_agent.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class PlotlyHeatmap:
    """Creates a plotly heatmap visualization of trade data."""

    @cached_property
    def heatmap(self) -> go.Figure:
        """Create a plotly heatmap figure with top-N filtering."""
        df = baci.ranked_oak_df
        max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))
        default_top_n = min(10, max_n)

        # Create pivot table for heatmap
        # Aggregate quantity by exporter_name and importer_name
        pivot_df = (
            df.groupby(["exporter_name", "importer_name"])["quantity"]
            .sum()
            .reset_index()
        )

        # Create list of unique countries sorted by rank
        exporter_totals = (
            df.groupby("exporter_name")["quantity"].sum().sort_values(ascending=False)
        )
        importer_totals = (
            df.groupby("importer_name")["quantity"].sum().sort_values(ascending=False)
        )
        all_countries = exporter_totals.index.union(importer_totals.index).unique()
        # Sort by total trade (exports + imports)
        country_totals = exporter_totals.add(importer_totals, fill_value=0)
        country_totals = country_totals.sort_values(ascending=False)
        sorted_countries = country_totals.index.tolist()

        # Create buttons for different top-N values
        buttons = []
        for n in range(2, max_n + 1):
            # Filter data for this top-N
            top_countries = sorted_countries[:n]
            filtered_df = pivot_df[
                pivot_df["exporter_name"].isin(top_countries)
                & pivot_df["importer_name"].isin(top_countries)
            ]

            # Create pivot matrix
            heatmap_matrix = filtered_df.pivot_table(
                index="importer_name",
                columns="exporter_name",
                values="quantity",
                fill_value=0,
            )

            # Reorder rows and columns to match sorted order
            heatmap_matrix = heatmap_matrix.reindex(
                index=[c for c in sorted_countries if c in heatmap_matrix.index],
                columns=[c for c in sorted_countries if c in heatmap_matrix.columns],
            )

            buttons.append(
                dict(
                    label=f"Top {n}",
                    method="update",
                    args=[
                        {
                            "z": [heatmap_matrix.values],
                            "x": [heatmap_matrix.columns.tolist()],
                            "y": [heatmap_matrix.index.tolist()],
                        },
                        {"title": f"Exporter → Importer heatmap (Top {n} countries)"},
                    ],
                )
            )

        # Initial data for default top-N
        top_countries = sorted_countries[:default_top_n]
        filtered_df = pivot_df[
            pivot_df["exporter_name"].isin(top_countries)
            & pivot_df["importer_name"].isin(top_countries)
        ]
        heatmap_matrix = filtered_df.pivot_table(
            index="importer_name",
            columns="exporter_name",
            values="quantity",
            fill_value=0,
        )
        heatmap_matrix = heatmap_matrix.reindex(
            index=[c for c in sorted_countries if c in heatmap_matrix.index],
            columns=[c for c in sorted_countries if c in heatmap_matrix.columns],
        )

        # Create the heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_matrix.values,
                x=heatmap_matrix.columns.tolist(),
                y=heatmap_matrix.index.tolist(),
                colorscale="Viridis",
                colorbar=dict(title="Quantity (tons)"),
                hovertemplate=(
                    "<b>Exporter:</b> %{x}<br>"
                    "<b>Importer:</b> %{y}<br>"
                    "<b>Quantity:</b> %{z:,.3f} tons<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Update layout with dropdown menu
        fig.update_layout(
            title=f"Exporter → Importer heatmap (Top {default_top_n} countries)",
            xaxis=dict(
                title="Exporter country",
                side="bottom",
                tickangle=-45,
            ),
            yaxis=dict(
                title="Importer country",
                autorange="reversed",  # Reverse Y axis to match typical heatmap layout
            ),
            width=800,
            height=800,
            updatemenus=[
                dict(
                    type="dropdown",
                    direction="down",
                    showactive=True,
                    x=0.1,
                    xanchor="left",
                    y=1.02,
                    yanchor="top",
                    buttons=buttons,
                )
            ],
        )

        return fig

    def __call__(self) -> None:
        """Create and save a plotly heatmap visualization."""
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_filename = "trade_heatmap_topn_plotly.html"
        output_path = output_dir / output_filename
        self.heatmap.write_html(output_path)
        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")


###############################################################################
# Make a singleton
plotly_heatmap = PlotlyHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    plotly_heatmap()

