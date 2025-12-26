#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This object uses bokeh to create a heatmap of the trade data.
"""

# Built-in modules
import webbrowser
from functools import cached_property

# Third-party modules
from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    CustomJS,
    HoverTool,
    LinearColorMapper,
    Slider,
)
from bokeh.plotting import figure

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class BokehHeatmap:
    """Creates a bokeh heatmap visualization of trade data."""

    title = "Exporter → Importer heatmap (filtered by Top-N total quantity)"

    @cached_property
    def heatmap(self):
        """Create a bokeh heatmap figure with top-N filtering using a slider."""
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

        # Filter data for default top-N
        top_countries = sorted_countries[:default_top_n]
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

        # Prepare data for Bokeh
        exporter_names = heatmap_matrix.columns.tolist()
        importer_names = heatmap_matrix.index.tolist()
        quantity_values = heatmap_matrix.values.flatten()

        # Create arrays for x, y coordinates
        x_coords = []
        y_coords = []
        quantities = []
        exporter_labels = []
        importer_labels = []

        for i, importer in enumerate(importer_names):
            for j, exporter in enumerate(exporter_names):
                x_coords.append(j)
                y_coords.append(i)
                quantities.append(heatmap_matrix.loc[importer, exporter])
                exporter_labels.append(exporter)
                importer_labels.append(importer)

        # Create ColumnDataSource with all data (for filtering)
        source = ColumnDataSource(
            data=dict(
                x=x_coords,
                y=y_coords,
                quantity=quantities,
                exporter=exporter_labels,
                importer=importer_labels,
            )
        )

        # Create color mapper
        min_qty = min(quantities) if quantities else 0
        max_qty = max(quantities) if quantities else 1
        color_mapper = LinearColorMapper(
            palette="Viridis256", low=min_qty, high=max_qty
        )

        # Create figure
        p = figure(
            width=800,
            height=800,
            title=self.title,
            x_range=exporter_names,
            y_range=list(reversed(importer_names)),  # Reverse to match typical heatmap
            tools="pan,box_zoom,wheel_zoom,reset,save",
            toolbar_location="above",
        )

        # Create rectangles for heatmap
        p.rect(
            x="x",
            y="y",
            width=0.95,
            height=0.95,
            source=source,
            fill_color={"field": "quantity", "transform": color_mapper},
            line_color=None,
        )

        # Add hover tool
        hover = HoverTool(
            tooltips=[
                ("Exporter", "@exporter"),
                ("Importer", "@importer"),
                ("Quantity", "@quantity{0,0.000} tons"),
            ]
        )
        p.add_tools(hover)

        # Add color bar
        color_bar = ColorBar(
            color_mapper=color_mapper,
            label_standoff=12,
            border_line_color=None,
            location=(0, 0),
            title="Quantity (tons)",
        )
        p.add_layout(color_bar, "right")

        # Set axis labels
        p.xaxis.axis_label = "Exporter country"
        p.yaxis.axis_label = "Importer country"
        p.xaxis.major_label_orientation = 3.14159 / 4  # 45 degrees

        # Create slider for Top N
        slider = Slider(
            start=2,
            end=max_n,
            value=default_top_n,
            step=1,
            title="Top # countries:",
            width=600,
        )

        # Store all data for filtering (we'll need to pass this to JavaScript)
        # Create a lookup of all country data by rank
        all_countries_by_rank = {}
        for rank in range(1, max_n + 1):
            countries = sorted_countries[:rank]
            all_countries_by_rank[rank] = countries

        # We need to create a more complex filtering mechanism
        # For static HTML, we'll pre-compute all possible heatmaps
        # and use JavaScript to switch between them
        all_heatmap_data = {}
        for n in range(2, max_n + 1):
            top_countries_n = sorted_countries[:n]
            filtered_df_n = pivot_df[
                pivot_df["exporter_name"].isin(top_countries_n)
                & pivot_df["importer_name"].isin(top_countries_n)
            ]
            heatmap_matrix_n = filtered_df_n.pivot_table(
                index="importer_name",
                columns="exporter_name",
                values="quantity",
                fill_value=0,
            )
            heatmap_matrix_n = heatmap_matrix_n.reindex(
                index=[c for c in sorted_countries if c in heatmap_matrix_n.index],
                columns=[c for c in sorted_countries if c in heatmap_matrix_n.columns],
            )

            exporter_names_n = heatmap_matrix_n.columns.tolist()
            importer_names_n = heatmap_matrix_n.index.tolist()

            x_coords_n = []
            y_coords_n = []
            quantities_n = []
            exporter_labels_n = []
            importer_labels_n = []

            for i, importer in enumerate(importer_names_n):
                for j, exporter in enumerate(exporter_names_n):
                    x_coords_n.append(j)
                    y_coords_n.append(i)
                    quantities_n.append(heatmap_matrix_n.loc[importer, exporter])
                    exporter_labels_n.append(exporter)
                    importer_labels_n.append(importer)

            all_heatmap_data[n] = {
                "x": x_coords_n,
                "y": y_coords_n,
                "quantity": quantities_n,
                "exporter": exporter_labels_n,
                "importer": importer_labels_n,
                "exporter_names": exporter_names_n,
                "importer_names": importer_names_n,
            }

        # Create JavaScript callback to update heatmap based on slider
        callback = CustomJS(
            args=dict(
                source=source,
                p=p,
                all_data=all_heatmap_data,
                color_mapper=color_mapper,
            ),
            code="""
            const n = cb_obj.value;
            const data = all_data[n];
            
            if (data) {
                // Update source data
                source.data = {
                    x: data.x,
                    y: data.y,
                    quantity: data.quantity,
                    exporter: data.exporter,
                    importer: data.importer
                };
                
                // Update axis ranges
                p.x_range.factors = data.exporter_names;
                p.y_range.factors = data.importer_names.slice().reverse();
                
                // Update color mapper range
                const quantities = data.quantity;
                const min_qty = Math.min(...quantities);
                const max_qty = Math.max(...quantities);
                color_mapper.low = min_qty;
                color_mapper.high = max_qty;
                
                // Update title
                p.title.text = 'Exporter → Importer heatmap (Top ' + n + ' countries)';
                
                // Trigger update
                source.change.emit();
                p.change.emit();
            }
            """,
        )

        slider.js_on_change("value", callback)

        # Combine plot and slider
        layout = column(slider, p)

        return layout

    def __call__(self) -> None:
        """Create and save a bokeh heatmap visualization."""
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_filename = "bokeh_heatmap_topn.html"
        output_path = output_dir / output_filename
        output_file(str(output_path))
        save(self.heatmap)
        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")


###############################################################################
# Make a singleton
bokeh_heatmap = BokehHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    bokeh_heatmap()
