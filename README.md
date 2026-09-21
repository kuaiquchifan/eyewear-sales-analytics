## 眼镜销售数据分析(eyewear-data-analysis)

## 项目总览

本仓库用于眼镜/门店销售数据的生成、校原始数据抓取与预处理脚本（从 PDF、文本抓取并标准化）。验、聚合、分析与建模。涵盖从原始数据采集、数据库初始化、数据校验、聚合特征构建，到客户聚类分群、销售预测、NLP 分析、RAG/LLM 实验与促销效果评估的完整流程。

## 项目结构
```bash
0-database-init：数据库与 ORM 表结构初始化、生成和插入模拟/测试数据的脚本集合。
1-data-collect：原始数据抓取与预处理脚本（从 PDF、文本抓取并标准化）。
2-data-validate：数据校验与清洗的 Jupyter 笔记本与脚本（按表验证字段、完整性和约束）。
3-data-aggregate：主聚合流程：按产品、时间、客户与门店汇总销售、成本和毛利等指标。
4-customer-segmentation：客户分群（特征工程、标准化、聚类、评价指标）。
5-sale-predict：销售预测（时间序列/回归模型、训练、评估、预测流水线）。
6-NLP：评论与投诉文本处理（预处理、情感分析、主题建模、关键句抽取）。
7-RAG+LLM：基于检索增强生成（RAG）与 LLM 的问答/报告自动化实验。
8-promo-effect：促销效果分析（A/B、时间窗口、归因、指标计算）。
9-review-complaint-overview：评论与投诉的汇总分析、趋势与问题聚类。
```

## 各个文件内部的功能特性

### 0-database-init

* 目的：定义 ORM 表、初始化数据库、插入测试数据以驱动后续分析与建模。
* 关键脚本（建议按顺序运行）：

  * `data_sheet_create_0_1.py`：定义表结构并创建所有表（首次必须运行）。
  * `insert_product_info_data.py`：生成并插入 ProductInfo（商品信息）。
  * `insert_store_info_data.py`：解析 rayban-store 的文本并插入 StoreInfo（门店）。
  * `insert_store_info_data_step2.py`：处理 lencrafter-store 文本并插入（第二类门店数据）。
  * `insert_promotion_activity_data.py`：插入 PromotionActivity（促销事件）。
  * `insert_customer_info_data.py`：生成并插入 CustomerInfo（客户数据）。
  * `insert_order_data.py`：生成并插入 Order 与 OrderItem（订单）。这些依赖 CustomerInfo、ProductInfo，且可关联 PromotionActivity。
  * `insert_customer_complaint_and_customer_review_data_v4_real_data_only_English.py`： 插入客户投诉和客户评论的数据。
  * `insert_competitor_info_data.py`：插入竞争者的数据

### 1-data-collect

* 目的：从原始文本/PDF/日志抓取并转换为结构化中间文件或 parquet。
* 关键脚本：

  * `data-collect-from-pdf.py`：从 PDF 提取门店/商品/评论文本（需按脚本注释安装依赖，如 pdfplumber）。
  * `sort_data.py`：对抓取结果排序或合并。
  * `insert_storecount_headers.py`：生成或插入表头信息（按需要）。

### 2-data-validate

* 目的：校验所有表的数据质量（缺失、异常、字段范围、外键约束）。
* 关键 notebook：
  * `countryname_validate.ipynb`：国家/地区名称标准化。
  * 各类 `*-data-validate.ipynb`（customer、order、product 等）：每张表一份校验笔记本，包含统计摘要、异常样例、修正建议。

### 3-data-aggregate

* 目的：把原始明细表聚合为用于分析和建模的特征表（按产品、客户、时间窗口等）。
* 典型 Notebook/Scripts：

  * `3-1-data-aggregate.ipynb`：总体聚合流程示例。
  * `3-2-cal-sale-amount-by-product.ipynb`：按产品计算销售金额。
  * `3-2-cal-sale-amount-by-timeline.ipynb`：按时间线（月/季度/年/客户聚类/店铺/产品）聚合。
  * `3-3-cal-product-cost-and-gross-margin-*.ipynb`：计算成本与毛利，按客户/订单/产品/月份等维度。
  * `3-4-cal-AOV-per-*.ipynb` : 按（月/季度/年/客户）计算AOV
  * `3-5-cal-sale-qty-by-*.ipynb` : 按（月/季度/年/客户聚类/店铺/产品/地区）计算销售数量
  * `3-6-cal-customer-quantity.ipynb` ：计算客户数量
  * `3-7-cal-product-customer-store-type_v2.ipynb` ： 计算客户店铺类型
  * `3-8-cal-order-status.ipynb` : 统计订单类型的数量分布
* 输出：聚合后的 Parquet（特征表），供 `4-`、`5-` 使用。



### 4-customer-segmentation

  * 目的：对客户进行分群（RFM、行为特征、聚类、分层）。
  * 主要内容：

    * 特征工程脚本（RFM 指标、复购率、平均客单价等）（`4-1-customer-segmentation-v3-k=5.ipynb`）：

      * 从PostgreSQL数据库用 SQL 提取并计算 RFM（recency、frequency、monetary）、复购率、平均客单价、购买品类比例（镜架/镜片/AI/太阳镜）、促销参与指标等特征。然后，合并特征表并筛选有购买行为客户；处理缺失值与时间字段（转天数）；对数值特征填充或替换后标准化。
    * 标准化、降维（PCA）、聚类（KMeans）、簇分析与可视化（`4-1-customer-segmentation-v3-k=5.ipynb`）:

      * 使用 StandardScaler 标准化后，用 PCA 检查主成分解释率（并用于 2D 可视化）。用 KMeans（示例 k=5）进行聚类，并评估聚类稳定性（多随机种子 ARI、bootstrap 抽样 ARI）及不同 k 的 inertia / silhouette 以辅助选 k。生成每个簇的画像（均值特征、customer_share、revenue_share）并通过 PCA 散点、热力图、雷达图可视化,评估指标（轮廓系数、簇内/簇间差异）。最后，导出带 `cluster` 标签的结果`customerinfo_cluster.parquet`。
    * 将聚类结果写回数据库（`4-2-write-cluster-data-to-data-sheet.ipynb`）：

      * 读取 `customerinfo_cluster.parquet`，将 `cluster` 更新到 `CustomerInfo.customer_hierarchy`。然后，根据映射表将 `cluster` 转为可读 `customer_type`（如 "VIP Loyal Customers"、"Lens Customers" 等），并更新到 `CustomerInfo.customer_type` 数据表，实现聚类结果持久化。
    * 导出聚类报表（`4-3-export-customer-cluster-info.ipynb`）：

      * 从数据库读取 CustomerInfo 及明细表，计算并保存每客户的 RFM 分数、RFM 段、生命周期阶段与流失风险（导出为 2023-2024_customer_cluster_rfm.parquet）。
        按聚类/客户类型聚合计算月度销售指标（销售额、数量、订单数、客户数、AOV、毛利与毛利率），并导出为 2023-2024_customer_cluster_monthly_sale.parquet，用于后续分析与可视化。

### 5-sale-predict
  * 目的：对销售数据进行预测建模，覆盖按 SKU、门店和时间窗口预测销量与销售额的场景。
  * 主要内容：
    * 从 PostgreSQL 中查询订单、商品、客户、促销等表，构造月度销售额数据集
    * 生成时间序列特征：滞后值、滚动均值、增长率、季节特征等，并建立 baseline（如移动均值、加权移动平均、指数加权均值等）
    * 结合促销、地区、品类等业务特征，构造预测特征矩阵
    * 对数据做缺失值处理和数据类型转换，再按时间顺序切分训练集和测试集
    * 训练 LightGBM 、CatBoost 、Prophet回归模型，并用 Optuna 调参
    * 采用 MAE、MAPE 等指标评估模型表现，并做偏差校准
    * 将不同模型与最终融合预测结果做对比，并可视化实际值和预测值
    * 最终输出预测对比结果，保存为 Parquet 文件，方便后续分析或汇报

  * 具体对应的文件：
    * `5-1-sale-amount-monthly-predict-v4-blend.ipynb`：按月销售金额预测
    * `5-2-sale-qty-monthly-predict-v2-blend.ipynb`：按月销量预测
    * `5-3-popular-product-sale-qty-monthly-predict-v2-blend.ipynb`：热门产品按月销量预测
    * `5-4-popular-product-sale-amount-monthly-predict-v3-blend.ipynb`：热门产品按月销售金额预测
    * `5-5-each-customer-cluster-sale-qty-monthly-predict-v2-blend.ipynb`：按客户聚类分组的月销量预测
    * `5-6-each-customer-cluster-sale-amount-monthly-predict-v2-blend.ipynb`：按客户聚类分组的月销售额预测

### 6-NLP
  * 目的：处理 CustomerReview / CustomerComplaint 文本，做情感分析、主题建模、关键句抽取与实体识别。
  * 主要内容：
    * 读取清洗后的评论/投诉数据
    * 文本清洗：去噪、分词、停用词处理、词形还原/词干化、过滤无意义短语、同义词归一、非英文文本翻译等。
    * 文本特征分析：词频统计、TF-IDF + Logistic Regression 分析、VADAR、Textblob、BERT主题建模。
    * 情感分析：规则方法或BERT预训练模型进行情感分类。
    * 关键词/实体抽取：使用keyBert识别并提取关键表达、品牌/产品词、痛点表达等。
    * BERTopic聚类：用 sentence-transformers 加载BERT模型，并用 BERTopic 对积极、消极的文本分别做主题聚类。
    * 结果输出：情感分数、topic 标签、典型案例文本、关键特征、聚类结果、
  * 数据集的选择：看dataset_download_url.txt    
  * BERT模型选择：cardiffnlp/twitter-roberta-base-sentiment-latest、nlptown/bert-base-multilingual-uncased-sentiment、distilbert-base-uncased-finetuned-sst-2-english
  * 解释结果的方案：LIME、Integrated Gradients + transformers_interpret/Captum 
  * python包的使用：nltk（词形还原）、sentence-transformers、BERTopic、torch、transformers、pyarrow（Parquet 读写）、spaCy、langdetect 
  * 具体对应的文件：
    * `6-1-data-extract-from-raw-data1.ipynb`: 从原始数据meta_Amazon_Fashion.parquet中提取不同眼镜商品的内容。
    * `6-2-data-format-convert-from-raw-data.ipynb`: 用于把原始的 Amazon JSONL / CSV 文件转成 Parquet 格式
    * `6-3-data-merge-from-customer-complaints.ipynb`: 合并顾客投诉数据。
    * `6-4-customer-review-data-preprocess-for-NLP-BERT-v2.ipynb`: 对评论文本做 BERT 预处理。
    * `6-4-1-customer-review-cluster-v3.ipynb`: 对客户评论进行BERTopic聚类分析。
    * `6-5-translate-non-english-text.ipynb`: 在Google sheet把客户评论中的非英文文本翻译成英文。
    * `6-6-download-BERT-model.ipynb`:下载 BERT 模型
    * `6-7-convert-BERT-model-file-format.ipynb`:转换 BERT 模型文件（safetensors）格式并保存。
    * `6-8-customer-complaint-data-preprocess-for-NLP-BERT-v4.ipynb`:对投诉文本做 BERT 预处理。
    * `6-8-1-customer-complaint-cluster-v2.ipynb`:对客户投诉进行BERTopic聚类分析。
    * `dataset_download_url.txt`: 数据集下载链接文件。
* 注意：多语言场景需按语言分支处理（英文/中文/其他），避免直接混合训练。

### 7-RAG+LLM
  * 目的：构建检索增强生成（RAG）演示与流水线，基于知识库（聚合表、FAQ、报告等）为业务问题提供检索 + 生成的自动化答案与分析报告。
  * 内容要点：
    * 构建知识库：从聚合表、报表、聚类结果等生成文档片段并建立索引（embeddings + 向量数据库）。
    * 检索策略：定义 chunk 大小、相似度阈值、重排序与召回策略以保证检索质量。
    * 生成与 Prompt 设计：设计 LLM prompts、控制上下文长度与指令模板；对 LLM 输出做去重、事实校验与可信度过滤。
    * 测试 demo 脚本（query → retrieve → generate）。


  * 产出与脚本（项目内对应文件）：
  * 知识构建：
    * `7-1-generate-product-knowledge.ipynb`：从商品信息与销售明细生成关于产品属性、分类与典型销售摘要的知识片段。
    * `7-2-generate-customer-cluster-knowledge-v2.ipynb`：把客户聚类结果和每类画像整理为可检索的文档（群体特征、代表客户与行为洞察）。
    * `7-3-generate-customer-review-complaint-knowledge-ignore.ipynb`：从客户评论与投诉中抽取主题化、去噪后的片段与典型案例用于知识库（可忽略或标记低质量项）。
    * `7-4-1-generate-sale-performance-knowledge.ipynb`：汇总按时间/产品/销售渠道的销售表现指标并生成用于回答业绩类问题的知识段。
    * `7-4-2-generate-customer-sales-predict-knowledge.ipynb`：导出销售预测相关的模型摘要、预测结果与特征重要性作为可检索的预测知识条目。
    * `7-5-generate-store-knowledge.ipynb`：整理门店元数据、地理与业绩概览为门店级知识片段（分店档案与比较视角）。
    * `7-6-generate-promotion-intro.ipynb`：把促销活动的时间、规则与效果摘要化，生成促销说明与易检索的影响要点。
    * `7-7-generate-high-freq-business-rules-and-questions.ipynb`：收集高频业务规则与常见问答，整理成 FAQ 风格的知识条目以支持快速检索与自动回答。
  * 建索引：`7-2-build_index/build-index.ipynb`：
  从指定输入目录读取 JSONL 文件，抽取每条记录的文本字段；用本地的 SentenceTransformer 模型（BAAI_bge_base_en_v15）把文本编码为向量（通过NVIDIA cuda加速），对向量做归一化并使用 FAISS（内积相似度 IndexFlatIP）构建向量索引；将索引和对应的元数据（docs）写入 build_index/ 输出目录。

  * 检索内容：`7-3-retrieval/retrieval-v2-gui.py`：该脚本使用 Python、faiss、torch、sentence-transformers、gradio 和 OpenAI 客户端（用于 DeepSeek API）实现一个基于向量检索的 RAG 演示：它载入已构建的 FAISS 索引与 knowledge_meta.json，用本地 SentenceTransformer 模型将用户查询编码为向量并在索引中检索相似片段（只保留来源包含 customer_cluster 的条目），把检索到的上下文拼成特定格式的 prompt 发给 DeepSeek（通过 OpenAI API 客户端），然后在一个 Gradio GUI 中展示 LLM 的回答和检索结果。
  * 演示成果： `final_output/` 下的示例截图。

### 8-promo-effect

  * 目的：评估促销活动对销售的影响与归因。
  * 分析方法：
    * 前后对比、对照组（店铺/产品层面）、差分中的差分（DiD）。
    * 时间窗口选择、平稳性检测、显著性检验。
    * 可视化（活动期间与基线对比）。
  * 具体对应的文件：`8-1_promo_effect.ipynb.py`
  * 输出：效果估计表、显著性报告、可复现的 notebook。

### 9-review-complaint-overview

  * 目的：从整体上汇总评论与投诉的主题、趋势与关键问题。
  * 包含：
    * 聚合统计（按店、产品、时间段的投诉率/好评率）。
    * 主题模型与问题分类（高频问题列表）。
    * 趋势检测（某问题是否在增长）与告警规则建议。
  * 具体对应的文件：`9-1-review-overview.ipynb.py`
  * 输出：可视化仪表板素材、汇总 parquet、建议改善点清单。

**环境与依赖**
  * Python 3.11+
  * miniconda 26.3.2
  * NVIDIA CUDA 13.3
  * PostgreSQL 17.10+
  * Microsoft Power BI 2.157.879

**数据集**
  * 眼镜产品数据集：从rayban和essilorluxottica官网的公开财报获取
  * 客户评论和投诉文本的数据集：看6-NLP/dataset_download_url.txt
**模型选择**
  * BERT模型选择：cardiffnlp/twitter-roberta-base-sentiment-latest、nlptown/bert-base-multilingual-uncased-sentiment、distilbert-base-uncased-finetuned-sst-2-english
  * LLM选择：deepseek-api
  * 文本编码转换成向量：SentenceTransformer 模型（BAAI_bge_base_en_v15）
**工具与库**
  * 解释结果的方案：LIME、Integrated Gradients + transformers_interpret/Captum 
  * pip包的使用：Python、pandas、SQLAlchemy、psycopg2、scikit-learn（StandardScaler、PCA、KMeans）、matplotlib、seaborn、plotly、numpy、nltk（词形还原）、sentence_transformers、BERTopic、torch、transformers、pyarrow（Parquet 读写）、spaCy、langdetect、faiss、gradio

**部署方法**   
下载项目并且打开文件夹
```bash
git clone <repository-url>
cd eyewear-data-analysis\
```
在miniconda创建并激活虚拟环境
```bash
conda create -n <your-venv-name> python=3.11
conda activate <your-venv-name>
```

安装依赖
```bash
pip install -r requirements.txt
```
创建PostgreSQL数据库
```SQL
CREATE DATABASE "eyewear-data"
OWNER postgres
ENCODING 'UTF8';
```
初始化数据
```bash
python 0-database-init/data_sheet_create_0_1.py
python 0-database-init/insert_product_info_data.py
python 0-database-init/insert_store_info_data.py
python 0-database-init/insert_store_info_data_step2.py
python 0-database-init/insert_promotion_activity_data.py
python 0-database-init/insert_customer_info_data.py
python 0-database-init/insert_order_data.py
```

然后按照文件夹编号从上到下运行ipynb文件

下载power bi后
查看来自的eyewear-data-analysis-dashboard-v3.pbix数据可视化结果

运行 RAG+LLM 程序。
首先准备好你的deepseek api key，写在7-RAG+LLM\7-3-retrieval\api-key.txt里面
然后执行指令
```bash
python .\7-RAG+LLM\7-3-retrieval\retrieval-v2-gui-LangChain.py

```
然后再浏览器里面输入 
http://127.0.0.1:7860
就可以查看到RAG+LLM的Gradio GUI了

## 许可协议

本项目为开源项目，遵循 **Apache 2.0** 许可协议。

## 作者与致谢

Author: Junliang Li
Email: 940747544@qq.com
