###### Global ######

global_layout = {
    'backgroundColor': '#f8f9fa'
}

container = {
    'backgroundColor': '#e2e2e2',
    'padding': '20px',
    'borderRadius': '15px',
    'boxShadow': '0px 4px 6px #808080',
    'marginBottom': '5px',
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

pie_bar_chart = {
    'title_font': {
        'family': 'Arial',
        'size': 20,
        'color': 'black',
    },
    'colors': {
        "Positif": '#74c476',
        "Neutre": '#dfe1fc',
        "Négatif": '#e65555'
    },
    'bar_colors': {
        "Factuel": {
            "Oui": '#98d399',
            "Non": '#ed8181'
        },
        "Sentiment": {
            "Positif": '#98d399',
            "Neutre": '#dfe1fc',
            "Négatif": '#ed8181'
        },
        "Nuancé": {
            "Oui": '#98d399',
            "Non": '#ed8181'
        }
    }
}
pie_bar_chart_colors_keys = list(pie_bar_chart['colors'].keys())


geographic_distribution = {
    'title': '🌍 Répartition géographique des tonalités',
    'title_font': {
        'family': 'Arial',
        'size': 20,
        'color': 'black',
    },
    'color_mapping': {
        'Positif': '#98d399',
        'Neutre': '#dfe1fc',  
        'Négatif': '#ed8181',
        'Inconnu': '#f2f2f2',
    }
}

sentiment_trend = {
    'color_mapping': {
        'Positif': '#98d399',
        'Neutre': '#a9aff7',  
        'Négatif': '#ed8181'
    }
}

wordcloud = {
    'title': {
        'text': '☁️ Fréquence des mots clés',
        'font': {
            'family': 'Arial',
            'size': 20,
            'color': 'black',
        },
    },
    'width': 800,
    'height': 400,
    'backgroundColor': 'white',
}

export_button = {
    'background-color': '#0f53b9',  
    'color': 'white',   
    'fontWeight': 'bold',           
    'border': 'none',              
    'font-size': '16px',
    'cursor': 'pointer',
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
        { # colors according to the pie chart
            'if': {
                'column_id': 'Sentiment',
                'filter_query': f'{{Sentiment}} = "{key}"'
            },
            'backgroundColor': color,  
            'color': 'black', 
        }
        for key, color in pie_bar_chart['colors'].items()
    ] + \
    [ # colors for less important columns 
        {'if': {'column_id': 'Date'}, 'backgroundColor': '#f6f6f6', 'color': 'black'}, 
        {'if': {'column_id': 'Territoire'}, 'backgroundColor': '#f6f6f6', 'color': 'black'}
    ],

}
