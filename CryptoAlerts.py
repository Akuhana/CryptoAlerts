
import os, logging
import json
from binance_f import SubscriptionClient, RequestClient
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

logger = logging.getLogger("binance-futures")
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


# Load api keys
with open(os.path.join(os.path.dirname(__file__),"./config.json")) as f:
    data = json.load(f)
    api_key     = data["api_key"]
    api_secret  = data["api_secret"]


class Futures:

    markPrice = None

    def __init__(self, requests_only=False):
        if not requests_only:
            self.sub_client = SubscriptionClient(api_key=api_key, secret_key=api_secret)
        self.request_client = RequestClient(api_key=api_key, secret_key=api_secret)


    def callback(self, data_type: 'SubscribeMessageType', event: 'any'):
        if data_type == SubscribeMessageType.RESPONSE:
            print("Event ID: ", event)
        elif data_type == SubscribeMessageType.PAYLOAD:
            self.markPrice = event.markPrice         
        else:
            print("Unknown Data:")

    def error(self, e: 'BinanceApiException'):
        print(e.error_code + e.error_message)

    def start_listening(self, ticker="btcusdt"):
        self.sub_client.subscribe_mark_price_event(ticker, self.callback, self.error)
    
    def stop_listening(self):
        self.sub_client.unsubscribe_all()

    def get_price(self, ticker="btcusdt"):
        return self.request_client.get_mark_price(symbol=ticker).markPrice


if __name__ == "__main__":
    futures = Futures()
    print(futures.get_price())