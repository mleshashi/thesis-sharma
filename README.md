# Master's Thesis: Statistics Retrieval for Arguments

## Abstract

This thesis introduces the task of chart retrieval for arguments and a first
approach to it based on Retrieval-Augmented Generation (RAG). Given a
user query, the task is to retrieve relevant charts and generate supporting
arguments to address it. This thesis analyzes the effectiveness of the RAG
system in providing users with relevant charts and generated answers to their
queries. The presented system retrieves relevant charts and their descriptions
related to a given query using different retrieval approaches, both sparse and
dense. These retrieval approaches are manually evaluated using the normalized
discounted cumulative gain (NDCG) metric to determine their effectiveness.
The result of the approach yielding the highest NDCG score is then inserted
into a prompt template and submitted to the Large Language Model (LLM),
precisely tailoring the information to answer the given query.

[Link for the report](https://downloads.webis.de/theses/papers/sharma_2024.pdf)
