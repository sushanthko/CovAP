#!/usr/bin/env python
# coding: utf-8

# # COVID-19 Analysis Platform

# In[1754]:


from jupyter_dash import JupyterDash


# In[1755]:


import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_bootstrap_components as dbc
import dash_table as dt
from dash.dependencies import Input, Output


# In[1756]:


debug = pd.read_json("properties.json", orient="index").debug.value


# In[1757]:


df = pd.read_csv("owid-covid-data.csv")


# In[1758]:


countries = df.location.unique()


# In[1759]:


dpm_countries = 20
world_code = "OWID_WRL"

null_fill_columns = {'new_cases': 0, 'new_deaths': 0, 'total_cases': 0, 'total_deaths': 0}
null_columns = ['new_cases', 'new_deaths', 'total_cases', 'total_deaths', 'total_cases_per_million', 'total_deaths_per_million']

dfmain = df[df.groupby(['location']).date.transform('max') == df.date]
dfmain = dfmain.fillna(null_fill_columns)

dftt = dfmain[['location', 'continent', 'total_cases', 'total_deaths']]
dftm = dfmain[['location', 'continent', 'total_cases_per_million', 'total_deaths_per_million']]

dfm = dfmain[['iso_code', 'location', 'total_cases_per_million', 'total_deaths_per_million']]
dfm = dfm[~dfm.iso_code.isin(['OWID_WRL'])] # Remove world row for map


# In[1760]:


header = html.H1("CovAP dashboard")
last_updated = html.H6("Last updated on: "+df.date.max(),className="text-right")


# In[1761]:


# Daily stats tab content
daily_stats_div = html.Div([
    
    html.Div(html.Div(html.Label("Select country"), className="col"), className="row"),
        
    html.Div(html.Div(dcc.Dropdown(
            id='country-input',
            options=[{'label': i, 'value': i} for i in countries],
            value='Norway',
            clearable=False,
    ), className="col-3"), className="row"),
    
    html.Div([
        
        html.Div(dcc.Graph(id='daily-cases'), className="col"),
        
        html.Div(dcc.Graph(id='daily-deaths'), className="col"),
        
        html.Div(dcc.Graph(id='daily-tests'), className="col"),
        
    ], className="row align-items-center"),
    
], className="container-fluid")


# In[1762]:


def getFormat(column):
    if(column in null_columns):
        if("per_million" in column):
            return {'specifier': ',.2f'}
        else:
            return {'specifier': ',.0f'}
    return None

    
def getType(column):
    if(column in null_columns):
        return "numeric"
    return "text"


def getTitleText(text):
    return text.title().replace('_', ' ')


# In[1763]:


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


# In[1764]:


# World data tab cotent
world_data_div = html.Div([
    
    html.Div([
        
        html.Div(html.Div([
            
            html.Div(html.Div(
                    dcc.RadioItems(
                    id='map-type',
                    options=[{'label': getTitleText(i), 'value': i}
                             for i in ['total_deaths_per_million', 'total_cases_per_million']],
                    value='total_deaths_per_million',
                    labelStyle={'display': 'inline-block', 'margin':'0 1%'}
                ),
                className="col"), className="row"),
            
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
                
                html.Div(html.H4("Reported cases and deaths by country", className="mt-2"), className="col-auto"),
                html.Div(
                    dcc.Checklist(id="table-type", options=[{'label': 'Per Million', 'value': 'per_million'}],
                                 labelStyle={'display': 'inline-block', 'margin':'0'}),
                    className="col d-flex align-items-center justify-content-start mt-2"),
            ], className="row"),
            
            html.Div(html.Div(world_table, className="col overflow-auto"), className="row"),
            
            ], className="container-fluid"), className="col"),
    ], className="row"),
        
], className="container-fluid")


# In[1765]:


# Analysis tab content
analysis_div = html.Div([
    
    html.Div(html.Div(
        html.H2("Analysis of top " +str(dpm_countries)+" countries with highest deaths per million"),
        className="col"), className="row"),
    
    html.Div(html.Div(dcc.RadioItems(
                id='parameter',
                options=[{'label': i, 'value': i} for i in ['Hospital beds per thousand', 'Aged 65 or older(%)']],
                value='Hospital beds per thousand',
#                 labelStyle={'display': 'inline-block'}
            ), className="col"), className="row"),
    
    html.Div(html.Div(dcc.Graph(id='deaths-per-million'), className="col"), className="row"),
    
], className="container-fluid")


# In[1766]:


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
        ]),
        dcc.Tab(label='Analysis', children=[
            analysis_div
        ]),
        dcc.Tab(label='Dataset', children=[
        ]),
    ]),className="col"),className="row"),
], className="container-fluid")


# In[1767]:


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


# In[1768]:


# Daily stats tab callback
@app.callback([
    Output('daily-cases', 'figure'),
    Output('daily-deaths', 'figure'),
    Output('daily-tests', 'figure'),
],
[
    Input('country-input', 'value'),
])
def update_daily_stats(country):

    dff = df[df.location == country]
       
    return (get_daily_graph(dff.date, dff.new_cases,"Daily New Cases"),
            get_daily_graph(dff.date, dff.new_deaths,"Daily New Deaths"),
            get_daily_graph(dff.date, dff.new_tests,"Daily New Tests"))


# In[1769]:


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


# In[1770]:


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


# In[1771]:


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


# In[1772]:


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
        data=dftm.to_dict('records')
        columns=[{'id': c, 'name': getTitleText(c.replace("total", "")),
                  "type": getType(c), 'format': getFormat(c)} for c in dftm.columns]
        sort_by=[{"column_id": 'total_deaths_per_million', "direction": "desc"}]
    return data, columns, sort_by


# In[1773]:


# Analysis tab callback
@app.callback(
    dash.dependencies.Output('deaths-per-million', 'figure'),
[
    dash.dependencies.Input('parameter', 'value')
])
def update_analysis(parameter):
    test = df[['location', 'date', 'total_deaths_per_million', 'hospital_beds_per_thousand', 'aged_65_older', 'population']]
    test = test[test.groupby(['location']).date.transform('max') == df.date]
    data = test.dropna().reset_index().sort_values("total_deaths_per_million", ascending=False).head(dpm_countries)
    
    y = data.hospital_beds_per_thousand
    if(parameter == "Aged 65 or older(%)"):
        y = data.aged_65_older
    
    figure =  {
        'data': [
                dict(
            x=data.location,
            y=y,
#             name=parameter,
#             customdata='Total deaths per million: '+str(data.total_deaths_per_million),
            type='bar',
#             mode='markers',
            marker={
#                 'size': 25,
#                 'opacity': 0.7,
                'color': 'orange',
#                 'line': {'width': 2, 'color': 'purple'}
            },
            hovertext="Total deaths per million: "+data.total_deaths_per_million.round(2).astype(str),
        )],
        'layout': dict(
#             margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
#             height=450,
#             hovermode='closest',
            title= parameter
        )
    }
    
    return figure


# In[1774]:

if __name__ == '__main__':
    app.run_server(debug=debug)

