import plotly.express as px
from plotly.subplots import make_subplots

def create_combined_pie_chart(filtered_df, style, category_order):

    threshold = 0.02  # 2% threshold
    media_counts = filtered_df['Média'].value_counts(normalize=True)
    filtered_df['Média'] = filtered_df['Média'].apply(
        lambda x: x if media_counts[x] > threshold else 'Autres'
    )

    # create a subplot for multiple the pie charts
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'pie'}, {'type': 'pie'}]],
        subplot_titles=[
            "📊 Répartition des médias",
            "📊 Répartition des tonalités",
        ]
    )

    # 1. Répartition des Médias
    media_pie = px.pie(
        filtered_df,
        names='Média',
        color='Média',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    fig.add_trace(media_pie.data[0], row=1, col=1)
    
    # 2. Répartition des tonalités
    tone_pie = px.pie(
        filtered_df,
        names='Qualité du retour',
        color='Qualité du retour',
        color_discrete_map=style['colors'],
        category_orders={"Qualité du retour": category_order}
    )
    fig.add_trace(tone_pie.data[0], row=1, col=2)

    # update figure
    fig.update_layout(
        title_font=style['title_font'],
        showlegend=True,
        margin=dict(t=50, b=0, l=20, r=0)
    )
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Percentage: %{percent:.1%}<br>"
            "Count: %{value}"
        ),
        hole=0.3,
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig.update_traces(showlegend=False, selector=0)

    return fig