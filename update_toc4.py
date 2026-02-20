import os
import re

file_path = "d:/새 폴더/uvm_page/final-chapters/book-table-of-contents.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

script_to_add = """
<script>
  document.addEventListener('DOMContentLoaded', () => {
    // Make both chapter titles and subsection links communicate with the parent window
    const allLinks = document.querySelectorAll('a[href^="chapter-"]');
    allLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        if (window.parent !== window) {
          e.preventDefault();
          const href = link.getAttribute('href'); // e.g. chapter-01-final.html#1-1-example
          const parentNavs = window.parent.document.querySelectorAll('.nav-item');
          
          let found = false;
          
          // First attempt: try finding exact match (especially helpful for sections with hashes)
          parentNavs.forEach(nav => {
            if (nav.getAttribute('data-src') === 'final-chapters/' + href) {
              nav.click();
              found = true;
            }
          });
          
          // Second attempt: if it's a chapter link with a hash and no exact match exists in the sidebar,
          // just click the main chapter link and let the iframe navigate to the hash natively.
          if (!found && href.includes('#')) {
             const baseHref = href.split('#')[0];
             parentNavs.forEach(nav => {
                if (nav.getAttribute('data-src') === 'final-chapters/' + baseHref) {
                   // We simulate clicking the chapter in the sidebar so it becomes active
                   nav.click();
                   // Then we manually tell the iframe to jump to the hash
                   window.location.href = href;
                   found = true;
                }
             });
          }
          
          // Fallback if not mapped in parent's sidebar at all
          if (!found) {
            window.location.href = href;
          }
        }
      });
    });
  });
</script>
</body>
"""

# Replace old script if it exists
if "<script>\n  document.addEventListener('DOMContentLoaded', () => {\n    const links = document.querySelectorAll('.ch-title');" in content:
    content = re.sub(r'<script>.*?</body>', script_to_add, content, flags=re.DOTALL)
elif "<script>\n  document.addEventListener('DOMContentLoaded', () => {\n    // Override" in content:
    content = re.sub(r'<script>.*?</body>', script_to_add, content, flags=re.DOTALL)
else:
    content = content.replace("</body>", script_to_add)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated book-table-of-contents.html links fully.")
