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

class exp_date():
    def __init__(self,name):
        self.name = name
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
    def add_exp_date(self,new_date):
        #new_date = exp_date()
        self.exp_dates.append(new_date)
        
def get_options(response,stock_price,date_str): #removed stock argument from front of list
    soup = bs(response.text, "lxml")
    tables = soup.find_all('table')
    if len(tables)<2:
        print('No data')# for '+date_str)
        return None
    table = tables[1]
    rows = table.find_all('tr')  
    new_date = exp_date(date_str)
    for row in rows[1:]:
        strike_string = row.contents[2].text
        strike = float(strike_string.replace(',',''))
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
    return date_ux,two_months_ux

def populate_data(date_ux,two_months_ux,stock_price,op_chain): #TODO: remove stock price after added in function
    while date_ux < two_months_ux :
        #TODO: scrape for stock price in here or use yahoo finance package
        date_dt = datetime.utcfromtimestamp(date_ux)
        if date_dt.timetuple().tm_wday in [0,1,2,3,4]:
            url = 'https://finance.yahoo.com/quote/' + op_chain.name + '/options?date='+str(date_ux)+'&p='+ op_chain.name
            response = requests.get(url,headers={'user-agent':'Mozilla/5.0'})
            if response.status_code == 200:
                date_str = date_dt.strftime("%b_%d_%Y")
                print('Pulling data for '+op_chain.name+' '+date_str+' -- ',end=''),
                newest = get_options(response,stock_price,date_str)
                if newest != None:
                    op_chain.add_exp_date(newest)
        date_ux+=86400
#    return op_chain

#TODO:add a menu to get stock tickers
#get stock ticker
tickers = 'SPY','GOOG'

#get current stock price right now TODO:remove me when scraping function for stock is good to go.
stock_price = 253.4

#master list of option chains for tickers
MASTER = []

for ticker in tickers:
    #set stock class per ticker
    MASTER.append(stock_op_chain(ticker))


#get dates
date_ux,two_months_ux = get_date()
for TCKR in MASTER:
    #populate chain data
    populate_data(date_ux,two_months_ux,stock_price,TCKR)    


##TODO: loop through plots
SPY = MASTER[1]
#begin plot stuff

fig=plt.figure()
ax=plt.axes()#(projection='3d')
n=0
x_tics=[]
xaxis_label=[]

minvals=[]
maxvals=[]
lengths=[]
for lists in SPY.exp_dates:
    minvals.append(min(lists.strike_list))
    maxvals.append(max(lists.strike_list))
minval =min(minvals)
maxval =max(maxvals)
norm = mpl.colors.Normalize(vmin=minval,vmax=maxval)

for dates in SPY.exp_dates:
    premiums = [i*100 for i in dates.premium_list]
    im = ax.scatter(n*np.ones(len(premiums)),premiums,c=dates.strike_list,norm=norm ,cmap=cm.coolwarm)
    xaxis_label.append(dates.name)
    x_tics.append(n)
    n+=1

#dates for x axis
ax.xaxis.set_ticks(x_tics)
ax.xaxis.set_ticklabels(xaxis_label)
plt.xticks(rotation=45)

#ylabel
ax.set_ylabel('Premium')
plt.ylabel('% Premium',rotation =0)

#colorbar
cbar = fig.colorbar(im,ax=ax)
new = cbar.get_ticks()
new_labels = [f'{(-1*(100-(i/stock_price*100))):.2f}' +'%, $' + f'{(i):.2f}' for i in new]
cbar.ax.set_yticklabels(new_labels)
cbar.ax.set_ylabel('$ % out of Money')
plt.show()

