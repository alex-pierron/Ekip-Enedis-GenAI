import os
import sys
import json
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from pathlib import Path

import nltk
from nltk.corpus import stopwords

PROJECT_PATH = Path(__file__).parent.absolute()
sys.path.append(PROJECT_PATH)

from utils.load_and_clean_df import load_data, clean_data
from utils.dash.search_filtering import create_accordion_item, filter_df, summary_filter
from utils.dash.pie_charts import create_combined_pie_chart
from utils.dash.articles_time_series import create_legend_trace, get_timeseries_background_shapes
from utils.dash.wordcloud import generate_wordcloud
from utils.dash.sentiment_trend import create_sentiment_trend_chart
from utils.dash.geographic_distribution import create_geographic_distribution_map

import assets.css.styles as myCSS

############################# CONFIG #############################

DASH_APP_URL = 'localhost'
DASH_APP_PORT = 8050

# availables : ['tone-pie-chart', 'combined-pie-chart', 'articles-time-series', 'sentiment-trend', 'word-cloud', 'geographic-distribution']
DATA_GRID = [
    ['combined-pie-chart', 'sentiment-trend'],
    ['word-cloud', 'geographic-distribution'],
]

##################################################################




##################
## I- LOAD DATA ##
##################

# load csv
df = load_data(data_folder=os.path.join(PROJECT_PATH, 'data'))
df = clean_data(df)

# load necessary data for the figures
grid_items = [item for sublist in DATA_GRID for item in sublist]

if 'word-cloud' in grid_items:
    nltk.download('stopwords')
    FRENCH_STOP_WORDS = set(stopwords.words('french'))
else:
    FRENCH_STOP_WORDS=None

if 'geographic-distribution' in grid_items:
    with open('assets/geojson/france-departements.geojson', 'r') as f:
        FRANCE_GEOJSON = json.load(f)
else:
    FRANCE_GEOJSON=None

TIME_SERIES_THRESHOLD = 0.1 if 'articles-time-series' in grid_items else None

##########################
## II- DASH APPLICATION ##
##########################
dash_app = Dash(__name__, external_stylesheets=[
    dbc.themes.FLATLY,
    'https://fonts.googleapis.com/css2?family=Aldrich&display=swap',
])
dash_app.title = 'Dashboard | Enedis'
dash_app._favicon = ("img/enedis-favicon.ico")

##############################
## II.a) application Layout ##
##############################

def generate_layout(grid):
    layout = []
    for row in grid:
        cols = []
        for graph_id in row:
            cols.append(dbc.Col(dcc.Graph(id=graph_id, style=myCSS.container), width=6))
        layout.append(dbc.Row(cols, className='mb-4'))
    return layout

dash_app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.Img(src='assets/img/enedis-logo.svg', height='60px'), width='auto', className='d-flex align-items-center justify-content-start'),
        dbc.Col(html.H1("Analyse des reportings Enedis", className='text-center mb-5 mt-3'), style=myCSS.title, width=True, className='d-flex justify-content-center'),
        dbc.Col(html.Img(src='assets/img/enedis-eolienne.svg', height='180px'), width='auto', className='d-flex align-items-center justify-content-start'),
        dbc.Col(html.Img(src='assets/img/hackathon-genIA-logo.png', height='60px'), width='auto', className='d-flex align-items-center justify-content-start')
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
    *generate_layout(DATA_GRID),

    html.Div([
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
], fluid=True)

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

@dash_app.callback(
    callback_outputs,
    [
        Input('theme-dropdown', 'value'),
        Input('tonalite-dropdown', 'value'),
        Input('territory-dropdown', 'value'),
        Input('media-dropdown', 'value'),
        Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date'),
        Input('keywords-search', 'value')
    ]
)
def update_visualizations(selected_themes, selected_tonalites, selected_territories, selected_medias, start_date, end_date, keywords):
    
    filtered_df = filter_df(df, (selected_themes, selected_tonalites, selected_territories, selected_medias, start_date, end_date, keywords)).sort_values(by='Date')

    # filters summary
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

    # Initialize a dictionary to store all figures
    figures = {}

    # Generate figures only for graphs present in DATA_GRID
    if 'tone-pie-chart' in grid_items:
        pie_chart = px.pie(
            filtered_df,
            names='Qualité du retour',
            title="📊 Répartition des tonalités",
            color='Qualité du retour',
            color_discrete_map=myCSS.pie_chart['colors'],
            category_orders={"Qualité du retour": myCSS.pie_chart_colors_keys}
        )
        pie_chart.update_layout(title_font=myCSS.pie_chart['title_font'])
        figures['tone-pie-chart'] = pie_chart

    if 'combined-pie-chart' in grid_items:
        combined_pie_chart = create_combined_pie_chart(filtered_df, myCSS.pie_chart, category_order=myCSS.pie_chart_colors_keys)
        figures['combined-pie-chart'] = combined_pie_chart

    if 'word-cloud' in grid_items:
        text = ' '.join(filtered_df['Sujet'].dropna().tolist() + filtered_df['Articles'].dropna().tolist())
        wordcloud = generate_wordcloud(text, style=myCSS.wordcloud, stopwords=FRENCH_STOP_WORDS)
        figures['word-cloud'] = wordcloud

    if 'geographic-distribution' in [item for sublist in DATA_GRID for item in sublist]:
        geographic_distribution = create_geographic_distribution_map(filtered_df, style=myCSS.geographic_distribution, geojson=FRANCE_GEOJSON)
        figures['geographic-distribution'] = geographic_distribution

    if 'sentiment-trend' in grid_items:
        sentiment_trend = create_sentiment_trend_chart(filtered_df, style=myCSS.sentiment_trend)
        figures['sentiment-trend'] = sentiment_trend

    if 'articles-time-series' in grid_items:
        time_series = px.line(
            data_frame=filtered_df.groupby('Date').size().reset_index(name="Nombre d'articles"),
            x='Date',
            y="Nombre d'articles",
            title="📈 Évolution du nombre d'articles",
            markers=True
        )
        time_series.update_yaxes(tickmode='linear', tick0=0, dtick=1, tickformat='d')
        time_series.update_traces(line=myCSS.time_series['line'])
        time_series.add_trace(
            create_legend_trace(
                category='positifs',
                color=myCSS.time_series['values_categories']['green']['color'],
                threshold=TIME_SERIES_THRESHOLD,
            )
        )
        time_series.add_trace(
            create_legend_trace(
                category='négatifs',
                color=myCSS.time_series['values_categories']['red']['color'],
                threshold=TIME_SERIES_THRESHOLD,
            )
        )
        background_shapes = get_timeseries_background_shapes(
            filtered_df, 
            values_categories=myCSS.time_series['values_categories'], 
            window='2D', 
            threshold=TIME_SERIES_THRESHOLD
        )
        time_series.update_layout(
            title=myCSS.time_series['title'],
            title_font=myCSS.time_series['title_font'],
            legend=myCSS.time_series['legend'],
            margin=myCSS.time_series['margin'], 
            shapes=background_shapes,
        )
        figures['articles-time-series'] = time_series

    # Prepare the return values in the correct order
    return_values = [figures.get(graph_id, {}) for graph_id in [item for sublist in DATA_GRID for item in sublist]]
    return_values.extend([table_data, theme_summary, tonalite_summary, territory_summary, media_summary, date_summary])

    return return_values
###################
## II.c) run app ##
###################
if __name__ == '__main__':
    dash_app.run(debug=True, host=DASH_APP_URL, port=DASH_APP_PORT)
