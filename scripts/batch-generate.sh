#!/bin/bash
# 批量生成短视频
# 用法：./batch-generate.sh topics.txt

set -e

TOPICS_FILE="$1"

if [ -z "$TOPICS_FILE" ] || [ ! -f "$TOPICS_FILE" ]; then
  echo "用法: $0 <主题文件>"
  echo "主题文件格式：每行一个主题"
  exit 1
fi

if [ -z "$ARK_API_KEY" ]; then
  echo "❌ 错误: ARK_API_KEY 未设置"
  exit 1
fi

COUNT=0
while IFS= read -r topic; do
  # 跳过空行和注释
  [[ -z "$topic" || "$topic" == \#* ]] && continue
  
  COUNT=$((COUNT + 1))
  echo ""
  echo "==========================================="
  echo "  生成 $COUNT: $topic"
  echo "==========================================="
  
  OUTPUT_DIR="$HOME/.openclaw/workspace/output/videos/batch-$(date +%Y%m%d-%H%M%S)-$COUNT"
  
  openclaw run video-pipeline-cn \
    --topic "$topic" \
    --output "$OUTPUT_DIR" \
    --wait
  
  # 避免 API 限流
  echo "⏸  等待 30s 避免限流..."
  sleep 30
done < "$TOPICS_FILE"

echo ""
echo "✅ 批量生成完成！共 $COUNT 个视频"
