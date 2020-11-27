#!/usr/bin/env python
# coding: utf-8

# # COVID-19 Analysis Platform

# In[1]:


from jupyter_dash import JupyterDash


# In[2]:


import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_bootstrap_components as dbc
import dash_table as dt
from dash.dependencies import Input, Output


# In[3]:


debug = pd.read_json("properties.json", orient="index").debug.value


# In[4]:


df = pd.read_csv("owid-covid-data.csv")


# In[5]:


countries = df.location.unique()


# In[6]:


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


# In[7]:


dpm_countries = 20
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

dft = dfmain[['location', 'continent', 'total_cases', 'total_deaths']]
dftpm = dfmain[['location', 'continent', 'total_cases_per_million', 'total_deaths_per_million']]

dfmain_no_world = dfmain[~dfmain.iso_code.isin(['OWID_WRL'])] # Remove world row for map
dfm = dfmain_no_world[['iso_code', 'location', 'total_cases_per_million', 'total_deaths_per_million']]


# In[8]:


header = html.H1("CovAP dashboard")
last_updated = html.H6("Last updated on: "+df.date.max(),className="text-right")


# In[9]:


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
# new_indices = [i.replace("Sales pure alcohol", "").strip() for i in alcohol_sales_pure_alcohol.index]
alcohol_sales_pure_alcohol = alcohol_sales_pure_alcohol.rename(
    index=dict(zip(alcohol_sales_pure_alcohol.index,new_indices)))
alcohol_sales_all


# In[10]:


# Trips data
trips = pd.read_csv("Trips (million), by type of destination, type of trip, contents and quarter.csv", delimiter=";")
grouped_trips = trips.groupby(["type of destination", "type of trip"]).sum()
grouped_trips_transposed = grouped_trips.T
new_indices_latest = new_indices.append("Q3 2020")
trips_grouped = grouped_trips_transposed.rename(index=dict(zip(grouped_trips_transposed.index,new_indices)))
trips = trips.rename(columns=dict(zip(trips.columns[2:],new_indices)))
domestic_trips = trips[trips["type of trip"] == "Total trips domestic"]


# In[11]:


alcohol_hovertemplate="%{y} litres<extra></extra>"
alcohol_title_text = "Sales of alcoholic beverages per capita"

def get_alcohol_sales_previous_year():
    return {
            'data': [dict(
                x=alcohol_sales.index,
                y=alcohol_sales["Q2 2019 Sales"],
                type='bar',
                marker={
                    'color': 'orange'
                },
                name="Q2 2019",
                hovertemplate=alcohol_hovertemplate,
            ),
            dict(
                x=alcohol_sales.index,
                y=alcohol_sales["Q2 2020 Sales"],
                type='bar',
                marker={
                    'color': 'red'
                },
                name="Q2 2020",
                hovertemplate=alcohol_hovertemplate,
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


# In[12]:


trips_hovertemplate="%{y} million<extra></extra>"
trips_title_text = "Domestic trips"

def get_trips_previous_year():
    return {
        'data': [dict(
            x=domestic_trips["type of destination"],
            y=domestic_trips["Q3 2019"],
            type='bar',
            marker={
                'color': 'lime'
            },
            hovertemplate=trips_hovertemplate,
            name="Q3 2019",
        ),
        dict(
            x=domestic_trips["type of destination"],
            y=domestic_trips["Q3 2020"],
            type='bar',
            marker={
                'color': 'green'
            },
            hovertemplate=trips_hovertemplate,
            name="Q3 2020",
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


# In[13]:


# Daily stats tab content
daily_stats_div = html.Div([
    
    html.Div([
        html.Div(html.Label("Select location"), className="col-auto"),
        
        html.Div(dcc.Dropdown(
            id='country-input',
            options=[{'label': i, 'value': i} for i in countries],
            value='Norway',
            clearable=False,
    ), className="col-4"),
    ], className="row mt-2"),
    
    html.Div([
        
        html.Div(dcc.Graph(id='daily-cases'), className="col"),
        
        html.Div(dcc.Graph(id='daily-deaths'), className="col"),
        
        html.Div(dcc.Graph(id='daily-tests'), className="col"),
        
    ], className="row align-items-center"),
    
], className="container-fluid")


# In[14]:


# Datasets tab content
datasets_options = ["previous_year", "show_trend"]
datasets_div = html.Div([
    html.Div(html.Div(html.H4("Impact of COVID-19 pandemic on Norwegian population"), className="col p-0"),
             className="row mt-2"),
    html.Div([
        html.Div(
            html.Div([
                html.Div(    
                    html.Div(
                        dcc.RadioItems(
                            id='alcohol-stats-type',
                            options=[{'label': getTitleText(i), 'value': i} for i in datasets_options ],
                            value=datasets_options[0],
                            labelClassName="mr-2"
                        ), className="col"), className="row mt-2"),

                    html.Div(html.Div(dcc.Graph(id='alcohol-stats'), className="col"),
                             className="row align-items-center"),

                ], className="container-fluid"), className="col"),

        html.Div(
            html.Div([
                html.Div(    
                    html.Div(
                        dcc.RadioItems(
                            id='trips-stats-type',
                            options=[{'label': getTitleText(i), 'value': i} for i in datasets_options ],
                            value=datasets_options[0],
                            labelClassName="mr-2"
                        ), className="col"), className="row mt-2"),

                    html.Div(html.Div(dcc.Graph(id='trips-stats'), className="col"), 
                         className="row align-items-center"),

                ], className="container-fluid"), className="col"),
    
    ], className="row"),
    
    html.Div(html.Div([
        "Source: ", html.A("Statistics Norway", href="https://www.ssb.no/en/statbank", target="_blank")
    ], className="col"), className="row"),
    
],className="container-fluid")


# In[15]:


world_table = dt.DataTable(
    id="world-table",
    page_size=12,
    sort_action='native',
    filter_action="native",
    style_cell={
            'whiteSpace': 'normal',
            'height': 'auto',
            'width': '22%',
            'font-family': "Helvetica Neue, Helvetica, Arial, sans-serif",
    },
    style_cell_conditional=[
        {'if': {'column_id': 'location'},
         'width': '33%'},
        {'if': {'column_id': 'continent'},
         'width': '22%'},
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


# In[16]:


# World data tab cotent
map_options = ['total_deaths_per_million', 'total_cases_per_million']
world_data_div = html.Div([
    
    html.Div([
        
        html.Div(html.Div([
            
            html.Div(html.Div(
                dcc.RadioItems(
                    id='map-type',
                    options=[{'label': getTitleText(i), 'value': i} for i in map_options ],
                    value=map_options[0],
                    labelClassName="mr-2"
                ), className="col"), className="row mt-2"),
            
            html.Div(html.Div(dcc.Graph(id='world-map'), className="col"), className="row"),
            
            html.Div(
                html.Div(html.H4(id='click-data'), className="col d-flex align-items-center justify-content-center"),
                className="row"),
            
            html.Div([
                
                html.Div([
                    html.H6("Total Cases:"),
                ], className="col d-flex align-items-center justify-content-center text-center"),
                
                html.Div([
                    html.H6("Cases Per Million:"),
                ], className="col d-flex align-items-center justify-content-center text-center"),
                
                html.Div([
                    html.H6("Total Deaths:"),
                ], className="col d-flex align-items-center justify-content-center text-center"),
                
                html.Div([
                    html.H6("Deaths Per Million:"), 
                ], className="col d-flex align-items-center justify-content-center text-center"),
                
            ], className="row"),
            html.Div([
                
                html.Div(html.Span(id="total-cases"),
                         className="col d-flex align-items-center justify-content-center"),
                
                html.Div(html.Span(id="total-cases-pm"), 
                         className="col d-flex align-items-center justify-content-center"),
                
                html.Div(html.Span(id="total-deaths"),
                         className="col d-flex align-items-center justify-content-center"),
                
                html.Div(html.Span(id="total-deaths-pm"), 
                         className="col d-flex align-items-center justify-content-center"),
                
            ], className="row"),
                        
            html.Div(html.Div(
                html.Button("World", id='btn-world', className="btn btn-light btn-sm", role="button"),
                className="col d-flex align-items-center justify-content-end p-0"), className="row"),
                                
            ], className="container-fluid"), 
            className="col"),    

        html.Div(html.Div([
            html.Div([
                
                html.Div(html.H4("Reported cases and deaths by country"), className="col-auto"),
                html.Div(
                    dcc.Checklist(
                        id="table-type", 
                        options=[{'label': 'Per Million People', 'value': 'per_million'}], 
                        labelClassName="m-0"
                    ), className="col d-flex align-items-center justify-content-start"),
            ], className="row mt-2"),
            
            html.Div(html.Div(world_table, className="col overflow-auto"), className="row"),
            
            ], className="container-fluid"), className="col"),
    ], className="row"),
        
], className="container-fluid")


# In[17]:


# Comparison tab content
comparison_options = ['new_cases_smoothed', 'new_cases_smoothed_per_million', 'new_deaths_smoothed',
                      'new_deaths_smoothed_per_million']
comparison_div = html.Div([
    
    html.Div([
        html.Div(html.Label("Select one or more locations"), className="col-auto"),
        html.Div(dcc.Dropdown(
            id='multi-country-input',
            options=[{'label': i, 'value': i} for i in countries],
            value=['Norway', 'Sweden', 'Denmark', 'Finland'],
            clearable=False,
            multi=True,
    ), className="col-4"),
        html.Div(
            dcc.RadioItems(
                id="comparison-type", 
                options=[{'label': getTitleText(c), 'value': c} for c in comparison_options],
                           value = comparison_options[0],
                          labelClassName="mr-2"), 
            className="col-auto")
    ], className="row mt-2"),
    
    html.Div(html.Div(dcc.Graph(id='comparison-plot'), className="col"), className="row align-items-center"),
    
], className="container-fluid")


# In[18]:


# Analysis tab content
analysis_measures = ["population", "population_density", "gdp_per_capita", "extreme_poverty", "cardiovasc_death_rate",
                     "diabetes_prevalence", "life_expectancy", "human_development_index"]

analysis_div = html.Div([
        
    html.Div([
            html.Div(html.Label("Metric"), className="col-auto"),
            html.Div(dcc.Dropdown(
                id='select-property',
                options=[
                    {'label': getTitleText(prop), 'value': prop} for prop in analysis_measures
                ],
                value="gdp_per_capita",
            ), className="col-4"),
            
            html.Div(
                dcc.Checklist(
                        id="analysis-options", 
                        options=[
                            {'label': 'Sort Reverse', 'value': 'sort_reverse'},
                            {'label': 'Per Million People', 'value': 'per_million'},
                        ],
                        labelClassName="mr-2"
            ), className="col-auto"),
    ], className="row mt-2"),
    
    html.Div(html.Div(dcc.Graph(id='analysis-plot'), className="col"), className="row align-items-center"),
    
], className="container-fluid")


# In[19]:


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = JupyterDash(__name__, external_stylesheets=external_stylesheets)
app = JupyterDash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create server variable with Flask server object for use with gunicorn
server = app.server

app.layout = html.Div([
    html.Div([
        html.Div(header, className="col"), 
        html.Div(last_updated, className="col d-flex align-items-end justify-content-end")
    ], className="row"),
    html.Div(html.Div(dcc.Tabs([
        dcc.Tab(label='Daily Statistics', children=[
            daily_stats_div
        ]),
        dcc.Tab(label='World Data', children=[
            world_data_div
        ]),
        dcc.Tab(label='Comparison', children=[
            comparison_div
        ]),
        dcc.Tab(label='Analysis', children=[
            analysis_div
        ]),
        dcc.Tab(label='Impact Study', children=[
            datasets_div
        ]),
    ]),className="col"),className="row"),
], className="container-fluid")


# In[20]:


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

def get_daily_graph(x, y, text):
    if(pd.isna(y.max())):
        return get_empty_graph(text)
    return  {
        'data': [dict(
            x=x,
            y=y,
            type='bar',
            marker={
                'color': 'grey'
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


# In[21]:


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
       
    return (get_daily_graph(dff.date, dff.new_cases,"Daily New Cases"),
            get_daily_graph(dff.date, dff.new_deaths,"Daily New Deaths"),
            get_daily_graph(dff.date, dff.new_tests,"Daily New Tests"))


# In[22]:


# Alcohol sales callback
@app.callback(Output('alcohol-stats', 'figure'), Input('alcohol-stats-type', 'value'))
def update_alcohol_sales_plot(alcohol_stats_type):
    if (alcohol_stats_type == datasets_options[0]):
        return get_alcohol_sales_previous_year()
    else:
        return get_alcohol_sales_trend()


# In[23]:


# Trips callback
@app.callback(Output('trips-stats', 'figure'), Input('trips-stats-type', 'value'))
def update_alcohol_sales_plot(alcohol_stats_type):
    if (alcohol_stats_type == datasets_options[0]):
        return get_trips_previous_year()
    else:
        return get_trips_trend()


# In[24]:


# Comparison tab callback
@app.callback(Output('comparison-plot', 'figure'), [
        Input('multi-country-input', 'value'),
        Input('comparison-type', 'value'),
    ])
def update_comparison_plot(locations, comparison_type):
#     return get_comparison_plot(locations, comparison_type, getTitleText(comparison_type) + " (7-day smoothed)")
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
        )
    }


# In[25]:


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


# In[26]:


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


# In[27]:


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


# In[28]:


# World table callback
@app.callback([
    Output('world-table', 'data'),
    Output('world-table', 'columns'),
    Output('world-table', 'sort_by'),
], Input('table-type', 'value'))
def update_table(table_type):
    data = []
    columns = {}
    sort_by = {}
    if(table_type == None or len(table_type) == 0):
        data=dft.to_dict('records')
        columns=[{'id': c, 'name': getTitleText(c), "type": getType(c), 'format': getFormat(c)} for c in dft.columns]
        sort_by=[{"column_id": 'total_deaths', "direction": "desc"}]
    else:
        data=dftpm.to_dict('records')
        columns=[{'id': c, 'name': getTitleText(c.replace("total", "")),
                  "type": getType(c), 'format': getFormat(c)} for c in dftpm.columns]
        sort_by=[{"column_id": 'total_deaths_per_million', "direction": "desc"}]
    return data, columns, sort_by


# In[29]:


# Analysis rank table callback
@app.callback(
    Output('analysis-plot', 'figure'),
    [
        Input('select-property', 'value'),
        Input('analysis-options', 'value'),
    ]
)
def update_analysis_graph(analysis_type, options):
    data = []
    number_of_countries = 10
    asc = False
    column = "new_deaths_smoothed"
    top = "Top"
    per_million = ""
    if(options != None):
        if("sort_reverse" in options):
            asc = True
            top = "Bottom"
        if("per_million" in options):
            column = "new_deaths_smoothed_per_million"
            per_million = "per million people"

    dfa = dfmain_no_world.sort_values(analysis_type, ascending=asc).head(number_of_countries)
    locations = dfa.location
    
    for location in locations:
        dfc = df[df.location == location]
        sub_data = dict(
            x=dfc.date,
            y=dfc[column],
            type='scatter',
            name=location,
            hovertemplate="%{y:,.2f}",
        )
        data.append(sub_data)
        
    return {
            'data': data,
            'layout': dict(
            margin={'l': 40, 'b': 30, 't': 60, 'r': 0},
            hovermode='x unified',
            title={
            'text': "Daily New Confirmed COVID-19 Deaths (7-day smoothed) ",
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
                    text=getTitleText(analysis_type) +" ("+
                    top +" "+ str(number_of_countries) +")",
                )
            ),
        )
    }


# In[30]:


# dfgm = pd.read_csv("Global_Mobility_Report.csv", dtype={"country_region_code": "string",
#                                                  "country_region": "string",
#                                                  "sub_region_1": "string",
#                                                  "sub_region_2": "string",
#                                                  "metro_area": "string",
#                                                  "iso_3166_2_code": "string",
#                                                  "census_fips_code": "string",
#                                                  })


# In[31]:


# dfgm[dfgm.sub_region_2 == "Ålesund Municipality"]


# In[32]:


if __name__ == '__main__':
	app.run_server(debug=debug)

