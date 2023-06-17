import os
from datetime import datetime as dt, timedelta
from smartapi import SmartConnect
import pandas as pd
from datetime import datetime as dt, timedelta, date
import pyotp
import streamlit as st
import traceback
import time
import json
import numpy as np
import os
from yaml.loader import SafeLoader
import yaml
import requests
import utils
import wget

st.set_page_config(layout="wide")


@st.cache_data()
def get_client_info():
    _client_info = pd.read_csv("../data_lake/data.csv")
    _client_info = _client_info[_client_info.status == "Active"]
    _client_info = _client_info.drop_duplicates(subset="name", keep="last")
    _client_info = _client_info.set_index("name")
    return _client_info


@st.cache_data()
def download_ao_instruments():
    _url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    wget.download(_url, out="../data_lake/base_dir/")


download_ao_instruments()


@st.cache_data()
def read_instrument():
    _instruments_ao = pd.read_json("../data_lake/base_dir/OpenAPIScripMaster.json")
    return _instruments_ao


instruments_ao = read_instrument()


@st.cache_data()
def get_tradable_stocks():
    _list1 = instruments_ao[instruments_ao.symbol.str.contains("EQ")].symbol.tolist()

    _list1 += instruments_ao[
        (instruments_ao.exch_seg == "NFO")
        & (instruments_ao.name.isin(["NIFTY", "BANKNIFTY"]))
    ].symbol.tolist()
    _list1 += instruments_ao[(instruments_ao.exch_seg == "MCX")].symbol.tolist()
    return _list1


tradable_stocks = get_tradable_stocks()


@st.cache_data()
def get_client_info():
    _client_info = pd.read_csv("./df2.csv")
    _client_info = _client_info.drop_duplicates(subset="name", keep="last")
    _client_info = _client_info.set_index("name")
    return _client_info


client_info = get_client_info()


def get_ao_token(_symbol):
    global instruments_ao
    _idf = instruments_ao[instruments_ao.symbol == _symbol]
    _exchange = _idf.exch_seg.iloc[0]
    _token = _idf.token.iloc[0]
    _lot = _idf.lotsize.iloc[0]

    return _exchange, _token, _lot


def get_ao_lot(_symbol):
    global instruments_ao
    _idf = instruments_ao[instruments_ao.symbol == _symbol]
    _lot = _idf.lotsize.iloc[0]

    return _lot


@st.cache(allow_output_mutation=True)
def get_client_obj():
    _obj_dict = {}
    global client_info
    for i, itarget in client_info.iterrows():
        if itarget.broker == "Angel":
            username = itarget["user_name"]
            Password = itarget["api_secret"]
            Password = str(itarget["api_secret"]).zfill(4)
            ApiKey = itarget["api_key"]
            totp_key = itarget["access_token"]

            totp_key = pyotp.TOTP(totp_key)
            totp_key = totp_key.now()
            while True:
                try:
                    obj = SmartConnect(
                        api_key=ApiKey,
                    )
                    print(username, Password, totp_key)
                    data = obj.generateSession(username, Password, totp_key)
                    feedToken = obj.getfeedToken()
                    _obj_dict[i] = obj
                except:
                    time.sleep(2)
                    continue
                break

    return _obj_dict


obj_dict = get_client_obj()


def get_ord_list(_name, _lag_minute="all"):
    global client_info
    obj = obj_dict[_name]
    order_book = obj.orderBook()["data"]
    if order_book != None:
        order_list = pd.DataFrame.from_records(order_book)
        if len(order_list) > 0:
            order_list.updatetime = pd.to_datetime(
                order_list.updatetime, format="%d-%b-%Y %H:%M:%S"
            )
            if _lag_minute != "all":
                time_past = dt.now() - timedelta(minutes=_lag_minute)
                order_list = order_list[order_list.updatetime > time_past]
            order_list = order_list[
                [
                    "exchtime",
                    "tradingsymbol",
                    "quantity",
                    "averageprice",
                    "transactiontype",
                    "orderid",
                    "exchtime",
                    "status",
                    "duration",
                ]
            ]
    else:
        order_list = pd.DataFrame()
    return order_list


def get_rms_limit():
    global client_info, obj_dict
    _df_rms = pd.DataFrame()
    for i, itarget in client_info.iterrows():
        obj = obj_dict[i]
        _df_rms.loc[i, "rmsLimit"] = obj.rmsLimit()["data"]["net"]
    return _df_rms


def place_order_from_list(_clients, _symb, _qty, _pos):
    global client_info
    targets = client_info.loc
    lot_size = get_ao_lot(_symb)
    exchng, tokn, lot = get_ao_token(_symb)
    for iclient in _clients:
        itarget = client_info.loc[iclient]
        Client_ID = iclient
        obj = obj_dict[iclient]
        if exchng == "NSE":
            producttype = "DELIVERY"
        if exchng == "NFO":
            producttype = "CARRYFORWARD"
        if exchng == "MCX":
            producttype = "CARRYFORWARD"
        _qty = int(itarget.strategy_mul) * int(_qty)
        utils.place_AO_order(
            obj,
            _symb,
            int(tokn),
            _qty=int(_qty),
            _pos=_pos,
            _exchange=exchng,
            _producttype=producttype,
            _retry_param=2,
            _client_id=Client_ID,
        )


def get_position(_name):
    global client_info
    obj = obj_dict[_name]
    order_book = obj.position()["data"]
    if order_book != None:
        order_list = pd.DataFrame.from_records(order_book)
        if len(order_list) > 0:
            order_list = order_list[
                [
                    "tradingsymbol",
                    "netqty",
                    "cfbuyavgprice",
                    "unrealised",
                ]
            ]
            order_list = (
                order_list.groupby(["tradingsymbol"])[["netqty", "unrealised"]]
                .sum()
                .reset_index()
            )
            order_list = order_list.rename(
                {
                    "tradingsymbol": "Trading Symbol",
                    "netqty": "Net QUantity",
                    "unrealised": "Unrealised P/L",
                },
                axis=1,
            )
    else:
        order_list = pd.DataFrame()
    return order_list


def get_holding(_name):
    global client_info
    obj = obj_dict[_name]
    order_book = obj.position()["data"]
    if order_book != None:
        order_list = pd.DataFrame.from_records(order_book)
        if len(order_list) > 0:
            order_list = order_list[
                [
                    "tradingsymbol",
                    "quantity",
                    "averageprice",
                    "ltp",
                ]
            ]
            order_list = order_list.rename(
                {
                    "tradingsymbol": "Trading Symbol",
                    "quantity": "QUantity",
                    "averageprice": "Entry Price",
                    "ltp": "Last Traded Price",
                },
                axis=1,
            )
    else:
        order_list = pd.DataFrame()
    return order_list


client_list = client_info.index.tolist()
tickers = tuple(client_list)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Client info", "Order History", "Trade Punch", "Positions"]
)

with tab1:
    df_rms_limit = get_rms_limit()
    st.dataframe(df_rms_limit)
    if st.button("Reload instruments"):
        download_ao_instruments()
        read_instrument()
        st.write("Reloaded instruments")

with tab2:
    st.title("Get list of orders")
    option = st.selectbox("Select account", tickers, key=1)
    st.dataframe(get_ord_list(option).iloc[:, 1::])

with tab3:
    options = st.multiselect(
        "Fire trade at multiple accounts",
        tuple(client_list),
        key=19,
        default=tuple(client_list),
    )
    symbol = st.selectbox("Enter tradingsymbol", tuple(tradable_stocks))
    position = st.selectbox("Position", ("BUY", "SELL"), key=20)
    lot_size = get_ao_lot(symbol)
    st.text(f"Lot size is {lot_size}")
    qty = st.number_input("Lot size", step=1, key=21)
    if st.button("Place order", key=23):
        place_order_from_list(options, _symb=symbol, _qty=qty, _pos=position)
        st.write(options)


with tab4:
    option = st.selectbox("Select account", tickers, key=2)
    st.dataframe(get_position(option))
