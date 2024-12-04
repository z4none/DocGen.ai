# 文档生成工具

## 概述
此项目是一个文档生成工具，适用于 C/C++ 项目。它自动从源代码中生成 markdown 文档，并且翻译成中文，支持多种静态网站生成器，包括但不限于 VitePress，未来将支持更多语言。

## 功能
- 从 C/C++ 源代码头文件自动生成 markdown 文档。
- 支持多种静态网站生成器的文档配置。
- 按字母顺序列出文档文件，并进行层次化组织。

## 先决条件
- Python 3.x
- OpenAI API
- 静态网站生成器，比如 VitePress

## 安装
1. 克隆仓库：
   ```bash
   git clone <repository-url>
   ```
2. 进入项目目录：
   ```bash
   cd DocGen.ai
   ```
3. 安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 配置 OpenAi 环境变量:
   ```bash
   export MAKE_DOC_API_TOKEN='your-openai-api-key'
   export MAKE_DOC_API_URL='https://api.openai.com/v1'
   ```
   支持兼容 OpenAi API 的第三方服务，比如 DeepSeek。

## 使用方法
运行主脚本以处理源代码并生成文档：
```bash
python main.py --input-dir <path-to-source> --output-dir <path-to-output>
```

## 配置
- 修改 `config.mts` 以调整 VitePress 设置。
- 根据需要调整 `make_doc.py` 中的处理参数。

## 贡献
欢迎贡献！请提交拉取请求或打开问题以提出建议或改进。

## 许可证
此项目根据 MIT 许可证授权。

## 联系
如有任何疑问或咨询，请联系 [z4none@gmail.com]。
