import os
import re

base_dir = "d:/새 폴더/uvm_page"
chapters_dir = os.path.join(base_dir, "final-chapters")
index_file = os.path.join(base_dir, "index.html")

# Define the book structure
groups = {
    "Part 1: 시작하기": [1, 2, 3, 4, 5],
    "Part 2: 깊이 파기": [6, 7, 8, 9, 10],
    "Part 3: 완성하기": [11, 12, 13, 14, 15]
}

chapter_titles = [
    "UVM 소개", "환경 설정", "SystemVerilog 핵심", "UVM 기본 컴포넌트", "첫 UVM 테스트벤치",
    "시퀀스 & 시퀀서", "드라이버 & 모니터 심화", "스코어보드 & 커버리지", "테스트 시나리오", "디버깅 기법",
    "인터페이스와 BFM", "레지스터 모델 (RAL)", "고급 시퀀스", "검증 자동화", "면접 준비 & 포트폴리오"
]

nav_html = ""

for group_name, ch_list in groups.items():
    nav_html += f'        <div class="nav-group">\n'
    nav_html += f'          <div class="nav-group-title">{group_name}</div>\n'
    
    for ch_num in ch_list:
        title = chapter_titles[ch_num-1]
        padded_num = f"{ch_num:02d}"
        ch_filename = f"chapter-{padded_num}-final.html"
        ch_path = os.path.join(chapters_dir, ch_filename)
        
        nav_html += f'          <div class="nav-chapter-container">\n'
        nav_html += f'            <a href="#" class="nav-item nav-chapter" data-src="final-chapters/{ch_filename}">\n'
        nav_html += f'              <span class="nav-num">{padded_num}</span> {title}\n'
        nav_html += f'            </a>\n'
        
        # Read the chapter file to get its TOC
        nav_html += f'            <div class="nav-sections">\n'
        if os.path.exists(ch_path):
            with open(ch_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'<nav class="toc">.*?<ul>(.*?)</ul>\s*</nav>', content, re.DOTALL)
            if match:
                toc_content = match.group(1)
                links = re.findall(r'<li(?: class="(.*?)")?>\s*<a href="(.*?)">(.*?)</a>\s*</li>', toc_content)
                for cls, href, text in links:
                    is_sub = "toc-sub" in str(cls)
                    item_class = "nav-item nav-section sub" if is_sub else "nav-item nav-section main"
                    target_src = f"final-chapters/{ch_filename}{href}"
                    nav_html += f'              <a href="#" class="{item_class}" data-src="{target_src}">{text}</a>\n'
        nav_html += f'            </div>\n'
        nav_html += f'          </div>\n'
    nav_html += f'        </div>\n\n'

html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UVM 완전정복 Book Viewer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-base: #24273a;
      --bg-mantle: #1e2030;
      --bg-crust: #181926;
      --text: #cad3f5;
      --subtext1: #b8c0e0;
      --subtext0: #a5adcb;
      --overlay2: #939ab7;
      --overlay1: #8087a2;
      --overlay0: #6e738d;
      --surface2: #5b6078;
      --surface1: #494d64;
      --surface0: #363a4f;
      
      --accent: #8aadf4; 
      --accent-hover: #7dc4e4; 
      --accent-active: #91d7e3; 
      
      --header-height: 60px;
      --sidebar-width: 320px;
      
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    }}
    
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-crust);
      color: var(--text);
      overflow: hidden; 
      display: flex;
      flex-direction: column;
      height: 100vh;
    }}

    header {{
      height: var(--header-height);
      background-color: var(--bg-mantle);
      border-bottom: 1px solid var(--surface0);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      z-index: 10;
      box-shadow: var(--shadow-sm);
    }}
    
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 700;
      font-size: 1.2rem;
      color: var(--accent);
      text-decoration: none;
    }}
    
    .brand span {{ color: var(--text); }}
    
    .header-actions {{ display: flex; align-items: center; gap: 16px; }}
    
    .icon-btn {{
      background: transparent; border: none; color: var(--subtext0);
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      width: 36px; height: 36px; border-radius: 8px; transition: all 0.2s;
    }}
    
    .icon-btn:hover {{ background-color: var(--surface0); color: var(--accent); }}
    
    .app-container {{
      display: flex; flex: 1; height: calc(100vh - var(--header-height)); overflow: hidden;
    }}
    
    .sidebar {{
      width: var(--sidebar-width); background-color: var(--bg-mantle);
      border-right: 1px solid var(--surface0); display: flex; flex-direction: column;
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); z-index: 5;
    }}
    
    .sidebar-header {{
      padding: 16px 20px; border-bottom: 1px solid var(--surface0);
      font-size: 0.9rem; font-weight: 600; color: var(--subtext1);
      text-transform: uppercase; letter-spacing: 0.5px;
    }}
    
    .toc-scroll-area {{ flex: 1; overflow-y: auto; padding: 12px 12px 24px; }}
    .toc-scroll-area::-webkit-scrollbar {{ width: 6px; }}
    .toc-scroll-area::-webkit-scrollbar-track {{ background: transparent; }}
    .toc-scroll-area::-webkit-scrollbar-thumb {{ background: var(--surface1); border-radius: 3px; }}
    .toc-scroll-area::-webkit-scrollbar-thumb:hover {{ background: var(--surface2); }}
    
    .nav-group {{ margin-bottom: 12px; }}
    .nav-group-title {{
      font-size: 0.75rem; font-weight: 700; color: var(--overlay1);
      padding: 8px 12px; text-transform: uppercase; letter-spacing: 1px;
    }}
    
    .nav-chapter-container {{ margin-bottom: 2px; }}
    
    .nav-item {{
      display: block; padding: 10px 12px; margin-bottom: 2px; border-radius: 6px;
      color: var(--subtext0); text-decoration: none; font-size: 0.9rem;
      font-weight: 500; transition: all 0.2s; border: 1px solid transparent; line-height: 1.4;
    }}
    
    .nav-item:hover {{ background-color: var(--surface0); color: var(--text); }}
    .nav-item.active {{
      background-color: rgba(138, 173, 244, 0.1); color: var(--accent);
      border-color: rgba(138, 173, 244, 0.2); font-weight: 600;
    }}
    
    .nav-num {{
      display: inline-block; width: 28px; font-family: 'JetBrains Mono', monospace;
      font-size: 0.8em; opacity: 0.7; margin-right: 4px;
    }}
    
    /* Sub-sections */
    .nav-sections {{
      display: none; padding-left: 28px; margin-top: 2px; margin-bottom: 8px;
    }}
    .nav-chapter-container.expanded .nav-sections {{ display: block; }}
    
    .nav-section {{
      font-size: 0.8rem; padding: 6px 10px; color: var(--subtext1);
      margin-bottom: 2px; font-weight: 400; border-left: 1px solid var(--surface0);
      border-radius: 0 6px 6px 0;
    }}
    .nav-section:hover {{ border-left-color: var(--accent); }}
    .nav-section.active {{ border-left-color: var(--accent); }}
    
    .nav-section.sub {{ padding-left: 16px; font-size: 0.75rem; color: var(--overlay0); border-left: none; }}
    .nav-section.sub:before {{ content: "- "; opacity: 0.5; }}
    
    .content-area {{ flex: 1; background-color: var(--bg-base); position: relative; display: flex; flex-direction: column; }}
    .content-frame {{ width: 100%; height: 100%; border: none; background-color: #ffffff; transition: filter 0.3s; }}
    
    .loader {{
      position: absolute; top: 0; left: 0; right: 0; bottom: 0;
      background-color: var(--bg-base); display: flex; flex-direction: column;
      align-items: center; justify-content: center; z-index: 10;
      opacity: 0; pointer-events: none; transition: opacity 0.3s;
    }}
    .loader.active {{ opacity: 1; pointer-events: all; }}
    
    .spinner {{
      width: 40px; height: 40px; border: 3px solid var(--surface1);
      border-top-color: var(--accent); border-radius: 50%;
      animation: spin 1s linear infinite; margin-bottom: 16px;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    
    .menu-toggle {{ display: none; }}
    .backdrop {{
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.5); z-index: 4; opacity: 0; pointer-events: none; transition: opacity 0.3s;
    }}
    
    @media (max-width: 768px) {{
      .menu-toggle {{ display: flex; }}
      .sidebar {{
        position: fixed; top: var(--header-height); left: 0; bottom: 0;
        transform: translateX(-100%); box-shadow: var(--shadow-lg);
      }}
      .sidebar.open {{ transform: translateX(0); }}
      .backdrop.open {{ opacity: 1; pointer-events: all; }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <button class="icon-btn menu-toggle" id="menuToggle" aria-label="Toggle Menu">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
      </button>
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
      <span>UVM Book Viewer</span>
    </div>
    <div class="header-actions">
      <a href="final-chapters/book-table-of-contents.html" target="chapterFrame" class="icon-btn" title="전체 목차">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
      </a>
    </div>
  </header>

  <div class="app-container">
    <div class="backdrop" id="backdrop"></div>
    
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">목차 (Table of Contents)</div>
      <div class="toc-scroll-area">
        <div class="nav-group">
           <a href="#" class="nav-item active" data-src="final-chapters/book-table-of-contents.html">📘 전체 목차 보기</a>
        </div>

{nav_html}

      </div>
    </aside>
    
    <main class="content-area">
      <div class="loader" id="loader">
        <div class="spinner"></div>
        <p>Loading Content...</p>
      </div>
      <iframe src="final-chapters/book-table-of-contents.html" class="content-frame" id="chapterFrame" name="chapterFrame" title="Book Content"></iframe>
    </main>
    
  </div>

  <script>
    document.addEventListener('DOMContentLoaded', () => {{
      const navItems = document.querySelectorAll('.nav-item');
      const navChapters = document.querySelectorAll('.nav-chapter');
      const iframe = document.getElementById('chapterFrame');
      const loader = document.getElementById('loader');
      const sidebar = document.getElementById('sidebar');
      const backdrop = document.getElementById('backdrop');
      const menuToggle = document.getElementById('menuToggle');
      
      iframe.addEventListener('load', () => {{
        loader.classList.remove('active');
      }});
      
      navItems.forEach(item => {{
        item.addEventListener('click', (e) => {{
          e.preventDefault();
          
          const targetSrc = item.getAttribute('data-src');
          
          // Manage active class
          navItems.forEach(nav => nav.classList.remove('active'));
          item.classList.add('active');
          
          // Expand logic for chapter click
          if(item.classList.contains('nav-chapter')) {{
            const currentContainer = item.closest('.nav-chapter-container');
            // Toggle expanded
            const isExpanded = currentContainer.classList.contains('expanded');
            
            // Optionally collapse others
            document.querySelectorAll('.nav-chapter-container').forEach(c => c.classList.remove('expanded'));
            
            if (!isExpanded) {{
              currentContainer.classList.add('expanded');
            }}
          }} else if(item.classList.contains('nav-section')) {{
            // Keep the parent chapter expanded
            const parent = item.closest('.nav-chapter-container');
            if(parent) parent.classList.add('expanded');
            // also highlight the parent chapter slightly
            parent.querySelector('.nav-chapter').classList.add('active');
          }}
          
          // Navigate iframe
          if(targetSrc && iframe.getAttribute('src') !== targetSrc) {{
            loader.classList.add('active');
            iframe.src = targetSrc;
          }} else if (targetSrc && iframe.getAttribute('src') === targetSrc) {{
            // force un-hash and hash to scroll to id if it's the same page
            if (targetSrc.includes('#')) {{
              iframe.src = targetSrc;
            }}
          }}
          
          if(window.innerWidth <= 768) {{
            sidebar.classList.remove('open');
            backdrop.classList.remove('open');
          }}
        }});
      }});
      
      menuToggle.addEventListener('click', () => {{
        sidebar.classList.toggle('open');
        backdrop.classList.toggle('open');
      }});
      
      backdrop.addEventListener('click', () => {{
        sidebar.classList.remove('open');
        backdrop.classList.remove('open');
      }});
      
    }});
  </script>
</body>
</html>"""

with open(index_file, "w", encoding="utf-8") as f:
    f.write(html_template)
print("index.html successfully updated")
