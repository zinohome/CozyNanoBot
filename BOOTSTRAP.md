# CozyNanoBot — Bootstrap 指针

> 本项目是 CozyEngine 项目套件的一部分。
> 完整的 Bootstrap 文档（种子目录、`.secrets/` 引用规则、接入流程等）请参见：
>
> **[CozyEngineV2/BOOTSTRAP.md](https://github.com/zinohome/CozyEngineV2/blob/main/BOOTSTRAP.md)**
>
> 该伞文档覆盖 CozyEngineV2 + CozyNanoBot + CozyVoice + 共享 `.secrets/` 的全部接入与维护规范。

## 快速参考

- 种子路径：`/home/ubuntu/CozySeeds/CozyNanoBot/`
- 共享密钥：`/home/ubuntu/CozySeeds/.secrets/cozyengine-keys.env`（只读绑定，禁止复制）
- 默认端口：8080（容器内）/ 28080（宿主映射）
- 依赖：OpenAI-compatible API（通过 CozyGate 或直连）
