###### Global ######

container = {
    'backgroundColor': '#e2e2e2',
    'padding': '20px',
    'borderRadius': '15px',
    'boxShadow': '0px 4px 6px #808080'
}

###### Header ######
title = {
    'fontFamily': 'Aldrich',
    'color': '#003366',
    'marginLeft': '10%'
}

###### Filters Section ######

keywords_search = {
    'width': '100%', 
    'borderRadius': '10px'
}

date_picker_range = {
    'borderRadius': '10px'
}


###### Data Visualization ######

pie_chart = {
    'title_font': {
        'family': 'Arial',
        'size': 20,
        'color': 'black',
    },
    'colors': {
        "Positif": "#74c476",
        "Factuel positif": "#a1d99b",
        "Factuel": "#dfe1fc",
        "Factuel négatif": "#f7b7a3",
        "Négatif": "#e65555"
    }
}
pie_chart_colors_keys = list(pie_chart['colors'].keys())

time_series = {
    'line': {
        'color': '#2b3aec',
        'width': 2
    },
    'title_font': {
        'family': 'Arial',
        'size': 20,
        'color': 'black',
    }
}

data_table = {
    'page_size': 20,

    'style_table': {
        'overflowX': 'auto'
    },

    'style_header': {
        'fontFamily': 'Arial', 
        'fontSize': '16px',
        'fontWeight': 'bold', 
        'backgroundColor': '#0f53b9', 
        'color': 'white', 
        'borderRadius': '10px', 
    },

    'style_cell': {
        'textAlign': 'left', 
        'padding': '12px', 
        'fontFamily': 'Arial', 
        'fontSize': '14px', 
        'color': '#333'},

    'style_data_conditional': [
        { # colors according to the Pie Chart
            'if': {
                'column_id': 'Qualité du retour',
                'filter_query': f'{{Qualité du retour}} = "{key}"'
            },
            'backgroundColor': color,  
            'color': 'black', 
        }
        for key, color in pie_chart['colors'].items()
    ] + \
    [ # colors for less important columns 
        {'if': {'column_id': 'Date'}, 'backgroundColor': '#f6f6f6', 'color': 'black'}, 
        {'if': {'column_id': 'Territoire'}, 'backgroundColor': '#f6f6f6', 'color': 'black'}
    ],

}