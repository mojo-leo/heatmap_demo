#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Built-in modules
import os
import subprocess
from functools import cached_property
from pathlib import Path

# Third-party modules
import pandas as pd
import plotly.graph_objects as go
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget

# Internal modules
from oak_trade_agent.data.baci_dataset import baci


###############################################################################
class ShinyHeatmap:
    """
    Shiny for Python app (dynamic, server-side):
    - Reactive slider input (Top N)
    - Full pivot matrix built once and cached
    - On change, slice rows/cols of the cached matrix (fast)
    - Uses a single Top-N country list for both axes (baci.country_ranks)
    """

    title = "Exporter → Importer heatmap (Top-N countries by total quantity)"

    @cached_property
    def df(self) -> pd.DataFrame:
        return baci.ranked_oak_df

    @cached_property
    def countries_ordered(self) -> list[str]:
        # Already sorted: rank 1 = largest
        return baci.country_ranks.index.tolist()

    @cached_property
    def max_n(self) -> int:
        return len(self.countries_ordered)

    @cached_property
    def full_matrix(self) -> pd.DataFrame:
        """
        Full NxN pivot matrix across ALL ranked countries (rows=importers, cols=exporters).
        Missing pairs filled with 0 so any slice is fully populated.
        """
        countries = self.countries_ordered
        sub = self.df[["exporter_name", "importer_name", "quantity"]]

        mat = sub.pivot_table(
            index="importer_name",
            columns="exporter_name",
            values="quantity",
            aggfunc="sum",
            fill_value=0.0,
        ).reindex(index=countries, columns=countries, fill_value=0.0)
        return mat

    def _slice_for_n(self, n: int) -> pd.DataFrame:
        countries = self.countries_ordered[:n]
        return self.full_matrix.loc[countries, countries]

    @cached_property
    def app_ui(self):
        return ui.page_fluid(
            ui.h3(self.title),
            ui.input_slider(
                "top_n",
                "Top N countries",
                min=2,
                max=self.max_n,
                value=min(10, self.max_n),
                step=1,
            ),
            ui.tags.div({"style": "height: 8px;"}),
            output_widget("heatmap"),
            ui.tags.div({"style": "height: 8px;"}),
            ui.output_text("status"),
        )

    def server(self, input, output, session):
        @reactive.calc
        def mat_n() -> pd.DataFrame:
            return self._slice_for_n(int(input.top_n()))

        @output
        @render.text
        def status():
            n = int(input.top_n())
            return f"Showing {n} × {n} countries"

        @output
        @render_widget
        def heatmap():
            m = mat_n()
            countries = list(m.columns)

            fig = go.Figure(
                data=[
                    go.Heatmap(
                        z=m.to_numpy(),
                        x=countries,
                        y=countries,
                        colorbar=dict(title="Quantity (tons)"),
                        hovertemplate=(
                            "Exporter: %{x}<br>"
                            "Importer: %{y}<br>"
                            "Quantity: %{z:,.3f}<extra></extra>"
                        ),
                    )
                ]
            )
            fig.update_layout(
                width=900,
                height=900,
                margin=dict(l=120, r=80, t=60, b=120),
                xaxis=dict(title="Exporter country"),
                yaxis=dict(title="Importer country"),
            )

            # shinywidgets is happiest when returning a widget-like object;
            # Plotly provides FigureWidget for this purpose.
            return go.FigureWidget(fig)

    @cached_property
    def app(self) -> App:
        return App(self.app_ui, self.server)

    def __call__(self) -> None:
        """
        Launch via the Shiny CLI as a subprocess, injecting PYTHONPATH so the package
        imports resolve no matter where `shiny run` sets the working directory.
        """
        env = os.environ.copy()

        # Repo root is two levels up from .../oak_trade_agent/dynamic/shiny_dynamic.py
        repo_root = Path(__file__).resolve().parents[2]
        env["PYTHONPATH"] = str(repo_root) + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )

        subprocess.run(
            ["shiny", "run", "--reload", str(Path(__file__).resolve())],
            check=False,
        )


###############################################################################
# Make a singleton
shiny_heatmap = ShinyHeatmap()

# Shiny expects an `app` object at module scope
app = shiny_heatmap.app

# Run the singleton when run as a script
if __name__ == "__main__":
    shiny_heatmap()
