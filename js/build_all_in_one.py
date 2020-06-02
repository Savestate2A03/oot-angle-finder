import re

def cleanjs(js):
    js = re.sub(re.compile("//#.*$", re.M), "", js)
    js = re.sub(re.compile("export ", re.M), "", js)
    js = re.sub(re.compile("import .*;.*$", re.M), "", js)
    return js

with open('use_ts.html', 'r') as f:
    htmlFile = f.read()
with open('dist/camera_favored.js') as f:
    favoredFile = cleanjs(f.read())
with open('dist/main.js') as f:
    mainFile = cleanjs(f.read())
with open('dist/angle_finder.js') as f:
    pureJSFile = cleanjs(f.read())

with open('oot-angle-finder.html', 'w') as w:
    newHtml = htmlFile.replace("<script type=\"module\" src=\"dist/main.js\"></script>", f"""
    <script type="text/javascript">
    {favoredFile}
    {pureJSFile}
    {mainFile}
    </script>
    """)
    w.write(newHtml)
