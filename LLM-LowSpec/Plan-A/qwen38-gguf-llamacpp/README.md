# Qwen3.8-27B · GGUF + llama.cpp 轻量部署

> 思路：**换推理引擎**（不依赖 AirLLM 的逐层流式），用 llama.cpp 把量化后的整模型常驻内存
> （RAM+VRAM 混合），相比 AirLLM≈0.025 tok/s，实测可达 **~2.4–2.5 tok/s（约 100x）**。
>
> 本项目为**独立自包含**项目（引擎 + 模型均内置，不依赖任何外部目录），彻底摆脱 AirLLM 的逐层流式方案。

---

## 一、目录结构

```
D:\A_BDBS\LLM-LowSpec\Plan-A\qwen38-gguf-llamacpp\
├── models\
│   └── Qwen3.8-27B-UD-Q3_K_XL.gguf   # 12.2 GB 量化模型（Unsloth Dynamic V3.0 Q3_K_Large）
├── llama\
│   └── bin\                          # llama.cpp b10472 CUDA 12.4 版
│       ├── llama-cli.exe             # 命令行对话
│       ├── llama-server.exe          # OpenAI 兼容 HTTP 服务（含内置网页）
│       └── llama-bench.exe           # 基准测试
└── README.md
```

## 二、模型文件

- 来源：HuggingFace 仓库 `unsloth/Qwen3.8-27B-GGUF`
- 文件：`Qwen3.8-27B-UD-Q3_K_XL.gguf`（约 12.2 GB，`Q3_K_Large`）
- 架构：`qwen35`，27.32B 参数，原生多模态（纯文本无需 mmproj 视觉投影）
- 重下方式（官方镜像均可）：
  ```bash
  # HuggingFace
  curl -L -o models/Qwen3.8-27B-UD-Q3_K_XL.gguf ^
    "https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-UD-Q3_K_XL.gguf"
  # 国内镜像（hf-mirror）
  curl -L -o models/Qwen3.8-27B-UD-Q3_K_XL.gguf ^
    "https://hf-mirror.com/unsloth/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-UD-Q3_K_XL.gguf"
  ```

## 三、运行方式

路径约定：
- `GGUF= models\Qwen3.8-27B-UD-Q3_K_XL.gguf`
- `BIN= llama\bin`
- `NGL= 33`（GPU offload 层数，本机 RTX4060 8G 最优值，见"调优"）

### 1. 命令行单次问答
```bat
%BIN%\llama-cli.exe -m %GGUF% -ngl %NGL% -p "请用一句话解释什么是人工智能AI。"
```

### 2. 命令行交互对话
```bat
%BIN%\llama-cli.exe -m %GGUF% -ngl %NGL% -cnv
```

### 3. 启动 HTTP 服务（OpenAI 兼容，可被任何 GUI/代码调用）
```bat
%BIN%\llama-server.exe -m %GGUF% -ngl %NGL% --port 8080
```
- OpenAI 兼容接口：`http://127.0.0.1:8080/v1/chat/completions`
- 内置简单网页：浏览器打开 `http://127.0.0.1:8080/`
- 调用示例：
  ```bash
  curl http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" \
    -d '{"model":"qwen3.8","messages":[{"role":"user","content":"你好"}]}'
  ```

### 4. 基准测试
```bat
%BIN%\llama-bench.exe -m %GGUF% -ngl %NGL% -p 32 -n 32
```

## 四、调优 & 性能

本机实测（RTX 4060 8G + 16G RAM，CPU=Alderlake）：

| offload 层数 (-ngl) | 生成 tg32 | 提示处理 pp32 | 说明 |
|---|---|---|---|
| **33** | **2.40 t/s** | 19.43 t/s | **最优**，CPU/GPU 混合 |
| 45 | 1.77 t/s | 10.19 t/s | |
| 999（全 offload） | 0.98 t/s | 14.59 t/s | 12.2GB 塞不进 8G 显存，反而慢 |

要点：
- 12.2GB 模型可常驻 16GB RAM，无需逐层流式，这是比 AirLLM 快 ~100x 的根本原因。
- **不要全 offload**：8G 显存装不下 12.2GB；`-ngl 33` 附近是甜点。
- 若要更省显存/更高吞吐，可改 `-ngl 24~30` 或降低并发；若图高精度，下更大 GGUF（Q4_K_XL ~17.9GB，需 24GB RAM，本机 16GB 偏紧）。

## 五、GUI 说明

**llama.cpp 本身是命令行/HTTP 工具，不自带桌面 GUI。** 但它内置了：
- `llama-server` 根路径的一个**极简网页对话界面**（浏览器即可用，无需安装）。
- OpenAI 兼容 API，可对接任意第三方 GUI 客户端（见下）。

若想要更完整的图形界面，可选用以下**外部客户端**（任选其一，都只是前端，内核仍是 llama.cpp；已评估占用小、对 8G/16G 机器友好）：
- **LM Studio**：自带模型下载与聊天 GUI，直接选 GGUF 文件。
- **Ollama** + **Open WebUI**：Ollama 做后端拉模型，Web 界面聊天。
- **Jan / KoboldCPP**：轻量单机 GUI，链接到本机或 Ollama。
- **AnythingLLM**：把本地模型接入知识库对话。

⚠️ 这些 GUI 都不是 llama.cpp 内置的额外功能，而是外部程序；本项目当前最轻的方式就是 `llama-server` 打开内置网页。

## 六、精度 / 体积权衡

| GGUF 版本 | 体积 | 建议 |
|---|---|---|
| IQ2_XXS | ~9.0 GB | 尝鲜/最省 |
| **UD-Q3_K_XL（当前）** | **~12.2 GB** | **16GB 机器甜点，本机采用** |
| UD-Q4_K_XL | ~17.9 GB | 精度更高，需 24GB RAM |
| NVFP4 | ~23.4 GB | 需 Blackwell(50 系)，4060 用不了 |

> 注：Unsloth 官方标注 Q3_K_XL ≈13.4GB，本机解压实际占用 ~12.2GB。