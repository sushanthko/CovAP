#!/usr/bin/env python
# coding: utf-8

# # COVID-19 Analysis Platform

# In[430]:


from jupyter_dash import JupyterDash


# In[431]:


import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_bootstrap_components as dbc
import dash_table as dt
from dash.dependencies import Input, Output
from statsmodels.tsa.arima_model import ARIMA
from pmdarima import auto_arima
import warnings
from fbprophet import Prophet


# In[432]:


debug = pd.read_json("properties.json", orient="index").debug.value


# In[433]:


df = pd.read_csv("owid-covid-data.csv")


# In[434]:


countries = df.location.unique()


# In[435]:


world_code = "OWID_WRL"

null_fill_columns = {'new_cases': 0, 'new_deaths': 0, 'total_cases': 0, 'total_deaths': 0,
                     'total_cases_per_million': 0, 'total_deaths_per_million' : 0, 
                     'new_cases_smoothed': 0, 'new_cases_smoothed_per_million': 0, 'new_deaths_smoothed': 0, 
                     'new_deaths_smoothed_per_million': 0}

numeric_columns = ['new_cases', 'new_deaths', 'total_cases', 'total_deaths', 'total_cases_per_million',
                'total_deaths_per_million']

df = df.fillna(null_fill_columns)

dfmain = df[df.groupby(['location']).date.transform('max') == df.date]
dfmain = dfmain.fillna(null_fill_columns)

dft = dfmain[['location', 'continent', 'total_cases', 'total_cases_per_million',
                'total_deaths', 'total_deaths_per_million']]

dfmain_no_world = dfmain[~dfmain.iso_code.isin(['OWID_WRL'])] # Remove world row for map
dfm = dfmain_no_world[['iso_code', 'location', 'total_cases_per_million', 'total_deaths_per_million']]


# In[436]:


# Alcohol sales data
alcohol_sales = pd.read_csv("Statistics on alcohol sales, by type of beverage, contents and quarter.csv", delimiter=";")
alcohol_sales = alcohol_sales.set_index("type of beverage")
alcohol_sales = alcohol_sales.rename(columns={
 "Sales of alcoholic beverages per capita 15 years and over, as sold (litres) 2019K1": "Q1 2019 Sales",
 "Sales of alcoholic beverages per capita 15 years and over, as sold (litres) 2019K2": "Q2 2019 Sales",
 "Sales of alcoholic beverages per capita 15 years and over, as sold (litres) 2019K3": "Q3 2019 Sales",
 "Sales of alcoholic beverages per capita 15 years and over, as sold (litres) 2019K4": "Q4 2019 Sales",
 "Sales of alcoholic beverages per capita 15 years and over, as sold (litres) 2020K1": "Q1 2020 Sales",
 "Sales of alcoholic beverages per capita 15 years and over, as sold (litres) 2020K2": "Q2 2020 Sales",
 "Sales of alcoholic beverages per capita 15 years (litres) and over, pure alcohol 2019K1": "Q1 2019 Sales pure alcohol",
 "Sales of alcoholic beverages per capita 15 years (litres) and over, pure alcohol 2019K2": "Q2 2019 Sales pure alcohol",
 "Sales of alcoholic beverages per capita 15 years (litres) and over, pure alcohol 2019K3": "Q3 2019 Sales pure alcohol",
 "Sales of alcoholic beverages per capita 15 years (litres) and over, pure alcohol 2019K4": "Q4 2019 Sales pure alcohol",
 "Sales of alcoholic beverages per capita 15 years (litres) and over, pure alcohol 2020K1": "Q1 2020 Sales pure alcohol",
 "Sales of alcoholic beverages per capita 15 years (litres) and over, pure alcohol 2020K2": "Q2 2020 Sales pure alcohol",  
})

alcohol_sales_all = alcohol_sales[["Q1 2019 Sales", "Q2 2019 Sales", "Q3 2019 Sales", "Q4 2019 Sales",
                                   "Q1 2020 Sales", "Q2 2020 Sales"]]
alcohol_sales_all = alcohol_sales_all.T
alcohol_sales_all.columns.name = None
new_indices = [i.replace("Sales", "").strip() for i in alcohol_sales_all.index]
alcohol_sales_all = alcohol_sales_all.rename(index=dict(zip(alcohol_sales_all.index,new_indices)))

alcohol_sales_pure_alcohol = alcohol_sales[["Q1 2019 Sales pure alcohol", "Q2 2019 Sales pure alcohol",
                                   "Q3 2019 Sales pure alcohol", "Q4 2019 Sales pure alcohol", 
                                   "Q1 2020 Sales pure alcohol", "Q2 2020 Sales pure alcohol"]]
alcohol_sales_pure_alcohol = alcohol_sales_pure_alcohol.T
alcohol_sales_pure_alcohol.columns.name = None
alcohol_sales_pure_alcohol = alcohol_sales_pure_alcohol.rename(
    index=dict(zip(alcohol_sales_pure_alcohol.index,new_indices)))

# To drop total alcohol sales
alcohol_sales = alcohol_sales.drop(alcohol_sales.index[0])


# In[437]:


# Trips data
trips = pd.read_csv("Trips (million), by type of destination, type of trip, contents and quarter.csv", delimiter=";")
grouped_trips = trips.groupby(["type of destination", "type of trip"]).sum()
grouped_trips_transposed = grouped_trips.T
new_indices_latest = new_indices.append("Q3 2020")
trips_grouped = grouped_trips_transposed.rename(index=dict(zip(grouped_trips_transposed.index,new_indices)))
trips = trips.rename(columns=dict(zip(trips.columns[2:],new_indices)))
domestic_trips = trips[trips["type of trip"] == "Total trips domestic"]

# To drop all trips
domestic_trips = domestic_trips.drop(domestic_trips.index[0])


# In[438]:


# Predictions data
predictions = pd.read_csv("predictions.csv")
# predictions


# In[439]:


def getFormat(column):
    if(column in numeric_columns):
        if("per_million" in column):
            return {'specifier': ',.2f'}
        else:
            return {'specifier': ',.0f'}
    return None

    
def getType(column):
    if(column in numeric_columns):
        return "numeric"
    return "text"


def getTitleText(text):
    return text.title().replace('_', ' ').replace("Gdp", "GDP")


# In[440]:


def replace_negatives(series):
    return series.mask(series.lt(0), 0)


# In[441]:


header = html.H1("CovAP dashboard")
last_updated = html.H6("Last updated on: "+df.date.max(),className="text-right")


# In[442]:


comparison_options = ['new_cases_smoothed', 'new_cases_smoothed_per_million', 'new_deaths_smoothed',
                      'new_deaths_smoothed_per_million']

location_comparison_div = html.Div([
    html.Div(html.Div(html.H4("Comparison of COVID-19 outbreak by location"), className="col p-0"),
             className="row mt-2"),
    
    html.Div([
        html.Div(html.Label("Select one or more locations"), className="col-auto p-0"),
        
        html.Div(dcc.Dropdown(
            id='multi-country-input',
            options=[{'label': i, 'value': i} for i in countries],
            value=['Norway', 'Sweden', 'Denmark', 'Finland'],
            clearable=False,
            multi=True,
        ), className="col-4"),
        
        html.Div(html.Label("Select a category"), className="col-auto p-0"),
        
        html.Div(
            dcc.Dropdown(
                id="comparison-type", 
                options=[{'label': getTitleText(c), 'value': c} for c in comparison_options],
                value = comparison_options[0],
                clearable=False,
            ), className="col-4"),
        
    ], className="row mb-2"),
    
    html.Div(html.Div(dcc.Graph(id='comparison-plot'), className="col border border-dark"),
             className="row align-items-center"),
    
], className="container-fluid")


# In[443]:


# Metric Analysis tab content
dot_measures = ["population", "population_density", "gdp_per_capita", "extreme_poverty", "cardiovasc_death_rate",
                "diabetes_prevalence", "life_expectancy", "human_development_index", "median_age", "stringency_index"]

dot_measures.sort()

default_analysis_type = dot_measures[2]

analysis_locations = dfmain_no_world[~dfmain_no_world[default_analysis_type].isna()].location
analysis_locations_list = analysis_locations.tolist()
first_location = "" if len(analysis_locations_list) == 0 else analysis_locations_list[0]
default_location = "Norway" if "Norway" in analysis_locations_list else first_location

dot_div = html.Div([
    html.Div(html.Div(html.H4("Analysis of COVID-19 prevalence with location wise metrics"), className="col p-0"),
             className="row mt-2"),
        
    html.Div([
            html.Div(html.Label("Select a metric"), className="col-auto p-0"),
            html.Div(dcc.Dropdown(
                id='dot-metric',
                options=[
                    {'label': getTitleText(prop), 'value': prop} for prop in dot_measures
                ],
                value="gdp_per_capita",
            ), className="col-4"),
            
            html.Div(html.Label("Select a location to highlight"), className="col-auto p-0"),
        
            html.Div(dcc.Dropdown(
                id='hightlight-input',
                options=[
                    {'label': location, 'value': location} for location in analysis_locations
                ],
                value=default_location,
            ), className="col-4"),
        
    ], className="row mb-2"),
    
    html.Div([
        html.Div(dcc.Graph(id='total-dot-plot'), className="col border border-dark"),
        
        html.Div(dcc.Graph(id='dot-plot'), className="col border-top border-right border-bottom border-dark"),
        
    ], className="row align-items-center"),
    
], className="container-fluid")


# In[444]:


# Daily stats tab content
daily_stats_div = html.Div([
    
    html.Div(html.Div(html.H4("Daily COVID-19 statistics by location"), className="col-auto p-0"), className="row mt-2"),
    
    html.Div([
        html.Div(html.Label("Select a location"), className="col-auto p-0"),
        
        html.Div(dcc.Dropdown(
            id='country-input',
            options=[{'label': i, 'value': i} for i in countries],
            value='Norway',
            clearable=False,
    ), className="col-4"),
    ], className="row mb-2"),
    
    html.Div([
        
        html.Div(dcc.Graph(id='daily-cases'), className="col border border-dark"),
        
        html.Div(dcc.Graph(id='daily-deaths'), className="col border-top border-right border-bottom border-dark"),
        
        html.Div(dcc.Graph(id='daily-tests'), className="col border-top border-right border-bottom border-dark"),
        
    ], className="row align-items-center"),
    
], className="container-fluid")


# In[445]:


world_table = dt.DataTable(
    id="world-table",
    data=dft.to_dict('records'),
    columns=[{'id': c, 'name': getTitleText(c), "type": getType(c), 'format': getFormat(c)} for c in dft.columns],
    sort_by=[{"column_id": 'total_deaths', "direction": "desc"}],
    page_size=12,
    sort_action='native',
    filter_action="native",
    style_cell={
            'whiteSpace': 'normal',
            'height': 'auto',
            'width': '15%',
            'font-family': "Helvetica Neue, Helvetica, Arial, sans-serif",
    },
    style_cell_conditional=[
        {'if': {'column_id': 'location'},
         'width': '22%'},
        {'if': {'column_id': 'continent'},
         'width': '18%'},
    ],
    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        },
        {
        'if': {
            'filter_query': '{location} = "World"'
        },
        'backgroundColor': 'grey',
        'color': 'white'
        },
        {
        'if': {
            'column_type': 'text'  # 'text' | 'any' | 'datetime' | 'numeric'
        },
        'textAlign': 'left'
        },
    ],
    style_header={
        'backgroundColor': 'rgb(230, 230, 230)',
        'fontWeight': 'bold',
        'textAlign': 'center'
    },
)


# In[446]:


map_details_div = html.Div([
    html.Div(
        html.Div(html.H4(id='click-data'), className="col d-flex align-items-center justify-content-center"),
        className="row"),
    
    html.Div([

        html.Div([
            html.H5("Cases"),
        ], className="col d-flex align-items-center justify-content-center text-center p-0 border-right border-dark"),

        html.Div([
            html.H5("Deaths"), 
        ], className="col d-flex align-items-center justify-content-center text-center p-0"),

    ], className="row border-top border-left border-right border-dark"),

    html.Div([

        html.Div([
            html.H6("Total"),
        ], className="col d-flex align-items-center justify-content-center text-center p-0 border-right border-dark"),

        html.Div([
            html.H6("Per Million"),
        ], className="col d-flex align-items-center justify-content-center text-center p-0 border-right border-dark"),

        html.Div([
            html.H6("Total"),
        ], className="col d-flex align-items-center justify-content-center text-center p-0 border-right border-dark"),

        html.Div([
            html.H6("Per Million"), 
        ], className="col d-flex align-items-center justify-content-center text-center p-0"),

    ], className="row border-top border-left border-right border-dark"),
    html.Div([

        html.Div(html.Span(id="total-cases"),
                 className="col d-flex align-items-center justify-content-center border-right border-dark"),

        html.Div(html.Span(id="total-cases-pm"), 
                 className="col d-flex align-items-center justify-content-center border-right border-dark"),

        html.Div(html.Span(id="total-deaths"),
                 className="col d-flex align-items-center justify-content-center border-right border-dark"),

        html.Div(html.Span(id="total-deaths-pm"), 
                 className="col d-flex align-items-center justify-content-center"),

    ], className="row border border-dark"),

    html.Div(html.Div(
        html.Button("Reset", id='btn-world', className="btn btn-light btn-sm",
                    role="button"),
        className="col d-flex align-items-center justify-content-end p-0 mt-2"), className="row"),

], className="container-fluid")


# In[447]:


# World data tab content
map_options = ['total_deaths_per_million', 'total_cases_per_million']
world_data_div = html.Div([
    
    html.Div(html.Div(html.H4("COVID-19 statistics for the world"), className="col-auto p-0"), className="row mt-2"),
    
    html.Div([
        html.Div(html.Label("Select a visual category"), className="col-auto p-0"),
        
        html.Div(
        dcc.RadioItems(
            id='world-type',
            options=[
                {'label': "Map", 'value': "map"},
                {'label': "Table", 'value': "table"}
            ],
            value="map",
            labelClassName="mr-2"
        ), className="col")
        
    ], className="row"),
    
    html.Div([ #row 3
            
            html.Div([
                html.Div([
                    
                    html.Div([
                        
                        html.Div(html.Label("Select a map type"), className="col-auto p-0"),
                        html.Div(
                            dcc.RadioItems(
                                id='map-type',
                                options=[{'label': getTitleText(i), 'value': i} for i in map_options ],
                                value=map_options[0],
                                labelClassName="mr-2"
                            ), className="col"),
                        ],className="row mt-2"),
                    
                    html.Div([
                        
                        html.Div(dcc.Graph(id='world-map'), className="col-8 p-0"),
                        
                        html.Div(map_details_div, className="col d-flex align-items-center justify-content-center p-0"),
                        
                    ], className="row align-items-center"),
                    
                    html.Div(
                        html.Div("Click on a map location to see details on the right.",
                                 className="col text-info text-left p-0"),
                    className="row"),
                    
                ], className="container-fluid"),
                
            ], className="col border border-dark", id="world-map-div",),  
        
        html.Div(world_table, className="col border border-dark", id="world-table-div",),   
            
    ], className="row"),
        
], className="container-fluid")


# In[448]:


# Predictions tab content
prediction_columns = ["new_cases_smoothed", "new_deaths_smoothed"]
predictions_div = html.Div([
    
    html.Div(html.Div(html.H4("COVID-19 predictions for Nordic countries"), className="col-auto p-0"), className="row mt-2"),
    
    html.Div([
        html.Div(html.Label("Select a location"), className="col-auto p-0"),
        html.Div(dcc.Dropdown(
            id='prediction-location',
            options=[{'label': i, 'value': i} for i in predictions.location.unique()],
            value='Norway',
            clearable=False,
    ), className="col-4"),
        html.Div(html.Label("Select a category"), className="col-auto p-0"),
        html.Div(
            dcc.RadioItems(
                id="prediction-column", 
                options=[{'label': getTitleText(c), 'value': c} for c in prediction_columns],
                           value = prediction_columns[0],
                          labelClassName="mr-2"), 
            className="col-auto")
    ], className="row mb-2"),
    
    html.Div([
        
        html.Div(dcc.Graph(id='prediction-new-cases'), className="col border border-dark"),
        
        html.Div(dcc.Graph(id='prediction-new-deaths'), className="col border-top border-right border-bottom border-dark"),
        
    ], className="row align-items-center"),
    
], className="container-fluid")


# In[449]:


# Datasets tab content
datasets_options = ["grouped", "show_trend"]
datasets_div = html.Div([
    html.Div(html.Div(html.H4("Impact of COVID-19 pandemic on Norwegian population"), className="col p-0"),
             className="row mt-2"),
    html.Div([
        html.Div(
            html.Div([
                html.Div([
                    html.Div(html.Label("Select a category"), className="col-auto pr-0"),
                    
                    html.Div(
                        dcc.RadioItems(
                            id='alcohol-stats-type',
                            options=[{'label': getTitleText(i), 'value': i} for i in datasets_options ],
                            value=datasets_options[0],
                            labelClassName="mr-2"
                        ), className="col"),
                    
                ], className="row mt-2"),

                    html.Div(html.Div(dcc.Graph(id='alcohol-stats'), className="col"),
                             className="row align-items-center"),

                ], className="container-fluid"), className="col p-0 border border-dark"),

        html.Div(
            html.Div([
                html.Div([
                    html.Div(html.Label("Select a category"), className="col-auto pr-0"),
                    
                    html.Div(
                        dcc.RadioItems(
                            id='trips-stats-type',
                            options=[{'label': getTitleText(i), 'value': i} for i in datasets_options ],
                            value=datasets_options[0],
                            labelClassName="mr-2"
                        ), className="col"),
                    
                ], className="row mt-2"),

                    html.Div(html.Div(dcc.Graph(id='trips-stats'), className="col"), 
                         className="row align-items-center"),

                ], className="container-fluid"), className="col p-0 border-top border-right border-bottom border-dark"),
    
    ], className="row"),
    
    html.Div(html.Div([
        "Source: ", html.A("Statistics Norway", href="https://www.ssb.no/en/statbank", target="_blank")
    ], className="col"), className="row"),
    
],className="container-fluid")


# In[450]:


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = JupyterDash(__name__, external_stylesheets=external_stylesheets)
app = JupyterDash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create server variable with Flask server object for use with gunicorn
server = app.server

app.layout = html.Div([
    html.Div([
        html.Div(className="col"), 
        
        html.Div(header, className="col d-flex align-items-center justify-content-center"), 
        
        html.Div(last_updated, className="col d-flex align-items-end justify-content-end")
        
    ], className="row"),
    
    html.Div(html.Div(dcc.Tabs([
        dcc.Tab(label='Daily Statistics', children=[
            daily_stats_div
        ]),
        dcc.Tab(label='World Data', children=[
            world_data_div
        ]),
        dcc.Tab(label='Metric Analysis', children=[
            dot_div
        ]),
        dcc.Tab(label='Location Comparison', children=[
            location_comparison_div
        ]),
        dcc.Tab(label='Impact Study', children=[
            datasets_div
        ]),
        dcc.Tab(label='COVID-19 Predictions', children=[
            predictions_div
        ]),
    ]),className="col"),className="row"),
], className="container-fluid")


# In[451]:


# World Type callback
@app.callback([
    Output('world-map-div', 'style'),
    Output('world-table-div', 'style'),
], Input('world-type', 'value'))
def set_world_type_plot(world_type):
    if (world_type == "map"):
        return {"display": "block"}, {"display": "none"}
    else:
        return {"display": "none"}, {"display": "block"}


# In[452]:


def get_empty_graph(text):
    return {
        "layout": {
            "xaxis": {
                "visible": False
            },
            "yaxis": {
                "visible": False
            },
            "annotations": [
                {
                    "text": "No "+ text.lower() +" data",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 20
                    }
                }
            ]
        }
    }

def get_daily_graph(x, y, text, color):
    if(pd.isna(y.max())):
        return get_empty_graph(text)
    return  {
        'data': [dict(
            x=x,
            y=y,
            type='bar',
            marker={
                'color': color
            },
            hovertemplate="%{y:,}<br>%{x}<extra></extra>"
        )],
        'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='closest',
            title={
            'text': text,
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
        )
    }


# In[453]:


# Daily stats tab callback
@app.callback([
    Output('daily-cases', 'figure'),
    Output('daily-deaths', 'figure'),
    Output('daily-tests', 'figure'),
],
[
    Input('country-input', 'value'),
])
def update_daily_stats(location):

    dff = df[df.location == location]
       
    return (get_daily_graph(dff.date, dff.new_cases,"Daily New Cases", "crimson"),
            get_daily_graph(dff.date, dff.new_deaths,"Daily New Deaths", "darkslateblue"),
            get_daily_graph(dff.date, dff.new_tests,"Daily New Tests", "deepskyblue"))


# In[454]:


alcohol_hovertemplate="%{y} litres<extra></extra>"
alcohol_title_text = "Sales of alcoholic beverages per capita"

def get_alcohol_sales_previous_year():
    x = alcohol_sales.index
    q2_2019 = "Q2 2019"
    q2_2020 = "Q2 2020"
    
    return {
            'data': [dict(
                x=x,
                y=alcohol_sales["Q2 2019 Sales"],
                type='bar',
                marker={
                    'color': 'orange'
                },
                name=q2_2019,
                hovertemplate=q2_2019 +"<br>"+ alcohol_hovertemplate,
            ),
            dict(
                x=x,
                y=alcohol_sales["Q2 2020 Sales"],
                type='bar',
                marker={
                    'color': 'red'
                },
                name=q2_2020,
                hovertemplate=q2_2020 +"<br>"+ alcohol_hovertemplate,
            )],
            'layout': dict(
                margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
                hovermode='closest',
                title={
                'text': getTitleText(alcohol_title_text),
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20),
                },
                hoverlabel=dict(
                    bgcolor="white",
                    font=dict(
                        size=16,
                        family="Rockwell"
                    ),
                ),
                legend=dict(
                    title=dict(
                        text="Quarters",
                    )
                ),
            )
        }

def get_alcohol_sales_trend():
    data = []
    
    for alcohol in alcohol_sales_all.columns:
        sales = alcohol_sales_all[alcohol]
        sub_data = dict(
            x=sales.index,
            y=sales,
            type='scatter',
            name=alcohol,
            hovertemplate=alcohol +" : "+ alcohol_hovertemplate,
        )
        data.append(sub_data)
        
    return {
            'data': data,
            'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='x unified',
            title={
            'text': getTitleText(alcohol_title_text),
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
            legend=dict(
                title=dict(
                    text="Alcoholic beverages",
                )
            ),
        )
    }


# In[455]:


# Alcohol sales callback
@app.callback(Output('alcohol-stats', 'figure'), Input('alcohol-stats-type', 'value'))
def update_alcohol_sales_plot(alcohol_stats_type):
    if (alcohol_stats_type == datasets_options[0]):
        return get_alcohol_sales_previous_year()
    else:
        return get_alcohol_sales_trend()


# In[456]:


trips_hovertemplate="%{y} million<extra></extra>"
trips_title_text = "Domestic trips"

def get_trips_previous_year():
    x=domestic_trips["type of destination"]
    q3_2019 = "Q3 2019"
    q3_2020 = "Q3 2020"
    
    return {
        'data': [dict(
            x=x,
            y=domestic_trips["Q3 2019"],
            type='bar',
            marker={
                'color': 'lime'
            },
            hovertemplate=q3_2019 +"<br>"+ trips_hovertemplate,
            name=q3_2019,
        ),
        dict(
            x=x,
            y=domestic_trips["Q3 2020"],
            type='bar',
            marker={
                'color': 'green'
            },
            hovertemplate=q3_2020 +"<br>"+ trips_hovertemplate,
            name=q3_2020,
        )],
        'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='closest',
            title={
            'text': getTitleText(trips_title_text),
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
            legend=dict(
                    title=dict(
                        text="Quarters",
                        )
                    ),
        )
    }

def get_trips_trend():
    data = []
    
    for type_of_destination in trips_grouped.columns.get_level_values("type of destination").unique():
        trips = trips_grouped[type_of_destination]["Total trips domestic"]
        sub_data = dict(
            x=trips_grouped.index,
            y=trips,
            type='scatter',
            name=type_of_destination,
            hovertemplate=type_of_destination +" : "+ trips_hovertemplate,
        )
        data.append(sub_data)
        
    return {
            'data': data,
            'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='x unified',
            title={
            'text': getTitleText(trips_title_text),
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
            legend=dict(
                title=dict(
                    text="Type of destination",
                )
            ),
        )
    }


# In[457]:


# Trips callback
@app.callback(Output('trips-stats', 'figure'), Input('trips-stats-type', 'value'))
def update_alcohol_sales_plot(alcohol_stats_type):
    if (alcohol_stats_type == datasets_options[0]):
        return get_trips_previous_year()
    else:
        return get_trips_trend()


# In[458]:


# Comparison tab callback
@app.callback(Output('comparison-plot', 'figure'), [
        Input('multi-country-input', 'value'),
        Input('comparison-type', 'value'),
    ])
def update_comparison_plot(locations, comparison_type):
    data = []
    
    for location in locations:
        dfc = df[df.location == location]
        sub_data = dict(
            x=dfc.date,
            y=dfc[comparison_type],
            type='scatter',
            name=location,
            hovertemplate="%{y:,.2f}",
        )
        data.append(sub_data)
        
    legend = dict(
        title=dict(
            text="Selected Locations",
        )
    )
        
    return {
            'data': data,
            'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='x unified',
            title={
            'text': getTitleText(comparison_type) + " (7-day smoothed)",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
                legend=legend,
        )
    }


# In[459]:


# Map callback
@app.callback(
    Output('world-map', 'figure'),
    Input('map-type', 'value')
)
def display_map(map_type):
    title = getTitleText(map_type)
    
    if(map_type == "total_cases_per_million"):
        text = "Global COVID-19 cases per million"
        column = dfm.total_cases_per_million
    else:
        text = "Global COVID-19 deaths per million"
        column = dfm.total_deaths_per_million
    
    return {
        'data': [dict(
            locations= dfm.iso_code,
            z = column.fillna(0),
            text = dfm.location,
            type='choropleth',
            colorscale = 'Reds',
            autocolorscale=False,
            reversescale=False,
            marker=dict(
                line_color='darkgray',
                line_width=0.5,
            ),
            colorbar = dict(
                title = 'COVID-19 <br>'+title,
            ),
            geo=dict(
                showframe=False,
                showcoastlines=False,
                projection_type='equirectangular'
            ),
            hoverinfo='z+text',
            hovertemplate="%{z:,.2f}<br>%{text}<extra></extra>"
        )],
        'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='closest',
            title={
            'text': text,
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20)
            },
        )
    }


# In[460]:


def get_click_data(clickData):
    int_formatter = "{:,.0f}".format
    float_formatter = "{:,.2f}".format
    location = None
    dfcountry = None
       
    if(clickData != None): 
        data = clickData["points"][0]
        location = data["text"]
        country_code = data["location"]
        dfcountry = dfmain[dfmain.iso_code == country_code]
    else:
        location = "World"
        dfcountry = dfmain[dfmain.iso_code == world_code]
        
    return (location, dfcountry.total_cases.apply(int_formatter), dfcountry.total_cases_per_million.apply(float_formatter), 
            dfcountry.total_deaths.apply(int_formatter), dfcountry.total_deaths_per_million.apply(float_formatter))


# In[461]:


# Map click callback
@app.callback([
    Output('click-data', 'children'),
    Output('total-cases', 'children'),
    Output('total-cases-pm', 'children'),
    Output('total-deaths', 'children'),
    Output('total-deaths-pm', 'children'),
],
    [
        Input('world-map', 'clickData'),
        Input('btn-world', 'n_clicks'),
    ])
def display_click_data(clickData, clicks):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'btn-world.n_clicks' == changed_id:
        return get_click_data(None)
    else:
        return get_click_data(clickData)


# In[462]:


# Predictions tab callback
@app.callback([
    Output('prediction-new-cases', 'figure'),
    Output('prediction-new-deaths', 'figure'),
], [
    Input('prediction-location', 'value'),
    Input('prediction-column', 'value'),
])
def update_prediction_plots(location, prediction_column):
    
    predictions_location = predictions[predictions.location == location]
    actual = predictions_location[predictions_location.predictor.isna()]
    arima = predictions_location[predictions_location.predictor == "ARIMA"]
    prophet = predictions_location[predictions_location.predictor == "Prophet"]
    
    color = "crimson"
    pridiction_color = "indigo"
    prophet_upper_column = "upper_cases"
    prophet_lower_column = "lower_cases"
    limit_color="lavender"
    column_type = "cases"
    if(prediction_column == "new_cases_smoothed"):
        color = "crimson"
        pridiction_color = "indigo"
        prophet_upper_column = "upper_cases"
        prophet_lower_column = "lower_cases"
        limit_color="lavender"
        column_type = "cases"
    elif(prediction_column == "new_deaths_smoothed"):
        color = "darkslateblue"
        pridiction_color = "brown"
        prophet_upper_column = "upper_deaths"
        prophet_lower_column = "lower_deaths"
        limit_color="bisque"
        column_type = "deaths"
        
    legend = dict(title=dict(text=getTitleText(prediction_column) + "<br>(7-day smoothed)",))
    
    hover_template = "%{y:,.2f}<extra></extra> "+ column_type
        
    actual_graph_data = dict(
                x=actual.date,
                y=actual[prediction_column],
                type='scatter',
                name="Actual",
                hovertemplate=hover_template,
                line = dict(color=color),
            )
    
    figure_prophet = {
        'data': [
            dict(
                 x=prophet.date,
                 y=replace_negatives(prophet[prophet_upper_column]),
                 type='scatter',
                 name="Prophet",
                 hovertemplate=hover_template,
                 line = dict(color=limit_color),
                 showlegend=False,
            ),
            dict(
                 x=prophet.date,
                 y=replace_negatives(prophet[prophet_lower_column]),
                 type='scatter',
                 name="Prophet",
                 hovertemplate=hover_template,
                 line = dict(color=limit_color),
                 showlegend=False,
                 fill='tonexty',
                 fillcolor = limit_color,
            ),
            dict(
                 x=prophet.date,
                 y=replace_negatives(prophet[prediction_column]),
                 type='scatter',
                 name="Prophet",
                 hovertemplate=hover_template,
                 line = dict(color=pridiction_color, dash='dash'),
            ),
            actual_graph_data,
        ],
            'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='closest',
            title={
            'text': "Prophet Prediction",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
                legend=legend
        )
    }
    
    figure_arima = {
        'data': [
            actual_graph_data,
            dict(
                 x=arima.date,
                 y=replace_negatives(arima[prediction_column]),
                 type='scatter',
                 name="ARIMA",
                 hovertemplate=hover_template,
                 line = dict(color=pridiction_color, dash='dash')
            ),
        ],
            'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='closest',
            title={
            'text': "ARIMA Prediction",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
            legend=legend  
        )
    }
    
    return figure_arima, figure_prophet


# In[463]:


def get_dot_graph(analysis_type, hightlight, column, title_text, hoverTemplate, color, highlight_color):
    dfd = dfmain_no_world[dfmain_no_world.location != hightlight]
    dfh = dfmain_no_world[dfmain_no_world.location == hightlight]
    
    return {
            'data': [
                dict(
                    x=dfd[analysis_type],
                    y=dfd[column],
                    type='scatter',
                    marker={
                            'color': color,
                        },
                    name=dfd.location,
                    hovertemplate= dfd.location +"<extra></extra><br>"+ hoverTemplate,
                    mode="markers",
                    showlegend=False,
                ),
                dict(
                    x=dfh[analysis_type],
                    y=dfh[column],
                    type='scatter',
                    marker={
                            'color': highlight_color,
                            "size": 18,
                        },
                    name=dfh.location,
                    hovertemplate= dfh.location +"<extra></extra><br>"+ hoverTemplate,
                    mode="markers",
                    showlegend=False,
                )
            ],
            'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='closest',
            title={
                'text': title_text,
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20),
            },
            hoverlabel=dict(
                bgcolor="white",
                font=dict(
                    size=16,
                    family="Rockwell"
                ),
            ),
                xaxis=dict(
                    title=getTitleText(analysis_type)
                ),
                yaxis=dict(
                    title=getTitleText(column)
                ),
        )
    }


# In[464]:


# Dot plot callbacks
@app.callback(Output('dot-plot', 'figure'),[
    Input('dot-metric', 'value'),
    Input('hightlight-input', 'value'),
])
def update_total_dot_graph(analysis_type, hightlight):
    column = "total_cases_per_million"
    
    hoverTemplate = getTitleText(analysis_type) +": %{x:,.2f}<br>%{y:,.2f} cases per million people"
    
    if(analysis_type == "population"):
        hoverTemplate = getTitleText(analysis_type) +": %{x:,.0f}<br>%{y:,.2f} cases per million people"
    
    title_text = getTitleText(analysis_type) +" Vs Total COVID-19 Cases Per Million"
    
    return get_dot_graph(analysis_type, hightlight, column, title_text, hoverTemplate, "burlywood", "darkred")

@app.callback(Output('total-dot-plot', 'figure'),[
    Input('dot-metric', 'value'),
    Input('hightlight-input', 'value'),
])
def update_dot_graph(analysis_type, hightlight):
    column = "total_deaths_per_million"
    
    hoverTemplate = getTitleText(analysis_type) +": %{x:,.2f}<br>%{y:,.2f} deaths per million people"
    
    if(analysis_type == "population"):
        hoverTemplate = getTitleText(analysis_type) +": %{x:,.0f}<br>%{y:,.2f} deaths per million people"
    
    title_text = getTitleText(analysis_type) +" Vs Total COVID-19 Deaths Per Million"
    
    return get_dot_graph(analysis_type, hightlight, column, title_text, hoverTemplate, "deepskyblue", "darkviolet")

@app.callback([
    Output('hightlight-input', 'options'),
    Output('hightlight-input', 'value'),
], Input('dot-metric', 'value'))
def update_highlight_locations(analysis_type):
    analysis_locations = dfmain_no_world[~dfmain_no_world[analysis_type].isna()].location
    analysis_locations_list = analysis_locations.tolist()
    first_location = "" if len(analysis_locations_list) == 0 else analysis_locations_list[0]
    default_location = "Norway" if "Norway" in analysis_locations_list else first_location
    
    return [
        {'label': location, 'value': location} for location in analysis_locations
    ], default_location


# In[465]:


# Reference: https://github.com/nachi-hebbar/ARIMA-Temperature_Forecasting

def predict_arima(df, country, column):
    from statsmodels.tsa.arima_model import ARIMA
    from pmdarima import auto_arima
    import warnings
    df=df[df.location == country]
    df = df[[column]]
    df=df.dropna()
    print('Shape of data',df.shape)

    #Figure Out Order for ARIMA Model
    # Ignore harmless warnings
    warnings.filterwarnings("ignore")

    stepwise_fit = auto_arima(df[column], 
                              suppress_warnings=True)           

    order = stepwise_fit.order

    model2=ARIMA(df[column],order=order)
    model2=model2.fit()
    
    predict_start_date = df[-1:].index[0] + pd.DateOffset(1)

    index_future_dates=pd.date_range(predict_start_date, periods=180)

    prediction=model2.predict(start=len(df),end=len(df) + index_future_dates.size - 1 ,
                              typ='levels').rename('ARIMA Predictions')
    prediction.index=index_future_dates
    return prediction


# In[466]:


# Reference: https://machinelearningmastery.com/time-series-forecasting-with-prophet-in-python/

def predict_prophet(df, country, column):
    from fbprophet import Prophet    
    df=df[df.location == country]
    df = df[["date", column]]
    df = df.rename(columns={"date":"ds", column:"y"})
    df=df.dropna()
    print('Shape of data',df.shape)
    # define the model
    model = Prophet()
    # fit the model
    model.fit(df)

    predict_start_date = df.iloc[-1].ds + pd.DateOffset(1)

    future=pd.date_range(predict_start_date, periods=180)

    future = pd.DataFrame(future)
    future.columns = ['ds']
    # use the model to make a forecast
    forecast = model.predict(future)
    return forecast["yhat"], forecast["yhat_upper"], forecast["yhat_lower"],


# In[467]:


def predict():    
    dfd = df.set_index("date")
    dfd.index = pd.to_datetime(dfd.index)
    
    columns = ["new_cases_smoothed", "new_deaths_smoothed"]
    
    countries = ["Norway", "Sweden", "Finland", "Denmark", "Iceland"]
    dfd = dfd[dfd.location.isin(countries)]
    
    pred_max = pd.to_datetime(predictions[predictions.predictor.isna()].date.max())
    df_max = pd.to_datetime(dfd.index.max())
    if(pred_max == df_max):
        return "Up to date"

    dfr = dfd.reset_index()
    dfp = dfr[["date", "location", "new_cases_smoothed", "new_deaths_smoothed"]].copy()
    dfp["predictor"] = ""
    dfp["upper_deaths"] = ""
    dfp["lower_deaths"] = ""
    dfp["upper_cases"] = ""
    dfp["lower_cases"] = ""
    
    for country in countries:
        pred1 = predict_arima(dfd, country, "new_cases_smoothed")
        pred2 = predict_arima(dfd, country, "new_deaths_smoothed")
        dfi = pd.DataFrame({ "new_cases_smoothed": pred1, "new_deaths_smoothed": pred2})
        dfi["date"] = pred1.index
        dfi["location"] = country
        dfi["predictor"] = "ARIMA"
        dfp = dfp.append(dfi, ignore_index=True)

        pred3, preduc, predlc = predict_prophet(dfr, country, "new_cases_smoothed")
        pred4, predud, predld = predict_prophet(dfr, country, "new_deaths_smoothed")
        dfj = pd.DataFrame({ "new_cases_smoothed": pred3, "new_deaths_smoothed": pred4,
                           "upper_deaths": predud, "lower_deaths": predld, "upper_cases": preduc, "lower_cases": predlc})
        dfj["date"] = pred1.index
        dfj["location"] = country
        dfj["predictor"] = "Prophet"
        dfp = dfp.append(dfj, ignore_index=True)
        
    dfp.to_csv("predictions.csv", index=False)
    return "Updated"


# In[468]:


if __name__ == '__main__':
	app.run_server(debug=debug)
# app.run_server(debug=False)


# In[469]:


# predict()

