# H-GenAI w/ Sia Partners x Enedis

##  Enedis vision
### Presentation
Enedis is the leading French electricity distribution operator, managing the largest distribution network in Europe. Thanks to its advanced data capabilities, the company has ranked first in the _Smart Grid Index_ for over three years, ahead of major players as US or Taiwan.

In the context of energy transition and increasing competition following the _Clean Energy Package_, Enedis places great importance on its public image and the perception of its actions.

### Project Objective
Enedis aims to automate the analysis of opinions and feedback expressed in regional press articles. The goal is to develop a solution capable of automatically detecting and classifying feedback on Enedis from recent articles published in the Nord-Pas-de-Calais region.
More specifically, we will assess the sentiment of the articles and identify key topics discussed.


### Expected Impact
This analysis will help Enedis better understand public perception and adapt its communication strategy accordingly. By leveraging AI to structure this feedback, the company can anticipate trends and strengthen its market positioning against competitors.

### Data

A first dataset has been released: an excel (.xlsx) file where each row contains article data. This dataset is sufficient to complete the challenge. However, this Excel file was manually annotated from PDFs, making the process quite labor-intensive.

It was therefore natural to propose an initial feature aimed at simplifying this annotation work as much as possible. For this reason, a second dataset has also been shared: a collection of PDFs containing each multiple articles.

## Exploratory Data Analysis

### Excel Dataset

The dataset includes the following feature columns: `Date`, `Territoire`, `Sujet`, `Thème`, `Nbre d'articles`, `Média`, `Articles`, and the following labels: `Thème`, `Tonalité`, `Qualité de retour`, and `Qualité de retour2`.

It’s immediately noticeable that several labels are very similar, if not identical: for example, `Qualité de retour` and `Qualité de retour2` are essentially the same, with only minor spelling differences. Additionally, `Tonalité` and `Qualité de retour` are also very similar. Therefore, we decided to remove the `Tonalité` and `Qualité de retour2 columns`.

The `Qualité de retour` feature appeared to be quite ambiguous, containing a mix of sentiment analysis (positive/negative), intensity (nuanced), and factual elements. So, we chose to separate this variable into three new categories: `nuance`, `sentiment`, and `factuel`. We based this decision on the assumption that if `sentiment` is not specified, it is neutral, and if `nuance` (or `factuality`) is not specified, it is absent.

Given the highly skewed distribution of the features (as shown below), we left the decision to Enedis whether to keep the `nuance` and `factuel` features. Our team opted to retain them, but we do not expect good results from these features, which will likely be discarded later. However, we used a distinct methodology for the nuance labeling process (cf. [dedicated section](#nuance-labelisation)) to minimize bias.

Before:
![frequence de retour](/static/qualité%20de%20retour%20bar.png)
After:
![distribution sentiment](/static/distribution%20sentiment.png)

After normalizing the feature names, the dataset now includes the following columns: `date`, `territoire`, `sujet`, `nb_articles`, `media`, `article`, `theme`, `sentiment`, `nuance`, and `factuel`, with spelling differences minimized as much as possible.

After processing, we observe that there are **16** distinct themes with the top10 following distribution:

![camembert theme](/static/camembert%20theme.png)



The distribution of themes is skewed, with a tripartite bias. Classical statistical methods would typically involve data augmentation or theme merging. However, we did not pursue this approach because we do not have sufficient domain knowledge in electricity distribution to ensure the quality of new themes or the augmented data.

Finally, we noticed the presence of the variable `nb_articles`, which indicates when multiple media outlets have written articles about the same event. Since we will be building a dashboard that tracks the number of articles over time, this information remains relevant. Therefore, we chose to split this data across multiple rows when applicable. If this was not possible due to incorrect labeling, we left it as is.


### PDFs Dataset


## Proposed solution

### Frontend w/ DashBoard

### AWS integrations

#### Pipeline

##### Nuance Labelisation

#### Roles

#### Architecture Summary

![architecture](/static/architecture.png)

## Data Analyse & Results 