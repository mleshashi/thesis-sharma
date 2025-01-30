# chart-retrieval-for-arguments

## Repository Structure

This repository contains the implementation of a chart retrieval system for arguments, leveraging Retrieval-Augmented Generation (RAG). The system integrates various retrieval approaches and evaluates them using the NDCG metric. Below is an overview of the repository structure:

### Folders and Files:

#### `.vscode/`
- Contains configuration files for Visual Studio Code.
- Includes settings for debugging and linting.

#### `ChartRetrieval/`
- This folder contains a chart retrieval system.
- With backend (query embeddings, model loading, evaluation).
- And frontend (HTML, CSS, JS) components, integrated into a web application.

#### `ElasticSearch/`
- Contains scripts and configurations for indexing and querying data using Elasticsearch.

#### `Research Papers/`
- Collection of research papers referenced in the project.
- Supports theoretical background and methodologies used.

#### `Additional codes /`
- Topic modeling, data statistics, retrieval results analysis, and generated answer analysis.

#### `dataset/`
- Contains Statista and Pew Research data, LLAVA-generated captions, and the queries.
- Also includes annotated data for each query and processed results from the analysis.

### Credential File:

#### `.gitignore`
- Excludes sensitive files, such as API keys and temporary build artifacts, from version control.

#### `README.md`
- Provides an overview of the project, structure, and usage details.

#### `docker-compose.yml`
- Configuration file for setting up Docker containers.
- Currently the Elasticsearch is not fully functional in Docker yet.

#### `dockerfile`
- Defines the Docker image for running the system.
- Includes dependencies and environment setup.

#### `requirements.txt`
- Lists dependencies required to run the project.

## Installation and Setup

1. Clone the repository:
   ```bash
   git clone https://git.webis.de/code-teaching/theses/thesis-sharma.git
   cd thesis-sharma
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
3. Set up the ElasticSearch engine and configuration for indexing given in folder ElasticSearch

4. Run the system:
   ```bash
   cd ChartRetrieval
   python webapp.py
   ```

## Usage
- The system takes user queries and retrieves relevant charts along with supporting arguments.
- Charts are retrieved using both sparse and dense retrieval methods.
- The best retrieval result is processed by a Large Language Model (LLM) to generate explanations.

## Contributing
- Contributions are welcome. Please submit issues or pull requests with suggested improvements.

