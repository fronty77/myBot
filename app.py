import json
from flask import Flask, request
import time
import base64
import hmac
import requests
import hashlib
import uuid

app = Flask(__name__)

# load config.json
with open('config.json') as config_file:
    config = json.load(config_file)


@app.route('/')
def index():
    return {'message': 'Server is running!'}


@app.route('/webhook', methods=['POST'])
def webhook():
    print("Hook Received!")
    print(request.data)
    data = json.loads(request.data)

    current_price = float(requests.get(f'https://api.kucoin.com/api/v1/market/stats?symbol={data["order_data"]["symbol"]}')["last"])
    price_after_when_stop_loss = str(current_price - (current_price * int(data["order_data"]["loss_percentage"]) / 100))

    if int(data['key']) != config['KEY']:
        print("Invalid Key, Please Try Again!")
        return {
            "status": "error",
            "message": "Invalid Key, Please Try Again!"
        }

    if data['order_type'] == 'buy':
        post_url = 'https://api.kucoin.com/api/v1/stop-order'
        api_key = config['auth']['api_key']
        api_secret = config['auth']['api_secret']
        api_passphrase = config['auth']['api_passphrase']
        now = int(time.time() * 1000)
        str_to_sign = str(now) + 'POST' + '/api/v1/stop-order'
        signature = base64.b64encode(
            hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
        passphrase = base64.b64encode(hmac.new(api_secret.encode(
            'utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": str(now),
            "KC-API-KEY": api_key,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }
        data_to_place = {
            'clientOid': uuid.uuid4(),
            'side': 'buy',
            'symbol': data['order_data']['symbol'],
            'type': 'market',
            'stop': 'loss',
            'stopPrice': price_after_when_stop_loss,
            'fund': data['order_data']['howmuch']
        }
        response = requests.request(
            'post', post_url, headers=headers, data=data_to_place)
        print('==', 'Buy has been triggered', data['order_data']['quantity'], 'with pair', data['order_data']['symbol'], '==')
        return {'message': 'success'}

    if data['order_type'] == 'sell':
        post_url = 'https://api.kucoin.com/api/v1/orders'
        api_key = config['auth']['api_key']
        api_secret = config['auth']['api_secret']
        api_passphrase = config['auth']['api_passphrase']
        now = int(time.time() * 1000)
        str_to_sign = str(now) + 'POST' + '/api/v1/stop-order'
        signature = base64.b64encode(
            hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
        passphrase = base64.b64encode(hmac.new(api_secret.encode(
            'utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
        headers = {
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": str(now),
            "KC-API-KEY": api_key,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }
        data_to_place = {
            'clientOid': uuid.uuid4(),
            'side': 'sell',
            'symbol': data['order_data']['symbol'],
            'type': 'market',
        }
        response = requests.request(
            'post', post_url, headers=headers, data=data_to_place)
        print('==', 'Buy has been triggered', data['order_data']['quantity'], 'with pair', data['order_data']['symbol'], '==')
        return {'message': 'success'}

    else:
        print("Invalid Exchange, Please Try Again!")
        return {
            "status": "error",
            "message": "Invalid Exchange, Please Try Again!"
        }


if __name__ == '__main__':
    app.run(debug=False)
