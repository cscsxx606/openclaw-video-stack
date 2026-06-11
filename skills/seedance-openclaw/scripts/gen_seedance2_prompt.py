#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seedance 2.0 专用提示词生成器
避免侵权，使用原创描述，符合平台规范
"""

import sys
import argparse
import random

# ============== Seedance 2.0 专用素材库（原创无侵权） ==============

# 古风场景（原创描述）
ANCIENT_SCENES = [
    "云雾缭绕的仙山之巅，青松翠柏环绕",
    "幽静竹林深处，阳光透过竹叶洒落斑驳光影",
    "古代宫殿庭院，雕梁画栋，飞檐翘角",
    "悬崖绝壁之上，云海翻腾，气势磅礴",
    "桃花盛开的山谷，粉色花瓣随风飘落",
    "静谧湖畔，倒映着远山和古建筑",
    "雪山之巅，白雪皑皑，寒风凛冽",
    "古镇街道，青石板路，两旁是木质建筑"
]

# 角色描述（避免具体 IP 名称）
CHARACTERS = [
    "身穿青色长袍的修仙者",
    "一袭白衣的女子，气质出尘",
    "黑衣剑客，眼神凌厉",
    "华服公子，手持折扇",
    "素衣少女，温婉动人",
    "长须老者，仙风道骨",
    "铠甲武士，威风凛凛",
    "紫衣女子，神秘优雅"
]

# 情绪描述（原创）
EMOTIONS = [
    "眼神中透露出坚定与决绝",
    "表情温柔，嘴角微微上扬",
    "眉头紧锁，若有所思",
    "目光深邃，仿佛看透一切",
    "神情冷漠，拒人千里之外",
    "眼中闪烁着泪光，情绪复杂",
    "面带微笑，温暖如春风",
    "表情凝重，气氛紧张"
]

# 原创台词（避免知名 IP）
ORIGINAL_LINES = [
    "这一战，我等你很久了。",
    "从此以后，你我各不相欠。",
    "有些话，再不说就来不及了。",
    "这条路，我自己走。",
    "谢谢你，陪我走过这一程。",
    "记住，永远不要放弃希望。",
    "今日之事，必有今日之果。",
    "若有来生，愿与你再相遇。",
    "这把剑，已经等待太久了。",
    "有些秘密，还是永远不要知道的好。"
]

# 运镜描述（丝滑流畅）
CAMERA_MOVES = [
    "镜头缓慢推进，聚焦人物面部表情",
    "环绕拍摄，展现人物与环境的和谐",
    "镜头缓缓拉远，展现宏大的场景",
    "平稳跟随，记录人物的每一个动作",
    "轻柔摇移，从远景过渡到近景",
    "流畅推进，从环境聚焦到人物",
    "缓慢上升，展现全景画面",
    "自然切换，多个角度展现同一场景"
]

# 光影效果
LIGHTING = [
    "柔和的自然光，营造温馨氛围",
    "侧逆光勾勒人物轮廓，增强立体感",
    "斑驳的光影透过树叶洒落",
    "晨曦的金色光线，温暖而梦幻",
    "黄昏的暖色调，浪漫而唯美",
    "明暗对比强烈，突出戏剧张力",
    "柔和的漫射光，画面干净通透",
    "逆光拍摄，营造梦幻光晕效果"
]

# 色彩风格
COLOR_STYLES = [
    "青绿色调为主，清新自然",
    "暖黄色调，温馨浪漫",
    "冷蓝色调，神秘深邃",
    "低饱和度，电影级质感",
    "高对比度，视觉冲击力强",
    "柔和的莫兰迪色系，高级感",
    "金黄色与青绿色对比，古典韵味",
    "黑白灰为主，极简风格"
]


def generate_seedance2_prompt(topic="古风仙侠", duration=15, ratio="16:9", version=1):
    """
    生成 Seedance 2.0 专用提示词（无侵权）
    
    Args:
        topic: 主题类型
        duration: 时长
        ratio: 画面比例
        version: 版本编号（用于生成不同变体）
    """
    
    # 随机选择元素（使用 version 作为随机种子，确保可复现）
    random.seed(version)
    
    scene = random.choice(ANCIENT_SCENES)
    char1 = random.choice(CHARACTERS)
    char2 = random.choice([c for c in CHARACTERS if c != char1])
    emotion = random.choice(EMOTIONS)
    line = random.choice(ORIGINAL_LINES)
    camera = random.choice(CAMERA_MOVES)
    lighting = random.choice(LIGHTING)
    color = random.choice(COLOR_STYLES)
    
    # 构建提示词（Seedance 2.0 格式）
    prompt = (
        f"{duration}秒古风仙侠视频，{color}，\n"
        f"场景：{scene}。\n"
        f"{char1}与{char2}相对而立，{emotion}。\n"
        f"{camera}。\n"
        f"{lighting}。\n"
        f'台词（{char1.split("的")[1] if "的" in char1 else "角色"}，{emotion.split("，")[0]}）："{line}"\n'
        f"时长：精准{duration}秒。\n"
        f"禁止项：禁止出现水印、字幕、Logo、文字、品牌标识。"
    )
    
    return prompt


def generate_multi_version(topic, duration, ratio, count=3):
    """生成多个版本供选择"""
    
    prompts = []
    for v in range(1, count + 1):
        prompt = generate_seedance2_prompt(topic, duration, ratio, version=v)
        prompts.append(prompt)
    
    return prompts


def main():
    parser = argparse.ArgumentParser(description="Seedance 2.0 专用提示词生成器（无侵权）")
    parser.add_argument("topic", help="主题类型（古风仙侠/都市情感/悬疑/科幻等）", default="古风仙侠", nargs="?")
    parser.add_argument("--duration", type=int, default=15, help="时长（秒）")
    parser.add_argument("--ratio", default="16:9", help="画面比例")
    parser.add_argument("--versions", type=int, default=3, help="生成版本数")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 Seedance 2.0 专用提示词生成器")
    print("=" * 60)
    print(f"主题：{args.topic}")
    print(f"时长：{args.duration}秒")
    print(f"比例：{args.ratio}")
    print(f"版本数：{args.versions}")
    print("=" * 60)
    
    prompts = generate_multi_version(args.topic, args.duration, args.ratio, args.versions)
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n【版本 {i}】\n")
        print(prompt)
        print("\n" + "-" * 60)
    
    print(f"\n✅ 生成完成！可直接复制到即梦平台使用。")
    print(f"📌 即梦平台：https://jimeng.jianying.com")
    print(f"\n💡 提示：所有台词和描述均为原创，无侵权风险。")


if __name__ == "__main__":
    main()
