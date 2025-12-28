#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
import base64
import gzip
from functools import cached_property
from pathlib import Path

# Third-party modules
import fsspec
import pandas
from py3_wget import download_file
from rich import print as rprint
from rich.padding import Padding
from rich.panel import Panel

# Internal modules
from heatmap_demo.paths import get_input_dir, get_output_dir


###############################################################################
class BaciDataset:
    """
    This class downloads the BACI dataset and provides a pandas dataframe with the
    data. It also provides a method to get the country codes and a ranked dataframe
    with the countries ranked by total quantity (exports + imports).
    """

    url = "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202501.zip"
    csv_name = "BACI_HS22_Y2023_V202501.csv"
    md5_sum = "9fcebe4ce5e404db20f0040f9cf5f37f"
    col_names = {
        "t": "year",
        "i": "exporter",
        "j": "importer",
        "k": "product",
        "v": "value",
        "q": "quantity",
    }

    @property
    def zip_path(self) -> Path:
        """The path where the ZIP file with all the data is stored."""
        return get_input_dir() / "BACI_HS22_V202501.zip"

    def __bool__(self) -> bool:
        """Returns True if the dataset is downloaded, False otherwise."""
        return self.zip_path.exists()

    def download(self) -> None:
        """Downloads the dataset from the BACI website and uncompresses it."""
        # So the user knows why it's taking time #
        msg = (
            "The dataset '%s' has not been downloaded yet."
            " This process will start now and might take some time"
            " depending on your internet connection. Please be"
            " patient. The result will be saved to '%s'. You can"
            " override this by setting the $%s environment variable."
        )
        msg = msg % (self.csv_name, self.zip_path, "OAK_TRADE_INPUT_DIR")
        title = "Large Download"
        rprint(Padding(Panel(msg, title=title, padding=2, expand=False), (2, 10)))
        download_file(self.url, self.zip_path, md5=self.md5_sum)

    @property
    def df(self) -> pandas.DataFrame:
        """The dataframe with all the data."""
        if not self:
            self.download()
        path = f"zip://{self.csv_name}::{self.zip_path}"
        with fsspec.open(path, mode="rt") as handle:
            df = pandas.read_csv(handle)
        # The columns are not named as we would like them to be
        df.rename(
            columns=self.col_names,
            inplace=True,
        )
        return df

    @property
    def country_codes(self) -> pandas.DataFrame:
        """This file is actually corrupted on the source end.
        Look for the mojibake bytes for "CÃ´te" stored as UTF-8:

            with fsspec.open(path, mode="rb") as f:
                blob = f.read(200_000)
                needle = "CÃ´te".encode("utf-8")
                print(needle)          # b'C\xc3\x83\xc2\xb4te'
                print(needle in blob)  # True
        """
        path = f"zip://country_codes_V202501.csv::{self.zip_path}"
        with fsspec.open(path, mode="rb") as handle:
            df = pandas.read_csv(handle, encoding="utf-8")

        # Don't trust BACI to check their datasets, what does this
        # mean for the rest of their work?
        def fix_mojibake(s: str) -> str:
            if isinstance(s, str):
                try:
                    return s.encode("latin1").decode("utf-8")
                except UnicodeError:
                    return s
            return s

        df = df.map(fix_mojibake)
        # Replace some country names so they fit better in small graphs
        df.replace(
            {
                "China, Hong Kong SAR": "Hong Kong",
                "Bolivia (Plurinational State of)": "Bolivia",
                "Bosnia Herzegovina": "Bosnia",
                "Russian Federation": "Russia",
                "Rep. of Korea": "Korea",
                "Rep. of Moldova": "Moldova",
                "United Arab Emirates": "UAE",
                "United Kingdom": "UK",
            },
            inplace=True,
        )
        return df

    @cached_property
    def oak_df(self) -> pandas.DataFrame:
        """The dataframe with only the oak data and the full country names."""
        df = self.df
        # Take only oak sawnwood
        df = df[df["product"] == 440791]
        # Switch to countries from numbers to names
        index = self.country_codes.set_index("country_code")["country_name"]
        df = df.assign(
            exporter_name=df["exporter"].map(index),
            importer_name=df["importer"].map(index),
        )
        return df

    @cached_property
    def country_ranks(self) -> pandas.Series:
        """
        Now we compute country ranks based on total quantity (exports + imports).
        1 = largest
        """
        exports = self.oak_df.groupby("exporter_name")["quantity"].sum()
        imports = self.oak_df.groupby("importer_name")["quantity"].sum()
        total = exports.add(imports, fill_value=0)
        ranks = total.rank(ascending=False, method="first").astype("int64")
        ranks.sort_values(ascending=True, inplace=True)
        return ranks

    @cached_property
    def ranked_oak_df(self) -> pandas.DataFrame:
        """Now we add those ranks to the dataframe.

        year  exporter  importer  product  ...  exporter_name  importer_name exporter_rank importer_rank
        2023       842       156   440791  ...    USA  China     1    2
        2023       842       191   440791  ...    USA  Croatia   1    3
        2023       842       251   440791  ...    USA  France    1    4
        2023       842       276   440791  ...    USA  Germany   1    5
        """
        df = self.oak_df
        df = df.assign(
            exporter_rank=df["exporter_name"].map(self.country_ranks),
            importer_rank=df["importer_name"].map(self.country_ranks),
        )
        df.sort_values(by=["exporter_rank", "importer_rank"], inplace=True)
        return df

    def diagnostics(self) -> None:
        """Print some diagnostics."""
        # Show unique combination of country pairs
        print("N exporters:", len(self.oak_df["exporter_name"].unique()))
        print("N importers:", len(self.oak_df["importer_name"].unique()))
        pairs = self.oak_df[["exporter_name", "importer_name"]].drop_duplicates()
        print(pairs)

    @property
    def json(self) -> str:
        """Returns the JSON representation of the ranked oak dataframe.

        You will get something like:
        [{"year":2023,"exporter":842,"importer":156,"product":440791,"value":270331.285,"quantity":170800.681,"exporter_name":"USA","importer_name":"China","exporter_rank":1,"importer_rank":2},{"year":2023, ...
        """
        return self.ranked_oak_df.to_json(orient="records")

    @cached_property
    def json_gzip_base64(self) -> str:
        """Compress JSON string using gzip and encode as base64."""
        json_bytes = self.json.encode("utf-8")
        compressed = gzip.compress(json_bytes)
        return base64.b64encode(compressed).decode("utf-8")

    def __call__(self) -> None:
        """Export the uncompresseddataframe to a JSON file."""
        output_dir = get_output_dir()
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "baci_dataset.json"
        output_path.write_text(self.json)
        print(f"Saved {output_path}")


###############################################################################
# Make a singelton
baci = BaciDataset()

# Run the singleton when run as a script
if __name__ == "__main__":
    baci()
