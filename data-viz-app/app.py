import os
import sys
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.absolute()
sys.path.append(PROJECT_PATH)

from utils.load_and_clean_df import load_data, clean_data
from utils.dash_display import create_accordion_item, filter_df, get_shapes_critical_periods

############################# CONFIG #############################
DASH_APP_URL = '127.0.0.1'
DASH_APP_PORT = 8050

CUSTOM_STYLE = {
    'backgroundColor': '#f8f9fa',
    'padding': '20px',
    'borderRadius': '10px',
    'boxShadow': '0px 4px 6px rgba(0, 0, 0, 0.1)'
}

PIE_CHART_COLORS = {
    "Positif": "#74c476",
    "Factuel positif": "#a1d99b",
    "Factuel": "#e5e5e5",
    "Factuel négatif": "#f7b7a3",
    "Négatif": "#e65555"
}
##################################################################


######################
## I- LOAD CSV DATA ##
######################
df = load_data(data_folder=os.path.join(PROJECT_PATH, 'data'))
df = clean_data(df)


##########################
## II- DASH APPLICATION ##
##########################
dash_app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

##############################
## II.a) application Layout ##
##############################

dash_app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src='assets/enedis-logo.png', height='60px'), width='auto', className='d-flex align-items-center justify-content-start'),
        dbc.Col(html.H1("Analyse des reportings Enedis", className='text-center mb-5 mt-3 text-primary'), width=True, className='d-flex justify-content-center'),
        dbc.Col(html.Img(src='assets/hackathon-genIA-logo.png', height='60px'), width='auto', className='d-flex align-items-center justify-content-start')
    ], align='center', className='mb-4'),
    
    # keyword search bar
    dbc.Row([
        dbc.Col([
            dcc.Input(
                id='keyword-search',
                type='text',
                placeholder="Rechercher un mot-clé...",
                debounce=True,
                className='form-control mb-3',
                style={'width': '100%'}
            )
        ], width=6)
    ], justify='center'),

    # Dropdown filter selection 
    dbc.Accordion([

        # multi-choice 
        create_accordion_item(df, title='Thème', id='theme'),
        create_accordion_item(df, title='Territoire', id='territory'),
        create_accordion_item(df, title='Média', id='media'),

        # range time
        dbc.AccordionItem([
            html.Label("Sélectionner une période de temps", className='fw-bold'),
            dcc.DatePickerRange(
                id='date-picker',
                start_date=df['Date'].min(),
                end_date=df['Date'].max(),
                display_format='DD/MM/YYYY',
                minimum_nights=0,
                className='form-control'
            ),
        ], title="Filtrer par Date", id='date-title'),
    
    ], className='mb-4'),


    # Graphs
    dbc.Row([
        dbc.Col(dcc.Graph(id='tone-pie-chart', style=CUSTOM_STYLE), width=6),
        dbc.Col(dcc.Graph(id='articles-time-series', style=CUSTOM_STYLE), width=6)
    ], className='mb-4'),

    # Table
    html.Div([
        dash_table.DataTable(
            id='data-table',
            columns=[{"name": col, "id": col} for col in df.columns],
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'fontWeight': 'bold', 'backgroundColor': '#006fe6', 'color': 'white'},
            row_selectable=False,
            cell_selectable=False
        )
    ], style=CUSTOM_STYLE)
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
        Output('territory-title', 'title'),
        Output('media-title', 'title'),
        Output('date-title', 'title')],
    [   
        Input('theme-dropdown', 'value'),
        Input('territory-dropdown', 'value'),
        Input('media-dropdown', 'value'),
        Input('date-picker', 'start_date'),
        Input('date-picker', 'end_date'),
        Input('keyword-search', 'value')]
)
def update_visualizations(selected_themes, selected_territories, selected_media, start_date, end_date, keyword):
    
    filtered_df = filter_df(df, (selected_themes, selected_territories, selected_media, start_date, end_date, keyword)).sort_values(by='Date')

    # applied filters summary
    theme_summary = f"Thème: {', '.join(selected_themes[:3])}..." if selected_themes else "Filtrer par Thème"
    territory_summary = f"Territoire: {', '.join(selected_territories[:3])}..." if selected_territories else "Filtrer par Territoire"
    media_summary = f"Média: {', '.join(selected_media[:3])}..." if selected_media else "Filtrer par Média"
    
    start_date_str = pd.to_datetime(start_date).strftime('%d/%m/%Y')
    end_date_str = pd.to_datetime(end_date).strftime('%d/%m/%Y')
    date_summary = f"Date: {start_date_str} - {end_date_str}" if start_date and end_date else "Filtrer par Date"

    # time series
    time_series = px.line(
        data_frame=filtered_df.groupby('Date').size().reset_index(name="Nombre d'articles"),
        x='Date',
        y="Nombre d'articles",
        title="Évolution du nombre d'articles",
        markers=True
    )
    critical_shapes = get_shapes_critical_periods(filtered_df, critical_values=['Négatif', 'Factuel négatif'], window='3D', threshold=0.1)
    time_series.update_layout(shapes=critical_shapes)

    # pie chart
    pie_chart = px.pie(
        filtered_df,
        names='Qualité du retour',
        title="Répartition des tonalités",
        color='Qualité du retour',
        color_discrete_map=PIE_CHART_COLORS,
        category_orders={"Qualité du retour": list(PIE_CHART_COLORS.keys())}
    )

    # table
    formated_date_df = filtered_df.reset_index().sort_values(by='Date', ascending=False)
    formated_date_df['Date'] = formated_date_df['Date'].dt.strftime('%d/%m/%Y')
    table_data = (formated_date_df.to_dict('records'))

    return pie_chart, time_series, table_data, theme_summary, territory_summary, media_summary, date_summary

###################
## II.c) run app ##
###################

if __name__ == '__main__':
    dash_app.run(debug=True, host=DASH_APP_URL, port=DASH_APP_PORT)
