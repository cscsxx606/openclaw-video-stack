#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seedance 视频提示词生成器
为字节跳动 Seedance 2.0（即梦）平台生成专业中文视频提示词
"""

import sys
import argparse
import random
from datetime import datetime

# 内置提示词素材库
CAMERA_LANG = {
    "景别": ["特写", "近景", "中景", "全景", "远景", "大远景"],
    "运镜": ["推", "拉", "摇", "移", "跟", "升", "降", "环绕", "俯拍", "仰拍"],
    "角度": ["正面", "侧面", "背面", "45 度角", "低角度", "高角度", "鸟瞰"],
    "节奏": ["缓慢", "平稳", "快速", "急促", "渐快", "渐慢", "忽快忽慢"],
    "焦点": ["实焦", "虚焦", "跟焦", "变焦", "浅景深", "深景深"],
    "转场": ["切", "淡入淡出", "叠化", "划像", "匹配剪辑", "跳跃剪辑"]
}

VISUAL_STYLE = {
    "画面质感": ["电影级", "电视剧级", "纪录片级", "广告级", "动画级", "写实", "超现实"],
    "影像风格": ["赛博朋克", "古风", "科幻", "奇幻", "悬疑", "浪漫", "恐怖", "喜剧"],
    "色调氛围": ["暖色调", "冷色调", "高对比", "低饱和", "霓虹", "黑白", "复古"],
    "艺术风格": ["写实主义", "印象派", "抽象", "极简", "巴洛克", "蒸汽波"],
    "光影效果": ["自然光", "逆光", "侧光", "顶光", "轮廓光", "霓虹灯光", "烛光"],
    "动画风格": ["2D 动画", "3D 动画", "定格动画", "水墨动画", "赛璐璐", "粘土动画"]
}

SCENE_TEMPLATES = {
    "电商广告": "产品 360 度旋转展示、爆炸分解、3D 渲染特效",
    "短剧对白": "剧本化场景，含角色台词、情绪标注和音效设计",
    "仙侠奇幻": "电影级武打、法术特效、变身变装序列",
    "科普教学": "4K 医学 CGI、半透明人体结构可视化",
    "MV 音乐": "宽银幕构图、多图卡点参考视频节奏",
    "悬疑惊悚": "低角度特写、阴影对比、紧张音效 buildup",
    "科幻未来": "霓虹灯光、全息投影、飞行器、电子音效",
    "古风历史": "传统建筑、服饰细节、古风配乐、武术动作"
}


def generate_prompt(topic, duration=15, ratio="16:9", images=0, videos=0, audios=0, style=None):
    """生成 Seedance 视频提示词"""
    
    # 根据主题选择默认风格
    if not style:
        if any(kw in topic for kw in ["仙侠", "古风", "武侠", "奇幻"]):
            style = "古风奇幻"
        elif any(kw in topic for kw in ["赛博", "科幻", "未来", "霓虹"]):
            style = "赛博朋克"
        elif any(kw in topic for kw in ["产品", "广告", "展示", "商品"]):
            style = "电商广告"
        elif any(kw in topic for kw in ["短剧", "剧情", "对白", "总裁"]):
            style = "短剧对白"
        else:
            style = "电影级"
    
    # 生成提示词
    if duration <= 15:
        return generate_single_segment(topic, duration, ratio, style, images, videos, audios)
    else:
        return generate_multi_segment(topic, duration, ratio, style, images, videos, audios)


def generate_single_segment(topic, duration, ratio, style, images, videos, audios):
    """生成单段提示词（≤15 秒）"""
    
    # 根据主题生成更具体的描述
    topic_details = get_topic_details(topic, style)
    
    # 随机选择镜头元素
    camera_close = random.choice(CAMERA_LANG["景别"])
    camera_move = random.choice(CAMERA_LANG["运镜"])
    camera_angle = random.choice(CAMERA_LANG["角度"])
    visual_texture = random.choice(VISUAL_STYLE["画面质感"])
    color_tone = random.choice(VISUAL_STYLE["色调氛围"])
    light_effect = random.choice(VISUAL_STYLE["光影效果"])
    
    # 构建提示词开头
    prompt = f"{duration}秒{style}{topic_details['type']}，{color_tone}，"
    
    # 分镜描述（按时间段）- 更详细
    segments = []
    segment_duration = min(4, duration) if duration <= 12 else 5
    
    actions = topic_details.get("actions", ["主角登场", "动作展示", "高潮定格"])
    sounds = topic_details.get("sounds", ["环境音效", "动作音效", "收尾音效"])
    
    # 确保有足够的 actions 和 sounds
    while len(actions) < 3:
        actions.append("精彩镜头")
    while len(sounds) < 3:
        sounds.append("背景音效")
    
    seg_index = 0
    for i in range(0, duration, segment_duration):
        end = min(i + segment_duration, duration)
        if seg_index == 0:
            seg = f"{i}-{end}秒：{camera_angle}{camera_close}，{visual_texture}画面，{light_effect}，{actions[0]}，伴随{sounds[0]}"
        elif seg_index == 1 and len(actions) > 2:
            seg = f"{i}-{end}秒：{camera_move}镜头，{actions[1]}，{actions[2]}，伴随{sounds[1]}与{sounds[2]}"
        else:
            seg = f"{i}-{end}秒：慢动作定格，{camera_move}镜头，高潮场面，伴随{sounds[min(seg_index, len(sounds)-1)]}渐弱"
        segments.append(seg)
        seg_index += 1
    
    prompt += "，".join(segments)
    
    # 添加台词（如果有）
    if topic_details.get("dialogue"):
        prompt += f"，台词：\"{topic_details['dialogue']}\""
    
    # 添加参考素材说明
    refs = []
    if images > 0:
        refs.append(f"@图片 1~@图片{images}：角色/场景参考")
    if videos > 0:
        refs.append(f"@视频 1~@视频{videos}：运镜/动作参考")
    if audios > 0:
        refs.append(f"@音频 1~@音频{audios}：音效/配乐参考")
    
    if refs:
        prompt += "\n\n参考素材：\n- " + "\n- ".join(refs)
    
    # 添加技术参数和禁止项
    prompt += f"\n\n技术参数：画幅比{ratio}，2K 分辨率\n禁止项：禁止出现水印、字幕、Logo、文字"
    
    return prompt


def get_topic_details(topic, style):
    """根据主题返回详细的场景描述"""
    
    details = {
        "type": "镜头",
        "actions": [],
        "sounds": [],
        "dialogue": None
    }
    
    topic_lower = topic.lower()
    
    if any(kw in topic_lower for kw in ["仙侠", "武侠", "古风", "修仙"]):
        details["type"] = "仙侠高燃战斗"
        details["actions"] = ["主角衣袍飘动握紧武器", "旋身挥出剑气冲击波", "跃起腾空劈向敌人"]
        details["sounds"] = ["剑鸣声", "破空声", "爆炸声"]
        details["dialogue"] = "此界之门，不容踏越！"
    
    elif any(kw in topic_lower for kw in ["赛博", "科幻", "未来", "太空", "外星"]):
        details["type"] = "赛博朋克城市"
        details["actions"] = ["霓虹灯闪烁的街道", "飞行器划过夜空", "全息广告变换"]
        details["sounds"] = ["电子合成音", "飞行器嗡鸣", "城市背景音"]
    
    elif any(kw in topic_lower for kw in ["产品", "广告", "展示", "商品", "可乐", "手机"]):
        details["type"] = "产品展示广告"
        details["actions"] = ["产品 360 度旋转", "爆炸分解展示内部", "3D 渲染特效"]
        details["sounds"] = ["科技感音效", "产品展示音效"]
    
    elif any(kw in topic_lower for kw in ["短剧", "剧情", "总裁", "女主", "撕合同", "反杀"]):
        details["type"] = "短剧名场面"
        details["actions"] = ["特写角色表情", "关键动作", "情绪爆发"]
        details["sounds"] = ["背景音乐", "台词回声", "情绪音效"]
        details["dialogue"] = "当初是你说我不配，现在求我？晚了！"
    
    elif any(kw in topic_lower for kw in ["悬疑", "惊悚", "追踪", "特工", "谍战"]):
        details["type"] = "悬疑追踪"
        details["actions"] = ["阴影中的人物剪影", "快速转身对视", "奔跑追逐"]
        details["sounds"] = ["紧张音效", "脚步声", "心跳声"]
        details["dialogue"] = "别躲了，我知道你在这。"
    
    elif any(kw in topic_lower for kw in ["巨龙", "奇幻", "魔法", "觉醒"]):
        details["type"] = "奇幻巨龙觉醒"
        details["actions"] = ["巨龙从沉睡中睁眼", "怒吼掀起风暴", "展翅飞向天空"]
        details["sounds"] = ["巨龙怒吼", "翅膀拍打声", "魔法能量声"]
    
    elif any(kw in topic_lower for kw in ["mv", "音乐", "卡点", "歌曲"]):
        details["type"] = "MV 音乐卡点"
        details["actions"] = ["节奏切换场景", "音乐节拍同步", "宽银幕构图"]
        details["sounds"] = ["背景音乐", "节拍音效"]
    
    else:
        details["type"] = "电影级镜头"
        details["actions"] = ["开场镜头建立场景", "主体动作展示", "收尾定格"]
        details["sounds"] = ["环境音", "动作音效", "收尾音效"]
    
    return details


def generate_multi_segment(topic, duration, ratio, style, images, videos, audios):
    """生成多段提示词（>15 秒）"""
    
    segments_count = (duration + 14) // 15  # 向上取整
    
    output = f"""## 超长视频提示词（总时长约{duration}秒）

**主题**：{topic}
**总段数**：{segments_count}段
**建议比例**：{ratio}

"""
    
    remaining = duration
    for i in range(segments_count):
        seg_duration = min(15, remaining)
        start_time = i * 15
        end_time = start_time + seg_duration
        
        if i == 0:
            output += f"""### 第{i+1}段（{start_time}-{end_time}秒）—— 正常生成

**生成时长**：{seg_duration}秒

#### 提示词
{generate_single_segment(topic, seg_duration, ratio, style, images, 0, 0)}

"""
            if i < segments_count - 1:
                output += f"""#### 衔接点
本段结尾画面：{topic}的高潮镜头，为下一段做铺垫。

"""
        else:
            output += f"""### 第{i+1}段（{start_time}-{end_time}秒）—— 视频延长

**操作**：将第{i}段生成的视频上传为 @视频 1

**生成时长**：{seg_duration}秒

#### 提示词
将@视频 1 延长{seg_duration}秒。{generate_single_segment(topic + "延续", seg_duration, ratio, style, 0, 1, audios if i == segments_count - 1 else 0)}

"""
        
        remaining -= seg_duration
    
    return output


def main():
    parser = argparse.ArgumentParser(description="Seedance 视频提示词生成器")
    parser.add_argument("topic", help="视频主题描述")
    parser.add_argument("--duration", type=int, default=15, help="视频时长（秒），默认 15")
    parser.add_argument("--ratio", default="16:9", help="画面比例，默认 16:9")
    parser.add_argument("--images", type=int, default=0, help="参考图片数量")
    parser.add_argument("--videos", type=int, default=0, help="参考视频数量")
    parser.add_argument("--audios", type=int, default=0, help="参考音频数量")
    parser.add_argument("--style", help="视频风格（如：仙侠、赛博朋克、电商广告等）")
    parser.add_argument("--versions", type=int, default=2, help="生成版本数，默认 2")
    
    args = parser.parse_args()
    
    print(f"🎬 Seedance 视频提示词生成器")
    print(f"主题：{args.topic}")
    print(f"时长：{args.duration}秒")
    print(f"比例：{args.ratio}")
    print(f"风格：{args.style or '自动匹配'}")
    print("=" * 60)
    
    for v in range(args.versions):
        print(f"\n【版本 {v+1}】\n")
        prompt = generate_prompt(
            args.topic,
            args.duration,
            args.ratio,
            args.images,
            args.videos,
            args.audios,
            args.style
        )
        print(prompt)
        print("\n" + "-" * 60)
    
    print(f"\n✅ 生成完成！可直接复制到即梦平台使用。")
    print(f"📌 即梦平台：https://jimeng.jianying.com")


if __name__ == "__main__":
    main()
