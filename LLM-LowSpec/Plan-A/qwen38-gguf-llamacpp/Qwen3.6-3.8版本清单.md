# Qwen3.6 / Qwen3.8 开源版本 + 社区清单（2026-08-25 整理）

> ⚠️ 开源社区无法"穷尽所有"——Qwen3.8-27B 发布 12h 就被社区贡献约 500 个量化版（HF 官方卡口径）。
> 本清单给的是**官方全量 + 主流量化/合并家族 + 各平台**，是权威且可用的完整版。

---

## 一、Qwen3.6（2026-04 发布，Alibaba Qwen 团队）

### 1.1 官方开源权重（Apache 2.0，社区：HuggingFace + 魔搭 ModelScope）
| 模型 | 结构 | 说明 |
|---|---|---|
| `Qwen/Qwen3.6-35B-A3B` | MoE 总35B/激活3B，多模态 | 4/16 开源，编码智能体，262K ctx |
| `Qwen/Qwen3.6-27B` | 稠密 27B，多模态代码特化 | 4/22 开源（~17GB@Q4），SWE-bench Verified 77.2 |
| （未见官方 3.6-FP8 单列） | — | — |

### 1.2 云端闭源（不可本地）
- Qwen3.6-Plus / Qwen3.6-Flash / Qwen3.6-Max-Preview（qwen.ai chat / OpenRouter API）

### 1.3 社区衍生
- **Unsloth AI**：`unsloth/Qwen3.6-35B-A3B-GGUF`、`unsloth/Qwen3.6-27B-GGUF`（HF + 魔搭）
- **bartowski**：Qwen3.6 系列 GGUF（HF）
- **HauhauCS（非审查，Uncensored）**：`Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive`
  - 0/465 拒绝，保留视觉，多量化：`IQ2_M`约13GB / `IQ4_XS`约20GB / `Q4`约22GB / `Q2_K_P`约16GB
  - 平台：Ollama + HuggingFace（3.6 现成的非审查版就是它）
- **Ollama**：聚合官方 + 大量社区量化

---

## 二、Qwen3.8（2026-08 发布，Alibaba Qwen 团队）

### 2.1 官方开源权重（社区：HuggingFace + 魔搭 ModelScope）
| 模型 | 结构 / 许可 | 体积 | 说明 |
|---|---|---|---|
| `Qwen/Qwen3.8-27B` | 稠密27B，Apache 2.0，多模态 | ~55.6GB(BF16) | 8/15 开源，登顶 Hacker News #1 |
| `Qwen/Qwen3.8-27B-FP8` | 上面 + FP8 | 更低 | 8/15 |
| `Qwen/Qwen3.8-2.4T-A95B` | MoE 2.4T/95B激活，仅文本，qwen3.8-max 许可 | ~4.89TB(BF16) | 数据中心级，不可本地 |
| `Qwen/Qwen3.8-2.4T-A95B-FP8` | 上面 + FP8 | ~2.5TB | 数据中心级 |

Qwen3.8-27B 规格：64层（48层 Gated DeltaNet + 16层 Gated Attention），隐层5120，原生262K ctx（YaRN 可扩 ~1M），默认思考模式，内置 MTP 多 token 预测。

### 2.2 云端闭源
- Qwen3.8-Max（API，闭源）

### 2.3 社区衍生 —— Qwen3.8-27B Unsloth Dynamic V3.0 GGUF（平台：HF + 魔搭 + GitCode 镜像）
| 量化文件 | 体积 | 建议（按显存） |
|---|---|---|
| `UD-IQ2_XXS` | ~9.0GB | 8GB 显存极限（能力保留 82.5%）|
| `UD-IQ2_M` | ~9.6GB | 8GB |
| `UD-IQ3_XXS` | ~11.1GB | — |
| `UD-Q3_K_XL` / `Q3_K_M` / `Q3_K_S` | 11.7~13.4GB | **16GB 甜点（本机已部署）✅** |
| `IQ4_XS` / `IQ4_NL` | 14.6~15.7GB | 16GB 上限 |
| `Q4_0/Q4_1` | 15.0~16.3GB | 兼容性最好 |
| `Q4_K_M` / `UD-Q4_K_XL` | 15~17.9GB | 24GB |
| `UD-Q5_K_XL` / `Q5_K_M/S` | 17.9~18.8GB | 24GB |
| `Q6_K` / `UD-Q6_K_XL` | 21~24GB | 32GB |
| `Q8_0` / `UD-Q8_K_XL` | 27~29GB | 32GB+ |
| `BF16`（分卷） | ~50.9GB | 多卡/服务器 |
| `mmproj-F16/BF16.gguf` | ~0.9GB | 多模态视觉（纯文本不需要）|

### 2.4 社区衍生 —— 其它
- **Ollama**：`ollama run qwen3.8`（默认 Q4_K_M ~18GB，发布当天支持）
- **LM Studio**：直接搜索 Qwen3.8-27B 下 GGUF
- **uns*loth NVFP4**：~23.4GB，需 Blackwell(50系)，4060 用不了
- **z-lab**：`z-lab/Qwen3.8-27B-DFlash2`（推测解码草稿模型，魔搭，与 DFlash 相关）
- **Qwen3.8 非审查版**：尚未搜到已确认版本（8 月中旬才开源，越狱版滞后；现有唯一非审查是 3.6 的 HauhauCS）

---

## 三、涉及的开源社区/平台汇总（国内外）

| 社区/平台 | 性质 | 3.6 / 3.8 情况 |
|---|---|---|
| **Hugging Face** | 国际主站，衍生态最全 | 官方 + Unsloth + bartowski + HauhauCS + ~500 量化 |
| **魔搭 ModelScope** | 国内主站 | 官方 + Unsloth NVFP4/GGUF + z-lab DFlash |
| **Ollama** | 一键运行库 | 官方 + 大量社区量化（含 HauhauCS uncensored）|
| **GitCode (hf_mirrors)** | 国内 HF 镜像 | Unsloth GGUF 全量镜像 |
| **hf-mirror.com** | 下载镜像通道 | 本机实际下载所用 |

---

## 四、本机部署对照（RTX 4060 8G + 16G RAM）

- **Qwen3.8-27B + llama.cpp + `UD-Q3_K_XL`（12.2GB）** = 当前实测 ~2.4-2.5 tok/s，`-ngl 33` 最优（详见同目录 `README.md`）
- 若要更小可换 `UD-IQ2_M`（~9.6GB）；要更高精度需 24GB 内存换 `UD-Q4_K_XL`（本机 16GB 偏紧）
- 若要"非审查 + 能本地跑"，可考虑 3.6 的 `Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive:IQ4_XS`（~20GB）或 `IQ2_M`（~13GB）