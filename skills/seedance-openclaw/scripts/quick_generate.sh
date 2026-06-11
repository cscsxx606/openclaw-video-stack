#!/bin/bash
# 快速视频生成脚本 - 半自动方案（最可靠）

echo "=========================================="
echo "🎬 即梦 Seedance 快速视频生成"
echo "=========================================="

# 检查参数
if [ -z "$1" ]; then
    echo "用法：$0 \"视频主题\" [时长]"
    echo ""
    echo "示例："
    echo "  $0 \"仙侠战斗\" 15"
    echo "  $0 \"产品展示广告\" 15"
    echo "  $0 \"古风短剧\" 30"
    echo ""
    exit 1
fi

TOPIC="$1"
DURATION="${2:-15}"
OUTPUT="${TOPIC//[^a-zA-Z0-9]/_}.mp4"

echo ""
echo "📝 主题：$TOPIC"
echo "⏱️  时长：$DURATION 秒"
echo "📹 输出：$OUTPUT"
echo ""

# 步骤 1：生成提示词
echo "=========================================="
echo "步骤 1/4: 生成提示词..."
echo "=========================================="
echo ""

PROMPT=$(python3 scripts/gen_prompt.py "$TOPIC" --duration "$DURATION" 2>&1 | \
    grep -A 5 "版本 1" | grep "秒" | head -1)

if [ -z "$PROMPT" ]; then
    echo "❌ 提示词生成失败"
    exit 1
fi

echo "✅ 提示词已生成："
echo ""
echo "$PROMPT"
echo ""

# 复制到剪贴板
echo "$PROMPT" | pbcopy
echo "✅ 提示词已复制到剪贴板"
echo ""

# 步骤 2：打开即梦
echo "=========================================="
echo "步骤 2/4: 打开即梦平台..."
echo "=========================================="
echo ""

open "https://jimeng.jianying.com/create/video"
echo "✅ 已打开即梦平台"
echo ""
echo "💡 在打开的网页中："
echo "   1. 粘贴提示词（Cmd+V）"
echo "   2. 选择时长：$DURATION 秒"
echo "   3. 选择比例：16:9"
echo "   4. 点击'生成'按钮"
echo ""

# 等待用户操作
read -p "✅ 完成后按回车键继续..."

# 步骤 3：等待生成
echo ""
echo "=========================================="
echo "步骤 3/4: 等待视频生成..."
echo "=========================================="
echo ""
echo "⏳ 通常需要 3-5 分钟..."
echo ""
echo "💡 在浏览器中可以："
echo "   - 查看生成进度"
echo "   - 预览生成的视频"
echo "   - 不满意可以重新生成"
echo ""

read -p "✅ 视频生成完成后按回车键..."

# 步骤 4：下载
echo ""
echo "=========================================="
echo "步骤 4/4: 下载视频..."
echo "=========================================="
echo ""
echo "💡 在浏览器中："
echo "   1. 点击'下载'按钮"
echo "   2. 保存为：$OUTPUT"
echo ""
echo "📹 建议保存位置："
echo "   ~/Movies/jimeng/$OUTPUT"
echo ""
echo "=========================================="
echo "✅ 完成！"
echo "=========================================="
echo ""
echo "生成的视频：$OUTPUT"
echo ""
echo "💡 提示："
echo "   - 查看提示词脚本：python3 scripts/gen_prompt.py --help"
echo "   - 查看使用指南：cat ../已登录模式使用指南.md"
echo ""
