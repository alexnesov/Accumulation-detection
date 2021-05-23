# A class with two functions that we can optionnaly call?
from scipy.signal import savgol_filter
import pandas as pd
import numpy as np
from datetime import datetime, timedelta 
import yfinance as yf
import matplotlib.pyplot as plt
#pd.set_option('display.max_rows', None)

# Parameters
START = "2020-01-01"
tickers = ['MSFT', 'TSLA', 'AAPL', 'PG', 'INSG', 'PLUG']



def pull_data(ticker, START):
    """
    Pulls stock market data from yahoo finance

    :ticker: stock string identifier
    :param START: format yyyy-mm-dd
    """
    today = str(datetime.today().strftime('%Y-%m-%d'))
    df = yf.download(ticker, start = START, end = today, period = "1d")
    df = df.reset_index()
    return df 


df = pull_data('TSLA', '2021-01-01')

class local_extremas:
    """
    :param ticker: STRING, the ticker of the stock
    :param df: DATAFRAME, stock market data (OHLC)
    :param n: INT, n defines the level of granularity (the scope) for the second algo
    :args: pol and win_size are optionally modifiable for Savgol filter

    You can either go for all local mins by calling the "find_all_mins" method
    Or you can directly call the "minsOfmins" method
    """

    def __init__(self, ticker, df, n=5, pol=3, win_size=51):
        # instance attributes
        self.ticker = ticker
        self.df = df
        self.n = n
        self.mins = []
        self.nb_mins = 0
        self.merged = None
        self.all_local_mins = "deactivated"
        self.sav = "deactivated"
        self.localminMode = None

        # polynomial order & window_size for Savgol filter
        self.pol = pol
        self.win_size = win_size

    def __repr__(self):
        return '{Ticker:'+self.ticker+', number of local mins:'+str(self.nb_mins)+f' Mode: {self.localminMode} '+'}'

    def countMin(self):
        self.nb_mins = len(self.mins)
                
    def generateCalculatedMinsDF(self):
        """
        1. Takes output of filter. The output is a 
        list of indices indicate where the mins are
        2. Creates a flag column, every flag being crated thanks to this list of minds indices

        returns: dataframe
        """
        ones = [1] * len(self.mins)
        new_zip = list(zip(self.mins,ones))
        new_df = pd.DataFrame(new_zip, columns=['index','flag'])
        merged = self.df.merge(new_df, on='index', how='left')
        merged['flag_min'] = np.where(merged['flag'].notna(),1,0)
        merged = merged.set_index('Date')
        self.merged = merged


    def find_all_mins(self):
        """
        returns:  list of valid indices
        """
        valid = []
        self.df['index'] = list(range(0,len(self.df)))

        for index in list(self.df['Close'].index):
            try:
                if self.df['Close'][index] < self.df['Close'][index-1] and \
                    self.df['Close'][index] < self.df['Close'][index+1]:
                    valid.append(index)
            except KeyError:
                pass

        self.mins = valid
        self.generateCalculatedMinsDF()
        self.countMin()
        self.localminMode = 'allMins'

    def second_algorithm(self):
        """
        """
        self.df['index'] = list(range(0,len(self.df)))
        # broader local minimums
        final_mins_idx = []
        for i in self.mins:
            try:
                print(self.df['Close'][i])
                start = i - self.n
                end = i + self.n 
                interval = list(range(start,end))
                in_interval = []
                prices_in_interval = []
                for v in self.mins:
                    if v in interval:
                        in_interval.append(v)
                        prices_in_interval.append(self.df['Close'][v])
                
                indexes_mins = [i for i, x in enumerate(prices_in_interval) \
                    if x == min(prices_in_interval)]
                
                # usualy we are going to get only one min (the probability to 
                # get exact two same prices, on decimals level on a 10 days 
                # interval for a same stock if very very mpw). but we never know
                for i in indexes_mins:
                    final_mins_idx.append(in_interval[i])
            except KeyError:
                pass
        final_mins_idx_unique = np.unique(final_mins_idx)

        self.mins = final_mins_idx_unique
        self.from_idx_to_DF()
        self.countMin()
        self.localminMode = 'minsOfMins'


    def savgol(self):
        yhat = savgol_filter(self.df.Close, self.win_size, self.pol)
        self.sav = "activated"
        self.merged['Savgol'] = yhat
        self.generate_plot()

def generate_plot(df, ticker):
    """
    """
    fig = plt.figure(figsize=(15,8))
    ax1 = fig.add_subplot(111, ylabel='Close',xlabel='Date')
    df.Close.plot(ax=ax1, color='black', lw=2, alpha=0.4)
    ax1.plot(df.loc[df.flag_min == 1.0].index,
        df.Close[df.flag_min == 1.0],
        '^', markersize=9, color='purple', label='local min')
    # ax1.plot(df.loc[df.flag_max == 1.0].index,
    #     df.Close[df.flag_max == 1.0],
    #     '*', markersize=9, color='green', label='local max')
    ax1.grid(color='grey', linestyle='-', linewidth=0.25, alpha=0.6)
    ax1.spines["top"].set_visible(False)    
    ax1.spines["bottom"].set_visible(False)    
    ax1.spines["right"].set_visible(False)    
    ax1.spines["left"].set_visible(False) 
    ax1.set_title(f"{ticker}")
    ax1.legend()


def main():

    genExtremas = local_extremas('TSLA',df)
    genExtremas.df
    genExtremas.find_all_mins()
    genExtremas.generateCalculatedMinsDF()
    genExtremas.merged

    generate_plot(genExtremas.merged, ticker="TSLA")

if __name__ == '__main__':
    main()

