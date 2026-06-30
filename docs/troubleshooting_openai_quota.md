# OpenAI 429 insufficient_quota 排查

## 现象

运行：

```powershell
python .\backend\app\morning_brief_demo.py
```

出现：

```text
OpenAI API HTTP 429
insufficient_quota
You exceeded your current quota, please check your plan and billing details.
```

## 这说明什么

这说明代码已经成功请求到了 OpenAI。

不是 Python 问题，不是 `.env` 没读到，也不是 API Key 完全无效。

问题是当前 OpenAI 账号、组织或项目没有可用 API 额度。

## 最常见原因

- 账号没有开通 API 付费。
- 没有充值或绑定付款方式。
- 免费额度已经过期或用完。
- 当前项目的 monthly budget 设置太低。
- 当前组织的 usage limit 已达到。
- API Key 属于另一个没有额度的 Project。

## 处理步骤

### 1. 检查 Usage

打开：

```text
https://platform.openai.com/usage
```

看当前项目是否已经有用量、是否达到上限。

### 2. 检查 Billing

打开：

```text
https://platform.openai.com/settings/organization/billing/overview
```

确认是否已经开通 API 账单。

### 3. 检查 Limits

打开：

```text
https://platform.openai.com/settings/organization/limits
```

检查 monthly budget / usage limit 是否过低。

### 4. 确认 API Key 所属 Project

打开：

```text
https://platform.openai.com/api-keys
```

确认你创建 key 的 Project 是有额度的项目。

### 5. 重新运行

修复账单或额度后，回到项目目录：

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py
```

## 现在项目会怎么处理

如果再次遇到 `insufficient_quota`，脚本会提示“OpenAI 已连通，但账号额度/账单暂时不可用”，然后自动回退到模板版早报。

