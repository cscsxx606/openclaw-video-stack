#!/bin/bash
# 免费版配置和测试脚本

echo "=========================================="
echo "🆓 即梦 Seedance 免费版配置工具"
echo "=========================================="

# 1. 检查 Selenium
echo ""
echo "📦 检查 Selenium..."
if python3 -c "import selenium" 2>/dev/null; then
    echo "✅ Selenium 已安装"
else
    echo "❌ Selenium 未安装，正在安装..."
    pip3 install selenium --break-system-packages
fi

# 2. 检查 Chrome
echo ""
echo "🌐 检查 Chrome 浏览器..."
if command -v google-chrome &> /dev/null || command -v chrome &> /dev/null; then
    echo "✅ Chrome 已安装"
else
    echo "⚠️  Chrome 未安装"
    echo "   请运行：brew install --cask google-chrome"
    echo "   或者手动下载：https://www.google.com/chrome/"
fi

# 3. 检查账号配置
echo ""
echo "🔑 检查账号配置..."
if [ -n "$JIMENG_EMAIL" ] && [ -n "$JIMENG_PASSWORD" ]; then
    echo "✅ 账号已配置（环境变量）"
    echo "   邮箱：$JIMENG_EMAIL"
else
    echo "⚠️  账号未配置"
    echo ""
    echo "   请运行以下命令配置账号："
    echo ""
    echo "   export JIMENG_EMAIL=\"your_email_or_phone\""
    echo "   export JIMENG_PASSWORD=\"your_password\""
    echo ""
    echo "   或者添加到 ~/.zshrc 永久保存："
    echo "   echo 'export JIMENG_EMAIL=\"your_email\"' >> ~/.zshrc"
    echo "   echo 'export JIMENG_PASSWORD=\"your_password\"' >> ~/.zshrc"
    echo "   source ~/.zshrc"
fi

# 4. 测试提示词生成
echo ""
echo "=========================================="
echo "🎬 测试提示词生成（文字）..."
echo "=========================================="
python3 scripts/gen_prompt.py "仙侠短片" --duration 15

echo ""
echo "=========================================="
echo "✅ 配置完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 配置即梦账号（如果还没配置）"
echo "2. 安装 Chrome 浏览器（如果还没安装）"
echo "3. 运行测试：python3 scripts/api_generate.py \"测试\" --api browser"
echo ""
