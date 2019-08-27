# TODO

- [ ] add id_key in config.yml
- [ ] add item\["content"\]\[0\]\["value"\]

# 配置

## config.yml

rsshub下面的host意思是用自建的RSSHub替换网上公开的。建议用自建的代替，一来可以加快刷新速度，二来可以减少对方服务器的负载。

## 自建RSSHub

可以根据[官方配置教程](https://docs.rsshub.app/install/)来配置，这里我建议使用以下命令来运行rsshub的docker镜像

```bash
docker run -d --name rsshub_diygod --restart=always -p 1202:1200 \
	-e CACHE_EXPIRE=5 -e CACHE_CONTENT_EXPIRE=60 \
	diygod/rsshub:latest
```
