class Strategy(StrategyBase):
    def __init__(self):
        # strategy property
        self.subscribed_books = {
            'Bitfinex': {
                'pairs': ['ETH-USDT'],
            },
        }
        self.period = 4 * 60 * 60
        self.options = {}

        self.amount = 0
        self.proportion = 0.2

        self.mom_period = 10


    def on_order_state_change(self,  order):
        pass

    # called every self.period
    def trade(self, candles):
        exchange, pair, base, quote = CA.get_exchange_pair()
        
        close_price_history = [candle['close'] for candle in candles[exchange][pair]]
        high_price_history = [candle['high'] for candle in candles[exchange][pair]]
        low_price_history = [candle['low'] for candle in candles[exchange][pair]]
        open_price_history = [candle['open'] for candle in candles[exchange][pair]]

        # convert to chronological order for talib
        close_price_history.reverse()
        high_price_history.reverse()
        low_price_history.reverse()
        open_price_history.reverse()

        # convert to np.array
        close_price_history = np.array(close_price_history)
        high_price_history = np.array(high_price_history)
        low_price_history = np.array(low_price_history)
        open_price_history = np.array(open_price_history)

        close_price = close_price_history[-1]

        if len(close_price_history) < self.mom_period:
            return

        momentum = talib.MOM(close_price_history, self.mom_period)

        signal = 0
        
        # 3 continuous negative momentum
        if momentum[-3] < 0 and momentum[-2] < 0 and momentum[-1] < 0: 
            signal = 1
        
        # 3 continuous positive momentum
        if momentum[-3] > 0 and momentum[-2] > 0 and momentum[-1] > 0:
            signal = -1
        
        # get available balance
        base_balance = CA.get_balance(exchange, base)
        quote_balance = CA.get_balance(exchange, quote)
        available_base_amount = base_balance.available
        available_quote_amount = quote_balance.available

        if self.amount == 0:
            self.amount = np.round((available_quote_amount / close_price) * self.proportion, 5)
        
        # place buy order
        if signal == 1:
            amount = self.amount
            if available_quote_amount >= amount * close_price:
                CA.log('Buy ' + base)
                CA.buy(exchange, pair, amount, CA.OrderType.MARKET)

        # place sell order
        elif signal == -1:
            if available_base_amount > 0.00001:
                CA.log('Sell ' + base)
                CA.sell(exchange, pair, available_base_amount, CA.OrderType.MARKET)

        return
