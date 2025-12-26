#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses d3blocks to create a heatmap of the trade data.
"""

# Built-in modules
import webbrowser
from functools import cached_property

# Third-party modules
from d3blocks import D3Blocks

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class D3BlocksHeatmap:
    """Creates a d3blocks heatmap visualization of trade data."""

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def heatmap_data(self):
        """Prepare and cache the heatmap data."""
        # Calculate max_n from the dataframe ranks
        df = baci.ranked_oak_df
        max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))
        default_top_n = min(10, max_n)

        # Filter data for top N countries
        filtered_df = df[
            (df["exporter_rank"] <= default_top_n)
            & (df["importer_rank"] <= default_top_n)
        ]

        # Aggregate quantity by exporter_name and importer_name
        pivot_df = (
            filtered_df.groupby(["exporter_name", "importer_name"])["quantity"]
            .sum()
            .reset_index()
        )

        # Create pivot table for d3blocks heatmap
        # d3blocks expects a DataFrame with index and columns as labels
        heatmap_matrix = pivot_df.pivot_table(
            index="importer_name",
            columns="exporter_name",
            values="quantity",
            fill_value=0,
        )

        return heatmap_matrix

    @cached_property
    def heatmap(self) -> D3Blocks:
        """Create and return the d3blocks heatmap object."""
        # Initialize d3blocks
        d3 = D3Blocks()
        d3.heatmap(
            self.heatmap_data,
            showfig=False,
            stroke="red",
            figsize=(800, 800),
            title=self.title,
        )

        return d3

    def __call__(self) -> None:
        """Create and save a d3blocks heatmap visualization."""
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_filename = "d3blocks_heatmap_topn.html"
        output_path = output_dir / output_filename
        
        # Create heatmap with filepath
        d3 = D3Blocks()
        d3.heatmap(
            self.heatmap_data,
            showfig=False,
            stroke="red",
            figsize=(800, 800),
            title=self.title,
            filepath=str(output_path),
        )
        
        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")


###############################################################################
# Make a singleton
d3blocks_heatmap = D3BlocksHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    d3blocks_heatmap()

