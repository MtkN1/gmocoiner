import json
import time
from logging import (
    DEBUG, FileHandler, Formatter, NullHandler, StreamHandler, getLogger)

from requests import Request, Session
from requests.exceptions import HTTPError

from .auth import GMOCoinAuth


class GMOCoin(object):
    """
    GMOコインAPIクライアント

    :param api_key: APIキー
    :type api_key: str
    :param secret: 秘密鍵
    :type secret: str
    :param late_limit: レート制限をクライアント制御する
    :type late_limit: bool
    :param logger: ロガー
    :type logger: Logger
    """
    endpoint = {
        'public': 'https://api.coin.z.com/public', 
        'private': 'https://api.coin.z.com/private'
    }

    def __init__(self, api_key, secret, late_limit=True, logger=None):
        self.logger = logger or getLogger(__name__)

        self.s = Session()
        self.s.headers['Content-Type'] = 'application/json'

        self.gmo_auth = GMOCoinAuth(api_key, secret)

        self.late_limit = late_limit
        self.last_req_time = 0
    
    def _request(self, method, path, payload, auth):
        for k, v in list(payload.items()):
            if v is None:
                del payload[k]

        if method == 'GET':
            body = None
            query = payload
        else:
            body = json.dumps(payload)
            query = None
        
        if not auth:
            endpoint = self.endpoint['public']
            self.s.auth = None
        else:
            endpoint = self.endpoint['private']
            self.s.auth = self.gmo_auth

        req = Request(method, endpoint + path, data=body, params=query)
        prepped = self.s.prepare_request(req)
        self.logger.debug(f'sending req to {prepped.url}: {prepped.body}')
        
        if self.late_limit:
            now = time.time()
            if self.last_req_time + 1 > now:
                wait_time = self.last_req_time + 1 - now
                time.sleep(wait_time)

        resp = None
        try:
            resp = self.s.send(prepped)
            resp.raise_for_status()
        except HTTPError as e:
            self.logger.error(e)
        
        if self.late_limit:
            self.last_req_time = time.time()

        self.logger.debug(f'{resp} {resp.text}')

        return resp

    # 
    # Public API
    # 

    def status(self):
        """
        取引所ステータス

        取引所の稼動状態を取得します。
        """
        payload = {}
        return self._request('GET', '/v1/status', payload, auth=False)

    def ticker(self, symbol):
        """
        最新レート

        指定した銘柄の最新レートを取得します。

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        """
        payload = {
            'symbol': symbol
        }
        return self._request('GET', '/v1/ticker', payload, auth=False)

    def orderbooks(self, symbol):
        """
        板情報

        指定した銘柄の板情報(snapshot)を取得します。

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        """
        payload = {
            'symbol': symbol
        }
        return self._request('GET', '/v1/orderbooks', payload, auth=False)

    def trades(self, symbol, page=None, count=None):
        """
        取引履歴

        指定した銘柄の取引履歴を取得します。

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        :param page: optional 取得対象ページ: 指定しない場合は1を指定したとして動作する。
        :type page: number
        :param count: optional 1ページ当りの取得件数: 指定しない場合は100(最大値)を指定したとして動作する。
        :type count: number
        """
        payload = {
            'symbol': symbol, 
            'page': page, 
            'count': count
        }
        return self._request('GET', '/v1/trades', payload, auth=False)

    # 
    # Private API
    # 

    def account_margin(self):
        """
        余力情報を取得

        指定した銘柄の取引履歴を取得します。
        対象: 現物取引、レバレッジ取引
        """
        payload = {}
        return self._request('GET', '/v1/account/margin', payload, auth=True)

    def account_assets(self):
        """
        資産残高を取得

        指定した銘柄の取引履歴を取得します。
        対象: 現物取引、レバレッジ取引
        """
        payload = {}
        return self._request('GET', '/v1/account/assets', payload, auth=True)

    def orders(self, orderId=None):
        """
        注文情報取得

        指定した注文IDの注文情報を取得します。
        対象: 現物取引、レバレッジ取引

        :param orderId: *required
        :type orderId: number
        """
        payload = {
            'orderId': orderId
        }
        return self._request('GET', '/v1/orders', payload, auth=True)

    def activeorders(self, symbol, page=None, count=None):
        """
        有効注文一覧

        有効注文一覧を取得します。
        対象: 現物取引、レバレッジ取引

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        :param page: optional 取得対象ページ: 指定しない場合は1を指定したとして動作する。
        :type page: number
        :param count: optional 1ページ当りの取得件数: 指定しない場合は100(最大値)を指定したとして動作する。
        :type count: number
        """
        payload = {
            'symbol': symbol, 
            'page': page, 
            'count': count
        }
        return self._request('GET', '/v1/activeOrders', payload, auth=True)

    def executions(self, orderId=None, executionId=None):
        """
        約定情報取得

        約定情報を取得します。
        対象: 現物取引、レバレッジ取引
            orderId executionId いずれか一つが必須です。2つ同時には設定できません。

        :param orderId: * orderId executionId いずれか一つが必須。
        :type orderId: number
        :param executionId: * orderId executionId いずれか一つが必須。
        :type executionId: number
        """
        payload = {
            'orderId': orderId, 
            'executionId': executionId
        }
        return self._request('GET', '/v1/executions', payload, auth=True)

    def latestexecutions(self, symbol, page=None, count=None):
        """
        最新の約定一覧

        最新約定一覧を取得します。
        対象: 現物取引、レバレッジ取引
            直近1日分の約定情報を返します。

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        :param page: optional 取得対象ページ: 指定しない場合は1を指定したとして動作する。
        :type page: number
        :param count: optional 1ページ当りの取得件数: 指定しない場合は100(最大値)を指定したとして動作する。
        :type count: number
        """
        payload = {
            'symbol': symbol, 
            'page': page, 
            'count': count
        }
        return self._request('GET', '/v1/latestExecutions', payload, auth=True)

    def openpositions(self, symbol, page=None, count=None):
        """
        建玉一覧を取得

        有効建玉一覧を取得します。
        対象: レバレッジ取引

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        :param page: optional 取得対象ページ: 指定しない場合は1を指定したとして動作する。
        :type page: number
        :param count: optional 1ページ当りの取得件数: 指定しない場合は100(最大値)を指定したとして動作する。
        :type count: number
        """
        payload = {
            'symbol': symbol, 
            'page': page, 
            'count': count
        }
        return self._request('GET', '/v1/openPositions', payload, auth=True)

    def positionsummary(self, symbol):
        """
        建玉ｻﾏﾘｰを取得

        建玉サマリーを取得します。
        対象: レバレッジ取引
            銘柄ごと、売買区分(買/売)ごとの建玉サマリー取得ができます。

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        """
        payload = {
            'symbol': symbol
        }
        return self._request('GET', '/v1/positionSummary', payload, auth=True)

    def order(self, symbol, side, executionType, size, price=None):
        """
        注文

        新規注文をします。
        対象: 現物取引、レバレッジ取引  

            現物取引: 買/売注文
            レバレッジ取引: 新規の買/売注文

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        :param side: *required BUY SELL
        :type side: str
        :param executionType: *required MARKET LIMIT
        :type executionType: str
        :param price: *executionTypeによる LIMIT の場合は必須、 MARKET の場合は不要。
        :type price: number
        :param size: *required
        :type size: str
        """
        payload = {
            'symbol': symbol, 
            'side': side, 
            'executionType': executionType, 
            'price': price, 
            'size': size, 
        }
        return self._request('POST', '/v1/order', payload, auth=True)

    def changeorder(self, orderId, price):
        """
        注文変更

        注文変更をします。
        対象: 現物取引、レバレッジ取引
        
        :param orderId: *required
        :type orderId: number
        :param price: *required
        :type price: str
        """
        payload = {
            'orderId': orderId, 
            'price': price
        }
        return self._request('POST', '/v1/changeOrder', payload, auth=True)

    def cancelorder(self, orderId):
        """
        注文キャンセル

        注文取消をします。
        対象: 現物取引、レバレッジ取引
        
        :param orderId: *required
        :type orderId: number
        """
        payload = {
            'orderId': orderId
        }
        return self._request('POST', '/v1/cancelOrder', payload, auth=True)

    def closeorder(self, symbol, side, executionType, 
                   settlePosition_positionId, settlePosition_size, price=None):
        """
        決済注文

        決済注文をします。
        対象: レバレッジ取引

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        :param side: *required BUY SELL
        :type side: str
        :param executionType: *required MARKET LIMIT
        :type executionType: str
        :param price: *executionTypeによる LIMIT の場合は必須、 MARKET の場合は不要。
        :type price: number
        :param settlePosition.positionId: *required 建玉は1つのみ指定可能。
        :type settlePosition.positionId: number
        :param settlePosition.size: *required 建玉は1つのみ指定可能。
        :type settlePosition.size: str
        """
        payload = {
            'symbol': symbol, 
            'side': side, 
            'executionType': executionType, 
            'price': price, 
            'settlePosition': [
                {
                    'positionId': settlePosition_positionId,
                    'size': settlePosition_size
                }
            ]
        }
        return self._request('POST', '/v1/closeOrder', payload, auth=True)

    def closebulkorder(self, symbol, side, executionType, size, price=None):
        """
        一括決済注文

        一括決済注文をします。
        対象: レバレッジ取引

        :param symbol: *required BTC ETH BCH LTC XRP BTC_JPY ETH_JPY BCH_JPY LTC_JPY XRP_JPY
        :type symbol: str
        :param side: *required BUY SELL
        :type side: str
        :param executionType: *required MARKET LIMIT
        :type executionType: str
        :param price: *executionTypeによる LIMIT の場合は必須、 MARKET の場合は不要。
        :type price: number
        :param size: *required
        :type size: str
        """
        payload = {
            'symbol': symbol, 
            'side': side, 
            'executionType': executionType, 
            'price': price, 
            'size': size
        }
        return self._request('POST', '/v1/closeBulkOrder', payload, auth=True)

    def changelosscutprice(self, positionId=None, losscutPrice=None):
        """
        ﾛｽｶｯﾄﾚｰﾄ変更

        建玉のロスカットレート変更をします。
        対象: レバレッジ取引
        
        :param positionId: *required
        :type positionId: number
        :param losscutPrice: *required
        :type losscutPrice: str
        """
        payload = {
            'positionId': positionId, 
            'losscutPrice': losscutPrice
        }
        return self._request('POST', '/v1/changeLosscutPrice', payload, auth=True)
