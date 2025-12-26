#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import webbrowser
from functools import cached_property

import holoviews as hv
import pandas as pd
import panel as pn
from panel.io import save as pn_save

from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir

hv.extension("bokeh")
pn.extension()


###############################################################################
class HoloViewsHeatmapStatic:
    """
    Resulting HTML file size is: 38.4 MB
    """

    title = "Exporter → Importer heatmap (resize by Top-N countries)"

    def __init__(self):
        df = baci.ranked_oak_df.copy()
        self.df = df

        self.max_n = int(max(df["exporter_rank"].max(), df["importer_rank"].max()))
        self.initial_n = min(10, self.max_n)

        self.exporters = (
            df[["exporter_name", "exporter_rank"]]
            .drop_duplicates()
            .sort_values("exporter_rank")["exporter_name"]
            .tolist()
        )
        self.importers = (
            df[["importer_name", "importer_rank"]]
            .drop_duplicates()
            .sort_values("importer_rank")["importer_name"]
            .tolist()
        )

        # IMPORTANT: keep a reference to the *exact* slider instance used in the app
        self.slider = pn.widgets.IntSlider(
            name="Top # countries",
            start=2,
            end=self.max_n,
            step=1,
            value=self.initial_n,
        )

    def _heatmap_for_n(self, n: int):
        x = self.exporters[:n]
        y = self.importers[:n]

        sub = self.df[
            self.df["exporter_name"].isin(x) & self.df["importer_name"].isin(y)
        ][["exporter_name", "importer_name", "quantity"]]

        mat = sub.pivot_table(
            index="importer_name",
            columns="exporter_name",
            values="quantity",
            aggfunc="sum",
            fill_value=0.0,
        ).reindex(index=y, columns=x, fill_value=0.0)

        long = mat.stack().rename("quantity").reset_index()

        return hv.HeatMap(
            long,
            kdims=["exporter_name", "importer_name"],
            vdims=["quantity"],
        ).opts(
            title=self.title,
            width=800,
            height=800,
            xrotation=90,
            tools=["hover"],
            colorbar=True,
            cmap="Viridis",
            xlabel="Exporter country",
            ylabel="Importer country",
        )

    @cached_property
    def app(self) -> pn.Column:
        view = pn.bind(self._heatmap_for_n, n=self.slider)
        return pn.Column(
            pn.pane.Markdown(f"## {self.title}"),
            self.slider,
            view,
            sizing_mode="stretch_width",
        )

    def __call__(self) -> None:
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "holoviews_static.html"

        all_states = list(range(2, self.max_n + 1))

        pn_save.save(
            self.app,
            output_path,
            embed=True,
            embed_states={self.slider: all_states},
            max_states=len(all_states),
            resources="cdn",
        )

        print(f"Saved {output_path} — open it in your browser.")
        webbrowser.open(f"file://{output_path.absolute()}")


###############################################################################
holoviews_heatmap_static = HoloViewsHeatmapStatic()

if __name__ == "__main__":
    holoviews_heatmap_static()
