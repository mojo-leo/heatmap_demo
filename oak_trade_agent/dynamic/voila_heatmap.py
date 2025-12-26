#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses Voila (Jupyter widgets) to create an interactive heatmap of the trade data.
"""

# Built-in modules
from functools import cached_property

# Third-party modules
import ipywidgets as widgets
from IPython.display import display
import plotly.graph_objects as go

# Internal modules
from oak_trade_agent.data.baci_dataset import baci


###############################################################################
class VoilaHeatmap:
    """Creates a Voila (Jupyter widgets) interactive heatmap visualization of trade data."""

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
    def widget(self) -> widgets.VBox:
        """Create an ipywidgets-based interactive heatmap with slider."""
        data = self.data_prep
        max_n = data["max_n"]
        default_top_n = min(10, max_n)

        # Create slider widget
        slider = widgets.IntSlider(
            value=default_top_n,
            min=2,
            max=max_n,
            step=1,
            description="Top # countries:",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="800px", margin="20px auto"),
        )

        # Create initial figure widget
        initial_fig = self.create_heatmap_figure(default_top_n)
        fig_widget = go.FigureWidget(initial_fig)

        def update_heatmap(change):
            """Update the heatmap when the slider value changes."""
            top_n = change["new"]
            new_fig = self.create_heatmap_figure(top_n)
            # Update the figure widget data
            with fig_widget.batch_update():
                fig_widget.data[0].z = new_fig.data[0].z
                fig_widget.data[0].x = new_fig.data[0].x
                fig_widget.data[0].y = new_fig.data[0].y
                fig_widget.layout.title.text = new_fig.layout.title.text

        # Link slider to update function
        slider.observe(update_heatmap, names="value")

        # Create title widget
        title_widget = widgets.HTML(
            value=f"<h1>{self.title}</h1>",
            layout=widgets.Layout(margin="20px auto", text_align="center"),
        )

        # Combine widgets
        return widgets.VBox(
            [title_widget, slider, fig_widget],
            layout=widgets.Layout(align_items="center", width="100%"),
        )

    def __call__(self) -> None:
        """Display the Voila widget interface."""
        display(self.widget)


###############################################################################
# Make a singleton
voila_heatmap = VoilaHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    voila_heatmap()

