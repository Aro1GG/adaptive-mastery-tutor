# 自适应导师 (Adaptive Mastery Tutor)

基于 Bloom 掌握学习模型的苏格拉底式自适应教学系统。追踪每位学生的知识点掌握程度，根据薄弱项因材施教，通过深度推理性终测验证真懂假懂。

**不是一次性出题工具。** 学生进度跨会话持久化，下次对话自动从中断处继续。目标场景：接入飞书/微信/Slack 等聊天工具，每个学生独立对话、独立追踪、独立出题。

---

## 🎯 核心理念

```
知识点掌握 ≠ 能做选择题
知识点掌握 = 能解释因果 → 能预测结果 → 能分析新场景 → 能给出完整逻辑链
```

每个知识点的验证路径：

```
not_started → L1 识记 → L2 理解 → L3 应用 → 🏆 深度推理终测 → mastered
                                            │
                                          ❌ 未通过
                                            │
                                    标记 weak_areas
                                    换题型、换角度重测
                                            │
                                    直到真正掌握
```

---

## 📁 文件结构

```
adaptive-tutor/
├── SKILL.md                    # 教学交互方法论（Claude 的"脑子"）
├── tutor.py                    # 数据管理 CLI（进度持久化的"手"）
├── knowledge-points.yaml       # 知识点定义（一门课一份，可替换）
├── source.md                   # 知识源材料
└── students/                   # 学生进度文件（每人一个 JSON）
    ├── alice.json
    ├── bob.json
    └── ...
```

---

## 🚀 快速开始

### 前置条件

```bash
pip install pyyaml
```

### 教师模式（Claude Code）

```bash
# 创建学生
python tutor.py student create "张三"

# 查看知识图谱
python tutor.py knowledge list

# 看看张三该学什么
python tutor.py knowledge next "张三"
```

在 Claude Code 中直接提及教学内容，`adaptive-tutor` skill 自动激活：

> "我要给张三讲 TCP 三次握手，按认知层级出题考他"

### 查看进度

```bash
python tutor.py stats show "张三"   # 个人掌握度报告
python tutor.py stats all           # 全班概览
```

---

## 🧠 认知层级 × 题型矩阵

| 层级 | 目标 | 题型示例 | 评分方式 |
|------|------|----------|----------|
| **L1 识记** | 知道概念和事实 | 选择题、判断题、填空题 | 客观题自动评分 |
| **L2 理解** | 能用自己话解释 | 概念解释、情景预测、类比迁移 | Claude 语义判断 |
| **L3 应用** | 新场景中运用 | 案例分析、方案设计、假设推演 | Claude 语义判断 |
| **🏆 终测** | 多步逻辑链 | 逻辑链追溯、对立论证、系统推演、错误溯源 | Claude 严格评估 |

### 终测的通过标准

- ❌ 只给结论无推理 → 不通过
- ⚠️ 有推理但跳步 → 追问缺失环节
- ✅ 完整逻辑链 + 能解释边界条件 → 通过

---

## 📊 CLI 命令一览

```
tutor.py student list                    列出所有学生
tutor.py student show <name>             查看学生完整进度（JSON）
tutor.py student create <name>           新增学生
tutor.py student delete <name>           删除学生
tutor.py student update <name> <kp-id>   更新知识点状态（支持多参数）
tutor.py knowledge list                  列出所有知识点及依赖
tutor.py knowledge next <name>           智能推荐：下一步该学/重测什么
tutor.py knowledge unlocked <name>       显示前置条件已满足的知识点
tutor.py stats show <name>               个人掌握度报告（含弱项列表）
tutor.py stats all                       全班概览（进度条、百分比）
```

---

## 🏗️ 架构：多学生 × 多聊天渠道

`tutor.py` 已经为多学生场景设计好数据层。接入聊天工具后，每个学生的对话独立、进度独立。

### 目标架构

```
                      ┌─────────────────────┐
                      │   聊天渠道适配层      │
                      │  (飞书/Slack/微信等)  │
                      └──────────┬──────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        学生 Alice          学生 Bob           学生 Charlie
      消息: "我不懂       消息: "再考我        消息: "继续学
      三次握手"           一次握手"            传输层"
              │                  │                  │
              ▼                  ▼                  ▼
       ┌──────────────────────────────────────────────────┐
       │              教学后端 (Claude API)                │
       │                                                  │
       │  1. 识别学生身份 → 加载 students/<name>.json      │
       │  2. SKILL.md 作为系统指令注入                      │
       │  3. Claude 生成个性化回复 + 出题                   │
       │  4. 评估答案 → tutor.py 更新进度                  │
       │                                                  │
       └──────────────────────────────────────────────────┘
```

### 数据隔离

每个学生的进度文件完全独立：

```json
// students/alice.json
{
  "name": "Alice",
  "knowledge_points": {
    "tcp-handshake": {
      "status": "in_progress",
      "attempts": 3,
      "weak_areas": ["半连接队列", "SYN Flood 防御"],
      "quiz_history": [...]
    }
  }
}

// students/bob.json
{
  "name": "Bob",
  "knowledge_points": {
    "tcp-handshake": {
      "status": "mastered",
      "attempts": 4,
      "quiz_history": [...]
    }
  }
}
```

### 接入聊天工具的步骤

1. **选择渠道** — 飞书/企业微信/Slack/Discord/Telegram 等
2. **搭建 bot 后端** — Python Flask/FastAPI，接收 webhook
3. **集成 Claude API** — 注入 `SKILL.md` 作为 system prompt
4. **调用 tutor.py** — 每个请求前后读写对应学生的进度文件
5. **返回消息** — Claude 的回复通过 bot 发回学生

---

## 🔧 自定义知识源

换一门课只需要换两个文件。

### knowledge-points.yaml

```yaml
topic: "你的课程名"
knowledge_points:
  - id: kp-1
    name: "知识点名称"
    bloom_level: understand     # remember | understand | apply
    prerequisites: []           # 前置知识点 ID 列表
    key_concepts:
      - "核心概念 1"
      - "核心概念 2"
```

### source.md

写一份对应知识点的教材/笔记/文档。Claude 会用它来理解知识内容并生成题目。

---

## 📄 许可

MIT License
