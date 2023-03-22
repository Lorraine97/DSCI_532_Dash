import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

TEMP_PATH = "https://raw.githubusercontent.com/UBC-MDS/climadash/main/data/processed/temperature_data.csv"
PREC_PATH = "https://raw.githubusercontent.com/UBC-MDS/climadash/main/data/processed/percipitation_data.csv"

temp_df = pd.read_csv(TEMP_PATH, sep=',', parse_dates=["LOCAL_DATE"])
prec_df = pd.read_csv(PREC_PATH, sep=',', parse_dates=["LOCAL_DATE"])
total_df = temp_df.merge(prec_df, how='inner', on=["LOCAL_DATE", "CITY"])
total_df["year"] = total_df["LOCAL_DATE"].dt.year
total_df["year_month"] = total_df["LOCAL_DATE"].dt.to_period('M')
cities = total_df['CITY'].unique()
year_range = total_df['year'].unique()

geo_df = pd.DataFrame(
    {
        "CITY": ["CALGARY", "EDMONTON", "HALIFAX", "MONCTON", "MONTREAL", "OTTAWA", "QUEBEC CITY",
                 "SASKATOON", "STJOHNS", "TORONTO", "VANCOUVER", "WHITEHORSE", "WINNIPEG"],
        "lat": [51.0447, 53.5444, 44.6488, 46.0878, 45.5017, 45.4215, 46.8139, 52.1332,
                47.5615, 43.6532, 49.2827, 60.7212, 49.8951],
        "long": [-114.0719, -113.4909, -63.5752, -64.7782, -73.5673, -75.6972, -71.2080,
                 -106.6700, -52.7126, -79.3832, -123.1207, -135.0568, -97.1384]
    })

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "20rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Setup app and layout/frontend
app = dash.Dash(external_stylesheets=[dbc.themes.LITERA])
app.layout = dbc.Container([
    
    dbc.Row([
        
        dbc.Col(
            [
                html.H3('Data Filters'),
                html.Div([
                    html.Hr(),
                    dcc.Dropdown(
                        id="city-dropdown",
                        options=cities,
                        value=["VANCOUVER", "TORONTO"],
                        multi=True),
                    html.Hr(),
                ]),
                html.Div([
                    html.Img(src="images/temperature.svg", height=15),
                    dcc.RadioItems(
                        options=[
                            {
                                "label": [
                                    html.Img(src="images/temperature.svg", height=15),
                                    html.Span("Temperature", style={'font-size': 15, 'padding-left': 10}),
                                ],
                                "value": "MEAN_TEMP_C"
                            },
                            {
                                "label": [
                                    html.Img(src="images/precipitation.png", height=15),
                                    html.Span("Precipitation", style={'font-size': 15, 'padding-left': 10}),
                                ],
                                "value": "TOTAL_PERCIP_mm"
                            },
                        ],
                        value='MEAN_TEMP_C',
                        id='data-option',
                    ),
                    
                    html.Hr(),
                ]),
                html.Div([
                    "Start year: ",
                    dcc.Dropdown(id="year-start", options=year_range, value=min(year_range)),
                    "End year: ",
                    dcc.Dropdown(id="year-end", value=max(year_range)),
                    html.Hr(),
                ]),
            ],
            style=SIDEBAR_STYLE,
        ),
        dbc.Col(
            [
                html.H1('Dash Demo'),
                dcc.Graph(id='line-graph'),
                html.Hr(),
                "Select year for the following graph: ",
                dcc.Dropdown(id="geo-year", value=max(year_range)),
                dcc.Graph(id='geo-graph'),
                html.Hr(),
            ],
            style=CONTENT_STYLE
        )
    ])
])


@app.callback(
    Output("geo-year", "options"),
    Input("year-start", "value"),
    Input("year-end", "value"),
)
def update_geo_year_options(year_start, year_end):
    if not year_start: year_start = min(year_range)
    if not year_end: year_end = max(year_range)
    return year_range[(year_range >= year_start) | (year_range >= year_end)]


@app.callback(
    Output("year-end", "options"),
    Input("year-start", "value"),
)
def update_year_end_options(year_start):
    if not year_start:
        return year_range
    else:
        return year_range[year_range > year_start]


@app.callback(
    Output("line-graph", "figure"),
    Input("city-dropdown", "value"),
    Input("data-option", "value"),
    Input("year-start", "value"),
    Input("year-end", "value"),
)
def update_cities_chart(selected_cities, data_option, start_year, end_year):
    if data_option == 'MEAN_TEMP_C':
        color_set = px.colors.qualitative.G10
        data_label = 'Temperature'
    else:
        color_set = px.colors.qualitative.Antique
        data_label = 'Precipitation'
    # filter cities
    df = total_df[total_df.CITY.isin(selected_cities)]
    # filter year range
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
    monthly_df = df.groupby(['year', 'CITY']).mean().reset_index()
    
    fig = px.line(
        monthly_df,
        x='year',
        y=data_option,
        color='CITY',
        color_discrete_sequence=color_set,
        title=f"Annual Average {data_label} for Canada Major Cities"
    )
    return fig


@app.callback(
    Output("geo-graph", "figure"),
    Input("geo-year", "value"),
    Input("data-option", "value"),
)
def plot_temp_prec(geo_year, data_option):
    if data_option == 'MEAN_TEMP_C':
        color_scale = 'Oranges'
        data_label = 'Temperature'
    else:
        color_scale = 'Blues'
        data_label = 'Precipitation'
    # filter year
    df = total_df[total_df["year"] == geo_year]
    df = df.groupby(['year', 'CITY']).mean().reset_index()
    df = df.merge(geo_df, on='CITY')
    fig = go.Figure(data=go.Scattergeo(
        lon=df['long'],
        lat=df['lat'],
        text=df['CITY'],
        mode='markers',
        marker=dict(
            opacity=0.8,
            color=df[data_option],
            colorscale=color_scale,
            cmin=df[data_option].min(),
            cmax=df[data_option].max(),
            colorbar_title=data_label
        )
    
    ))
    
    fig.update_layout(
        title=f'{data_label} Heatmap for Major Cities in Canada, Year {geo_year}',
        geo_scope='north america',
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
