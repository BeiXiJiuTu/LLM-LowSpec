# 本地大模型部署使用文档

> 部署路径：`D:\A_BDBS`
> 硬件：NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM) + CUDA 12.8 驱动
> 系统：Windows + PowerShell

---

## 一、模型清单与作用

| 模型 | 格式 / 量化 | 体积 | 推理引擎 | 作用 |
|------|------------|------|---------|------|
| **Qwen2-7B-Instruct** | EXL2 4.25 bpw | ~5 GB | ExLlamaV2 | 通用中文对话、问答、写作 |
| **Qwen2.5-Coder-7B-Instruct** | EXL2 5.0 bpw | ~5.5 GB | ExLlamaV2 | 代码生成、补全、调试、技术问答（速度约 37 t/s） |
| **Qwen2-VL-7B-Instruct** | EXL2 4.0 bpw | ~5 GB | ExLlamaV2 | 图文多模态：图像理解、OCR、图表解读 |
| **Qwen3.6-35B-A3B-Uncensored** | GGUF IQ3_M (3.66 bpw) | 14.4 GB | llama.cpp | MoE 大模型（35B 总参/3B 激活），无审查，思考模式，质量更高但速度较慢（~7 t/s） |

模型文件位于 `D:\A_BDBS\exllamav2-models\` 下各子目录。

> 注：`Qwen2-VL-7B-Instruct-6.0bpw` 目录因下载未完成缺少 tokenizer 文件，暂不可用，请使用 `4.0bpw` 版本。

---

## 二、推理引擎对比

| 引擎 | 支持格式 | 优势 | 劣势 |
|------|---------|------|------|
| **ExLlamaV2** | EXL2 | GPU 全量加速，速度快（30+ t/s）；原生支持 MRoPE 多模态 | 仅支持 EXL2 格式；VRAM 占用高 |
| **llama.cpp** | GGUF | 支持 CPU+GPU 混合 offload；MoE 专家可放 CPU；格式通用 | 大模型在 8GB VRAM 上速度较慢 |

**选择建议**：
- 7B 模型优先用 ExLlamaV2（速度快 3-5 倍）
- 35B MoE 大模型必须用 llama.cpp（ExLlamaV2 无法在 8GB VRAM 加载）

---

## 三、推理引擎 1：ExLlamaV2（EXL2 模型）

### 3.1 环境激活

**所有 ExLlamaV2 命令必须先激活虚拟环境：**

```powershell
cd D:\A_BDBS
.\exl2-venv\Scripts\Activate.ps1
```

或直接用虚拟环境的 Python（无需激活）：

```powershell
cd D:\A_BDBS
.\exl2-venv\Scripts\python.exe <脚本名>.py
```

### 3.2 文本对话：Qwen2-7B-Instruct / Qwen2.5-Coder-7B-Instruct

使用 [test_model.py](file:///D:/A_BDBS/test_model.py)：

```powershell
# Qwen2-7B 通用对话
.\exl2-venv\Scripts\python.exe test_model.py `
  --model exllamav2-models\Qwen2-7B-Instruct-4.25bpw `
  --prompt "用三句话介绍量子计算"

# Qwen2.5-Coder 代码生成
.\exl2-venv\Scripts\python.exe test_model.py `
  --model exllamav2-models\Qwen2.5-Coder-7B-Instruct-5.0bpw `
  --prompt "写一个Python快速排序函数，带注释"
```

参数说明：
- `--model`：模型目录路径
- `--prompt`：输入提示词（不传则进入交互模式）

### 3.3 视觉多模态：Qwen2-VL-7B-Instruct

使用 [chat_vision.py](file:///D:/A_BDBS/chat_vision.py)：

```powershell
# 单次问答（指定图片和问题）
.\exl2-venv\Scripts\python.exe chat_vision.py `
  --model exllamav2-models\Qwen2-VL-7B-Instruct-4.0bpw `
  --image test_image.png `
  --prompt "这张图里有什么颜色？"

# 交互模式（不传 --prompt）
.\exl2-venv\Scripts\python.exe chat_vision.py `
  --model exllamav2-models\Qwen2-VL-7B-Instruct-4.0bpw `
  --image photo.jpg

# 生成测试图片
.\exl2-venv\Scripts\python.exe gen_test_image.py
```

参数说明：
- `--model`：模型目录
- `--image`：输入图片路径（支持 PNG/JPG）
- `--prompt`：问题（可选）
- `--max-new-tokens`：最大生成长度（默认 512）

> ⚠️ Qwen2-VL 4.0bpw 量化精度较低，视觉理解质量有限。复杂图像任务建议升级到更高 bpw 版本。

### 3.4 ExLlamaV2 常见问题

| 问题 | 解决方案 |
|------|---------|
| `ModuleNotFoundError: tokenizers` | 运行 `.\exl2-venv\Scripts\python.exe -m pip install tokenizers transformers` |
| 生成乱码/重复 | 检查 `encode_special_tokens=True`，确认 chat template 正确 |
| 显存不足 (OOM) | 7B 模型需 ~6GB VRAM；关闭其他 GPU 应用 |
| Qwen2-VL 纯文本也异常 | DynamicGenerator 对 MRoPE 处理有限，建议优先用图文模式 |

---

## 四、推理引擎 2：llama.cpp（GGUF 模型）

### 4.1 安装位置

llama.cpp 预编译版（b10176, CUDA 12.4）已解压到：`D:\A_BDBS\llama.cpp\`

主要可执行文件：

| 程序 | 作用 |
|------|------|
| `llama-cli.exe` | 命令行对话（交互/单次） |
| `llama-server.exe` | OpenAI 兼容 HTTP API 服务器 |
| `llama-qwen2vl-cli.exe` | Qwen2-VL 视觉模型专用 |
| `llama-mtmd-cli.exe` | 通用多模态 |
| `llama-bench.exe` | 性能测试 |
| `llama-quantize.exe` | 模型量化工具 |

### 4.2 Qwen3.6-35B-A3B 对话（命令行）

**单次问答：**

```powershell
cd D:\A_BDBS
.\llama.cpp\llama-cli.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -p "你好，请用一句中文介绍你自己。" `
  -n 200 `
  -ngl 12 `
  -t 6 `
  --simple-io
```

**交互对话（推荐）：**

```powershell
.\llama.cpp\llama-cli.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -ngl 12 -t 6 -c 8192 --color
```

交互命令：`/exit` 退出 · `/clear` 清空历史 · `/regen` 重新生成

**关键参数说明：**

| 参数 | 含义 | 推荐值 |
|------|------|--------|
| `-m` | 模型文件路径 | 必填 |
| `-p` | 提示词（不传则进入交互模式） | 可选 |
| `-n` | 最大生成 token 数 | 200-2000 |
| `-ngl` | GPU offload 层数（0=纯CPU） | 12（8GB VRAM 平衡值） |
| `-t` | CPU 线程数 | 6-8 |
| `-c` | 上下文长度 | 8192（默认 4096） |
| `--color` | 彩色输出 | 可选 |
| `--simple-io` | 简单 IO（单次模式减少日志） | 可选 |
| `--temp` | 温度（0=贪心，1=随机） | 0.7 |

> 💡 **MoE 模型优化**：Qwen3.6-35B-A3B 是 MoE（总参 35B / 激活 3B），即使 CPU 推理也可接受（~7 t/s）。如需更快，可增加 `-ngl`（但 VRAM 占用上升）。

### 4.3 Qwen3.6-35B-A3B HTTP 服务（推荐用于应用集成）

启动 OpenAI 兼容 API 服务器：

```powershell
.\llama.cpp\llama-server.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -ngl 12 -t 6 -c 8192 `
  --host 127.0.0.1 --port 8080
```

访问方式：
- **Web UI**：浏览器打开 `http://127.0.0.1:8080`
- **API 调用**（OpenAI 兼容）：

```powershell
curl.exe -X POST http://127.0.0.1:8080/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"qwen3.6\",\"messages\":[{\"role\":\"user\",\"content\":\"写一首关于秋天的诗\"}],\"max_tokens\":300}'
```

- **Python 调用**：

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="not-needed")
resp = client.chat.completions.create(
    model="qwen3.6",
    messages=[{"role": "user", "content": "写一首关于秋天的诗"}],
    max_tokens=300,
)
print(resp.choices[0].message.content)
```

### 4.4 性能测试

```powershell
.\llama.cpp\llama-bench.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -ngl 12 -t 6 -p 512 -n 128
```

参考结果（RTX 4060 Laptop + 12 层 offload）：
- Prompt 处理：~4.1 t/s
- Token 生成：~6.9 t/s

### 4.5 llama.cpp 常见问题

| 问题 | 解决方案 |
|------|---------|
| `cublas64_12.dll not found` | 确认 `cudart-llama-bin-win-cuda-12.4-x64.zip` 已解压到 `llama.cpp\` 目录 |
| 显存不足 | 降低 `-ngl`（如 `-ngl 6` 或 `-ngl 0` 纯 CPU） |
| 速度太慢 | 增加 `-ngl`；关闭其他 GPU 应用；确认 `ggml-cuda.dll` 已加载 |
| 上下文超限报错 | 增大 `-c`（如 `-c 16384`），但会占用更多内存 |
| 输出乱码 | 检查模型文件完整性；尝试 `--temp 0` 贪心解码 |

---

## 五、图形界面：TextGen 桌面应用

除命令行外，还安装了 **TextGen**（text-generation-webui 的桌面版），提供 ChatGPT 风格的图形界面，支持聊天、视觉多模态、文件上传、工具调用等。

### 5.1 安装位置

```
D:\A_BDBS\textgen\textgen-4.9\
├── textgen.bat              # 启动脚本（双击即可）
├── app\                     # 应用程序（含 Electron + Python 环境）
└── user_data\
    └── models\              # 模型目录（已链接 GGUF 模型）
        └── Qwen3.6-35B-A3B-IQ3_M\  → 软链接到 exllamav2-models
```

### 5.2 启动方式

**方式 1：桌面 GUI（推荐）**

双击 `D:\A_BDBS\textgen\textgen-4.9\textgen.bat`，或在 PowerShell 执行：

```powershell
cd D:\A_BDBS\textgen\textgen-4.9
.\textgen.bat
```

会打开一个独立窗口，无需浏览器。

**方式 2：浏览器模式（服务器模式）**

```powershell
cd D:\A_BDBS\textgen\textgen-4.9
.\textgen.bat --no-electron --listen
```

然后浏览器打开 `http://127.0.0.1:7860`。

### 5.3 加载模型

1. 启动后在左侧选择 **Model** 标签
2. 在模型列表中选择 `Qwen3.6-35B-A3B-IQ3_M`
3. 调整参数（推荐）：
   - **gpu-layers**: `12`（8GB VRAM 平衡值）
   - **ctx-size**: `8192`
   - **threads**: `6`
4. 点击 **Load** 加载模型
5. 切换到 **Chat** 标签开始对话

### 5.4 TextGen 功能特性

| 功能 | 说明 |
|------|------|
| 聊天对话 | 支持 instruct / chat / chat-instruct 三种模式 |
| 视觉多模态 | 在聊天中上传图片（需多模态模型） |
| 文件附件 | 上传 PDF / docx / txt 文件进行问答 |
| 工具调用 | 模型可调用自定义函数（web 搜索、计算等） |
| API 服务 | 自动提供 OpenAI 兼容 API（端口 7860） |
| 笔记本模式 | 自由文本生成（非对话式） |

### 5.5 TextGen 支持的模型

TextGen 便携版使用 **llama.cpp** 后端，支持 GGUF 格式：

| 模型 | 支持 | 说明 |
|------|------|------|
| Qwen3.6-35B-A3B (GGUF) | ✅ | 已配置，直接在 UI 选择 |
| Qwen2-7B (EXL2) | ❌ | 需完整安装 + ExLlamaV3 后端 |
| Qwen2.5-Coder-7B (EXL2) | ❌ | 同上 |
| Qwen2-VL-7B (EXL2) | ❌ | 同上 |

> 💡 **EXL2 模型继续使用命令行脚本**（第三章），或下载 GGUF 版本放入 `textgen\textgen-4.9\user_data\models\` 即可在 TextGen 中使用。

### 5.6 TextGen 常见问题

| 问题 | 解决方案 |
|------|---------|
| 启动后窗口空白 | 等待首次初始化（约 10-30 秒） |
| 模型加载失败 | 检查 `user_data/models` 下模型文件完整 |
| 显存不足 | 降低 gpu-layers 数值 |
| 想用 API | 启动时加 `--api` 参数，默认端口 7860 |
| 想后台运行 | 用 `--no-electron` 模式，无窗口 |

---

## 六、典型使用场景速查

### 场景 1：日常中文对话
```powershell
.\exl2-venv\Scripts\python.exe test_model.py `
  --model exllamav2-models\Qwen2-7B-Instruct-4.25bpw `
  --prompt "解释一下什么是微服务架构"
```

### 场景 2：写代码
```powershell
.\exl2-venv\Scripts\python.exe test_model.py `
  --model exllamav2-models\Qwen2.5-Coder-7B-Instruct-5.0bpw `
  --prompt "用Python实现一个线程安全的单例模式"
```

### 场景 3：看图说话
```powershell
.\exl2-venv\Scripts\python.exe chat_vision.py `
  --model exllamav2-models\Qwen2-VL-7B-Instruct-4.0bpw `
  --image screenshot.png `
  --prompt "描述这张图片的内容"
```

### 场景 4：高质量长文创作（无审查）
```powershell
.\llama.cpp\llama-cli.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -p "写一篇500字的科幻小说开头" -n 800 -ngl 12 -t 6 --simple-io
```

### 场景 5：提供 API 给其他应用
```powershell
# 启动服务
.\llama.cpp\llama-server.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -ngl 12 -t 6 --host 127.0.0.1 --port 8080

# 另开终端调用
curl.exe http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" `
  -d '{\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}'
```

---

## 七、目录结构

```
D:\A_BDBS\
├── exl2-venv\                          # ExLlamaV2 Python 虚拟环境
├── exllamav2-models\                   # 所有模型文件
│   ├── Qwen2-7B-Instruct-4.25bpw\
│   ├── Qwen2.5-Coder-7B-Instruct-5.0bpw\
│   ├── Qwen2-VL-7B-Instruct-4.0bpw\
│   └── Qwen3.6-35B-A3B-IQ3_M\
├── llama.cpp\                          # llama.cpp 预编译版 (b10176, CUDA 12.4)
│   ├── llama-cli.exe
│   ├── llama-server.exe
│   ├── llama-qwen2vl-cli.exe
│   └── *.dll (CUDA runtime + ggml)
├── textgen\textgen-4.9\                # TextGen 桌面应用 (v4.9, CUDA 12.4)
│   ├── textgen.bat                     # 启动脚本（双击即可）
│   ├── app\                            # Electron + Python 便携环境
│   └── user_data\models\               # 模型目录（含 GGUF 软链接）
├── test_model.py                       # ExLlamaV2 文本模型脚本
├── chat_vision.py                      # ExLlamaV2 视觉模型脚本
├── gen_test_image.py                   # 生成测试图片
├── download_model.py                   # EXL2 模型下载脚本
└── USAGE.md                            # 本文档
```

---

## 八、推理引擎总结

| 引擎 | UI 形式 | 支持模型 | 适合场景 |
|------|---------|---------|---------|
| **ExLlamaV2** | 终端 | 3 个 EXL2 7B 模型 | 快速对话/代码/视觉（30+ t/s） |
| **llama.cpp** | 终端 + Web UI + API | Qwen3.6-35B GGUF | 大模型推理、API 服务 |
| **TextGen** | 桌面 GUI + 浏览器 + API | Qwen3.6-35B GGUF | 图形界面聊天、文件上传、工具调用 |

**快速选择：**
- 想要图形界面 → 双击 `textgen\textgen-4.9\textgen.bat`
- 想要最快速度 → ExLlamaV2 命令行（第三章）
- 想要 API 服务 → llama.cpp `llama-server.exe`（第四章）
- 想要无审查大模型 → Qwen3.6-35B（TextGen 或 llama.cpp）
