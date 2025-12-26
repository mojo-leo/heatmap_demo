#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
import json
import os
import subprocess
from functools import cached_property

# Third-party modules
import ipywidgets as widgets
import pandas as pd
import plotly.graph_objects as go
from IPython.display import display

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class VoilaHeatmap:

    title = "Exporter → Importer heatmap (Top-N countries by total quantity)"

    # If you move this file, update the import below
    NOTEBOOK_IMPORT = "from oak_trade_agent.dynamic.voila_dynamic import voila_heatmap"

    @cached_property
    def df(self) -> pd.DataFrame:
        # cached_property already caches; no need to copy unless you mutate it
        return baci.ranked_oak_df

    @cached_property
    def countries_ordered(self) -> list[str]:
        # baci.country_ranks is already sorted ascending by rank (1 = largest)
        return baci.country_ranks.index.tolist()

    @cached_property
    def max_n(self) -> int:
        return int(len(self.countries_ordered))

    @cached_property
    def full_matrix(self) -> pd.DataFrame:
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

    def _slice_for_n(self, n: int) -> tuple[list[str], list[str], list[list[float]]]:
        countries = self.countries_ordered[:n]
        mat_n = self.full_matrix.loc[countries, countries]  # rows then cols
        x = countries
        y = countries
        z = mat_n.to_numpy().tolist()
        return x, y, z

    @cached_property
    def slider(self) -> widgets.IntSlider:
        return widgets.IntSlider(
            value=min(10, self.max_n),
            min=2,
            max=self.max_n,
            step=1,
            description="Top N:",
            continuous_update=False,
        )

    @cached_property
    def status(self) -> widgets.HTML:
        return widgets.HTML()

    @cached_property
    def fig(self) -> go.FigureWidget:
        x, y, z = self._slice_for_n(int(self.slider.value))
        fig = go.FigureWidget(
            data=[
                go.Heatmap(
                    z=z,
                    x=x,
                    y=y,
                    colorbar=dict(title="Quantity (tons)"),
                    hovertemplate=(
                        "Exporter: %{x}<br>"
                        "Importer: %{y}<br>"
                        "Quantity: %{z:,.3f}<extra></extra>"
                    ),
                )
            ],
            layout=go.Layout(
                title=self.title,
                width=900,
                height=900,
                margin=dict(l=120, r=80, t=80, b=120),
                xaxis=dict(title="Exporter country"),
                yaxis=dict(title="Importer country"),
            ),
        )
        return fig

    @cached_property
    def ui(self) -> widgets.VBox:
        header = widgets.HTML(f"<h3>{self.title}</h3>")
        controls = widgets.HBox([self.slider, self.status])

        def update(n: int) -> None:
            x, y, z = self._slice_for_n(n)
            with self.fig.batch_update():
                self.fig.data[0].x = x
                self.fig.data[0].y = y
                self.fig.data[0].z = z
            self.status.value = f"<b>Showing:</b> {n} × {n} countries"

        def on_change(change):
            if change["name"] == "value":
                update(int(change["new"]))

        self.slider.observe(on_change, names="value")
        update(int(self.slider.value))

        return widgets.VBox([header, controls, self.fig])

    def show(self) -> None:
        """Display inside a notebook (Voilà will render this)."""
        display(self.ui)

    def __call__(self) -> None:
        """
        Launch Voilà by:
        1) writing a tiny notebook into the output directory
        2) calling `voila <notebook>` via subprocess
        """
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)

        nb_path = output_dir / "voila_dynamic.ipynb"

        nb = {
            "cells": [
                {
                    "cell_type": "code",
                    "metadata": {},
                    "execution_count": None,
                    "outputs": [],
                    "source": [
                        f"{self.NOTEBOOK_IMPORT}\n",
                        "voila_heatmap.show()\n",
                    ],
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        nb_path.write_text(json.dumps(nb, indent=2), encoding="utf-8")
        print(f"Wrote Voilà notebook: {nb_path}")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(get_output_dir().parent)

        subprocess.run(
            ["voila", str(nb_path), "--strip_sources=True", "--theme=auto"],
            check=False,
            env=env,
        )


###############################################################################
# Make a singleton
voila_heatmap = VoilaHeatmap()

# Run the singleton when run as a script
if __name__ == "__main__":
    voila_heatmap()
