""" 
This script populates a Comtrade datbase using biotrade and a data dump


- Remove the POSTGRESQL environment variables so that it creates an SQLite database instead.
    - commented out in bash aliases
    # export BIOTRADE_DATABASE_URL="postgresql://rdb@localhost:5433/biotrade"


Load the data from the BACI website:

    wget https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V202501.zip

uncompress:

"""



from biotrade.comtrade import comtrade

# Refresh the HS product list by downloading it again from the API
# Do this only once
# comtrade.pump.update_db_parameter()


def load_wood_trade_from_biotrade_dump():
    """ Load the wood trade data under HS code 44 Load monthly data for one 2
    digit level code and all child codes under it """
    file_path = comtrade.dump.data_dir / "raw_comtrade_yearly_44.csv.gz"
    comtrade.dump.load_2d_csv("monthly", file_path)



def load_from_baci_dump(file_path):
    """Load from BACI dump file"""



