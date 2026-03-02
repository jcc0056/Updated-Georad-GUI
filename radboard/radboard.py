from __future__ import annotations
import functools
import importlib
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple, Union
from IPython.display import display
from ipywidgets import HBox, VBox, Button, Layout, HTML, Output, GridspecLayout, Dropdown, Textarea, Text, Password
from panelobj import PanelObject
PanelFactory = Union[type, Callable[[], Any], str]

@dataclass(frozen=True)
class RegisteredPanel:
    factory: PanelFactory
    description: str

def _resolve_factory(factory: PanelFactory) -> Callable[[], Any]:
    if isinstance(factory, str):
        if ':' in factory:
            mod_name, attr = factory.split(':', 1)
        else:
            parts = factory.split('.')
            if len(parts) < 2:
                raise ValueError(f'Invalid import path: {factory!r}')
            mod_name, attr = ('.'.join(parts[:-1]), parts[-1])
        mod = importlib.import_module(mod_name)
        obj = getattr(mod, attr)
        if not callable(obj):
            raise TypeError(f'Imported object {factory!r} is not callable')
        return obj
    if callable(factory):
        return factory
    raise TypeError(f'Unsupported factory type: {type(factory)}')

class _ErrorPanel(PanelObject):

    def __init__(self, title: str, error: BaseException):
        self.title = title
        super().__init__()
        with self.out_cp:
            self.out_cp.clear_output()
            tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            display(HTML(f"<div style='font-family: monospace; font-size: 12px;'><b>Panel failed to initialize.</b><br>This does <i>not</i> crash the whole dashboard anymore.<br><br><b>Error:</b><br><pre>{tb}</pre></div>"))

    def getCP(self):
        return self.cp

#Added all

class RADashBoard:

    def __init__(self):
        self.out_cp = Output()
        display(self.out_cp)
        self._panels: Dict[str, RegisteredPanel] = {}
        self.title = 'Research & Applications Dashboard'
        self.nx = 1
        self.ny = 1
        self.panelWidth = [250, 500]
        self.panelHeight = [250, 500]
        #self.ob  =   OpenAQGui().createCP()
        self.gridGap = 15
        self.gridPad = 15
        self.panelBorder = 3
        self.dbBorder = 5
        self.pwdDict: Dict[str, Dict[str, str]] = {}
        self.accList = ['NASA Earth Data']
        self.cpMain = None

    def addAccount(self, accname: str) -> None:
        self.accList.append(accname)

    def addObject(self, obj: PanelFactory, short_name: str, desc: str) -> None:
        self._panels[short_name] = RegisteredPanel(factory=obj, description=desc)

    def displayCP(self):
        self.rowSW = Dropdown(options=[1, 2, 3, 4], value=1, description='Rows:', disabled=False, layout={'width': '150px'})
        self.colSW = Dropdown(options=[1, 2, 3, 4], value=1, description='Columns:', disabled=False, layout={'width': '150px'})
        self.conDB = Button(description='Configure Dashboard', disabled=False, layout={'width': '150px', 'border': '3px outset'})
        self.topLabel = HTML(disabled=False, layout={'width': 'auto'})
        self.topLabel.value = f"""<div style="background-color: #C0C0C0; padding: 1em 0em 0em 0em; border-bottom-style:groove; border-width:4px"><b><font size='4'><center><h2>{self.title}</h2></center></font></b></div>"""
        self.rule = HTML(disabled=True, layout=Layout(width='auto', padding='0px'))
        self.rule.value = '<div><hr></div>'
        self.cpMain = VBox([HBox([self.topLabel], layout={'justify_content': 'center', 'flex_flow': 'column'}), HBox([HBox([self.rowSW], layout={'justify_content': 'flex-start'}), HBox([self.colSW], layout={'justify_content': 'flex-end'})], layout={'padding': '15px'}), HBox([self.conDB], layout={'justify_content': 'center', 'padding': '15px'})], layout={'border': '3px groove', 'width': '400px'})
        self.rowSW.observe(self._rowSWCB, names='value')
        self.colSW.observe(self._colSWCB, names='value')
        self.conDB.on_click(self._configDBCB)
        with self.out_cp:
            self.out_cp.clear_output()
            display(self.cpMain)

    def _rowSWCB(self, change):
        if change.get('type') == 'change':
            # set the city to the new user selected value given 
            # by the "value" attribute in the city selection widget.

            self.ny = int(self.rowSW.value)

    def _colSWCB(self, change):
        if change.get('type') == 'change':
            # set the city to the new user selected value given 
            # by the "value" attribute in the city selection widget.

            self.nx = int(self.colSW.value)

    def _configDBCB(self, b):
        self.out_cp.clear_output()
        self.objList = list(self._panels.keys())
        if not self.objList:
            with self.out_cp:
                display(HTML('<b>No panels registered.</b>'))
            return
        pw = self.panelWidth[0]
        lw = pw * self.nx + (self.nx - 1) * self.gridGap + self.gridPad * 2
        gw = lw + 2 * self.dbBorder
        self.topLabel.layout = {'width': f'{lw - 2}px'}
        gap = f'{self.gridGap}px'
        pd = str(self.gridPad)
        pad = f'{pd}px {pd}px {pd}px {pd}px'
        self.gridDB1 = GridspecLayout(self.ny, self.nx, layout={'scroll': 'False', 'grid_gap': gap, 'padding': pad})
        self.objSW = [[None] * self.nx for _ in range(self.ny)]
        self.objinfoTW = [[None] * self.nx for _ in range(self.ny)]
        self.pwTW = [[None] * self.nx for _ in range(self.ny)]
        self.phTW = [[None] * self.nx for _ in range(self.ny)]
        txw = f'{int(0.96 * float(self.panelWidth[0]))}px'
        for i in range(self.ny):
            for j in range(self.nx):
                desc = f'Panel({i + 1},{j + 1}):'
                self.objSW[i][j] = Dropdown(options=self.objList, value=self.objList[0], description=desc, disabled=False, layout={'width': txw})
                objinfo = self._panels[self.objList[0]].description
                self.objinfoTW[i][j] = Textarea(value=objinfo, placeholder='', description='', disabled=False, layout={'width': txw, 'border': '2px inset'})
                self.pwTW[i][j] = Text(value=str(self.panelWidth[1]), placeholder='', description='Panel Width:', disabled=False, layout={'width': txw, 'border': '2px inset'})
                self.phTW[i][j] = Text(value=str(self.panelHeight[1]), placeholder='', description='Panel Height', disabled=False, layout={'width': txw, 'border': '2px inset'})
                self.gridDB1[i, j] = VBox([self.objSW[i][j], self.pwTW[i][j], self.phTW[i][j], self.objinfoTW[i][j]], layout={'border': '2px solid black'})
                self.objSW[i][j].observe(functools.partial(self._objSWCB, irow_=i, jcol_=j), names='value')
                self.phTW[i][j].observe(functools.partial(self._phTWCB, irow_=i, jcol_=j), names='value')
        gp = f'{self.gridPad}px'
        dbb = f'{self.dbBorder}px groove'
        dbw = f'{gw}px'
        self.pmLabel = HTML(disabled=False, layout={'width': 'auto', 'flex_flow': 'column'})
        self.pmLabel.value = '<div style="background-color: #C0C0C0; border-top-style:groove; border-width:3px; padding: 1em 0em 0em 0em; border-bottom-style:groove; border-width:3px"><b><font size=\'4\'><center><h3>Password Manager</h3></center></font></b></div>'
        self.accSW = Dropdown(options=self.accList, value=self.accList[0], description='Account:', disabled=False, layout={'width': txw})
        self.usrTW = Text(value='', placeholder='', description='Username:', disabled=False, layout={'width': txw})
        self.pwdPW = Password(value='', placeholder='', description='Password:', disabled=False, layout={'width': txw})
        self.addPWD = Button(description='Add Account', disabled=False, layout={'width': '150px', 'border': '3px outset'})
        self.createDB = Button(description='Create Dashboard', disabled=False, layout={'width': '150px', 'border': '3px outset'})
        self.reconfigDB = Button(description='Reconfigure Dashboard', disabled=False, layout={'width': '180px', 'border': '3px outset'})
        self.addPWD.on_click(self._addPWDCB)
        self.createDB.on_click(self._createDBCB)
        self.reconfigDB.on_click(self._reconfigDBCB)
        self.cp = VBox([HBox([self.topLabel], layout={'flex_flow': 'column'}), HBox([self.gridDB1]), HBox([self.pmLabel], layout={'flex_flow': 'column'}), VBox([self.accSW, self.usrTW, self.pwdPW]), HBox([self.addPWD], layout={'justify_content': 'center'}), self.rule, HBox([self.reconfigDB, self.createDB], layout={'justify_content': 'center', 'padding': gp})], layout={'border': dbb, 'width': dbw})
        with self.out_cp:
            self.out_cp.clear_output()
            display(self.cp)

    def _objSWCB(self, change, irow_, jcol_):
        name = self.objSW[irow_][jcol_].value
        self.objinfoTW[irow_][jcol_].value = self._panels[name].description

    def _phTWCB(self, change, irow_, jcol_):
        self.objinfoTW[irow_][jcol_].value = 'Hint: Set the same height of all the panels in a row for optimal panel layout'

    def _addPWDCB(self, b):
        self.pwdDict[self.accSW.value] = {'user': self.usrTW.value, 'password': self.pwdPW.value}

    def _createDBCB(self, b):
        self.out_cp.clear_output()
        wd = [0] * self.ny
        for i in range(self.ny):
            for j in range(self.nx):
                wd[i] += int(self.pwTW[i][j].value)
        tpw = max(wd)
        lw = tpw + (self.nx - 1) * self.gridGap + self.gridPad * 2
        gw = lw + 2 * self.dbBorder
        gap = f'{self.gridGap}px'
        pd = str(self.gridPad)
        pad = f'{pd}px {pd}px {pd}px {pd}px'
        self.gridDB2 = GridspecLayout(self.ny, self.nx, layout={'scroll': 'True', 'grid_gap': gap, 'padding': pad})
        pb = f'{self.panelBorder}px groove'
        for i in range(self.ny):
            for j in range(self.nx):
                pw = f'{self.pwTW[i][j].value}px'
                ph = f'{self.phTW[i][j].value}px'
                name = self.objSW[i][j].value
                reg = self._panels[name]
                try:
                    factory = _resolve_factory(reg.factory)
                    obj = factory()
                    if hasattr(obj, 'pwdDict'):
                        obj.pwdDict = self.pwdDict
                    if hasattr(obj, 'spacer'):
                        obj.spacer.layout = {'width': pw}
                    cp = obj.getCP() if hasattr(obj, 'getCP') else obj
                except Exception as e:
                    cp = _ErrorPanel(f'{name} (Error)', e).getCP()
                try:
                    cp.layout = {'overflow_x': 'visible', 'overflow_y': 'visible'}
                except Exception:
                    pass
                self.gridDB2[i, j] = HBox([cp], layout={'height': ph, 'width': pw, 'border': pb})
        gp = f'{self.gridPad}px'
        dbb = f'{self.dbBorder}px groove'
        dbw = f'{gw}px'
        self.topLabel.layout = {'width': 'auto'}
        self.cp = VBox([VBox([self.topLabel, self.gridDB2], layout={'flex_flow': 'column'}), HBox([self.reconfigDB], layout={'justify_content': 'center', 'padding': gp})], layout={'border': dbb, 'width': dbw})
        with self.out_cp:
            self.out_cp.clear_output()
            display(self.cp)

    def _reconfigDBCB(self, b):
        with self.out_cp:
            self.out_cp.clear_output()
            if self.cpMain is not None:
                display(self.cpMain)

class AQDashBoard:

    def __init__(self):
        self.DashBoard = RADashBoard()
        self.DashBoard.title = 'Air Pollution Research & Applications Dashboard'
        self.DashBoard.addObject('oaqtools:QueryOpenAq', 'OpenAQ Query', 'Query OpenAQ database')
        self.DashBoard.addObject('oaqtools:PlotOpenAq', 'OpenAQ Plot', 'Plot OpenAQ observations')
        self.DashBoard.addObject('nmtools:MERRA_WindRose', 'MERRA_WindRose', 'Wind rose for a location (MERRA2)')
        self.DashBoard.addObject('nmtools:MerraAQSpatial', 'Merra Spatial', 'Plot MERRA2 aerosol spatial maps')
        self.DashBoard.addObject('nmtools:MerraAQTseries', 'Merra Series', 'Plot MERRA2 aerosol time series')
        self.DashBoard.addObject('workbooks:ColabWorkbooks', 'Colab Workbooks', 'Browse and preview packaged / local notebooks ("workbooks")')
        self.DashBoard.addObject('gibstools:NasaGibsViewer', 'NASA GIBS Imagery', 'Plot NASA GIBS imagery')

    def show(self):
        self.DashBoard.displayCP()
