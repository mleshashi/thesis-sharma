## ElasticSearch: Indexing and Retrieval for Chart-based Argumentation

### Overview

This folder contains scripts and configurations for indexing, querying, and retrieving text and image embeddings using **Elasticsearch**. Various **dense** and **sparse** retrieval techniques are implemented using **BM25, CLIP, Mistral, and Qwen2 models**. The indexed data includes **charts from Statista and Pew Research**, along with **LLAVA-generated captions**.

---
### Elasticsearch Installation and Setup (Debian/Ubuntu)

This guide provides step-by-step instructions to install and start **Elasticsearch** on Debian-based systems like **Ubuntu**.

#### **Step 1: Import the Elasticsearch PGP Key**
Before installing Elasticsearch, add the official **PGP key**:
```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
```

#### **Step 2: Install Required Dependencies**
Ensure `apt-transport-https` is installed for secure package downloads:
```bash
sudo apt-get install apt-transport-https
```

#### **Step 3: Add the Elasticsearch APT Repository**
Add the Elasticsearch repository to your system sources list:
```bash
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
```

#### **Step 4: Install Elasticsearch**
Update the package index and install Elasticsearch:
```bash
sudo apt-get update && sudo apt-get install elasticsearch
```

#### **Step 5: Enable and Start Elasticsearch Service**
Reload systemd, enable Elasticsearch to start on boot, and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch.service
sudo systemctl start elasticsearch.service
```

#### **Step 6: Check Elasticsearch Service Status**
To verify if Elasticsearch is running:
```bash
sudo systemctl status elasticsearch.service
```

#### **Step 7:  Disable Elasticsearch Security (xpack.security.enabled)***
Open the Elasticsearch Configuration File
```bash
sudo nano /etc/elasticsearch/elasticsearch.yml
```
Add or modify the following lines to:
```yaml
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
```
Restart Elasticsearch
```bash
sudo systemctl restart elasticsearch
```

---

### Usage

- **Indexing**:
  - Open `1ElasticSearch.ipynb` and follow instructions to create indices and mappings.
  - Open `BM25 retrieval.ipynb` and follow instructions to index the text fields (title, caption, and llava_description), and images in base64 format.
  - Open `Embedd-clip.ipynb` and follow instructions to index the images using the CLIP model.
  - Open `Embedd-llava-cont.ipynb` and follow instructions to index the LLAVA-generated textual descriptions using mistral model.
  - Open `Embedd-mistral.ipynb` and follow instructions to index the textual descriptions using mistral model.
  - Open `Embedd-Qwen2.ipynb` and follow instructions to index the textual descriptions using QWEN2 model.

---

### Repository Structure

#### **1. 1ElasticSearch.ipynb**
- **Purpose:** Initializes an **Elasticsearch** index named `"documents"`, defining custom **text analyzers** and **dense vector fields**.
- **Key Features:**
  - Sets up **custom English text analysis**.
  - Creates fields for **title, content, Base64-encoded images, and embeddings (Qwen2, Mistral, CLIP, and LLAVA)**.
  - Verifies the existence of indices and retrieves their sizes.
  - Updates mappings dynamically by adding new embedding fields (optional step).

#### **2. BM25 retrieval.ipynb**
- **Purpose:** Implements **BM25 retrieval** to fetch relevant documents from Elasticsearch based on text queries.
- **Key Features:**
  - Preprocesses and indexed **title, caption, and LLAVA descriptions**.
  - Uses **BM25 scoring** to rank documents based on query relevance.
  - Retrieves **top-ranked documents** along with Base64-encoded images.

#### **3. Embedd-Qwen2.ipynb**
- **Purpose:** Indexes text embeddings using the **Qwen2 model** and performs similarity-based retrieval.
- **Key Features:**
  - Loads **Qwen2-7B-instruct** with **4-bit quantization**.
  - Generates **dense text embeddings** and indexed.
  - Performs **cosine similarity-based search** in Elasticsearch.

#### **4. Embedd-clip.ipynb**
- **Purpose:** Indexes **image embeddings** using **OpenAI's CLIP model** and performs image-to-text retrieval.
- **Key Features:**
  - Generates **image embeddings** using CLIP.
  - Retrieves **relevant images** for a given **text query**.

#### **5. Embedd-llava-cont.ipynb**
- **Purpose:** Indexes **LLAVA-generated textual descriptions** using **Mistral-7B**.
- **Key Features:**
  - Cleans and processes **LLAVA descriptions**.
  - Loads **Mistral-7B-Instruct** with **quantization**.
  - Generates **embeddings for LLAVA-text** and indexed.
  - Performs **cosine similarity-based search** in Elasticsearch.

#### **6. Embedd-mistral.ipynb**
- **Purpose:** Indexes text embeddings using **Mistral-7B** for dense retrieval.
- **Key Features:**
  - Loads **Mistral-7B-Instruct** with **quantization**.
  - Generates **dense text embeddings** and indexed.
  - Performs **cosine similarity-based search** in Elasticsearch.

#### **7. dataProcessor.py**
- **Purpose:** Handles data processing tasks, including **text cleaning, metadata extraction, and correction**.
- **Key Features:**
  - Loads **Statista and Pew datasets**.
  - Performs **text normalization and misinterpretation correction**.
  - Prepares structured data for indexing.

#### **8. QuantizeMistral.ipynb**
- **Purpose:** Testing of **quantization techniques** to optimize the **Mistral model** for efficient inference.

#### **9. QuantizeQwen2.ipynb**
- **Purpose:** Tests **quantized Qwen2-7B** model for retrieval and similarity computation.

---
