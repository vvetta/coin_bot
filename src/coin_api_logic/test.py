import requests
from requests.exceptions import RequestException


def get_cryptocurrency_prices(coin_ids):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'bd1de36a-2f43-474b-b249-212c77502727',
    }
    parameters = {
        'symbol': ','.join(map(str, coin_ids)),  # Пример: '1,1027,825'
        'convert': 'USD'
    }
    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        data = response.json()
        return {coin: data['data'][str(coin)]['quote']['USD']['price'] for coin in coin_ids}
    except RequestException as e:
        print(f"Ошибка запроса: {e}")
        return {}


# Пример использования:
coin_ids = ["ETH", "SOL", "BTC"]  # ID для Bitcoin, Ethereum, Tether
prices = get_cryptocurrency_prices(coin_ids)
print(prices)
