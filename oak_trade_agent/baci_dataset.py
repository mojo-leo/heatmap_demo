#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Built-in modules
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
from oak_trade_agent.paths import get_input_dir


###############################################################################
class BaciDataset:

    url = "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202501.zip"
    csv_name = "BACI_HS22_Y2023_V202501.csv"
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
        download_file(self.url, self.zip_path)

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
        path = f"zip://country_codes_V202501.csv::{self.zip_path}"
        with fsspec.open(path, mode="rt") as handle:
            df = pandas.read_csv(handle)
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

    def __call__(self) -> None:
        """Print some diagnostics."""
        # Show unique combination of country pairs
        print("N exporters:", len(self.oak_df["exporter_name"].unique()))
        print("N importers:", len(self.oak_df["importer_name"].unique()))
        pairs = self.oak_df[["exporter_name", "importer_name"]].drop_duplicates()
        print(pairs)


###############################################################################
# Make a singelton
baci = BaciDataset()
