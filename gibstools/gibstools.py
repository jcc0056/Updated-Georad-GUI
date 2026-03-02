import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
from IPython.display import display
from ipywidgets import HBox, VBox, Button, Layout, HTML, Output, Dropdown, GridBox, Textarea, Text, Password
from ipywidgets import DatePicker, FloatSlider, IntProgress, Label, Output
import cartopy.crs as ccrs
from panelobj import PanelObject

class NasaGibsViewer(PanelObject):

    def __init__(self, ptype='time', *args, **kwargs):
        self.title = 'NASA GIBS Image Viewer'
        PanelObject.__init__(self, *args, **kwargs)
        self.url = 'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi'
        self.plat = 24.42
        self.plon = 54.43
        self.height = 1.0
        self.width = 1.0

    def getCP(self):
        self.setLabel()
        self.imgDate = datetime.now()
        self.selectVar = 'MODIS_Terra_SurfaceReflectance_Bands143'
        self.dateSW = DatePicker(description='Date', layout=Layout(width='220px'), value=self.imgDate, disabled=False)
        self.vardict = {'TerraRGB': 'MODIS_Terra_SurfaceReflectance_Bands143', 'AquaRGB': 'MODIS_Aqua_SurfaceReflectance_Bands143', 'AquaLST Day': 'MODIS_Aqua_Land_Surface_Temp_Day'}
        self.varSW = Dropdown(options=['TerraRGB', 'AquaRGB', 'AquaLST Day'], value='TerraRGB', layout=Layout(width='220px'), description='Var:', disabled=False)
        self.latSW = Text(description='Lat:', disabled=False, value='24.42', layout=Layout(width='220px'))
        self.lonSW = Text(description='Lon:', disabled=False, value='54.43', layout=Layout(width='220px'))
        self.plotPB = Button(description='Plot', disabled=False, layout={'width': 'auto', 'border': '3px outset'})
        self.latRS = FloatSlider(value=5, min=2.0, max=15, step=0.2, description='Width', disabled=False, continuous_update=False, orientation='horizontal', readout=True, readout_format='.1f')
        self.lonRS = FloatSlider(value=5.0, min=2.0, max=15.0, step=0.2, description='Height:', disabled=False, continuous_update=False, orientation='horizontal', readout=True, readout_format='.1f')
        self.inpUSR.children += (HBox([VBox([self.plotPB]), VBox([self.dateSW, self.latSW, self.lonSW]), VBox([self.latRS, self.lonRS, self.varSW])], layout={'overflow': 'visible'}),)
        self.dateSW.observe(self.dateSWCB)
        self.varSW.observe(self.varSWCB, names='value')
        self.latSW.observe(self.latSWCB, names='value')
        self.lonSW.observe(self.lonSWCB, names='value')
        self.latRS.observe(self.latRSCB, names='value')
        self.lonRS.observe(self.lonRSCB, names='value')
        self.plotPB.on_click(self.plotGIBS)
        return self.cp

    def dateSWCB(self, change):
        if change['type'] == 'change':
            self.imgDate = self.dateSW.value

    def varSWCB(self, b):
        self.selectVar = self.vardict[self.varSW.value]

    def latSWCB(self, change):
        self.plat = float(self.latSW.value)

    def lonSWCB(self, change):
        self.plon = float(self.lonSW.value)

    def latRSCB(self, change):
        self.height = self.latRS.value * 0.5

    def lonRSCB(self, change):
        self.width = self.lonRS.value * 0.5

    def plotGIBS(self, b):
        self.lat1 = self.plat - self.height
        self.lat2 = self.plat + self.height
        self.lon1 = self.plon - self.width
        self.lon2 = self.plon + self.width
        with self.out_cp:
            plt.ioff()
            layer = self.selectVar
            date_str = '{}-{}-{}'.format(self.imgDate.strftime('%Y'), self.imgDate.strftime('%m'), self.imgDate.strftime('%d'))
            print(layer, date_str)
            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            ax.add_wmts(self.url, layer, wmts_kwargs={'time': date_str})
            self.out_cp.clear_output()
            ax.set_extent([self.lon1, self.lon2, self.lat1, self.lat2], crs=ccrs.PlateCarree())
            ax.coastlines(resolution='50m', color='yellow')
            plt.plot(self.plon, self.plat, marker='o', color='red', markersize=15, alpha=1.0)
            plt.show()
