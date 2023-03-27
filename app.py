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
access_key="AKIA5OVBSQSKYHJA3XUO"
secret_key="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"

s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
# Download the csv file
#csv_obj = bucket.Object('objets-trouves-restitution.csv').get()['Body'].read().decode('utf-8')
df = pd.read_csv(f's3://{bucket}/objets-trouves-restitution.csv')
#df = pd.read_csv(io.StringIO(csv_obj))

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
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)