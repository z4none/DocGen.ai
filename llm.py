import os
import requests
import openai

class LLM:
    def __init__(self):
        """
        Initialize the LLM class with API token and URL from environment variables.
        """
        self.client = openai.OpenAI(
            api_key=os.getenv('MAKE_DOC_API_TOKEN'),
            base_url=os.getenv('MAKE_DOC_API_URL'),
        )
        # Define the prompt template during initialization
        self.prompt_template = '''帮我用中文整理以下SDK 中的 函数、参数以及结构定义的说明，输出为 markdown
我希望输出的格式为：
1. 本函数说明的标题，形如 `## function_name {#function_name}`
2. 函数的完整定义，用 markdown code 格式输出
3. 函数的描述，翻译函数注释中的描述相关内容为中文
4. 函数参数说明，用 markdown 表格输出
5. 函数返回值，详细说明各种情况的返回值

接下来我的每次输入都是 SDK 定义，请帮我按以上要求输出'''

    def _make_request(self, code_block: str) -> str:
        """
        Make a request to the LLM API to generate documentation.

        Args:
            code_block (str): The code block to process.

        Returns:
            str: The generated documentation in markdown format.
        """
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": self.prompt_template
                },
                {
                    "role": "user",
                    "content": code_block
                }
            ],
            stream=False
        )


        return response.choices[0].message.content

    def make_doc(self, code_block: str) -> str:
        """
        Generate documentation for the given code block.

        Args:
            code_block (str): The code block to document.

        Returns:
            str: The documentation in markdown format.
        """
        return self._make_request(code_block)
