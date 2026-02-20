import os
import re

file_path = "d:/새 폴더/uvm_page/final-chapters/book-table-of-contents.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

script_to_add = """
<script>
  document.addEventListener('DOMContentLoaded', () => {
    // When clicking a chapter title
    const links = document.querySelectorAll('.ch-title');
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        if (window.parent !== window) {
          e.preventDefault();
          const href = link.getAttribute('href');
          const parentNavs = window.parent.document.querySelectorAll('.nav-chapter');
          
          let clicked = false;
          parentNavs.forEach(nav => {
            if (nav.getAttribute('data-src') === 'final-chapters/' + href) {
              nav.click();
              clicked = true;
            }
          });
          
          if (!clicked) window.location.href = href;
        }
      });
    });
  });
</script>
</body>
"""

if "document.querySelectorAll('.ch-title')" not in content:
    content = content.replace("</body>", script_to_add)
    with open(file_path, "w", encoding="utf-8") as f:
         f.write(content)
    print("Script injected successfully.")
else:
    print("Already injected.")
