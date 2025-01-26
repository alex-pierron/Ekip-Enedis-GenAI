import pandas as pd
import plotly.express as px

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