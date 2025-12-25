#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses Dash to create an interactive heatmap of the trade data.
"""

# Built-in modules
from functools import cached_property

# Third-party modules
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

# Internal modules
from oak_trade_agent.baci_dataset import baci


###############################################################################
class DashHeatmap:
    """Creates a Dash interactive heatmap visualization of trade data."""

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def app(self) -> dash.Dash:
        """Create a Dash app with interactive heatmap and slider."""
        app = dash.Dash(__name__)

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

        # Create initial heatmap
        def create_heatmap_figure(top_n: int) -> go.Figure:
            """Create a Plotly heatmap figure for the given top_n value."""
            top_countries = sorted_countries[:top_n]
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

            # Update layout
            fig.update_layout(
                title=f"Exporter → Importer heatmap (Top {top_n} countries)",
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
            )

            return fig

        # Define app layout
        app.layout = html.Div(
            [
                html.H1(self.title),
                html.Div(
                    [
                        html.Label("Top # countries:", style={"font-size": "16px"}),
                        dcc.Slider(
                            id="top-n-slider",
                            min=2,
                            max=max_n,
                            step=1,
                            value=default_top_n,
                            marks={
                                i: str(i) if i % 5 == 0 or i == 2 or i == max_n else ""
                                for i in range(2, max_n + 1)
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ],
                    style={"width": "800px", "margin": "20px auto"},
                ),
                dcc.Graph(id="heatmap-graph", figure=create_heatmap_figure(default_top_n)),
            ],
            style={"text-align": "center", "font-family": "Arial, sans-serif"},
        )

        # Define callback to update heatmap based on slider
        @app.callback(
            Output("heatmap-graph", "figure"),
            Input("top-n-slider", "value"),
        )
        def update_heatmap(top_n: int) -> go.Figure:
            """Update the heatmap when the slider value changes."""
            return create_heatmap_figure(top_n)

        return app

    def __call__(self, debug: bool = False, port: int = 8050) -> None:
        """Run the Dash app server."""
        print(f"Starting Dash server on http://127.0.0.1:{port}")
        print("Press Ctrl+C to stop the server.")
        self.app.run_server(debug=debug, port=port)


###############################################################################
# Make a singleton
dash_heatmap = DashHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    dash_heatmap()

