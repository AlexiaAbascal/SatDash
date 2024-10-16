import dash
import serial
from dash import html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px
import threading
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_daq as daq
import os

## SENSOR TYPES
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
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200

## organization structure of received data
data = pd.DataFrame(columns=['date', 'time', 'sensor_type', 'value'])

## serial connection
serial_connection = serial.Serial(SERIAL_PORT,BAUD_RATE)
previous_clicks = 0
data_lock = threading.Lock()

def read_serial():
    global data
    while True:
        try:
            date = serial_connection.readline().decode('utf-8').strip()
            time = serial_connection.readline().decode('utf-8').strip()
            sensor_type = serial_connection.readline().decode('utf-8').strip()
            value = serial_connection.readline().decode('utf-8').strip()

            new_row = pd.DataFrame({
                'date': [date],
                'time': [time],
                'sensor_type': [sensor_type],
                'value': [value]
            })

            with data_lock: 
                data = pd.concat([data, new_row], ignore_index=True)
            print(f"Stored Data: {data}")

        except (IndexError, ValueError) as e:
            print(f"Error parsing data: {e}")
                       
threading.Thread(target=read_serial, daemon=True).start()

app.layout = html.Div([
    
    dbc.NavbarSimple(
        brand = html.Div(
            "Sat-Dash",
            style={'fontWeight':'600', 'color': 'white'}

        ),
        color = "#1e1e1e",
        sticky = "top",
        dark = True,
        children=[
            html.Div(id='date-time'),
            html.Button('Save Data', id='save-data-button', n_clicks=0),
        ], 
        style={'height': '40px'}
    ),
    
    dbc.Container([
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='gps-map'),
            width=12    
        )
    ),
    
    dbc.Row([
        dbc.Col(
            html.Div(
                [
                    html.Label("Yaw", className="label-yaw"),
                    daq.LEDDisplay(
                        id='led-yaw',
                        value='0.00',
                        color='#15B392',
                        backgroundColor= '#1e1e1e',
                        size=20)
                ]
            ),
            width=3
        ),
        dbc.Col(
            html.Div(
                [
                    html.Label("Pitch", className="label-pitch"),
                    daq.LEDDisplay(
                        id='led-pitch',
                        value='0.00',
                        color='#15B392',
                        backgroundColor= '#1e1e1e',
                        size=20
                    )
                ]            
            ),
            width=3
        ),
        dbc.Col(
            html.Div(
                [
                    html.Label("Roll",className="label-roll"),
                    daq.LEDDisplay(
                        id='led-roll',
                        value='0.00',
                        color='#15B392',
                        backgroundColor= '#1e1e1e',
                        size=20
                    )
                ]
            ),
            width=3
        )],
        justify='between'
    ),
 
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='temperature-scatter'),
            width=5,
        ),
        dbc.Col(
            dcc.Graph(id='temperature-gauge'),
            width=5
        ),
        dbc.Col(
            html.Div(
                [
                    html.Label("Telemetry Commands",className="label-telemetry"),
                    dcc.Dropdown(
                        id='sensor-dropdown',
                        options=[
                            {'label': 'Temperature', 'value': 'Temperature'},
                            {'label': 'Pressure', 'value': 'Pressure'},
                            {'label': 'GPS', 'value': 'GPS'},
                            {'label': 'Gyroscope', 'value': 'Gyroscope'},
                            {'label': 'Battery', 'value': 'Battery'}
                        ],
                    ), 
                    dcc.Input(
                        id= 'input-interval',
                        placeholder='Enter seconds',
                        type='number',
                        value=''
                    ),  
                    html.Div(
                        html.Button('Send', id='start-button', n_clicks=0),
                        className='button-container'
                    )
                ],
            className="telemetry-container"),
            width=2
        )
        ],
        justify='between',
    ),
    
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='pressure-scatter'),
            width=5
        ),
        dbc.Col(
            dcc.Graph(id='pressure-gauge'),
            width=5
        ),
        dbc.Col(
            daq.Tank(
                id='battery-tank',
                label={"label": "Battery Level", "style": {"color": "white"}}, 
                units="percent",
                labelPosition = 'bottom',
                color = '#15B392', 
                value = 5,
                showCurrentValue=True,
                width=100,
                height = 160,
                min=0,
                max=100,

            ),
            width = 2
    
        )],
        justify='between'
    ),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
],fluid=True,style={'padding': '0px', 'margin': '0px', 'maxWidth': '100vw', 'overflowX': 'hidden'})
])

@callback(
    Output('save-data-button', 'n_clicks'),
    Input('save-data-button', 'n_clicks')
)

def save_data(n_clicks):
    if n_clicks > 0:
        with data_lock:
            if not data.empty:
                for sensor_type in ['Temperature', 'Pressure', 'GPS', 'Gyroscope']:
                    sensor_data = data[data['sensor_type'] == sensor_type]
                    if not sensor_data.empty:
                        filename = f'{sensor_type}_data.csv'
                        if os.path.exists(filename):
                            with open(filename, 'r') as f:
                                last_line = f.readlines()[-1].strip()
                            last_entry = pd.read_csv(filename).iloc[-1]
                            last_entry_index = sensor_data[(sensor_data == last_entry).all(axis=1)].index
                            if not last_entry_index.empty:
                                new_data = sensor_data.loc[last_entry_index[-1] + 1:]
                            else:
                                new_data = sensor_data  
                        else:
                            new_data = sensor_data  
                        if not new_data.empty:
                            new_data.to_csv(filename, mode='a', header=not os.path.exists(filename), index=False)
                            print(f"New data appended to {filename}.")
                        else:
                            print(f"No new data to append for {sensor_type}.")
                    else:
                        print(f"No data to save for {sensor_type}.")
            else:
                print("No data to save.")
    return 0


@callback(
    Output('start-button', 'children'),
    Input('start-button', 'n_clicks'),
    Input('sensor-dropdown', 'value'),
    Input('input-interval', 'value') 

)

def update_button_text(n_clicks, selected_value, interval):
    global previous_clicks

    if n_clicks > previous_clicks:
        print(f"click {n_clicks} {selected_value},{interval}")
        request = f"{selected_value},{interval}"
        serial_connection.write(request.encode('utf-8'))  

        previous_clicks = n_clicks

    return 'Send'

@app.callback(
    [   
        Output('gps-map', 'figure'),

        Output('led-yaw', 'value'),
        Output('led-pitch', 'value'),
        Output('led-roll', 'value'),
        
        Output('temperature-scatter', 'figure'),
        Output('temperature-gauge', 'figure'),

        Output('pressure-scatter', 'figure'),
        Output('pressure-gauge', 'figure'),
        Output('battery-tank','value'),
        
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

    map_fig.update_layout(paper_bgcolor='#2b2b2b', plot_bgcolor='#2b2b2b', font_color='white')
    temp_fig.update_layout(paper_bgcolor='#2b2b2b', plot_bgcolor='#2b2b2b', font_color='white')
    gauge_temp_fig.update_layout(paper_bgcolor='#2b2b2b', plot_bgcolor='#2b2b2b', font_color='white')
    pressure_fig.update_layout(paper_bgcolor='#2b2b2b', plot_bgcolor='#2b2b2b', font_color='white')
    gauge_pressure_fig.update_layout(paper_bgcolor='#2b2b2b', plot_bgcolor='#2b2b2b', font_color='white')
    
    with data_lock:
        if not data.empty:
            # date and time data
            latest_date_time = data.iloc[-1]
            date_time = f"{latest_date_time['date']} {latest_date_time['time']}"

            # Filtering GPS data
            gps_data = data[data['sensor_type'] == 'GPS'].copy()
            if not gps_data.empty:
                gps_data[['lat', 'lon']] = gps_data['value'].str.split(',', expand=True)
                gps_data = gps_data.drop(columns=['value'])
                gps_data = gps_data.astype({'lat': float, 'lon': float})
                
                # Creating the GPS map figure
                map_fig = go.Figure(go.Scattermap(
                    lat=gps_data['lat'],
                    lon=gps_data['lon'],
                    mode='markers',
                    marker=go.scattermap.Marker(color='#15B392', size=9),
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
                        zoom=0, 
                        style='dark',
                    ),
                    margin=dict(l=0, r=0, t=0, b=0),
                )

            # Filtering gyroscope data
            gyro_data = data[data['sensor_type'] == 'Gyroscope'].copy()
            if not gyro_data.empty:
                gyro_data[['yaw', 'pitch', 'roll']] = gyro_data['value'].str.split(',', expand=True)
                gyro_data = gyro_data.drop(columns=['value'])
                gyro_data = gyro_data.astype({'yaw': float, 'pitch': float, 'roll': float})
                latest_gyro = gyro_data.iloc[-1]
                yaw_value = f"{latest_gyro['yaw']:.2f}"
                pitch_value = f"{latest_gyro['pitch']:.2f}"
                roll_value = f"{latest_gyro['roll']:.2f}"
            else:
                yaw_value = ""
                pitch_value = ""
                roll_value = ""
      
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
                    margin=dict(l=15, r=15, t=80, b=15),
                    title_font=dict(color='white', size=15), 
                    xaxis_title='Time (s)',
                    xaxis_title_font=dict(color='gray',size=10),
                    xaxis_tickfont=dict(color='gray',size=10),
                    xaxis=dict(linecolor='gray', gridcolor='gray'),
                    yaxis_title='Temperature',
                    yaxis_title_font=dict(color='gray',size=10),
                    yaxis_tickfont=dict(color='gray',size=10),
                    yaxis=dict(showgrid=False),
                    plot_bgcolor='#2b2b2b',
                    paper_bgcolor='#2b2b2b',
                    hoverlabel=dict(font=dict(color='rgba(30, 30, 30,1)'))
                )

                temp_fig.update_traces(marker=dict(color='#15B392'), marker_size=8)

                # Gauge for temperature
                gauge_temp_fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=latest_temp,
                    title={'text': "Current Temperature", 'font': {'size': 15}},
                    gauge={
                        'axis': {'range': [None, 100], 'tickcolor': 'gray'},
                        'bar': {'color': '#15B392'},
                        'steps': [
                            {'range': [0, 50], 'color': 'darkgray'},
                            {'range': [50, 100], 'color': 'gray'},
                        ],
                    }
                ))

                gauge_temp_fig.update_layout(
                    paper_bgcolor='#2b2b2b', 
                    font_color='white', 
                    margin=dict(l=30, r=30, t=55, b=30)
                )
        
            # Filtering pressure data
            pressure_data = data[data['sensor_type'] == 'Pressure'].copy()
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
                    margin=dict(l=15, r=15, t=80, b=15),
                    title_font=dict(color='white', size=15),
                    xaxis_title='Time (s)',
                    xaxis_title_font=dict(color='gray',size=10),
                    xaxis_tickfont=dict(color='gray',size=10),
                    xaxis=dict(linecolor='gray', gridcolor='gray'),
                    yaxis_title='Pressure',
                    yaxis_title_font=dict(color='gray',size=10),
                    yaxis_tickfont=dict(color='gray',size=10),
                    yaxis=dict(showgrid=False),
                    plot_bgcolor='#2b2b2b',
                    paper_bgcolor='#2b2b2b',
                    hoverlabel=dict(font=dict(color='rgba(30, 30, 30,1)')),
                )

                pressure_fig.update_traces(marker=dict(color='#15B392'), marker_size=8)

                # Gauge for pressure
                gauge_pressure_fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=latest_pressure,
                    title={'text': "Current Pressure", 'font': {'size': 15}},
                    gauge={
                        'axis': {'range': [None, 100], 'tickcolor': 'gray'},
                        'bar': {'color': '#15B392'},
                        'steps': [
                            {'range': [0, 50], 'color': 'darkgray'},
                            {'range': [50, 100], 'color': 'gray'},
                        ],
                    }
                ))

                gauge_pressure_fig.update_layout(
                    paper_bgcolor='#2b2b2b', 
                    font_color='white', 
                    margin=dict(l=30, r=30, t=55, b=30)
                )
                
                # Filtering battery data
                battery_data = data[data['sensor_type'] == 'Battery'].copy()
                if not battery_data.empty:
                    battery_data = battery_data.astype({'value':float})
                    latest_battery = battery_data.iloc[-1]['value']
                    battery_value = float(latest_battery)
                else:
                    battery_value = 0
        else :
            date_time = ""
            yaw_value = ""
            pitch_value = ""
            roll_value = ""
            battery_value = 0
        return map_fig, yaw_value, pitch_value, roll_value, temp_fig, gauge_temp_fig, pressure_fig, gauge_pressure_fig, battery_value, date_time
        
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)