import requests
import pandas as pd
import ftplib
import io
import re
import json
import datetime

try:
    from requests_html import HTMLSession
except Exception:
    print("""Warning - Certain functionality 
             requires requests_html, which is not installed.
             
             Install using: 
             pip install requests_html
             
             After installation, you may have to restart your Python session.""")

try:
    import mplfinance as mpf
except Exception:
    print("""Warning - Certain functionality 
             requires mplfinance, which is not installed.
             
             Install using: 
             pip install mplfinance
             
             After installation, you may have to restart your Python session.""")    
    
base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"

def build_url(ticker, start_date = None, end_date = None, interval = "1d"):
    
    if end_date is None:  
        end_seconds = int(pd.Timestamp("now").timestamp())
        
    else:
        end_seconds = int(pd.Timestamp(end_date).timestamp())
        
    if start_date is None:
        start_seconds = 7223400    
        
    else:
        start_seconds = int(pd.Timestamp(start_date).timestamp())
    
    site = base_url + ticker + ".ns"
    
    params = {"period1": start_seconds, "period2": end_seconds,
              "interval": interval.lower(), "events": "div,splits"}
    
    
    return site, params


def force_float(elt):
    
    try:
        return float(elt)
    except:
        return elt
    
def _convert_to_numeric(s):

    if "M" in s:
        s = s.strip("M")
        return force_float(s) * 1_000_000
    
    if "B" in s:
        s = s.strip("B")
        return force_float(s) * 1_000_000_000
    
    return force_float(s)


def get_data(ticker, start_date = None, end_date = None, index_as_date = True,
             interval = "1d"):
    '''Downloads historical stock price data into a pandas data frame.  Interval
       must be "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d",
       "1wk", "1mo", or "3mo" for daily, weekly, monthly, or minute data.
       Intraday minute data is limited to 7 days.
    
       @param: ticker
       @param: start_date = None
       @param: end_date = None
       @param: index_as_date = True
       @param: interval = "1d"
    '''
    
    if interval not in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"):
        raise AssertionError("interval must be of '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo' or '3mo'")
    
    # build and connect to URL
    site, params = build_url(ticker, start_date, end_date, interval)
    resp = requests.get(site, params = params)
    
    if not resp.ok:
        raise AssertionError(resp.json())
        
    
    # get JSON response
    data = resp.json()
    
    # get open / high / low / close data
    frame = pd.DataFrame(data["chart"]["result"][0]["indicators"]["quote"][0])

    # get the date info
    tem_time = data["chart"]["result"][0]["timestamp"]
    temp_time = [time + 19800 for time in tem_time]

    frame.index = pd.to_datetime(temp_time, unit = "s")
    frame = frame[["open", "high", "low", "close", "volume"]]    
        
    frame['ticker'] = ticker.upper()
    
    if not index_as_date:  
        frame = frame.reset_index()
        frame.rename(columns = {"index": "date"}, inplace = True)
        
    return frame

'''
def tickers_nifty50(include_company_data = False):

    #Downloads list of currently traded tickers on the NIFTY 50, India

    site = "https://finance.yahoo.com/quote/%5ENSEI/components?p=%5ENSEI"
    table = pd.read_html(site)[0]
    
    if include_company_data:
        return table
    
    nifty50 = sorted(table['Symbol'].tolist())

    return nifty50
'''


def get_quote_table(ticker , dict_result = True): 
    
    '''Scrapes data elements found on Yahoo Finance's quote page 
       of input ticker
    
       @param: ticker
       @param: dict_result = True
    '''

    site = "https://finance.yahoo.com/quote/" + ticker + ".ns" + "?p=" + ticker + ".ns"
    
    tables = pd.read_html(site)

    data = tables[0].append(tables[1])

    data.columns = ["attribute" , "value"]
    
    quote_price = pd.DataFrame(["Quote Price", get_live_price(ticker)]).transpose()
    quote_price.columns = data.columns.copy()
    
    data = data.append(quote_price)
    
    data = data.sort_values("attribute")
    
    data = data.drop_duplicates().reset_index(drop = True)
    
    data["value"] = data.value.map(force_float)

    if dict_result:
        
        result = {key : val for key,val in zip(data.attribute , data.value)}
        return result
        
    return data


def _parse_json(url):
    html = requests.get(url=url).text

    json_str = html.split('root.App.main =')[1].split(
        '(this)')[0].split(';\n}')[0].strip()
    data = json.loads(json_str)[
        'context']['dispatcher']['stores']['QuoteSummaryStore']

    # return data
    new_data = json.dumps(data).replace('{}', 'null')
    new_data = re.sub(r'\{[\'|\"]raw[\'|\"]:(.*?),(.*?)\}', r'\1', new_data)

    json_info = json.loads(new_data)

    return json_info


def _parse_table(json_info):

    df = pd.DataFrame(json_info)
    del df["maxAge"]

    df.set_index("endDate", inplace=True)
    df.index = pd.to_datetime(df.index, unit="s")
 
    df = df.transpose()
    df.index.name = "Breakdown"

    return df


def get_live_price(ticker):
    
    '''Gets the live price of input ticker
    
       @param: ticker
    '''    
    
    df = get_data(ticker, end_date = pd.Timestamp.today() + pd.DateOffset(10))
    
    
    return df.close[-1]


def get_quote_data(ticker):
    
    '''Inputs: @ticker
    
       Returns a dictionary containing over 70 elements corresponding to the 
       input ticker, including company name, book value, moving average data,
       pre-market / post-market price (when applicable), and more.'''
    
    site = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + ticker + ".ns"
    
    resp = requests.get(site)
    
    if not resp.ok:
        raise AssertionError("""Invalid response from server.  Check if ticker is
                              valid.""")
    
    
    json_result = resp.json()
    info = json_result["quoteResponse"]["result"]
    
    return info[0]
    

def get_market_status():
    
    '''Returns the current state of the market - PRE, POST, OPEN, or CLOSED'''
    
    quote_data = get_quote_data("^dji")

    return quote_data["marketState"]

def get_premarket_price(ticker):

    '''Inputs: @ticker
    
       Returns the current pre-market price of the input ticker
       (returns value if pre-market price is available.'''
    
    quote_data = get_quote_data(ticker)
    
    if "preMarketPrice" in quote_data:
        return quote_data["preMarketPrice"]
        
    raise AssertionError("Premarket price not currently available.")

def get_postmarket_price(ticker):

    '''Inputs: @ticker
    
       Returns the current post-market price of the input ticker
       (returns value if pre-market price is available.'''
    
    quote_data = get_quote_data(ticker)
    
    if "postMarketPrice" in quote_data:
        return quote_data["postMarketPrice"]
    
    raise AssertionError("Postmarket price not currently available.")
    
