# Skill Center

OpenClaw skill 集合。

## Skills

### video-searcher

影视资源搜索 skill，一句话找到电影/剧集，直接返回可播放链接。

**触发词：** 找片、搜影视、看电影、找剧、免费看

**原理：**
1. TMDB API 搜索影视元数据
2. 获取 IMDB ID
3. 生成 VidSrc 嵌入播放链接
4. 返回可点击链接

**示例：**
```
用户: "找 肖申克的救赎"
返回: https://vidsrc.to/embed/movie/tt0111161
```
