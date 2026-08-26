"""ExLlamaV2 模型加载与生成测试脚本（非交互式，使用 ExLlamaV2StreamingGenerator）

用法:
    python test_model.py --model exllamav2-models\\Qwen2-7B-Instruct-4.25bpw --prompt "用一句话介绍自己"
    python test_model.py --model exllamav2-models\\Qwen2.5-Coder-7B-Instruct-5.0bpw --prompt "写一个Python快排函数"
"""
import argparse
import time
import sys

import torch
from transformers import AutoTokenizer
from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Cache, ExLlamaV2Tokenizer
from exllamav2.generator import ExLlamaV2StreamingGenerator, ExLlamaV2Sampler


def parse_args():
    p = argparse.ArgumentParser(description="ExLlamaV2 模型测试")
    p.add_argument("--model", required=True, help="模型目录路径")
    p.add_argument("--prompt", default="用三句话介绍人工智能的发展历史。", help="测试提示词")
    p.add_argument("--max-seq-len", type=int, default=4096)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.8)
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--repetition-penalty", type=float, default=1.05)
    return p.parse_args()


def main():
    args = parse_args()
    if not torch.cuda.is_available():
        print("[错误] 未检测到 CUDA，ExLlamaV2 需要 NVIDIA GPU。")
        sys.exit(1)

    print(f"[1/4] 加载配置: {args.model}")
    config = ExLlamaV2Config(args.model)
    config.arch_compat_overrides()

    print("[2/4] 加载模型权重...")
    t0 = time.time()
    model = ExLlamaV2(config)
    cache = ExLlamaV2Cache(model, max_seq_len=args.max_seq_len, lazy=True)
    model.load_autosplit(cache, progress=True)
    tokenizer = ExLlamaV2Tokenizer(config)
    load_time = time.time() - t0
    print(f"      加载耗时: {load_time:.1f}s")

    vram_used = torch.cuda.memory_allocated() / 1024**3
    vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"      显存占用: {vram_used:.2f} GB / {vram_total:.2f} GB")

    print("[3/4] 构建流式生成器...")
    # 使用 ExLlamaV2StreamingGenerator，不依赖 Flash Attention / paged attention
    generator = ExLlamaV2StreamingGenerator(model=model, cache=cache, tokenizer=tokenizer)
    # 设置停止条件：EOS token
    generator.set_stop_conditions([tokenizer.eos_token_id])
    hf_tokenizer = AutoTokenizer.from_pretrained(args.model)

    # 构造聊天 prompt
    messages = [{"role": "user", "content": args.prompt}]
    prompt = hf_tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)

    sampler = ExLlamaV2Sampler.Settings(
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        token_repetition_penalty=args.repetition_penalty,
    )

    print("[4/4] 流式生成中...")
    print("-" * 60)
    print(f"用户: {args.prompt}")
    print("助手: ", end="", flush=True)

    # 编码 prompt
    input_ids = tokenizer.encode(prompt, add_bos=False, encode_special_tokens=False)
    generator.begin_stream(input_ids, sampler)

    full_text = []
    token_count = 0
    t_gen = time.time()
    while True:
        chunk, eos, _ = generator.stream()
        if chunk:
            print(chunk, end="", flush=True)
            full_text.append(chunk)
            token_count += 1
        if eos:
            break
        if token_count >= args.max_new_tokens:
            break
    gen_time = time.time() - t_gen
    print()
    print("-" * 60)
    tps = token_count / gen_time if gen_time > 0 else 0
    print(f"生成耗时: {gen_time:.1f}s | tokens: {token_count} | 速度: {tps:.1f} tokens/s")
    print("\n✅ 测试通过！模型加载和生成均正常。")


if __name__ == "__main__":
    main()
