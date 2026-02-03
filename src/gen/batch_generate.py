#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from typing import Optional
import time
import openai
from ..conf import cm


class DatasetGenerator:
    """LLM 数据集生成器"""

    def __init__(
        self,
        system_prompt_path: str = "prompt.md",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: str = "gpt-4-turbo",
    ):
        self.system_prompt_path = system_prompt_path
        self.model = model

        # 读取系统提示词
        if not os.path.exists(system_prompt_path):
            raise FileNotFoundError(f"系统提示词文件不存在: {system_prompt_path}")

        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        # 配置 OpenAI 客户端
        self.api_key = api_key
        if not self.api_key:
            raise ValueError(
                "未设置 API 密钥，请通过参数或 OPENAI_API_KEY 环境变量提供"
            )

        if api_base:
            openai.api_base = api_base

        self.client = openai.OpenAI(api_key=self.api_key, base_url=api_base)

    def load_questions(self, questions_file: Optional[str] = None) -> list[str]:
        if questions_file is None or not os.path.exists(questions_file):
            raise FileNotFoundError("未找到问题列表文件")

        questions = []
        file_ext = Path(questions_file).suffix.lower()

        if file_ext != ".txt":
            raise RuntimeError("仅支持 txt 格式的问题列表文件")
        with open(questions_file, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]

        print(f"已加载 {len(questions)} 个问题")
        return questions

    def generate_response(self, question: str, retry_times: int = 3) -> Optional[str]:
        """
        调用 LLM 生成回答
        """
        for attempt in range(retry_times):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": question},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )
                res = response.choices[0].message.content
                if res:
                    return res.strip()
                else:
                    raise ValueError(f"响应内容无效: {res}")
            except (openai.APIError, openai.APIConnectionError, ValueError) as e:
                if attempt < retry_times - 1:
                    wait_time = (2**attempt) * 2  # 指数退避
                    print(
                        f"API 错误 ({attempt + 1}/{retry_times})，{wait_time} 秒后重试: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    print(f"生成回答失败 (已重试 {retry_times} 次): {str(e)}")
                    return None

    def batch_generate(
        self,
        output_file: str = "dataset.json",
        questions_file: Optional[str] = None,
        max_samples: Optional[int] = None,
        rate_limit: float = 0.5,
    ) -> None:
        """
        批量生成数据集
        """
        # 加载问题
        questions = self.load_questions(questions_file)

        if max_samples:
            questions = questions[:max_samples]

        total = len(questions)

        print(f"\n开始生成数据集，共 {total} 个问题")
        # 加载进度文件
        progress_file = output_file + ".progress"
        start_idx = 0
        if os.path.exists(progress_file):
            with open(progress_file, "r", encoding="utf-8") as pf:
                idx_str = pf.read().strip()
                if idx_str.isdigit():
                    start_idx = int(idx_str)
                    print(f"检测到进度文件，已跳过前 {start_idx} 个问题")

        for idx, question in enumerate(questions, 1):
            if idx <= start_idx:
                continue
            output = self.generate_response(question)
            if output:
                if output.startswith("```xml"):
                    output = output[6:-3].strip()
                data_to_save = {
                    "instruction": question,
                    "input": "",
                    "output": output,
                }
                # 保存进度
                self._save_dataset(idx, data_to_save, output_file)
                print(f"成功: {idx}/{total}")
            else:
                raise RuntimeError(f"第 {idx} 个问题生成失败，任务退出")

            # 速率限制
            if idx < total:
                time.sleep(rate_limit)

        # 最终保存
        print(f"数据集已保存到: {output_file}")

    def _save_dataset(self, idx: int, data_to_save: dict, output_file: str) -> None:
        """
        追加写入到数据集文件，并保存进度索引，用于进度恢复
        """
        # 路径不存在时，创建目录
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        # 保存进度索引（不存在时创建）
        progress_file = output_file + ".progress"
        with open(progress_file, "w", encoding="utf-8") as pf:
            pf.write(str(idx))
        # 追加写入数据
        with open(output_file, "a+", encoding="utf-8") as f:
            f.write(json.dumps(data_to_save, ensure_ascii=False) + "\n")


def main():
    """主函数"""
    config = cm.get_config("gen")

    generator = DatasetGenerator(
        system_prompt_path=config["prompt_file"],
        api_key=config["api_key"],
        api_base=config["api_base"],
        model=config["model"],
    )

    generator.batch_generate(
        output_file=config["out_dir"],
        questions_file=config["questions_file"],
        max_samples=config["samples_cnt"],
        rate_limit=config["rate_limit"],
    )


if __name__ == "__main__":
    main()
