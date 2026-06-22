#!/usr/bin/env python3
"""生成 FileBrain 功能展示信息图"""

import asyncio
from playwright.async_api import async_playwright

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    width: 1080px; font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f5f2ed; padding: 40px; color: #2c2c2c;
}}
.container {{ max-width: 1000px; margin: 0 auto; }}
h1 {{
    text-align: center; font-size: 32px; color: #c97a3a;
    margin-bottom: 8px; letter-spacing: 2px;
}}
.subtitle {{
    text-align: center; font-size: 16px; color: #888;
    margin-bottom: 30px; border-bottom: 2px solid #e8d5c0;
    padding-bottom: 16px;
}}
{content}
.footer {{
    text-align: center; margin-top: 30px; padding-top: 16px;
    border-top: 1px solid #d4cfc8;
    color: #aaa; font-size: 12px;
}}
</style>
</head>
<body>
<div class="container">
<h1>{title}</h1>
<div class="subtitle">{subtitle}</div>
{content}
<div class="footer">FileBrain · 文件大脑  —  github.com/mmm1111lhc/FileBrain</div>
</div>
</body>
</html>"""


STEP_CARD = """
<div class="step-card">
    <div class="step-num">{num}</div>
    <div class="step-icon">{icon}</div>
    <div class="step-title">{step_title}</div>
    <div class="step-desc">{step_desc}</div>
</div>
"""


BOX_STYLE = """
<style>
.steps-row {{
    display: flex; gap: 16px; justify-content: space-between;
    margin-bottom: 20px;
}}
.step-card {{
    flex: 1; background: #fff; border-radius: 12px;
    padding: 20px 16px; text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    position: relative;
}}
.step-num {{
    position: absolute; top: -8px; left: -8px;
    width: 28px; height: 28px; border-radius: 50%;
    background: #c97a3a; color: #fff;
    font-size: 14px; font-weight: bold;
    display: flex; align-items: center; justify-content: center;
}}
.step-icon {{ font-size: 36px; margin-bottom: 8px; }}
.step-title {{ font-size: 16px; font-weight: bold; margin-bottom: 6px; }}
.step-desc {{ font-size: 13px; color: #666; line-height: 1.5; }}

.arrow-row {{
    display: flex; align-items: center; justify-content: center;
    gap: 8px; margin: 6px 0;
}}
.arrow {{ font-size: 28px; color: #c97a3a; }}

.feature-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
    margin-bottom: 20px;
}}
.feature-card {{
    background: #fff; border-radius: 10px; padding: 16px;
    display: flex; align-items: flex-start; gap: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
.feature-icon {{ font-size: 28px; flex-shrink: 0; }}
.feature-text h3 {{ font-size: 15px; margin-bottom: 4px; color: #c97a3a; }}
.feature-text p {{ font-size: 13px; color: #666; }}

.naming-demo {{
    background: #fff; border-radius: 10px; padding: 20px;
    margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
.naming-row {{
    display: flex; align-items: center; gap: 16px;
    padding: 8px 0; border-bottom: 1px dashed #eee;
}}
.naming-row:last-child {{ border-bottom: none; }}
.naming-label {{ font-size: 13px; color: #888; width: 60px; flex-shrink: 0; }}
.naming-file {{
    font-family: "Menlo", monospace; font-size: 14px;
    background: #f8f6f2; padding: 6px 12px; border-radius: 6px;
    flex: 1;
}}
.naming-before {{ color: #b85450; }}
.naming-after {{ color: #5a8f5a; }}
.naming-arrow {{ color: #c97a3a; font-size: 20px; }}

.github-step {{
    background: #fff; border-radius: 12px; padding: 20px;
    margin-bottom: 12px; display: flex; align-items: flex-start;
    gap: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
.gs-num {{
    width: 32px; height: 32px; border-radius: 50%;
    background: #c97a3a; color: #fff;
    font-size: 16px; font-weight: bold;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}}
.github-step h3 {{ font-size: 16px; margin-bottom: 4px; }}
.github-step p {{ font-size: 13px; color: #666; }}
.code {{
    font-family: "Menlo", monospace; background: #f0ede8;
    padding: 2px 6px; border-radius: 4px; font-size: 12px;
}}
</style>
"""


def make_workflow_image():
    """FileBrain 工作流程图"""
    steps = [
        ("📁", "文件出现/修改", "监控目录中有文件新增或被编辑"),
        ("🔍", "识别文件类型", "PDF / Word / Excel / 图片"),
        ("📖", "提取内容", "文字提取 + 扫描件 OCR 识别"),
        ("🏷️", "智能命名", "内容摘要_日期_作者_版本号"),
        ("📌", "存入索引", "全文检索索引，随时搜索"),
    ]

    step_html = '<div class="steps-row">'
    for i, (icon, title, desc) in enumerate(steps, 1):
        step_html += STEP_CARD.format(
            num=i, icon=icon, step_title=title, step_desc=desc
        )
    step_html += "</div>"

    # 箭头连接
    arrows = '<div class="arrow-row">' + "".join(
        ['<span class="arrow">➜</span>' for _ in range(len(steps)-1)]
    ) + "</div>"

    naming_demo = """
    <div class="naming-demo">
        <h3 style="margin-bottom:12px;color:#c97a3a;">📄 文件重命名效果</h3>
        <div class="naming-row">
            <span class="naming-label">重命名前</span>
            <span class="naming-file naming-before">审批回执_20260622_1425.pdf</span>
            <span class="naming-arrow">→</span>
        </div>
        <div class="naming-row">
            <span class="naming-label">重命名后</span>
            <span class="naming-file naming-after">建设工程规划许可证_20260622_张三_v1.0.pdf</span>
        </div>
        <div style="margin-top:8px;font-size:12px;color:#888;text-align:center;">
            格式：内容摘要_日期_作者_版本号
        </div>
    </div>"""

    return HTML_TEMPLATE.format(
        title="🧠 FileBrain · 文件大脑",
        subtitle="桌面文件智能整理工具 — 工作流程",
        content=BOX_STYLE + step_html + arrows + naming_demo
    )


def make_github_image():
    """GitHub 上传步骤图"""
    steps = [
        ("打开 github.com/new", "在浏览器访问 GitHub，创建一个新仓库"),
        ("仓库名称填 FileBrain", "设为 Public（公开），不要勾选 README"),
        ("复制仓库地址", "创建后页面上会显示仓库 URL"),
        ("终端执行推送命令", f"<code class='code'>cd ~/FileBrain && git remote add origin https://github.com/mmm1111lhc/FileBrain.git && git push -u origin main</code>"),
        ("✅ 完成", "代码已上传到 GitHub，可以在视频里展示了！"),
    ]

    steps_html = ""
    for i, (title, desc) in enumerate(steps, 1):
        steps_html += f"""
        <div class="github-step">
            <div class="gs-num">{i}</div>
            <div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
        </div>"""

    return HTML_TEMPLATE.format(
        title="📤 上传 FileBrain 到 GitHub",
        subtitle="把你做的小工具开源分享给更多人",
        content=BOX_STYLE + steps_html
    )


def make_features_image():
    """功能总览图"""
    features = [
        ("👀", "自动扫描", "监控桌面文件夹，新文件出现自动处理"),
        ("🏷️", "智能命名", "提取内容 → 内容摘要_日期_作者_版本号"),
        ("📄", "PDF 识别", "文字 PDF + 扫描件 OCR（中英文）"),
        ("📝", "Word / Excel", "读取文档标题、内容，支持表格"),
        ("🖼️", "图片 OCR", "识别图片中的文字，提取关键信息"),
        ("🔎", "全文检索", "搜索关键词，瞬间定位是哪份文件"),
        ("📤", "发送留痕", "记录文件发给过谁、什么时间、什么方式"),
        ("📌", "版本管理", "按修改时间自动标注 v1.0、v1.1、v2.0..."),
    ]

    grid = '<div class="feature-grid">'
    for icon, title, desc in features:
        grid += f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-text">
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
        </div>"""
    grid += "</div>"

    # 使用场景
    scenarios = """
    <div style="background:#fff;border-radius:10px;padding:16px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <h3 style="color:#c97a3a;margin-bottom:10px;">💡 典型使用场景</h3>
        <div style="display:flex;gap:12px;">
            <div style="flex:1;background:#f8f6f2;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;">🏛️</div>
                <div style="font-size:13px;font-weight:bold;">政务软件下载</div>
                <div style="font-size:12px;color:#666;">浙里办、随申办→自动命名</div>
            </div>
            <div style="flex:1;background:#f8f6f2;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;">💼</div>
                <div style="font-size:13px;font-weight:bold;">办公文档管理</div>
                <div style="font-size:12px;color:#666;">合同/方案→按内容归档</div>
            </div>
            <div style="flex:1;background:#f8f6f2;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;">📚</div>
                <div style="font-size:13px;font-weight:bold;">学术资料整理</div>
                <div style="font-size:12px;color:#666;">论文/扫描件→OCR+检索</div>
            </div>
            <div style="flex:1;background:#f8f6f2;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;">🏠</div>
                <div style="font-size:13px;font-weight:bold;">个人文件归档</div>
                <div style="font-size:12px;color:#666;">证件扫描件→自动命名</div>
            </div>
        </div>
    </div>"""

    return HTML_TEMPLATE.format(
        title="🧠 FileBrain · 文件大脑",
        subtitle="8 大核心功能 · 4 大使用场景",
        content=BOX_STYLE + grid + scenarios
    )


async def render_html(html: str, output_path: str, width: int = 1080):
    """将 HTML 渲染为 PNG 图片"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": width, "height": 100},
            device_scale_factor=2
        )
        await page.set_content(html, wait_until="networkidle")
        await page.screenshot(
            path=output_path,
            full_page=True
        )
        await browser.close()
    print(f"✅ 图片已生成: {output_path}")


async def main():
    import os
    output_dir = os.path.expanduser("~/FileBrain/images")
    os.makedirs(output_dir, exist_ok=True)

    await render_html(
        make_workflow_image(),
        os.path.join(output_dir, "FileBrain_工作流程.png")
    )
    await render_html(
        make_features_image(),
        os.path.join(output_dir, "FileBrain_功能总览.png")
    )
    await render_html(
        make_github_image(),
        os.path.join(output_dir, "FileBrain_GitHub上传步骤.png")
    )
    print(f"\n🎉 全部图片已生成到 {output_dir}/")
    print("可以直接打开浏览器截图，或插入到视频中使用")


if __name__ == "__main__":
    asyncio.run(main())
