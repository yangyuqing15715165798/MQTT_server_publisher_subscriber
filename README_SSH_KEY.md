# GitHub SSH Key 配置详细教程（适合初学者，Windows版）

本教程适用于在 Windows 系统下，将本地 Git 仓库通过 SSH 方式推送到 GitHub，适合没有配置过 SSH key 的初学者。

---

## 1. 检查是否已有 SSH key

打开 **Git Bash** 或 **PowerShell**，输入：

```bash
ls ~/.ssh
```

如果看到有 `id_rsa` 和 `id_rsa.pub`（或 `id_ed25519` 和 `id_ed25519.pub`）文件，说明你已经有 SSH key，可以跳到第3步。

---

## 2. 生成新的 SSH key

在 **Git Bash** 或 **PowerShell** 中输入：

```bash
ssh-keygen -t ed25519 -C "你的邮箱@example.com"
```

- 如果你的 Git 版本较老不支持 `ed25519`，可以用 `-t rsa`。
- 按提示一路回车即可（不需要设置密码也可以）。

生成后会在 `C:\Users\你的用户名\.ssh\` 目录下生成 `id_ed25519` 和 `id_ed25519.pub` 两个文件。

---

## 3. 添加 SSH key 到 GitHub

1. 用记事本打开 `C:\Users\你的用户名\.ssh\id_ed25519.pub`（或 `id_rsa.pub`），复制里面的全部内容。
2. 登录你的 GitHub 账号，进入 [SSH Keys管理页面](https://github.com/settings/keys)。
3. 点击 **New SSH key** 或 **Add SSH key**。
4. Title 随便填，Key 内容粘贴刚才复制的内容，点击 **Add SSH key**。

---

## 4. 修改 Git 远程地址为 SSH

在你的项目目录下，执行：

```bash
git remote set-url origin git@github.com:你的用户名/你的仓库名.git
```

例如：
```bash
git remote set-url origin git@github.com:yangyuqing15715165798/MQTT_server_publisher_subscriber.git
```

用下面命令确认：

```bash
git remote -v
```

显示类似如下内容即为成功：
```
origin  git@github.com:yangyuqing15715165798/MQTT_server_publisher_subscriber.git (fetch)
origin  git@github.com:yangyuqing15715165798/MQTT_server_publisher_subscriber.git (push)
```

---

## 5. 测试 SSH 连接

执行：

```bash
ssh -T git@github.com
```

第一次会提示"Are you sure you want to continue connecting (yes/no/[fingerprint])?"，输入 `yes` 回车。

如果看到：
```
Hi 你的用户名! You've successfully authenticated, but GitHub does not provide shell access.
```
说明配置成功。

---

## 6. 推送代码

现在可以正常推送了：

```bash
git push origin main
```

---

## 常见问题

- 如果推送时还是报错，重启一下 Git Bash 或电脑再试。
- 如果提示权限问题，检查 SSH key 是否添加到 GitHub，且是当前用户的 key。
- 如果你有多个 GitHub 账号，建议为不同账号生成不同的 key，并配置 `~/.ssh/config` 文件。

---

如有任何一步遇到问题，把报错信息发给开发同伴或AI助手寻求帮助！ 