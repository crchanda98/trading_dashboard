import traceback


def place_AO_order(
    _obj,
    _symb,
    _token,
    _qty,
    _exchange="NFO",
    _pos="SELL",
    _retry=False,
    _retry_param=1,
    _producttype="DELIVERY",
    _client_id="C00000",
):
    _iretry = 0
    _msg = "FAILURE"
    if _exchange == "NSE":
        _producttype = "DELIVERY"
    if _exchange == "NFO":
        _producttype = "CARRYFORWARD"
    if _exchange == "MCX":
        _producttype = "CARRYFORWARD"

    while _iretry < _retry_param:
        try:
            orderparams = {
                "variety": "NORMAL",
                "tradingsymbol": _symb,
                "symboltoken": str(_token),
                "transactiontype": _pos,
                "exchange": _exchange,
                "ordertype": "MARKET",
                "producttype": _producttype,
                "duration": "DAY",
                "quantity": str(_qty),
            }
            orderId = _obj.placeOrder(orderparams)
            _msg = "SUCCESS"
            _iretry = _retry_param
        except Exception as e:
            e = traceback.format_exc()
            print(e)

            if _iretry == _retry_param:
                print("Order did not pass through")
            _iretry += 1
