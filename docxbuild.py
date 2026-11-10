"""Small python-docx helpers: inline markup (**bold**, *italic*, ^sup^, ~sub~), citation keys [@A,B] numbered by first use,
headings, figures, tables, line numbers and page numbers, matching the original manuscript (Arial 11, A4, double spacing)."""
import re
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

TOKEN = re.compile(r'(\*\*.+?\*\*|\*[^*\s][^*]*?\*|\^[^^]+?\^|~[^~\s][^~]*?~)')


import re as _re
def clean_cell(v):
    v = v.replace('->', '→')
    v = _re.sub(r'(^|[\s(\[/])-(?=\d)', lambda m: m.group(1) + '−', v)
    v = _re.sub(r'[−+]0(\.0+)?(?![\d.])', lambda m: '0' + (m.group(1) or ''), v)
    v = _re.sub(r'(\d)–(−?\d)', lambda m: m.group(0), v)
    return v


class Doc:
    def __init__(self, refs=None, line_numbers=True, spacing=2.0, size=11):
        self.d = Document(); self.refs = refs or {}; self.order = []; self.size = size; self.spacing = spacing
        sec = self.d.sections[0]
        sec.page_width, sec.page_height = Mm(210), Mm(297)
        for m in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'): setattr(sec, m, Mm(25.4))
        st = self.d.styles['Normal']; st.font.name = 'Arial'; st.font.size = Pt(size)
        st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
        pf = st.paragraph_format; pf.line_spacing = spacing; pf.space_after = Pt(0); pf.space_before = Pt(0)
        for lvl, sz in ((1, 14), (2, 12), (3, 11)):
            h = self.d.styles[f'Heading {lvl}']; h.font.name = 'Arial'; h.font.size = Pt(sz); h.font.bold = True; h.font.italic = False
            h.font.color.rgb = RGBColor(0, 0, 0); h.element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial'); h.element.rPr.rFonts.set(qn('w:ascii'), 'Arial'); h.element.rPr.rFonts.set(qn('w:hAnsi'), 'Arial')
            h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(6); h.paragraph_format.keep_with_next = True
            h.paragraph_format.line_spacing = spacing
        if line_numbers:
            ln = OxmlElement('w:lnNumType'); ln.set(qn('w:countBy'), '1'); ln.set(qn('w:distance'), '300'); ln.set(qn('w:restart'), 'continuous')
            sec._sectPr.append(ln)
        p = sec.footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._field(p, 'PAGE')

    def _field(self, p, code):
        r = p.add_run(); f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'), 'begin'); r._r.append(f1)
        r2 = p.add_run(); it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = code; r2._r.append(it)
        r3 = p.add_run(); f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'), 'end'); r3._r.append(f2)

    def cite(self, keys):
        nums = []
        for k in keys:
            k = k.strip()
            if k not in self.refs: raise KeyError(f'missing reference {k}')
            if k not in self.order: self.order.append(k)
            nums.append(self.order.index(k) + 1)
        nums = sorted(set(nums)); out = []; i = 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1: j += 1
            out.append(f'{nums[i]}–{nums[j]}' if j - i >= 2 else (f'{nums[i]},{nums[j]}' if j == i + 1 else f'{nums[i]}'))
            i = j + 1
        return ','.join(out)

    def runs(self, p, text, size=None, color=None):
        text = re.sub(r'\[@([^\]]+)\]', lambda m: '^' + self.cite(m.group(1).split(',')) + '^', text)
        for part in TOKEN.split(text):
            if not part: continue
            kw = {}
            if part.startswith('**') and part.endswith('**') and len(part) > 4: t, kw = part[2:-2], dict(bold=True)
            elif part.startswith('*') and part.endswith('*') and len(part) > 2: t, kw = part[1:-1], dict(italic=True)
            elif part.startswith('^') and part.endswith('^') and len(part) > 2: t, kw = part[1:-1], dict(sup=True)
            elif part.startswith('~') and part.endswith('~') and len(part) > 2: t, kw = part[1:-1], dict(sub=True)
            else: t = part
            # nested italic inside bold e.g. **a *b***: keep simple
            r = p.add_run(t)
            if kw.get('bold'): r.bold = True
            if kw.get('italic'): r.italic = True
            if kw.get('sup'): r.font.superscript = True
            if kw.get('sub'): r.font.subscript = True
            if size: r.font.size = Pt(size)
            if color: r.font.color.rgb = RGBColor(*color)
        return p

    def h(self, text, level=1):
        p = self.d.add_heading(level=level); self.runs(p, text); return p

    def para(self, text, align=None, size=None, after=0, before=0, indent_first=False, spacing=None, keep=False):
        p = self.d.add_paragraph(); self.runs(p, text, size=size)
        pf = p.paragraph_format; pf.space_after = Pt(after); pf.space_before = Pt(before)
        if spacing: pf.line_spacing = spacing
        if align == 'center': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == 'justify': p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if keep: pf.keep_with_next = True
        return p

    def equation(self, text, num):
        t = self.d.add_table(rows=1, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        w = [Mm(140), Mm(19)]
        for i, c in enumerate(t.rows[0].cells): c.width = w[i]
        p = t.rows[0].cells[0].paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER; self.runs(p, text)
        q = t.rows[0].cells[1].paragraphs[0]; q.alignment = WD_ALIGN_PARAGRAPH.RIGHT; q.add_run(f'({num})')
        self._noborders(t)
        return t

    def _noborders(self, t):
        tbl = t._tbl; pr = tbl.tblPr; b = OxmlElement('w:tblBorders')
        for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            el = OxmlElement(f'w:{e}'); el.set(qn('w:val'), 'nil'); b.append(el)
        pr.append(b)

    def figure(self, path, caption, width_mm=165):
        p = self.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Mm(width_mm))
        c = self.para(caption, after=12, spacing=1.5)
        return c

    def _border(self, el_parent, tag, sides):
        b = OxmlElement(tag)
        for e, val, sz in sides:
            el = OxmlElement(f'w:{e}'); el.set(qn('w:val'), val)
            if val != 'nil': el.set(qn('w:sz'), str(sz)); el.set(qn('w:space'), '0'); el.set(qn('w:color'), '000000')
            b.append(el)
        el_parent.append(b)

    def table(self, header, rows, widths_mm=None, size=8, bold_header=True, caption=None, note=None, group_rows=None):
        """Nature style: bold title above ('Table n | Title.'), three horizontal rules (top, below the header, bottom), no
        vertical rules or shading; the legend goes below the table as a note. If `caption` holds the title followed by a
        legend, the legend is moved below the table."""
        legend = None
        if caption:
            m = re.match(r'^(\*\*.+?\*\*)\s*(.*)$', caption, flags=re.S)
            title, legend = (m.group(1), m.group(2).strip()) if m else (caption, None)
            self.para(title, spacing=1.15, after=4, keep=True)
        t = self.d.add_table(rows=1 + len(rows), cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._border(t._tbl.tblPr, 'w:tblBorders', [('top', 'single', 8), ('left', 'nil', 0), ('bottom', 'single', 8), ('right', 'nil', 0),
                                                    ('insideH', 'nil', 0), ('insideV', 'nil', 0)])
        for j, hd in enumerate(header):
            cell = t.rows[0].cells[j]; cell.paragraphs[0].paragraph_format.line_spacing = 1.0
            cell.paragraphs[0].paragraph_format.space_before = Pt(2); cell.paragraphs[0].paragraph_format.space_after = Pt(2)
            self.runs(cell.paragraphs[0], str(hd), size=size)
            for rr in cell.paragraphs[0].runs: rr.bold = bold_header
            self._border(cell._tc.get_or_add_tcPr(), 'w:tcBorders', [('bottom', 'single', 4)])
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                cell = t.rows[i + 1].cells[j]; pf = cell.paragraphs[0].paragraph_format; pf.line_spacing = 1.0; pf.space_before = Pt(1); pf.space_after = Pt(1)
                self.runs(cell.paragraphs[0], clean_cell(str(v)) or '\u200b', size=size)
                if j > 0 and re.match(r'^[−+\-]?[0-9.,]+', clean_cell(str(v))): cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        if widths_mm:
            tot = sum(widths_mm); scale = min(1.0, 159.0 / tot); widths_mm = [w * scale for w in widths_mm]
            t.autofit = False
            tblPr = t._tbl.tblPr
            lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
            tw = OxmlElement('w:tblW'); tw.set(qn('w:w'), str(int(sum(widths_mm) * 56.7))); tw.set(qn('w:type'), 'dxa')
            for old in tblPr.findall(qn('w:tblW')): tblPr.remove(old)
            tblPr.append(tw)
            grid = t._tbl.tblGrid
            for j, gc in enumerate(grid.findall(qn('w:gridCol'))): gc.set(qn('w:w'), str(int(widths_mm[j] * 56.7)))
            for row in t.rows:
                for j, c in enumerate(row.cells): c.width = Mm(widths_mm[j])
            mar = OxmlElement('w:tblCellMar')
            for side in ('left', 'right'):
                e = OxmlElement(f'w:{side}'); e.set(qn('w:w'), '57'); e.set(qn('w:type'), 'dxa'); mar.append(e)
            tblPr.append(mar)
        trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement('w:tblHeader'); th.set(qn('w:val'), 'true'); trPr.append(th)
        text = ' '.join(x for x in [legend, note] if x)
        if text: self.para(text, size=8, spacing=1.15, after=10)
        else: self.para('', after=6)
        return t

    def box(self, paras, size=10):
        t = self.d.add_table(rows=1, cols=1); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = t.rows[0].cells[0]; cell.width = Mm(159)
        sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), 'F2F2F2'); cell._tc.get_or_add_tcPr().append(sh)
        first = True
        for ptxt in paras:
            p = cell.paragraphs[0] if first else cell.add_paragraph(); first = False
            p.paragraph_format.line_spacing = 1.15; p.paragraph_format.space_after = Pt(4)
            self.runs(p, ptxt, size=size)
        self.para('', after=6)
        return t

    def pagebreak(self):
        from docx.enum.text import WD_BREAK
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def references(self, title='References'):
        self.h(title, 1)
        for i, k in enumerate(self.order):
            p = self.para(f'{i + 1}. ' + self.refs[k], spacing=self.spacing)

    def save(self, path):
        self.d.save(path)
