import dash
import serial
from dash import html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px
import threading

app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

SERIAL_PORT = 'COM3'
BAUD_RATE = 115200

## Gyroscope : yaw, pitch, roll
## GPS : latitude, altitude
## Temperature : degrees
## Pressure : pressure

data = pd.DataFrame(columns=['date', 'time', 'sensor_type', 'value'])

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
    dcc.Graph(id='temperature-scatter'),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

@app.callback(
    Output('temperature-scatter', 'figure'),
    Input('interval-component', 'n_intervals')
)

def update_graph(n):
    if not data.empty:
        temperature_data = data[data['sensor_type'] == 'Temperature']
        temperature_data['time'] = pd.to_numeric(temperature_data['time']) 

        fig = px.scatter(
            temperature_data,
            x='time',
            y='value',
            title='Temperature Over Time',  
        )

        fig.update_layout(
            title_font_color='white',  
            xaxis_title='Time (s)',  
            xaxis_title_font=dict(color='gray'),  
            xaxis_tickfont=dict(color='gray'),  
            xaxis=dict(linecolor='gray', gridcolor='gray'),

            
            yaxis_title='Temperature (°C)',  
            yaxis_title_font=dict(color='gray'),  
            yaxis_tickfont=dict(color='gray'),  
            yaxis=dict(showgrid=False),

            plot_bgcolor='#2b2b2b', 
            paper_bgcolor='#2b2b2b',  
            hoverlabel=dict(font=dict(color='rgba(30, 30, 30,1)'))
        )

        fig.update_traces(marker=dict(color='#FE347E'), marker_size=15)  
        return fig
    

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
