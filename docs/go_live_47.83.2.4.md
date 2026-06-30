# 松果上线执行单（当前环境）

当前已知信息：

- 域名：`lemoncypress.com`
- GitHub 仓库：`https://github.com/lemon-cypress/sunguo-ai-butler.git`
- ECS 公网 IP：`47.83.2.4`

## 一、阿里云域名解析现在就这样填

进入：

- 阿里云
- 域名与网站
- 域名列表
- 你的域名 `lemoncypress.com`
- 点击 `解析`

然后新增两条记录：

1. 根域名
- 记录类型：`A`
- 主机记录：`@`
- 解析请求来源：默认
- 记录值：`47.83.2.4`
- TTL：默认

2. www
- 记录类型：`A`
- 主机记录：`www`
- 解析请求来源：默认
- 记录值：`47.83.2.4`
- TTL：默认

如果你更想先把松果放在子域名，也可以新增：

- 记录类型：`A`
- 主机记录：`ai`
- 记录值：`47.83.2.4`

这样访问地址就是：

```text
http://ai.lemoncypress.com
```

## 二、阿里云安全组要放行这些端口

进入：

- 云服务器 ECS
- 实例
- 找到你的实例
- 点实例名
- 安全组
- 配置规则

确认入方向放行：

- `22`
- `80`
- `443`

协议：

- `TCP`

授权对象：

```text
0.0.0.0/0
```

## 三、登录 ECS 后执行什么

先用阿里云控制台里的远程连接，或者你自己的 SSH 工具登录。

登录后依次执行：

```bash
sudo mkdir -p /opt/sunguo
cd /opt/sunguo
```

如果你想一步部署，直接执行仓库里准备好的脚本内容即可。最稳的是先手动执行：

```bash
sudo apt update
sudo apt install -y python3 python3-pip nginx git nodejs npm
cd /opt/sunguo
git clone https://github.com/lemon-cypress/sunguo-ai-butler.git ai-butler
cd /opt/sunguo/ai-butler
npm install
cp .env.example .env
```

然后编辑 `.env`：

```bash
nano .env
```

你至少要改这些：

```text
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的真实key
DEEPSEEK_MODEL=deepseek-v4-flash
DEFAULT_CITY=北京-朝阳
TIMEZONE=Asia/Shanghai
```

如果暂时不想接真实市场和新闻，可以先改成更稳的演示模式：

```text
USE_REAL_MARKETS=false
USE_REAL_NEWS=false
USE_REAL_THEMES=false
USE_REAL_COMPANIES=false
USE_REAL_WEATHER=true
```

## 四、先在服务器本机验证服务

在 ECS 上执行：

```bash
cd /opt/sunguo/ai-butler
python3 backend/app/dashboard_server.py --host 127.0.0.1 --port 8000
```

看到：

```text
Sunguo dashboard: http://127.0.0.1:8000/frontend/
```

说明服务正常。

新开一个终端窗口，再测：

```bash
curl http://127.0.0.1:8000/frontend/
```

如果能返回 HTML，就说明后端跑通了。

## 五、配置开机自启

执行：

```bash
cd /opt/sunguo/ai-butler
sudo cp deploy/aliyun/sunguo-dashboard.service /etc/systemd/system/sunguo-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable sunguo-dashboard
sudo systemctl start sunguo-dashboard
sudo systemctl status sunguo-dashboard --no-pager
```

## 六、配置 Nginx

执行：

```bash
cd /opt/sunguo/ai-butler
sudo cp deploy/aliyun/sunguo.nginx.conf /etc/nginx/sites-available/sunguo
sudo ln -sf /etc/nginx/sites-available/sunguo /etc/nginx/sites-enabled/sunguo
sudo nginx -t
sudo systemctl reload nginx
```

## 七、现在怎么验证公网打开

先验证 IP：

在浏览器打开：

```text
http://47.83.2.4
```

如果能打开，再验证域名：

```text
http://lemoncypress.com
http://www.lemoncypress.com
```

## 八、如果 IP 能打开，但域名打不开

优先检查：

1. 域名解析还没生效
2. A 记录填错了
3. 安全组没放行 80
4. Nginx 没 reload

## 九、如果域名能打开，下一步就做 HTTPS

等 `http://lemoncypress.com` 能正常打开后，我们下一步就做：

- 阿里云免费证书
- Nginx 443 配置
- 自动跳转 HTTPS

## 十、后续你和我继续改网页的方式

以后你本地让我改代码，流程就是：

1. 本地改好并确认效果
2. `git add .`
3. `git commit -m "描述改动"`
4. `git push`
5. 服务器执行：

```bash
cd /opt/sunguo/ai-butler
bash deploy/aliyun/update_sunguo.sh
```

这样线上就会同步看到新网页。
