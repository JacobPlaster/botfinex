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
    } else if (CORE_TICKERS.includes(tickerTo)) {
        amount = -req.body.amount;
        pair = `${tickerTo}${tickerFrom}`;
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
    Promise.all(pairs.map((pair) => openOrders(pair)))
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
        })
        .then((data) => res.json(data))
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

function openOrders(pair) {
    return new Promise((resolve, reject) => {
        sb.orderbook(pair, { user: username }, (err, res) => {
            if (err) return reject(err);
            resolve(res);
        })
    })
}


app.listen(PORT, () => console.log(`Eosfinex interface running on ${PORT}`))