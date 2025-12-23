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
    digit hs code from roundwood oak.

"""

import pandas
import os
import inspect
import zipfile

# Get current directory
file_name = inspect.getframeinfo(inspect.currentframe()).filename
this_dir = os.path.dirname(os.path.abspath(file_name)) + "/"

# The path to the CSV file with all the data
baci_file = this_dir + "../data/BACI_HS22_Y2023_V202501.csv"


def load_from_baci_dump(file_path, product_code):
    """Load from BACI dump file"""
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


def download_baci_file(baci_file):
    """Downloads the baci file from the BACI website and uncompresses it."""
    from py3_wget import download_file

    url = "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202501.zip"
    download_file(url, baci_file)
    # Uncompress the file
    with zipfile.ZipFile(baci_file, "r") as zip_ref:
        zip_ref.extractall(cache_directory)


def get_baci_file():
    """Checks if the baci file is loacated in the cache firectory already.
    If it is not, then it downloads it.
    Returns the file path to the baci file.
    """
    cache_directory = this_dir + "../data/"
    if not os.path.exists(cache_directory):
        os.makedirs(cache_directory)
    short_name = "BACI_HS22_Y2023_V202501.csv"
    baci_file = os.path.join(cache_directory, short_name)
    if not os.path.exists(baci_file):
        download_baci_file(baci_file)
    return baci_file


def example():
    # Load the dataframe
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
