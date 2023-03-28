import dash
from dash import dcc
from dash import html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
import boto3
import io
import os

# Connect to S3 bucket
bucket = "tnb-cust11"
access_key=os.environ["AWS_ACCESS_KEY_ID"]
secret_key=os.environ["AWS_SECRET_ACCESS_KEY"]

s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
# Download the csv file
#csv_obj = bucket.Object('objets-trouves-restitution.csv').get()['Body'].read().decode('utf-8')
df = pd.read_csv(f's3://{bucket}/objets-trouves-restitution.csv')
#df = pd.read_csv(io.StringIO(csv_obj))

# Compute the size of each group of stations
size = df.groupby('fields.gc_obo_gare_origine_r_name').size().reset_index(name='size')

# Merge the size information with the original DataFrame
df = pd.merge(df, size, on='fields.gc_obo_gare_origine_r_name')

# Create the Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div([
    html.H1('Lost and Found Records'),
    html.Div([
        dcc.Graph(id='map-graph')
    ], style={'width': '50%', 'display': 'inline-block'}),
    html.Div([
        html.H2('Statistics'),
        html.P(f'Total records: {len(df)}'),
        html.P(f'Total unique stations: {len(df["fields.gc_obo_gare_origine_r_name"].unique())}'),
        html.P(f'Total unique types: {len(df["fields.gc_obo_type_c"].unique())}')
    ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'})
])

# Define the map graph
@app.callback(
    Output('map-graph', 'figure'),
    Input('map-graph', 'clickData')
)
def update_map(click_data):
    fig = px.scatter_mapbox(df, 
                            lat='latitude', 
                            lon='longitude', 
                            hover_name='fields.gc_obo_gare_origine_r_name', 
                            zoom=3, 
                            height=600,
                            size='size',
                            color='fields.gc_obo_type_c',
                            mapbox_style='open-street-map')
    fig.update_layout(transition_duration=500)
    fig.update_layout(showlegend=False)  # Remove the legend
    fig.update_layout(mapbox_style='open-street-map', mapbox=dict(center=dict(lat=48.85, lon=2.35), zoom=10))  # Set the default map position and zoom level
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})  # Remove the margin
    fig.update_layout(width=900)  # Increase the width of the map
    fig.update_traces(hovertemplate=None)  # Remove the latitude and longitude when hovering over the points
    return fig


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
