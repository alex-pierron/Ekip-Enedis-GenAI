import re
from dash import dcc
import dash_bootstrap_components as dbc
from utils.shared_utils import normalize_text

def create_accordion_item(df, title, id, multi=True, style=None, ordered_values=None):
    options = df[title].unique()

    # sort options by ordered given list, else alphabetically 
    if ordered_values:
        sorted_options = sorted(options, key=lambda option: ordered_values.index(option) if option in ordered_values else float('inf'))
    else:
        sorted_options = sorted(options)

    # create the accordion item
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

def filter_df(df, filters):
    theme, tonalite, territory, media, start_date, end_date, keywords = filters

    # filter dataframe
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
        # split keywords by comma, space, or semicolon
        keywords_list = [normalize_text(kw) for kw in re.split(r'[,\s;]+', keywords.strip()) if kw.strip()]
        
        # filter rows that all keywords are present in either 'Sujet' or 'Articles'
        def contains_all_keywords(row):
            combined_text = normalize_text(f"{row['Sujet']} {row['Articles']}")
            return all(kw in combined_text for kw in keywords_list)

        df = df[df.apply(contains_all_keywords, axis=1)]

    return df

def summary_filter(column, selected_values):
    # generate the text to summarize applied filters
    if selected_values:
        if len(selected_values) <= 3:
            summary = f"Filtrer par {column}: {', '.join(selected_values)}"
        else:
            summary = f"Filtrer par {column}: {', '.join(selected_values[:3])}..."
    else:
        summary = f"Filtrer par {column}"
    return summary
