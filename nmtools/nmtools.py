from pydap.client import open_url
from pydap.cas.urs import setup_session
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from ipywidgets import Button, Output
from datetime import datetime, timedelta, date
from dateutil import rrule
import ipywidgets as widgets
from IPython.display import display
from ipywidgets import HBox, VBox, Button, Layout, HTML, Output, GridspecLayout, Dropdown, GridBox, Textarea, Text, Password
from ipywidgets import DatePicker, FloatSlider, IntProgress, Label
import seaborn as sns
from windrose import WindroseAxes
from calendar import monthrange
from datetime import datetime, timedelta, date
import pandas as pd
import cartopy.crs as ccrs
from panelobj import PanelObject

class MERRA_WindRose(PanelObject):

    def __init__(self, *args, **kwargs):
        self.title = 'MERRA2 Wind Rose'
        self.accList = ['NASA Earth Data']
        PanelObject.__init__(self, *args, **kwargs)
        self.windms = []
        self.windkt = []
        self.winddir = []
        self.times = []
        self.latv = 24.42
        self.lonv = 54.43
        self.start_date = datetime(2020, 4, 20)
        self.end_date = datetime(2020, 4, 30)

    def getCP(self):
        self.setLabel()
        self.usrTW = Text(value='', placeholder='', description='Username:', disabled=False)
        self.usrTW.observe(self.username, names='values')
        self.pwdPW = Password(value='', placeholder='', description='Password:', disabled=False)
        self.pwdPW.observe(self.password, names='value')
        self.st = widgets.DatePicker(description='Start Date', value=datetime(2020, 4, 20), disabled=False, layout=Layout(width='220px'))
        self.et = widgets.DatePicker(description='End Date', value=datetime(2020, 4, 30), disabled=False, layout=Layout(width='220px'))
        self.st.observe(self.startDate)
        self.et.observe(self.endDate)
        self.latitude = Text(value='24.42', description='Latitude:', disabled=False, layout=Layout(width='220px'))
        self.longitude = Text(value='54.43', description='Longitude:', disabled=False, layout=Layout(width='220px'))
        self.latitude.observe(self.set_lat_val, names='value')
        self.longitude.observe(self.set_lon_val, names='value')
        self.plotms = Button(description='Plot in m/s', disabled=False, layout={'width': 'auto', 'border': '3px outset'})
        self.plotms.on_click(self.plotWindRose_ms)
        self.plotkt = Button(description='Plot in kt', disabled=False, layout={'width': 'auto', 'border': '3px outset'})
        self.plotkt.on_click(self.plotWindRose_kt)
        self.inpUSR.children += (HBox([VBox([self.st, self.latitude, self.longitude]), VBox([self.et, self.plotms, self.plotkt])], layout={'overflow': 'visible'}),)
        return self.cp

    def username(self, t):
        username = t.value

    def password(self, t):
        password = self.pwdPW.value

    def startDate(self, date):
        self.start_date = datetime(self.st.value.year, self.st.value.month, self.st.value.day)
        return self.start_date

    def endDate(self, date):
        self.end_date = datetime(self.et.value.year, self.et.value.month, self.et.value.day)
        return self.end_date

    def lonlatToIndex(self, plon, plat):
        self.ilat = int(np.interp(plat, (self.lat.data.min(), self.lat.data.max()), (0, self.lat.shape[0] - 1)))
        self.ilon = int(np.interp(plon, (self.lon.data.min(), self.lon.data.max()), (0, self.lon.shape[0] - 1)))

    def get_data(self):
        url1 = 'https://goldsmr4.gesdisc.eosdis.nasa.gov:443/opendap/MERRA2/M2I1NXASM.5.12.4/'
        url2 = '/MERRA2_'
        url3 = '.inst1_2d_asm_Nx.'
        zero = '0'
        slash = '/'
        nc = '.nc4'
        for dt in rrule.rrule(rrule.DAILY, dtstart=self.start_date, until=self.end_date):
            #print('Getting data for',dt)
            self.times.append(dt)
            if dt.year >= 2011:
                val = 400
            if dt.year < 2011 and dt.year >= 2001:
                val = 300
            if dt.year < 2001 and dt.year >= 1992:
                val = 200
            if dt.year < 1992:
                val = 100
            if dt.month > 9 and dt.day < 10:
                opendap_url = url1 + str(dt.year) + slash + str(dt.month) + url2 + str(val) + url3 + str(dt.year) + str(dt.month) + zero + str(dt.day) + nc
            if dt.month > 9 and dt.day >= 10:
                opendap_url = url1 + str(dt.year) + slash + str(dt.month) + url2 + str(val) + url3 + str(dt.year) + str(dt.month) + str(dt.day) + nc
            if dt.month < 10 and dt.day < 10:
                opendap_url = url1 + str(dt.year) + slash + zero + str(dt.month) + url2 + str(val) + url3 + str(dt.year) + zero + str(dt.month) + zero + str(dt.day) + nc
            if dt.month < 10 and dt.day >= 10:
                opendap_url = url1 + str(dt.year) + slash + zero + str(dt.month) + url2 + str(val) + url3 + str(dt.year) + zero + str(dt.month) + str(dt.day) + nc
            username = self.pwdDict['NASA Earth Data']['user']
            password = self.pwdDict['NASA Earth Data']['password']
            session = setup_session(username, password, check_url=opendap_url)
            dataset = open_url(opendap_url, session=session)
            self.lon = dataset['lon'][:]
            self.lat = dataset['lat'][:]
            self.time = dataset['time'][:]
            self.uwind = np.squeeze(dataset['U10M'][:, :, :])
            self.vwind = np.squeeze(dataset['V10M'][:, :, :])
            self.lons, self.lats = np.meshgrid(self.lon, self.lat)
            self.lonlatToIndex(self.lonv, self.latv)
            uwind = self.uwind[:, self.ilat, self.ilon].mean()
            vwind = self.vwind[:, self.ilat, self.ilon].mean()
            wind_speed = np.sqrt(uwind ** 2 + vwind ** 2)
            self.windms.append(wind_speed)
            ws_to_kt = wind_speed * 0.514444
            self.windkt.append(ws_to_kt)
            wind_dir_trig_to = np.arctan2(uwind / wind_speed, vwind / wind_speed)
            wind_dir_trig_to_degrees = wind_dir_trig_to * (180 / np.pi)
            wind_dir = wind_dir_trig_to_degrees + 180
            self.winddir.append(wind_dir)

    def set_lat_val(self, value):
        self.latv = float(self.latitude.value)

    def set_lon_val(self, value):
        self.lonv = float(self.longitude.value)

    def plotWindRose_kt(self, b):
        plt.ioff()
        with self.out_cp:
            self.out_cp.clear_output()
            print('Getting data ...')
            self.get_data()
            print('Finished')
            fig = plt.figure(figsize=(10, 5))
            ax = WindroseAxes.from_ax()
            ax.bar(self.winddir, self.windkt, normed=True, opening=0.8, edgecolor='white')
            ax.set_legend()
            title = 'MERRA2 Wind Rose (kt) from ' + str(self.start_date) + ' to ' + str(self.end_date) + ' at Latitude ' + str(self.latitude.value) + ' and Longitude ' + str(self.longitude.value)
            ax.set_title(title)
            plt.show()

    def plotWindRose_ms(self, b):
        plt.ioff()
        
        with self.out_cp:
            self.out_cp.clear_output()
            print('Getting data ...')
            self.get_data()
            print('Finished')
            self.out_cp.clear_output()
            fig = plt.figure(figsize=(10, 5))
            ax = WindroseAxes.from_ax()
            ax.bar(self.winddir, self.windms, normed=True, opening=0.8, edgecolor='white')
            title = 'MERRA2 Wind Rose (m/s) from ' + str(self.start_date) + ' to ' + str(self.end_date) + ' at Latitude ' + str(self.latitude.value) + ' and Longitude ' + str(self.longitude.value)
            ax.set_title(title)
            ax.set_legend()
            plt.show()

class MerraAQSpatial(PanelObject):

    def __init__(self, ptype='space', *args, **kwargs):
        self.title = 'MERRA2 AQ Spatial Plots'
        PanelObject.__init__(self, *args, **kwargs)
        self.ptype = ptype

    def getCP(self):
        self.setLabel()
        self.plon = 0.0
        self.plat = 0.0
        self.dateSelection = datetime.now()
        self.dateSelection = datetime(2020, 4, 23)
        self.dateLast = datetime(1950, 1, 1)
        self.selectVar = 'AOD'
        self.selectTime = 0
        self.dateSW = DatePicker(description='Date', layout=Layout(width='250px'), value=self.dateSelection, disabled=False)
        self.myWidget1 = Dropdown(options=['AOD', 'DUST_PM', 'SALT_PM', 'ORG_CARB', 'BLK_CARB', 'SO4', 'PM2.5'], value='AOD', layout=Layout(width='250px'), description='Varibale:', disabled=False)
        self.myWidget2 = Dropdown(options=[], value=None, layout=Layout(width='250px'), description='Varibale:', disabled=False)
        self.myWidget3 = Dropdown(options=[], value=None, description='Date:', disabled=False)
        self.myWidget4 = Dropdown(options=[], value=None, layout=Layout(width='250px'), description='Time:', disabled=False)
        self.latSW = FloatSlider(min=-90.0, max=90.0, step=0.25, description='Lat:', disabled=False, continuous_update=False, orientation='horizontal', readout=True, readout_format='.2f')
        self.lonSW = FloatSlider(min=-180.0, max=180.0, step=0.25, description='Lon:', disabled=False, continuous_update=False, orientation='horizontal', readout=True, readout_format='.2f')
        self.plotBW = Button(description='Spatial Plot', disabled=False, layout={'width': '200px', 'border': '3px outset'})
        if self.ptype == 'space':
            self.inpUSR.children += (HBox([VBox([self.dateSW, self.myWidget4, self.myWidget1]), VBox([self.plotBW])], layout={'overflow': 'visible'}),)
        else:
            self.inpUSR.children += (HBox([VBox([self.dateSW, self.myWidget1]), VBox([self.timeplot, self.latSW, self.lonSW])], layout={'overflow': 'visible'}),)
        self.year = np.arange(41) + 1980
        self.mm = np.arange(12) + 1
        
        # formatter = "{:02d}".format
        # self.months=[formatter(item) for item in mm]
        self.dateSW.observe(self.dateSWCB)
        self.myWidget2.options = self.mm
        self.myWidget1.observe(self.myCallback1, names='value')
        self.myWidget2.observe(self.myCallback2, names='value')
        self.date = np.arange(1, 30) + 1
        self.time = np.arange(24)
        self.myWidget3.options = self.date
        self.myWidget4.options = self.time
        self.myWidget3.observe(self.myCallback3, names='value')
        self.myWidget4.observe(self.myCallback4, names='value')
        self.latSW.observe(self.latSWCB, names='value')
        self.lonSW.observe(self.lonSWCB, names='value')
        self.plotBW.on_click(self.plotObs)
        return self.cp

    def dateSWCB(self, change):
        if change['type'] == 'change':
            self.dateSelection = self.dateSW.value

    def myCallback1(self, b):
        self.selectVar = self.myWidget1.value
        # print(self.selectYear)

    def myCallback2(self, b):
        formatter = '{:02d}'.format
        self.selectMonth = self.myWidget2.value
        self.selectMonth = formatter(self.selectMonth)
        
        # print(self.selectMonth)

    def myCallback3(self, b):
        formatter = '{:02d}'.format
        self.selectDate = formatter(self.myWidget3.value)

    def myCallback4(self, b):
        self.selectTime = self.myWidget4.value

    def latSWCB(self, change):
        self.plat = self.latSW.value

    def lonSWCB(self, change):
        self.plon = self.lonSW.value

    def plotObs(self, b):
        if self.dateSelection.year < 1992:
            self.Vnumber = '100'
        elif self.dateSelection.year < 2001:
            self.Vnumber = '200'
        elif self.dateSelection.year < 2011:
            self.Vnumber = '300'
        else:
            self.Vnumber = '400'
        self.selectYear = self.dateSelection.strftime('%Y')
        self.selectMonth = self.dateSelection.strftime('%m')
        self.selectDate = self.dateSelection.strftime('%d')
        if self.dateSelection != self.dateLast:
            username = self.pwdDict['NASA Earth Data']['user']
            password = self.pwdDict['NASA Earth Data']['password']
            with self.out_cp:
                print('Accessing data...')
            self.opendap_url = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2T1NXAER.5.12.4/' + self.selectYear + '/' + self.selectMonth + '/MERRA2_' + self.Vnumber + '.tavg1_2d_aer_Nx.' + self.selectYear + self.selectMonth + self.selectDate + '.nc4'
            session = setup_session(username, password, check_url=self.opendap_url)
            dataset = open_url(self.opendap_url, session=session)
            #dataset = open_url(opendap_url)
            lon = dataset['lon'][:]
            lat = dataset['lat'][:]
            self.lons, self.lats = np.meshgrid(lon, lat)
            t = int(self.selectTime)
            aod = np.squeeze(dataset['TOTEXTTAU'][t, :, :], axis=0)
            dust_pm = np.squeeze(dataset['DUSMASS25'][t, :, :], axis=0) * 1000000000.0
            salt_pm = np.squeeze(dataset['SSSMASS25'][t, :, :], axis=0) * 1000000000.0
            org_carb = np.squeeze(dataset['OCSMASS'][t, :, :], axis=0) * 1000000000.0
            blk_carb = np.squeeze(dataset['BCSMASS'][t, :, :], axis=0) * 1000000000.0
            so4 = np.squeeze(dataset['SO4SMASS'][t, :, :], axis=0) * 1000000000.0
            pm25 = 1.375 * so4 + 1.6 * org_carb + blk_carb + dust_pm + salt_pm
            self.vardict = {'AOD': aod, 'DUST_PM': dust_pm, 'SALT_PM': salt_pm, 'ORG_CARB': org_carb, 'BLK_CARB': blk_carb, 'SO4': so4, 'PM2.5': pm25}
        self.varlab = {'AOD': 'Unitless', 'DUST_PM': '$\\mu g m^{-3}$', 'SALT_PM': '$\\mu g m^{-3}$', 'ORG_CARB': '$\\mu g m^{-3}$', 'BLK_CARB': '$\\mu g m^{-3}$', 'SO4': '$\\mu g m^{-3}$', 'PM2.5': '$\\mu g m^{-3}$'}
        var = self.vardict[self.selectVar]
        
        # Set the figure size, projection, and extent
        with self.out_cp:
            plt.ioff()
            self.out_cp.clear_output()
            fig = plt.figure(figsize=(8, 4))
            ax = plt.axes(projection=ccrs.PlateCarree())
            ax.set_global()
            #ax.set_extent([65, 100, 5.0,35.0])
            ax.coastlines(resolution='110m', linewidth=1)
            ax.gridlines(linestyle='--', color='black')
            # Set contour levels, then draw the plot and a colorbar
            clevs = np.arange(230, 311, 5)
            plt.contourf(self.lons, self.lats, var, transform=ccrs.PlateCarree(), cmap=plt.cm.jet)
            formatter = '{:02d}'.format
            tt = formatter(self.selectTime)
            plt.title('MERRA2 ' + self.selectVar + ',' + tt + ':00 UTC ' + self.selectYear + '-' + self.selectMonth + '-' + self.selectDate, size=14)
            cb = plt.colorbar(ax=ax, orientation='vertical', pad=0.02, aspect=16, shrink=0.8)
            cb.set_label(self.varlab[self.selectVar], size=12, rotation=90, labelpad=15)
            cb.ax.tick_params(labelsize=10)
            plt.show()
            self.dateLast = self.dateSelection

class MerraAQTseries(PanelObject):

    def __init__(self, ptype='time', *args, **kwargs):
        self.title = 'MERRA2 AQ Time Series'
        self.stateChange = True
        self.init = True
        self.progVal = -1
        self.progMax = 1
        PanelObject.__init__(self, *args, **kwargs)
        self.ptype = ptype
        self.baseURL = 'https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2/M2T1NXAER.5.12.4'
        self.lat = 24.42
        self.lon = 54.43
        self.endDate = datetime.now()
        self.startDate = self.endDate - timedelta(days=1)
        self.endDate = datetime(2020, 4, 30)
        self.startDate = datetime(2020, 4, 20)
        self.varlab = {'AOD': 'AOD (Unitless)', 'DUST_PM': 'Dust PM$_{2.5}(\\mu g m^{-3})$', 'SALT_PM': 'Salt PM$_{2.5}(\\mu g m^{-3})$', 'ORG_CARB': 'Org Carbon PM$_{2.5} (\\mu g m^{-3})$', 'BLK_CARB': 'Black Carbon PM$_{2.5}(\\mu g m^{-3})$', 'SO4': 'SO$_4 PM_{2.5} (\\mu g m^{-3})$', 'PM2.5': 'Total PM$_{2.5}(\\mu g m^{-3})$'}

    def initSession(self):
        username = self.pwdDict['NASA Earth Data']['user']
        password = self.pwdDict['NASA Earth Data']['password']
        self.session = setup_session(username, password, check_url=self.baseURL)
        firstDay = datetime(1980, 1, 1)
        dataset = open_url(self.getUrlMERRA(firstDay), session=self.session)
        self.lon = dataset['lon'][:]
        self.lat = dataset['lat'][:]

    def getCP(self):
        self.setLabel()
        self.plon = 54.43
        self.plat = 24.42
        self.dateSelection = datetime.now()
        self.dateLast = datetime(1950, 1, 1)
        self.selectVar = 'AOD'
        self.selectTime = 0
        self.sdateSW = DatePicker(description='Start Date', layout=Layout(width='auto'), value=self.startDate, disabled=False)
        self.edateSW = DatePicker(description='End Date', layout=Layout(width='auto'), value=self.endDate, disabled=False)
        self.varSW = Dropdown(options=['AOD', 'DUST_PM', 'SALT_PM', 'ORG_CARB', 'BLK_CARB', 'SO4', 'PM2.5'], value='AOD', layout=Layout(width='280px'), description='Variable:', disabled=False)
        self.latSW = Text(description='Latitude:', disabled=False, value='24.42', layout=Layout(width='180px'))
        self.lonSW = Text(description='Longitude:', disabled=False, value='54.43', layout=Layout(width='180px'))
        self.plotPB = Button(description='Time Series Plot', disabled=False, layout={'width': 'auto', 'border': '3px outset'})
        self.inpUSR.children += (HBox([VBox([self.sdateSW, self.edateSW, self.varSW]), VBox([self.latSW, self.lonSW, self.plotPB])], layout={'overflow': 'visible'}),)
        self.sdateSW.observe(self.sdateSWCB)
        self.edateSW.observe(self.edateSWCB)
        self.varSW.observe(self.varSWCB, names='value')
        self.latSW.observe(self.latSWCB, names='value')
        self.lonSW.observe(self.lonSWCB, names='value')
        self.plotPB.on_click(self.plotTS)
        return self.cp

    def sdateSWCB(self, change):
        if change['type'] == 'change':
            self.startDate = self.sdateSW.value
            self.stateChange = True

    def edateSWCB(self, change):
        if change['type'] == 'change':
            self.endDate = self.edateSW.value
            self.stateChange = True

    def varSWCB(self, b):
        self.selectVar = self.varSW.value

    def latSWCB(self, change):
        self.plat = float(self.latSW.value)
        self.stateChange = True

    def lonSWCB(self, change):
        self.plon = float(self.lonSW.value)
        self.stateChange = True

    def lonlatToIndex(self, plon, plat):
        self.ilat = int(np.interp(plat, (self.lat.data.min(), self.lat.data.max()), (0, self.lat.shape[0] - 1)))
        self.ilon = int(np.interp(plon, (self.lon.data.min(), self.lon.data.max()), (0, self.lon.shape[0] - 1)))

    def updateProg(self, prog):
        while self.progVal < self.progMax:
            if self.progVal != prog.value:
                prog.value = self.progVal

    def getTS(self, startDate, endDate):
        ndays = (endDate - startDate).days + 1
        if self.init:
            ndays += 1
        currentDate = startDate
        delta = timedelta(days=1)
        self.df = pd.DataFrame(columns=['datetime', 'AOD', 'DUST_PM', 'SALT_PM', 'ORG_CARB', 'BLK_CARB', 'SO4', 'PM2.5'])
        with self.out_cp:
            self.out_cp.clear_output()
            pbar = IntProgress(min=0, max=int(ndays))
            pbar.description = 'Progress:'
            info1 = Label('0%')
            info2 = Label(' ')
            display(VBox([HBox([pbar, info1]), HBox([info2], layout=Layout(justify_content='center'))]))
            progVal = 0
            if self.init:
                info2.value = 'Initializing NASA Earth Data Connection..'
                self.initSession()
                self.init = False
                pbar.value += 1
                progVal += 1
                info1.value = '{:.1f}%'.format(float(progVal) / float(ndays) * 100.0)
            self.lonlatToIndex(self.plon, self.plat)
            while currentDate <= endDate:
                url = self.getUrlMERRA(currentDate)
                info2.value = 'Accessing data for {}'.format(currentDate)
                dataset = open_url(url, session=self.session)
                aod = np.squeeze(dataset['TOTEXTTAU'][:, self.ilat, self.ilon])
                dust_pm = np.squeeze(dataset['DUSMASS25'][:, self.ilat, self.ilon]) * 1000000000.0
                salt_pm = np.squeeze(dataset['SSSMASS25'][:, self.ilat, self.ilon]) * 1000000000.0
                org_carb = np.squeeze(dataset['OCSMASS'][:, self.ilat, self.ilon]) * 1000000000.0
                blk_carb = np.squeeze(dataset['BCSMASS'][:, self.ilat, self.ilon]) * 1000000000.0
                so4 = np.squeeze(dataset['SO4SMASS'][:, self.ilat, self.ilon]) * 1000000000.0
                pm25 = 1.375 * so4 + 1.6 * org_carb + blk_carb + dust_pm + salt_pm
                dt = pd.date_range(currentDate, periods=24, freq='H')
                vardict = {'datetime': dt, 'AOD': aod, 'DUST_PM': dust_pm, 'SALT_PM': salt_pm, 'ORG_CARB': org_carb, 'BLK_CARB': blk_carb, 'SO4': so4, 'PM2.5': pm25}
                df_add = pd.DataFrame(vardict)
                self.df = pd.concat([self.df, df_add])
                currentDate += delta
                progVal += 1
                info1.value = '{:.1f}%'.format(float(progVal) / float(ndays) * 100.0)
                pbar.value += 1
        self.stateChange = False

    def plotTS(self, b):
        if self.stateChange:
            self.getTS(self.startDate, self.endDate)
        with self.out_cp:
            plt.ioff()
            fig, ax = plt.subplots(1, figsize=(12, 6))
            ax = self.df.plot(ax=ax, x='datetime', y=self.selectVar)
            ax.set_xlabel('Time (UTC)')
            ax.set_ylabel(self.varlab[self.selectVar])
            self.out_cp.clear_output()
            plt.show()

    def getUrlMERRA(self, dayObj):
        if dayObj.year < 1992:
            Vnumber = '100'
        elif dayObj.year < 2001:
            Vnumber = '200'
        elif dayObj.year < 2011:
            Vnumber = '300'
        else:
            Vnumber = '400'
        yy = dayObj.strftime('%Y')
        mm = dayObj.strftime('%m')
        dd = dayObj.strftime('%d')
        self.opendap_url = self.baseURL + '/{}/{}/MERRA2_{}.tavg1_2d_aer_Nx.{}{}{}.nc4'.format(yy, mm, Vnumber, yy, mm, dd)
        return self.opendap_url
