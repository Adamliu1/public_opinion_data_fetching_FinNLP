import sqlite3
import pandas as pd
# Easymoney
from finnlp.data_sources.news.eastmoney_streaming import Eastmoney_Streaming
from tqdm import tqdm
import time
import random

def init_db(db_name: str = "new_db.db"):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    return con, cur

def init_main_table(con: sqlite3.Connection, file: str = "000852cons.xls"):
    """
    NOTE: need to handle exception, TBD
    """
    # only support excel and csv for now
    main_df = pd.read_excel(file, dtype=str) if file.split(".")[-1] == "xls" else pd.read_csv(file, dtype=str)
    # print(main_df["成份券代码Constituent Code"])
    main_df.to_sql("MAINTABLE", con, if_exists='replace')

def fetch_news_data_eastmoney(stock_code: str, pages:int = 3):
    stock = stock_code
    # NOTE: maybe max_retry is not helpful here???? Since I modified the loop code for "fetch_and_process_to_db".
    config = {
        "use_proxy": "china_free",
        "max_retry": 10,
        "proxy_pages": 5,
    }

    news_downloader = Eastmoney_Streaming(config)
    try:
        news_downloader.download_streaming_stock(stock,pages)
        df = news_downloader.dataframe
        # selected_columns = ["title", "create time"]
        # df[selected_columns].head(10)
    except:
        df = None

    return df

# NOTE: TBD
def fetch_news_sina():
    raise NotImplemented

def append_info(df: pd.DataFrame, new_cols: list[str], vals: list[str]):
    res_df = df.copy()
    for idx, _ in enumerate(new_cols):
        res_df[_] = vals[idx]

    return res_df


def fetch_and_process_to_db(con: sqlite3.Connection):
    main_df = pd.read_sql(
    f'SELECT "成份券代码Constituent Code", "成份券名称Constituent Name" \
      FROM MAINTABLE;', con)
    
    # NOTE: manual continue task
    # main_df = main_df[400:]
    for _, r in tqdm(main_df.iterrows()):
        while True:
            tmp_df = fetch_news_data_eastmoney(r["成份券代码Constituent Code"])    
            print(f"cur_code:\n {r}")
            if tmp_df is not None:
                tmp_df = append_info(tmp_df, new_cols=["成份券代码Constituent Code", "成份券名称Constituent Name"], vals=r.to_list())
                tmp_df.to_sql("NEWSTALBE", con, if_exists='append')
                break
            else:
                print("ERROR HERE, SLEEP AND RETYRING...")
                print(f"current time: {time.ctime}")
                time.sleep(300) # if failed, wait 300 secs to retry process


def run_data_fetching():
    db_name = "new_data_000852.db"
    con, _ = init_db(db_name)
    init_main_table(con)
    fetch_and_process_to_db(con)


if __name__ == "__main__":
    run_data_fetching()