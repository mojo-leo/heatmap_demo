#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses Shiny to create an interactive heatmap of the trade data.
"""

# Built-in modules
from functools import cached_property

# Third-party modules
from shiny import App, ui, render
import plotly.graph_objects as go

# Internal modules
from oak_trade_agent.baci_dataset import baci


###############################################################################
class ShinyHeatmap:
    """Creates a Shiny interactive heatmap visualization of trade data."""

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def data_prep(self) -> dict:
        """Prepare and cache the data for the heatmap."""
        df = baci.ranked_oak_df
        max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))

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

        return {
            "pivot_df": pivot_df,
            "sorted_countries": sorted_countries,
            "max_n": max_n,
        }

    def create_heatmap_figure(self, top_n: int) -> go.Figure:
        """Create a Plotly heatmap figure for the given top_n value."""
        data = self.data_prep
        sorted_countries = data["sorted_countries"]
        pivot_df = data["pivot_df"]

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

    @cached_property
    def app(self) -> App:
        """Create a Shiny app with interactive heatmap and slider."""
        data = self.data_prep
        max_n = data["max_n"]
        default_top_n = min(10, max_n)

        # Define UI
        app_ui = ui.page_fluid(
            ui.h1(self.title),
            ui.div(
                ui.input_slider(
                    "top_n",
                    "Top # countries:",
                    min=2,
                    max=max_n,
                    value=default_top_n,
                    step=1,
                ),
                style="width: 800px; margin: 20px auto;",
            ),
            ui.output_plotly("heatmap", height="800px"),
        )

        # Define server logic
        def server(input, output, session):
            @output
            @render.plotly
            def heatmap():
                """Render the heatmap plot."""
                top_n = input.top_n()
                return self.create_heatmap_figure(top_n)

        return App(app_ui, server)

    def __call__(self, port: int = 8000, host: str = "127.0.0.1") -> None:
        """Run the Shiny app server."""
        print(f"Starting Shiny server on http://{host}:{port}")
        print("Press Ctrl+C to stop the server.")
        self.app.run(port=port, host=host)


###############################################################################
# Make a singleton
shiny_heatmap = ShinyHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    shiny_heatmap()

