"""ExLlamaV2 模型批量下载工具 (httpx 流式下载 + 断点续传)

说明:
- huggingface_hub 的 snapshot_download 在本机下载大文件会卡死(hf-xet CDN 问题),
  改用 httpx 直连 HF resolve URL 流式下载, 实测稳定 4-5 MB/s。
- 支持断点续传: 中断后重新运行会从已下载位置继续。
"""
import os
import time
import httpx
from huggingface_hub import list_repo_files, hf_hub_url

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# 模型配置
# 注意: bartowski 分支名用下划线(如 4_25); turboderp 分支名用点(如 4.0bpw)
# DeepSeek-Coder-V2 无 EXL2 版本且 16B 超出 8GB VRAM, 改用 Qwen2.5-Coder-7B-Instruct
MODELS = [
    {
        "repo_id": "bartowski/Qwen2-7B-Instruct-exl2",
        "revision": "4_25",
        "local_dir": r"D:\A_BDBS\exllamav2-models\Qwen2-7B-Instruct-4.25bpw",
    },
    {
        "repo_id": "bartowski/Qwen2.5-Coder-7B-Instruct-exl2",
        "revision": "5_0",
        "local_dir": r"D:\A_BDBS\exllamav2-models\Qwen2.5-Coder-7B-Instruct-5.0bpw",
    },
    {
        "repo_id": "turboderp/Qwen2-VL-7B-Instruct-exl2",
        "revision": "4.0bpw",
        "local_dir": r"D:\A_BDBS\exllamav2-models\Qwen2-VL-7B-Instruct-4.0bpw",
    },
]

# 不需要的文件(省略以节省空间)
SKIP_FILES = {".gitattributes", ".cache"}
CHUNK_SIZE = 1024 * 1024  # 1 MB
MAX_RETRIES = 6


def fmt_size(b: float) -> str:
    if b >= 1e9:
        return f"{b/1e9:.2f} GB"
    return f"{b/1e6:.1f} MB"


def download_file(repo_id: str, revision: str, filename: str, local_path: str) -> bool:
    """流式下载单个文件, 支持断点续传"""
    url = hf_hub_url(repo_id, filename, revision=revision)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # 断点续传: 已存在则跳过, 部分文件用 Range 续传
    if os.path.exists(local_path):
        print(f"  [跳过] {filename} (已存在)")
        return True

    tmp_path = local_path + ".part"
    have = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0

    for attempt in range(1, MAX_RETRIES + 1):
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            t0 = time.time()
            with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(30.0, read=20.0)) as c:
                with c.stream("GET", url, headers=headers) as r:
                    if r.status_code == 416:  # 已下载完(范围不满足)
                        break
                    r.raise_for_status()
                    # 206=续传成功追加; 200=服务器忽略range, 重新下载
                    if r.status_code == 200:
                        have = 0
                        mode = "wb"
                    else:
                        mode = "ab"
                    total = int(r.headers.get("content-length", 0)) + have
                    downloaded = have
                    last_log = t0
                    with open(tmp_path, mode) as f:
                        for chunk in r.iter_bytes(chunk_size=CHUNK_SIZE):
                            f.write(chunk)
                            downloaded += len(chunk)
                            now = time.time()
                            if now - last_log >= 2.0:
                                pct = downloaded / total * 100 if total else 0
                                spd = (downloaded - have) / (now - t0) / 1e6
                                print(f"  {filename}: {fmt_size(downloaded)}/{fmt_size(total)} "
                                      f"({pct:.0f}%) {spd:.1f} MB/s", end="\r", flush=True)
                                last_log = now
                    have = downloaded
                    print(f"  {filename}: {fmt_size(downloaded)}/{fmt_size(total)} 完成{' ' * 20}")
                    break
        except (httpx.TransportError, httpx.HTTPStatusError) as e:
            print(f"\n  [重试 {attempt}/{MAX_RETRIES}] {filename} 断点({fmt_size(have)}): {type(e).__name__}")
            time.sleep(2 * attempt)
        else:
            break
    else:
        print(f"  [失败] {filename} 重试耗尽")
        return False

    os.replace(tmp_path, local_path)
    return True


def download_model(model_info: dict) -> bool:
    print(f"\n{'=' * 60}")
    print(f"开始下载: {model_info['repo_id']} ({model_info['revision']})")
    print(f"保存到: {model_info['local_dir']}")
    print(f"{'=' * 60}\n")

    try:
        files = list_repo_files(model_info["repo_id"], revision=model_info["revision"])
    except Exception as e:
        print(f"❌ 获取文件列表失败: {e}")
        return False

    files = [f for f in files if f not in SKIP_FILES]
    os.makedirs(model_info["local_dir"], exist_ok=True)

    ok = True
    for fname in files:
        local_path = os.path.join(model_info["local_dir"], fname.replace("/", os.sep))
        if not download_file(model_info["repo_id"], model_info["revision"], fname, local_path):
            ok = False

    if ok:
        print(f"\n✅ 下载完成: {model_info['repo_id']}")
    else:
        print(f"\n❌ 下载不完整: {model_info['repo_id']}")
    return ok


if __name__ == "__main__":
    print("ExLlamaV2 模型批量下载工具 (httpx 直连 huggingface.co)")
    print(f"共 {len(MODELS)} 个模型待下载\n")

    success = 0
    failed = []
    for i, model in enumerate(MODELS, 1):
        print(f"[{i}/{len(MODELS)}] ", end="")
        if download_model(model):
            success += 1
        else:
            failed.append(model["repo_id"])

    print(f"\n{'=' * 60}")
    print(f"下载完成！成功: {success}/{len(MODELS)}")
    if failed:
        print(f"失败: {', '.join(failed)}")
    print(f"{'=' * 60}")
