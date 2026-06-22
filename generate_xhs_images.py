#!/usr/bin/env python3
"""生成 FileBrain 小红书适配信息图（竖版 3:4，手机阅读优化）"""

import asyncio
from playwright.async_api import async_playwright

# ── 样式定义 ──

BASE_STYLE = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    width: 1080px; font-family: "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
    background: #f5f2ed; padding: 0; color: #2c2c2c;
}
.container { width: 100%; padding: 48px 44px; }
"""

COVER_STYLE = BASE_STYLE + """
.bg {
    background: linear-gradient(160deg, #f5f2ed 0%, #e8d5c0 100%);
    min-height: 1440px; display: flex; flex-direction: column;
    justify-content: center; align-items: center; text-align: center;
    padding: 48px 44px;
}
.emoji-big { font-size: 80px; margin-bottom: 12px; }
.title-main { font-size: 52px; font-weight: 800; color: #2c2c2c; letter-spacing: 2px; margin-bottom: 8px; }
.title-sub { font-size: 28px; color: #c97a3a; font-weight: 600; margin-bottom: 32px; }
.tag-row { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 40px; }
.tag {
    background: #fff; padding: 8px 20px; border-radius: 20px;
    font-size: 20px; color: #666; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.feature-list { text-align: left; background: #fff; border-radius: 16px; padding: 28px 32px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06); width: 100%; max-width: 900px; }
.feature-item { display: flex; align-items: center; gap: 12px; padding: 10px 0;
    border-bottom: 1px solid #f0ede8; font-size: 22px; color: #333; }
.feature-item:last-child { border-bottom: none; }
.feature-icon { font-size: 30px; }
.privacy-badge {
    background: #5a8f5a; color: #fff; padding: 14px 28px; border-radius: 12px;
    font-size: 22px; font-weight: bold; display: inline-block; margin-top: 28px;
}
.footer {
    text-align: center; margin-top: 36px; padding-top: 20px;
    border-top: 1px solid #d4cfc8; color: #aaa; font-size: 18px; width: 100%;
}
"""

CARD_STYLE = BASE_STYLE + """
.bg {
    background: #f5f2ed; min-height: 1440px; padding: 48px 44px;
}
.section-title {
    font-size: 36px; font-weight: 700; color: #2c2c2c;
    text-align: center; margin-bottom: 28px;
}
.section-title span { color: #c97a3a; }
.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.card {
    background: #fff; border-radius: 14px; padding: 22px 18px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    display: flex; align-items: flex-start; gap: 14px;
}
.card-icon { font-size: 34px; flex-shrink: 0; }
.card-text h3 { font-size: 20px; font-weight: 600; color: #c97a3a; margin-bottom: 4px; }
.card-text p { font-size: 16px; color: #666; line-height: 1.4; }

.scenario-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.scenario-card {
    background: #fff; border-radius: 12px; padding: 18px; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.scenario-icon { font-size: 32px; margin-bottom: 4px; }
.scenario-title { font-size: 17px; font-weight: 600; color: #333; margin-bottom: 4px; }
.scenario-desc { font-size: 14px; color: #888; }

.highlight-box {
    background: #e8f5e8; border: 2px solid #5a8f5a; border-radius: 14px;
    padding: 20px; text-align: center; margin-bottom: 24px;
}
.highlight-box h2 { font-size: 26px; color: #5a8f5a; margin-bottom: 6px; }
.highlight-box p { font-size: 17px; color: #555; }
"""

COMPARE_STYLE = BASE_STYLE + """
.bg {
    background: #f5f2ed; min-height: 1440px; padding: 48px 44px;
    display: flex; flex-direction: column; justify-content: center;
}
.title-big { font-size: 40px; font-weight: 700; text-align: center; color: #2c2c2c; margin-bottom: 32px; }
.title-big span { color: #c97a3a; }

.compare-card {
    background: #fff; border-radius: 16px; padding: 28px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 20px;
}
.compare-label { font-size: 16px; color: #888; margin-bottom: 8px; }
.compare-file {
    font-family: "Menlo", monospace; font-size: 24px; padding: 14px 18px;
    border-radius: 10px; word-break: break-all;
}
.before { background: #fef0ef; color: #b85450; }
.after { background: #e8f5e8; color: #5a8f5a; }
.arrow-big { text-align: center; font-size: 40px; color: #c97a3a; margin: 8px 0; }

.source-list { margin-top: 24px; }
.source-item {
    display: flex; align-items: center; gap: 12px; padding: 10px 0;
    border-bottom: 1px solid #f0ede8; font-size: 20px;
}
.source-item:last-child { border-bottom: none; }
.source-icon { font-size: 26px; }
.source-text { color: #333; }
"""


async def render_html(html: str, output_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1440},
            device_scale_factor=2
        )
        await page.set_content(html, wait_until="networkidle")
        # 精确裁剪 3:4 比例 (1080×1440)
        await page.screenshot(
            path=output_path,
            clip={"x": 0, "y": 0, "width": 1080, "height": 1440}
        )
        await browser.close()
    print(f"✅ {output_path}")


def make_cover():
    """小红书封面图 —— 吸引点击"""
    features = "🏷️ 智能重命名  📄 PDF/Word/Excel  🖼️ 图片OCR  🔎 全文检索  📤 发送留痕".split("  ")
    feature_items = "\n".join(
        f'<div class="feature-item"><span class="feature-icon">{f.split()[0]}</span><span>{f.split(maxsplit=1)[1]}</span></div>'
        for f in features
    )

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{COVER_STYLE}</style></head><body>
<div class="bg">
    <div class="emoji-big">🧠</div>
    <div class="title-main">FileBrain</div>
    <div class="title-sub">文件大脑 · 桌面智能整理工具</div>

    <div class="tag-row">
        <div class="tag">#效率工具</div>
        <div class="tag">#办公必备</div>
        <div class="tag">#免费开源</div>
        <div class="tag">#本地运行</div>
    </div>

    <div class="feature-list">
        {feature_items}
    </div>

    <div class="privacy-badge">🔒 纯本地 · 不过云 · 数据不上传</div>

    <div class="footer">📥 GitHub 搜索「FileBrain」免费下载</div>
</div></body></html>"""


def make_features_card():
    """功能展示卡 —— 8 大功能 + 4 大场景 + 不过云强调"""
    features_cards = [
        ("👀", "自动扫描", "监控文件夹，新文件自动处理"),
        ("🏷️", "智能命名", "内容摘要_日期_作者_版本号"),
        ("📄", "PDF 识别", "文字PDF + 扫描件OCR"),
        ("📝", "Word/Excel", "读取文档标题和内容"),
        ("🖼️", "图片 OCR", "识别图片中的文字信息"),
        ("🔎", "全文检索", "搜索关键词定位文件"),
        ("📤", "发送留痕", "记录文件分享给谁"),
        ("📌", "版本管理", "按修改时间标v1.0/v1.1"),
    ]

    grid = ""
    for icon, title, desc in features_cards:
        grid += f"""
        <div class="card">
            <div class="card-icon">{icon}</div>
            <div class="card-text"><h3>{title}</h3><p>{desc}</p></div>
        </div>"""

    scenarios = [
        ("🏛️", "政务软件", "浙里办·粤省事\n随申办·北京通等"),
        ("💬", "办公通讯", "钉钉·企业微信\n飞书·WeChat"),
        ("💼", "办公文档", "合同·方案·报告\n按内容版本归档"),
        ("🏠", "个人资料", "论文·扫描件·证件\nOCR识别+检索"),
    ]
    scenario_grid = ""
    for icon, title, desc in scenarios:
        scenario_grid += f"""
        <div class="scenario-card">
            <div class="scenario-icon">{icon}</div>
            <div class="scenario-title">{title}</div>
            <div class="scenario-desc">{desc.replace(chr(10), '<br>')}</div>
        </div>"""

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{CARD_STYLE}</style></head><body>
<div class="bg">
    <div class="section-title">🧠 FileBrain · <span>核心功能</span></div>

    <div class="highlight-box">
        <h2>🔒 纯本地 · 不过云</h2>
        <p>所有文件在本地处理，数据不上传任何云端服务器<br>政务文件、商业合同、个人隐私全部留在你磁盘里</p>
    </div>

    <div class="card-grid">{grid}</div>

    <div class="section-title" style="font-size:28px;margin-top:8px;">💡 <span>适用场景</span></div>
    <div class="scenario-row">{scenario_grid}</div>

    <div class="footer">github.com/mmm1111lhc/FileBrain</div>
</div></body></html>"""


def make_compare_card():
    """效果对比图 —— 重命名前后对比 + 来源说明"""
    sources = [
        ("🏛️", "全国政务App：浙里办、粤省事、随申办、北京通、鄂汇办……"),
        ("💬", "办公通讯：钉钉文件、企业微信文档、飞书、WeChat"),
        ("📥", "任何地方下载的 PDF / Word / Excel / 图片"),
    ]
    source_items = "\n".join(
        f'<div class="source-item"><div class="source-icon">{i}</div><div class="source-text">{t}</div></div>'
        for i, t in sources
    )

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{COMPARE_STYLE}</style></head><body>
<div class="bg">
    <div class="title-big">📄 重命名前后 <span>效果对比</span></div>

    <div class="compare-card">
        <div class="compare-label">⬅ 重命名前（乱码/无意义）</div>
        <div class="compare-file before">
            📄 20260622_142537_审批回执.pdf<br>
            📄 钉钉文件_20260621_0897234.docx<br>
            📄 扫描件_20260620_001.pdf
        </div>
    </div>

    <div class="arrow-big">⬇</div>

    <div class="compare-card">
        <div class="compare-label">➡ 重命名后（自动识别内容）</div>
        <div class="compare-file after">
            📄 建设工程规划许可证_20260622_张三_v1.0.pdf<br>
            📄 项目方案评审意见_20260621_李四_v1.0.docx<br>
            📄 身份证复印件_20260620_王五_v1.0.pdf
        </div>
        <div style="margin-top:8px;font-size:16px;color:#888;text-align:center;">
            格式：内容摘要_日期_作者_版本号
        </div>
    </div>

    <div class="highlight-box" style="margin-top:28px;">
        <h2>🔒 纯本地处理 · 数据不过云</h2>
        <p>安全放心，文件始终留在你的电脑磁盘里</p>
    </div>

    <div class="source-list" style="margin-top:20px;">
        <div style="font-size:18px;font-weight:600;color:#2c2c2c;margin-bottom:8px;">📥 支持来源</div>
        {source_items}
    </div>

    <div class="footer">🧠 FileBrain · 文件大脑 — github.com/mmm1111lhc/FileBrain</div>
</div></body></html>"""


async def main():
    import os
    out = os.path.expanduser("~/FileBrain/images")
    os.makedirs(out, exist_ok=True)

    fns = [
        (make_cover(), "xhs_封面.png"),
        (make_features_card(), "xhs_功能展示.png"),
        (make_compare_card(), "xhs_效果对比.png"),
    ]
    for html, fn in fns:
        await render_html(html, os.path.join(out, fn))

    print(f"\n🎉 3 张小红书适配图已生成到 {out}/")
    print("尺寸：1080×1440 竖版 · 适合小红书笔记配图")


if __name__ == "__main__":
    asyncio.run(main())
