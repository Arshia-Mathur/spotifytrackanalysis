#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 20:24:02 2024

@author: arshia.mathur
"""

import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc


# Load and prepare your data
file_path = '/Users/arshia.mathur/Desktop/spotifydata2023.csv'
spotify_data = pd.read_csv(file_path, encoding='utf-8-sig')
spotify_data['streams'] = pd.to_numeric(spotify_data['streams'], errors='coerce').dropna().astype(int)

# Prepare aggregated data for the first graph
print(spotify_data.columns)
aggregated_data = spotify_data.groupby(['key', 'mode']).agg(
    total_streams=('streams', 'sum'),
    song_count=('track_name', 'count')).reset_index()

# Filter data for the second graph
lower_limit = spotify_data['streams'].quantile(0.1)
filtered_data = spotify_data[spotify_data['streams'] >= lower_limit]

# Categorizing 'streams' into popularity segments by quartile
stream_bins = [0, spotify_data['streams'].quantile(0.33), spotify_data['streams'].quantile(0.66), spotify_data['streams'].max()]
stream_labels = ['Least-Streamed', 'Middle-Streamed', 'Top-Streamed']
spotify_data['stream_category'] = pd.cut(spotify_data['streams'], bins=stream_bins, labels=stream_labels, include_lowest=True)


genres = ['danceability_%', 'acousticness_%', 'instrumentalness_%', 'liveness_%', 'speechiness_%', 'energy_%', 'valence_%']


# Initialize the Dash app with Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Define the app layout using Bootstrap's grid system
app.layout = dbc.Container([
    html.H1("Spotify Track Analysis", className='text-center text-primary mb-4'),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='key-dropdown',
                options=[{'label': key, 'value': key} for key in aggregated_data['key'].unique()],
                value=aggregated_data['key'].unique().tolist(),
                multi=True
            ),
            dcc.Checklist(
                id='mode-checklist',
                options=[{'label': mode, 'value': mode} for mode in aggregated_data['mode'].unique()],
                value=aggregated_data['mode'].unique().tolist(),
                labelStyle={'display': 'inline-block'}
            ),
        ], width=12),
    ]),
    
    # Dropdown for second chart
    dcc.Dropdown(
    id='metric-dropdown',
    options=[
        {'label': 'Streams', 'value': 'streams'},
        {'label': 'Spotify Playlist Numbers', 'value': 'in_spotify_playlists'}
    ],
    value='streams'  
    ),

    # Second graph
    dbc.Row([
        dbc.Col(dcc.Graph(id='song-distribution-chart', style={'height': '300px'}), width=6),
        dbc.Col(dcc.Graph(id='bubble-chart', style={'height': '300px'}), width=6),
    ]),

    dbc.Row([
        dbc.Col([
            html.Label("Select metrics to display over time:"),
            dcc.Checklist(
                id='time-series-metrics',
                options=[
                    {'label': 'Average Energy', 'value': 'energy'},
                    {'label': 'Average BPM', 'value': 'bpm'}
                ],
                value=['energy', 'bpm'],
                style={'margin': '10px'}
            ),
            dcc.Graph(id='time-series-plot', style={'height': '300px'}),
        ], width=6),
        dbc.Col([
            html.Label("Select metrics for streams correlation:"),
            dcc.Checklist(
                id='streams-correlation-metrics',
                options=[
                    {'label': 'Energy vs. Streams', 'value': 'energy_streams'},
                    {'label': 'BPM vs. Streams', 'value': 'bpm_streams'}
                ],
                value=['energy_streams', 'bpm_streams'],
                style={'margin': '10px'}
            ),
            dcc.Graph(id='streams-correlation-plot', style={'height': '300px'}),
        ], width=6),
    ]),
    
    # final graph
    html.H4('Interactive Scatter Plot'),
    dcc.Graph(id="scatter-plot"),
    html.P("Select Genre:"),
    dcc.Dropdown(
        id='genre-dropdown',
        options=[{'label': genre, 'value': genre} for genre in genres],
        value='danceability_%'  # Default value
    ),
    html.P("Select Stream Category:"),
    dcc.Dropdown(
        id='stream-category-dropdown',
        options=[{'label': label, 'value': label} for label in stream_labels],
        value=stream_labels[0] if stream_labels else None  # Default value
    ),
], fluid=True)

# Callback function to update the chart based on user selections
@app.callback(
    Output('song-distribution-chart', 'figure'),  # Output is the figure of the graph component
    [Input('key-dropdown', 'value'),  # Input from dropdown selection
     Input('mode-checklist', 'value')]  # Input from checklist selection
)
def update_chart(selected_keys, selected_modes):
    # Filter the aggregated data based on selected keys and modes
    filtered_data = aggregated_data[
        (aggregated_data['key'].isin(selected_keys)) &
        (aggregated_data['mode'].isin(selected_modes))
        ]
    # Create a bar chart using Plotly Express with the filtered data
    fig = px.bar(
        filtered_data,
        x='key',
        y='total_streams',
        color='mode',
        text='song_count',
        title='Distribution of Songs by Key and Mode with Streaming Numbers',
        labels={'total_streams': 'Total Streaming Numbers', 'song_count': 'Song Count'},
    )
    # Adjust figure layout to display bars side by side and other stylistic elements
    fig.update_layout(
        xaxis_title='Musical Key',
        yaxis_title='Total Streaming Numbers',
        legend_title='Mode',
        barmode='group',  # Ensure bars for different modes are side by side
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    return fig  # Return the figure to be rendered in the graph component


# Callback to update the bubble chart
@app.callback(
    Output('bubble-chart', 'figure'),
    [Input('key-dropdown', 'value')],
    [Input('metric-dropdown', 'value')]
    
)

def update_bubble_chart(selected_keys, selected_metric):  # Add selected_metric parameter
    # Modify the bubble chart creation based on selected_metric
    fig = px.scatter(
        filtered_data, x='danceability_%', y=selected_metric,  # Update this line
        size='energy_%', color='valence_%',
        hover_name='track_name', size_max=60,
        color_continuous_scale=px.colors.sequential.Viridis,
        opacity=0.7)

    # Customize the layout
    y_axis_title = 'Streams' if selected_metric == 'streams' else 'Playlist Numbers'  # Update this line
    fig.update_layout(
        title='Bubble Chart of Song Attributes and ' + y_axis_title,  # Update this line
        xaxis=dict(title='Danceability (%)'),
        yaxis=dict(title=y_axis_title),  # Update this line
        coloraxis_colorbar=dict(title='Valence (%)')
    )

    return fig

# Callback to third graph
@app.callback(
    Output('time-series-plot', 'figure'),
    [Input('time-series-metrics', 'value')]
)
def update_time_series(selected_metrics):
    '''
    This function updates the time series plot based on the selected metrics of energy and bpm.
    :param: selected_metrics (energy or bpm)
    :return: a plot display the average energy and/or bpm over time (based on what the user selects)
    '''
    fig = go.Figure()
    if 'energy' in selected_metrics:
        fig.add_trace(go.Scatter(
            x=spotify_data.groupby('released_year')['released_year'].first(),
            y=spotify_data.groupby('released_year')['energy_%'].mean(),
            mode='lines+markers',
            name='Average Energy'
        ))
    if 'bpm' in selected_metrics:
        fig.add_trace(go.Scatter(
            x=spotify_data.groupby('released_year')['released_year'].first(),
            y=spotify_data.groupby('released_year')['bpm'].mean(),
            mode='lines+markers',
            name='Average BPM'
        ))
    fig.update_layout(title='Average Energy and BPM Over Time', xaxis_title='Year', yaxis_title='Value')
    return fig


@app.callback(
    Output('streams-correlation-plot', 'figure'),
    [Input('streams-correlation-metrics', 'value')]
)
def update_streams_correlation(selected_metrics):
    '''
    This function creates a scatter plot based on the number of streams vs the selected metrics of energy and/or bpm.
    :param selected metrics of energy and/or bpm
    :return: scatter plot displaying the respective relationships
    '''
    fig = go.Figure()
    if 'energy_streams' in selected_metrics:
        fig.add_trace(go.Scatter(
            x=spotify_data['energy_%'],
            y=spotify_data['streams'],
            mode='markers',
            name='Energy vs. Streams',
            marker=dict(color='blue', opacity=0.5)
        ))
    if 'bpm_streams' in selected_metrics:
        fig.add_trace(go.Scatter(
            x=spotify_data['bpm'],
            y=spotify_data['streams'],
            mode='markers',
            name='BPM vs. Streams',
            marker=dict(color='red', opacity=0.5)
        ))
    fig.update_layout(title='Correlation Between Streams and Music Metrics', xaxis_title='Metric Value',
                      yaxis_title='Streams')
    return fig

# Callback for last graph
@app.callback(
    Output("scatter-plot", "figure"), 
    [Input("genre-dropdown", "value"), Input('stream-category-dropdown', 'value')])

def update_scatter_plot(selected_genre, selected_stream_category):
    if selected_stream_category:
        filtered_df = spotify_data[spotify_data['stream_category'] == selected_stream_category]
    else:
        filtered_df = spotify_data
    fig = px.scatter(
        filtered_df, x="released_year", y=selected_genre, 
        color='stream_category', 
        hover_data=genres + ['stream_category'])

    # Defining more readable labels
    readable_labels = {
        'danceability_%': 'Percent Danceability',
        'acousticness_%': 'Percent Acousticness',
        'instrumentalness_%': 'Percent Instrumentalness',
        'liveness_%': 'Percent Liveness',
        'speechiness_%': 'Percent Speechiness',
        'energy_%': 'Percent Energy',
        'valence_%': 'Percent Valence'
    }

    # Update the y-axis title based on selected genre
    y_axis_label = readable_labels.get(selected_genre, selected_genre)

    fig.update_yaxes(title=y_axis_label)
    fig.update_xaxes(title="Released Year")

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

