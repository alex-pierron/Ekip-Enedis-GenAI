import os
import io
import sys
import json
import base64
import pandas as pd
from pathlib import Path

import dash
from dash.exceptions import PreventUpdate
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import nltk
from nltk.corpus import stopwords

PROJECT_PATH = Path(__file__).parent.absolute()
sys.path.append(PROJECT_PATH)

from utils.load_and_clean_df import (
    load_data,
    clean_data
)
from utils.import_export import (
    import_uploaded_pdf,
    export_table_to_excel
)
from utils.dash_filtering import (
    create_accordion_item, 
    filter_df, 
    summary_filter
)
from utils.dash_figures import (
    create_combined_pie_chart,
    create_sentiment_trend_area,
    create_geographic_distribution_map,
    create_wordcloud
)
import assets.css.styles as myCSS

############################# CONFIG #############################

DASH_APP_URL = 'localhost'
DASH_APP_PORT = 8050

# availables : ['combined-pie-chart', 'geographic-distribution', 'sentiment-trend-area', 'word-cloud']
DATA_GRID = [
    ['combined-pie-chart', 'sentiment-trend-area'],
    ['word-cloud', 'geographic-distribution'],
]

DEBUG_MODE = True

##################################################################


# Load data and define parameters regarding the given grid
grid_items = [item for sublist in DATA_GRID for item in sublist]

if 'geographic-distribution' in grid_items:
    with open(os.path.join(PROJECT_PATH, 'assets/geojson/france-departements.geojson'), 'r') as geojson_file:
        FRANCE_GEOJSON = json.load(geojson_file)
else:
    FRANCE_GEOJSON=None

if 'word-cloud' in grid_items:
    nltk.download('stopwords')
    FRENCH_STOP_WORDS = set(stopwords.words('french'))
else:
    FRENCH_STOP_WORDS=None



######################
## I- LOAD CSV DATA ##
######################

df = load_data(data_folder=os.path.join(PROJECT_PATH, 'data'))
df = clean_data(df)



##########################
## II- DASH APPLICATION ##
##########################

dash_app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, 'https://fonts.googleapis.com/css2?family=Aldrich&display=swap'])

dash_app.title = 'Dashboard | Enedis'
dash_app._favicon = "img/enedis-favicon.ico"

##############################
## II.a) application Layout ##
##############################

def generate_grid_layout(grid):
    grid_layout = []
    for row in grid:
        cols = []
        for graph_id in row:
            cols.append(dbc.Col(dcc.Graph(id=graph_id, style=myCSS.container), width=6))
        grid_layout.append(dbc.Row(cols, className='mb-4'))
    return grid_layout

dash_app.layout = dbc.Container([

    # Header
    dbc.Row([
        dbc.Col(html.Img(src='assets/img/enedis-logo.svg', height='60px'), width='auto', className='d-flex align-items-center justify-content-start'),
        dbc.Col(html.H1("Analyse des reportings Enedis", className='text-center mb-5 mt-3'), style=myCSS.title, width=True, className='d-flex justify-content-center'),
        dbc.Col(html.Img(src='assets/img/enedis-eolienne.svg', height='180px'), width='auto', className='d-flex align-items-center justify-content-start'),
        dbc.Col(html.Img(src='assets/img/hackathon-GenAI.png', height='60px'), width='auto', className='d-flex align-items-center justify-content-start')
    ], align='center', className='mb-4'),

    # Import Button
    dbc.Row([
        dbc.Col(dcc.Upload(
            id='upload-pdf',
            children=html.Button('Importer PDF', className='btn btn-primary'),
            multiple=True,
        ), width='auto', className='d-flex align-items-center justify-content-start'),
    ], align='center', className='mb-4'),

    # Search Bar
    dbc.Row([
        dbc.Col(dcc.Input(
            id='keywords-search',
            type='text',
            placeholder="💡 Rechercher des mots-clés...",
            debounce=True,
            className='form-control shadow-sm',
            style=myCSS.keywords_search
        ), width=6)
    ], justify='center', className='mb-4'),

    # Filters Section
    dbc.Accordion([
        create_accordion_item(df, title='Thème', id='theme'),
        create_accordion_item(df, title='Qualité du retour', id='tonalite', ordered_values=myCSS.pie_chart_colors_keys),
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

    # Data Visualization
    *generate_grid_layout(DATA_GRID),

    # Data Table
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

############################################
## II.b) callback to update visualization ##
############################################

# dynamically generate callback outputs based on the grid
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
@dash_app.callback(callback_outputs, callback_inputs)


def update_visualizations(selected_themes, selected_tonalites, selected_territories, selected_medias, start_date, end_date, keywords):
    
    filtered_df = filter_df(df, (selected_themes, selected_tonalites, selected_territories, selected_medias, start_date, end_date, keywords)).sort_values(by='Date')

    # Filters summary
    theme_summary = summary_filter('Thème', selected_themes)
    tonalite_summary = summary_filter('Qualité du retour', selected_tonalites)
    territory_summary = summary_filter('Territoire', selected_territories)
    media_summary = summary_filter('Média', selected_medias)
    
    start_date_str = pd.to_datetime(start_date).strftime('%d/%m/%Y')
    end_date_str = pd.to_datetime(end_date).strftime('%d/%m/%Y')
    date_summary = f"📅 Filtrer par Date: {start_date_str} - {end_date_str}" if start_date and end_date else "📅 Filtrer par Date"

    # Table data
    formated_date_df = filtered_df.reset_index().sort_values(by='Date', ascending=False)
    formated_date_df['Date'] = formated_date_df['Date'].dt.strftime('%d/%m/%Y')
    table_data = formated_date_df.to_dict('records')

    # Generate figures regarding the given grid 
    figures = {}

    if 'combined-pie-chart' in grid_items:
        combined_pie_chart = create_combined_pie_chart(filtered_df, myCSS.pie_chart, category_order=myCSS.pie_chart_colors_keys)
        figures['combined-pie-chart'] = combined_pie_chart

    if 'geographic-distribution' in [item for sublist in DATA_GRID for item in sublist]:
        geographic_distribution = create_geographic_distribution_map(filtered_df, style=myCSS.geographic_distribution, geojson=FRANCE_GEOJSON)
        figures['geographic-distribution'] = geographic_distribution

    if 'sentiment-trend-area' in grid_items:
        sentiment_trend_area = create_sentiment_trend_area(filtered_df, style=myCSS.sentiment_trend)
        figures['sentiment-trend-area'] = sentiment_trend_area

    if 'word-cloud' in grid_items:
        text = ' '.join(filtered_df['Sujet'].dropna().tolist() + filtered_df['Articles'].dropna().tolist())
        wordcloud = create_wordcloud(text, style=myCSS.wordcloud, stopwords=FRENCH_STOP_WORDS)
        figures['word-cloud'] = wordcloud

    # Prepare the return values in the correct order
    values_to_return = [figures.get(graph_id, {}) for graph_id in [item for sublist in DATA_GRID for item in sublist]]
    values_to_return.extend([table_data, theme_summary, tonalite_summary, territory_summary, media_summary, date_summary])

    return values_to_return


#######################################################
## II.c) callbacks for imports (pdf) / export (xlsx) ##
#######################################################

@dash_app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("export-button", "n_clicks"),
    Input('data-table', 'data'),
    prevent_initial_call=True
)
def handle_xlsx_export(n_clicks, table_data):
    return export_table_to_excel(n_clicks, table_data)


@dash_app.callback(
    Output('upload-pdf', 'children'),
    Input('upload-pdf', 'contents'),
    Input('upload-pdf', 'filename'),
    prevent_initial_call=True
)
def handle_pdf_import(contents, filenames):
    return import_uploaded_pdf(contents, filenames)


###################
## II.d) run app ##
###################

if __name__ == '__main__':
    dash_app.run(debug=DEBUG_MODE, host=DASH_APP_URL, port=DASH_APP_PORT)
