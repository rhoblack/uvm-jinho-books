import os
import re

file_path = "d:/새 폴더/uvm_page/final-chapters/book-table-of-contents.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make all anchor tags in the TOC trigger the parent window's iframe update
# We can do this by adding a small script at the end of the file, or changing hrefs.
# The easiest and most robust way without breaking the original page if viewed alone 
# is to let JS in the parent index.html handle it, or add an onclick handler to these links.

# Actually, the user wants the links in the "COMPLETE BOOK TABLE OF CONTENTS" (iframe) 
# to update the iframe itself (or tell the parent to update).
# If the links are just `<a href="chapter-01-final.html">`, they will naturally open in the iframe.
# BUT we want the parent's sidebar to also update its active state.
# Let's add a script to book-table-of-contents.html to communicate with the parent.

script_to_add = """
<script>
  document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('.ch-title');
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        // If we are inside an iframe
        if (window.parent !== window) {
          e.preventDefault();
          const href = link.getAttribute('href');
          const fullPath = 'final-chapters/' + href;
          
          // Find the corresponding nav-item in parent and click it to sync state
          const parentNavs = window.parent.document.querySelectorAll('.nav-item');
          let found = false;
          parentNavs.forEach(nav => {
            if (nav.getAttribute('data-src') === fullPath) {
              nav.click();
              found = true;
            }
          });
          
          // Fallback if not found in parent sidebar
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

if "<script>\n  document.addEventListener('DOMContentLoaded', () => {\n    const links" not in content:
    content = content.replace('</body>', script_to_add)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("book-table-of-contents.html successfully updated")
else:
    print("Script already exists in book-table-of-contents.html")
