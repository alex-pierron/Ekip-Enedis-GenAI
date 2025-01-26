import plotly.express as px

def create_sentiment_trend_chart(filtered_df, style):
    # group values
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
        title="📊 Tendance des tonalités au fil du temps",
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