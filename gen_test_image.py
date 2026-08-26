"""生成测试图片供 Qwen2-VL 视觉模型测试使用"""
from PIL import Image, ImageDraw, ImageFont
import os

# 创建 640x480 的彩色图片
img = Image.new("RGB", (640, 480), color=(135, 206, 235))  # 天蓝色背景
draw = ImageDraw.Draw(img)

# 画一个红色矩形（房子主体）
draw.rectangle([200, 200, 440, 400], fill=(220, 50, 50), outline=(0, 0, 0), width=2)

# 画三角形屋顶
draw.polygon([(180, 200), (460, 200), (320, 100)], fill=(80, 80, 80), outline=(0, 0, 0))

# 画门
draw.rectangle([290, 300, 350, 400], fill=(101, 67, 33), outline=(0, 0, 0), width=2)

# 画窗户
draw.rectangle([230, 240, 280, 290], fill=(173, 216, 230), outline=(0, 0, 0), width=2)
draw.rectangle([360, 240, 410, 290], fill=(173, 216, 230), outline=(0, 0, 0), width=2)

# 画太阳
draw.ellipse([500, 50, 580, 130], fill=(255, 215, 0), outline=(0, 0, 0), width=2)

# 画草地
draw.rectangle([0, 400, 640, 480], fill=(34, 139, 34))

# 添加文字
try:
    font = ImageFont.truetype("arial.ttf", 24)
except OSError:
    font = ImageFont.load_default()
draw.text((220, 430), "A Red House", fill=(255, 255, 255), font=font)

out_path = os.path.join(os.path.dirname(__file__), "test_image.png")
img.save(out_path)
print(f"测试图片已生成: {out_path}")
print(f"图片尺寸: {img.size}")
