# 自适应导师 (Adaptive Mastery Tutor)

基于 Bloom 掌握学习模型的苏格拉底式自适应教学系统。追踪每位学生的知识点掌握程度，根据薄弱项因材施教，通过深度推理性终测验证真正掌握。

## 🎯 核心特性

- **逐级评估:** 识记 → 理解 → 应用 → 深度推理终测
- **学生追踪:** 每位学生独立的进度文件，跨会话持久化
- **自适应出题:** 薄弱项换题型、换角度重测，防止死记硬背
- **深度推理终测:** 要求完整逻辑链，不能靠猜或背通过
- **知识源可替换:** 换一套 `knowledge-points.yaml` 就是换一门课

## 📁 文件结构

```
adaptive-tutor/
├── SKILL.md                    # 教学交互方法论
├── tutor.py                    # 数据管理 CLI 脚本
├── knowledge-points.yaml       # 知识点定义（示例：计算机网络-传输层）
├── source.md                   # 知识源材料
└── students/                   # 学生进度文件（JSON）
```

## 🚀 快速开始

### 前置条件

```bash
pip install pyyaml
```

### 创建学生

```bash
python tutor.py student create "张三"
```

### 查看知识图谱

```bash
python tutor.py knowledge list
python tutor.py knowledge next "张三"
```

### 教学过程

在 Claude Code 中说：`/adaptive-tutor` 或者提到教学内容，skill 会自动激活。

手动调用：`Skill` 工具 `adaptive-tutor`

### 查看进度

```bash
python tutor.py stats show "张三"
python tutor.py stats all
```

## 🧠 认知层级 × 题型

| 层级 | 目标 | 题型示例 |
|------|------|----------|
| L1 识记 | 知道概念和事实 | 选择题、判断题、填空题 |
| L2 理解 | 懂为什么 | 概念解释、情景预测、类比迁移 |
| L3 应用 | 在新场景使用 | 案例分析、方案设计、假设推演 |
| 🏆 终测 | 深度推理 | 逻辑链追溯、对立论证、系统推演、错误溯源 |

## 📊 CLI 命令一览

```
tutor.py student list                    列出所有学生
tutor.py student show <name>             查看学生进度
tutor.py student create <name>           新增学生
tutor.py student delete <name>           删除学生
tutor.py student update <name> <kp-id>   更新掌握状态
tutor.py knowledge list                  列出知识点
tutor.py knowledge next <name>           下一步该学什么
tutor.py knowledge unlocked <name>       已解锁的知识点
tutor.py stats show <name>               个人掌握度报告
tutor.py stats all                       全班概览
```

## 🔧 自定义知识源

创建你自己的 `knowledge-points.yaml`：

```yaml
topic: "你的课程名"
knowledge_points:
  - id: kp-1
    name: "知识点名称"
    bloom_level: understand  # remember | understand | apply
    prerequisites: []        # 前置知识点 ID
    key_concepts:
      - "核心概念1"
      - "核心概念2"
```

然后创建对应的 `source.md` 作为知识源材料。

## 📄 许可

MIT License
