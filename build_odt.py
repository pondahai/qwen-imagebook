import os
import re
import zipfile
import subprocess
from xml.sax.saxutils import escape

project_dir = r'C:\Users\USER\Downloads\qwen-imagebook'
compressed_dir = os.path.join(project_dir, 'compressed')
story_path = os.path.join(project_dir, 'storyboard', '完整故事.md')
output_odt = os.path.join(project_dir, '繪本_42頁完整版.odt')
temp_dir = os.path.join(project_dir, 'build_tmp')
os.makedirs(temp_dir, exist_ok=True)
docx_name = '繪本_42頁完整版.docx'
docx_path = os.path.join(temp_dir, docx_name)
soffice = r'C:\Program Files\LibreOffice\program\soffice.exe'
profile = 'file:///C:/Users/USER/AppData/Local/Temp/opencode/lo_profile_final'

# ---- parse story (完整故事.md: title + body) ----
with open(story_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

pages = {}
current = None
for line in lines:
    s = line.strip()
    m = re.match(r'^\*\*P(\d+)\s+(.+?)\*\*$', s)
    if m:
        current = int(m.group(1))
        pages[current] = {'title': m.group(2).strip(), 'body': ''}
        continue
    if current is None:
        continue
    if s.startswith('>'):
        pages[current]['body'] += s[1:].strip() + '\n'
    elif s.startswith('#') or s == '---':
        current = None

missing = [i for i in range(1, 43) if i not in pages or not pages[i]['body']]
if missing:
    raise SystemExit('Missing story pages: ' + str(missing))
print('Parsed story pages:', len(pages))

image_names = []
missing_img = []
for i in range(1, 43):
    name = 'page%d.jpg' % i
    if os.path.exists(os.path.join(compressed_dir, name)):
        image_names.append((i, name))
    else:
        missing_img.append(name)
if missing_img:
    raise SystemExit('Missing images: ' + ', '.join(missing_img))

# ---- DOCX XML helpers ----
EMU = 5040000  # 14 cm

def drawing_xml(i):
    return f'''<w:p>
  <w:pPr><w:spacing w:before="120" w:after="120"/><w:jc w:val="center"/></w:pPr>
  <w:r>
    <w:drawing>
      <wp:inline distT="0" distB="0" distL="0" distR="0">
        <wp:extent cx="{EMU}" cy="{EMU}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:docPr id="{i}" name="image{i}"/>
        <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
        <a:graphic>
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic>
              <pic:nvPicPr>
                <pic:cNvPr id="{i}" name="image{i}"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip r:embed="rId{i}"/>
                <a:stretch><a:fillRect/></a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm>
                  <a:off x="0" y="0"/>
                  <a:ext cx="{EMU}" cy="{EMU}"/>
                </a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>'''

def text_para(text, size=22, bold=False, align='left', color=None, before=0, after=120):
    t = escape(text)
    ppr = f'<w:spacing w:before="{before}" w:after="{after}"/><w:jc w:val="{align}"/>'
    rpr = f'<w:sz w:val="{size}"/>'
    if bold:
        rpr += '<w:b/>'
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    return f'<w:p><w:pPr>{ppr}</w:pPr><w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{t}</w:t></w:r></w:p>'

def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

body = []
for idx, i in enumerate(range(1, 43)):
    if idx > 0:
        body.append(page_break())
    p = pages[i]
    body.append(text_para(f'Page {i}', size=18, align='center', color='999999', after=60))
    body.append(text_para(f"P{i} {p['title']}", size=24, bold=True, align='center', after=60))
    body.append(drawing_xml(i))
    body.append(text_para(p['body'].strip(), size=22, align='left', before=120, after=0))

document_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
<w:body>
''' + '\n'.join(body) + '''
<w:sectPr>
  <w:pgSz w:w="11906" w:h="16838"/>
  <w:pgMar w:top="850" w:right="1134" w:bottom="850" w:left="1134" w:header="720" w:footer="720" w:gutter="0"/>
  <w:cols w:space="708"/>
</w:sectPr>
</w:body>
</w:document>'''

rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
for i in range(1, 43):
    rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{i}.jpg"/>')
rels.append('</Relationships>')
doc_rels_xml = '\n'.join(rels)

root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="jpg" ContentType="image/jpeg"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

if os.path.exists(docx_path):
    os.remove(docx_path)
z = zipfile.ZipFile(docx_path, 'w', zipfile.ZIP_DEFLATED)
z.writestr('[Content_Types].xml', content_types)
z.writestr('_rels/.rels', root_rels)
z.writestr('word/document.xml', document_xml)
z.writestr('word/_rels/document.xml.rels', doc_rels_xml)
for i, name in image_names:
    z.write(os.path.join(compressed_dir, name), f'word/media/image{i}.jpg')
z.close()
print('DOCX built:', docx_path, os.path.getsize(docx_path) // 1024, 'KB')

# ---- convert DOCX -> ODT ----
if os.path.exists(output_odt):
    os.remove(output_odt)
cmd = [
    soffice,
    '--headless',
    '--norestore',
    f'-env:UserInstallation={profile}',
    '--convert-to',
    'odt:writer8',
    '--outdir',
    project_dir,
    docx_path,
]
r = subprocess.run(cmd, capture_output=True, timeout=600)
print('DOCX->ODT stdout:', r.stdout.decode('utf-8', 'replace')[:800])
print('DOCX->ODT stderr:', r.stderr.decode('utf-8', 'replace')[:800])
print('ODT exists:', os.path.exists(output_odt), (os.path.getsize(output_odt) // 1024 // 1024 if os.path.exists(output_odt) else 0), 'MB')

# ---- roundtrip ODT to inspect frames/images ----
rt_dir = os.path.join(temp_dir, 'roundtrip')
os.makedirs(rt_dir, exist_ok=True)
rt_cmd = [
    soffice,
    '--headless',
    '--norestore',
    f'-env:UserInstallation={profile}',
    '--convert-to',
    'odt:writer8',
    '--outdir',
    rt_dir,
    output_odt,
]
r = subprocess.run(rt_cmd, capture_output=True, timeout=600)
rt_path = os.path.join(rt_dir, os.path.basename(output_odt))
print('Roundtrip exists:', os.path.exists(rt_path))
if os.path.exists(rt_path):
    zz = zipfile.ZipFile(rt_path)
    c = zz.read('content.xml').decode('utf-8', 'replace')
    frames = re.findall(r'<draw:frame[^>]*>', c)
    images = re.findall(r'<draw:image[^>]*>', c)
    media = [n for n in zz.namelist() if n.startswith('Pictures/') and n.endswith('.jpg')]
    print('Roundtrip frames:', len(frames), 'images:', len(images), 'jpg media:', len(media))

# ---- ODT -> PDF ----
pdf_dir = os.path.join(temp_dir, 'pdf')
os.makedirs(pdf_dir, exist_ok=True)
pdf_cmd = [
    soffice,
    '--headless',
    '--norestore',
    f'-env:UserInstallation={profile}',
    '--convert-to',
    'pdf',
    '--outdir',
    pdf_dir,
    output_odt,
]
r = subprocess.run(pdf_cmd, capture_output=True, timeout=600)
pdf_path = os.path.join(pdf_dir, os.path.basename(output_odt).replace('.odt', '.pdf'))
print('PDF exists:', os.path.exists(pdf_path))
if os.path.exists(pdf_path):
    size = os.path.getsize(pdf_path)
    with open(pdf_path, 'rb') as f:
        data = f.read()
    page_count = len(re.findall(rb'/Type\s*/Page[^s]', data))
    print('PDF size MB:', round(size / 1024 / 1024, 2), 'page_count:', page_count, 'image_embedded:', b'DCTDecode' in data)