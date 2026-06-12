#!/usr/bin/env python3
"""
video-pipeline-cn 720p 降本自动推荐模块

根据预算自动选择最优分辨率 + 并发策略

用法：
    from resolution_advisor import advise_resolution
    
    resolution, max_workers, estimated_cost = advise_resolution(budget=20, duration=30)
    # 返回: ('720p', 4, 16.06)
"""

import sys
from pathlib import Path

# 添加 Seedance2-skill 到路径
SEEDANCE2_DIR = Path(__file__).parent.parent / "Seedance2-skill" / "scripts"
sys.path.insert(0, str(SEEDANCE2_DIR))

try:
    import db
except ImportError as e:
    print(f"❌ 无法导入 db.py: {e}")
    sys.exit(1)


# 配置
BUDGET_720P_THRESHOLD = 20  # 预算 < ¥20 自动选 720p
BUDGET_1080P_THRESHOLD = 50  # 预算 < ¥50 推荐 720p，但允许 1080p

# 并发策略
MAX_WORKERS_720P = 4  # 720p 可以 4 并发（实测 4x 加速）
MAX_WORKERS_1080P = 2  # 1080p 建议 2 并发（保守）

# 分辨率参数
RESOLUTIONS = {
    "720p": {
        "factor": 0.444,  # 实测 720p tokens 缩放
        "max_workers": 4,
        "quality": "中等",
        "speed_boost": "4x 加速（4 min 总耗时）"
    },
    "1080p": {
        "factor": 1.0,
        "max_workers": 2,
        "quality": "电影感",
        "speed_boost": "2x 加速（8 min 总耗时）"
    }
}


def estimate_cost(duration=30, resolution="1080p", has_video_input=False, segments=2):
    """
    估算视频成本
    
    Args:
        duration: 总时长（秒）
        resolution: 分辨率
        has_video_input: 是否含参考视频（延长模式）
        segments: 分段数（默认 2 段 15s）
    
    Returns:
        float: 估算成本（元）
    """
    segment_duration = duration / segments
    
    cost_per_segment = db.estimate_cost(
        duration=segment_duration,
        has_video_input=has_video_input,
        flex=False,  # 2.0 不支持 flex
        draft=False,  # 2.0 不支持 draft
        resolution=resolution
    )
    
    return cost_per_segment * segments


def advise_resolution(budget, duration=30, has_video_input=False, segments=2, prefer_quality=False):
    """
    根据预算推荐最优分辨率 + 并发策略
    
    Args:
        budget: 预算（元）
        duration: 总时长（秒）
        has_video_input: 是否含参考视频
        segments: 分段数
        prefer_quality: 是否优先质量（预算允许时选 1080p）
    
    Returns:
        tuple: (resolution, max_workers, estimated_cost, recommendation)
    """
    # 计算两种分辨率的成本
    cost_720p = estimate_cost(duration, "720p", has_video_input, segments)
    cost_1080p = estimate_cost(duration, "1080p", has_video_input, segments)
    
    print(f"💰 预算: ¥{budget}")
    print(f"   720p 估算: ¥{cost_720p:.2f}（{RESOLUTIONS['720p']['quality']}）")
    print(f"   1080p 估算: ¥{cost_1080p:.2f}（{RESOLUTIONS['1080p']['quality']}）")
    
    # 决策逻辑
    if budget < BUDGET_720P_THRESHOLD:
        # 预算 < ¥20：强制 720p
        resolution = "720p"
        max_workers = MAX_WORKERS_720P
        estimated_cost = cost_720p
        recommendation = f"预算紧张（¥{budget} < ¥{BUDGET_720P_THRESHOLD}），强制 720p + 4 并发，省 {((cost_1080p-cost_720p)/cost_1080p*100):.0f}%"
        
    elif budget < BUDGET_1080P_THRESHOLD:
        # 预算 ¥20-50：推荐 720p，但允许 1080p
        if prefer_quality and budget >= cost_1080p:
            resolution = "1080p"
            max_workers = MAX_WORKERS_1080P
            estimated_cost = cost_1080p
            recommendation = f"预算允许（¥{budget}），优先质量选 1080p"
        else:
            resolution = "720p"
            max_workers = MAX_WORKERS_720P
            estimated_cost = cost_720p
            recommendation = f"预算适中（¥{budget}），推荐 720p 省 {((cost_1080p-cost_720p)/cost_1080p*100):.0f}%，加 --prefer-quality 可强制 1080p"
    
    else:
        # 预算 > ¥50：默认 1080p
        resolution = "1080p"
        max_workers = MAX_WORKERS_1080P
        estimated_cost = cost_1080p
        recommendation = f"预算充足（¥{budget}），默认 1080p 电影感"
    
    print(f"\n🎯 推荐方案: {recommendation}")
    print(f"   分辨率: {resolution}")
    print(f"   并发数: {max_workers}")
    print(f"   估算成本: ¥{estimated_cost:.2f}")
    print(f"   加速: {RESOLUTIONS[resolution]['speed_boost']}")
    
    return resolution, max_workers, estimated_cost, recommendation


def get_resolution_info(resolution):
    """获取分辨率详细信息"""
    return RESOLUTIONS.get(resolution, {})


if __name__ == "__main__":
    # 测试不同预算
    test_budgets = [10, 20, 30, 50, 100]
    
    print("=== 720p 降本自动推荐测试 ===\n")
    
    for budget in test_budgets:
        print(f"\n{'='*50}")
        resolution, max_workers, cost, recommendation = advise_resolution(budget)
        print(f"\n结果: {resolution} + {max_workers} workers = ¥{cost:.2f}")
        print(f"{'='*50}\n")
