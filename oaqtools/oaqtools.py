from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
import traceback
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display
from ipywidgets import Button, HBox, Layout, Text, VBox
from openaqgui import OpenAQGui
#from ..openaqgui.openaqgui import OpenAQGui


class QueryOpenAq(OpenAQGui):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def getCP(self):
        self.title = 'Query OpenAQ Database'
        self.setLabel()
        self.showInfo = Button(description='Query', disabled=False, layout={'width': '120px', 'border': '3px outset'})
        self.showInfo.on_click(self.showQuery)
        self.inpUSR.children += (HBox([self.showInfo], layout={'gap': '8px'}),)
        return self.cp

    def showQuery(self, b):
        self.execQuery()

class PlotOpenAq(OpenAQGui):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def getCP(self):
        self.title = 'Time Series Plots of OpenAQ Observations'
        self.setLabel()
        self.paramTW = Text(value='pm25', placeholder='e.g. pm25, no2, o3', description='Parameter:', layout=Layout(width='260px'))
        self.daysTW = Text(value='14', description='Days:', layout=Layout(width='160px'))
        self.plotStn = Button(description='Plot', disabled=False, layout={'width': '120px', 'border': '3px outset'})
        self.plotStn.on_click(self.plotObs)
        self.inpUSR.children += (VBox([HBox([self.paramTW, self.daysTW, self.plotStn], layout={'gap': '8px'})], layout={'overflow': 'visible'}),)
        return self.cp

    def _plot_dataframe(self, df: pd.DataFrame, time_col: str, value_col: str, label: str):
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df = df.dropna(subset=[time_col])
        df = df.sort_values(time_col)
        df = df.set_index(time_col)
        with self.out_cp:
            self.out_cp.clear_output()
            plt.ioff()
            fig, ax = plt.subplots(1, figsize=(12, 6))
            sns.set(style='ticks', font_scale=1.2)
            # Convert from ppm to ppb
            # Plot the data
            df[value_col].plot(ax=ax, label=label)
            ax.legend(loc='best')
            ax.set_ylabel(value_col)
            ax.set_xlabel('')
            # move the legend to the side
            #plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
            sns.despine(offset=5)
            #display(fig)
            plt.show()

    def plotObs(self, b):
        param = (self.paramTW.value or 'pm25').strip().lower()
        try:
            days = int((self.daysTW.value or '14').strip())
        except Exception:
            days = 14
        if not getattr(self, '_ready', False):
            with self.out_cp:
                self.out_cp.clear_output()
                display('OpenAQ client not ready. Please set API key above.')
            return False
        if getattr(self, '_client_mode', 'unknown') == 'legacy':
            try:
                res = self._call_api('measurements', df=True, location=self.location, parameter=param, limit=10000)
                time_col = None
                for cand in ('date.utc', 'date.local', 'date', 'datetime'):
                    if cand in res.columns:
                        time_col = cand
                        break
                if time_col is None:
                    if isinstance(res.index, pd.DatetimeIndex):
                        res = res.reset_index().rename(columns={'index': 'datetime'})
                        time_col = 'datetime'
                    else:
                        raise ValueError('Could not find a datetime column in legacy measurements response.')
                value_col = 'value' if 'value' in res.columns else res.columns[-1]
                label = str(self.location or 'location')
                self._plot_dataframe(res, time_col, value_col, label)
                return True
            except Exception:
                with self.out_cp:
                    self.out_cp.clear_output()
                    display(f'Failed to fetch/plot legacy measurements.\n{traceback.format_exc()}')
                return False
        loc_id: Optional[int] = getattr(self, 'location_id', None)
        if loc_id is None:
            with self.out_cp:
                self.out_cp.clear_output()
                display('Select a location with an id (OpenAQ SDK mode). Try filtering and re-selecting.')
            return False
        try:
            sensors_res = self.api.locations.sensors(loc_id)
            sdf = self._to_dataframe(sensors_res)
        except Exception as e:
            with self.out_cp:
                self.out_cp.clear_output()
                display(f'Failed to retrieve sensors for location {loc_id}: {e}')
            return False
        if sdf.empty:
            with self.out_cp:
                self.out_cp.clear_output()
                display('No sensors returned for this location.')
            return False
        sensor_id = None
        param_cols = [c for c in sdf.columns if 'parameter' in c.lower() and 'name' in c.lower()]
        if param_cols:
            col = param_cols[0]
            try:
                match = sdf.loc[sdf[col].astype(str).str.lower() == param]
                if not match.empty and 'id' in match.columns:
                    sensor_id = int(match.iloc[0]['id'])
            except Exception:
                pass
        if sensor_id is None and 'id' in sdf.columns:
            try:
                sensor_id = int(sdf.iloc[0]['id'])
            except Exception:
                sensor_id = None
        if sensor_id is None:
            with self.out_cp:
                self.out_cp.clear_output()
                display('Could not determine a sensor id for this location.')
            return False
        dt_to = datetime.utcnow()
        dt_from = dt_to - timedelta(days=days)
        try:
            mdf = self._call_api('measurements', df=True, sensors_id=sensor_id, datetime_from=dt_from.strftime('%Y-%m-%d'), datetime_to=dt_to.strftime('%Y-%m-%d'), limit=1000)
        except Exception as e:
            with self.out_cp:
                self.out_cp.clear_output()
                display(f'Failed to retrieve measurements for sensor {sensor_id}: {e}')
            return False
        if mdf.empty:
            with self.out_cp:
                self.out_cp.clear_output()
                display('No measurements returned.')
            return False
        time_col = None
        for cand in ('period.datetime_from.utc', 'period.datetime_from.local', 'period.datetime_from', 'datetime.utc', 'datetime.local', 'datetime', 'date.utc', 'date.local', 'date'):
            if cand in mdf.columns:
                time_col = cand
                break
        if time_col is None:
            with self.out_cp:
                self.out_cp.clear_output()
                display('Could not find a datetime column. Columns were:')
                display(mdf.columns)
            return False
        value_col = 'value' if 'value' in mdf.columns else None
        if value_col is None:
            for cand in ('summary.median', 'summary.mean', 'summary.max', 'summary.min'):
                if cand in mdf.columns:
                    value_col = cand
                    break
        if value_col is None:
            with self.out_cp:
                self.out_cp.clear_output()
                display('Could not find a value column in measurements.')
                display(mdf.head())
            return False
        label = f"{self.location or 'location'} ({param})"
        self._plot_dataframe(mdf, time_col, value_col, label)
        return True
