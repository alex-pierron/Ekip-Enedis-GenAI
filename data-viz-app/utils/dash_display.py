import re
import unicodedata
import pandas as pd
from dash import dcc
import dash_bootstrap_components as dbc


def create_accordion_item(df, title, id, multi=True, style=None, ordered_values=None):
    options = df[title].unique()

    # sort options by ordered given list, else alphabetically 
    if ordered_values:
        sorted_options = sorted(options, key=lambda option: ordered_values.index(option) if option in ordered_values else float('inf'))
    else:
        sorted_options = sorted(options)

    accordion_item = dbc.AccordionItem([
        dcc.Dropdown(
            id=f"{id}-dropdown",
            options=[{'label': option, 'value': option} for option in sorted_options],
            placeholder=f"Sélectionnez un ou plusieurs {title.lower()}s" if id!='tonalite' else "Sélectionnez une ou plusieurs qualités du retour",
            multi=multi,
            style=style or {'margin-bottom': '10px'}
        ),
    ], title=f"Filtrer par {title}", id=f"{id}-title")
    return accordion_item


def normalize_text(text):
    """Convert text to lowercase and remove accents."""
    text = str(text).lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', text) 
        if unicodedata.category(c) != 'Mn'
    )


def filter_df(df, filters):
    theme, tonalite, territory, media, start_date, end_date, keywords = filters

    if theme:
        df = df[df['Thème'].isin(theme)]
    if tonalite:
        df = df[df['Qualité du retour'].isin(tonalite)]
    if territory:
        df = df[df['Territoire'].isin(territory)]
    if media:
        df = df[df['Média'].isin(media)]
    if start_date and end_date:
        df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

    if keywords and keywords.strip():
        # splt keywords by comma, space, or semicolon
        keywords_list = [normalize_text(kw) for kw in re.split(r'[,\s;]+', keywords.strip()) if kw.strip()]
        
        # filter rows that all keywords are present in either 'Sujet' or 'Articles'
        def contains_all_keywords(row):
            combined_text = normalize_text(f"{row['Sujet']} {row['Articles']}")
            return all(kw in combined_text for kw in keywords_list)

        df = df[df.apply(contains_all_keywords, axis=1)]

    return df

def summary_filter(column, selected_values):
    if selected_values:
        if len(selected_values) <= 3:
            summary = f"Filtrer par {column}: {', '.join(selected_values)}"
        else:
            summary = f"Filtrer par {column}: {', '.join(selected_values[:3])}..."
    else:
        summary = f"Filtrer par {column}"
    return summary

def create_red_rectangle_shape(start, end):
    shape = {
        'type': 'rect',
        'xref': 'x',
        'yref': 'paper',
        'x0': start,
        'x1': end,
        'y0': 0,
        'y1': 1,
        'fillcolor': '#f7b7a3',
        'layer': 'below',
        'line_width': 0,
    }
    return shape


def get_shapes_critical_periods(df, critical_values=['Négatif', 'Factuel négatif'], window='3D', threshold=0.1):
    # sort by date
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()

    # get a mean of critical values over a rolling window
    critical_values_per_line = df['Qualité du retour'].isin(critical_values)
    critical_ratio_per_date = critical_values_per_line.groupby('Date').mean()
    rolling_window = critical_ratio_per_date.rolling(window=window, min_periods=1).mean()
    rolling_window = rolling_window.reset_index().rename(columns={'Qualité du retour': 'Ratio critique'})

    # filter dates where threshold is reached
    critical_dates = rolling_window[rolling_window['Ratio critique'] >= threshold].reset_index()

    # generates red rectangles shapes for periods where threshold is reached    
    shapes = []
    if(critical_dates.shape[0] > 1):

        intervals = []
        for i in range(len(critical_dates)-1):
            current_date = critical_dates.iloc[i]
            next_date = critical_dates.iloc[i+1]

            if(next_date['index'] - current_date['index'] == 1):
                intervals.append((current_date['Date'], next_date['Date']))

        shapes = [create_red_rectangle_shape(start, end) for start, end in intervals]

    return shapes