from config import settings
from sqlalchemy import create_engine
import pandas as pd
from logger import LOGGER

bridge_address = '0:d19c5400e081ae772c7dd2dab07199097fc06672574ccc1015a8da8c7d4f32c5'

async def check(wallet: str) -> list:
    """Сheck if the address is a DEX or a bridge"""
    _db_ever_str = settings.get_database_src('evermarketparse')
    sql_eng =  create_engine(_db_ever_str)
    db_connect = sql_eng.connect()

    try:
        db_response = pd.read_sql(f"SELECT x.* FROM freeton_wallets.everscale_wallets x WHERE wallet like '{wallet}'", con=db_connect)
        LOGGER.info(str(db_response.to_dict()))
        db_connect.close()
        sql_eng.dispose()
        if db_response.empty:
            return ["SIMPLE_ADDRESS", '']
        else:
            db_response = db_response.to_dict()
            if (db_response['wallet'][0] == bridge_address):
                return ["BRIDGE", 'Octus Bridge']
            elif (db_response['type'][0] == 'dex'):
                return ["DEX", db_response['name'][0]]
            elif (db_response['type'][0] == 'exchange'):
                return ["CEX", db_response['name'][0]]
            elif (db_response['type'][0] == 'farming'):
                return ["FARMING", db_response['name'][0]]
            else:
                return ["SIMPLE_ADDRESS", '']
    except Exception as e:
        LOGGER.error(str(e))
        db_connect.close()
        sql_eng.dispose()
        return ["SIMPLE_ADDRESS", '']

