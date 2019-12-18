# RSS Spider

RSS Spider是一个爬虫项目，用于爬取已有的RSS并存放到自己的数据库（而不是爬取网页生成RSS）。

这个项目的特点有：
1. RSS提供的是格式化好的数据，非常容易爬取
2. RSS提供的数据会一直更新，希望把这些数据保存到自己的数据库当中
3. 如果要自己爬取普通网页，则需要针对每个网站的反爬机制设计相应的爬虫；而使用RSS Spider则可以很方便地调用[RSSHub](https://github.com/DIYgod/RSSHub)，可以使用他人写好的js爬虫，减少工作量
4. 设置一个docker容器，可以不间断地爬取数据，更方便管理运行

RSS Spider 项目正在开发中，欢迎各位提供各种各样的建议或者提交issues和pull requests

# 配置

强烈推荐使用docker来运行这个项目。

## config.yml

一个config.yml的样例如下：

```yaml
mongodb:
    link: mongodb://localhost:27017
rsshub:
    host: http://localhost:1200/
rss:
    zhihu_hotlist:
        link: https://rsshub.app/zhihu/hotlist
        key_list:
            - title
            - link
            - published
            - author
            - summary
```

- 第2行中的是mongoDB数据库的地址。如果你使用docker的容器连接，请把localhost替换成mongo容器的名称（例如mongo_rss_spider）
- 第4行中的是RSSHub的地址，记得写明是http还是https，这个地址会自动替换调rss中的`rsshub_host`。如果有自建的RSSHub，请用自建RSSHub的容器IP地址和端口；如果没有用自建的，请改成`https://rsshub.app/`。如果你使用docker的容器连接，请把localhost替换成RSSHub容器的名称（例如rsshub_diygod）
- 第6行中的zhihu_hotlist表示一个子项目的名称，数据库中的rss_spider下的会生成一个collection，名字就叫zhihu_hotlist
- 第7行中的link表示一个子项目的RSS链接地址。
- 第9行到第13行中的键值表示要存放的键值，这个键值应该与RSS源相匹配，title和link是必须要存放的。

目前只支持把数据存放到mongoDB数据库。

## 自建RSSHub（可选）

建议用自建的代替，一来可以加快刷新速度，二来可以减少对RSSHub作者服务器的负载。

可以根据[RSSHub官方配置教程](https://docs.rsshub.app/install/)来配置，这里我建议使用以下命令来运行rsshub的docker镜像，调低缓存时间，以免错过一些更新比较快的榜单。

```bash
docker run -d --name rsshub_diygod --restart=always -p 1200:1200 \
	-e CACHE_EXPIRE=5 -e CACHE_CONTENT_EXPIRE=60 \
	diygod/rsshub:latest
```

## 在docker中运行mongoDB（可选）

```bash
docker run -d -p 27017:27017 --name mongo_rss_spider --restart=always \
	-v mongo_rss_spider_data_configdb:/data/configdb \
	-v mongo_rss_spider_data_db:/data/db \
	-v d:/docker_mount/mongo_rss_spider_backup:/mongo_backup \
	mongo
```



# 致谢

特别感谢[DIYgod](https://github.com/DIYgod)写的[RSSHub](https://github.com/DIYgod/RSSHub)项目