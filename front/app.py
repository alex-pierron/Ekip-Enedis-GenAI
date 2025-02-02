import os
import sys
import json
import dash
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify
from threading import Lock

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

import nltk
from nltk.corpus import stopwords

# Set up the project path and make sure modules are found
PROJECT_PATH = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_PATH))

# Import your project utilities and assets
from utils.load_and_clean_df import clean_data, fetch_table_as_df
from utils.import_export import import_uploaded_pdf_to_s3, export_table_to_excel
from utils.dash_filtering import create_accordion_item, filter_df, summary_filter
from utils.dash_figures import (
    create_combined_pie_bar_chart,
    create_sentiment_trend_area,
    create_geographic_distribution_map,
    create_wordcloud
)
import assets.css.styles as myCSS

############################# CONFIG #############################

DASH_APP_URL = '127.0.0.1'
DASH_APP_PORT = 8050

# Available grid items and dashboard configuration
DATA_GRID = [
    ['combined-pie-chart', 'sentiment-trend-area'],
    ['word-cloud', 'geographic-distribution'],
]

DEBUG_MODE = True

##################################################################

# Load data and define parameters regarding the given grid
grid_items = [item for sublist in DATA_GRID for item in sublist]

# GeoJSON for geographic distribution if needed
if 'geographic-distribution' in grid_items:
    with open(os.path.join(PROJECT_PATH, 'assets/geojson/france-departements.geojson'), 'r') as geojson_file:
        FRANCE_GEOJSON = json.load(geojson_file)
else:
    FRANCE_GEOJSON = None

# NLTK stop words if word cloud is needed
if 'word-cloud' in grid_items:
    nltk.download('stopwords')
    FRENCH_STOP_WORDS = set(stopwords.words('french'))
else:
    FRENCH_STOP_WORDS = None

######################
## I- LOAD CSV DATA ##
######################

# Fetch data from the database
df = fetch_table_as_df(
    host=os.getenv("RDS_HOST_READ"),
    user=os.getenv("RDS_USER"),
    password=os.getenv("RDS_PASSWORD"),
    db_name=os.getenv("RDS_DB"),
    table_name='media_enedis_bis'# os.getenv("RDS_TABLE")
)

# Clean the data (e.g., standardize column names, modify values)
df = clean_data(df)

##########################
## II- DASH APPLICATION ##
##########################
# Initialize Flask and Dash app
server = Flask(__name__)
dash_app = Dash(__name__, 
                server=server, 
                url_base_pathname='/',
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.FLATLY, 'https://fonts.googleapis.com/css2?family=Aldrich&display=swap']
)

dash_app.title = 'Dashboard | Enedis'
dash_app._favicon = "img/enedis-favicon.ico"

# Thread-safe state for PDF import status
pdf_import_status = {"imported": 0}  # 0: Default, 1: Importing, 2: Import Done
pdf_import_lock = Lock()

# Route to update PDF import status
@server.route('/update-pdf-status', methods=['POST'])
def update_pdf_status():
    with pdf_import_lock:
        pdf_import_status["imported"] = 2
    return jsonify({"status": "success"})

# Callback to reset PDF import status on page load
@dash_app.callback(
    Output('pdf-import-store', 'data', allow_duplicate=True),
    Input('initial-pdf-import-status', 'data'),
    prevent_initial_call=True
)
def reset_pdf_import_status_on_load(initial_data):
    return initial_data

##############################
## II.a) Application Layout ##
##############################

# Reset PDF import status
def reset_pdf_import_status():
    with pdf_import_lock:
        pdf_import_status["imported"] = 0  # Reset to default state

# Generate the layout grid dynamically based on configuration
def generate_grid_layout(grid):
    grid_layout = []
    for row in grid:
        cols = []
        for graph_id in row:
            cols.append(dbc.Col(dcc.Graph(id=graph_id, style=myCSS.container), width=6))
        grid_layout.append(dbc.Row(cols, className='mb-4'))
    return grid_layout

# Define the layout of the app using Dash components
dash_app.layout = dbc.Container([

    # Header row with logo and title
    dbc.Row([
        dbc.Col(html.Img(src='assets/img/enedis-logo.svg', height='60px'),
                width='auto', className='d-flex align-items-center justify-content-start'),
        dbc.Col(html.H1("Analyse des reportings Enedis", className='text-center mb-5 mt-3'),
                style=myCSS.title, width=True, className='d-flex justify-content-center'),
        dbc.Col(html.Img(src='assets/img/enedis-eolienne.svg', height='180px'),
                width='auto', className='d-flex align-items-center justify-content-start'),
        dbc.Col(html.Img(src='assets/img/hackathon-GenAI.png', height='60px'),
                width='auto', className='d-flex align-items-center justify-content-start')
    ], align='center', className='mb-4'),

    # PDF import button
    dbc.Row([
        dbc.Col(dcc.Upload(
            id='upload-pdf',
            children=html.Button('Importer PDF', id='upload-button', className='btn btn-primary', style={'margin-top': '-100px'}),
            multiple=True,
        ), width=12, className='d-flex justify-content-center'),
    ], className='mb-4'),

    # PDF import status store and interval for polling
    dcc.Store(id='pdf-import-store', data={'imported': 0}),
    dcc.Store(id='initial-pdf-import-status', data={'imported': 0}),
    dcc.Interval(id='poll-interval', interval=2000, n_intervals=0),

    # Search Bar for keywords
    dbc.Row([
        dbc.Col(dcc.Input(
            id='keywords-search',
            type='text',
            placeholder="💡 Rechercher des mots-clés...",
            debounce=True,
            className='form-control shadow-sm',
            style=myCSS.keywords_search
        ), width=6, className='d-flex justify-content-start') 
    ], className='mb-4'),

    # Filters Section with various filtering options (Theme, Sentiment, Territory, etc.)
    dbc.Accordion([
        create_accordion_item(df, title='Thème', id='theme'),
        create_accordion_item(df, title='Sentiment', id='tonalite', ordered_values=myCSS.pie_bar_chart_colors_keys),
        create_accordion_item(df, title='Territoire', id='territory'),
        create_accordion_item(df, title='Média', id='media'),
        dbc.AccordionItem([
            html.Label("🕒 Sélectionner une période de temps", className='fw-bold text-secondary'),
            dcc.DatePickerRange(
                id='date-picker',
                start_date=df['Date'].min(),
                end_date=df['Date'].max(),
                display_format='DD/MM/YYYY',
                className='form-control',
                style=myCSS.date_picker_range
            ),
        ], title="📅 Filtrer par Date", id='date-title')
    ], className='mb-4 shadow-sm'),

    # Data Visualizations: Charts and other visual elements
    *generate_grid_layout(DATA_GRID),

    # Data Table and Export button
    html.Div([
        html.Div([
            html.Button('Exporter Excel', id='export-button', n_clicks=0, className='btn btn-primary')
        ], style={'padding': '10px'}),
        dcc.Download(id="download-dataframe-xlsx"),
        dash_table.DataTable(
            id='data-table',
            columns=[{"name": col, "id": col} for col in df.columns],
            page_size=myCSS.data_table['page_size'],
            style_table=myCSS.data_table['style_table'],
            style_header=myCSS.data_table['style_header'],
            style_cell=myCSS.data_table['style_cell'],
            row_selectable=False,
            cell_selectable=False,
            style_data_conditional=myCSS.data_table['style_data_conditional'],
        )
    ], style=myCSS.container)
], fluid=True, style=myCSS.global_layout)

#reset_pdf_import_status()
#print(pdf_import_status["imported"])

############################################
## II.b) Callback to Update Visualization ##
############################################

# Dynamically generate callback outputs for visualizations
callback_outputs = []
for row in DATA_GRID:
    for graph_id in row:
        callback_outputs.append(Output(graph_id, 'figure'))
callback_outputs.extend([
    Output('data-table', 'data'),
    Output('theme-title', 'title'),
    Output('tonalite-title', 'title'),
    Output('territory-title', 'title'),
    Output('media-title', 'title'),
    Output('date-title', 'title')
])
callback_inputs = [
    Input('theme-dropdown', 'value'),
    Input('tonalite-dropdown', 'value'),
    Input('territory-dropdown', 'value'),
    Input('media-dropdown', 'value'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date'),
    Input('keywords-search', 'value')
]

# Callback function to update the visualizations based on filter inputs
@dash_app.callback(callback_outputs, callback_inputs)
def update_visualizations(selected_themes, selected_tonalites, selected_territories, selected_medias, start_date, end_date, keywords):
    filtered_df = filter_df(df, (selected_themes, selected_tonalites, selected_territories, selected_medias, start_date, end_date, keywords)).sort_values(by='Date')

    # Filters summary
    theme_summary = summary_filter('Thème', selected_themes)
    tonalite_summary = summary_filter('Sentiment', selected_tonalites)
    territory_summary = summary_filter('Territoire', selected_territories)
    media_summary = summary_filter('Média', selected_medias)
    
    start_date_str = pd.to_datetime(start_date).strftime('%d/%m/%Y')
    end_date_str = pd.to_datetime(end_date).strftime('%d/%m/%Y')
    date_summary = f"📅 Filtrer par Date: {start_date_str} - {end_date_str}" if start_date and end_date else "📅 Filtrer par Date"

    # Table data
    formated_date_df = filtered_df.reset_index().sort_values(by='Date', ascending=False)
    formated_date_df['Date'] = formated_date_df['Date'].dt.strftime('%d/%m/%Y')
    table_data = formated_date_df.to_dict('records')

    # Generate figures for the grid items 
    figures = {}

    if 'combined-pie-chart' in grid_items:
        combined_pie_chart = create_combined_pie_bar_chart(filtered_df, myCSS.pie_bar_chart)
        figures['combined-pie-chart'] = combined_pie_chart

    if 'geographic-distribution' in [item for sublist in DATA_GRID for item in sublist]:
        geographic_distribution = create_geographic_distribution_map(filtered_df, style=myCSS.geographic_distribution, geojson=FRANCE_GEOJSON)
        figures['geographic-distribution'] = geographic_distribution

    if 'sentiment-trend-area' in grid_items:
        sentiment_trend_area = create_sentiment_trend_area(filtered_df, style=myCSS.sentiment_trend)
        figures['sentiment-trend-area'] = sentiment_trend_area

    if 'word-cloud' in grid_items:
        text = ' '.join(filtered_df['Sujet'].dropna().tolist() + filtered_df['Article'].dropna().tolist())
        wordcloud = create_wordcloud(text, style=myCSS.wordcloud, stopwords=FRENCH_STOP_WORDS)
        figures['word-cloud'] = wordcloud

    # Prepare return values in the correct order
    values_to_return = [figures.get(graph_id, {}) for graph_id in [item for sublist in DATA_GRID for item in sublist]]
    values_to_return.extend([table_data, theme_summary, tonalite_summary, territory_summary, media_summary, date_summary])
    return values_to_return

########################################################
## II.c) Callbacks for Imports (PDF) / Export (Excel) ##
########################################################

# Callback for Excel export
@dash_app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("export-button", "n_clicks"),
    Input('data-table', 'data'),
    prevent_initial_call=True
)
def handle_xlsx_export(n_clicks, table_data):
    return export_table_to_excel(n_clicks, table_data)

# Callback to handle PDF import status
@dash_app.callback(
    Output('pdf-import-store', 'data'),
    [Input('poll-interval', 'n_intervals'),
     Input('upload-pdf', 'contents'),
     Input('upload-pdf', 'filename')],
    State('pdf-import-store', 'data'),
    prevent_initial_call=True
)
def handle_pdf_store_update(n_intervals, contents, filenames, store_data):
    ctx = dash.callback_context

    # Check what triggered the callback
    if not ctx.triggered:
        return dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Polling trigger
    if triggered_id == 'poll-interval':
        with pdf_import_lock:
            store_data['imported'] = pdf_import_status["imported"]

    # PDF upload trigger
    elif triggered_id == 'upload-pdf':
        if contents and filenames:
            success_str = import_uploaded_pdf_to_s3(contents, filenames)
            with pdf_import_lock:
                pdf_import_status["imported"] = 1
            store_data['imported'] = 1

    return store_data


# Callback to update the upload button's appearance based on PDF import status
@dash_app.callback(
    [Output('upload-button', 'className'),
     Output('upload-button', 'children')],
    Input('pdf-import-store', 'data')
)
def update_upload_button_style_and_text(store_data):
    if store_data and store_data.get('imported') == 1:
        return 'btn btn-primary', 'Import en cours...'
    elif store_data and store_data.get('imported') == 2:
        return 'btn btn-success', 'Import terminé !'
    else:
        return 'btn btn-primary', 'Importer PDF'

########################
## II.e) Run dash app ##
########################

# Start the Dash app
if __name__ == '__main__':
    dash_app.run(debug=DEBUG_MODE, host=DASH_APP_URL, port=DASH_APP_PORT)
