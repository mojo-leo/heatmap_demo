#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Built-in modules
import webbrowser
from functools import cached_property

# Third-party modules
import pandas as pd
from d3blocks import D3Blocks

# Internal modules
from oak_trade_agent.data.baci_dataset import baci
from oak_trade_agent.paths import get_output_dir


###############################################################################
class D3BlocksHeatmap:
    """
    Resulting HTML file size is: 129KB
    """

    title = "Exporter → Importer heatmap (Top-N countries)"

    @cached_property
    def df(self) -> pd.DataFrame:
        return baci.ranked_oak_df

    @cached_property
    def max_n(self) -> int:
        return int(max(self.df["exporter_rank"].max(), self.df["importer_rank"].max()))

    def _pivot_for_n(self, top_n: int) -> pd.DataFrame:
        df = self.df[
            (self.df["exporter_rank"] <= top_n) & (self.df["importer_rank"] <= top_n)
        ]

        mat = df.pivot_table(
            index="importer_name",
            columns="exporter_name",
            values="quantity",
            aggfunc="sum",
            fill_value=0.0,
        )
        return mat

    def __call__(self, top_n: int = 10) -> None:
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / "d3blocks_static.html"

        mat = self._pivot_for_n(top_n)

        d3 = D3Blocks()
        d3.heatmap(
            mat,
            title=self.title,
            filepath=str(output_path),
        )

        print(f"Saved {output_path}")
        webbrowser.open(f"file://{output_path.absolute()}")


###############################################################################
# Make a singleton
d3blocks_heatmap = D3BlocksHeatmap()

# Run when executed as a script
if __name__ == "__main__":
    d3blocks_heatmap()
