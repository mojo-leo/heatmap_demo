"""
This script loads the trade data from the BACI website.

Load the data from the BACI website:

    cd $HOME/repos/oak_trade_agent/data
    wget https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202501.zip

Uncompress:

    unzip BACI_HS22_V202501.zip

Test read with Pandas:

    import pandas
    df = pandas.read_csv("BACI_HS22_Y2023_V202501.csv")
    # Oak sawnwood
    df.query("k == 440791")

    There is a column k in the csv file and I only want to read the part of the
    file with pandas for the value 440791 for sawnwood oak and the other 6
    digit hs code fro roundwood oak.

"""

import pandas
import os
import inspect
import requests
import zipfile


def load_from_baci_dump(file_path, product_code):
    """Load from BACI dump file

    cd /home/paul/rp/oak_trade_agent/
    ipython
    from scripts.load_baci_data import load_from_baci_dump
    df = load_from_baci_dump("data/BACI_HS22_Y2023_V202501.csv", 440791)

    """
    df = pandas.read_csv(file_path)
    df.rename(
        columns={
            "t": "year",
            "i": "exporter",
            "j": "importer",
            "k": "product",
            "v": "value",
            "q": "quantity",
        },
        inplace=True,
    )
    # Filter by product code
    df = df[df["product"] == product_code]
    # Load country codes
    country_df = pandas.read_csv("data/country_codes_V202501.csv")
    # Merge exporter names
    df = df.merge(
        country_df[["country_code", "country_name"]],
        left_on="exporter",
        right_on="country_code",
        how="left",
    )
    df.rename(columns={"country_name": "exporter_name"}, inplace=True)
    df.drop("country_code", axis=1, inplace=True)
    # Merge importer names
    df = df.merge(
        country_df[["country_code", "country_name"]],
        left_on="importer",
        right_on="country_code",
        how="left",
    )
    df.rename(columns={"country_name": "importer_name"}, inplace=True)
    df.drop("country_code", axis=1, inplace=True)
    return df


def select_n_largest_partners(df, n):
    """Select n largest exporters and importers for a given commodity and sum
    the rest of the values into an new importer called "ROW" for rest of the
    world

    Select the first n exporters based on total export quantity
    Select the first n importers based on total import quantity

    Input data:

    In [32]: df.head(2)
    Out[32]:
       year  exporter  importer  product   value  quantity exporter_name importer_name
    0  2023         8       196   440791  12.811     4.596       Albania        Cyprus
    1  2023        36        32   440791  26.174    16.852     Australia     Argentina

    Usage:

        cd /home/paul/rp/oak_trade_agent/
        ipython
        from scripts.load_baci_data import load_from_baci_dump
        from scripts.load_baci_data import select_n_largest_partners
        oak = load_from_baci_dump("data/BACI_HS22_Y2023_V202501.csv", 440791)
        select_n_largest_partners(oak, 5)

    """
    # Calculate total export quantity per exporter
    exporter_totals = (
        df.groupby("exporter_name")["quantity"].sum().sort_values(ascending=False)
    )
    top_exporters = exporter_totals.head(n).index.tolist()

    # Calculate total import quantity per importer
    importer_totals = (
        df.groupby("importer_name")["quantity"].sum().sort_values(ascending=False)
    )
    top_importers = importer_totals.head(n).index.tolist()

    # Create a copy of df
    df_copy = df.copy()

    # Aggregate non-top exporters
    non_top_exporters = df_copy[~df_copy["exporter_name"].isin(top_exporters)]
    if not non_top_exporters.empty:
        # Sum quantities and values for non-top exporters
        aggregated_exports = (
            non_top_exporters.groupby(["year", "importer_name", "product"])
            .agg({"value": "sum", "quantity": "sum"})
            .reset_index()
        )
        # Set exporter_name to 'ROW'
        aggregated_exports["exporter_name"] = "ROW"
        # Add a dummy exporter code, perhaps -1
        aggregated_exports["exporter"] = -1
        # Keep only necessary columns
        aggregated_exports = aggregated_exports[
            [
                "year",
                "exporter",
                "importer",
                "product",
                "value",
                "quantity",
                "exporter_name",
                "importer_name",
            ]
        ]
        # Note: importer and importer_name need to be matched, but since aggregated per importer, need to map back
        # Actually, since grouped by importer_name, need to get importer code
        # To do that, perhaps merge with original to get importer code
        importer_codes = df[["importer_name", "importer"]].drop_duplicates()
        aggregated_exports = aggregated_exports.merge(
            importer_codes, on="importer_name", how="left"
        )
        aggregated_exports = aggregated_exports[
            [
                "year",
                "exporter",
                "importer",
                "product",
                "value",
                "quantity",
                "exporter_name",
                "importer_name",
            ]
        ]

        # Remove non-top exporters from df_copy
        df_copy = df_copy[df_copy["exporter_name"].isin(top_exporters)]
        # Append aggregated
        df_copy = pandas.concat([df_copy, aggregated_exports], ignore_index=True)

    # Now, aggregate non-top importers
    non_top_importers = df_copy[~df_copy["importer_name"].isin(top_importers)]
    if not non_top_importers.empty:
        # Sum quantities and values for non-top importers
        aggregated_imports = (
            non_top_importers.groupby(["year", "exporter_name", "product"])
            .agg({"value": "sum", "quantity": "sum"})
            .reset_index()
        )
        # Set importer_name to 'ROW'
        aggregated_imports["importer_name"] = "ROW"
        # Add dummy importer code
        aggregated_imports["importer"] = -1
        # Get exporter codes
        exporter_codes = df[["exporter_name", "exporter"]].drop_duplicates()
        aggregated_imports = aggregated_imports.merge(
            exporter_codes, on="exporter_name", how="left"
        )
        aggregated_imports = aggregated_imports[
            [
                "year",
                "exporter",
                "importer",
                "product",
                "value",
                "quantity",
                "exporter_name",
                "importer_name",
            ]
        ]

        # Remove non-top importers from df_copy
        df_copy = df_copy[df_copy["importer_name"].isin(top_importers)]
        # Append aggregated
        df_copy = pandas.concat([df_copy, aggregated_imports], ignore_index=True)

    return df_copy


def download_baci_file(baci_file):
    """Downloads the baci file from the BACI website and uncompresses it."""
    url = "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202501.zip"
    response = requests.get(url)
    with open(baci_file, "wb") as file:
        file.write(response.content)
    # Uncompress the file
    with zipfile.ZipFile(baci_file, "r") as zip_ref:
        zip_ref.extractall(cache_directory)


def get_baci_file():
    """Checks if the baci file is loacated in the cache firectory already.
    If it is not, then it downloads it.
    Returns the file path to the baci file.
    """
    # Get current directory
    file_name = inspect.getframeinfo(inspect.currentframe()).filename
    this_dir = os.path.dirname(os.path.abspath(file_name)) + "/"
    cache_directory = this_dir + "../data/"
    if not os.path.exists(cache_directory):
        os.makedirs(cache_directory)
    short_name = "BACI_HS22_Y2023_V202501.csv"
    baci_file = os.path.join(cache_directory, short_name)
    if not os.path.exists(baci_file):
        download_baci_file(baci_file)
    return baci_file


def example():
    baci_file = get_baci_file()
    df = load_from_baci_dump(baci_file, 440791)
    # Oak sawnwood data
    selector = df["product"] == 440791
    oak = df.loc[selector].copy()
    selector = oak["exporter_name"] == "France"
    selector &= oak["importer_name"] == "China"
    oak.loc[selector]

    # Show unique combination of country pairs
    print("N exporters:", len(oak["exporter_name"].unique()))
    print("N importers:", len(oak["importer_name"].unique()))
    unique_pairs = oak[["exporter_name", "importer_name"]].drop_duplicates()
    print(unique_pairs)

    # Write to csv file for frontend
    oak.to_csv("data/oak.csv", index=False)
