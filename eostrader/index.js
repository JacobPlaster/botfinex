const express = require('express');
const app = express();
const bodyParser = require('body-parser');
const PORT = 3000;


const Sunbeam = require('sunbeam')
const Eos = require('eosjs')

const readNodeConf = {
  httpEndpoint: 'http://35.189.86.89:8888',
  keyProvider: [
    '5KM3tHLwik5q91FALSkeqSRYPa6Kk7SpQn2BVdWusGLF4pG4f4F'
  ]
}

const writeNodeConf = {
  httpEndpoint: 'http://35.189.86.89:8888', // 'http://writenode.example.com'
  keyProvider: [
    '5KM3tHLwik5q91FALSkeqSRYPa6Kk7SpQn2BVdWusGLF4pG4f4F'
  ]
}
const eos = {
  Eos,
  readNodeConf,
  writeNodeConf
}

// dev: true allows one node for read and write
const username = 'testuser1111';
const opts = { dev: true, account: username }
const sb = new Sunbeam(eos, opts);

const TICKERS = [ 'BTC', 'USD', 'ETH', 'EUR', 'EOS' ]
const CORE_TICKERS = [ 'BTC', 'ETH', 'EOS' ]

// parse application/json
app.use(bodyParser.json());                        

// parse application/x-www-form-urlencoded
app.use(bodyParser.urlencoded({ extended: true }));
  

app.post('/api/v1/orders/order/create', (req, res) => {
    console.log('POST Opening Order');
    const tickerFrom = req.body.tickerFrom;
    const tickerTo = req.body.tickerTo;
    const value = req.body.value;

    let pair = null;
    let amount = 0
    if (CORE_TICKERS.includes(tickerFrom)) {
        amount = req.body.amount;
        pair = `${tickerFrom}${tickerTo}`;
        console.log('1:' + amount)
    } else if (CORE_TICKERS.includes(tickerTo)) {
        amount = req.body.amount;
        pair = `${tickerTo}${tickerFrom}`;
        console.log('2:' + amount)
    } else {
        res.status(401).json({ error: 'Inavlid trading pair'});
        return;
    }
    const payload = {
        symbol: pair,
        price: value.toString(),
        amount: amount,
        type: 'EXCHANGE_LIMIT',
        clientId: '123'
    }
    console.log(payload);
    const order = sb.createOrder(payload)
    return new Promise((resolve, reject) => {
        sb.place(order, (err, res) => {
            if (err) return reject(err)
            return resolve();
        })
    })
    .then(() => res.status(200).json({ status: 'OK' }))
})

app.get('/api/v1/orders', (req, res) => {
    console.log('GET Getting orders');
    return getAllOpenOrders()
        .then((data) => {
            console.log(data);
            return res.json(data)
        })
        .catch((err) => console.log(err))
});

app.get('/api/v1/balance', (req, res) => {
    console.log('GET Getting balance');
    return new Promise((resolve, reject) => {
        sb.balance((err, res) => {
            if (err) return reject(err);
            resolve(res);
        })
    })
    .then((data) => {
        balance = {};
        data.forEach((item) => {
            if(item.includes('BTC')) {
                balance['BTC'] = Number(item.replace(' BTC', ''));
            } else if (item.includes('USD')) {
                balance['USD'] = Number(item.replace(' USD', ''));
            } else if (item.includes('ETH')) {
                balance['ETH'] = Number(item.replace(' ETH', ''));
            } else if (item.includes('EUR')) {
                balance['EUR'] = Number(item.replace(' EUR', ''));
            } else if (item.includes('EOS'))  {
                balance['EOS'] = Number(item.replace(' EOS', ''));
            }
        })
        return balance
    })
    .then((data) => res.json(data));
});

app.post('/api/v1/cancel', (req, res) => {
    const orderId = req.body.orderId;
    console.log(`Cancelling order ${orderId}`)
    return getAllOpenOrders()
        .then((data) => {
            //  { EOSUSD: { asks: [ [Object] ] } }
            let keys = Object.keys(data);
            for (let i = 0; i < keys.length; i++) {
                let asks = data[keys[i]].asks || [];
                let bids = data[keys[i]].bids || [];
                for (let i2 = 0; i2 < asks.length; i2++) {
                    if (asks[i2].id === orderId) {
                        return { key: keys[i], orderId, side: 'ask' };
                    } else {
                        const idString = asks[i2].id.toString()
                        const shortId = idString.substring(idString.length - 3);
                        if (shortId === orderId) {
                            return { key: keys[i], orderId: asks[i2].id, side: 'ask' };
                        }
                    }
                }
                for (let i3 = 0; i3 < bids.length; i3++) {
                    if (bids[i3].id === orderId) {
                        return { key: keys[i], orderId, side: 'bid' }
                    } else {
                        const idString = bids[i3].id.toString()
                        const shortId = idString.substring(idString.length - 3);
                        if (shortId === orderId.toString()) {
                            return { key: keys[i], orderId: bids[i3].id, side: 'bid' };
                        }
                    }
                }
            }
        })
        .then((inOrderId) => {
            console.log(inOrderId);
            return new Promise((resolve, reject) => {
                console.log({
                    id: inOrderId.orderId,
                    symbol: inOrderId.key,
                    side: inOrderId.side
                });
                sb.cancel({
                    id: inOrderId.orderId,
                    symbol: inOrderId.key,
                    side: inOrderId.side
                }, {}, (err, res2) => {
                    if (err) return reject(err);
                    return resolve(res2);
                })
            })
        })
        .then(() => res.json({ status: 'OK' }))
        .catch((err) => console.log(err));
});

function getAllOpenOrders() {
    pairs = [ 
        'BTCUSD',
        'BTCETH',
        'BTCEUR',
        'BTCEOS',
        'ETHUSD',
        'ETHEUR',
        'ETHEOS',
        'EOSUSD',
        'EOSEUR' 
    ];
    return Promise.all(pairs.map((pair) => openOrders(pair)))
        .then((data) => {
            orders = {}
            data.forEach((d, i) => {
                if (d.asks.length > 0) {
                    let o = d.asks.filter((order) => order.account === "testuser1111")
                    if (o.length > 0)
                        orders[pairs[i]] = { asks: o };
                }
                if (d.bids.length > 0) {
                    let o = d.bids.filter((order) => order.account === "testuser1111")
                    if (o.length > 0)
                        orders[pairs[i]] = {bids: o };
                }
            });
            return orders;
        });
}


function openOrders(pair) {
    return new Promise((resolve, reject) => {
        sb.orderbook(pair, { user: username }, (err, res) => {
            if (err) return reject(err);
            resolve(res);
        })
    })
}

/*
{
  "asks": [
    {
      "id": 1,
      "account": "testuser1555",
      "clId": 1,
      "price": "74100200000000",
      "qty": "10000000000",
      "type": 0
    },
    {
      "id": 2,
      "account": "testuser1555",
      "clId": 1,
      "price": "74100100000000",
      "qty": "10000000000",
      "type": 0
    },
    {
      "id": 3,
      "account": "testuser1555",
      "clId": 1,
      "price": "74100100000000",
      "qty": "10000000000",
      "type": 0
    },
    {
      "id": 4,
      "account": "testuser1555",
      "clId": 1,
      "price": "74100100000000",
      "qty": "10000000000",
      "type": 0
    },
    {
      "id": 5,
      "account": "testuser1555",
      "clId": 1,
      "price": "74100100000000",
      "qty": "10000000000",
      "type": 0
    },
    {
      "id": 6,
      "account": "testuser1555",
      "clId": 1,
      "price": "74100100000000",
      "qty": "10000000000",
      "type": 0
    },
    {
      "id": 7,
      "account": "testuser1555",
      "clId": 1,
      "price": "74100100000000",
      "qty": "10000000000",
      "type": 0
    }
  ],
  "bids": [
    {
      "id": "18446744073709551613",
      "account": "testuser1122",
      "clId": 125,
      "price": 1000000000,
      "qty": 1000000000,
      "type": 1
    }
  ]
}
*/

app.get('/api/v1/currentPrice/:pair', (req, res) => {
    console.log('GET Getting Current Price');
    const pair = req.params.pair;

    new Promise((resolve, reject) => {
        sb.orderbook(pair, {}, (err, reponse) => {
            if (err) return reject(err);  
            resolve(reponse);
        })
    })
    .then((data) => {
        const asks = data.asks;
        let lowestAsk = null;
        asks.forEach((ask) => {
            if (!lowestAsk || lowestAsk > ask.price) {
                lowestAsk = ask.price;
            }
        });
        return lowestAsk || 0;
    })
    .then((price) => res.json({ price }));
});


app.listen(PORT, () => console.log(`Eosfinex interface running on ${PORT}`))