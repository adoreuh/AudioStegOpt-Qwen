# 贡献指南

感谢您对音频信息隐藏系统项目的关注！我们欢迎所有形式的贡献，包括但不限于报告Bug、提出新功能建议、改进文档和提交代码。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [审查流程](#审查流程)

---

## 行为准则

本项目采用 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。参与本项目即表示您同意遵守此准则。

### 我们的承诺

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

---

## 如何贡献

### 报告 Bug

如果您发现了Bug，请通过 [GitHub Issues](https://github.com/yourusername/audio-stego/issues) 报告，并包含以下信息：

- **问题描述**: 清晰简洁地描述问题
- **复现步骤**: 详细说明如何复现问题
- **期望行为**: 描述您期望发生的行为
- **实际行为**: 描述实际发生的行为
- **环境信息**:
  - 操作系统及版本
  - Python版本
  - 项目版本/提交哈希
- **附加信息**: 截图、日志文件等

### 提出新功能

如果您有新功能建议：

1. 先检查是否已有类似的Issue
2. 创建新的Issue，使用 "Feature Request" 标签
3. 详细描述新功能及其使用场景
4. 如果可能，提供实现思路或参考

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/yourusername/audio-stego.git
   cd audio-stego
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **进行更改**
   - 编写代码
   - 添加测试
   - 更新文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```

5. **推送到您的Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建 Pull Request**
   - 描述您的更改
   - 关联相关Issue
   - 等待审查

---

## 开发环境设置

### 前置要求

- Python 3.8+
- Git
- (可选) ffmpeg

### 设置步骤

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/audio-stego.git
cd audio-stego/audio_stego

# 2. 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装开发依赖
pip install pytest black flake8 mypy

# 5. 验证安装
python -c "import audio_stego; print('安装成功')"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_stego.py

# 生成覆盖率报告
pytest --cov=audio_stego --cov-report=html
```

---

## 代码规范

### Python 代码风格

我们遵循 [PEP 8](https://pep8.org/) 规范，并使用以下工具：

- **Black**: 代码格式化
- **Flake8**: 代码风格检查
- **mypy**: 类型检查

```bash
# 格式化代码
black .

# 检查代码风格
flake8 .

# 类型检查
mypy .
```

### 代码规范要点

1. **命名规范**
   - 类名: `PascalCase`
   - 函数名: `snake_case`
   - 常量: `UPPER_CASE`
   - 私有变量: `_leading_underscore`

2. **文档字符串**
   ```python
   def process_audio(audio_path: str) -> dict:
       """
       处理音频文件并返回特征信息。

       Args:
           audio_path: 音频文件路径

       Returns:
           包含音频特征的字典

       Raises:
           FileNotFoundError: 文件不存在时
           ValueError: 文件格式不支持时
       """
       pass
   ```

3. **类型注解**
   ```python
   from typing import Dict, List, Optional

   def optimize_params(
       audio_features: Dict[str, float],
       message_length: int
   ) -> Optional[Dict[str, int]]:
       pass
   ```

4. **注释规范**
   - 使用中文注释
   - 解释"为什么"而不是"做什么"
   - 复杂算法需要详细注释

### 项目结构规范

```
audio_stego/
├── api/           # API端点
├── core/          # 核心算法
├── utils/         # 工具函数
├── tests/         # 测试文件
└── docs/          # 文档
```

---

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交类型

- **feat**: 新功能
- **fix**: Bug修复
- **docs**: 文档更新
- **style**: 代码格式（不影响功能）
- **refactor**: 代码重构
- **perf**: 性能优化
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动

### 提交示例

```bash
# 新功能
git commit -m "feat: 添加AI智能参数优化功能"

# Bug修复
git commit -m "fix: 修复MP3文件加载失败的问题"

# 文档更新
git commit -m "docs: 更新API文档和示例"

# 性能优化
git commit -m "perf: 优化DWT算法，提升30%速度"
```

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

示例：
```
feat(core): 添加音频质量分析功能

- 实现基于频谱特征的音频质量评估
- 集成AI模型进行智能分析
- 添加质量评分和推荐算法

Closes #123
```

---

## 审查流程

### Pull Request 规范

1. **PR标题**: 清晰描述更改内容
   ```
   feat: 添加批量音频处理功能
   fix: 修复FLAC文件内存泄漏
   ```

2. **PR描述**: 包含以下信息
   - 更改内容概述
   - 相关Issue链接
   - 测试情况
   - 截图（如适用）

3. **审查检查清单**
   - [ ] 代码符合规范
   - [ ] 测试通过
   - [ ] 文档已更新
   - [ ] 无合并冲突

### 审查标准

- **代码质量**: 可读性、可维护性
- **功能正确性**: 是否实现预期功能
- **测试覆盖**: 是否有足够的测试
- **文档**: 是否更新相关文档
- **性能**: 是否引入性能问题

---

## 发布流程

### 版本号规范

我们使用 [语义化版本](https://semver.org/lang/zh-CN/) (SemVer)：

- **MAJOR**: 不兼容的API更改
- **MINOR**: 向下兼容的功能添加
- **PATCH**: 向下兼容的问题修复

### 发布步骤

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建发布标签
4. 构建发布包
5. 发布到PyPI（如适用）

---

## 社区

### 沟通渠道

- **GitHub Issues**: Bug报告和功能请求
- **GitHub Discussions**: 一般性讨论
- **邮件**: 私密问题联系

### 贡献者名单

感谢所有为项目做出贡献的人！

<!-- 贡献者列表将自动生成 -->

---

## 许可证

通过贡献代码，您同意您的贡献将在 [MIT 许可证](LICENSE) 下发布。
