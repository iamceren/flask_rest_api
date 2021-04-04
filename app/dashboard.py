# import time
# from flask_sqlalchemy import SQLAlchemy
# import dash
# from dash.dependencies import Output, Input
# import dash_core_components as dcc
# import dash_html_components as html
# import plotly
# import random
# from app import server, LogData
# import plotly.graph_objs as go
# from collections import deque
#
# app = dash.Dash(__name__, server=server)
#
# app.layout = html.Div(
#     children=[
#         html.Div(className='row',
#                  children=[
#                      html.Div(className='four columns div-user-controls',
#                               children=[
#                                   html.H2('DASH - STOCK PRICES'),
#                                   html.P('Visualising time series with Plotly - Dash.'),
#                                   html.P('Pick one or more stocks from the dropdown below.')
#                               ]
#                               ),
#                      html.Div(className='eight columns div-for-charts bg-grey')
#                  ])
#     ]
#
# )
#
#
# @app.callback(
#     Output('live-graph', 'figure'),
#     [Input('graph-update', 'n_intervals')]
# )
# def update_graph_scatter():
#     hour = time.time() - 60 * 60
#     message = LogData.query.filter(LogData.timestamp >= hour).all()
#     print(message[0])
#     X = 1
#     Y = 2
#
#     data = plotly.graph_objs.Scatter(
#         x=list(X),
#         y=list(Y),
#         name='Scatter',
#         mode='lines+markers'
#     )
#
#     return {'data': [data],
#             'layout': go.Layout(xaxis=dict(
#                 range=[min(X), max(X)]), yaxis=
#             dict(range=[min(Y), max(Y)]),
#             )}
#
#
# if __name__ == '__main__':
#     app.run_server(port=5000)
