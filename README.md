## 官方开发文档
----
http://docs.ansible.com/ansible/dev_guide/index.html

> 非常推荐大家看**官方文档**

## 环境
----
本次所用的环境
- ansible `2.3.0.0`
- os `Centos 6.7 X64`
- python `2.6.6`

## 介绍
----
Ansible 开发分为两大模块，一是`modules`，而是`plugins`。

首先，要记住这两部分内容在哪个地方执行？
- `modules` 文件被传送到**远端主机**并执行。
- `plugins` 是在**ansible服务器**上执行的。

再者是执行顺序？
`plugins` 先于 `modules` 执行。

然后大家明确这两部分内容是干啥用的？
- `modules` 是ansible的核心内容，它使playbook变得更加简单明了，一个task就是完成某一项功能。ansible模块是被传送到远程主机上运行的。所以它们可以用远程主机可以执行的任何语言编写modules。
- `plugins` 是在**ansible主机**上执行的，用来辅助modules做一些操作。比如连接远程主机，拷贝文件到远程主机之类的。


## ansible执行ping模块的过程。
----
![ansible运行过程.jpg](https://raw.githubusercontent.com/kuailemy123/Ansible-dev/master/ansible运行过程.jpg)

如果想要源文件，请加入QQ群[425931784](http://shang.qq.com/wpa/qunwpa?idkey=47638ae0b21fc2b1e714939524706b1fc405bc04cbd9426a8bcc9ed3d0c83954)，至群文件下载。


## 使用说明
---

http://www.jianshu.com/p/667dabe96f04