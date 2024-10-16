import dash
import serial
from dash import html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px
import threading
import plotly.graph_objects as go
import dash_bootstrap_components as dbc


## Gyroscope : yaw, pitch, roll
## GPS : latitude, altitude
## Temperature : degrees
## Pressure : pressure

app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width"}
    ],
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

## serial port communication configs
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200

## organization structure of received data
data = pd.DataFrame(columns=['date', 'time', 'sensor_type', 'value'])

## serial connection
serial_connection = serial.Serial(SERIAL_PORT,BAUD_RATE)

def read_serial():
    while True:
            try:
                date = serial_connection.readline().decode('utf-8').strip()
                time = serial_connection.readline().decode('utf-8').strip()
                sensor_type = serial_connection.readline().decode('utf-8').strip()
                value = serial_connection.readline().decode('utf-8').strip()
                            
                new_row = pd.DataFrame({
                    'date': [date],
                    'time' : [time],
                    'sensor_type': [sensor_type],
                    'value': [value]
                })
                
                global data
                data = pd.concat([data, new_row], ignore_index=True)
                print(f"Stored Data: {data}")
                
            except (IndexError, ValueError) as e:
                print(f"Error parsing data: {e}")
                       
threading.Thread(target=read_serial, daemon=True).start()

app.layout = html.Div([
    
    dbc.NavbarSimple(
        brand = "Sat-Dash",
        color = "#1e1e1e",
        sticky = "top",
        dark = True,
        children=[
            html.Div(id='date-time', style={'color': 'white', 'float': 'right', 'padding': '1rem'})
        ]
    ),
    
    dbc.Container([
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='gps-map'),
            width=12    
        ),
    ),
    
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='temperature-scatter'),
            width=5
        ),
        dbc.Col(
            dcc.Graph(id='temperature-gauge', style={'height': '300px'}),
            width=5
        )],
        justify='between'
    ),
    
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='pressure-scatter'),
            width=6
        ),
        dbc.Col(
            dcc.Graph(id='pressure-gauge', style={'height': '300px'}),
            width=6
        )],
        justify='between'
    ),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
],fluid=True,style={'padding': '0px', 'margin': '0px', 'maxWidth': '100vw', 'overflowX': 'hidden'})
])

@app.callback(
    [   
        Output('gps-map', 'figure'),

        Output('temperature-scatter', 'figure'),
        Output('temperature-gauge', 'figure'),

        Output('pressure-scatter', 'figure'),
        Output('pressure-gauge', 'figure'),
        
        Output('date-time', 'children'),
        
        Input('interval-component', 'n_intervals')
    ]
)

def update_graphs(n):
    map_fig = go.Figure()  
    temp_fig = go.Figure()  
    gauge_temp_fig = go.Figure()
    pressure_fig = go.Figure()  
    gauge_pressure_fig = go.Figure()  
    

    if not data.empty:
        # date and time 
        latest_date_time = data.iloc[-1]
        date_time = f"{latest_date_time['date']} {latest_date_time['time']}"

        # Filtering GPS data
        gps_data = data[data['sensor_type'] == 'Coordinates'].copy()
        if not gps_data.empty:
            gps_data[['lat', 'lon']] = gps_data['value'].str.split(',', expand=True)
            gps_data = gps_data.drop(columns=['value'])
            gps_data = gps_data.astype({'lat': float, 'lon': float})
            
            # Creating the GPS map figure
            map_fig = go.Figure(go.Scattermap(
                lat=gps_data['lat'],
                lon=gps_data['lon'],
                mode='markers',
                marker=go.scattermap.Marker(color='#FE347E', size=9),
                text=gps_data['time']
            ))
            
            map_fig.update_layout(
                map=dict(
                    bearing=0,
                    center=dict(
                        lat=gps_data['lat'].mean(),
                        lon=gps_data['lon'].mean()
                    ),
                    pitch=0,
                    zoom=1,  # Adjust zoom level as needed
                    style='dark',
                ),
                margin=dict(l=0, r=0, t=0, b=0),
            )

        # Filtering temperature data
        temperature_data = data[data['sensor_type'] == 'Temperature'].copy()
        if not temperature_data.empty:
            temperature_data = temperature_data.astype({'value': float})
            latest_temp = temperature_data.iloc[-1]['value']

            # Figure for temperature
            temp_fig = px.scatter(
                temperature_data,
                x='time',
                y='value',
                title='Temperature Over Time',
            )

            temp_fig.update_layout(
                title_font_color='white',
                xaxis_title='Time (s)',
                xaxis_title_font=dict(color='gray'),
                xaxis_tickfont=dict(color='gray'),
                xaxis=dict(linecolor='gray', gridcolor='gray'),
                yaxis_title='Temperature',
                yaxis_title_font=dict(color='gray'),
                yaxis_tickfont=dict(color='gray'),
                yaxis=dict(showgrid=False),
                plot_bgcolor='#2b2b2b',
                paper_bgcolor='#2b2b2b',
                hoverlabel=dict(font=dict(color='rgba(30, 30, 30,1)'))
            )

            temp_fig.update_traces(marker=dict(color='#FE347E'), marker_size=15)

            # Gauge for temperature
            gauge_temp_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest_temp,
                title={'text': "Current Temperature", 'font': {'size': 18}},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': 'gray'},
                    'bar': {'color': '#FE347E'},
                    'steps': [
                        {'range': [0, 50], 'color': 'darkgray'},
                        {'range': [50, 100], 'color': 'gray'},
                    ],
                }
            ))

            gauge_temp_fig.update_layout(paper_bgcolor='#2b2b2b', font_color='white')
       
        # Filtering pressure data
        pressure_data = data[data['sensor_type'] == 'Temperature'].copy()
        if not pressure_data.empty:
            pressure_data = pressure_data.astype({'value': float})
            latest_pressure = pressure_data.iloc[-1]['value']

            # Figure for pressure
            pressure_fig = px.scatter(
                pressure_data,
                x='time',
                y='value',
                title='Pressure Over Time',
            )

            pressure_fig.update_layout(
                title_font_color='white',
                xaxis_title='Time (s)',
                xaxis_title_font=dict(color='gray'),
                xaxis_tickfont=dict(color='gray'),
                xaxis=dict(linecolor='gray', gridcolor='gray'),
                yaxis_title='Pressure',
                yaxis_title_font=dict(color='gray'),
                yaxis_tickfont=dict(color='gray'),
                yaxis=dict(showgrid=False),
                plot_bgcolor='#2b2b2b',
                paper_bgcolor='#2b2b2b',
                hoverlabel=dict(font=dict(color='rgba(30, 30, 30,1)'))
            )

            pressure_fig.update_traces(marker=dict(color='#FE347E'), marker_size=15)

            # Gauge for pressure
            gauge_pressure_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest_pressure,
                title={'text': "Current Pressure", 'font': {'size': 18}},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': 'gray'},
                    'bar': {'color': '#FE347E'},
                    'steps': [
                        {'range': [0, 50], 'color': 'darkgray'},
                        {'range': [50, 100], 'color': 'gray'},
                    ],
                }
            ))

            gauge_pressure_fig.update_layout(paper_bgcolor='#2b2b2b', font_color='white')
    else :
        date_time = ""
    return map_fig, temp_fig, gauge_temp_fig, pressure_fig, gauge_pressure_fig, date_time
    
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)