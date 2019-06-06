import json

from gmocoiner import GMOCoin

if __name__ == '__main__':
    api_key = 'YOUR_API_KEY'
    secret = 'YOUR_SECRET_KEY'

    gmo = GMOCoin(api_key, secret, late_limit=True, logger=None)

    # ティッカー情報を表示
    resp = gmo.ticker(symbol='BTC_JPY')
    ticker = resp.json()
    print(json.dumps(ticker, indent=2))

    # 資産残高を表示
    resp = gmo.account_assets()
    print(json.dumps(resp.json(), indent=2))

    # 最寄買い気配地 - 5000の価格に買い指値
    buy = int(ticker['data'][0]['bid']) - 5000
    resp = gmo.order(symbol='BTC_JPY', side='BUY',
                     executionType='LIMIT', size='0.01', price=buy)
    print(json.dumps(resp.json(), indent=2))
