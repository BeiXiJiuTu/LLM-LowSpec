# Third-Party Notices

This project is a **usage guide, deployment record, and collection of helper scripts**
for running large language models locally on low-spec hardware. It does **not**
contain or redistribute the model weights themselves. Models and inference engines
are referenced and orchestrated, but the binaries/weights remain on the user's machine.

Below are the third-party projects referenced by this repository, along with their
license obligations. Where required by the license, the full license text is retained
and a link is provided.

## Inference Engines

### llama.cpp
- Homepage: https://github.com/ggml-org/llama.cpp
- License: **MIT License**
- Copyright (c) 2023-2026 The ggml authors
- Obligation: retain the copyright and permission notice in copies/substantial portions.
- Full license: https://github.com/ggml-org/llama.cpp/blob/master/LICENSE

### FreeToken
- Homepage: https://github.com/FlashML-org/FreeToken
- License: **Apache License 2.0**
- Copyright (c) 2026 FlashML-org and contributors
- Obligation: retain copyright notice, include a copy/link of the Apache-2.0 license;
  state changes made if any; retain NOTICE/attribution.
- Suggested citation (per upstream README):
  ```
  @article{yang2026freetoken,
   title={FreeToken: Efficient Edge-Native MoE Serving with Bandwidth-Adaptive Execution},
   author={Yang, Shuo and Fan, Xiaoze and Pan, Melissa and Xi, Haocheng and Wang, Zhe and Sun, Shanlin and Keutzer, Kurt and Han, Song and Zaharia, Matei and Xu, Chenfeng and Stoica, Ion},
   journal={arXiv preprint arXiv:2608.16157},
   year={2026}
  }
  ```
- Full license: https://github.com/FlashML-org/FreeToken/blob/main/LICENSE

### AirLLM
- Homepage: https://github.com/lyogavin/airllm
- License: **Apache License 2.0**
- Copyright (c) the AirLLM authors
- Obligation: retain copyright notice, include a copy/link of the Apache-2.0 license.
- Full license: https://github.com/lyogavin/airllm/blob/main/LICENSE

## Acknowledgements

- This work was inspired in part by the architectures and ideas in AirLLM and llama.cpp,
  and the engineering analysis covers FreeToken. All analysis is the author's own reading
  of the open-source source code under the respective licenses.

## Model Weights Disclaimer

Model weights referenced in this repository belong to their respective creators/owners
(e.g., Qwen, OpenAI, Google, Meta). This repository does not host, publish, or distribute
any model weights. Users are responsible for obtaining models from official sources under
the models' own terms of use.