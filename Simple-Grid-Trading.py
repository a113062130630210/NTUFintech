class Strategy(StrategyBase):
    def __init__(self):
        # strategy attributes
        self.period = 4*60*60
        self.subscribed_books = {
            'FTX': {
                'pairs': ['BTC-USD'],
            },
        }
        self.options = {}

        # define your attributes here
        self.upper = 54000 ###上界
        self.lower = 40000 ###下界
        self.average = 47800 ###
        self.fee = 0.07  ###手續費比例
        self.number = 60 ###60格網格
        self.amount = 0 ###買幾棵
        self.proportion = 0.7 ###買入比例
        self.total_transaction = 0 ###總交易量

        self.buy_line = [ int((self.average - self.lower ) / ( self.number/2) * i )+ int(self.lower)\
                             for i in range(int(self.number/2)) ] ### 切網格
        self.sell_line = [ int((self.upper - self.average ) / ( self.number/2) * i )+ int(self.average)\
                             for i in range(int(self.number/2)) ] ### 切網格
        self.last_line = 0
        pass

    def on_order_state_change(self,  order):
        pass

    def trade(self, candles):
        exchange, pair, base, quote = CA.get_exchange_pair()
        # Log(str(self.sell_line.reverse()))

        target_currency_amount = self['assets'][exchange][quote]
        close_price = candles[exchange][pair][0]['close']
        
        base_balance = CA.get_balance(exchange, base)
        quote_balance = CA.get_balance(exchange, quote)
        available_base_amount = base_balance.available
        available_quote_amount = quote_balance.available
        
        if self.amount == 0:
            self.amount = np.round((available_quote_amount / close_price) * self.proportion, 5)
            
        singal = 0 #  1 for buy, -1 for sell
        cur_line = 0
        if close_price > self.average:
            for  line in self.sell_line:
                idx = self.sell_line.index(line)
                if(close_price < line):
                    cur_line = self.sell_line[idx-1]
                    break
        else:
            for line in self.buy_line:
                idx = self.buy_line.index(line)
                if(close_price > line):
                    cur_line = self.buy_line[idx-1]
                    break
        if self.last_line != cur_line:
            if close_price > self.average: ### 賣
                signal = -1
            else:
                signal = 1                 ### 買
            self.last_line = cur_line
        else:
            signal = 0
        # Log(str(close_price) + "  " + str(cur_line) + "  " + str(signal))
        if signal == 1:
            amount = self.amount
            if available_quote_amount >= amount * close_price:
                CA.log('Buy ' + base)
                self.last_type = 'buy'
                CA.buy(exchange, pair, amount, CA.OrderType.MARKET)
                self.total_transaction += 1
        # place sell order
        elif signal == -1:
            if available_base_amount > 0.00001:
                CA.log('Sell ' + base)
                self.last_type = 'sell'
                CA.sell(exchange, pair, available_base_amount, CA.OrderType.MARKET)
                self.total_transaction += 1
