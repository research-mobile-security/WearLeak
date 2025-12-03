
# Detecting Privacy Non-Compliance in Wearable Apps via Knowledge Graphs and LLMs (aka WearLeak)


## 1. Citation

If you use WearLeak results, please cite the following information. Thank you.
### Paper Link [MetaLeak on IEEE Xplore](https://ieeexplore.ieee.org/document/11257567)
```bibtex
@INPROCEEDINGS{11257567,
  author={Nguyen, Tran Thanh Lam and Carminati, Barbara and Ferrari, Elena},
  booktitle={2025 21th International Conference on Wireless and Mobile Computing, Networking and Communications (WiMob)}, 
  title={Detecting Privacy Non-Compliance in Wearable Apps via Knowledge Graphs and LLMs}, 
  year={2025},
  volume={},
  number={},
  pages={1-7},
  keywords={Wireless communication;Privacy;Large language models;Knowledge graphs;Telecommunication traffic;Safety;Security;Biomedical monitoring;Wearable devices;Standards;Wearable apps;Privacy;Large Language Models (LLM);GraphRAG},
  doi={10.1109/WiMob66857.2025.11257567}}

```

## 2. Introduction
This is the source code of the research **"Detecting Privacy Non-Compliance in Wearable Apps via Knowledge Graphs and LLMs (aka WearLeak)"** project.
The **WearLeak** system is used to investigate whether Wearable apps (WearOS) send sensitive metadata.

Threat model illustrated as figure below
<img src="https://github.com/research-mobile-security/WearLeak/blob/main/project-image/wearable-ecosystem-new.png">

## 3. System architecture

**WearLeak** combines hybrid analysis based on **[MetaLeak's](https://github.com/research-mobile-security/MetaLeak)** framework with LLMs (GraphRAG and Few-shot learning) to (1) identify third-party services that the app integrates with and (2) summarize the app's sent-out traffic, thereby identifying privacy non-compliance when compared to the data safety declared by the app developer.

**WearLeak** consists of four stage, as illustrated in the Figure below, including:

- **Stage 1**: Static Analysis
- **Stage 2**: Building Knowledge Graph
- **Stage 3**: Dynamic Analysis
- **Stage 4**: Sent-out Traffic Summarization 

<img src="https://github.com/research-mobile-security/WearLeak/blob/main/project-image/figure-architecture.png">


