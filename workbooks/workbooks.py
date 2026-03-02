from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from IPython.display import HTML as IPyHTML, display
from ipywidgets import Button, Dropdown, HBox, Layout, Text, VBox
from panelobj import PanelObject

class ColabWorkbooks(PanelObject):

    def __init__(self, *args, **kwargs):
        self.title = 'Colab Workbooks'
        super().__init__(*args, **kwargs)
        self._notebooks: Dict[str, Path] = {}
        self._options: List[Tuple[str, str]] = []
        self.nbSW = Dropdown(options=[], value=None, description='Workbook:', layout=Layout(width='420px'), disabled=False)
        self.refreshBT = Button(description='Refresh', layout={'width': '120px'})
        self.previewBT = Button(description='Preview', layout={'width': '120px'})
        self.openURLBT = Button(description='Open URL', layout={'width': '120px'})
        self.urlTW = Text(value='', placeholder='Optional: paste a Colab / GitHub / nbviewer URL to open', description='URL:', layout=Layout(width='700px'))
        self.inpUSR.children += (VBox([HBox([self.nbSW, self.refreshBT, self.previewBT], layout={'gap': '8px'}), HBox([self.urlTW, self.openURLBT], layout={'gap': '8px'})], layout={'overflow': 'visible'}),)
        self.refreshBT.on_click(self._refresh_cb)
        self.previewBT.on_click(self._preview_cb)
        self.openURLBT.on_click(self._open_url_cb)
        self._refresh()

    def getCP(self):
        return self.cp

    def _candidate_dirs(self) -> List[Path]:
        dirs: List[Path] = []
        env = os.environ.get('GEORAD_WORKBOOKS_DIR', '').strip()
        if env:
            for part in env.split(os.pathsep):
                p = Path(part).expanduser().resolve()
                if p.exists() and p.is_dir():
                    dirs.append(p)
        dirs.append(Path(__file__).resolve().parent / 'notebooks')
        cwd = Path.cwd()
        for name in ('workbooks', 'notebooks', 'examples'):
            p = cwd / name
            if p.exists() and p.is_dir():
                dirs.append(p)
        seen = set()
        out: List[Path] = []
        for d in dirs:
            if d not in seen:
                seen.add(d)
                out.append(d)
        return out

    def _scan_notebooks(self) -> Dict[str, Path]:
        found: Dict[str, Path] = {}
        for d in self._candidate_dirs():
            try:
                for p in sorted(d.glob('*.ipynb')):
                    found.setdefault(p.name, p)
            except Exception:
                continue
        return found

    @staticmethod
    def _extract_title(nb_path: Path) -> Optional[str]:
        try:
            import nbformat
            nb = nbformat.read(str(nb_path), as_version=4)
            for cell in nb.cells:
                if getattr(cell, 'cell_type', '') != 'markdown':
                    continue
                src = (cell.source or '').strip()
                if not src:
                    continue
                line = src.splitlines()[0].strip()
                if line.startswith('#'):
                    line = line.lstrip('#').strip()
                line = re.sub('[*_`]', '', line).strip()
                if line:
                    return line[:120]
        except Exception:
            return None
        return None

    def _build_options(self, notebooks: Dict[str, Path]) -> List[Tuple[str, str]]:
        options: List[Tuple[str, str]] = []
        for fname, path in notebooks.items():
            title = self._extract_title(path)
            label = f'{title} ({fname})' if title else fname
            options.append((label, fname))
        return options

    def _refresh(self):
        self._notebooks = self._scan_notebooks()
        self._options = self._build_options(self._notebooks)
        self.nbSW.options = self._options
        self.nbSW.value = self._options[0][1] if self._options else None
        with self.out_cp:
            self.out_cp.clear_output()
            dirs = self._candidate_dirs()
            display(IPyHTML(f"<div style='font-size: 13px;'><b>Found {len(self._options)} workbook(s).</b><br>Search folders (in order):<br>" + '<br>'.join([f'&nbsp;&nbsp;• {d}' for d in dirs]) + '<br><br>Tip: set <code>GEORAD_WORKBOOKS_DIR</code> to your notebook folder to add your own workbooks.</div>'))

    @staticmethod
    def _render_notebook_html(nb_path: Path) -> str:
        try:
            from nbconvert import HTMLExporter
            exporter = HTMLExporter()
            exporter.exclude_input_prompt = True
            exporter.exclude_output_prompt = True
            body, _ = exporter.from_filename(str(nb_path))
            return "<div style='max-height: 600px; overflow: auto; border: 1px solid #ddd; padding: 8px;'>" + body + '</div>'
        except Exception:
            try:
                import nbformat
                nb = nbformat.read(str(nb_path), as_version=4)
                parts: List[str] = ["<div style='max-height: 600px; overflow: auto; border: 1px solid #ddd; padding: 8px;'>", f'<h3>{nb_path.name}</h3>']
                for cell in nb.cells:
                    if cell.cell_type == 'markdown':
                        txt = (cell.source or '').strip()
                        if txt:
                            parts.append("<pre style='white-space: pre-wrap;'>" + _escape_html(txt) + '</pre>')
                    elif cell.cell_type == 'code':
                        code = (cell.source or '').strip()
                        if code:
                            parts.append("<pre style='background:#f7f7f7; padding: 6px; white-space: pre-wrap;'>" + _escape_html(code) + '</pre>')
                parts.append('</div>')
                return '\n'.join(parts)
            except Exception as e:
                return f"<div style='color: #b00020;'>Unable to render notebook preview. Error: {_escape_html(str(e))}</div>"

    def _refresh_cb(self, _b):
        self._refresh()

    def _preview_cb(self, _b):
        if not self.nbSW.value:
            return
        nb_path = self._notebooks.get(self.nbSW.value)
        if not nb_path:
            return
        html = self._render_notebook_html(nb_path)
        with self.out_cp:
            self.out_cp.clear_output()
            display(IPyHTML(html))

    def _open_url_cb(self, _b):
        url = (self.urlTW.value or '').strip()
        if not url:
            with self.out_cp:
                self.out_cp.clear_output()
                display(IPyHTML('<div>Please paste a URL first.</div>'))
            return
        with self.out_cp:
            self.out_cp.clear_output()
            display(IPyHTML(f"<div style='font-size: 13px;'><b>Open workbook URL:</b><br><a href='{_escape_attr(url)}' target='_blank' rel='noopener noreferrer'>{_escape_html(url)}</a><br><br>If this is a Colab link, it will open in a new tab.</div>"))

def _escape_html(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def _escape_attr(s: str) -> str:
    return _escape_html(s)
