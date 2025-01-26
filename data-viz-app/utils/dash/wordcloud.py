from wordcloud import WordCloud
import plotly.graph_objects as go

def generate_wordcloud(text, style, stopwords):
    # create word cloud
    wordcloud = WordCloud(
        width=style['width'], 
        height=style['height'], 
        background_color=style['backgroundColor'],
        stopwords=stopwords,
        max_words=100,
        prefer_horizontal=0.9,
    ).generate(text)

    # convert word cloud to np.array
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