# 松果线上更新工作流

这份文档解决的是：

- 你和我继续对话改代码
- 本地先看网页效果
- GitHub 留存代码版本
- ECS 线上站点同步更新

## 一、推荐工作模式

推荐固定使用这条链路：

```text
Codex 改本地代码 -> 本地浏览器确认 -> git commit -> git push -> ECS git pull -> 重启服务
```

这是当前阶段最稳的方案。

## 二、本地改完怎么看效果

在本地项目目录执行：

```powershell
cd E:\松果\ai-butler
.\scripts\start_dashboard_api.ps1
```

浏览器打开：

```text
http://127.0.0.1:8765/frontend/
```

然后你告诉我：

- 哪个区域要改
- 要改成什么样
- 哪些文案、动作、布局不满意

我直接在本地代码上改。

## 三、确认满意后怎么进 GitHub

本地执行：

```powershell
git add .
git commit -m "Describe the change"
git push
```

## 四、线上 ECS 怎么同步

服务器执行：

```bash
cd /opt/sunguo/ai-butler
git pull
npm install
sudo systemctl restart sunguo-dashboard
```

仓库里也已经帮你准备了脚本：

- [deploy/aliyun/update_sunguo.sh](/E:/松果/ai-butler/deploy/aliyun/update_sunguo.sh)

你以后在服务器上可以直接执行：

```bash
bash /opt/sunguo/ai-butler/deploy/aliyun/update_sunguo.sh
```

## 五、什么情况下要重新装依赖

这些情况需要：

- 改了 `package.json`
- 新增了前端库
- 新增了 Python 依赖

如果只是改 `html/css/js/py` 逻辑，通常不需要重装很多东西，但 `npm install` 保留着最省心。

## 六、什么情况下网页会看不到新效果

优先排查：

1. 浏览器缓存
2. ECS 没有 `git pull`
3. 服务没有重启
4. 改的是本地文件，但线上仓库没有 push
5. 域名解析到的不是这台 ECS

## 七、建议你的实际分工

你负责：

- 说需求
- 看页面效果
- 决定最终样式和方向

我负责：

- 改代码
- 补脚本
- 调结构
- 处理部署链路

这会是我们后续最省力的合作方式。
