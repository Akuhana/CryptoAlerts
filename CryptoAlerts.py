
import logging, time
from binance_f import SubscriptionClient, RequestClient
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException
from binanceapi import BinanceAPI

logger = logging.getLogger("binance-futures")
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class Futures(BinanceAPI):

    markPrice = None

    def __init__(self, requests_only=False):
        super().__init__()
        
        if not requests_only:
            self.sub_client = SubscriptionClient(api_key=self.api_key, secret_key=self.api_secret)
        self.request_client = RequestClient(api_key=self.api_key, secret_key=self.api_secret)


    def callback(self, data_type: 'SubscribeMessageType', event: 'any'):
        if data_type == SubscribeMessageType.RESPONSE:
            print("Event ID: ", event)
        elif data_type == SubscribeMessageType.PAYLOAD:
            self.markPrice = event.markPrice         
        else:
            print("Unknown Data:")

    def error(self, e: 'BinanceApiException'):
        return e.error_code + e.error_message

    def start_listening(self, ticker="btcusdt"):
        self.sub_client.subscribe_mark_price_event(ticker, self.callback, self.error)
    
    def stop_listening(self):
        self.sub_client.unsubscribe_all()

    def get_price(self, ticker="btcusdt"):
        try:
            return self.request_client.get_mark_price(symbol=ticker).markPrice
        except BinanceApiException as e:
            return "Invalid symbol." if e.error_code == "ExecuteError" else e.error_message
            


if __name__ == "__main__":
    futures = Futures()
    print(futures.get_price())