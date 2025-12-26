#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses holoviews to create a heatmap of the trade data.
"""

# Built-in modules
import webbrowser
from functools import cached_property

# Third-party modules
import holoviews as hv
import panel as pn

# Internal modules
from oak_trade_agent.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir

# Set the backend for static HTML export
hv.extension("bokeh")


###############################################################################
class HoloviewsHeatmap:
    """Creates a holoviews heatmap visualization of trade data."""

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def heatmap(self) -> pn.Column:
        """Create the holoviews heatmap visualization with interactive slider."""
        # Calculate max_n from the dataframe ranks
        df = baci.ranked_oak_df
        max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))
        default_top_n = min(10, max_n)

        # Create a function that generates the heatmap based on top_n
        def create_heatmap(top_n: int) -> hv.HeatMap:
            """Create heatmap filtered by top_n countries."""
            filtered_df = df[
                (df["exporter_rank"] <= top_n) & (df["importer_rank"] <= top_n)
            ]
            # Create the heatmap
            heatmap = hv.HeatMap(
                filtered_df,
                kdims=["exporter_name", "importer_name"],
                vdims=["quantity"],
            )
            # Sort by exporter and importer names
            heatmap = heatmap.sort(["exporter_name", "importer_name"])
            # Apply styling
            heatmap = heatmap.opts(
                width=800,
                height=800,
                title=self.title,
                xlabel="Exporter country",
                ylabel="Importer country",
                colorbar=True,
                cmap="Viridis",
                tools=["hover"],
                xrotation=45,
                yrotation=0,
            )
            return heatmap

        # Create a Panel widget for the slider
        top_n_slider = pn.widgets.IntSlider(
            name="Top # countries:",
            start=2,
            end=max_n,
            step=1,
            value=default_top_n,
        )

        # Create a dynamic map that updates with the slider
        # Use pn.bind to connect the widget to the function
        dmap = pn.bind(create_heatmap, top_n=top_n_slider)

        # Combine the slider and heatmap in a Panel layout
        panel_layout = pn.Column(top_n_slider, dmap)
        return panel_layout

    def __call__(self) -> None:
        """Create and save a holoviews heatmap visualization."""
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_filename = "holoviews_heatmap_topn.html"
        output_path = output_dir / output_filename

        # Save the panel layout (which includes the interactive slider) to HTML
        self.heatmap.save(output_path)
        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")


###############################################################################
# Make a singleton
holoviews_heatmap = HoloviewsHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    holoviews_heatmap()
