## Tradingboard

Often we manage multiple trading accounts and handling them at a single platform becomes a challenge. Though brokers offer their proprietary terminal, it requires sub-brokership which comes with hefty terms and conditions! This has motivated me to build Tradingboard.

**Tradingboard** is a lightweight, fast and easy-to-use app to manage multiple trading accounts through a single platform. This is built using open-source softwares and libraries like python and streamlit. With this, you can manage multiple accounts and check their

- [ ] Account details
- [ ] Available margin
- [ ] Positions
- [ ] Current P/L
- [ ] Place orders at multiple account in a single click
- [ ] Check their order status

At present, this can handle only AngelOne accounts. In following version, we will extend this to Zerodha, Upstox and others.

To use this, you need to create a `csv` file containing all the required credentials like

1.  Username
2.  mPin
3.  TOTP key
4.  API key

The username and mPin will be available once you open account. TheTOTP key and API key has to be retrieved from https://smartapi.angelbroking.com/

Once you have these for all the accounts, keep them in the following path "./data/data.csv" and hit following commands

Once you have these for all the accounts, keep them in the following path "../data/data.csv" in the format:

| name | user_name | broker | api_key | api_secret | access_token | status |
| --- | --- | --- | --- | --- | --- | --- |
| User1 | UUPO1008 | Angel | {API key} | {mPin} | {TOTP key} | Active |
| User2 | P880520 | Angel | {API key} | {mPin} | {TOTP key} | Active |
| User2 | UUPO1017 | Angel | {API key} | {mPin} | {TOTP key} | Active |

and run

```
streamlit run main.py

```

This needs the list of instruments which can be downloaded from [here](https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json "Angel Instruments") and should be saved at `../data/OpenAPIScripMaster.json` .

But the script already has a function to download it at fresh start.  You can refresh it from the interface as the list changes in the morning of every trading day.

This is one of my part-time project and I will keep adding features with time. Feel free to give your feedback, suggestion and contribute.

Reach me at [crchanda98@gmail.com](mailto:crchanda98@gmail.com)