import os
import sys
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

from utils.load_and_clean_df import (
    load_data, 
    clean_data
)
from utils.dash_display import (
    create_accordion_item, 
    filter_df, 
    summary_filter,
    create_legend_trace,
    get_timeseries_background_shapes,
    generate_wordcloud
)
import assets.css.styles as myCSS

nltk.download('stopwords')
FRENCH_STOP_WORDS = set(stopwords.words('french'))

############################# CONFIG #############################

DASH_APP_URL = 'localhost'
DASH_APP_PORT = 8050

# highlights periods on the time series when the ratio of positive or negatives articles exceed the threshold
TIME_SERIES_THRESHOLD = 0.1

# set to True to display the word cloud
SHOW_WORDCLOUD = True

##################################################################


#######################
## I- LOAD CSV DATA ##
#######################
df = load_data(data_folder=os.path.join(PROJECT_PATH, 'data'))
df = clean_data(df)


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

# conditional layout for word cloud
wordcloud_section = dbc.Row([
    dbc.Col([dcc.Graph(id='word-cloud', style=myCSS.container)], width=6)
], className='mb-4', justify="center") if SHOW_WORDCLOUD else None

# layout
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
    dbc.Row([
        dbc.Col(dcc.Graph(id='tone-pie-chart', style=myCSS.container), width=6),
        dbc.Col(dcc.Graph(id='articles-time-series', style=myCSS.container), width=6)
    ], className='mb-4'),

    wordcloud_section,

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

@dash_app.callback(
    [
        Output('tone-pie-chart', 'figure'),
        Output('articles-time-series', 'figure'),
        Output('data-table', 'data'),
        Output('theme-title', 'title'),
        Output('tonalite-title', 'title'),
        Output('territory-title', 'title'),
        Output('media-title', 'title'),
        Output('date-title', 'title'),
        *([Output('word-cloud', 'figure')] if SHOW_WORDCLOUD else [])
    ],
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

    # time series
    time_series = px.line(
        data_frame=filtered_df.groupby('Date').size().reset_index(name="Nombre d'articles"),
        x='Date',
        y="Nombre d'articles",
        title="📈 Évolution du nombre d'articles",
        markers=True
    )
    time_series.update_yaxes(tickmode='linear', tick0=0, dtick=1, tickformat='d')

    time_series.update_traces(line=myCSS.time_series['line'])

    # add invisible traces for legend
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
    # add background shapes
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

    # pie chart
    pie_chart = px.pie(
        filtered_df,
        names='Qualité du retour',
        title="📊 Répartition des tonalités",
        color='Qualité du retour',
        color_discrete_map=myCSS.pie_chart['colors'],
        category_orders={"Qualité du retour": myCSS.pie_chart_colors_keys}
    )
    pie_chart.update_layout(title_font=myCSS.pie_chart['title_font'])

    # word cloud
    if SHOW_WORDCLOUD:
        text = ' '.join(filtered_df['Sujet'].dropna().tolist() + filtered_df['Articles'].dropna().tolist())
        wordcloud = generate_wordcloud(text, style=myCSS.wordcloud, stopwords=FRENCH_STOP_WORDS)

    # Table data
    formated_date_df = filtered_df.reset_index().sort_values(by='Date', ascending=False)
    formated_date_df['Date'] = formated_date_df['Date'].dt.strftime('%d/%m/%Y')
    table_data = formated_date_df.to_dict('records')

    if SHOW_WORDCLOUD:
        return pie_chart, time_series, table_data, theme_summary, tonalite_summary, territory_summary, media_summary, date_summary, wordcloud
    else:
        return pie_chart, time_series, table_data, theme_summary, tonalite_summary, territory_summary, media_summary, date_summary

###################
## II.c) run app ##
###################
if __name__ == '__main__':
    dash_app.run(debug=False, host=DASH_APP_URL, port=DASH_APP_PORT)
