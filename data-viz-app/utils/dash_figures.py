import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_combined_pie_chart(filtered_df, style, category_order):

    # group non-pertinent medias based on a threshold ratio 
    threshold = 0.02  
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
        hole=0.4,
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig.update_traces(showlegend=False, selector=0)

    return fig



def create_geographic_distribution_map(filtered_df, style, geojson):
    # get most frequent Tonalité for each Territoire
    aggregated_df = filtered_df.groupby('Territoire')['Qualité du retour'].agg(
        lambda x: x.mode()[0] if not x.mode().empty else 'Inconnu'
    ).reset_index()

    # map Tonalité to style's group
    aggregated_df['Tonalité'] = aggregated_df['Qualité du retour'].map(style['group_mapping'])

    # get Territoires from the GeoJSON file
    all_territoires = pd.DataFrame({
        'Territoire': [feature['properties']['nom'] for feature in geojson['features']]
    })

    # merge with aggregated_df
    merged_df = all_territoires.merge(aggregated_df, on='Territoire', how='left')

    # set default grey color to Territoires with no data
    merged_df['Tonalité'] = merged_df['Tonalité'].fillna('Inconnu')

    # create choropleth map
    geo_fig = px.choropleth(
        merged_df, 
        geojson=geojson, 
        locations='Territoire', 
        featureidkey="properties.nom",
        color='Tonalité',
        color_discrete_map=style['color_mapping'],
        title=style['title'],
        hover_data=['Territoire', 'Tonalité'],
    )
    geo_fig.update_layout(
        title_font=style['title_font'],
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )    
    geo_fig.update_geos(fitbounds="locations", visible=False)
    
    return geo_fig



def create_sentiment_trend_area(filtered_df, style):
    # group values based on mapping
    filtered_df['Tonalité'] = filtered_df['Qualité du retour'].map(style['group_mapping'])

    # aggregate data by grouped sentiment and date
    sentiment_trend = (
        filtered_df.groupby(['Date', 'Tonalité'])
        .size()
        .reset_index(name='Count')
    )

    # stacked area chart
    fig = px.area(
        sentiment_trend, 
        x='Date', 
        y='Count', 
        color='Tonalité',
        title="📈 Tendance des tonalités au fil du temps",
        color_discrete_map=style['color_mapping']
    )
    
    fig.update_layout(
        title_font=dict(size=20),
        xaxis_title="Date",
        yaxis_title="Nombre d'articles",
        legend_title="Tonalité",
        template="plotly_white"
    )

    return fig 



def create_wordcloud(text, style, stopwords):
    # create word cloud
    wordcloud = WordCloud(
        width=style['width'], 
        height=style['height'], 
        background_color=style['backgroundColor'],
        stopwords=stopwords,
        max_words=100,
        prefer_horizontal=0.9,
    ).generate(text)

    # convert word cloud to np.array (to get a better quality than a static png)
    wordcloud_array = wordcloud.to_array()

    # transform it into a plotly figure 
    fig = go.Figure()
    fig.add_trace(go.Image(z=wordcloud_array, hoverinfo='skip'))

    fig.update_layout(
        title=style['title'],
        xaxis=dict(visible=False, scaleanchor='y'),
        yaxis=dict(visible=False, scaleanchor='x'),
        margin=dict(l=0, r=0, t=40, b=0), 
        paper_bgcolor='white',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig
