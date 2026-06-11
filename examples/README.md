# 📚 示例项目

> 3 个完整的端到端案例，覆盖不同主题/风格/用途

| 示例 | 主题 | 风格 | 状态 |
|------|------|------|------|
| [`su7-ultra-nurburgring/`](./su7-ultra-nurburgring/) | 小米 SU7 Ultra 纽北 | 汽车资讯 · 电影级 | ✅ 完整 |
| [`opus47-final/`](./opus47-final/) | Claude Opus 4.7 发布 | 科技资讯 · 蓝色科技 | ✅ 完整 |
| [`deepseek-v4-pixsou/`](./deepseek-v4-pixsou/) | DeepSeek V4 + 像素灵境 | 科技资讯 · 蓝黑 | ✅ 完整 |

## 📊 主题对比

| 案例 | 字数 | 镜头 | 提示词长度 | 卖点 |
|------|------|------|-----------|------|
| SU7 Ultra | 148 | 5 | 720 字 | 4 个数据点 |
| Opus 4.7 | 145 | 5 | 680 字 | 3 个能力维度 |
| DeepSeek V4 | 150 | 5 | 700 字 | 双主题对比 |

## 🔍 每个案例包含

- **口播稿**（Markdown，约 150 字）
- **分镜 Seedance 提示词**（2 段 × 15 秒，可直接粘贴即梦）
- **字幕文件**（ASS 格式）
- **README**（完整流程说明）

## 🔁 复用流程

```bash
# 1. 复制一个案例的提示词模板
cp examples/su7-ultra-nurburgring/分镜-Seedance提示词.md /tmp/my-prompt.md

# 2. 改写提示词
# （用 LLM 或手工改写）

# 3. 粘贴到即梦生成
# （或调用 Seedance API）
```

## 🎯 选哪个参考？

- **想做汽车类** → SU7 Ultra
- **想做 AI 模型** → Opus 4.7
- **想做新闻盘点** → DeepSeek V4
