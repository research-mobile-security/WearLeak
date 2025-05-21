
# WearLeak: Leveraging LLMs to Detect Security and Privacy Violations in Wearable Apps

## 1. Introduction
This is the source code of the research **"WearLeak: Leveraging LLMs to Detect Security and Privacy Violations in Wearable Apps"** project.
The **WearLeak** system is used to investigate whether Wearable apps (WearOS) send sensitive metadata.

Threat model illustrated as figure below
<img src="https://github.com/research-mobile-security/WearLeak/blob/main/project-image/wearable-ecosystem-new.png">

## 2. System architecture

**WearLeak** combines hybrid analysis based on **[MetaLeak's](https://github.com/research-mobile-security/MetaLeak)** framework with LLMs (GraphRAG and Few-shot learning) to (1) identify third-party services that the app integrates with and (2) summarize the app's sent-out traffic, thereby identifying privacy non-compliance when compared to the data safety declared by the app developer.

**WearLeak** consists of four stage, as illustrated in the Figure below, including:

- **Stage 1**: Static Analysis
- **Stage 2**: Building Knowledge Graph
- **Stage 3**: Dynamic Analysis
- **Stage 4**: Sent-out Traffic Summarization 

<img src="https://github.com/research-mobile-security/WearLeak/blob/main/project-image/figure-architecture.png">


