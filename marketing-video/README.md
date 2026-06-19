# 内窥镜主控板 & 影像系统定制开发团队 · 5 秒营销视频

一个完全用代码生成的 **5 秒 / 1080p / 30fps** 营销宣传片。画面由 Canvas 程序化绘制，
逐帧由系统 Chrome 截取，再用 ffmpeg 合成 MP4，结果可复现、可随时改文案重渲染。

## 成片

- 视频：`dist/endoscope-marketing.mp4`（H.264，1920×1080，30fps，5.0s）
- 封面：`dist/poster.png`

## 分镜（5 秒）

| 时间 | 场景 | 内容 |
| ---- | ---- | ---- |
| 0.0–1.3s | 品牌开场 | 「内窥镜主控板 · 影像系统」「定制开发团队」 |
| 1.3–3.0s | 核心能力 | 主控板设计 / 影像系统 / 定制集成 三张能力卡 |
| 2.8–4.2s | 实力展示 | 影像系统实景 + 4 条卖点（4K 高清、软硬一体、快速量产、国产化） |
| 4.1–5.0s | 行动号召 | 「从硬件到影像 · 一站式定制交付」+ 立即联系按钮 |

## 本地预览

```bash
npm install
npm run preview     # 打开 http://localhost:8080 实时循环预览
```

## 导出视频

```bash
npm install
npm run render        # 输出 dist/endoscope-marketing.mp4（30fps）
npm run render:hq     # 60fps 更顺滑版本
```

依赖：系统已安装 `google-chrome`（或 chromium）与 `ffmpeg`；中文需 `fonts-noto-cjk`。
可用环境变量 `CHROME_PATH` 指定浏览器路径。

## 改文案 / 配色

所有文字、分镜时间、配色都集中在 `video.js`：

- `COL`：主题色板
- `draw(ctx, t)`：按时间 `t`（秒）驱动的各场景文案与动画

修改后重新 `npm run render` 即可。替换 `assets/board.png`、`assets/imaging.png`
可更换实拍素材。
