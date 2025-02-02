import re
import pandas as pd
from dash import dcc
import dash_bootstrap_components as dbc
from utils.shared_utils import normalize_text


def create_accordion_item(
    df: pd.DataFrame,
    title: str,
    id: str,
    multi: bool = True,
    style: dict = None,
    ordered_values: list = None,
) -> dbc.AccordionItem:
    """
    Creates an accordion item with a dropdown filter for a specific column in a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to filter.
        title (str): The name of the column to filter by.
        id (str): The unique identifier for the accordion item.
        multi (bool, optional): Whether the dropdown allows multiple selections. Defaults to True.
        style (dict, optional): Custom CSS styles to apply to the dropdown. Defaults to None.
        ordered_values (list, optional): A list of ordered values to sort the dropdown options. Defaults to None.

    Returns:
        dbc.AccordionItem: A Dash accordion item containing the dropdown filter.
    """
    # Get unique options from the DataFrame column
    options = df[title].unique()

    # Sort options by an ordered list if provided, otherwise alphabetically
    if ordered_values:
        sorted_options = sorted(
            options,
            key=lambda option: ordered_values.index(option)
            if option in ordered_values
            else float("inf"),
        )
    else:
        sorted_options = sorted(options)

    # Create the accordion item with the dropdown
    accordion_item = dbc.AccordionItem(
        [
            dcc.Dropdown(
                id=f"{id}-dropdown",
                options=[
                    {"label": option, "value": option} for option in sorted_options
                ],
                placeholder=f"Sélectionnez un ou plusieurs {title.lower()}s"
                if id != "tonalite"
                else "Sélectionnez une ou plusieurs qualités du retour",
                multi=multi,
                style=style or {"margin-bottom": "10px"},
            ),
        ],
        title=f"Filtrer par {title}",
        id=f"{id}-title",
    )

    return accordion_item


def filter_df(df: pd.DataFrame, filters: list) -> pd.DataFrame:
    """
    Filters the DataFrame based on the provided filter criteria.

    Args:
        df (pd.DataFrame): The DataFrame to filter.
        filters (list): A list containing the filter criteria in the following order:
                        [theme, tonalite, territory, media, start_date, end_date, keywords].

    Returns:
        pd.DataFrame: A filtered DataFrame based on the provided filters.
    """
    theme, tonalite, territory, media, start_date, end_date, keywords = filters

    # Apply filters to the DataFrame
    if theme:
        df = df[df["Thème"].isin(theme)]
    if tonalite:
        df = df[df["Qualité du retour"].isin(tonalite)]
    if territory:
        df = df[df["Territoire"].isin(territory)]
    if media:
        df = df[df["Média"].isin(media)]
    if start_date and end_date:
        df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    # If keywords are provided, filter based on matching keywords in 'Sujet' or 'Article'
    if keywords and keywords.strip():
        # Split keywords by comma, space, or semicolon and normalize the text
        keywords_list = [
            normalize_text(kw)
            for kw in re.split(r"[,\s;]+", keywords.strip())
            if kw.strip()
        ]

        # Filter rows where all keywords are present in either 'Sujet' or 'Article'
        def contains_all_keywords(row):
            combined_text = normalize_text(f"{row['Sujet']} {row['Article']}")
            return all(kw in combined_text for kw in keywords_list)

        df = df[df.apply(contains_all_keywords, axis=1)]

    return df


def summary_filter(column: str, selected_values: list) -> str:
    """
    Generates a summary text for the applied filters.

    Args:
        column (str): The name of the column that is being filtered.
        selected_values (list): A list of selected values for the filter.

    Returns:
        str: A string summarizing the applied filter for the specified column.
    """
    # Generate a summary based on the selected values
    if selected_values:
        if len(selected_values) <= 3:
            summary = f"Filtrer par {column}: {', '.join(selected_values)}"
        else:
            summary = f"Filtrer par {column}: {', '.join(selected_values[:3])}..."
    else:
        summary = f"Filtrer par {column}"

    return summary
