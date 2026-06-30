# 松果阿里云上线指南

这套项目当前不是纯静态站，而是一个带后端接口的网页应用。

原因：

- 网页里有 `/api/ask`
- 有提醒读写接口
- 有记忆管理接口
- 有动作参数保存接口

所以最稳的上线方式是：

1. 买一台阿里云 ECS 云服务器
2. 把 `ai-butler` 项目上传到服务器
3. 在服务器上运行 `dashboard_server.py`
4. 用 Nginx 反向代理
5. 在阿里云域名控制台把域名解析到 ECS 公网 IP
6. 最后申请 HTTPS 证书

## 一、推荐部署方式

推荐你走 `ECS + 域名解析 + Nginx`。

不推荐这一步直接用 OSS 静态网站托管，因为松果当前有后端接口，单独上传 `frontend` 不够。

## 二、你现在需要准备什么

- 一个阿里云 ECS 实例
- 一个公网 IP
- 域名 `lemoncypress.com`
- 能登录 ECS 的账号

如果 ECS 放在中国大陆节点，通常还需要先做备案。

备案官方入口：

- MIIT 备案系统：[https://beian.miit.gov.cn/](https://beian.miit.gov.cn/)

如果你暂时不想备案，最简单的办法是先把 ECS 放在中国香港或海外地域，先跑通公网访问。

## 三、服务器推荐

松果当前是原型阶段，推荐最低配置：

- `2 vCPU`
- `2 GB` 内存
- `40 GB` 系统盘
- `Ubuntu 22.04`

## 四、把项目放到服务器

建议服务器目录：

```bash
/opt/sunguo/ai-butler
```

如果你已经把项目放到 GitHub，可以在服务器上执行：

```bash
sudo mkdir -p /opt/sunguo
cd /opt/sunguo
git clone <你的仓库地址> ai-butler
cd /opt/sunguo/ai-butler
```

如果还没放 GitHub，也可以先用压缩包上传整个 `ai-butler` 目录。

## 五、安装运行环境

在 Ubuntu 上执行：

```bash
sudo apt update
sudo apt install -y python3 python3-pip nginx git
cd /opt/sunguo/ai-butler
npm install
```

如果服务器没有 `npm`，再补：

```bash
sudo apt install -y nodejs npm
```

说明：

- Python 负责后端服务
- `npm install` 用来安装 `three` 和 `@pixiv/three-vrm`
- 当前项目的大多数 Python 模块是标准库，原型版不强依赖额外后端包

如果你后面希望服务器也生成更自然语音，可以额外安装：

```bash
python3 -m pip install edge-tts
```

## 六、启动松果服务

先手动测试：

```bash
cd /opt/sunguo/ai-butler
python3 backend/app/dashboard_server.py --host 127.0.0.1 --port 8000
```

如果返回类似：

```text
Sunguo dashboard: http://127.0.0.1:8000/frontend/
```

说明后端已启动。

此时你可以在服务器上测试：

```bash
curl http://127.0.0.1:8000/frontend/
```

## 七、配置 systemd 开机自启

把仓库里的模板文件复制到系统目录：

```bash
sudo cp /opt/sunguo/ai-butler/deploy/aliyun/sunguo-dashboard.service /etc/systemd/system/sunguo-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable sunguo-dashboard
sudo systemctl start sunguo-dashboard
sudo systemctl status sunguo-dashboard
```

如果你的项目目录不是 `/opt/sunguo/ai-butler`，记得先改模板里的路径：

- [deploy/aliyun/sunguo-dashboard.service](/E:/松果/ai-butler/deploy/aliyun/sunguo-dashboard.service)

## 八、配置 Nginx

把模板复制到 Nginx：

```bash
sudo cp /opt/sunguo/ai-butler/deploy/aliyun/sunguo.nginx.conf /etc/nginx/sites-available/sunguo
sudo ln -s /etc/nginx/sites-available/sunguo /etc/nginx/sites-enabled/sunguo
sudo nginx -t
sudo systemctl reload nginx
```

如果你不是 `sites-available` 结构，也可以直接复制到：

```bash
/etc/nginx/conf.d/sunguo.conf
```

模板文件在这里：

- [deploy/aliyun/sunguo.nginx.conf](/E:/松果/ai-butler/deploy/aliyun/sunguo.nginx.conf)

如果你的域名不是 `lemoncypress.com` 或还要加子域名，要改 `server_name`。

## 九、阿里云域名解析怎么配

你截图里已经在阿里云域名列表页了，下一步是进入解析设置。

对 `lemoncypress.com` 建议先加两条记录：

1. 根域访问
   `记录类型`: `A`
   `主机记录`: `@`
   `记录值`: `你的 ECS 公网 IP`

2. `www` 访问
   `记录类型`: `A`
   `主机记录`: `www`
   `记录值`: `你的 ECS 公网 IP`

生效后：

- `lemoncypress.com` 会打开松果
- `www.lemoncypress.com` 也会打开松果

如果你只想把松果放在子域名上，更推荐这样配：

1. `记录类型`: `A`
   `主机记录`: `ai`
   `记录值`: `你的 ECS 公网 IP`

这样访问地址会变成：

```text
https://ai.lemoncypress.com
```

我个人更推荐你先用子域名上线松果，主站以后可以留给品牌官网。

## 十、放行安全组端口

在阿里云 ECS 控制台里，确认安全组已放行：

- `80`
- `443`
- `22`

如果没放行，域名解析正确也打不开。

## 十一、配置 HTTPS

公网可访问后，再给域名上证书。

常见做法：

1. 阿里云证书服务申请免费证书
2. 或使用 `certbot` 给 Nginx 自动签发

如果你先只想验证是否能打开，可以先跑 `HTTP`，确认没问题后再补 `HTTPS`。

## 十二、最小上线检查清单

按顺序检查：

1. ECS 公网 IP 能访问
2. `python3 backend/app/dashboard_server.py --host 127.0.0.1 --port 8000` 能运行
3. `curl http://127.0.0.1:8000/frontend/` 有内容
4. Nginx `proxy_pass` 指向 `127.0.0.1:8000`
5. 域名 A 记录指向 ECS 公网 IP
6. 安全组放行 80/443
7. 域名可通过公网打开

## 十三、这次最适合你的落地路径

如果你想最快把松果放上公网，建议直接这样做：

1. 阿里云买一台香港或海外 ECS
2. 把 `ai-butler` 上传上去
3. 用这份文档部署
4. 域名先解析到 `ai.lemoncypress.com`
5. 跑通后再决定是否做大陆备案和正式主域名切换

## 十四、我已经帮你准备好的文件

- [deploy/aliyun/sunguo.nginx.conf](/E:/松果/ai-butler/deploy/aliyun/sunguo.nginx.conf)
- [deploy/aliyun/sunguo-dashboard.service](/E:/松果/ai-butler/deploy/aliyun/sunguo-dashboard.service)
- [docs/aliyun_ecs_domain_deploy.md](/E:/松果/ai-butler/docs/aliyun_ecs_domain_deploy.md)

下一步最适合继续做的是：

- 我帮你把这套项目整理成一个“可上传服务器的发布包”
- 或者你把 ECS 公网 IP 发我，我直接告诉你阿里云域名解析页每一项该填什么
