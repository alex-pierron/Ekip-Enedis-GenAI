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

The project utilizes a dataset comprising PDF files that contain reports on various events related to the electricity distribution company Enedis. These PDFs are rich sources of information, as they include articles from multiple media outlets covering news and events in the northern regions of France. The primary goal of working with this dataset was to process and analyze the PDFs to extract structured and meaningful information from their contents.

Each PDF in the dataset is a compilation of articles, often containing both textual content and images. The challenge lies in the unstructured nature of PDFs, which typically do not provide a clear separation between individual articles or sections. To address this, the project focuses on developing a methodology to segment and identify distinct articles within a single PDF. This segmentation is crucial for isolating individual news pieces, enabling further analysis and extraction of relevant metadata.

The extracted metadata includes key details such as the article's title, publication date, source media, and any associated images. By transforming the unstructured PDF content into a structured format, the dataset becomes more accessible for downstream tasks such as data analysis, visualization, and machine learning. For instance, the structured data can be used to analyze trends in media coverage, sentiment analysis of articles, or geographic distribution of reported events.


## Proposed solution

### Frontend w/ DashBoard

This project offers a sophisticated, interactive web-based dashboard developed with Python using the Dash framework and Plotly for data visualization. The dashboard connects to an AWS RDS MySQL database and dynamically retrieves reporting data related to Enedis. This tool is designed for data analysts, business intelligence professionals, and anyone looking to gain deeper insights into Enedis's data through graphical and tabular views.
Features:

- Keyword Search Functionality: This feature enables users to search for specific keywords within the dataset. The system will filter relevant records based on the keyword input, helping users quickly locate the data they need.
- Filtering Options: Users can filter the data based on multiple criteria such as theme, sentiment, territory, media type, and date range. These filters allow for more targeted analysis and ensure that users can focus on the specific subsets of the data they are interested in.
- Interactive Visualizations:
        - Combined Pie and Bar Charts: The dashboard displays combined pie and bar charts that represent media and sentiment distribution. This helps users understand the breakdown of data and the prevalence of different sentiments or media types across reports.
        - Sentiment Trend Chart: An interactive area chart visualizes the sentiment trends over time, offering a clear view of how sentiments have evolved across various periods.
        - Word Cloud: A dynamic word cloud is generated based on the dataset, displaying the most frequent words and phrases. This is particularly useful for text analysis and extracting key themes or subjects in the reports.
        - Geographic Distribution Map: A geographic map (using GeoJSON data for French regions) illustrates the distribution of data across various territories, allowing users to see trends based on location.
    - Tabular Data Display: A paginated data table presents the filtered data in a user-friendly format.

Additionally, the application has functionality to export the data as an Excel file (XLSX format). Users can also upload PDF files for processing, enriching the dataset with new information that can be visualized within the dashboard.

### AWS Integrations

This project's infrastructure leverages AWS services to facilitate seamless and scalable data processing. The solution is entirely serverless, ensuring scalability, low maintenance, and cost-efficiency.

- S3 Bucket: The S3 bucket is used to store input PDF files as well as the data extracted from the AI pipeline. Once a PDF is uploaded, it is sent through various processing stages, and the extracted data is saved to S3 before being used to update the dashboard.
    - PDF Text Extraction: PDFs are processed through a text extraction service. The extracted text is then parsed for relevant data to be added to the dataset.
    - NOVA Light: NOVA Light is utilized to extract specific fields from the PDF documents. This step ensures that structured data, such as key metrics or data points, can be used directly in the dashboard, providing meaningful insights.
    - MISTRAL Large: This service performs sentiment analysis on the extracted text, classifying the data into different sentiment categories (positive, neutral, negative). The results are integrated into the dashboard for visualizing sentiment trends and distributions.
    - RDS MySQL: The AWS RDS MySQL database serves as the centralized storage for all structured data. This data is used to populate the dashboard’s visualizations and tables, ensuring the data is consistent, up-to-date, and ready for analysis.

These AWS services work together to create a robust, scalable solution that supports a fully automated data pipeline from PDF upload to data visualization.

#### Pipeline Overview

The AI pipeline within this project is designed to be fully automated and integrated with the dashboard. It processes uploaded PDF files and enriches the data through various machine learning models and extraction tools.

- PDF Upload and Extraction: The process begins when a user uploads a PDF file via the dashboard. The file is stored in an S3 bucket and sent for text extraction.
- Data Extraction: The text extracted from the PDF is analyzed and parsed using NOVA Light, which identifies and extracts relevant data fields from the document.
- Sentiment Analysis: The extracted text is then passed through MISTRAL Large, which applies sentiment analysis models to classify the content's sentiment. This step enriches the dataset with sentiment information, which is then displayed on the dashboard.
- Data Storage: Once the text is processed and sentiment is analyzed, the resulting data is structured and saved into the RDS MySQL database, where it becomes available for querying by the dashboard.
- Dashboard Visualization: The dashboard queries the database to retrieve the structured data and uses Dash and Plotly to generate interactive visualizations, including charts, maps, and tables. Users can interact with the dashboard in real-time, apply filters, and explore different insights.

By automating these steps, the pipeline provides a seamless workflow that efficiently integrates new data into the dashboard, ensuring that users always have access to the most up-to-date information.

##### Nuance Labelisation

#### Roles

AWS services use a role-based system that enables precise management of permissions for each object and service.
Each service must be configured with the necessary roles for proper functionality.

This management is primarily handled through IAM (Identity and Access Management), the permission manager, but also within the individual services (Lambda, SQS, S3, etc.).

#### Architecture Summary

![architecture](/static/architecture.png)

## Data Analyse & Results 
