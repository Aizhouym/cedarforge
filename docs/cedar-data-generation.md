# Cedar SFT 数据构造方案

## 核心原则

数据构造的目标不是"让模型背住 Cedar 的例子"，而是让模型理解 Cedar 的**生成规则**。
这意味着：覆盖语法空间 > 堆积数量，多样性 > 重复，错误对比 > 只看正确。

---

## 一、数据来源分层

按质量和可信度分为三层，构造时混合使用：

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Ground Truth（真实数据）                     │
│  来源: Cedar 官方 repo / 文档 / 论文                    │
│  质量: ★★★★★   数量: ~300-500 条                      │
│  作用: 作为 seed data + validation benchmark           │
├─────────────────────────────────────────────────────┤
│  Layer 2: Validated Synthetic（验证过的合成数据）       │
│  来源: 强模型生成 → Cedar CLI 验证通过                  │
│  质量: ★★★★☆   数量: ~3000-5000 条                    │
│  作用: 主要训练数据                                     │
├─────────────────────────────────────────────────────┤
│  Layer 3: Negative Examples（反例数据）                │
│  来源: 故意注入错误 + 模型自然犯错收集                   │
│  质量: ★★★★☆   数量: ~1500-2500 条                    │
│  作用: 教模型识别和修正错误                              │
└─────────────────────────────────────────────────────┘
```

---

## 二、Layer 1: Ground Truth 数据提取

### 2.1 从 cedar-integration-tests 提取

这是最有价值的数据源。每个 integration test 包含完整的
policy + schema + entities + authorization requests + expected results。

```
cedar-integration-tests/
├── tests/
│   ├── example_use_cases_doc/    # 文档示例场景
│   ├── multi/                   # 多策略交互
│   ├── ip/                      # IP 地址扩展
│   └── corpus/                  # 模糊测试生成的语料
│       └── ...                  # (数百个自动生成的测试)
```


### 2.2 从 cedar-examples 提取

```
cedar-examples/
├── tinytodo/          # 任务管理应用
│   ├── policies.cedar
│   ├── entities.json
│   └── tinytodo.cedarschema
├── cedar-example-use-cases/
│   ├── document_cloud/    # 文档云存储
│   ├── tags_n_roles/      # 标签 + 角色
│   ├── hotel_chains/      # 酒店管理
│   └── tax_preparer/      # 税务处理
└── ...
```

每个示例应用提取方式：
1. 读取 .cedar 文件中的每条策略
2. 读取 .cedarschema
3. 为每条策略编写自然语言描述（手动或用强模型辅助）
4. 构造 instruction → policy 的训练对

### 2.3 从官方文档提取

Cedar 文档（docs.cedarpolicy.com）中的关键页面：

| 页面 | 可提取内容 |
|------|-----------|
| Basic syntax | 每个语法元素的示例 + 说明 |
| Policy grammar | 完整 EBNF 规则 |
| Operators | 每个操作符的用法示例 |
| Schema | Schema 语法 + 验证规则 |
| Best practices | 推荐写法 vs 反模式 |
| Templates | 模板语法和使用场景 |

**Current status of the Layer 1 docs pipeline**

已完成：
- 已有官方文档抓取脚本 `src/data/scrape_docs.py`
- 已配置一组 Cedar 官方文档页面作为抓取入口
- 已能逐页抓取 HTML，并抽取 code block、段落描述、`h2/h3` 标题上下文
- 已能按启发式区分 `policy` / `schema` / `mixed`
- 已输出原始 JSONL 到 `data/layer1_raw/cedar_docs.jsonl`
- 当前仓库里已有 72 条文档样本，其中 66 条 `policy`、6 条 `schema`
- 每条记录已带上 `source / page_url / page_title / section_heading / nl_description / cedar_code / code_type / needs_expansion`

还需要做：
- 将当前抓取逻辑对齐到正式版规则，改为只处理 `<code>` / `<pre>` 块，并显式以最近的标题或段落作为 `nl_description`
- 将 `section_heading` 明确绑定为所在 section 的 `<h2>/<h3>`
- 将 `code_type` 判断规则固定为：
  `permit/forbid -> policy`，`entity/action appliesTo -> schema`，两者同时出现则拆成两条，其他如 JSON / shell 一律跳过
- 用 `WebFetch + BeautifulSoup` 替换当前基于 `urllib + HTMLParser` 的实现
- 复跑抓取并重建 `data/layer1_raw/cedar_docs.jsonl`
- 对抓下来的文档样本做人工 spot check，重点检查空 `page_title`、空 `section_heading`、描述错配和 mixed block 拆分质量
- 在后处理阶段补充去重、质量过滤和后续 `needs_expansion` enrichment 流程

**Layer 1 document scraping method (English spec)**

Use `WebFetch` to download each documentation page as raw HTML, then parse the HTML with Python `BeautifulSoup`.

Extraction rules:
- Iterate over every `<code>` and `<pre>` block on the page.
- For each code block, use the nearest preceding heading or paragraph as `nl_description`.
- Use the enclosing section's `<h2>` or `<h3>` as `section_heading`.
- Classify `code_type` with simple content rules:
  - If the block contains `permit` or `forbid`, label it as `policy`.
  - If the block contains `entity` or `action ... appliesTo`, label it as `schema`.
  - If both policy and schema signals appear in the same block, split it into two records.
  - If the block is something else, such as JSON or shell, skip it.

Recommended output fields:
`source`, `page_url`, `page_title`, `section_heading`, `nl_description`, `cedar_code`, `code_type`, `needs_expansion`.

---

## 三、Layer 2: Validated Synthetic 数据生成

这是数据量的主体。使用强模型（Claude / GPT-4）作为 teacher 生成，
然后用 Cedar CLI 验证每一条。

### 3.1 业务场景矩阵

先定义要覆盖的业务场景维度，确保多样性：

**行业维度（10+个）：**
```
医疗健康: 患者记录访问、处方权限、科室管理
金融: 交易审批、账户查看、合规审计
教育: 课程管理、成绩查看、学生隐私
电商: 商品管理、订单操作、卖家权限
SaaS 多租户: 租户隔离、管理员权限、API 访问
政府: 公文流转、数据分级、跨部门协作
媒体: 内容审核、发布权限、订阅者访问
IoT: 设备控制、数据读取、固件更新
游戏: 物品交易、聊天管理、GM 权限
HR: 薪资查看、假期审批、绩效评估
```

**授权模型维度（5个）：**
```
RBAC: 基于角色的简单权限
ABAC: 基于属性的动态权限
ReBAC: 基于关系的层级权限
混合: RBAC + ABAC 组合
多策略交互: permit + forbid 冲突解决
```

**复杂度维度（4级）：**
```
L1 - 简单: 单策略、单条件、直接匹配
L2 - 中等: 2-3 个条件组合、层级关系
L3 - 复杂: 多策略交互、嵌套条件、template
L4 - 边界: 类型不匹配、空集、循环层级
```

**总组合空间: 10 × 5 × 4 = 200 个"场景槽"**
每个槽生成 15-25 条 → **3000-5000 条**

### 3.2 合成 Prompt 模板

用于向 Claude/GPT-4 发送生成请求的 prompt：

```markdown
你是一位 Cedar 策略语言专家。请根据以下要求生成训练数据。

## 场景信息
- 行业: {industry}
- 授权模型: {auth_model}
- 复杂度: {complexity}

## 要求
1. 先设计一个合理的 Cedar Schema（.cedarschema 格式）
2. 基于该 Schema，生成一个自然语言需求描述
3. 编写满足该需求的 Cedar 策略
4. 提供 3-5 个 authorization request 测试用例
   （包含 expected decision: ALLOW 或 DENY）

## 输出格式（JSON）
{
  "schema": "entity User in [Group] { ... }; ...",
  "natural_language_requirement": "...",
  "cedar_policy": "permit(...) when { ... };",
  "test_cases": [
    {
      "principal": "User::\"alice\"",
      "action": "Action::\"read\"",
      "resource": "Document::\"doc1\"",
      "context": {},
      "expected_decision": "ALLOW",
      "explanation": "因为 alice 是 doc1 的 owner"
    }
  ]
}

## 重要约束
- Cedar 策略必须严格遵循官方语法
- Entity 引用格式: Type::"id"
- 策略末尾必须有分号 ;
- when/unless 条件用花括号 { }
- scope 中 principal/action/resource 用逗号分隔
- 确保 schema 和 policy 中的类型名一致
```

### 3.3 验证流水线

**每条合成数据必须通过以下验证才能入库：**

```python
def validate_synthetic_sample(sample: dict) -> tuple[bool, list[str]]:
    """验证一条合成数据的质量"""
    errors = []
    
    # Step 1: 语法检查
    parse_result = run_cedar_cli(
        "validate", 
        "--policies", sample["cedar_policy"]
    )
    if not parse_result.success:
        errors.append(f"Syntax error: {parse_result.stderr}")
    
    # Step 2: Schema 验证
    if sample.get("schema"):
        schema_result = run_cedar_cli(
            "validate",
            "--policies", sample["cedar_policy"],
            "--schema", sample["schema"]
        )
        if not schema_result.success:
            errors.append(f"Schema error: {schema_result.stderr}")
    
    # Step 3: 语义验证（跑测试用例）
    if sample.get("test_cases") and not errors:
        for i, tc in enumerate(sample["test_cases"]):
            auth_result = run_cedar_cli(
                "authorize",
                "--policies", sample["cedar_policy"],
                "--entities", tc.get("entities", "[]"),
                "--principal", tc["principal"],
                "--action", tc["action"],
                "--resource", tc["resource"]
            )
            actual = "ALLOW" if auth_result.stdout.strip() == "ALLOW" else "DENY"
            if actual != tc["expected_decision"]:
                errors.append(
                    f"Test case {i}: expected {tc['expected_decision']}, "
                    f"got {actual}"
                )
    
    # Step 4: 格式检查
    if not sample["cedar_policy"].strip().endswith(";"):
        errors.append("Policy missing trailing semicolon")
    
    if not sample.get("natural_language_requirement"):
        errors.append("Missing natural language requirement")
    
    return (len(errors) == 0, errors)
```

**验证结果处理：**
```
验证通过 → 直接入库（Layer 2）
语法错误 → 修正后重新验证，或转为 Layer 3 反例数据
语义错误 → 调整测试用例或策略，或丢弃
```

### 3.4 合成数据去重与多样性保障

```python
def check_diversity(new_sample, existing_samples):
    """确保新样本与已有数据有足够差异"""
    
    # 1. 结构指纹去重
    fingerprint = extract_structure(new_sample["cedar_policy"])
    # 结构 = (effect, scope_pattern, condition_operators, depth)
    # 例如: ("permit", "principal==,action==,resource_in", 
    #         ["&&", "has", "=="], 2)
    
    if fingerprint in existing_fingerprints:
        return False, "Duplicate structure"
    
    # 2. 检查该场景槽是否已满
    slot = (new_sample["industry"], new_sample["auth_model"], 
            new_sample["complexity"])
    if slot_counts[slot] >= MAX_PER_SLOT:
        return False, f"Slot {slot} full"
    
    # 3. 语法覆盖检查
    features = extract_features(new_sample["cedar_policy"])
    # features = {用了哪些操作符, 条件数量, 是否有unless, 
    #             是否有template, 实体层级深度, ...}
    
    return True, "OK"
```

---

## 四、Layer 3: 反例数据（Error Detection & Correction）

这层数据对消除 syntax/semantic error 至关重要。

### 4.1 系统性错误注入

定义一个**错误注入器**，对正确的 Cedar 策略自动注入常见错误：

```python
ERROR_INJECTORS = {
    # ====== 语法错误 ======
    "missing_semicolon": {
        "transform": lambda p: p.rstrip().rstrip(";"),
        "error_description": "策略末尾缺少分号 ;",
        "frequency": 0.15  # 15% 的反例用这种错误
    },
    "single_equals": {
        "transform": lambda p: p.replace("==", "=", 1),
        "error_description": "使用了赋值符 = 而非比较符 ==",
        "frequency": 0.15
    },
    "missing_action_prefix": {
        "transform": lambda p: p.replace('Action::', '', 1),
        "error_description": "Action 实体缺少 Action:: 类型前缀",
        "frequency": 0.10
    },
    "wrong_quotes": {
        "transform": lambda p: p.replace('::"', "::\'", 1),
        "error_description": "实体标识符使用了单引号而非双引号",
        "frequency": 0.08
    },
    "scope_condition_confusion": {
        "transform": lambda p: move_when_to_scope(p),
        "error_description": "将 when 条件错误地放在了 scope 中",
        "frequency": 0.10
    },
    "missing_braces": {
        "transform": lambda p: p.replace("when {", "when (", 1)
                                .replace("}", ")", 1),
        "error_description": "when 子句使用了圆括号 () 而非花括号 {}",
        "frequency": 0.10
    },
    
    # ====== 语义错误 ======
    "unless_logic_inversion": {
        "transform": lambda p: p.replace("when", "unless", 1),
        "error_description": "错误使用 unless 导致逻辑反转，"
                           "本意是允许满足条件的请求，"
                           "但 unless 会排除满足条件的请求",
        "frequency": 0.08
    },
    "missing_has_check": {
        "transform": lambda p: remove_has_check(p),
        "error_description": "访问可选属性前未使用 has 检查，"
                           "可能导致运行时错误",
        "frequency": 0.08
    },
    "in_vs_equals": {
        "transform": lambda p: p.replace(" in ", " == ", 1),
        "error_description": "应使用 in（层级包含）但错误使用了 =="
                           "（严格相等），导致子层级实体无法匹配",
        "frequency": 0.08
    },
    "wildcard_scope_unintended": {
        "transform": lambda p: remove_scope_constraints(p),
        "error_description": "scope 中未限定 principal/action/resource，"
                           "导致策略范围过于宽泛",
        "frequency": 0.08
    },
}

def generate_error_sample(correct_policy: str, correct_description: str):
    """从正确策略生成一条错误 → 修正的训练数据"""
    
    # 随机选择一种错误类型（按频率加权）
    error_type = weighted_random_choice(ERROR_INJECTORS)
    injector = ERROR_INJECTORS[error_type]
    
    # 注入错误
    broken_policy = injector["transform"](correct_policy)
    
    # 构造训练样本
    return {
        "task_type": "error_correction",
        "instruction": f"以下 Cedar 策略存在错误，请找出错误并修正：\n\n"
                      f"{broken_policy}\n\n"
                      f"策略意图：{correct_description}",
        "output": f"**错误分析：**\n"
                 f"{injector['error_description']}\n\n"
                 f"**修正后的策略：**\n"
                 f"{correct_policy}",
        "metadata": {
            "error_type": error_type,
            "source": "synthetic_error_injection"
        }
    }
```

### 4.2 从模型自然错误中收集

在 SFT 训练过程中，定期用 checkpoint 生成策略并收集错误：

```python
def collect_model_errors(model, eval_prompts, cedar_cli):
    """收集模型实际犯的错误，用于后续训练"""
    error_samples = []
    
    for prompt in eval_prompts:
        generated = model.generate(prompt)
        validation = cedar_cli.validate(generated)
        
        if not validation.success:
            # 模型犯了错！这是宝贵的训练数据
            error_samples.append({
                "task_type": "error_correction",
                "instruction": f"以下 Cedar 策略存在错误，请修正：\n\n"
                              f"{generated}\n\n"
                              f"验证器报错：{validation.error_msg}",
                "output": get_corrected_version(prompt),  # 人工或强模型修正
                "metadata": {
                    "source": "model_natural_error",
                    "checkpoint": model.checkpoint_id,
                    "error_msg": validation.error_msg
                }
            })
    
    return error_samples
```

这种"从模型自身错误中学习"的策略特别有效，因为它直接针对模型的薄弱环节。

---

## 五、训练数据最终格式

### 5.1 Chat Template 格式

Qwen 使用 ChatML 格式，所有训练数据应转换为：

```
<|im_start|>system
你是一个 Cedar 策略语言专家。你的任务是根据用户的需求，
生成语法正确、语义准确的 Cedar 策略代码。
<|im_end|>
<|im_start|>user
{instruction}
<|im_end|>
<|im_start|>assistant
{output}
<|im_end|>
```

### 5.2 数据集拆分

```
总数据: ~5000-8000 条
├── Training:  90% (~4500-7200)
├── Validation: 5% (~250-400)
└── Test:       5% (~250-400)

注意：
- Test set 必须只包含 Layer 1 (Ground Truth) 的数据
- Validation set 混合 Layer 1 + Layer 2
- Training set 混合所有三层
- 确保 test set 中没有与 training set 结构重复的样本
```

### 5.3 Task Type 混合比例

```
Training Set 中各类型占比：

Policy Generation (从需求生成策略)     ~35%  ← 核心能力
Error Detection & Correction           ~25%  ← 消除错误的关键
Schema-aware Generation                ~20%  ← 真实场景必需
Policy Explanation (解释策略含义)       ~10%  ← 增强理解深度
Multi-policy Reasoning (多策略分析)     ~10%  ← 高级场景
```

---

## 六、数据质量控制清单

每条数据入库前必须检查：

```
□ Cedar policy 通过 `cedar validate` 语法检查
□ 如有 schema，通过 `cedar validate --schema` 检查
□ 如有 test cases，authorize 结果与 expected 一致
□ instruction 中的自然语言描述准确反映策略意图
□ output 格式规范（缩进、换行一致）
□ 不与已有数据结构指纹重复
□ 策略末尾有分号
□ Entity 引用格式正确（Type::"id"）
□ 标注了 task_type 和 metadata
□ 复杂度标签正确（L1-L4）
```

---
