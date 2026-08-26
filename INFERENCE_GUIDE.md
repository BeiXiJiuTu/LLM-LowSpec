# 本地推理引擎完整使用指南

> 部署路径：`D:\A_BDBS`
> 硬件：NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM) + 驱动 610.62
> 系统：Windows + PowerShell

---

## 引擎概览

当前部署了 **2 个推理引擎**，共可使用 **4 个模型**。

| 引擎 | 界面形式 | 支持模型 | 速度 | 易用性 |
|------|---------|---------|------|--------|
| **TextGen** (ExLlamaV3) | Web UI + API | 全部 4 个模型 (EXL2 + GGUF) | ⚡ 快 (30+ t/s) | ⭐⭐⭐⭐⭐ |
| **llama.cpp** | 终端 + Web UI + API | Qwen3.6-35B GGUF | 🐢 中等 (7 t/s) | ⭐⭐⭐ |

### 模型清单

| 模型 | 格式 / 量化 | 体积 | 推理引擎 | 作用 |
|------|------------|------|---------|------|
| **Qwen2-7B-Instruct** | EXL2 4.25 bpw | ~5 GB | TextGen (ExLlamaV3) | 通用中文对话、问答、写作 |
| **Qwen2.5-Coder-7B-Instruct** | EXL2 5.0 bpw | ~5.5 GB | TextGen (ExLlamaV3) | 代码生成、补全、调试（~37 t/s） |
| **Qwen2-VL-7B-Instruct** | EXL2 4.0 bpw | ~5 GB | TextGen (ExLlamaV3) | 图文多模态：图像理解、OCR |
| **Qwen3.6-35B-A3B-Uncensored** | GGUF IQ3_M (3.66 bpw) | 14.4 GB | TextGen (llama.cpp) / llama.cpp | MoE 大模型（35B/3B 激活），无审查，思考模式 |

---

## 一、TextGen（Web UI / 推荐）

TextGen 是功能最全的推理界面，通过 ExLlamaV3 加载 EXL2 模型，通过 llama.cpp 加载 GGUF 模型。

### 1.1 启动方式

```powershell
cd D:\A_BDBS\textgen\textgen-4.9

# 双击启动（自动打开浏览器）
.\textgen.bat

# 自定义端口
.\textgen.bat --port 8080
```

启动后自动打开浏览器：`http://127.0.0.1:7860`

### 1.2 加载 EXL2 模型（Qwen2 / Qwen2.5-Coder / Qwen2-VL）

1. 启动后点击顶部 **Model** 标签
2. **Model loader** 下拉框选择 `ExLlamav3_HF`
3. 模型列表选择模型目录（如 `Qwen2-7B-Instruct-4.25bpw`）
4. 推荐参数：
   - **ctx-size**: `4096`
   - **cache-type**: `fp16`
5. 点击 **Load**

### 1.3 加载 GGUF 模型（Qwen3.6-35B）

1. **Model loader** 下拉框选择 `llama.cpp`
2. 模型列表选择 `Qwen3.6-35B-A3B-IQ3_M`
3. 推荐参数：
   - **gpu-layers**: `12`
   - **ctx-size**: `8192`
   - **threads**: `6`
4. 点击 **Load**

### 1.4 功能使用

| 功能 | 操作方式 |
|------|---------|
| **聊天** | Chat 标签 → 输入消息 → Generate |
| **上传图片** | 聊天框附件按钮（Qwen2-VL 模型） |
| **上传文件** | 拖拽 PDF/docx/txt 到聊天框 |
| **笔记本模式** | Notebook 标签 → 自由文本续写 |
| **API 调用** | 自动启用，`http://127.0.0.1:5000/v1`，OpenAI 兼容 |
| **切换模型** | Model 标签 → 选新模型 → Load（自动卸载旧的） |
| **参数调整** | Parameters 标签 → 温度、top-p、重复惩罚等 |
| **会话管理** | Session 标签 → 保存/加载对话历史 |

### 1.5 API 调用示例

```powershell
curl.exe -X POST http://127.0.0.1:5000/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d '{\"model\":\"Qwen2-7B-Instruct-4.25bpw\",\"messages\":[{\"role\":\"user\",\"content\":\"写一首诗\"}],\"max_tokens\":300}'
```

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:5000/v1", api_key="not-needed")
resp = client.chat.completions.create(
    model="Qwen2-7B-Instruct-4.25bpw",
    messages=[{"role": "user", "content": "写一首诗"}],
    max_tokens=300,
)
print(resp.choices[0].message.content)
```

### 1.6 TextGen 使用技巧

| 技巧 | 说明 |
|------|------|
| **首次启动慢** | 需 10-30 秒初始化，属正常现象 |
| **EXL2 vs GGUF** | 7B 模型用 ExLlamav3_HF（快），35B 用 llama.cpp（大但慢） |
| **显存管理** | 一次只加载一个模型；切换时自动卸载 |
| **代码生成** | Qwen2.5-Coder 设 `temperature 0.3` 更准确 |
| **创意写作** | Qwen2-7B 设 `temperature 0.9, top_p 0.95` 更有创意 |
| **避免重复** | 若输出重复，提高 `repetition_penalty 1.1` |
| **Qwen2-VL** | 加载后可在聊天中上传图片，进行图文对话 |
| **预设模板** | Parameters 标签可保存采样参数预设 |

---

## 二、llama.cpp（终端 / Web UI / API）

### 2.1 命令行对话

```powershell
cd D:\A_BDBS

# 单次问答
.\llama.cpp\llama-cli.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -p "你好，请用一句中文介绍你自己。" `
  -n 200 -ngl 12 -t 6 --simple-io

# 交互对话（推荐）
.\llama.cpp\llama-cli.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -ngl 12 -t 6 -c 8192 --color
```

**交互命令：** `/exit` 退出 · `/clear` 清空历史 · `/regen` 重新生成

**关键参数：**

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `-m` | 必填 | 模型文件路径 |
| `-ngl` | 12 | GPU offload 层数（0=纯CPU，越多越快但占显存） |
| `-t` | 6 | CPU 线程数 |
| `-c` | 8192 | 上下文长度 |
| `-n` | 200-2000 | 最大生成 token 数 |
| `--temp` | 0.7 | 温度 |

### 2.2 Web UI + API 服务

```powershell
cd D:\A_BDBS

.\llama.cpp\llama-server.exe `
  -m "exllamav2-models\Qwen3.6-35B-A3B-IQ3_M\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf" `
  -ngl 12 -t 6 -c 8192 `
  --host 127.0.0.1 --port 8080
```

**访问方式：**
- **Web UI**：浏览器打开 `http://127.0.0.1:8080`
- **API**（OpenAI 兼容）：`http://127.0.0.1:8080/v1`

### 2.3 llama.cpp 使用技巧

| 技巧 | 说明 |
|------|------|
| **MoE 优化** | Qwen3.6 是 MoE 模型，CPU 推理也可接受（~7 t/s） |
| **显存平衡** | `-ngl 12` 是 8GB VRAM 的最佳平衡点 |
| **纯 CPU 模式** | 显存不足时用 `-ngl 0`，速度约 2-3 t/s |
| **上下文长度** | 长文档用 `-c 16384`，但占内存更多 |
| **贪心解码** | `--temp 0` 输出最确定，适合代码/事实问答 |
| **停止服务** | `Stop-Process -Name llama-server` |

---

## 三、场景速查表

| 场景 | 推荐引擎 | 操作 |
|------|---------|------|
| 日常中文对话（快） | TextGen | ExLlamav3_HF + Qwen2-7B |
| 写代码（快） | TextGen | ExLlamav3_HF + Qwen2.5-Coder |
| 看图说话 | TextGen | ExLlamav3_HF + Qwen2-VL |
| 高质量长文（无审查） | TextGen / llama.cpp | llama.cpp + Qwen3.6-35B |
| 图形界面聊天 | TextGen | 双击 `textgen.bat` |
| 给应用提供 API | TextGen | 自动启用 `http://127.0.0.1:5000/v1` |
| 独立 API 服务 | llama.cpp | `llama-server.exe --port 8080` |
| 终端快速对话 | llama.cpp | `llama-cli.exe -m ... -ngl 12` |

---

## 四、核心选择建议

- **追求速度** → TextGen + ExLlamav3_HF（7B 模型，30+ t/s）
- **追求质量** → TextGen + llama.cpp（35B 大模型）
- **想要 GUI** → TextGen（双击启动，功能最全）
- **开发者集成** → TextGen API 或 llama.cpp llama-server
- **视觉任务** → TextGen + Qwen2-VL（ExLlamav3_HF 加载，支持图片上传）

---

## 五、常见问题

### TextGen

| 问题 | 解决方案 |
|------|---------|
| 启动后浏览器空白 | 等待首次初始化（约 10-30 秒） |
| localhost 无法访问 | textgen.bat 已设置 `NO_PROXY`，检查系统代理 |
| EXL2 模型加载失败 | 确认 Model loader 选 `ExLlamav3_HF` |
| GGUF 模型加载失败 | 确认 Model loader 选 `llama.cpp` |
| 显存不足 | EXL2: 降低 ctx-size；GGUF: 降低 gpu-layers |
| API 端口 | 默认 5000，用 `--api-port` 修改 |

### llama.cpp

| 问题 | 解决方案 |
|------|---------|
| `cublas64_12.dll not found` | 确认 CUDA runtime DLL 已解压到 `llama.cpp\` 目录 |
| 显存不足 | 降低 `-ngl`（如 `-ngl 6` 或 `-ngl 0` 纯 CPU） |
| 速度太慢 | 增加 `-ngl`；关闭其他 GPU 应用 |
| 输出乱码 | 检查模型文件完整性；尝试 `--temp 0` 贪心解码 |

---

## 六、环境配置

### TextGen 运行环境

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11.4 | exl2-venv 虚拟环境 |
| PyTorch | 2.7.0+cu128 | CUDA 12.8 |
| ExLlamaV3 | 1.2.0+cu128.torch2.7.0 | 预编译 wheel |
| Gradio | 4.37.2+custom.21 | TextGen 定制版 |
| llama.cpp | 0.136.0+cu124 | GGUF 模型支持 |

### textgen.bat 配置说明

textgen.bat 已配置为：
- 使用 `D:\A_BDBS\exl2-venv\Scripts\python.exe` 运行
- 模型目录指向 `D:\A_BDBS\exllamav2-models`
- 设置 `NO_PROXY` 绕过代理访问 localhost
- 自动打开浏览器（`--auto-launch`）
- 启用 API（`--api`）

---

## 七、目录结构

```
D:\A_BDBS\
├── exl2-venv\                          # Python 虚拟环境 (3.11 + torch 2.7 + ExLlamaV3)
├── exllamav2-models\                   # 所有模型文件
│   ├── Qwen2-7B-Instruct-4.25bpw\      # EXL2 通用对话
│   ├── Qwen2.5-Coder-7B-Instruct-5.0bpw\ # EXL2 代码生成
│   ├── Qwen2-VL-7B-Instruct-4.0bpw\    # EXL2 视觉多模态
│   └── Qwen3.6-35B-A3B-IQ3_M\          # GGUF MoE 大模型
├── llama.cpp\                          # llama.cpp 预编译版
│   ├── llama-cli.exe                   # 命令行推理
│   ├── llama-server.exe                # Web UI + API 服务
│   └── *.dll                           # CUDA runtime
├── textgen\textgen-4.9\                # TextGen Web UI
│   ├── textgen.bat                     # 启动脚本（双击即可）
│   ├── app\                            # TextGen 应用代码
│   └── user_data\                      # 用户数据（设置、角色、预设）
├── test_model.py                       # ExLlamaV2 文本脚本（已停用）
├── chat_vision.py                      # ExLlamaV2 视觉脚本（已停用）
├── gen_test_image.py                   # 生成测试图片
├── download_model.py                   # 模型下载脚本
├── USAGE.md                            # 基础使用文档
└── INFERENCE_GUIDE.md                  # 本文档
```

> **注意：** `test_model.py` 和 `chat_vision.py` 基于 ExLlamaV2，已随环境升级到 ExLlamaV3 而停用。请改用 TextGen Web UI 加载模型。
