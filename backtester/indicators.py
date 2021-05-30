import pandas as pd
import pandas_ta as ta
from stock_info import get_data
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import date, timedelta
import pandas_ta as ta

def stock_data(ticker, start, end, interval):
    # To get ticker data
    data = get_data(ticker, start_date=start, end_date=end, interval=interval)
    return data

def indicator(ticker, start, end, interval, s1, s2):
    data = stock_data(ticker, start, end, interval)

    # To append indicators in dataframe
    data.ta.sma(length=s1,append=True, min_periods=0)
    data.ta.sma(length=s2,append=True, min_periods=0)
    return data

    # To get all indicators
    #data.ta.indicators()

'''
def strate():
    # (1) Create the Strategy
    MyStrategy = ta.Strategy(
        name="Strategy1",
        description="SMA 20,50,100, RSI, MACD",
        ta=[
            {"kind": "sma", "length": 20},
            {"kind": "sma", "length": 50},
            {"kind": "sma", "length": 100},
            {"kind": "rsi"},
            {"kind": "macd", "fast": 8, "slow": 21},
        ]
    )

    # (2) Run the Strategy
    strat = data.ta.strategy(MyStrategy)
'''

def signal(ticker, start, end, interval, s1, s2):
    # Getting data and Initiating values
    data = indicator(ticker, start, end, interval, s1, s2)
    close = data['close']
    op = data['open']
    sma6 = data[data.columns[6]]
    sma7 = data[data.columns[7]]
    buy = []
    sell = []
    buys=0
    sells=0

    # Buy and Sell signals generation
    for i in range(len(close)):
        if op[i] > sma6[i]:
            if sma6[i] > sma7[i] and buys==0:
                buy.append(round(close[i],2))
                #index_b.append(data.index[i])
                buys = 1
                sells = 0
            else:
                buy.append(None)
            sell.append(None)
        elif op[i] < sma6[i]:
            if sma6[i] < sma7[i] and sells==0:
                sell.append(round(close[i],2))
                #index_s.append(data.index[i])
                sells = 1
                buys = 0
            else:
                sell.append(None)
            buy.append(None)
        else:
            buy.append(None)
            sell.append(None)
    return buy, sell


def net(ticker, start, end, interval, s1, s2):
    buy, sell = signal(ticker, start, end, interval, s1, s2)
    net_val = 0
    buys = []
    sells = []
    value = []
    for i in range(len(buy)):
        if buy[i]!=None:
            buys.append(buy[i])
        if sell[i]!=None:
            sells.append(sell[i])
    if len(buys)>len(sells):
        val = sells
    else:
        val = buys
    for i in range(len(val)):
        net_val = net_val + (sells[i] - buys[i])
        value.append(sells[i] - buys[i])
    return round(net_val,2)
#    return buys, sells, value


def plot(ticker, start, end, interval, s1, s2):
    # Get data with SMAs included
    if s1>s2:
        L1=s2
        L2=s1
    else:
        L1=s1
        L2=s2
    data = indicator(ticker, start, end, interval, L1, L2)
    sma6 = data[data.columns[6]]
    sma7 = data[data.columns[7]]

    # Buy and Sell signals
    buy, sell = signal(ticker, start, end, interval, L1, L2)
    data['buy'] = buy
    data['sell'] = sell
    buy_d = data['buy']
    sell_d = data['sell']

    # Customized style for charts
    mc = mpf.make_marketcolors(
                                up='tab:green',down='tab:red',
                                edge={'up':'green','down':'red'},
                                wick={'up':'green','down':'red'},
                                volume='tab:blue',
                               )
    style1  = mpf.make_mpf_style(marketcolors=mc,gridcolor='darkgrey',gridstyle='--')

    # Check if buy and sell in empty
    result1 = all(elem1 == None for elem1 in buy)
    result2 = all(elem2 == None for elem2 in sell)

    # Add plots for sma and markers
    if result1:
        if result2:
            ap = [mpf.make_addplot(sma6),
                mpf.make_addplot(sma7)
            ]
        else:
            ap = [mpf.make_addplot(sma6),
                mpf.make_addplot(sma7),
                mpf.make_addplot(sell_d, scatter=True, markersize=100, marker=11)
            ]
    elif result2:
        ap = [mpf.make_addplot(sma6),
            mpf.make_addplot(sma7),
            mpf.make_addplot(buy_d, scatter=True, markersize=100, marker=10)
        ]
    else:
        ap = [mpf.make_addplot(sma6),
            mpf.make_addplot(sma7),
            mpf.make_addplot(buy_d, scatter=True, markersize=100, marker=10),
            mpf.make_addplot(sell_d, scatter=True, markersize=100, marker=11)
        ]

#    ap = [  mpf.make_addplot(sma6),
#            mpf.make_addplot(sma7),
#            mpf.make_addplot(buy_d, scatter=True, markersize=100, marker=10),
#            mpf.make_addplot(sell_d, scatter=True, markersize=100, marker=11)
#        ]

    # To plot multiple graphs using mplfinance
    ind = ['SMA'+str(L1), 'SMA'+str(L2)]
    fig,ax = mpf.plot(data,type='candle',title='\n'+ticker.upper(),style=style1,volume=True,addplot=ap,returnfig=True)
    ax[0].legend(ind, loc='upper left')
    #plt.show()
    return fig

def plot_live(ticker, interval, s1, s2):
    # Deciding timelines
    today = date.today()
    yesterday = today - timedelta(days=1)
    day = yesterday.strftime("%A")
    if day=='Saturday':
        yesterday = today - timedelta(days=2)
    elif day=='Sunday':
        yesterday = today - timedelta(days=3)

    # Getting data
    if s1>s2:
        L1=s2
        L2=s1
    else:
        L1=s1
        L2=s2
    data = indicator(ticker, yesterday, today, interval, L1, L2)
    sma6 = data[data.columns[6]]
    sma7 = data[data.columns[7]]

    # Customized style for charts
    mc = mpf.make_marketcolors(
                                up='tab:green',down='tab:red',
                                edge={'up':'green','down':'red'},
                                wick={'up':'green','down':'red'},
                                volume='tab:blue',
                               )
    style1  = mpf.make_mpf_style(marketcolors=mc,gridcolor='darkgrey',gridstyle='--')

    # To plot multiple graphs using mplfinance
    ap = [  mpf.make_addplot(sma6),
            mpf.make_addplot(sma7)
        ]
    ind = ['SMA9'+str(L1), 'SMA20'+str(L2)]
    fig,ax = mpf.plot(data,type='candle',title='\n'+ticker.upper(),style=style1,volume=True,addplot=ap, returnfig=True)
    ax[0].legend(ind, loc='upper left')
    plt.show()
    #return fig, ax

