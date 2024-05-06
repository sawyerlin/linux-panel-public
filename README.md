<p align="center">
  <h3 align="center">linux-panel</h3>
  <p align="center">一款简单Linux面板服务</p>
  <p align="center">强烈推荐系统:debian</p>
</p>

### 简介

* SSH终端工具
* 面板收藏功能
* 网站子目录绑定
* 网站备份功能
* 插件方式管理

基本上可以使用,后续会继续优化!欢迎提供意见！

- [兼容性测试报告](/compatibility.md)
- [常用命令说明](/cmd.md) [ mw default ]

### 主要插件介绍

* OpenResty - 轻量级，占有内存少，并发能力强。
* PHP[53-83] - PHP是世界上最好的编程语言。
* MySQL - 一种关系数据库管理系统。
* MariaDB - 是MySQL的一个重要分支。
* MySQL[APT/YUM] - 一种关系数据库管理系统。
* MongoDB - 一种非关系NOSQL数据库管理系统。
* phpMyAdmin - 著名Web端MySQL管理工具。
* Memcached - 一个高性能的分布式内存对象缓存系统。
* Redis - 一个高性能的KV数据库。
* PureFtpd - 一款专注于程序健壮和软件安全的免费FTP服务器软件。
* Gogs - 一款极易搭建的自助Git服务。
* Rsyncd - 通用同步服务。


### 插件开发相关

```
插件文档还不完善，如果有不明白的地方提Issue! 我会尽力完善。
如果你自己写了插件，想分享出来，也可以提Issue。
```

- 简单例子 - https://github.com/mw-plugin/simple-plugin 
- 插件地址 - https://github.com/mw-plugin
- 开发文档 - https://github.com/midoks/mdserver-web/wiki/插件开发

## 其他插件

- OP鉴权 - https://github.com/mw-plugin/op_auth


# Note

```
phpMyAdmin[4.4.15]支持MySQL[5.5-5.7]
phpMyAdmin[5.2.0]支持MySQL[8.0]

PHP[53-72]支持phpMyAdmin[4.4.15]
PHP[72-83]支持phpMyAdmin[5.2.0]
```

### 版本更新 0.16.3

* 面板配置-可以配置时区。
* PHP(GD)扩展安装优化。
* PHP界面功能调整。
* PHP-FPM设置多个应用池(提高高并发稳定性)。
* MySQL(apt/yum)调整优化。
* 网站类型优化。
* 增加数据管理插件。

### 安装

- 安装

```
curl --insecure -fsSL https://raw.githubusercontent.com/sawyerlin/linux-panel/master/scripts/install_new.sh | bash
```
### China

```
curl --insecure -fsSL https://ceshi.tingwen777.com/ceshi_proxy/raw.githubusercontent.com/sawyerlin/linux-panel/master/scripts/install_new.sh | bash
```

- 更新

```
curl --insecure -fsSL https://raw.githubusercontent.com/sawyerlin/linux-panel/master/scripts/update_new.sh | bash
```

### China

```
curl --insecure -fsSL https://ceshi.tingwen777.com/ceshi_proxy/raw.githubusercontent.com/sawyerlin/linux-panel/master/scripts/update_new.sh | bash
```

- 卸载 (TODO: update)

```
wget --no-check-certificate -O uninstall.sh https://cdn.jsdelivr.net/gh/sawyerlin/linux-panel@master/scripts/uninstall.sh && bash uninstall.sh
```

### 授权许可

本项目采用 Apache 开源授权许可证，完整的授权说明已放置在 [LICENSE](https://github.com/midoks/mdserver-web/blob/master/LICENSE) 文件中。

