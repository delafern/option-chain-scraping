from bs4 import BeautifulSoup as bs
import requests
import urllib.request
#from googlefinance import getQuotes
import lxml
from datetime import date, datetime
import calendar

import numpy as np
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib as mpl

import re
from json import loads

class exp_date():
    def __init__(self,date):
        self.date = date
        self.strike_list = []
        self.bid_list = []
        self.premium_list = []
    def add_vals(self,strike,bid,premium):
        self.strike_list.append(strike)
        self.bid_list.append(bid)
        self.premium_list.append(premium)

class stock_op_chain():
    def __init__(self,name):
        self.name = name
        self.exp_dates = []
        self.stock_price = []
    def add_exp_date(self,new_date):
        #new_date = exp_date()
        self.exp_dates.append(new_date)
    def add_stock_price(self,stock_price):
        self.stock_price = stock_price
        
def get_options(response,stock_price,date_str):
    soup = bs(response.text, "lxml")
    table = soup.find('table',{'class':'puts'})    
    if table == None:
        print('No data')
        return None

    if 'class' not in table.attrs:
        print('No data')
        return None   
        
    if table.attrs['class'][0] !='puts':
        print('No data')
        return None

    rows = table.find_all('tr')  
    new_date = exp_date(date_str)
    for row in rows[1:]:
        strike_string = row.contents[2].text
        strike = float(strike_string.replace(',',''))
        if strike <= stock_price:
            bid = row.contents[4].text
            if bid =='-':
                bid = 0
            else:
                bid = float(bid)
            new_date.add_vals(strike,bid,(bid/strike))
    print('Success')    
    return new_date

def get_date():
    today_dt = date.today()
    date_ux = int(calendar.timegm(today_dt.timetuple()))
    two_months_ux = int(5184000 + date_ux)
    return two_months_ux

def populate_data(two_months_ux,op_chain): #can probably get rid of date ux
    url = 'https://finance.yahoo.com/quote/' + op_chain.name + '/options?'
    response = requests.get(url,headers={'user-agent':'Mozilla/5.0'})    
    soup = bs(response.text, "lxml")
    script = soup.find('script',text=re.compile('root.App.main')).text
    data = loads(re.search("root.App.main\s+=\s+(\{.*\})", script).group(1))    
    stock_str = data['context']['dispatcher']['stores']['QuoteSummaryStore']['price']['regularMarketPrice']['fmt']
    op_chain.add_stock_price(float(stock_str.replace(',','')))
    date_ux = data['context']['dispatcher']['stores']['OptionContractsStore']['meta']['expirationDates']
    n=0
    while date_ux[n] < two_months_ux:
        date_dt = datetime.utcfromtimestamp(date_ux[n])
        url = 'https://finance.yahoo.com/quote/' + op_chain.name + '/options?date='+str(date_ux[n])+'&p='+ op_chain.name
        response = requests.get(url,headers={'user-agent':'Mozilla/5.0'})
        if response.status_code == 200:
            date_str = date_dt.strftime("%b_%d_%Y")
            print('Pulling Option Chain for '+op_chain.name+' '+date_str+' -- ',end=''),
            newest = get_options(response,op_chain.stock_price,date_str)
            if newest != None:
                op_chain.add_exp_date(newest)
        n+=1
    
def normalize_cmap(TCKR):
    minvals=[]
    maxvals=[]
    lengths=[]
    for lists in TCKR.exp_dates:
        minvals.append(min(lists.strike_list))
        maxvals.append(max(lists.strike_list))
    minval =min(minvals)
    maxval =max(maxvals)
    norm = mpl.colors.Normalize(vmin=minval,vmax=maxval)
    return norm


#TODO:add a menu to get stock tickers
#get stock ticker
tickers = input("Input tickers as comma separated list (ie: SPY,GOOG,TSLA): ")
tickers = tickers.split(',')
#master list of option chains for tickers
MASTER = []

for ticker in tickers:
    #set stock class per ticker
    MASTER.append(stock_op_chain(ticker))

#get dates
two_months_ux = get_date()
for TCKR in MASTER:
    #populate chain data
    populate_data(two_months_ux,TCKR)    

print('Generating Plots')
plt.style.use('dark_background')

#loop through tickers, generate plots
fig = []
for TCKR in MASTER:
    fig.append(plt.figure())
    ax=plt.axes()
    n=0
    x_tics=[]
    xaxis_label=[]
    norm = normalize_cmap(TCKR)

    for dates in TCKR.exp_dates:
        premiums = [i*100 for i in dates.premium_list]
        im = ax.scatter(n*np.ones(len(premiums)),premiums,c=dates.strike_list,norm=norm ,cmap=cm.rainbow_r)
        xaxis_label.append(dates.date)
        x_tics.append(n)
        n+=1

    #dates for x axis
    ax.xaxis.set_ticks(x_tics)
    ax.xaxis.set_ticklabels(xaxis_label)
    plt.xticks(rotation=45)

    #ylabel
    plt.ylabel('% Premium')

    #colorbar
    cbar = plt.colorbar(im,ax=ax,orientation ='horizontal',pad=0.2)
    new = cbar.get_ticks()
    new_labels = [f'{(1*(100-(i/TCKR.stock_price*100))):.2f}' +'% / $' + f'{(i):.2f}' for i in new]
    cbar.ax.set_xticklabels(new_labels)
    cbar.ax.set_xlabel('% Out Of Money / Strike')

    #grid
    plt.grid(True,linewidth='.5',linestyle='--',color='lightgray')
    
    #title
    plt.title(TCKR.name+ ' Option Chain',fontsize = 15)

plt.show()