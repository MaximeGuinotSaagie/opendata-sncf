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
        'flexwrap': 'wrap',
        'justifycontent': 'space-around',
    },
    'header': {
        'fontsize': '36px',
        'fontweight': 'bold',
        'textalign': 'center',
        'marginbottom': '50px',
    },
    'stat-item': {
        'display': 'flex',
        'textalign': 'center',
        'margin': '10px',
        'flexbasis': '250px',
        'border': '1px solid #ddd',
        'padding': '10px',
        'borderradius': '10px',
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
obj = s3.get_object(Bucket=bucket, Key="objets-trouves-restitution.csv")
df = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8')

# Compute the size of each group of stations
size = df.groupby('fields.gc_obo_gare_origine_r_name').size().reset_index(name='size')

# Merge the size information with the original DataFrame
df = pd.merge(df, size, on='fields.gc_obo_gare_origine_r_name')

# Define the app layout
app.layout = html.Div(
    style=styles["container"],
    children=[
        html.H1("Objets perdus en Gare", style=styles["header"]),
        html.Div(
            id="stats-container",
            className="stats-container",
            children=[
                html.Div(
                    id="total-records",
                    className="stat-item",
                    style=styles["stat-item"],
                    children=[
                        html.P("Nombre de lignes"),
                        html.Br(),
                        html.H4(f"{len(df)}"),
                        
                    ],
                ),
                html.Div(
                    id="total-stations",
                    className="stat-item",
                    style=styles["stat-item"],
                    children=[
                        html.P(f"{len(df['fields.gc_obo_gare_origine_r_name'].unique())}"),
                        html.Br(),
                        html.P("Nombre de gares"),
                    ],
                ),
                html.Div(
                    id="data-since",
                    className="stat-item",
                    style=styles["stat-item"],
                    children=[
                        html.P(f"Données depuis {df['record_timestamp'].min()[:10]}"),
                        html.Br(),
                        html.P(""),
                    ],
                ),
                html.Div(
                    id="max-objects-station",
                    className="stat-item",
                    style=styles["stat-item"],
                    children=[
                        html.P(f"{df.groupby('fields.gc_obo_gare_origine_r_name').size().idxmax()}"),
                        html.Br(),
                        html.P("Gare avec le plus grand nombre d'objets trouvés"),
                    ],
                ),
            ],
        ),
        html.Div(
            className="map-container",
            style=styles["map-container"],
            children=[
                dcc.Graph(id="map-graph", clickData={'points': [{'hovertext': df["fields.gc_obo_gare_origine_r_name"].iloc[0]}]}),
            ],
        ),
    ],
)

# Define the map graph
@app.callback(
    [Output("stats-container", "children"),
     Output("map-graph", "figure")],
    Input("map-graph", "clickData")
)
def update_stats_and_map(click_data):
    if click_data:
        selected_gare = click_data["points"][0]["hovertext"]
        selected_df = df[df["fields.gc_obo_gare_origine_r_name"] == selected_gare].copy()
        selected_df = df.copy()
        
        if selected_df.empty:
            # Set selected_gare to a default value or the first value of the column
            selected_gare = df["fields.gc_obo_gare_origine_r_name"].iloc[0]
            selected_df = df[df["fields.gc_obo_gare_origine_r_name"] == selected_gare].copy()
            selected_df = df.copy()
        # Update the statistics div
        stats = [
            html.Div(
                id="total-records",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.H4("Nombre de Lignes", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{len(selected_df)}"),
     
                ],
            ),
            html.Div(
                id="total-stations",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.P("Nombre de gares", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{len(selected_df['fields.gc_obo_gare_origine_r_name'].unique())}"),
                    
                ],
            ),
            html.Div(
                id="data-since",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.H4("Données depuis", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{selected_df['record_timestamp'].min()[:10]}"),
                ],
            ),
            html.Div(
                id="max-objects-station",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.H4("Top gare", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{selected_df.groupby('fields.gc_obo_gare_origine_r_name').size().idxmax()}"),
                    
                ],
            ),
        ]

        # Update the map figure
        fig = px.scatter_mapbox(
            selected_df,
            lat="latitude",
            lon="longitude",
            hover_name="fields.gc_obo_gare_origine_r_name",
            zoom=10,
            height=600,
            size="size",
            color="size",
            color_continuous_scale=bluered,
            mapbox_style="open-street-map",
        )
        fig.update_layout(transition_duration=500)
        fig.update_layout(coloraxis_colorbar=dict(title="Number of Objects"))
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        fig.update_layout(showlegend=False)

        return (stats, fig)
    else:
        selected_df = df.copy()
        # Update the statistics div
        stats = [
            html.Div(
                id="total-records",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.H4("Nombre de Lignes", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{len(selected_df)}"),
     
                ],
            ),
            html.Div(
                id="total-stations",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.P("Nombre de gares", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{len(selected_df['fields.gc_obo_gare_origine_r_name'].unique())}"),
                    
                ],
            ),
            html.Div(
                id="data-since",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.H4("Données depuis", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{selected_df['record_timestamp'].min()[:10]}"),
                ],
            ),
            html.Div(
                id="max-objects-station",
                className="stat-item",
                style=styles["stat-item"],
                children=[
                    html.H4("Top gare", style={"font-weight": "bold"}),
                    html.Br(),html.Br(),html.Br(),
                    html.P(f"{selected_df.groupby('fields.gc_obo_gare_origine_r_name').size().idxmax()}"),
                    
                ],
            ),
        ]

        # Update the map figure
        fig = px.scatter_mapbox(
            selected_df,
            lat="latitude",
            lon="longitude",
            hover_name="fields.gc_obo_gare_origine_r_name",
            zoom=10,
            height=600,
            size="size",
            color="size",
            color_continuous_scale=bluered,
            mapbox_style="open-street-map",
        )
        fig.update_layout(transition_duration=500)
        fig.update_layout(coloraxis_colorbar=dict(title="Number of Objects"))
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
        fig.update_layout(showlegend=False)

        return (stats, fig)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

