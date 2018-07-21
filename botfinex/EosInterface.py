import requests
import urllib.request
import json

def createBuyOrder(ticker, ticker2, amount, value):
    payload = {
        "tickerFrom": ticker,
        "tickerTo": ticker2,
        "amount": amount,
        "value": value
    }
    url = "http://localhost:3000/api/v1/orders/order/create"
    r = requests.post(url, json=payload)
    return r

def createSellOrder(ticker, ticker2, amount, value):
    payload = {
        "tickerFrom": ticker,
        "tickerTo": ticker2,
        "amount": amount,
        "value": value
    }
    url = "http://localhost:3000/api/v1/orders/order/create"
    r = requests.post(url, json=payload)
    return r

def getBalance():
    url = "http://localhost:3000/api/v1/balance"
    r = contents = urllib.request.urlopen(url).read()
    ret = json.loads(r)
    return ret

def getPriceOf():
    pass

def getOrderBook():
    url = "http://localhost:3000/api/v1/orders"
    r = contents = urllib.request.urlopen(url).read()
    ret = json.loads(r)
    return ret