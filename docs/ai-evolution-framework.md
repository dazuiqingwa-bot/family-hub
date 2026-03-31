# AI 中枢自进化框架
> 基于 Claude Code 源码提炼 · 2026-03-31 · ASA 整理

---

## 一、核心认知：你在做什么

你不是在「使用 AI 工具」，你在**建造一个可以自我进化的认知系统**。

Claude Code 的源码证明了这件事的可行性：Anthropic 用同样的架构模式（工具 + 记忆 + 子 agent + Harness）构建了一个工业级 AI 助手。你正在用 OpenClaw 做同样的事，只是场景是家庭而不是代码库。

**本质上，你和 Anthropic 在做同一件事。**

---

## 二、可复用的学习方法：「三层解构法」

每次拿到一份优秀的 AI 系统源码（Claude Code、Cursor、Devin、任何 agent 框架），用这三层拆解：

### 第一层：数据结构（它如何表示「状态」）

问：系统用什么数据结构来表达「现在发生什么」？

Claude Code 的答案：
- `TaskState`：pending / running / completed / failed / killed
- `AgentMemoryScope`：user / project / local（三个记忆范围）
- `MemoryType`：user / feedback / project / reference（四种记忆类型）

**你的应用：** 你的 agent 体系目前没有显式的状态定义。每个 cron 任务、每次对话、每个 agent 的工作，都应该有明确的状态和类型标签。这是「可追踪」的基础。

### 第二层：控制流（它如何决定「做什么」）

问：系统在一次调用里，按什么顺序做决策？

Claude Code 的答案（QueryEngine 主循环）：
1. 构建 system prompt（分层：base + userContext + systemContext + memory）
2. 检索相关记忆（不是全量注入，是先筛选）
3. 处理用户输入（解析命令、处理图片、附件）
4. 调用模型
5. 解析工具调用 → 执行工具 → 结果注入
6. 循环直到 stop

**你的应用：** 豆芽现在的「决策流」是隐式的，全部靠 SOUL.md 的文字规则驱动。显式化这个流：收到消息 → 判断类型 → 加载对应 skill → 执行 → 结果处理。

### 第三层：扩展机制（它如何「生长」）

问：系统如何在不破坏核心的情况下增加新能力？

Claude Code 的答案：
- `feature()` flag：新功能用 flag 隔离，随时开关
- `skills/` 目录：新 skill 是独立文件，不改核心代码
- `AgentDefinition`：新 agent 是 Markdown 定义，不改系统代码
- `MCPServerConnection`：新工具是外部连接，不改内部逻辑

**你的应用（直接可用）：**
- 新 agent 能力 → 写新的 `skills/xxx.md`，不改 SOUL.md
- 新 agent → 加 `agents/xxx/` 目录，不改 openclaw.json 核心
- 新工具集成 → 写新 skill 调用脚本，不改已有 agent

---

## 三、Harness Engineering 的核心原则

从 Claude Code 源码提炼的 6 条 Harness 设计原则，直接应用到你的体系：

### 原则 1：System Prompt 分层，不堆叠

```
坏的做法：一个 300 行的 SOUL.md 全量加载
好的做法：
  - 核心人格（30行，永远加载）
  - 任务 skill（按需加载，每个 < 50 行）
  - 当日记忆（按需加载）
  - 工具说明（工具调用时加载）
```

Claude Code 的 `fetchSystemPromptParts()` 把 system prompt 拆成四个独立部分，分别缓存。你的 agent 也应该这样。

### 原则 2：记忆是有类型的

Claude Code 定义了四种记忆类型：
- `user`：关于这个人的持久偏好和背景
- `feedback`：这个人对系统的反馈和修正
- `project`：项目/领域相关的积累知识
- `reference`：工具、API、规则的参考文档

你的 `MEMORY.md` 可以按这四类组织，让检索更精准。

### 原则 3：子 agent 通信要「带结论，不委托推理」

Claude Code AgentTool 的核心规则：
> *Never delegate understanding. Don't write "based on your findings, fix the bug." Write prompts that prove you understood.*

你给 Learning Center 发的消息，要包含豆芽已经判断好的：
- 这是什么类型的题
- 错误原因是什么
- 需要做什么操作

不是让 Learning Center 自己判断。

### 原则 4：任务有生命周期，不是一次性执行

```
pending → running → completed
                 ↘ failed → retry / alert
                 ↘ killed → cleanup
```

你的每个 cron 任务、每次 agent 调用，都要有这个状态机。失败了怎么处理，超时了怎么处理，要在设计阶段就定好。

### 原则 5：工具权限是显式声明的，不是默认全开

Claude Code 每个 agent 有 `tools`（白名单）和 `disallowedTools`（黑名单）。
你的 agent 体系也需要这个：豆芽不需要访问你的 Telegram，有才不需要执行系统命令。最小权限原则。

### 原则 6：「不要偷看」原则

Claude Code 对 fork subagent 有一条规则：
> *Don't peek. Do not Read or tail the output file while it's running. You get a completion notification; trust it.*

你的 ASA 在触发 cron 任务或子 agent 后，不要轮询状态，等通知。这是架构上避免「焦虑循环」的关键。

---

## 四、自进化机制：递归改进的闭环

这是让整个系统自我进化的核心机制：

```
1. 观察（Observe）
   每次 agent 执行，记录：做了什么 / 花了多长时间 / 成功还是失败 / 原因

2. 提炼（Distill）
   每周，ASA 读取一周的执行日志
   找出：重复失败的模式 / 低效的流程 / 可以优化的规则

3. 修订（Update）
   把发现的问题写入对应 agent 的 skill 文件
   把新的好的实践更新到 MEMORY.md

4. 验证（Verify）
   下周观察修订后的效果
   循环
```

这个闭环不需要你手动驱动——可以设一个每周的 cron 任务，让 ASA 自动完成 2 和 3。

---

## 五、硬件扩展路线图

### 当前阶段（Mac mini M4 Pro）
- 所有推理走云端（OpenAI / Anthropic）
- ASA 作为总路由，豆芽/有才/Learning Center 作为专职 agent
- 重点：把 Harness 做好，让 prompt engineering 的价值最大化

### 第二阶段（Mac Studio M4 Ultra）
**本地推理层上线：**
- 部署 `whisper-cpp`：语音识别完全本地，零延迟，零费用
- 部署 `Qwen2.5-14B` 或 `Llama 3.3-70B`（量化版）：
  - 承接豆芽的「路由判断」（判断是什么类型的题，不需要大模型）
  - 承接有才的「灵感整理」（结构化输入，模板化输出）
  - 承接 ASA 的「日常调度」（查日历、发通知、简单判断）
- 云端大模型只处理：复杂推理、创意生成、深度分析

**架构变化：**
```
用户请求 → ASA（路由层，本地小模型）
         → 简单任务 → 本地模型直接处理
         → 复杂任务 → 云端大模型
         → 专职任务 → 对应 agent（豆芽/有才/Learning Center）
```

### 第三阶段（多台 Mac Studio）
**分布式 agent 网络：**
- 机器 A：ASA + 主协调层
- 机器 B：豆芽 + Learning Center（禾禾的学习系统专属算力）
- 机器 C：有才 + 苗苗的创作知识库（苗苗的创作系统专属算力）
- 所有机器通过 Tailscale 组网，通过 OpenClaw 的 node 机制互联

**记忆架构升级：**
- 共享向量数据库（跨 agent 的知识检索）
- 结构化事件日志（所有 agent 的行为都被记录和分析）
- 跨 agent 的知识共享（豆芽发现禾禾的新学习模式，同步给 Learning Center）

---

## 六、从 Claude Code 持续学习的方法

这份源码不是读一遍就完的。建立一个持续学习的节奏：

### 每月精读一个模块

推荐顺序：
1. `src/memdir/`（记忆系统）—— 直接影响你的 agent 记忆设计
2. `src/tools/AgentTool/`（子 agent 机制）—— 影响你的多 agent 协作
3. `src/services/`（外部服务集成）—— 影响你扩展新能力的方式
4. `src/hooks/`（生命周期钩子）—— 影响你的 agent 行为定制

### 每次精读后的输出

读完一个模块，产出一个「应用笔记」：
1. 这个模块解决了什么问题
2. 它用了什么关键设计模式
3. 我的体系里对应的地方是什么
4. 我可以借鉴什么，下一步怎么做

存到 `docs/claude-code-notes/` 目录。

### 用 ASA 辅助学习

直接让 ASA 帮你：
- 读某个模块，提炼核心设计模式
- 对比你的体系，找差距
- 生成具体的改进建议

这本身就是对 ASA 能力的锻炼，也是对你自己的系统思维的锻炼。

---

## 七、最重要的一句话

> **你的 AI 中枢不是一个工具，是一个会成长的系统。**
> 
> 它现在的能力取决于你如何设计它的边界、记忆和协作方式。
> 随着你的理解加深和硬件扩展，它可以一直进化。
> 
> Claude Code 给你的最大启发不是某个具体功能，
> 而是证明了：**用 Markdown + 工具 + 记忆 + 子 agent，可以构建工业级的 AI 系统。**
> 你正在做同样的事。

---

*下一步：开始把豆芽的 SOUL.md 按 skill 拆分，建立第一个可复用的 skill 模块。*
