# Mac 微调 Qwen3

> 常见的微调方法在 Mac 上的兼容性较差
>
> MLX-LM 在 Mac 设备上对训练、微调有较好的支持

## Lora 微调流程（以 Qwen3-32B为例）

1. 下载 [Qwen3-32B 模型](http://huggingface.co/Qwen/Qwen3-32B)，放置到 `Qwen/` 目录下
2. 下载训练数据集，这里以[自我认知数据集](https://modelscope.cn/datasets/swift/self-cognition) 为例，放置到 `mlx_data/` 目录下
3. 创建虚拟环境并安装依赖，然后激活虚拟环境，以 uv 为例

```bash
uv venv
uv sync
source .venv/bin/activate
```

4. 执行脚本，处理训练数据，划分出验证集和训练集，可以修改代码以替换名称 `python trans_data.py`
5. 运行 `train.bash` 脚本，开始训练，此步骤会要求注册登陆 swanlab 账号（可选），推荐登录，可以在网页端查看训练详情
6. 待训练完成后，可以运行 `chat.bash` 在控制台直接运行模型以开始对话，测试效果
7. 最后可以运行 `export.bash` 导出模型文件到 `QWen/` 目录下，以在其他软件中使用（可以使用 `--export-gguf` 选项来输出 gguf 格式）

## 参考

- [微调教程](https://github.com/ShaohonChen/Finetune_Qwen3_on_MacBook)
- [MLX-LM LORA文档](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md)