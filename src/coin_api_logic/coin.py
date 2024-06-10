import requests


class CoinMarket(object):
    """Класс, позволяющий общаться с coinmarket."""

    def __init__(self, api_key: str):
        self.api_key: str = api_key
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }

    def get_current_price(self, symbol: list = "BTC", convert: str = "USD") -> dict:
        """Возвращает актуальную стоимость критовалюты."""
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'

        parameters = {
            'symbol': ','.join(map(str, symbol)),
            'convert': convert
        }

        response = requests.get(url, headers=self.headers, params=parameters)
        data = response.json()

        return {coin: data['data'][str(coin)]['quote']['USD']['price'] for coin in symbol}
