# 第 1 周安装与账号准备教程

## 1. 安装 VS Code

1. 打开官网：https://code.visualstudio.com/
2. 点击 Download for Windows。
3. 安装时建议勾选：
   - Add to PATH
   - Register Code as an editor
   - Add "Open with Code" action
4. 安装完成后打开 VS Code。
5. 在 Extensions 中安装：
   - Python
   - Pylance
   - GitLens，可选

验证：

```powershell
code --version
```

## 2. 安装 Python

推荐先安装 Python 3.12 或 3.11，项目第一阶段两者都可以。

1. 打开官网：https://www.python.org/downloads/windows/
2. 下载 Windows installer (64-bit)。
3. 安装第一页一定勾选：
   - Add python.exe to PATH
4. 点击 Install Now。
5. 安装完成后打开 PowerShell。

验证：

```powershell
python --version
pip --version
```

如果 `python --version` 没反应，试：

```powershell
py --version
```

## 3. 安装 Git

1. 打开官网：https://git-scm.com/downloads/win
2. 下载 Git for Windows。
3. 安装选项大部分保持默认。
4. 推荐确认这些选项：
   - Use Git from the command line and also from 3rd-party software
   - Use Visual Studio Code as Git's default editor，如果出现这个选项
   - Checkout Windows-style, commit Unix-style line endings
5. 安装完成后打开 PowerShell。

验证：

```powershell
git --version
```

首次设置姓名和邮箱：

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

## 4. 安装 GitHub Desktop

1. 打开官网：https://desktop.github.com/
2. 下载并安装 GitHub Desktop。
3. 用 GitHub 账号登录。
4. 后续我们会用它把 `E:\松果\ai-butler` 发布到私有 GitHub 仓库。

## 5. 创建 OpenAI API Key

1. 打开：https://platform.openai.com/
2. 登录或注册账号。
3. 进入 API keys 页面：https://platform.openai.com/api-keys
4. 点击 Create new secret key。
5. 名字建议写：`sunguo-dev-local`
6. 创建后立刻复制保存。这个 key 只显示一次。
7. 不要发给任何人，也不要写进 GitHub。

后续我们会把它放到本地 `.env` 文件中：

```text
OPENAI_API_KEY=你的_key
```

注意：

- API 通常需要绑定付款方式或充值额度。
- 可以设置使用限额，避免误调用造成过高费用。
- Key 泄露后应立刻删除并重新创建。

## 6. Outlook / Microsoft Graph 权限准备

松果要读取和写入 Outlook 日历，需要 Microsoft Graph 权限。

第一阶段目标权限：

- `Calendars.ReadWrite`

它允许应用在用户授权后创建、读取、更新和删除用户日历事件。

安全设计：

- 第一次只在测试日历里写入。
- 写入前必须给你展示计划写入的内容。
- 你确认后才执行。
- 删除或修改日历事件也必须确认。

后续步骤：

1. 注册 Microsoft Azure 应用。
2. 配置回调地址。
3. 添加 Microsoft Graph delegated permission：`Calendars.ReadWrite`。
4. 通过 OAuth 登录授权。
5. 代码中读取当天事件。
6. 代码中创建测试日历事件。

## 7. 本周你只需要完成的检查

PowerShell 中能看到这些版本即可：

```powershell
python --version
pip --version
git --version
code --version
```

OpenAI API Key 和 Outlook 授权可以先准备账号，不急着马上接代码。

