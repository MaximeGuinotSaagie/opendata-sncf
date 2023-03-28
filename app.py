import dash
from dash import dcc
from dash import html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
import boto3
import io
import os

# Define the styles inline
styles = {
    'container': {
        'margin': 'auto',
        'max-width': '800px',
        'font-family': 'Arial, sans-serif',
    },
    'header': {
        'font-size': '36px',
        'font-weight': 'bold',
        'text-align': 'center',
        'margin-bottom': '50px',
    },
    'stat-item': {
        'text-align': 'center',
        'margin': '0 50px',
        'display': 'inline-block',
        'width': '200px',
        'border': '1px solid #ddd',
        'padding': '10px',
        'border-radius': '10px',
    },
    'map-container': {
        'height': '600px',
    },
}

# Create the Dash app
app = dash.Dash(__name__)

# Connect to S3 bucket
bucket = "tnb-cust11"
access_key=os.environ["AWS_ACCESS_KEY_ID"]
secret_key=os.environ["AWS_SECRET_ACCESS_KEY"]

s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)

# Download the csv file
df = pd.read_csv(f's3://{bucket}/objets-trouves-restitution.csv')

# Compute the size of each group of stations
size = df.groupby('fields.gc_obo_gare_origine_r_name').size().reset_index(name='size')

# Merge the size information with the original DataFrame
df = pd.merge(df, size, on='fields.gc_obo_gare_origine_r_name')

# Define the app layout
app.layout = html.Div(
    className="container",
    children=[
        html.H1("Lost and Found Records"),
        html.Div(
            className="stats-container",
            children=[
                html.Div(
                    className="stat-item",
                    children=[
                        html.P(f"{len(df)}"),
                        html.P("Nombre de lignes"),
                    ],
                ),
                html.Div(
                    className="stat-item",
                    children=[
                        html.P(f"{len(df['fields.gc_obo_gare_origine_r_name'].unique())}"),
                        html.P("Nombre de gares"),
                    ],
                ),
                html.Div(
                    className="stat-item",
                    children=[
                        html.P(f"Données depuis {df['record_timestamp'].min():%d-%m-%Y}"),
                        html.P(""),
                    ],
                ),
                html.Div(
                    className="stat-item",
                    children=[
                        html.P(f"{df.groupby('fields.gc_obo_gare_origine_r_name').size().idxmax()}"),
                        html.P("Gare avec le plus grand nombre d'objets trouvés"),
                    ],
                ),
            ],
        ),
        html.Div(
            className="map-container",
            children=[
                dcc.Graph(id="map-graph"),
            ],
        ),
    ],
)

# Define the map graph
@app.callback(
    Output("map-graph", "figure"),
    Input("map-graph", "clickData"),
)
def update_map(click_data):
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="fields.gc_obo_gare_origine_r_name",
        zoom=3,
        height=600,
        size="size",
        color="size",
        color_continuous_scale=px.colors.sequential.Blues_r,
        mapbox_style="open-street-map",
    )
    fig.update_layout(transition_duration=500)
    fig.update_layout(coloraxis_colorbar=dict(title="Number of Objects"))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    fig.update_layout(showlegend=False)
    return fig


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
