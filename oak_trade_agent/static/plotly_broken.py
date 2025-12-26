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

# Internal modules
from oak_trade_agent.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class PlotlyHeatmap:
    """Creates a plotly heatmap visualization of trade data."""

    @cached_property
    def heatmap(self) -> go.Figure:
        """Create a plotly heatmap figure with top-N filtering using a slider."""
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
        # Sort by total trade (exports + imports)
        country_totals = exporter_totals.add(importer_totals, fill_value=0)
        country_totals = country_totals.sort_values(ascending=False)
        sorted_countries = country_totals.index.tolist()

        # Create frames for slider (one frame per top-N value)
        frames = []
        slider_steps = []
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

            # Create frame for this top-N value
            frames.append(
                go.Frame(
                    data=[
                        go.Heatmap(
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
                    ],
                    name=str(n),
                    layout=go.Layout(
                        title=f"Exporter → Importer heatmap (Top {n} countries)"
                    ),
                )
            )

            # Create slider step
            slider_steps.append(
                dict(
                    args=[
                        [str(n)],
                        {
                            "frame": {"duration": 0, "redraw": True},
                            "mode": "immediate",
                            "transition": {"duration": 0},
                        },
                    ],
                    label=f"Top {n}",
                    method="animate",
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
            ),
            frames=frames,
        )

        # Update layout with slider
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
            sliders=[
                dict(
                    active=default_top_n
                    - 2,  # Index of default value (2 is first, so -2)
                    currentvalue={
                        "prefix": "Top # countries: ",
                        "visible": True,
                        "xanchor": "right",
                    },
                    pad={"t": 50},
                    steps=slider_steps,
                )
            ],
        )

        return fig

    def __call__(self) -> None:
        """Create and save a plotly heatmap visualization."""
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_filename = "plotly_heatmap_topn.html"
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
