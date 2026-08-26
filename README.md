# LLM-LowSpec · 低配硬件大模型高效部署

在 **RTX 4060 8G 显存 + 16G 内存**这类低配机器上，高效运行大语言模型（LLM）的
完整工程记录与工具集。含两条实战验证的路线：

| 路线 | 路径 | 引擎 | 模型 | 实测速度 |
|---|---|---|---|---|
| **Plan-A** | `LLM-LowSpec/Plan-A/` | llama.cpp | Qwen3.8-27B (UD-Q3_K_XL) | ~2.4 tok/s |
| **Plan-B** | `LLM-LowSpec/Plan-B/` | FreeToken | gpt-oss-20b (MXFP4) | MoE 跑通 |

<div align="center">

---

### 完整部署全记录（首页展示用）

**[《低配硬件大模型高效部署全记录》 →](低配硬件大模型高效部署全记录.md)**

*RTX 4060 8G 显存 + 16G 内存 · 从 AirLLM 逐层流式到 llama.cpp / FreeToken 跑通 MoE 的
完整工程复盘 · 含 AirLLM / DFlash2 / FreeToken 三大引擎源码级剖析、经验教训与性能实测数据汇总*

---

</div>

## 核心结论

1. **优先"换引擎"，而非"调参"**：AirLLM 逐层流式 ~0.025 tok/s → 换 llama.cpp + GGUF
   整模型驻留 → ~2.4 tok/s（约 100x 提速）。
2. **MoE 是低配硬件跑大模型的出路**，但受**物理内存**硬约束（专家权重需锁进内存，
   默认权限 + 16G 内存是门槛）。
3. **16G 内存往往比 8G 显存更硬**：锁页需 `Lock pages in memory` 权限 + 管理员身份。
4. **量化选型有甜点**：本机 llama.cpp `-ngl 33`（CPU/GPU 混合）优于全 offload。

## 目录结构

```
D:\A_BDBS\
├── LLM-LowSpec\                     # 低配硬件大模型部署总目录
│   ├── Plan-A\                      # llama.cpp + GGUF 路线
│   └── Plan-B\                      # FreeToken + MoE 路线
├── scripts\                          # 辅助脚本（如锁页权限工具）
├── LICENSE
├── THIRD_PARTY_NOTICES.md
└── 低配硬件大模型高效部署全记录.md
```

## 免责声明

> **本仓库是一份"部署指南 + 使用记录 + 脚本集"，不包含任何模型权重。**
>
> 1. 引用的模型（Qwen / OpenAI gpt-oss / Google Gemma 等）及其权重归**各自厂商**所有，
>    需从官方源按其自身条款下载；本仓库不托管、不分发任何权重。
> 2. 引用的推理引擎（llama.cpp / FreeToken / AirLLM）均为**第三方开源项目**，各自
>    遵循其许可证（见 `THIRD_PARTY_NOTICES.md`），请遵守相应版权与引用要求。
> 3. 本仓库中的脚本与文档按 **MIT License** 授权，以 **"AS IS"（现状）** 提供，
>    **无任何明示或暗示担保**。作者不对使用本仓库产生的任何直接或间接损失负责。
> 4. 涉及系统权限修改的脚本（如锁定内存页）请在理解其影响后使用，可自行还原。

## 快速开始

- **Plan-A（llama.cpp）**：见 `LLM-LowSpec/Plan-A/qwen38-gguf-llamacpp/README.md`
- **Plan-B（FreeToken）**：下载桌面端 → 授予锁页权限 → 以管理员运行 → 加载模型
- **锁页权限工具**：`scripts/` 下一键启用/还原

## License

- 本仓库：`LICENSE`（MIT）
- 第三方组件：见 `THIRD_PARTY_NOTICES.md`