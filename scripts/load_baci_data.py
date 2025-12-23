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

    there is a column k in the csv file and I only want to read the part of the
    file with pandas for the value 440791 for sawnwood oak and the other 6
    digit hs code fro roundwood oak.

"""
import pandas

def load_from_baci_dump(file_path, product_code):
    """Load from BACI dump file"""
    df = pandas.read_csv(file_path)
    # df.rename(columns=
    # Rename columns to 
    # t: year
    # i: exporter
    # j: importer
    # k: product
    # v: value
    # q: quantity
    return df




# Keep only the


