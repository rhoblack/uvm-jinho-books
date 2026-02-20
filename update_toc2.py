import os

file_path = "d:/새 폴더/uvm_page/final-chapters/book-table-of-contents.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add JS that automatically overrides link clicks
js_code = """
<script>
  document.addEventListener('DOMContentLoaded', () => {
    // Override chapter links inside this iframe to talk to parent window
    const links = document.querySelectorAll('a');
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        if (window.parent !== window) {
          e.preventDefault();
          const href = link.getAttribute('href');
          
          if (href && href.startsWith('chapter-')) {
             const parentNavs = window.parent.document.querySelectorAll('.nav-item');
             let found = false;
             
             // First check exact match for sub-sections or chapters
             parentNavs.forEach(nav => {
                if (nav.getAttribute('data-src') === 'final-chapters/' + href) {
                   nav.click();
                   found = true;
                }
             });
             
             if (!found) {
                window.location.href = href;
             }
          } else {
             window.location.href = href;
          }
        }
      });
    });
  });
</script>
</body>
"""

if "<script>\n  document.addEventListener('DOMContentLoaded', () => {\n    // Override" not in content:
    content = content.replace("</body>", js_code)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("book-table-of-contents modified to link with parent.")
else:
    print("Already modified.")
