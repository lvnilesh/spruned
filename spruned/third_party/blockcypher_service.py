from pip._vendor import requests
from spruned import settings
from spruned.service.abstract import RPCAPIService
from datetime import datetime


class BlockCypherService(RPCAPIService):
    def __init__(self, coin):
        self.client = requests.Session()
        self.BASE = 'https://api.blockcypher.com/v1/'
        self.coin = {
            settings.Network.BITCOIN: 'btc/main/',
            settings.Network.BITCOIN_TESTNET: 'btc/testnet/'
        }[coin]
        self._e_d = datetime(1970, 1, 1)

    def getrawtransaction(self, txid, **_):
        url = self.BASE + self.coin + 'txs/' + txid + '?includeHex=1&limit=1'
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        _c = data['confirmed'].split('.')[0]
        utc_time = datetime.strptime(_c, "%Y-%m-%dT%H:%M:%S")
        epoch_time = int((utc_time - self._e_d).total_seconds())
        return {
            'rawtx': data['hex'],
            'blockhash': data['block_hash'],
            'blockheight': data['block_height'],
            'confirmations': data['confirmations'],
            'time': epoch_time,
            'size': data['size'],
        }

    def getblock(self, blockhash):
        _s = 0
        _l = 500
        d = None
        while 1:
            url = self.BASE + self.coin + 'blocks/' + blockhash + '?txstart=%s&limit=%s' % (_s, _l)
            response = self.client.get(url)
            response.raise_for_status()
            res = response.json()
            if d is None:
                d = res
            else:
                d['txids'].extend(res['txids'])
            if len(res['txids']) < 500:
                break
            _s += 500
            _l += 500
        utc_time = datetime.strptime(d['time'], "%Y-%m-%dT%H:%M:%SZ")
        epoch_time = int((utc_time - self._e_d).total_seconds())
        return {
            'hash': d['hash'],
            'confirmations': None,
            'strippedsize': None,
            'size': d['size'],
            'weight': None,
            'height': d['height'],
            'version': d['ver'],
            'versionHex': None,
            'merkleroot': d['mrkl_root'],
            'tx': d['txids'],
            'time': epoch_time,
            'mediantime': None,
            'nonce': d['nonce'],
            'bits': d['bits'],
            'difficulty': None,
            'chainwork': None,
            'previousblockhash': d['prev_block'],
            'nextblockhash': None
        }

    def getblockheader(self, blockhash):
        raise NotImplementedError