import os
file_path = "d:/새 폴더/uvm_page/final-chapters/book-table-of-contents.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Make sure hrefs are exactly triggering parent navs by adding an onclick
js_code = """
<script>
  document.addEventListener('DOMContentLoaded', () => {
    // Override chapter links inside this iframe to talk to parent window
    const links = document.querySelectorAll('.ch-title');
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        if (window.parent !== window) {
          e.preventDefault();
          const href = link.getAttribute('href');
          
          if (href && href.startsWith('chapter-')) {
             const parentNavs = window.parent.document.querySelectorAll('.nav-chapter');
             let found = false;
             
             // Check exact match for chapters
             parentNavs.forEach(nav => {
                if (nav.getAttribute('data-src') === 'final-chapters/' + href) {
                   nav.click();
                   found = true;
                }
             });
             
             if (!found) {
                window.location.href = href;
             }
          }
        }
      });
    });
  });
</script>
</body>
"""

if "<script>\n  document.addEventListener('DOMContentLoaded', () => {\n    // Override" not in content and "content.replace" not in content:
    content = content.replace("</body>", js_code)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("book-table-of-contents updated.")
else:
    print("Already updated.")
