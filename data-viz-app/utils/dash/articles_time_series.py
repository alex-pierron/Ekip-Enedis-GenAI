import pandas as pd
import plotly.express as px

def create_legend_trace(category, color, threshold):
    name = f"Pourcentage d'articles {category} >{threshold:.0%}"
    invisible_scatter = px.scatter(
        x=[None], y=[None], 
        color_discrete_sequence=[color]
    ).data[0].update(
        name=name, 
        legendgroup=category, 
        showlegend=True
    )
    return invisible_scatter

def create_rectangle_shape(start, end, color):
    shape = {
        'type': 'rect',
        'xref': 'x',
        'yref': 'paper',
        'x0': start,
        'x1': end,
        'y0': 0,
        'y1': 1,
        'fillcolor': color,
        'layer': 'below',
        'line_width': 0,
    }
    return shape

def get_timeseries_background_shapes(df, values_categories, window='2D', threshold=0.5):
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date').sort_index()
    
    # iterate (green/red)
    shapes = []
    for color_dict in values_categories.values():
        values = color_dict['values']
        color = color_dict['color']

        values_per_line = df['Qualité du retour'].isin(values)
        values_ratio_per_date = values_per_line.groupby('Date').mean()

        # rolling mean over the specified window period
        rolling_window = values_ratio_per_date.rolling(window=window, min_periods=1).mean()
        rolling_window = rolling_window.reset_index()

        # identify periods where rolling mean exceeds threshold
        values_dates = rolling_window[rolling_window['Qualité du retour'] > threshold].reset_index()

        # catch the period
        if values_dates.shape[0] > 1:
            intervals = []
            for i in range(len(values_dates)-1):
                current_date = values_dates.iloc[i]
                next_date = values_dates.iloc[i+1]
                if next_date['index'] - current_date['index'] == 1:
                    interval = (current_date['Date'], next_date['Date'])
                    intervals.append(interval)

            # generate colored shapes
            shapes.extend([create_rectangle_shape(start, end, color) for start, end in intervals])
            
    return shapes
