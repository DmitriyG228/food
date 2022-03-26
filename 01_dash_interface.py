from tendo import singleton
me = singleton.SingleInstance()

from dash import html,dcc,Dash
from numpy import False_
import plotly.express as px
import requests
import pandas as pd
from dash.dependencies import Input, Output,State
import dash_bootstrap_components as dbc
import urllib
from dash.exceptions import PreventUpdate
from sqlalchemy import true

from reai.tools import *
import plotly.graph_objects as go
from reai.tools import mapbox_access_token

from  dash_dangerously_set_inner_html import DangerouslySetInnerHTML

from dash import callback_context


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
app.title = "away.guru"

def search(text,min_bedrooms=None,min_beds=None,min_price=None,max_price=None,min_latitude=None,max_latitude=None,min_longitude=None,max_longitude=None, topk = 480): #
    text = text if text !='' else 'amazing lounge with great view'
    url = f"http://localhost:8181/search"
    params = {k:v for k,v in locals().items()}
    response = requests.post(url,params=params)
    return pd.read_json(response.json())

def update_map(df):

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox( lat=df['latitude'],
                                    lon=df['longitude'],
                                    mode='markers',
                                    marker_size=9, 
                                    opacity = 0.7,
                                    marker_color='red',
                                    hoverinfo='text',
                                    text=df['bedrooms'],
                                    customdata=(df[['link','url']]),
                                    
                                    ))
    fig.update_layout(
        autosize=True,
        hovermode='closest',
        title='Bathymetrical Data',
        margin=dict(t=0, b=0, l=0, r=0),
        mapbox=dict(
            accesstoken= mapbox_access_token,
            zoom=1,
            style="satellite-streets"
        ),
    )
    fig['layout']['uirevision'] = 'no reset of zoom'
    return fig

def prep_listing(row):
    img = row['url']
    card_content =[ dbc.CardHeader(f"{row['bedrooms']}-bedroom", className = 'center'),
                    dbc.CardBody(
                        [html.A(
                            # dbc.CardImg(src=row['url'],alt = 'sorry, image is broken')
                            DangerouslySetInnerHTML(f'<img class="card-img" src="{img}" style="border-radius: 0px;" loading="lazy">')
                            
                            , href=row['link'], target='_blank')]
                    ),
                    dbc.CardFooter(f"{int(row['price'])} $" if (row['price']==row['price'] or row['price']==0) else 'price not avaliable', className = 'center'),
                ] 

    return dbc.Col(dbc.Card(card_content),xs=12,sm=6,md=4,lg=3,xl=2)



contact = dbc.Row(html.A([html.Img(src='https://away.guru/photos/facebook-Button.jpg',height=40,width=120)], 
                                 href='https://www.facebook.com/dmi.grankin', 
                                 target='_blank',className = 'center'))


app.layout = dbc.Container(
    [
        contact,
        html.Br(),
        html.Br(),
        dcc.Location(id='url', refresh=True),
        dbc.Row(html.H4('search hidden features of airbnb homes',className = 'text-center text-primary, mb-4')), #
        dbc.Row([
                dbc.Col(dbc.Input    (id='q'  , type="search", value   ='amazing terrasse with fantastic view over the ocean', 
                                      debounce=True, persistence=True,placeholder = 'what do you want to see in the pictures?'), xs=11,sm=11,md=11,lg=11,xl=11),
                dbc.Col(dcc.Clipboard(id="share", title="copy", style={
                    "display": "inline-block",
                    "fontSize": 20,
                    "verticalAlign": "top",
                },), xs=1,sm=1,md=1,lg=1,xl=1),                
                ]),

        html.Br(),        
        html.Br(),
        dbc.Row([


            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("min bedrooms", style={"width": 100,'fontSize': 12}),
                    dbc.Input(id="min_bedrooms", type='number', min=0, max=9, persistence=True, style={"width": 20,'fontSize': 12},placeholder = 1),
                ])


            ],xs=12,sm=12,md=3,lg=2,xl=2),

            dbc.Col([
                dbc.InputGroup([
                        dbc.InputGroupText("min beds", style={"width": 100,'fontSize': 12}),
                        dbc.Input(id="min_beds", type='number', min=1, max=15, persistence=True, style={"width": 20,'fontSize': 12},placeholder = 1),
                ])
            ],xs=12,sm=12,md=3,lg=2,xl=2),

            dbc.Col([
                dbc.InputGroup([
                        dbc.InputGroupText("min price", style={"width": 100,'fontSize': 12}),
                        dbc.Input(id="min_price", type='number', min=1, max=5000, persistence=True, style={"width": 10,'fontSize': 12},placeholder = 1),
                ])

            ],xs=12,sm=12,md=3,lg=2,xl=2),

            dbc.Col([
                dbc.InputGroup([
                        dbc.InputGroupText("max price", style={"width": 100,'fontSize': 12}),
                        dbc.Input(id="max_price", type='number', min=20, max=100000, persistence=True, style={"width": 10,'fontSize': 12},placeholder = 10000)
                ])

            ],xs=12,sm=12,md=3,lg=2,xl=2),


            dbc.Col([
                    dbc.Button(id="collapse-button",
                                className="mb-3",
                                color="primary",
                                n_clicks=0,
                            ),
                        ],xs=12,sm=12,md=5,lg=3,xl=2),
            ],justify='center'),



        dbc.Row([
            html.Div(
                        [
                            dbc.Collapse(
                                dbc.Card([
                                    dbc.CardHeader('zoom into the area of interest and check search results'),
                                    dbc.CardBody([
                                        html.Div
                                        ([
                                            dcc.Graph(id='map',config = {'displayModeBar':False}),
                                            ]),

                                ]),
                                    
                                    ]),
                                id="collapse",
                                is_open=False),
                        ]
                    )

        ]),


        html.Br(),
        html.Br(),
        dbc.CardGroup(id='body'),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(id='coordinates',style={'display': 'none'}),
        ],fluid = True)


def build_share_url(params):
    return "https://away.guru/search/?"+urllib.parse.urlencode(params)


# @app.callback(
#     Output('map-clicks', 'children'),
#     [Input('map', 'clickData')])
# def display_click_data(clickData):
#     if clickData is None:
#         return 'nothing yet'
#     else:
#         link,img = clickData['points'][0]['customdata']
#         # link=clickData['points'][0]['customdata']['link']
#         # img     =clickData['points'][0]['customdata']['url']
#         # # school_name = clickData['points'][0]['text']
#         # print(link)
#         # # return html.A(school_name, href=the_link, target='_blank')
#         return html.A(DangerouslySetInnerHTML(f'<img class="card-img" src="{img}" style="border-radius: 0px;" loading="lazy">')
                            
#                             , href=link, target='_blank')



@app.callback(
    Output("collapse", "is_open"),
    Output("collapse-button", "children"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    init_state = "open map"
    open_state = 'collapse map'
    if  n==0: return False, init_state
    elif n%2!=0: return not is_open, open_state
    elif n%2==0: return not is_open, init_state



@app.callback(Output('body','children'), 
               Output('map','figure'), 
               Output('share', 'content'),
               Input('q','value'),
               Input('min_bedrooms', 'value'),
               Input('min_beds', 'value'),
               Input('min_price', 'value'),
               Input('max_price', 'value'),
               Input('coordinates','children'))
def update(text,min_bedrooms,min_beds,min_price,max_price,coordinates):
        print(callback_context.triggered)

        min_latitude,max_latitude,min_longitude,max_longitude = coordinates
        del coordinates
        params = {k:v for k, v in locals().items() if v is not None}
        share_url = build_share_url(params)

        df = search(**params)
        results = df.iterrows()

        return [prep_listing(r[1]) for r in results], update_map(df),share_url

from collections import defaultdict

@app.callback(
    Output('coordinates', 'children'),
    Input('map', 'relayoutData'))
def display_relayout_data(relayoutData):
    try:
        coords = relayoutData['mapbox._derived']['coordinates']
        lon_min = coords[0][0]
        lon_max = coords[1][0]
        lat_min = coords[2][1]
        lat_max = coords[1][1]
        
        return [lat_min, lat_max, lon_min, lon_max]
    except:
        return [None,None,None,None]

# @app.callback(Output('q', 'value'),
#               Output('min_bedrooms', 'value'),
#               Output('min_beds', 'value'),
#               Output('min_price', 'value'),
#               Output('max_price', 'value'),
#               Output('coordinates','children'),
#               Input('url', 'search'),
#               State('url', 'pathname'),
#               )
# def display_page(search, pathname):
#     parsed_url   = urllib.parse.urlparse(search)
#     parsed_query = urllib.parse.parse_qs(parsed_url.query)
#     parsed_query = defaultdict(lambda:[None],parsed_query)

#     print(parsed_query)

#     if pathname.strip('/') != 'search': 
#         raise PreventUpdate
    
#     result = {x:parsed_query[x][0] for x in ['q']}
#     if not any(result.values()): 
#         raise PreventUpdate

#     for k in ['min_bedrooms', 'min_beds']:
#         if result[k] is not None: 
#             result[k] = int(result[k])

#     print(result)
#     return *result.values(), ''



if __name__ == '__main__': app.run_server(port = 8867,debug=False)

