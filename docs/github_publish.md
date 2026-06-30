# 松果 GitHub 发布指南

这份文档解决两件事：

1. 把 `ai-butler` 项目安全放到 GitHub
2. 给后续“我和你一起改网页，再同步到线上”打基础

## 一、发布前先确认

当前项目里有这些本地敏感内容：

- `.env`
- Microsoft token
- 本地生成的语音音频

这些已经被 `.gitignore` 忽略，不会跟代码一起上传。

## 二、推荐仓库名

推荐仓库名：

```text
sunguo-ai-butler
```

推荐先建成：

```text
Private
```

原因：

- 里面还有你的个人配置和原型逻辑
- 后面公网部署稳定后，再决定要不要公开

## 三、本地初始化 Git

在 PowerShell 里进入项目目录：

```powershell
cd E:\松果\ai-butler
git init
git branch -M main
git add .
git commit -m "Initial Sunguo prototype"
```

如果 Git 提示你没有用户名或邮箱，执行：

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"
```

然后重新执行 `git commit`。

## 四、在 GitHub 上新建仓库

你可以用两种方式：

### 方式 A：GitHub Desktop

1. 打开 `GitHub Desktop`
2. 选择 `Add an Existing Repository from your Hard Drive`
3. 选中：

```text
E:\松果\ai-butler
```

4. 如果提示不是仓库，先执行上面的 `git init`
5. 点击 `Publish repository`
6. 仓库名填：

```text
sunguo-ai-butler
```

7. 勾选：

```text
Keep this code private
```

8. 点击发布

### 方式 B：GitHub 网站

1. 打开 GitHub
2. 点击 `New repository`
3. 名称填：

```text
sunguo-ai-butler
```

4. 选择 `Private`
5. 不要勾选初始化 README、.gitignore、license
6. 创建后，在本地执行：

```powershell
git remote add origin https://github.com/你的用户名/sunguo-ai-butler.git
git push -u origin main
```

## 五、以后你和我怎么协作改网页

推荐用这条工作流：

1. 你在本地运行松果
2. 你告诉我想改什么页面、文案、数字人、交互
3. 我直接改 `E:\松果\ai-butler` 里的代码
4. 你本地刷新网页先看效果
5. 满意后提交到 GitHub
6. 服务器执行更新脚本，同步线上版本

这样你会有三层保险：

- 本地开发版
- GitHub 代码版
- 线上公网版

## 六、哪些文件是以后最常改的

前端页面主要看这里：

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `frontend/avatar3d_scene.js`
- `frontend/reminder_admin.js`
- `frontend/memory_admin.js`

后端接口主要看这里：

- `backend/app/dashboard_server.py`
- `backend/app/morning_brief_demo.py`
- `backend/app/qa_builder.py`

## 七、推荐提交习惯

每做完一个清晰改动就提交一次，例如：

```powershell
git add .
git commit -m "Tune avatar motion controls"
git push
```

提交说明尽量写成“这次改了什么”，不要只写 `update`。

## 八、如果你想让我继续帮你推 GitHub

我已经把本地发布准备工作整理好了。

如果你下一步愿意，我可以继续帮你：

1. 直接初始化本地 Git 仓库
2. 帮你检查第一次提交里会包含哪些文件
3. 再带你把它发布到 GitHub Desktop
