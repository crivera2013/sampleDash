# Author: Christian Rivera

# Goal: Tutorial to show how to create a web app using Dash, Plotly with stock data from IEX and yahoo

from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from flask import Flask

from dash_table import DataTable  #create javascript tables

import plotly.graph_objs as go  #plots

import pandas as pd
import json
import requests
from sklearn.linear_model import LinearRegression
from pandas_datareader import data
from datetime import datetime as dt
import numpy as np



###################################################
#######			Style Section            #######
###################################################


#CSS template.  Determines the style of the webpage
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


# create 2 python dictionaries that represent changes to the CSS we will add to certain
# sections of the HTML
styling = {'font-family':'Georgia', 'font-size': '18px', 
				'padding': '10px', 'text-align': 'center'}

styling2 = { 'font-family':'Georgia', 'font-size': '18px',
				'padding': '10px',  'text-align': 'left'}

center_style = {'textAlign':'center','align':'center'}


###################################################
#######			Function Section            #######
###################################################

# Get list of possible securities
def getListSecurities():
	# pull the list of all securities from IEX
	url = 'https://api.iextrading.com/1.0/ref-data/symbols?filter=symbol'
	securities = requests.get(url)
	securities = securities.json()
	securities = pd.DataFrame(securities)
	securities['b'] = securities['symbol']
	securities.columns= ['label','value']
	securities = securities.to_dict('records')
	return securities

# Function that returns the OHLC data using Yahoo Finance and PandasDatareader package

def getStock(stock, startdate, enddate):

	results = data.DataReader(stock,'yahoo',startdate,enddate)
	# create a linear regression line
	lin_reg = LinearRegression().fit(np.array(range(results.shape[0])).reshape(-1,1),results['Adj Close'].values.reshape(-1,1))
	results['linreg'] = lin_reg.predict(np.array(range(results.shape[0])).reshape(-1,1))

	dates = list(results.index.strftime("%Y-%m-%d"))  #convert date to string as JSON only takes strings

	return results, dates


###################################################
#######			Flask Section                ######
###################################################

# Create our Flask Instance
server = Flask(__name__)

# Create our Dash app from our Flask server
app = Dash(name='app1', sharing=True,server=server, 
			csrf_protect=False, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions']=True



###################################################
#######			HTML Section                #######
###################################################


# Create the HTML layout for the webpage.
# This is the Dash python way of writing HTML.  You could also write HTML

# We will be creating a singe page web app with 2 tags:
#	Tab 1: an Ohlc graph that you can specify the stock, the date range, and a linear regression
#   Tab 2: sample markdown

# start with a parent div tag
app.layout = html.Div([    #app.layout = lines 100-194

	#create a title
	html.H1("I'm an H1 tag. Im at the top since I am first"),

	dcc.Tabs(id="tabs", children=[

	# create our first tab
	dcc.Tab(label='OHLC Chart', children=[

		# 1st horizontal div tag for showing the Chart
		html.Div([
			dcc.Graph(
				id='Ohlc-graph',
				config={
					'displayModeBar': False,
					'scrollZoom': True,
				}
			),

			### IMPORTANT !!!!!!!!!!!!
			### IMPORTANT !!!!!!!!!!!!
			#An Invisible Div tag we use to hide the data that the graph calls
			html.Div(id='hidden-stock-data', style={'display': 'none'})
		]),

		# 2nd horizontal div tag, 3 sub veritical div tags for 
		# selecting stock, date range, and show regression line
		html.Div([

			# 1st sub div: Select Stock
			html.Div([

				html.Label('Select Security',style = styling), #title for dropdown
				
				#create dropdown menu, fill menu with values from 'securities' variable
				dcc.Dropdown(
					options = getListSecurities(),
					value = 'NVDA',  #start value
					multi = False,
					clearable = False,
					id='dropdown-securities-menu', # to reference for update functions
				)
			]),


			# 2nd sub div: Date Range
			html.Div([

				html.Label("Date Range",style = styling),
				
				#Create Date Range picker
				dcc.DatePickerRange(
					id='date-range-menu',
					min_date_allowed=dt(2008,1,1),
					max_date_allowed=dt.now().date(),
					initial_visible_month=dt.now().date(),
					start_date=dt(dt.now().year-1,dt.now().month,dt.now().day-1).date(),
					end_date=dt(dt.now().year, dt.now().month, dt.now().day-1).date(),
					calendar_orientation='vertical',
					day_size=30,
					number_of_months_shown=1,
					#with_portal=True
					)

			]),


			# 3rd sub div: Radio Buttons to show linear regression off close
			html.Div([

				html.Label('Linear Regression Line',style = styling2),

				# Create Radio Buttons
				dcc.RadioItems(
					options=[
						{'label': 'Off', 'value': 0},
						{'label': 'Show', 'value': 1},
					],
					value=0,
					labelStyle={'display':'block','font-family':'Georgia',
								'font-size': '12px'},
					id='LinReg-RadioItems',
					style={'align':'left'}
				)
			])

		],style={'columnCount':3,'textAlign':'center','align':'center'})

	]),

	# 2nd tab for just having some markdown text
	dcc.Tab(label='Markdown Example', children=[
		dcc.Markdown('''
## You Remember Markdown Tabs don't you?
- Author: **Christian Rivera**
- Reference: [Actual Dashboard](https://asset-dashboard-cr.appspot.com)
		''')
	])

	])  #dcc.Tabs

])  ## Started all the way back at line 100


###################################################
#######			Callbacks Section           #######
###################################################

# Callbacks = when some part of the webpage changes, execute a function

# Inputs: callback activates when this (id) section of the page changes  
#			which returns some value
# State : Use stored value in this (id) section of the page 
# Output: Change the data in this (id) section of the page

# when the user picks a different Security or Date Range
@app.callback(
	Output(component_id="hidden-stock-data", component_property='children'),
	[
		Input(component_id='date-range-menu', component_property='start_date'),
		Input(component_id='date-range-menu', component_property='end_date'),
		Input(component_id='dropdown-securities-menu', component_property='value')	
	]
)
def get_and_hide_data(Input1, Input2, Input3):
	# Use the dynamic inputs as argument parameters to request EOD stock data from yahoo. 
	# Save 'df_stock' and 'dates' as values in a python dictionary. 
	# convert dictionary to JSON object
	# Hide JSON Object in div tag: 'hidden-stock-data'
	EOD_data , dates = getStock(Input3, Input1, Input2)

	# convert df_stock (a pandas dataframe) to a list of dictionaries
	# so that it is compatible with JSON format
	EOD_data = EOD_data.to_dict('records')

	result = {
		'EOD_data':EOD_data,  
		'dates' : dates, 
}

	return json.dumps(result)   #send result to 'hidden-stock-data' div


# When the hidden-stock-data or the linear regression buttons are changed
@app.callback(
	Output(component_id="Ohlc-graph", component_property='figure'),
	[
		Input(component_id='hidden-stock-data', component_property='children'),
		Input(component_id='LinReg-RadioItems', component_property='value')	
	],
	[ State(component_id='dropdown-securities-menu', component_property='value')]
)
def plot_the_ohlc_graph(hidden_json, linRegFlag, security_name):
	# convert the JSON object back to Dictionary
	extracted_dict = json.loads(hidden_json)

	# extract EOD_data and convert back to dataframe
	df_EOD = pd.DataFrame(extracted_dict['EOD_data'])
	df_EOD['Date'] = pd.to_datetime(extracted_dict['dates'], format="%Y-%m-%d") #convert string back to date
	# Create a graph data for the OHLC chart sometimes the Linear Regression chart

	graphs = []

	ohlc_chart = go.Ohlc(x=df_EOD.Date,open=df_EOD.Open,high=df_EOD.High,low=df_EOD.Low,close=df_EOD.Close)

	linReg_chart = go.Scatter(x=df_EOD.Date, y=df_EOD.linreg)

	graphs.append(ohlc_chart)

	#if linReg button set to show, then linRegFlag ==1, so add that chart to the graph
	if linRegFlag ==1:
		graphs.append(linReg_chart)

	# Provide extra stylings to the graph
	layout = go.Layout(title="OHLC Chart: "+security_name,yaxis={'title': 'Stock Price ($)'},
						hovermode='closest', 
						xaxis = dict(rangeslider = dict(visible = False)))

	#configure the graph to show toolbar
	config = {'scrollZoom': True,'displayModeBar': True,'editable': False}

	#bring it all together to send to figure in "Ohlc-graph"
	results = {'data':graphs, 'layout':layout,'config':config}
	return results

###################################################
#######			Main Section                #######
###################################################

# Initiate the webserver
# This code runs when "python app.py" is executed

if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0')











