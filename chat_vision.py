"""ExLlamaV2 视觉多模态聊天脚本（适用于 Qwen2-VL-7B-Instruct）

使用 ExLlamaV2DynamicGenerator(paged=False) 原生支持 MRoPE 位置编码，
无需 Flash Attention，适合 Windows 环境。

用法:
    .\\exl2-venv\\Scripts\\python.exe chat_vision.py --model exllamav2-models\\Qwen2-VL-7B-Instruct-4.0bpw --image photo.jpg --prompt "描述这张图片"
    .\\exl2-venv\\Scripts\\python.exe chat_vision.py --model exllamav2-models\\Qwen2-VL-7B-Instruct-4.0bpw --image photo.jpg
不传 --prompt 则进入交互模式，可连续提问（同一张图）。
"""
import argparse
import sys

import torch
from PIL import Image
from transformers import AutoTokenizer

from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache,
    ExLlamaV2Tokenizer,
    ExLlamaV2VisionTower,
)
from exllamav2.generator import (
    ExLlamaV2DynamicGenerator,
    ExLlamaV2Sampler,
)

# 图像在 prompt 中的占位符，会被视觉嵌入替换
IMAGE_PLACEHOLDER = "<image>"


def parse_args():
    p = argparse.ArgumentParser(description="ExLlamaV2 视觉多模态聊天 (Qwen2-VL)")
    p.add_argument("--model", required=True, help="模型目录路径")
    p.add_argument("--image", required=True, help="输入图片路径")
    p.add_argument("--prompt", default=None, help="一次性提问; 不传则进入交互模式")
    p.add_argument("--max-seq-len", type=int, default=4096, help="最大上下文(图像token较多，建议4096+)")
    p.add_argument("--max-new-tokens", type=int, default=1024, help="单轮最大生成token数")
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.8)
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--repetition-penalty", type=float, default=1.05)
    return p.parse_args()


def load_vlm(args):
    """加载文本模型 + 视觉塔 + tokenizer + 动态生成器

    使用 ExLlamaV2DynamicGenerator(paged=False)，原生支持 MRoPE，
    且不需要 Flash Attention（paged 模式才需要）。
    """
    config = ExLlamaV2Config(args.model)
    config.arch_compat_overrides()

    # 1. 文本模型
    model = ExLlamaV2(config)
    cache = ExLlamaV2Cache(model, max_seq_len=args.max_seq_len, lazy=True)
    model.load_autosplit(cache, progress=True)
    tokenizer = ExLlamaV2Tokenizer(config)

    # 2. 视觉塔(含投影层)
    vision_tower = ExLlamaV2VisionTower(config)
    vision_tower.load(progress=True)

    # 3. 动态生成器 (paged=False 不需要 Flash Attention)
    generator = ExLlamaV2DynamicGenerator(
        model=model,
        cache=cache,
        tokenizer=tokenizer,
        paged=False,
    )

    # 4. HF tokenizer 仅用于套用 Qwen2-VL 聊天模板
    hf_tokenizer = AutoTokenizer.from_pretrained(args.model)

    print(f"\n[已加载] {args.model}")
    print(f"[显存] {torch.cuda.memory_allocated() / 1024**3:.2f} GB / "
          f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB\n")
    return model, cache, tokenizer, vision_tower, generator, hf_tokenizer


def build_prompt(hf_tokenizer, user_text):
    """构造聊天 prompt，图像占位符放在用户消息开头"""
    content = f"{IMAGE_PLACEHOLDER}\n{user_text}"
    messages = [{"role": "user", "content": content}]
    return hf_tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)


def generate_response(generator, model, tokenizer, vision_tower, prompt, image, args):
    """生成回复（视觉多模态）

    使用 generator.generate() 高层 API，内部自动处理 MRoPE 位置编码、
    indexed_embeddings 注入、prefill 和生成。embeddings 参数为 list[list]，
    外层对应 batch，内层为每个 prompt 的嵌入列表。
    """
    sampler = ExLlamaV2Sampler.Settings(
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        token_repetition_penalty=args.repetition_penalty,
    )

    # 计算图像嵌入
    mme = vision_tower.get_image_embeddings(
        model, tokenizer, image, text_alias=IMAGE_PLACEHOLDER
    )

    # 使用 generate 高层 API（非流式，简单可靠）
    # generate() 内部会对单 prompt 自动包裹一层 list，所以这里传 [mme]
    completion = generator.generate(
        prompt=prompt,
        max_new_tokens=args.max_new_tokens,
        gen_settings=sampler,
        stop_conditions=[tokenizer.eos_token_id],
        add_bos=False,
        encode_special_tokens=True,
        embeddings=[mme],
        completion_only=True,  # 只返回生成的部分，不包含 prompt
    )
    return completion


def main():
    args = parse_args()
    if not torch.cuda.is_available():
        print("[错误] 未检测到 CUDA，ExLlamaV2 需要 NVIDIA GPU。")
        sys.exit(1)

    # 读取图片
    try:
        image = Image.open(args.image).convert("RGB")
    except Exception as e:
        print(f"[错误] 无法读取图片 {args.image}: {e}")
        sys.exit(1)

    model, cache, tokenizer, vision_tower, generator, hf_tokenizer = load_vlm(args)

    print("=" * 60)
    print(f"ExLlamaV2 视觉聊天已就绪 (图片: {args.image})")
    print("=" * 60)

    if args.prompt:
        # 一次性模式
        prompt = build_prompt(hf_tokenizer, args.prompt)
        print("助手: ", end="", flush=True)
        response = generate_response(generator, model, tokenizer, vision_tower, prompt, image, args)
        print(response)
        return

    # 交互模式：同一张图连续提问
    while True:
        try:
            user_input = input("\n用户: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        if not user_input:
            continue
        if user_input == "/exit":
            print("再见!")
            break

        prompt = build_prompt(hf_tokenizer, user_input)
        print("助手: ", end="", flush=True)
        response = generate_response(generator, model, tokenizer, vision_tower, prompt, image, args)
        print(response)


if __name__ == "__main__":
    main()
