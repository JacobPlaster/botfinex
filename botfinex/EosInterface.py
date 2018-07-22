import requests
import urllib.request
import json

def createBuyOrder(ticker, ticker2, amount, value):
    print ("BUY ORDER")
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
    print ("SELL ORDER")
    payload = {
        "tickerFrom": ticker,
        "tickerTo": ticker2,
        "amount": -amount,
        "value": value
    }
    url = "http://localhost:3000/api/v1/orders/order/create"
    r = requests.post(url, json=payload)
    return r

def getBalance():
    url = "http://localhost:3000/api/v1/balance"
    r = urllib.request.urlopen(url).read()
    ret = json.loads(r)
    return ret

def getPriceOf():
    pass

def getOrderBook():
    url = "http://localhost:3000/api/v1/orders"
    r = urllib.request.urlopen(url).read()
    ret = json.loads(r)
    return ret

def cancelOrder(orderId):
    payload = {
        "orderId": orderId
    }
    url = "http://localhost:3000/api/v1/cancel"
    r = requests.post(url, json=payload)
    # ret = json.loads(r)
    return r

def getCurrentPrice(pair):
    url = "http://localhost:3000/api/v1/currentPrice/{}".format(pair)
    r = urllib.request.urlopen(url).read()
    ret = json.loads(r)
    return ret['price']
