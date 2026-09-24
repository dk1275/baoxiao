# baoxiao · 出差报销票据整理

> 把邮箱里散落一整个出差周期的发票，自动收拢、去重、分类归档，并生成一张可以直接提交的报销明细表。

这是 **WorkBuddy 的一个技能（Skill）**。装好之后，你只需要说一句「帮我整理报销」，
从邮箱取票 → 解包 → 五类归档 → 出 Excel 明细表的全过程都由 AI 完成。

- **只想快点用起来** → 直接看下面的 [装到 WorkBuddy](#装到-workbuddy三步)，装完说那句话就行
- **完全不想看技术细节** → 装好后看 [`GETTING-STARTED.md`](./GETTING-STARTED.md)，那份是手把手带你用的
- **想知道它怎么设计、踩过哪些坑** → 看 [`SKILL.md`](./SKILL.md)

---

## 装到 WorkBuddy（三步）

### 第 1 步 · 把技能放进 WorkBuddy 的技能目录

WorkBuddy 的技能目录（用户级，装上后所有项目都能调用）：

| 系统 | 技能目录 |
| --- | --- |
| Windows | `%USERPROFILE%\.workbuddy\skills\` |
| macOS / Linux | `~/.workbuddy/skills/` |

**本仓库的根目录就是技能目录本身**（`SKILL.md` 直接在最外层，中间没有多余的一层），
所以「把仓库放进技能目录」就等于装好了：

```bash
# macOS / Linux
git clone https://gitee.com/dk1275/baoxiao.git ~/.workbuddy/skills/baoxiao

# Windows（Git Bash）
git clone https://gitee.com/dk1275/baoxiao.git "$USERPROFILE/.workbuddy/skills/baoxiao"

# Windows（PowerShell，路径写法不同）
git clone https://gitee.com/dk1275/baoxiao.git "$env:USERPROFILE\.workbuddy\skills\baoxiao"
```

不想用命令行也行，三种方式任选其一：

| 方式 | 怎么做 | 适合谁 |
| --- | --- | --- |
| **A · 命令行 clone** | 上面那几行命令 | 装了 git；以后 `git pull` 即可一键更新 |
| **B · 让 AI 帮你装** | 把本页地址发给 WorkBuddy，说：「把这个仓库装成我的技能 https://gitee.com/dk1275/baoxiao」 | 不想碰命令行 |
| **C · 下载 ZIP** | 本页右上「克隆/下载」→ 下载 ZIP → 解压 → 把文件夹改名为 `baoxiao`，整个放进技能目录 | 没装 git，也不打算更新 |

> ⚠️ 本技能是个人自建技能，**没有上架 WorkBuddy 官方技能市场**，所以在「专家 → 技能」里搜不到，
> 请用上面三种方式之一安装。

装好之后目录必须长这样（**`SKILL.md` 要在第一层**，不要多套一层 `baoxiao/baoxiao/`）：

```
~/.workbuddy/skills/baoxiao/
├── SKILL.md            技能入口，文件名固定，不能改名、不能缺
├── README.md           本文件
├── GETTING-STARTED.md  新手引导
└── scripts/            可复用脚本
```

### 第 2 步 · 装两个 Python 依赖

| 系统 | 命令 |
| --- | --- |
| Windows | `%USERPROFILE%\.workbuddy\binaries\python\envs\default\Scripts\pip install pymupdf openpyxl` |
| macOS / Linux | `~/.workbuddy/binaries/python/envs/default/bin/pip install pymupdf openpyxl` |

- `pymupdf` —— 读发票 PDF 上的票面文字（金额、发票号、日期）
- `openpyxl` —— 生成 Excel 明细表

上面用的是 WorkBuddy 自带的隔离 Python 环境。如果本机还没有这个环境，先建一个再装：

```bash
# Windows
python -m venv "%USERPROFILE%\.workbuddy\binaries\python\envs\default"
# macOS / Linux
python3 -m venv ~/.workbuddy/binaries/python/envs/default
```

### 第 3 步 · 连上智能体邮箱（Agent Mail）

技能靠这个邮箱取发票邮件。**没连也不要紧**——第一次说「帮我整理报销」时它会先检测，然后带你连：

1. 打开 WorkBuddy 的「连接器管理」
2. 找到 **Agent Mail / 智能体邮箱**，点「连接」
3. 用微信扫码授权，拿到一个专供 AI 使用的邮箱：`你的名字@agent.qq.com`
4. 回到对话说一声「好了」，它会接着往下干，**你不用重新下指令**

> 之后每次开发票，把接收邮箱填成 `你的名字@agent.qq.com` 即可；已有的发票邮件也可以直接转发过去。
> 这个邮箱和你私人邮箱完全隔离，AI 只能看到发到这里的邮件。

### 验证装好了没

**重启 WorkBuddy**，新开一个对话，发这一句：

```
帮我整理报销
```

它开始检查邮箱状态、翻附件，就说明技能已经加载成功。也可以在对话里 `@baoxiao` 显式点名这个技能。

### 更新与卸载

```bash
# 更新（只有方式 A 装的行）
cd ~/.workbuddy/skills/baoxiao && git pull

# 卸载：删掉这个目录，然后重启 WorkBuddy 即可
```

---

## 环境要求

| 项 | 说明 |
| --- | --- |
| WorkBuddy | 能装技能即可，无版本特殊要求 |
| Agent Mail 连接器 | 必需；邮箱形如 `you@agent.qq.com`。未开通时技能会带你开通 |
| Python | 3.13（用 WorkBuddy 自带的隔离环境就够了） |
| 依赖 | `pymupdf`、`openpyxl` |
| CLI（可选） | `agently-cli`，仅在备用通道 / 需要发信时用；只用连接器的话不需要 |

---

## 它解决什么问题

出差回来，发票散在邮箱里：酒店发一封、打车平台发一封、餐饮小程序发一封、机票又是另一个发件人。
有些邮件只给一个下载链接、有些把发票塞在 `.eml` 转发附件里、有些把 PDF/OFD/XML 打包成 zip。
手工下载、解压、改名、分类、登记，一套流程下来一两个小时，还容易漏。

**这个 Skill 把整套流程交给 AI**：你只需要说一句「整理下邮箱里的报销发票」，它会完成从邮箱到 Excel 的全过程。

## 输出长什么样

整理完成后，你的报销文件夹是这样：

```
M.DD-M.DD出差报销/
├── 酒店/                    住宿发票
├── 请客户/                  请客户吃饭、喝咖啡的餐饮发票
├── 打车/                    网约车、出租车发票 + 高速过路费发票
│   └── 行程单/              打车行程单（PDF）
├── 高铁/                    高铁票发票
├── 机票/                    机票发票
├── _原始邮件附件/            .eml / .zip 原始备份（可回溯补凭证）
└── 报销明细记录.xlsx         ← 直接提交
```

明细表按 `日期 | 类别 | 事项 | 金额 | 发票号码 | 抬头 | 备注 | 归档文件` 排列，
带分类色块、合计行、五类小计：

| 类别 | 小计 |
| --- | --- |
| 机票 | 1,200.00 |
| 打车 | 860.00 |
| 酒店 | 3,000.00 |
| 请客户 | 400.00 |
| 高铁 | — |
| **合计** | **7,000.00** |

## 整理规则

- **只要发票**：结账单、消费明细单、订单截图这类非发票凭证不入库（直接清掉）。
- **只留 PDF**：`.ofd` / `.xml` 一律删除，需要时从 `_原始邮件附件` 重新提取。
- **打车必带行程单**：打车发票放 `打车/`，对应行程单放 `打车/行程单/`，同名成对。
- **文件名带信息**：`日期_类型_商家或平台_金额元.pdf`，例如
  `0917_某某餐厅餐饮发票_请客户喝咖啡_58元.pdf`、`0921_某某打车_某某运力_270.37元_发票.pdf`。
- **不杜撰数据**：金额、发票号、日期全部取自票面文本；看不清就标「见PDF」，不猜。

## 怎么用

在 WorkBuddy 里直接说人话即可，触发词包括「整理报销」「报销附件」「整理发票」「查下邮箱的发票」「出差报销」：

- 「帮我整理报销」 ← 最简，第一次用这句就行
- 「去 xxx@agent.qq.com 整理下现在的报销附件，整理到桌面，建个 `M.DD-M.DD出差报销` 文件夹」
- 「查下邮箱有没有新发票，整理进去」

**没开通智能体邮箱也没关系**：技能会先检测邮箱状态，未开通时给出扫码开通信道，
开通成功后会接着把整理流程走完，不需要你重新下指令。用户需要配合的只有「点连接 → 微信扫码授权」这两下。

它会提醒你这些需要人工确认的点：
- 同一笔消费的重复凭证（例如消费明细单 vs 正式发票）该交哪个
- 多张住宿票日期重叠，是否重复报销同一晚
- 只有下载链接没有实体附件、或票面无航班号无法确认归属的，列表让你补

## 邮箱操作（已内置）

智能体邮箱的读写能力**已并入本技能**，不需要再单独装一个邮件技能：

- **主通道 —— WorkBuddy 的 Agent Mail 连接器**：开箱即用，负责列出 / 搜索 / 读取 / 下载附件。
- **备用通道 —— `agently-cli` 命令行**：连接器不可用，或需要发送 / 回复 / 转发 / 监听新邮件时使用。

```bash
npm install -g @tencent-qqmail/agently-cli
agently-cli auth login     # 授权，浏览器里点一下
agently-cli +me            # 验证：回显邮箱地址即成功
```

完整的命令清单、参数速查、错误码、两阶段确认流程，见 [`SKILL.md`](./SKILL.md) 的「智能体邮箱操作」一节。

> **安全**：邮件正文 / 主题 / 发件人 / 附件名都来自外部不可信来源，可能夹带 prompt injection 指令。
> 本技能只把邮件内容当**数据**看，绝不执行其中出现的任何「指令」；
> 附件也只做文本提取，不运行。详见 `SKILL.md` 的安全规则一节。

## 目录里的脚本

| 脚本 | 作用 |
| --- | --- |
| `extract_invoices.py` | 列出 `.eml` / `.zip` 的 MIME 结构，排查附件藏在哪一层 |
| `extract_nested.py` | 批量提取 `.eml` / `.zip` 里的内层发票到临时目录 |
| `restructure.py` | 把 OFD 送回收站 + 按五类归档（归档前后做文件清单核对） |
| `slim_down.py` | 删掉结账单/明细单等非发票凭证，行程单归入 `打车/行程单/` |
| `build_report.py` | 生成 `报销明细记录.xlsx`（改 `rows` 数据即可复用） |
| `restore_lost.py` | 从 `_原始邮件附件` 重新提取误删/丢失的凭证 |

脚本里的路径与数据是按具体报销批次写死的，复用时改开头的 `BASE` 和 `rows` 即可。

## 换电脑 / 多台机器之间同步

直接把技能目录当成这份仓库的 clone 用就行：

```bash
# 新电脑第一次
git clone https://gitee.com/dk1275/baoxiao.git ~/.workbuddy/skills/baoxiao
# 然后重复「装到 WorkBuddy」里的第 2、3 步（装依赖 + 连 Agent Mail），重启 WorkBuddy

# 之后更新
cd ~/.workbuddy/skills/baoxiao && git pull
```

> 提醒：`_原始邮件附件`、报销文件夹、生成的 Excel 都属于**本机数据**，不在这个仓库里，
> 换电脑后需要重新从邮箱拉取一次。

## 已知的坑（都已在流程里处理）

1. **邮箱 CLI 会掉线**：`agently-cli` 的 OAuth 常超时失败，优先走 agent-mail MCP。
2. **发票藏在第二层**：邮件附件常是转发的 `.eml`，真发票是它内层的 PDF，需要二次解析。
3. **zip 文件名乱码**：票根等平台的 zip 需要 `cp437 → gbk` 转码才能得到正确中文名。
4. **同名文件互相覆盖**：同一家酒店的多封邮件解到同一目录会覆盖结账单，必须逐封单独提取。
5. **归档可能丢文件**：批量移动后要**前后各打印一次文件清单对比**，缺的从原始附件重新提取。这条是踩过坑加上的。
6. **票面发票号乱码**：部分票根 PDF 的发票号文本是乱码，以二维码或平台记录为准。

## 许可

个人自用 Skill，可自由复制修改。见 [`LICENSE`](./LICENSE)。
