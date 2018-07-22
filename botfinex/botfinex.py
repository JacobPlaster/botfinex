
import urllib.request
import time
import json
import config
import os
import logging
import EosInterface

TICKERS = [
    ("BTC", ["bitcoin", "btc", "bitcoins", "btcs"]),
    ("USD", ["dollars", "usd", "usds", "usdt", "tether", "dollar"]),
    ("ETH", ["eth", "ether", "eths", "ethereum", "ethereums", "ethers"]),
    ("EUR", ["eur", "euros", "euro", "eurs"]),
    ("EOS", ["eos", "eoss"])
]

# Mine
import NaturalLanguage

from threading import Thread

# Setup
logging.getLogger().setLevel(logging.DEBUG)

## make poll function
PATH_TO_NEXT_ID = 'nextUpdateId.txt'

# action definers
# These defined which process path the actions travel down
BUY_ORDER = ['buy', 'purchase', 'order', 'get']
SELL_ORDER = ['convert', 'sell']
SET_ACTION = ['make', 'set', 'create']
ALERT_ACTION = ['alert', 'remind', 'tell', 'message']
WHAT_ACTION = ['what', 'tell', 'display', 'whats', 'show', 'be', 'are', 'how', 'is', 'have']
CANCEL_ACTION = ['cancel', 'remove', 'delete', 'dispose', 'close']

nextUpdateId = None
## read next epected telegram id from local
if os.path.exists(PATH_TO_NEXT_ID):
    with open(PATH_TO_NEXT_ID) as f:
        for line in f:
            nextUpdateId = int(line)

def sendMessage(chatId, text):
    url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}&parse_mode=html".format(config.telegram['TOKEN'], chatId, text)
    logging.info('Polling Url={}'.format(url))
    r = contents = urllib.request.urlopen(url).read()

def getRootStatement(syntax):
    for index, item in enumerate(syntax):
        if item[2] == "ROOT" or item[0] == "how" or item[0] == "close":
            return syntax[index:]
            break

def getTickerByName(text):
    for pair in TICKERS:
        if text in pair[1]:
            return pair[0]
    return None

def getNumberByWord(textnum, numwords={}):
    print (textnum)
    try: 
        i = int(textnum)
        return i
    except ValueError:
        pass
    try:
        f = float(textnum)
        return f
    except ValueError:
        pass
    units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
    ]
    for index, w in enumerate(units):
        if w == textnum:
            return index
    return None

## Process an entire text input input
def processMessage(message):
    user = {
        "username": message['message']['chat']['username'],
        "chatid": message['message']['chat']['id']
    }
    text = message['message']['text'].lower()
    logging.info('Processing new message id={} from user={}'.format(message.get('update_id', 0), user['username']))
    # get syntax of text
    syntax = NaturalLanguage.parseSyntax(text)
    # remove unnecessary words from array
    syntax = getRootStatement(syntax)
    # Split into actions
    actions = []
    tmpAction = []
    for item in syntax:
        if item[1] == "CONJ":
            actions.append(tmpAction)
            tmpAction = []
        else:
            tmpAction.append(item)
    actions.append(tmpAction)
    logging.info('Parsed syntax actions={}'.format(actions))
    for action in actions:
        processAction(user, action)

# Process and action sequence ie ['buy', 'some', 'bitcoin']
def processAction(user, actionSyntax):
    # re-parse the syntax to find root
    text = ' '.join([x[0] for x in actionSyntax])
    syntax = NaturalLanguage.parseSyntax(text)
    # Find route and decide action to take
    rootItem = None
    for item in syntax:
        if (item[2] == 'ROOT' or item[0] == "how" or item[0] == "close"):
            rootItem = item
            break
    print (rootItem)
    # decide action based on route
    if processBuyAction(user, syntax, rootItem):
        print ('Buy order')
    elif processSellAction(user, syntax, rootItem):
        print ('Sell order')
    elif processWhatAction(user, syntax, rootItem):
        print ('What action')
    elif processAlertAction(user, syntax, rootItem):
        print ('Alert action')
    elif processCancelAction(user, syntax, rootItem):
        print ('Cancel action')
    else:
        print ('Unable to find an action')

'''
[('buy', 'VERB', 'ROOT'), ('me', 'PRON', 'IOBJ'), ('some', 'DET', 'DET'), ('neo', 'NOUN', 'DOBJ')]
[[('buy', 'VERB', 'ROOT'), ('4', 'NUM', 'NUM'), ('neo', 'NOUN', 'DOBJ')]]
[('buy', 'VERB', 'ROOT'), ('neo', 'NOUN', 'DOBJ'), ('at', 'ADP', 'PREP'), ('$35', 'NOUN', 'POBJ')]
[('buy', 'VERB', 'ROOT'), ('2', 'NUM', 'NUM'), ('neo', 'NOUN', 'DOBJ'), ('@', 'ADP', 'PREP'), ('$35', 'NOUN', 'POBJ')]
[('buy', 'VERB', 'ROOT'), ('2', 'NUM', 'NUM'), ('neo', 'NOUN', 'DOBJ'), ('with', 'ADP', 'PREP'), ('bitcoin', 'NOUN', 'POBJ')]
'''
def processBuyAction(user, actionSyntax, root):
    if root[0] not in BUY_ORDER:
        return False
    '''
    Find the first target of the buy order
    '''
    # find a target
    targetTicker = None
    amount = None
    # Incrememnt through nouns to find target
    for pair in actionSyntax:
        if pair[1] == "NOUN":
            targetTicker = getTickerByName(pair[0])
            if (targetTicker != None):
                break
    if targetTicker == None:
        return False
    # find an amount
    for pair in actionSyntax:
        if getNumberByWord(pair[0]):
            amount = getNumberByWord(pair[0])
            break
    '''
    Find the second target of the the buy order
    '''
    shortSyntax = []
    for index, pair in enumerate(actionSyntax):
        if pair[1] == 'ADP':
            shortSyntax = actionSyntax[index:]
            break
    toTargetTicker = None
    valueAmount = None
    for pair in shortSyntax:
        if pair[1] == "NOUN":
            toTargetTicker = getTickerByName(pair[0])
            if (toTargetTicker != None):
                break
     # find an amount
    for pair in shortSyntax:
        if getNumberByWord(pair[0]):
            valueAmount = getNumberByWord(pair[0])
            break

    if toTargetTicker:
        if valueAmount:
            EosInterface.createBuyOrder(targetTicker, toTargetTicker, amount, valueAmount)
            sendMessage(
                user['chatid'], 
                "Sure {}, I've opend an order to buy {} x {}/{} at a price of {}".format(user['username'], amount, targetTicker, toTargetTicker, valueAmount)
            )
            return True
        else:
            EosInterface.createBuyOrder(targetTicker, toTargetTicker, amount, 0)
            sendMessage(
                user['chatid'], 
                "Sure {}, I've opend an order to buy {} x {}/{} at market price".format(user['username'], amount, targetTicker, toTargetTicker)
            )
            return True
    EosInterface.createBuyOrder(targetTicker, 'USD', 99999999999999, 0)
    sendMessage(
        user['chatid'], 
        "Sure {}, I've opend an order to buy all {}/{} at market price".format(user['username'], targetTicker, 'USD')
    )
    return True

'''
[('sell', 'VERB', 'ROOT'), ('my', 'PRON', 'POSS'), ('all', 'DET', 'DOBJ'), ('of', 'ADP', 'PREP'), ('my', 'PRON', 'POSS'), ('neo', 'NOUN', 'POBJ')]
[('sell', 'VERB', 'ROOT'), ('my', 'PRON', 'POSS'), ('neo', 'NOUN', 'DOBJ'), ('into', 'ADP', 'PREP'), ('bitcoin', 'NOUN', 'POBJ')]
[('convert', 'VERB', 'ROOT'), ('my', 'PRON', 'POSS'), ('bitcoin', 'NOUN', 'DOBJ'), ('into', 'ADP', 'PREP'), ('neo', 'NOUN', 'POBJ')]
[('sell', 'VERB', 'ROOT'), ('my', 'PRON', 'POSS'), ('bitcoin', 'NOUN', 'DOBJ'), ('at', 'ADP', 'PREP'), ('24', 'NUM', 'POBJ')]
'''
def processSellAction(user, actionSyntax, root):
    if root[0] not in SELL_ORDER:
        return False
    # find a target
    targetTicker = None
    amount = None
    # Incrememnt through nouns to find target
    for pair in actionSyntax:
        if pair[1] == "NOUN":
            targetTicker = getTickerByName(pair[0])
            if (targetTicker != None):
                break
    if targetTicker == None:
        return False
    # find an amount
    for pair in actionSyntax:
        if getNumberByWord(pair[0]):
            amount = getNumberByWord(pair[0])
            break
    '''
    Find the second target of the the sell order
    '''
    shortSyntax = []
    for index, pair in enumerate(actionSyntax):
        if pair[1] == 'ADP':
            shortSyntax = actionSyntax[index:]
            break
    toTargetTicker = None
    valueAmount = None
    for pair in shortSyntax:
        if pair[1] == "NOUN":
            toTargetTicker = getTickerByName(pair[0])
            if (toTargetTicker != None):
                break
    # find an amount
    for pair in shortSyntax:
        if getNumberByWord(pair[0]):
            valueAmount = getNumberByWord(pair[0])
            break

    if toTargetTicker:
        if valueAmount:
            EosInterface.createSellOrder(targetTicker, toTargetTicker, amount, valueAmount)
            sendMessage(
                user['chatid'], 
                "Sure {}, I've opend an order to sell {} x {}/{} at a price of {}".format(user['username'], amount, targetTicker, toTargetTicker, valueAmount)
            )
            return True
        else:
            EosInterface.createSellOrder(targetTicker, toTargetTicker, amount, 0)
            sendMessage(
                user['chatid'], 
                "Sure {}, I've opend an order to sell {} x {}/{} at market price".format(user['username'], amount, targetTicker, toTargetTicker)
            )
            return True
    EosInterface.createSellOrder(targetTicker, 'USD', 999999999999, 0)
    sendMessage(
        user['chatid'], 
        "Sure {}, I've opend an order to sell all {}/{} at market price".format(user['username'], targetTicker, 'USD')
    )
    return True

'''
[('remind', 'VERB', 'ROOT'), ('me', 'PRON', 'DOBJ'), ('when', 'ADV', 'ADVMOD'), ('bitcoin', 'NOUN', 'NSUBJ'), ('reach', 'VERB', 'ADVCL'), ('20', 'NUM', 'DOBJ')]
[('set', 'VERB', 'ROOT'), ('a', 'DET', 'DET'), ('reminder', 'NOUN', 'DOBJ'), ('for', 'ADP', 'PREP'), ('bitcoin', 'NOUN', 'POBJ'), ('to', 'PRT', 'AUX'), ('hit', 'VERB', 'XCOMP'), ('12k', 'NOUN', 'DOBJ')]
'''
def processAlertAction(user, actionSyntax, root):
    if root[0] not in ALERT_ACTION:
        return False
    # fin an alert condition
    # 

'''
[('be', 'VERB', 'ROOT'), ('the', 'DET', 'DET'), ('price', 'NOUN', 'ATTR'), ('of', 'ADP', 'PREP'), ('bitcoin', 'NOUN', 'POBJ'), ('?', 'PUNCT', 'P')]
[('be', 'VERB', 'ROOT'), ('my', 'PRON', 'POSS'), ('balance', 'NOUN', 'ATTR'), ('?', 'PUNCT', 'P')]
[('be', 'VERB', 'ROOT'), ('my', 'PRON', 'POSS'), ('open', 'ADJ', 'AMOD'), ('order', 'NOUN', 'ATTR'), ('?', 'PUNCT', 'P')]
'''
def processWhatAction(user, actionSyntax, root):
    if root[0] not in WHAT_ACTION:
        return False
    ordersCalls = ['orders', 'trades', 'limits']
    '''
    {'BTCUSD': {'bids': [{'id': '18446744073709551613', 'account': 'testuser1111', 'clId': 123, 'price': '10000000000', 'qty': '100000000000', 'type': 1},
    {'id': '18446744073709551614', 'account': 'testuser1111', 'clId': 123, 'price': '10000000000', 'qty': '100000000000', 'type': 1}]},
    'BTCETH': {'bids': [{'id': '18446744073709551615', 'account': 'testuser1111', 'clId': 123, 'price': '10000000000', 'qty': '100000000000', 'type': 1}]},
    'ETHBTC': {'bids': [{'id': '18446744073709551615', 'account': 'testuser1111', 'clId': 123, 'price': '10000000000', 'qty': '100000000000', 'type': 1}]}}
    '''
    # check if user is trying to find open orders
    for action in actionSyntax:
        if (action[0] in ordersCalls):
            orders = EosInterface.getOrderBook()
            ordersString = ""
            orderCount = 0
            for key in orders.keys():
                ordersString += '%0A<b>' + key + '</b>%0A'
                print (orders[key])
                for ask in orders[key].get('asks', []):
                    id = str(bid['id'])
                    if (len(id) > 5):
                        id = id[-3:]
                    ordersString += '<b>' + id + '</b>'
                    ordersString += ". Quantity {} at price {}".format(ask['qty'], ask['price'])
                    ordersString += '%0A'
                    orderCount += 1
                for bid in orders[key].get('bids', []):
                    id = str(bid['id'])
                    if (len(id) > 5):
                        id = id[-3:]
                    ordersString += '<b>' +id + '</b>'
                    ordersString += ". Quantity {} at price {}".format(bid['qty'], bid['price'])
                    ordersString += '%0A'
                    orderCount +=1
            plural = "order" if orderCount == 1 else "orders"
            sendMessage(
                user['chatid'], 
                "You have {} {} open. %0A{}".format(orderCount, plural, ordersString)
            )
            return True
    balanceCalls = ['balance', 'wallets', 'funds', 'balances', 'money', 'much', 'many', 'own']
    for action in actionSyntax:
        if (action[0] in balanceCalls):
            balance = EosInterface.getBalance()
            targetTicker = None
            for pair in actionSyntax:
                toTargetTicker = getTickerByName(pair[0])
                if toTargetTicker != None:
                    break
            if (toTargetTicker):
                sendMessage(
                    user['chatid'],
                    "You have {} {} in your account.".format(balance[toTargetTicker], toTargetTicker)
                )
                return True
            else:
                balanceString = ""
                for key in balance.keys():
                    balanceString += "%0A" + str(balance[key])
                    balanceString += "<b> " + key + "</b>" 
                sendMessage(
                    user['chatid'], 
                    "Your full account balance is: %0A{}.".format(balanceString)
                )
                return True

def processCancelAction(user, actionSyntax, root):
    if root[0] not in CANCEL_ACTION:
        return False
    orderCalls = ['order', 'limit', 'trade']
    for action in actionSyntax:
        if (action[0] in orderCalls):
            print ("CANCELLING ORDER")
            # find number to cancel
            orderId = None
            for a in actionSyntax:
                if a[2] == "NUM":
                    print ("ORDER ID " + str(int(a[0])))
                    orderId = int(a[0])
            if not orderId:
                sendMessage(
                    user['chatid'], 
                    "Sorry, I was unable to find that order."
                )
                return True
            else:
                EosInterface.cancelOrder(orderId)
                sendMessage(
                        user['chatid'], 
                        "Great, I've now cancelled order {}".format(orderId)
                    )
                return True


## Poll Telegram for incoming messages
# Only grab the messages we havent processed using the nextUpdate and offset variables
while True:
    if not nextUpdateId:
        url = "https://api.telegram.org/bot{}/getUpdates".format(config.telegram['TOKEN'])
        logging.info('Polling Url={}'.format(url))
        r = contents = urllib.request.urlopen(url).read()
    else:
        url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(config.telegram['TOKEN'], nextUpdateId)
        logging.info('Polling Url={}'.format(url))
        r = contents = urllib.request.urlopen(url).read()

    newMessages = json.loads(r).get('result', [])
    if len(newMessages) > 0:
         nextUpdateId = newMessages[len(newMessages)-1]['update_id'] +1
         with open(PATH_TO_NEXT_ID, 'w') as f:
            f.write('%d' % nextUpdateId)

    newMessages = json.loads(r).get('result', [])

    time.sleep(2)

    for message in newMessages:
        thread = Thread(target = processMessage, args = (message,))
        thread.start()