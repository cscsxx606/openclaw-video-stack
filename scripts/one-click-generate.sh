#!/bin/bash
# 一键生成 30 秒短视频
# 用法：./one-click-generate.sh "主题" [-o output_dir]

set -e

TOPIC="$1"
OUTPUT_DIR="${2:-$HOME/.openclaw/workspace/output/videos/$(date +%Y%m%d-%H%M%S)}"

if [ -z "$TOPIC" ]; then
  echo "用法: $0 <主题> [输出目录]"
  echo "示例: $0 '小米 SU7 Ultra 纽北跑进 7 分'"
  exit 1
fi

# 检查 API Key
if [ -z "$ARK_API_KEY" ]; then
  echo "❌ 错误: ARK_API_KEY 未设置"
  echo "   export ARK_API_KEY='<your-key>'"
  exit 1
fi

# 创建项目目录
mkdir -p "$OUTPUT_DIR"
echo "📁 项目目录: $OUTPUT_DIR"

# 调用 OpenClaw skill
openclaw run video-pipeline-cn \
  --topic "$TOPIC" \
  --output "$OUTPUT_DIR" \
  --wait

echo ""
echo "✅ 生成完成！"
echo "📁 项目位置: $OUTPUT_DIR"
echo "🎬 最终成片: $OUTPUT_DIR/su7-final.mp4"
