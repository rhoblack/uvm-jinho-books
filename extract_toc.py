import re
import os

html_files = [f"chapter-{i:02d}-final.html" for i in range(1, 16)]
base_dir = "d:/새 폴더/uvm_page/final-chapters"

sidebar_html = ""

for i, filename in enumerate(html_files):
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract TOC
    match = re.search(r'<nav class="toc">.*?<ul>(.*?)</ul>\s*</nav>', content, re.DOTALL)
    if not match:
        continue
        
    toc_html = match.group(1)
    
    # Process TOC items
    # We want to convert <li><a href="#id">text</a></li> to <a href="#" class="nav-sub-item" data-src="...">text</a>
    
    # Let's extract all links
    links = re.findall(r'<li(?: class="(.*?)")?><a href="(.*?)">(.*?)</a></li>', toc_html)
    
    sub_items = []
    for cls, href, text in links:
        is_sub = "toc-sub" in str(cls)
        # We might want to skip sub-sub sections for clarity or include them with more padding
        item_class = "nav-sub-item toc-sub" if is_sub else "nav-sub-item"
        target_src = f"final-chapters/{filename}{href}"
        sub_items.append(f'<a href="#" class="{item_class}" data-src="{target_src}">{text}</a>')
        
    print(f"Chapter {i+1} found {len(links)} sections")
    # Save the processed sub_items somewhere or just print to inspect
    with open(f"toc_ch{i+1}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sub_items))
