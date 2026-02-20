import os
import re

base_dir = "d:/새 폴더/uvm_page"
chapters_dir = os.path.join(base_dir, "final-chapters")
toc_file = os.path.join(chapters_dir, "book-table-of-contents.html")

with open(toc_file, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure CSS is there
if ".ch-sections a" not in content:
    css_to_add = """
    .ch-sections a { text-decoration: none; color: inherit; transition: color 0.15s; }
    .ch-sections a:hover { color: var(--accent); }
    """
    content = content.replace("</style>", css_to_add + "\n  </style>")

# For each chapter, find its <div class="ch-sections"> block and replace its inner HTML 
# with the generated links from the chapter's <nav class="toc">.
for ch_num in range(1, 16):
    padded_num = f"{ch_num:02d}"
    ch_filename = f"chapter-{padded_num}-final.html"
    ch_path = os.path.join(chapters_dir, ch_filename)
    
    if os.path.exists(ch_path):
        with open(ch_path, "r", encoding="utf-8") as f:
            ch_content = f.read()
        
        match = re.search(r'<nav class="toc">.*?<ul>(.*?)</ul>\s*</nav>', ch_content, re.DOTALL)
        if match:
            toc_list = match.group(1)
            links = re.findall(r'<li(?: class="(.*?)")?>\s*<a href="(.*?)">(.*?)</a>\s*</li>', toc_list)
            
            new_html = '<ul style="list-style:none;padding:0">\n'
            in_sub = False
            for cls, href, text in links:
                is_sub = "toc-sub" in str(cls)
                full_url = f"{ch_filename}{href}"
                
                if is_sub:
                    if not in_sub:
                        new_html += '            <ul class="subsection-list">\n'
                        in_sub = True
                    new_html += f'              <li class="subsection-item"><a href="{full_url}">{text}</a></li>\n'
                else:
                    if in_sub:
                        new_html += '            </ul>\n'
                        in_sub = False
                        new_html += '          </li>\n'
                    else:
                        if not new_html.endswith('<ul style="list-style:none;padding:0">\n'):
                            new_html += '          </li>\n'
                            
                    new_html += f'          <li class="section-item"><a href="{full_url}">{text}</a>\n'
                    
            if in_sub:
                new_html += '            </ul>\n          </li>\n'
            else:
                if not new_html.endswith('<ul style="list-style:none;padding:0">\n'):
                    new_html += '          </li>\n'
            
            new_html += '        </ul>'
            
            # Use a robust regex to replace everything inside the specific chapter's <div class="ch-sections"> ... </div>
            card_regex = re.compile(
                r'(<span class="ch-num">' + padded_num + r'</span>.*?'
                r'<div class="ch-sections">\s*)(.*?)(</div></div>)', 
                re.DOTALL
            )
            
            def repl(m):
                return m.group(1) + new_html + "\n      " + m.group(3)
                
            content = card_regex.sub(repl, content)

with open(toc_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Properly updated TOC sections with clickable links.")
