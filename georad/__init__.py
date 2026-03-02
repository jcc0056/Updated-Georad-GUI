from __future__ import annotations
__all__ = ['__version__', 'AQDashBoard', 'RADashBoard', 'OpenAQGui', 'QueryOpenAq', 'PlotOpenAq', 'PanelObject', 'NasaGibsViewer', 'MERRA_WindRose', 'MerraAQSpatial', 'MerraAQTseries', 'ColabWorkbooks']
__version__ = '0.0.5'

def __getattr__(name: str):
    if name in {'AQDashBoard', 'RADashBoard'}:
        from radboard import AQDashBoard, RADashBoard
        return {'AQDashBoard': AQDashBoard, 'RADashBoard': RADashBoard}[name]
    if name == 'OpenAQGui':
        from openaqgui import OpenAQGui
        return OpenAQGui
    if name in {'QueryOpenAq', 'PlotOpenAq'}:
        from oaqtools import PlotOpenAq, QueryOpenAq
        return {'QueryOpenAq': QueryOpenAq, 'PlotOpenAq': PlotOpenAq}[name]
    if name == 'PanelObject':
        from panelobj import PanelObject
        return PanelObject
    if name == 'NasaGibsViewer':
        from gibstools import NasaGibsViewer
        return NasaGibsViewer
    if name in {'MERRA_WindRose', 'MerraAQSpatial', 'MerraAQTseries'}:
        from nmtools import MERRA_WindRose, MerraAQSpatial, MerraAQTseries
        return {'MERRA_WindRose': MERRA_WindRose, 'MerraAQSpatial': MerraAQSpatial, 'MerraAQTseries': MerraAQTseries}[name]
    if name == 'ColabWorkbooks':
        from workbooks import ColabWorkbooks
        return ColabWorkbooks
    raise AttributeError(f"module 'georad' has no attribute {name!r}")
