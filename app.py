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
df = pd.read_csv(f's3://{bucket}/objets-trouves-restitution.csv')


# Compute the size of each group of stations
size = df.groupby('fields.gc_obo_gare_origine_r_name').size().reset_index(name='size')

# Merge the size information with the original DataFrame
df = pd.merge(df, size, on='fields.gc_obo_gare_origine_r_name')


# Create the Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div(
    className="container",
    children=[
        html.Link(
            rel='stylesheet',
            href='./style.css'
        ),
        html.H1("Lost and Found Records"),
        html.Div(
            className="stats-container",
            children=[
                html.H2("Statistics"),
                html.Div(
                    className="stat-item",
                    children=[
                        html.P(f"{len(df)}"),
                        html.P("Total Records"),
                    ],
                ),
                html.Div(
                    className="stat-item",
                    children=[
                        html.P(f"{len(df['fields.gc_obo_gare_origine_r_name'].unique())}"),
                        html.P("Total Unique Stations"),
                    ],
                ),
                html.Div(
                    className="stat-item",
                    children=[
                        html.P(f"{len(df['fields.gc_obo_type_c'].unique())}"),
                        html.P("Total Unique Types"),
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
