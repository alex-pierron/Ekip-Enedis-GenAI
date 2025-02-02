import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_combined_pie_bar_chart(filtered_df, style):

    # Group non-pertinent medias based on a threshold ratio 
    threshold = 0.02  
    media_counts = filtered_df['Média'].value_counts(normalize=True)
    filtered_df['Média'] = filtered_df['Média'].apply(
        lambda x: x if media_counts[x] > threshold else 'Autres'
    )

    # Create a subplot for multiple charts
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'pie'}, {'type': 'bar'}]],
        subplot_titles=[
            "📊 Répartition des médias",
            "📊 Répartition des tonalités",
        ]
    )

    # 1. Répartition des Médias (Pie Chart)
    media_pie = px.pie(
        filtered_df,
        names='Média',
        color='Média',
        color_discrete_sequence=px.colors.qualitative.Plotly,
    )
    fig.add_trace(media_pie.data[0], row=1, col=1)

    # Apply the same pie chart styling as before
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Percentage: %{percent:.1%}<br>"
            "Count: %{value}"
        ),
        hole=0.4,
        marker=dict(line=dict(color='#FFFFFF', width=2)),
        selector=0
    )
    fig.update_traces(showlegend=False, selector=0)

    # 2. Répartition des ratios (Bar Chart)
    factuel_ratio = filtered_df['Factuel'].value_counts(normalize=True).to_dict()
    sentiment_ratio = filtered_df['Sentiment'].value_counts(normalize=True).to_dict()
    nuance_ratio = filtered_df['Nuancé'].value_counts(normalize=True).to_dict()

    # Structure
    ratio_data = {
        'Factuel': factuel_ratio,
        'Sentiment': sentiment_ratio,
        'Nuancé': nuance_ratio
    }

    # Bar chart with stacked bars for each category
    categories = ['Factuel', 'Sentiment', 'Nuancé']
    bars = []

    for category in categories:
        labels = list(ratio_data[category].keys())
        values = list(ratio_data[category].values())
        
        # Create a stacked bar trace for each label
        for i, label in enumerate(labels):
            color = style['bar_colors'][category].get(label, '#000000')  # Default to black
            
            bars.append(go.Bar(
                x=[category],
                y=[values[i]],
                name="",
                text=[f"{values[i]:.1%}"],
                textposition="inside",
                hovertemplate=(
                    f"<b>{category}: {label}</b><br>"
                    "Ratio: %{y:.1%}<br>"
                ),
                marker=dict(color=color),
            ))

    # Add bars to the plot
    for bar in bars:
        fig.add_trace(bar, row=1, col=2)

    # 3. Update layout
    fig.update_layout(
        title_font=style['title_font'],
        showlegend=False,
        margin=dict(t=50, b=10, l=5, r=20),
        barmode="stack",
        xaxis_title="Category",
        yaxis_title="Ratio Distribution",
        yaxis=dict(showgrid=True),
        bargap=0.3
    )

    return fig



def create_geographic_distribution_map(filtered_df, style, geojson):
    # get most frequent Tonalité for each Territoire
    aggregated_df = filtered_df.groupby('Territoire')['Sentiment'].agg(
        lambda x: x.mode()[0] if not x.mode().empty else 'Inconnu'
    ).reset_index()

    # get Territoires from the GeoJSON file
    all_territoires = pd.DataFrame({
        'Territoire': [feature['properties']['nom'] for feature in geojson['features']]
    })

    # merge with aggregated_df
    merged_df = all_territoires.merge(aggregated_df, on='Territoire', how='left')

    # set default grey color to Territoires with no data
    merged_df['Sentiment'] = merged_df['Sentiment'].fillna('Inconnu')

    # create choropleth map
    geo_fig = px.choropleth(
        merged_df, 
        geojson=geojson, 
        locations='Territoire', 
        featureidkey="properties.nom",
        color='Sentiment',
        color_discrete_map=style['color_mapping'],
        title=style['title'],
        hover_data=['Territoire', 'Sentiment'],
    )
    geo_fig.update_layout(
        title_font=style['title_font'],
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
    )    
    geo_fig.update_geos(fitbounds="locations", visible=False)
    
    return geo_fig



def create_sentiment_trend_area(filtered_df, style):

    # Aggregate data by grouped sentiment and date
    sentiment_trend = (
        filtered_df.groupby(['Date', 'Sentiment'])
        .size()
        .reset_index(name='Count')
    )

    # Filter data for 'Factuel' where the value is 'Oui'
    factuel_trend = (
        filtered_df[filtered_df['Factuel'] == 'Oui'] 
        .groupby(['Date', 'Factuel'])
        .size()
        .reset_index(name='Count')
    )

    # Rename 'Factuel' column to 'Sentiment' and replace 'Oui' with 'Factuel'
    factuel_trend = factuel_trend.rename(columns={'Factuel': 'Sentiment'})
    factuel_trend['Sentiment'] = 'Factuel'

    # Combine sentiment and factuel data into a single DataFrame
    combined_trend = pd.concat([sentiment_trend, factuel_trend], axis=0)

    # Create a single figure
    fig = px.area(
        combined_trend, 
        x='Date', 
        y='Count', 
        color='Sentiment',
        color_discrete_map=style['color_mapping'],
        title="📈 Tendance des tonalités et des articles factuels au fil du temps"
    )

    # Update layout
    fig.update_layout(
        title_font=dict(size=20),
        xaxis_title="Date",
        yaxis_title="Nombre d'articles",
        legend_title="Légende",
        template="plotly_white",
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
