[![English](https://img.shields.io/badge/README-English-2ea44f?style=for-the-badge)](README.md)
[![中文](https://img.shields.io/badge/README-中文-ffb703?style=for-the-badge)](README_zh.md)
## Eyewear Sales Data Analysis (eyewear-data-analysis)

## Project Overview

This repository is used for generating eyewear/store sales data, building raw data collection and preprocessing scripts (extracting and standardizing data from PDFs and text files), validating, aggregating, analyzing, and modeling. It covers the complete workflow from raw data collection, database initialization, data validation, aggregated feature construction, to customer segmentation, sales forecasting, NLP analysis, RAG/LLM experiments, and promotion effect evaluation.

## Project Structure
```bash
0-database-init: Database and ORM table initialization scripts, as well as scripts to generate and insert simulated/test data.
1-data-collect: Raw data extraction and preprocessing scripts (from PDFs, text, and standardized data).
2-data-validate: Jupyter notebooks and scripts for data validation and cleaning (checking table fields, completeness, and constraints).
3-data-aggregate: Main aggregation workflow: summarizing sales, cost, and gross margin by product, time, customer, and store.
4-customer-segmentation: Customer segmentation (feature engineering, standardization, clustering, evaluation metrics).
5-sale-predict: Sales forecasting (time series/regression models, training, evaluation, prediction pipeline).
6-NLP: Review and complaint text processing (preprocessing, sentiment analysis, topic modeling, key sentence extraction).
7-RAG+LLM: Retrieval-augmented generation (RAG) and LLM-based question answering/report automation experiments.
8-promo-effect: Promotion effect analysis (A/B testing, time windows, attribution, metric calculation).
9-review-complaint-overview: Summary analysis of reviews and complaints, trend analysis, and issue clustering.
```

## Functional Features of Each Folder

### 0-database-init

* Purpose: Define ORM tables, initialize the database, and insert test data to drive downstream analysis and modeling.
* Key scripts (recommended to run in order):
  * `data_sheet_create_0_1.py`: Defines table structures and creates all tables (must be run the first time).
  * `insert_product_info_data.py`: Generates and inserts ProductInfo (product information).
  * `insert_store_info_data.py`: Parses the rayban-store text and inserts StoreInfo (stores).
  * `insert_store_info_data_step2.py`: Processes lencrafter-store text and inserts the second type of store data.
  * `insert_promotion_activity_data.py`: Inserts PromotionActivity (promotional events).
  * `insert_customer_info_data.py`: Generates and inserts CustomerInfo (customer data).
  * `insert_order_data.py`: Generates and inserts Order and OrderItem records (orders). These depend on CustomerInfo and ProductInfo and can be linked to PromotionActivity.
  * `insert_customer_complaint_and_customer_review_data_v4_real_data_only_English.py`: Inserts customer complaint and customer review data.
  * `insert_competitor_info_data.py`: Inserts competitor data.

### 1-data-collect

* Purpose: Extract raw text/PDF/log data and convert it into structured intermediate files or Parquet datasets.
* Key scripts:
  * `data-collect-from-pdf.py`: Extracts store/product/review text from PDFs (install dependencies as indicated in the script comments, such as pdfplumber).
  * `sort_data.py`: Sorts or merges extracted results.
  * `insert_storecount_headers.py`: Generates or inserts header information as needed.

### 2-data-validate

* Purpose: Validate the data quality of all tables (missing values, anomalies, field ranges, foreign key constraints).
* Key notebooks:
  * `countryname_validate.ipynb`: Standardizes country/region names.
  * Various `*-data-validate.ipynb` notebooks (customer, order, product, etc.): Each table has a validation notebook containing summary statistics, abnormal examples, and correction recommendations.

### 3-data-aggregate

* Purpose: Aggregate raw detail tables into feature tables for analysis and modeling (by product, customer, time window, etc.).
* Typical notebooks/scripts:
  * `3-1-data-aggregate.ipynb`: Overall aggregation workflow example.
  * `3-2-cal-sale-amount-by-product.ipynb`: Calculates sales amount by product.
  * `3-2-cal-sale-amount-by-timeline.ipynb`: Aggregates by timeline (month/quarter/year/customer cluster/store/product).
  * `3-3-cal-product-cost-and-gross-margin-*.ipynb`: Calculates cost and gross margin by customer/order/product/month, etc.
  * `3-4-cal-AOV-per-*.ipynb`: Calculates AOV by (month/quarter/year/customer)
  * `3-5-cal-sale-qty-by-*.ipynb`: Calculates sales quantity by (month/quarter/year/customer cluster/store/product/region)
  * `3-6-cal-customer-quantity.ipynb`: Calculates customer count
  * `3-7-cal-product-customer-store-type_v2.ipynb`: Calculates customer/store type
  * `3-8-cal-order-status.ipynb`: Statistics on order type distribution
* Output: Aggregated Parquet tables (feature tables) for use in `4-` and `5-`.

### 4-customer-segmentation

* Purpose: Perform customer segmentation (RFM, behavioral features, clustering, stratification).
* Main content:
  * Feature engineering scripts (RFM metrics, repeat purchase rate, average order value, etc.) (`4-1-customer-segmentation-v3-k=5.ipynb`):
    * Extract and calculate RFM (recency, frequency, monetary), repeat purchase rate, average order value, category purchase ratios (frames/lenses/AI/sunglasses), promotional participation indicators, etc., from the PostgreSQL database using SQL.
    * Merge feature tables and filter for customers with purchase behavior; handle missing values and time fields (convert to days); fill or replace numeric features, then standardize them.
  * Standardization, dimensionality reduction (PCA), clustering (KMeans), cluster analysis, and visualization (`4-1-customer-segmentation-v3-k=5.ipynb`):
    * After StandardScaler normalization, use PCA to check the explained variance ratio of principal components (used for 2D visualization).
    * Use KMeans (example k=5) for clustering and evaluate clustering stability (ARI across multiple random seeds, bootstrap-sampled ARI) and inertia/silhouette for different k values to help determine the optimal k.
    * Generate a cluster profile (mean features, customer_share, revenue_share) and visualize it via PCA scatter plots, heatmaps, and radar charts.
    * Evaluate metrics: silhouette coefficient, within-cluster/between-cluster differences.
    * Finally, export results with the `cluster` label to `customerinfo_cluster.parquet`.
  * Write clustering results back to the database (`4-2-write-cluster-data-to-data-sheet.ipynb`):
    * Read `customerinfo_cluster.parquet`, update the `cluster` values to `CustomerInfo.customer_hierarchy`.
    * Then map the cluster to readable `customer_type` values (e.g., "VIP Loyal Customers", "Lens Customers", etc.) and update the `CustomerInfo.customer_type` table to persist the clustering results.
  * Export cluster reports (`4-3-export-customer-cluster-info.ipynb`):
    * Read CustomerInfo and detail tables from the database, calculate and save each customer’s RFM score, RFM segment, lifecycle stage, and churn risk (exported as `2023-2024_customer_cluster_rfm.parquet`).
    * Aggregate by cluster/customer type to calculate monthly sales metrics (sales amount, quantity, order count, customer count, AOV, gross profit, and gross margin), then export as `2023-2024_customer_cluster_monthly_sale.parquet` for subsequent analysis and visualization.

### 5-sale-predict

* Purpose: Build forecasting models for sales data, covering scenarios for predicting sales volume and sales amount by SKU, store, and time window.
* Main content:
  * Query order, product, customer, and promotion tables from PostgreSQL to construct a monthly sales dataset
  * Generate time-series features: lag values, rolling means, growth rates, seasonal features, etc., and build baseline models (e.g., moving average, weighted moving average, exponentially weighted mean,etc)
  * Construct the prediction feature matrix by incorporating promotion, region, category, and other business features
  * Handle missing values and convert data types, then split the training and testing sets in time order
  * Train LightGBM, CatBoost, and Prophet regression models, and tune hyperparameters using Optuna
  * Evaluate model performance with MAE, MAPE, and other metrics, and perform bias calibration
  * Compare different models and the final blended prediction results, and visualize actual vs predicted values
  * Output final prediction comparison results and save them as Parquet files for downstream analysis or reporting
* Corresponding files:
  * `5-1-sale-amount-monthly-predict-v4-blend.ipynb`: Monthly sales amount prediction
  * `5-2-sale-qty-monthly-predict-v2-blend.ipynb`: Monthly sales quantity prediction
  * `5-3-popular-product-sale-qty-monthly-predict-v2-blend.ipynb`: Popular product monthly sales quantity prediction
  * `5-4-popular-product-sale-amount-monthly-predict-v3-blend.ipynb`: Popular product monthly sales amount prediction
  * `5-5-each-customer-cluster-sale-qty-monthly-predict-v2-blend.ipynb`: Monthly sales quantity prediction by customer cluster
  * `5-6-each-customer-cluster-sale-amount-monthly-predict-v2-blend.ipynb`: Monthly sales amount prediction by customer cluster

### 6-NLP

* Purpose: Process CustomerReview / CustomerComplaint text for sentiment analysis, topic modeling, key sentence extraction, and entity recognition.
* Main content:
  * Read cleaned review/complaint data
  * Text cleaning: denoising, tokenization, stopword removal, lemmatization/stemming, filtering meaningless phrases, synonym normalization, and translation of non-English text
  * Text feature analysis: word frequency statistics, TF-IDF + Logistic Regression analysis, VADAR, TextBlob, BERT-based topic modeling
  * Sentiment analysis: rule-based methods or BERT pre-trained models for sentiment classification
  * Interpreting BERT Text Sentiment Analysis Results: LIME, Integrated Gradients + transformers_interpret/Captum
  * Keyword/entity extraction: Use keyBERT to identify and extract key expressions, brand/product terms, pain points, etc.
  * BERTopic clustering: Use sentence-transformers to load BERT models and apply BERTopic to positive and negative texts separately for topic clustering
  * Output: sentiment scores, topic labels, representative case texts, key features, and clustering results
* Corresponding files:
  * `6-1-data-extract-from-raw-data1.ipynb`: Extract information about different eyewear products from the raw data provided by Hugging Face.
  * `6-2-data-format-convert-from-raw-data.ipynb`: Convert the Amazon JSONL/CSV files containing raw data from Hugging Face into Parquet format
  * `6-3-data-merge-from-customer-complaints.ipynb`: Merges customer complaint data
  * `6-4-customer-review-data-preprocess-for-NLP-BERT-v2.ipynb`: Performing BERT NLP sentiment analysis on comment text and interpreting the BERT results
  * `6-4-1-customer-review-cluster-v3.ipynb`: Performs BERTopic clustering analysis on customer reviews
  * `6-5-translate-non-english-text.ipynb`: Translates non-English customer review text into English in Google Sheets
  * `6-6-download-BERT-model.ipynb`: Downloads BERT models
  * `6-7-convert-BERT-model-file-format.ipynb`: Converts BERT model files to safetensors format and saves them
  * `6-8-customer-complaint-data-preprocess-for-NLP-BERT-v4.ipynb`: Perform BERT-based NLP sentiment analysis on the complaint text and interpret the BERT results.
  * `6-8-1-customer-complaint-cluster-v2.ipynb`: Performs BERTopic clustering analysis on customer complaints
  * `dataset_download_url.txt`: Data set download link file
* Note: In multilingual scenarios, text should be processed by language branch (English/Chinese/other), rather than training directly on mixed-language data.

### 7-RAG+LLM

* Purpose: Build a Retrieval-Augmented Generation (RAG) demonstration and pipeline that leverages a knowledge base (aggregate tables, FAQs, reports, etc.) to provide automated answers and analytical reports—combining retrieval and generation—for business questions.

* Key Points:
  * Building the Knowledge Base: Generate document snippets from aggregated tables, reports, clustering results, etc., and index them (embeddings + vector database).
  * Retrieval Strategy: Define chunk size, similarity thresholds, reordering, and recall strategies to ensure retrieval quality.
  * Generation and Prompt Design: Design LLM prompts, control context length and instruction templates; perform deduplication, fact-checking, and credibility filtering on LLM outputs.
  * Test Gradio GUI scripts (`query → retrieve → generate`).

* Outputs and scripts (corresponding files in the project):
  * Knowledge generation:
    * `7-1-generate-product-knowledge.ipynb`: Generates product-attribute, category, and typical sales summary knowledge fragments from product information and sales details.
    * `7-2-generate-customer-cluster-knowledge-v2.ipynb`: Organizes customer clustering results and representative customer personas into retrievable documents (group characteristics, representative customers, behavioral insights).
    * `7-3-generate-customer-review-complaint-knowledge-ignore.ipynb`: Extracts themed, denoised fragments and representative cases from customer reviews and complaints for the knowledge base (low-quality items can be ignored or flagged).
    * `7-4-1-generate-sale-performance-knowledge.ipynb`: Summarizes sales performance metrics by time/product/channel and creates knowledge segments for performance-related questions.
    * `7-4-2-generate-customer-sales-predict-knowledge.ipynb`: Exports sales forecast summaries, prediction results, and feature importance as retrievable prediction knowledge entries.
    * `7-5-generate-store-knowledge.ipynb`: Organizes store metadata, geographic information, and overview performance into store-level knowledge fragments (branch profiles and comparison views).
    * `7-6-generate-promotion-intro.ipynb`: Summarizes promotion timing, rules, and effects to generate promotional descriptions and easily retrievable impact highlights.
    * `7-7-generate-high-freq-business-rules-and-questions.ipynb`: Collects common business rules and frequently asked questions, organizing them into FAQ-style knowledge entries for quick retrieval and automated answers.
  * Build index: `7-2-build_index/build-index.ipynb`:
    * Reads JSONL files from a specified input directory, extracts the text field from each record, encodes texts into vectors using a local SentenceTransformer model (`BAAI_bge_base_en_v15`) with NVIDIA CUDA acceleration, normalizes the embeddings, and builds a vector index with FAISS (`IndexFlatIP` for inner product similarity).
    * Writes the index and corresponding metadata (`docs`) to the `build_index/` output directory.
  * Retrieval: `7-3-retrieval\retrieval-v2-gui-LangChain.py`: This script uses Python, LangChain, faiss, torch, sentence-transformers, gradio, and the OpenAI client (for the DeepSeek API) to implement a vector-based RAG demo: It loads a pre-built FAISS index and the `knowledge_meta.json` file, encodes the user’s query into a vector using a local SentenceTransformer model, and retrieves similar snippets from the index (retaining only entries whose sources contain `customer_cluster`). It then concatenates the retrieved context into a prompt in a specific format and sends it to DeepSeek (via the OpenAI API client), before displaying the LLM’s response and the retrieval results in a Gradio GUI.
  * Demo result: Example screenshots under `final_output/`.

### 8-promo-effect

* Purpose: Evaluate the incremental impact of promotional campaigns on sales performance and attribute that impact.
* Analysis Methods:
  * Before-and-after comparison, same-store, same-product baseline comparison, and comparison between the campaign window and an equally long baseline window.
  * Measure campaign effectiveness using metrics such as sales revenue, sales volume, gross profit, AOV, gross profit margin, and ROI.
  * Calculate the incremental revenue from the campaign and the revenue relative to the baseline, and generate a performance evaluation table.
* Corresponding file: `8-1_promo_effect.ipynb.py`
* Output: Promotion effectiveness evaluation table, Parquet output file, and a reproducible notebook.

### 9-review-complaint-overview

* Purpose: To aggregate customer review and complaint data and provide foundational data for subsequent topic analysis, complaint rate analysis, and trend analysis.
* Includes:
  * Integration of review and complaint data (linked by order, product, store, and time).
  * Standardized organization of review/complaint fields and date processing.
  * Export aggregated Parquet files for subsequent topic modeling, positive review rate/complaint rate analysis, and issue clustering.
* Corresponding file: `9-1-review-overview.ipynb.py`
* Output: Aggregated review Parquet file, aggregated complaint Parquet file, and intermediate data required for subsequent analysis.


## Environment and Dependencies

* Python 3.11+
* miniconda 26.3.2
* NVIDIA CUDA 13.3
* PostgreSQL 17.10+
* Microsoft Power BI 2.157.879

## Datasets

* Eyewear product dataset: Sourced from publicly available financial reports on the Ray-Ban and EssilorLuxottica websites. See the `1-data-collect` folder for details.
* Dataset of customer reviews and complaints (from Hugging Face and Kaggle): See `6-NLP/dataset_download_url.txt` for details.

## Model Choices
* BERT model choices: `cardiffnlp/twitter-roberta-base-sentiment-latest`, `nlptown/bert-base-multilingual-uncased-sentiment`, `distilbert-base-uncased-finetuned-sst-2-english`
* Text-to-vector embedding model: SentenceTransformer (`BAAI_bge_base_en_v15`)

## Selecting an LLM Model
* LLM Selection: deepseek-api

## Approaches for Interpreting BERT NLP Text Sentiment Analysis Results:
LIME, Integrated Gradients + transformers_interpret/Captum

## Tools and Libraries

* The pip package primarily uses the following:
  ```bash
  gradio==4.44.1
  Jinja2==3.0.3
  langchain==0.2.16
  langchain-community==0.2.16
  langchain-core==0.2.43
  langchain-openai==0.1.25
  langchain-protocol==0.0.19
  langchain-text-splitters==0.2.4
  langsmith==0.1.147
  pandas==2.3.3
  SQLAlchemy==2.0.54
  psycopg2==2.9.12
  starlette==0.46.2
  transformers==4.57.6
  torch==2.5.1
  websockets==12.0
  nltk==3.10.3
  scikit-learn==1.9.0
  seaborn==0.13.2
  plotly==6.9.0
  numpy==2.4.6
  sentence-transformers==3.2.1
  bertopic==0.17.4
  pyarrow==25.0.0
  spacy==3.8.16
  spacy-legacy==3.0.12
  spacy-loggers==1.0.5
  langdetect==1.0.9
  lightgbm==4.7.0
  lime==0.2.0.1
  faiss-cpu==1.15.0
  fastapi==0.112.4
  catboost==1.2.10
  optuna==4.9.0
  matplotlib==3.10.9
  ```

## Deployment Instructions
### Download the project and open the folder

Download the project and open the folder:

```bash
git clone <repository-url>
cd eyewear-data-analysis\
```
### Create and activate a virtual environment in miniconda:

```bash
conda create -n <your-venv-name> python=3.11
conda activate <your-venv-name>
```

### Install dependencies:
```bash
pip install -r requirements.txt
```
### Create a PostgreSQL database:
```SQL
CREATE DATABASE "eyewear-data"
OWNER postgres
ENCODING 'UTF8';
```

### Initialize the data:

```bash
python 0-database-init/data_sheet_create_0_1.py
python 0-database-init/insert_product_info_data.py
python 0-database-init/insert_store_info_data.py
python 0-database-init/insert_store_info_data_step2.py
python 0-database-init/insert_promotion_activity_data.py
python 0-database-init/insert_customer_info_data.py
python 0-database-init/insert_order_data.py
```
Then run the notebooks in numeric order from top to bottom.

### View the Data Visualization Results
After downloading Power BI, view the dashboard results from the `eyewear-data-analysis-dashboard-v3.pbix` file.

### Run the RAG+LLM program:
First prepare your DeepSeek API key and place it in `api-key.txt`.
Then execute:
```bash
python .\7-RAG+LLM\7-3-retrieval\retrieval-v2-gui-LangChain.py
```
Then open the following URL in your browser:
**http://127.0.0.1:7860**

You can then view the Gradio GUI for the RAG+LLM system.

## License

This project is an open-source project licensed under the **Apache 2.0** License.

## Author and Acknowledgments

Author: Junliang Li
Email: [940747544@qq.com](mailto:940747544@qq.com)
