"""
This script load trade data from the BACI website

Load the data from the BACI website:

    cd $HOME/repos/oak_trade_agent/data
    wget https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202501.zip

Uncompress:

    unzip BACI_HS22_V202501.zip

Test read with Pandas

    import pandas
    df = pandas.read_csv("BACI_HS22_Y2023_V202501.csv")
    # Oak sawnwood
    df.query("k == 440791")

    There is a column k in the csv file and I only want to read the part of the
    file with pandas for the value 440791 for sawnwood oak and the other 6
    digit hs code fro roundwood oak.

"""

import pandas


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


if __name__ == "__main__":
    df = load_from_baci_dump("data/BACI_HS22_Y2023_V202501.csv", 440791)
    # Oak sawnwood data
    oak = df
    #
