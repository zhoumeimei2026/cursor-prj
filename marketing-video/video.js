/*
 * 5 秒营销视频 —— 内窥镜主控板 & 影像系统定制开发团队
 * 纯 Canvas 程序化渲染，draw(t) 完全由时间驱动，保证逐帧导出可复现。
 */
(function (global) {
  "use strict";

  const W = 1920;
  const H = 1080;
  const DURATION = 5.0; // 秒

  // ---- 调色板 ----
  const COL = {
    bg0: "#03070f",
    bg1: "#0a1830",
    cyan: "#21e6ff",
    cyanSoft: "#7af2ff",
    blue: "#2f6bff",
    white: "#f2f8ff",
    grayText: "#9fb6d6",
  };

  const FONT = `"Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif`;

  // ---- 缓动函数 ----
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
  const easeInOutCubic = (t) =>
    t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const easeOutBack = (t) => {
    const c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  };
  // 区间映射：把 t 从 [a,b] 归一到 [0,1]
  const seg = (t, a, b) => clamp((t - a) / (b - a));

  // ---- 资源 ----
  const assets = { board: null, imaging: null };
  function loadImage(src) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => resolve(null);
      img.src = src;
    });
  }
  async function preload(base = "assets/") {
    [assets.board, assets.imaging] = await Promise.all([
      loadImage(base + "board.png"),
      loadImage(base + "imaging.png"),
    ]);
  }

  // ---- 确定性的"随机"粒子（避免每帧抖动）----
  const PARTICLES = [];
  (function buildParticles() {
    let s = 1337;
    const rnd = () => {
      s = (s * 1664525 + 1013904223) % 4294967296;
      return s / 4294967296;
    };
    for (let i = 0; i < 90; i++) {
      PARTICLES.push({
        x: rnd() * W,
        y: rnd() * H,
        r: 0.6 + rnd() * 2.2,
        sp: 6 + rnd() * 22,
        ph: rnd() * Math.PI * 2,
        amp: 8 + rnd() * 26,
      });
    }
  })();

  // 绘制图片 cover 填充到指定矩形
  function drawCover(ctx, img, dx, dy, dw, dh, alpha) {
    if (!img) return;
    ctx.save();
    ctx.globalAlpha = alpha;
    const ir = img.width / img.height;
    const r = dw / dh;
    let sw, sh, sx, sy;
    if (ir > r) {
      sh = img.height;
      sw = sh * r;
      sx = (img.width - sw) / 2;
      sy = 0;
    } else {
      sw = img.width;
      sh = sw / r;
      sx = 0;
      sy = (img.height - sh) / 2;
    }
    ctx.beginPath();
    ctx.rect(dx, dy, dw, dh);
    ctx.clip();
    ctx.drawImage(img, sx, sy, sw, sh, dx, dy, dw, dh);
    ctx.restore();
  }

  // 背景：渐变 + 流动网格 + 粒子
  function drawBackground(ctx, t) {
    const g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, COL.bg0);
    g.addColorStop(0.55, COL.bg1);
    g.addColorStop(1, "#04101f");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // 中心辉光
    const rg = ctx.createRadialGradient(W * 0.5, H * 0.42, 60, W * 0.5, H * 0.42, W * 0.7);
    rg.addColorStop(0, "rgba(33,168,255,0.18)");
    rg.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = rg;
    ctx.fillRect(0, 0, W, H);

    // 透视网格
    ctx.save();
    ctx.globalAlpha = 0.16;
    ctx.strokeStyle = COL.cyan;
    ctx.lineWidth = 1;
    const off = (t * 60) % 80;
    for (let y = H * 0.62; y < H + 80; y += 80) {
      ctx.beginPath();
      ctx.moveTo(0, y + off * 0);
      ctx.lineTo(W, y);
      ctx.stroke();
    }
    for (let x = -200 + (off); x < W + 200; x += 80) {
      ctx.beginPath();
      ctx.moveTo(x, H * 0.62);
      ctx.lineTo((x - W / 2) * 2.2 + W / 2, H);
      ctx.stroke();
    }
    ctx.restore();

    // 粒子
    ctx.save();
    for (const p of PARTICLES) {
      const x = (p.x + t * p.sp) % (W + 40) - 20;
      const y = p.y + Math.sin(t * 1.2 + p.ph) * p.amp;
      const tw = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(t * 2 + p.ph));
      ctx.globalAlpha = 0.5 * tw;
      ctx.fillStyle = COL.cyanSoft;
      ctx.beginPath();
      ctx.arc(x, y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  // 发光文字
  function glowText(ctx, text, x, y, size, color, alpha, weight = "700", spacing = 0, glow = 24) {
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.font = `${weight} ${size}px ${FONT}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.shadowColor = color;
    ctx.shadowBlur = glow;
    ctx.fillStyle = color;
    if (spacing === 0) {
      ctx.fillText(text, x, y);
    } else {
      // 手动字间距
      const chars = [...text];
      ctx.font = `${weight} ${size}px ${FONT}`;
      let total = 0;
      const widths = chars.map((c) => {
        const w = ctx.measureText(c).width + spacing;
        total += w;
        return w;
      });
      let cx = x - total / 2;
      ctx.textAlign = "left";
      for (let i = 0; i < chars.length; i++) {
        ctx.fillText(chars[i], cx, y);
        cx += widths[i];
      }
    }
    ctx.restore();
  }

  // 一条带发光端点的装饰线
  function accentLine(ctx, x, y, w, alpha) {
    ctx.save();
    ctx.globalAlpha = alpha;
    const g = ctx.createLinearGradient(x - w / 2, 0, x + w / 2, 0);
    g.addColorStop(0, "rgba(33,230,255,0)");
    g.addColorStop(0.5, COL.cyan);
    g.addColorStop(1, "rgba(33,230,255,0)");
    ctx.strokeStyle = g;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x - w / 2, y);
    ctx.lineTo(x + w / 2, y);
    ctx.stroke();
    ctx.restore();
  }

  // 能力卡片
  function capabilityCard(ctx, cx, cy, appear, title, sub, iconFn) {
    const cw = 430, ch = 300;
    const e = easeOutCubic(appear);
    const y = cy + (1 - e) * 60;
    const a = appear;
    ctx.save();
    ctx.globalAlpha = a;
    // 卡面
    const x0 = cx - cw / 2, y0 = y - ch / 2;
    roundRect(ctx, x0, y0, cw, ch, 22);
    const cardG = ctx.createLinearGradient(x0, y0, x0, y0 + ch);
    cardG.addColorStop(0, "rgba(20,46,84,0.85)");
    cardG.addColorStop(1, "rgba(8,20,40,0.85)");
    ctx.fillStyle = cardG;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(33,230,255,0.55)";
    ctx.stroke();

    // 顶部高光条
    ctx.save();
    ctx.globalAlpha = a;
    accentLine(ctx, cx, y0 + 26, cw - 120, 1);
    ctx.restore();

    // 图标
    ctx.save();
    ctx.translate(cx, y0 + 110);
    ctx.globalAlpha = a;
    iconFn(ctx);
    ctx.restore();

    // 文本
    glowText(ctx, title, cx, y0 + 200, 46, COL.white, a, "800", 2, 10);
    glowText(ctx, sub, cx, y0 + 250, 26, COL.grayText, a, "500", 1, 0);
    ctx.restore();
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // ---- 图标（矢量绘制）----
  function iconBoard(ctx) {
    ctx.save();
    ctx.strokeStyle = COL.cyan;
    ctx.fillStyle = "rgba(33,230,255,0.12)";
    ctx.lineWidth = 4;
    ctx.shadowColor = COL.cyan;
    ctx.shadowBlur = 16;
    roundRect(ctx, -55, -45, 110, 90, 10);
    ctx.fill();
    ctx.stroke();
    // 芯片
    ctx.fillStyle = COL.cyanSoft;
    roundRect(ctx, -22, -18, 44, 36, 6);
    ctx.fill();
    // 引脚
    ctx.lineWidth = 3;
    for (let i = -1; i <= 1; i++) {
      line(ctx, -22, i * 12, -45, i * 12);
      line(ctx, 22, i * 12, 45, i * 12);
    }
    ctx.restore();
  }
  function iconImaging(ctx) {
    ctx.save();
    ctx.strokeStyle = COL.cyan;
    ctx.lineWidth = 4;
    ctx.shadowColor = COL.cyan;
    ctx.shadowBlur = 16;
    // 镜头外环
    circle(ctx, 0, 0, 48, false, true);
    circle(ctx, 0, 0, 30, false, true);
    ctx.fillStyle = "rgba(33,230,255,0.25)";
    circle(ctx, 0, 0, 14, true, false);
    // 高光
    ctx.fillStyle = COL.white;
    circle(ctx, -10, -12, 5, true, false);
    ctx.restore();
  }
  function iconCustom(ctx) {
    ctx.save();
    ctx.strokeStyle = COL.cyan;
    ctx.lineWidth = 4;
    ctx.shadowColor = COL.cyan;
    ctx.shadowBlur = 16;
    // 齿轮
    const teeth = 8, ro = 46, ri = 30;
    ctx.beginPath();
    for (let i = 0; i < teeth; i++) {
      const a0 = (i / teeth) * Math.PI * 2;
      const a1 = ((i + 0.5) / teeth) * Math.PI * 2;
      ctx.lineTo(Math.cos(a0) * ro, Math.sin(a0) * ro);
      ctx.lineTo(Math.cos(a1) * ro, Math.sin(a1) * ro);
      ctx.lineTo(Math.cos(a1) * ri, Math.sin(a1) * ri);
      const a2 = ((i + 1) / teeth) * Math.PI * 2;
      ctx.lineTo(Math.cos(a2) * ri, Math.sin(a2) * ri);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(33,230,255,0.12)";
    ctx.fill();
    ctx.stroke();
    circle(ctx, 0, 0, 14, false, true);
    ctx.restore();
  }
  function line(ctx, x1, y1, x2, y2) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }
  function circle(ctx, x, y, r, fill, stroke) {
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    if (fill) ctx.fill();
    if (stroke) ctx.stroke();
  }

  // 勾选要点
  function tickItem(ctx, x, y, text, appear) {
    const a = easeOutCubic(appear);
    ctx.save();
    ctx.globalAlpha = a;
    const slide = (1 - a) * 30;
    ctx.translate(-slide, 0);
    // 勾
    ctx.strokeStyle = COL.cyan;
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.shadowColor = COL.cyan;
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + 12, y + 12);
    ctx.lineTo(x + 32, y - 16);
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.font = `600 36px ${FONT}`;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillStyle = COL.white;
    ctx.fillText(text, x + 52, y);
    ctx.restore();
  }

  // 渐隐黑场
  function fade(ctx, alpha) {
    if (alpha <= 0) return;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = "#03070f";
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
  }

  // ============ 主绘制 ============
  function draw(ctx, t) {
    t = clamp(t, 0, DURATION);
    ctx.clearRect(0, 0, W, H);
    drawBackground(ctx, t);

    // -------- 场景 1：品牌开场 (0.0 - 1.25) --------
    if (t < 1.35) {
      const a = seg(t, 0.15, 0.75);
      const aOut = 1 - seg(t, 1.05, 1.35);
      const alpha = clamp(a) * clamp(aOut);
      const rise = (1 - easeOutCubic(seg(t, 0.15, 0.85))) * 40;
      glowText(ctx, "ENDOSCOPE  SYSTEMS", W / 2, H / 2 - 150 + rise, 32, COL.cyan, alpha * 0.9, "600", 8, 18);
      accentLine(ctx, W / 2, H / 2 - 100 + rise, 360 * easeOutCubic(seg(t, 0.3, 0.9)), alpha);
      glowText(ctx, "内窥镜主控板 · 影像系统", W / 2, H / 2 + 0 + rise, 96, COL.white, alpha, "900", 4, 28);
      glowText(ctx, "定 制 开 发 团 队", W / 2, H / 2 + 110 + rise, 52, COL.cyanSoft, alpha, "700", 12, 18);
    }

    // -------- 场景 2：核心能力 (1.25 - 2.85) --------
    if (t >= 1.2 && t < 3.0) {
      const local = t - 1.25;
      const headA = clamp(seg(t, 1.3, 1.7)) * (1 - seg(t, 2.7, 3.0));
      glowText(ctx, "我们能为你做什么", W / 2, 180, 60, COL.white, headA, "800", 6, 18);
      accentLine(ctx, W / 2, 235, 300, headA);

      const baseY = H / 2 + 60;
      const c1 = clamp(seg(t, 1.45, 1.85)) * (1 - seg(t, 2.75, 3.0));
      const c2 = clamp(seg(t, 1.6, 2.0)) * (1 - seg(t, 2.75, 3.0));
      const c3 = clamp(seg(t, 1.75, 2.15)) * (1 - seg(t, 2.75, 3.0));
      capabilityCard(ctx, W / 2 - 500, baseY, c1, "主控板设计", "硬件 / FPGA / 固件", iconBoard);
      capabilityCard(ctx, W / 2, baseY, c2, "影像系统", "成像算法 / 图像处理", iconImaging);
      capabilityCard(ctx, W / 2 + 500, baseY, c3, "定制集成", "整机方案 / 国产替代", iconCustom);
    }

    // -------- 场景 3：影像实力展示 (2.85 - 4.15) --------
    if (t >= 2.8 && t < 4.25) {
      const a = clamp(seg(t, 2.9, 3.25)) * (1 - seg(t, 4.0, 4.25));
      // 影像图（左侧大图）
      const panelW = 880, panelH = 620;
      const px = 120, py = H / 2 - panelH / 2;
      const reveal = easeOutCubic(seg(t, 2.9, 3.4));
      ctx.save();
      ctx.globalAlpha = a;
      roundRect(ctx, px, py, panelW, panelH, 20);
      ctx.clip();
      drawCover(ctx, assets.imaging || assets.board, px, py, panelW, panelH, 1);
      // 扫描光带
      const sy = py + reveal * panelH;
      const sg = ctx.createLinearGradient(0, sy - 60, 0, sy + 60);
      sg.addColorStop(0, "rgba(33,230,255,0)");
      sg.addColorStop(0.5, "rgba(33,230,255,0.35)");
      sg.addColorStop(1, "rgba(33,230,255,0)");
      ctx.fillStyle = sg;
      ctx.fillRect(px, sy - 60, panelW, 120);
      ctx.restore();
      ctx.save();
      ctx.globalAlpha = a;
      roundRect(ctx, px, py, panelW, panelH, 20);
      ctx.lineWidth = 2;
      ctx.strokeStyle = "rgba(33,230,255,0.6)";
      ctx.stroke();
      ctx.restore();

      // 右侧要点
      const tx = px + panelW + 110;
      glowText(ctx, "为什么选择我们", tx + 170, py + 70, 54, COL.white, a, "800", 2, 16);
      accentLine(ctx, tx + 170, py + 115, 300, a);
      tickItem(ctx, tx, py + 210, "4K 高清 · 低延迟成像", seg(t, 3.15, 3.5) * a);
      tickItem(ctx, tx, py + 300, "主控板软硬件一体交付", seg(t, 3.3, 3.65) * a);
      tickItem(ctx, tx, py + 390, "成熟算法 · 快速量产落地", seg(t, 3.45, 3.8) * a);
      tickItem(ctx, tx, py + 480, "全程定制 · 国产化方案", seg(t, 3.6, 3.95) * a);
    }

    // -------- 场景 4：行动号召 (4.1 - 5.0) --------
    if (t >= 4.05) {
      const a = clamp(seg(t, 4.2, 4.55));
      const rise = (1 - easeOutBack(clamp(seg(t, 4.2, 4.8)))) * 30;
      glowText(ctx, "从硬件到影像 · 一站式定制交付", W / 2, H / 2 - 70 + rise, 78, COL.white, a, "900", 3, 28);
      accentLine(ctx, W / 2, H / 2 + 10, 520 * easeOutCubic(seg(t, 4.4, 4.9)), a);
      glowText(ctx, "内窥镜主控板 & 影像系统定制开发团队", W / 2, H / 2 + 90, 40, COL.cyanSoft, a, "600", 4, 14);

      // 按钮
      const bw = 420, bh = 96, bx = W / 2 - bw / 2, by = H / 2 + 180;
      const pulse = 0.5 + 0.5 * Math.sin((t - 4.2) * 6);
      ctx.save();
      ctx.globalAlpha = a;
      roundRect(ctx, bx, by, bw, bh, bh / 2);
      const bg = ctx.createLinearGradient(bx, by, bx + bw, by);
      bg.addColorStop(0, COL.blue);
      bg.addColorStop(1, COL.cyan);
      ctx.fillStyle = bg;
      ctx.shadowColor = COL.cyan;
      ctx.shadowBlur = 30 + pulse * 25;
      ctx.fill();
      ctx.restore();
      glowText(ctx, "立即联系我们 ›", W / 2, by + bh / 2, 44, "#04101f", a, "900", 2, 0);
    }

    // 首尾淡入淡出
    fade(ctx, 1 - seg(t, 0.0, 0.25));
    fade(ctx, seg(t, 4.82, 5.0));
  }

  global.MVideo = { W, H, DURATION, draw, preload };
})(typeof window !== "undefined" ? window : globalThis);
