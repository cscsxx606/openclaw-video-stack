#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 短剧提示词生成器 - 丝滑流畅版
专为短剧/剧情视频优化，生成更自然流畅的提示词
"""

import sys
import argparse
import random
from datetime import datetime

# ============== 短剧专属素材库 ==============

# 短剧类型
DRAMA_TYPES = {
    "霸道总裁": {
        "场景": ["豪华办公室", "总裁办公室", "会议室", "高档餐厅", "豪宅客厅"],
        "角色": ["霸道总裁", "职场精英", "富家千金", "灰姑娘", "秘书"],
        "情绪": ["霸道", "冷漠", "温柔", "慌乱", "坚定", "委屈"],
        "经典台词": [
            "女人，你这是在玩火！",
            "整个公司都是我的，多你一个又何妨？",
            "签了它，你就是我的人。",
            "当初是你说我不配，现在求我？晚了！",
            "记住，从今以后你只能属于我一个人！"
        ]
    },
    "古风仙侠": {
        "场景": ["仙山云海", "竹林深处", "古代宫殿", "悬崖绝壁", "桃花林"],
        "角色": ["剑修", "仙女", "魔尊", "师尊", "小师弟"],
        "情绪": ["坚毅", "冷漠", "温柔", "决绝", "深情"],
        "经典台词": [
            "此界之门，不容踏越！",
            "今日，我便以这柄剑，镇尔等邪祟！",
            "师尊，徒儿愿为您赴汤蹈火！",
            "三生三世，我只爱你一人。",
            "这一剑，我等了千年！"
        ]
    },
    "都市情感": {
        "场景": ["咖啡厅", "地铁站", "公寓楼道", "公司楼下", "公园长椅"],
        "角色": ["职场女性", "暖男", "前男友", "闺蜜", "上司"],
        "情绪": ["忧伤", "温暖", "纠结", "释然", "感动"],
        "经典台词": [
            "我们，还是算了吧。",
            "原来，你一直都在等我。",
            "这一次，我不会再放手了。",
            "有些人，一旦错过就不在。",
            "谢谢你，让我相信爱情。"
        ]
    },
    "悬疑推理": {
        "场景": ["案发现场", "审讯室", "黑暗走廊", "废弃工厂", "雨夜街道"],
        "角色": ["侦探", "嫌疑人", "目击者", "警察", "凶手"],
        "情绪": ["紧张", "恐惧", "冷静", "狡诈", "愤怒"],
        "经典台词": [
            "凶手，就在我们中间。",
            "别躲了，我知道你在这。",
            "真相，永远只有一个。",
            "你逃不掉的，自首吧。",
            "这一切，都是你策划的！"
        ]
    },
    "甜宠恋爱": {
        "场景": ["樱花树下", "海边栈道", "游乐园", "图书馆", "天台"],
        "角色": ["校花", "学霸", "校草", "青梅竹马", "同桌"],
        "情绪": ["害羞", "甜蜜", "开心", "吃醋", "心动"],
        "经典台词": [
            "你愿意做我女朋友吗？",
            "我喜欢你，从很久很久以前就开始了。",
            "笨蛋，我一直在等你啊。",
            "这是我们的第一个吻。",
            "以后每一天，我都想和你一起度过。"
        ]
    }
}

# 丝滑转场描述
TRANSITIONS = [
    "镜头缓缓推进，",
    "画面渐渐清晰，",
    "随着镜头摇移，",
    "镜头缓慢拉远，",
    "画面柔和过渡，",
    "镜头自然切换，",
    "丝滑转场，",
    "流畅过渡，"
]

# 情绪递进描述
EMOTION_FLOW = [
    "情绪从平静转为激动，",
    "表情由冷漠变为温柔，",
    "眼神从坚定到动摇，",
    "语气从冷漠到深情，",
    "动作由缓慢变急促，",
    "氛围从紧张到释然，",
]


def generate_drama_prompt(drama_type, duration=15, ratio="16:9", scenes=1):
    """
    生成丝滑流畅的短剧提示词
    
    Args:
        drama_type: 短剧类型（霸道总裁/古风仙侠/都市情感/悬疑推理/甜宠恋爱）
        duration: 时长（秒）
        ratio: 画面比例
        scenes: 场景数量
    """
    
    # 获取短剧类型配置
    if drama_type not in DRAMA_TYPES:
        drama_type = random.choice(list(DRAMA_TYPES.keys()))
    
    config = DRAMA_TYPES[drama_type]
    
    # 生成场景
    scene = random.choice(config["场景"])
    character1 = random.choice(config["角色"])
    character2 = random.choice([c for c in config["角色"] if c != character1])
    emotion = random.choice(config["情绪"])
    line = random.choice(config["经典台词"])
    
    # 生成丝滑的提示词
    prompt = generate_smooth_prompt(
        drama_type=drama_type,
        scene=scene,
        character1=character1,
        character2=character2,
        emotion=emotion,
        line=line,
        duration=duration,
        scenes=scenes
    )
    
    return prompt


def generate_smooth_prompt(drama_type, scene, character1, character2, emotion, line, duration, scenes):
    """生成丝滑流畅的提示词"""
    
    # 开场描述
    opening = random.choice([
        f"{duration}秒{drama_type}短剧，电影级质感，",
        f"{duration}秒高清短剧，{drama_type}风格，",
        f"电影级{duration}秒{drama_type}，",
    ])
    
    # 场景描述（丝滑版）
    scene_desc = random.choice([
        f"场景：{scene}。{random.choice(TRANSITIONS)}{character1}与{character2}对峙，",
        f"地点：{scene}。镜头缓缓推进，{character1}站在画面中央，{character2}从远处走近，",
        f"{scene}中，{random.choice(TRANSITIONS)}{character1}表情{emotion}，",
    ])
    
    # 情绪递进
    emotion_desc = random.choice([
        f"情绪{emotion}，眼神充满戏张力，",
        f"表情从平静转为{emotion}，情绪层层递进，",
        f"{random.choice(EMOTION_FLOW)}{emotion}爆发，",
    ])
    
    # 台词（如果有）
    if line:
        dialogue = f'台词（{character1}，{emotion}）："{line}"，'
    else:
        dialogue = ""
    
    # 运镜描述（丝滑版）
    camera_desc = random.choice([
        "镜头语言丰富，推拉摇移自然流畅，",
        "运镜丝滑，景别切换自然，",
        "电影级运镜，流畅的镜头运动，",
    ])
    
    # 光影描述
    light_desc = random.choice([
        "电影级布光，明暗对比强烈，",
        "柔和光线，营造浪漫氛围，",
        "戏剧性光影，突出人物情绪，",
    ])
    
    # 音效描述
    sound_desc = random.choice([
        "配乐：紧张悬疑背景音，",
        "音效：环境音 + 情绪配乐，",
        "BGM：浪漫温馨钢琴曲，",
    ])
    
    # 组合成完整提示词
    prompt = (
        f"{opening}"
        f"{scene_desc}"
        f"{emotion_desc}"
        f"{dialogue}"
        f"{camera_desc}"
        f"{light_desc}"
        f"{sound_desc}"
        f"禁止项：禁止出现水印、字幕、Logo、文字"
    )
    
    return prompt


def generate_multi_scene_drama(drama_type, duration=30, ratio="16:9"):
    """生成多场景短剧（超长视频）"""
    
    # 分段生成
    if duration <= 30:
        segments = 2
    elif duration <= 45:
        segments = 3
    else:
        segments = 4
    
    segment_duration = duration // segments
    
    output = f"""## 超长短剧提示词（总时长约{duration}秒）

**类型**：{drama_type}
**总段数**：{segments}段
**建议比例**：{ratio}

"""
    
    for i in range(segments):
        start_time = i * segment_duration
        end_time = start_time + segment_duration
        
        prompt = generate_drama_prompt(drama_type, segment_duration, ratio)
        
        if i == 0:
            output += f"""### 第{i+1}段（{start_time}-{end_time}秒）—— 正常生成

**生成时长**：{segment_duration}秒

#### 提示词
{prompt}

"""
            if i < segments - 1:
                output += f"""#### 衔接点
本段结尾：情绪高潮点，为下一段做铺垫。

"""
        else:
            output += f"""### 第{i+1}段（{start_time}-{end_time}秒）—— 视频延长

**操作**：将第{i}段生成的视频上传为 @视频 1

**生成时长**：{segment_duration}秒

#### 提示词
将@视频 1 延长{segment_duration}秒。{prompt}

参考素材：@视频 1：前段剧情

"""
    
    return output


def main():
    parser = argparse.ArgumentParser(description="AI 短剧提示词生成器 - 丝滑流畅版")
    parser.add_argument("type", help="短剧类型（霸道总裁/古风仙侠/都市情感/悬疑推理/甜宠恋爱）")
    parser.add_argument("--duration", type=int, default=15, help="时长（秒）")
    parser.add_argument("--ratio", default="16:9", help="画面比例")
    parser.add_argument("--scenes", type=int, default=1, help="场景数量")
    parser.add_argument("--versions", type=int, default=3, help="生成版本数")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 AI 短剧提示词生成器 - 丝滑流畅版")
    print("=" * 60)
    print(f"类型：{args.type}")
    print(f"时长：{args.duration}秒")
    print(f"比例：{args.ratio}")
    print(f"版本数：{args.versions}")
    print("=" * 60)
    
    for v in range(args.versions):
        print(f"\n【版本 {v+1}】\n")
        
        if args.duration <= 15:
            prompt = generate_drama_prompt(args.type, args.duration, args.ratio, args.scenes)
        else:
            prompt = generate_multi_scene_drama(args.type, args.duration, args.ratio)
        
        print(prompt)
        print("\n" + "-" * 60)
    
    print(f"\n✅ 生成完成！可直接复制到即梦平台使用。")
    print(f"📌 即梦平台：https://jimeng.jianying.com")


if __name__ == "__main__":
    main()
