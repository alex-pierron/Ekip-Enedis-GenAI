import pandas as pd
from dash import dcc
import dash_bootstrap_components as dbc


def create_accordion_item(df, title, id, multi=True, style=None):
    options = df[title].unique()
    accordion_item = dbc.AccordionItem([
        dcc.Dropdown(
            id=f"{id}-dropdown",
            options=[{'label': option, 'value': option} for option in options],
            placeholder=f"Sélectionnez un ou plusieurs {title.lower()}s",
            multi=multi,
            style=style or {'margin-bottom': '10px'}
        ),
    ], title=f"Filtrer par {title}", id=f"{id}-title")
    return accordion_item


def filter_df(df, filters):
    theme, territory, media, start_date, end_date, keyword = filters

    if theme:
        df = df[df['Thème'].isin(theme)]
    if territory:
        df = df[df['Territoire'].isin(territory)]
    if media:
        df = df[df['Média'].isin(media)]
    if start_date and end_date:
        df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    if keyword and keyword.strip():
        df = df[df[['Sujet', 'Articles']].apply(lambda x: x.str.contains(keyword, case=False, na=False)).any(axis=1)]

    return df


def create_red_rectangle_shape(start, end):
    shape = {
        'type': 'rect',
        'xref': 'x',
        'yref': 'paper',
        'x0': start,
        'x1': end,
        'y0': 0,
        'y1': 1,
        'fillcolor': 'rgba(255, 0, 0, 0.3)',
        'opacity': 0.5,
        'layer': 'below',
        'line_width': 0,
    }
    return shape


def get_shapes_critical_periods(df, critical_values, window, threshold):
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