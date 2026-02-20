import os
import re

base_dir = "d:/새 폴더/uvm_page"
chapters_dir = os.path.join(base_dir, "final-chapters")
toc_file = os.path.join(chapters_dir, "book-table-of-contents.html")

with open(toc_file, "r", encoding="utf-8") as f:
    orig_content = f.read()

# Make sure CSS is there
if ".ch-sections a" not in orig_content:
    css_to_add = """
    .ch-sections a { text-decoration: none; color: inherit; transition: color 0.15s; }
    .ch-sections a:hover { color: var(--accent); }
    """
    orig_content = orig_content.replace("</style>", css_to_add + "\n  </style>")

# Split the content by ch-card to isolate each chapter
parts = re.split(r'(<!-- Ch\.\d+ -->)', orig_content)
new_content = parts[0]

for i in range(1, len(parts), 2):
    ch_marker = parts[i]
    ch_html = parts[i+1]
    
    # Extract chapter number
    m = re.search(r'<!-- Ch\.(\d+) -->', ch_marker)
    if m:
        ch_num = int(m.group(1))
        padded_num = f"{ch_num:02d}"
        ch_filename = f"chapter-{padded_num}-final.html"
        ch_path = os.path.join(chapters_dir, ch_filename)
        
        if os.path.exists(ch_path):
            with open(ch_path, "r", encoding="utf-8") as cf:
                ch_file_html = cf.read()
                
            toc_match = re.search(r'<nav class="toc">.*?<ul>(.*?)</ul>\s*</nav>', ch_file_html, re.DOTALL)
            if toc_match:
                toc_list = toc_match.group(1)
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
                
                # Now replace inside ch_html
                # We want to replace everything inside <div class="ch-sections"> ... </div>
                # Find the start of ch-sections
                sec_start = ch_html.find('<div class="ch-sections">')
                if sec_start != -1:
                    inner_start = sec_start + len('<div class="ch-sections">')
                    # Find the first </div> that closes ch_sections.
                    # Actually ch-body has:
                    # <div class="ch-sections">
                    #   ...
                    # </div>
                    # So we can just use regex for this specific chapter slice
                    ch_html = re.sub(r'(<div class="ch-sections">).*?(</div>\s*</div>)', r'\1\n' + new_html + r'\n\2', ch_html, flags=re.DOTALL)
    
    new_content += ch_marker + ch_html

with open(toc_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Links generated and injected successfully.")
