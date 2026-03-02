from __future__ import annotations
import os
import re
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from IPython.display import display
from ipywidgets import HBox, VBox, Button, Layout, HTML, Output, Dropdown, Text, Password
import pandas as pd
from panelobj import PanelObject
#from ..panelobj.panelobj import PanelObject

try:
    import openaq
except Exception:
    openaq = None

def _read_dotenv(key: str) -> Optional[str]:
    for candidate in ('.env', os.path.join(os.getcwd(), '.env')):
        try:
            if not os.path.exists(candidate):
                continue
            with open(candidate, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
        except Exception:
            continue
    return None

class OpenAQGui(PanelObject):

    def __init__(self, *args, **kwargs):
        self.title = 'OpenAQ GUI'
        super().__init__(*args, **kwargs)
        # initialize openaq api

        self.api: Any = None
        self._client_mode: str = 'unknown'
        self._ready: bool = False
        self.country: Optional[str] = None
        self.ccode: Optional[str] = None
        self.city: Optional[str] = None
        self.location: Optional[str] = None
        self.location_id: Optional[int] = None
        self.countries: pd.DataFrame = pd.DataFrame()
        self.cities: pd.DataFrame = pd.DataFrame()
        self.locations: pd.DataFrame = pd.DataFrame()
        self.apiKeyPW = Password(value='', placeholder='OpenAQ API key', description='API Key:', layout=Layout(width='520px'))
        self.setKeyBT = Button(description='Set Key', layout={'width': '120px', 'border': '3px outset'})
        self.statusHTML = HTML(value='', layout=Layout(width='auto'))
        self.setKeyBT.on_click(self._set_key_cb)
        self.inpUSR.children += (VBox([HBox([self.apiKeyPW, self.setKeyBT], layout={'gap': '8px', 'overflow': 'visible'}), self.statusHTML], layout={'overflow': 'visible'}),)
        self.createGuiElemenents()

    def getCP(self):
        return self.cp

    @staticmethod
    def _get_api_key() -> Optional[str]:
        return os.environ.get('OPENAQ_API_KEY') or os.environ.get('OPENAQ_APIKEY') or _read_dotenv('OPENAQ_API_KEY')

    def _init_client(self, api_key: Optional[str]) -> None:
        if openaq is None:
            raise ImportError("The 'openaq' package is not installed. Install with: pip install openaq")
        try:
            self.api = openaq.OpenAQ(api_key=api_key)
            self._client_mode = 'sdk'
            return
        except TypeError:
            pass
        self.api = openaq.OpenAQ()
        self._client_mode = 'legacy'

    def _set_status(self, html: str) -> None:
        self.statusHTML.value = f"<div style='font-size: 13px;'>{html}</div>"

    def _set_key_cb(self, b):
        key = (self.apiKeyPW.value or '').strip()
        if not key:
            self._set_status("<b style='color:#b00'>No key entered.</b>")
            return
        os.environ['OPENAQ_API_KEY'] = key
        self._set_status("<b style='color: #060'>API key set for this session.</b>")
        try:
            self._ready = False
            self._load_metadata()
        except Exception as e:
            self._set_status("<b style='color:#b00'>Failed to load OpenAQ metadata.</b><br>" + f'<pre>{traceback.format_exc()}</pre>')

    def _to_dataframe(self, res: Any) -> pd.DataFrame:
        if isinstance(res, pd.DataFrame):
            return res
        if isinstance(res, tuple) and len(res) >= 1:
            res = res[0]
        if hasattr(res, 'model_dump') and callable(getattr(res, 'model_dump')):
            try:
                res = res.model_dump()
            except Exception:
                pass
        elif hasattr(res, 'dict') and callable(getattr(res, 'dict')):
            try:
                res = res.dict()
            except Exception:
                pass
        if isinstance(res, dict):
            if 'results' in res:
                res = res['results']
            elif 'data' in res:
                res = res['data']
        if isinstance(res, list):
            out = []
            for item in res:
                if hasattr(item, 'model_dump') and callable(getattr(item, 'model_dump')):
                    out.append(item.model_dump())
                elif hasattr(item, 'dict') and callable(getattr(item, 'dict')):
                    out.append(item.dict())
                elif isinstance(item, dict):
                    out.append(item)
                else:
                    out.append(getattr(item, '__dict__', item))
            try:
                return pd.json_normalize(out)
            except Exception:
                return pd.DataFrame(out)
        if res is None:
            return pd.DataFrame()
        try:
            return pd.json_normalize(res)
        except Exception:
            try:
                return pd.DataFrame(res)
            except Exception:
                return pd.DataFrame()

    def _call(self, target: Any, df: bool=False, **kwargs):
        if callable(target):
            try:
                res = target(**kwargs)
            except TypeError:
                kw = dict(kwargs)
                kw.pop('df', None)
                res = target(**kw)
            return self._to_dataframe(res) if df else res
        raise TypeError('Target is not callable')

    def _call_api(self, endpoint_name: str, df: bool=False, **kwargs):
        ep = getattr(self.api, endpoint_name, None)
        if ep is None:
            raise AttributeError(f"OpenAQ client has no endpoint '{endpoint_name}'")
        if callable(ep):
            try:
                res = ep(df=df, **kwargs)
            except TypeError:
                res = ep(**kwargs)
            return self._to_dataframe(res) if df else res
        for meth in ('list', 'get', 'latest', 'sensors'):
            fn = getattr(ep, meth, None)
            if callable(fn):
                res = self._call(fn, df=df, **kwargs)
                return res
        raise TypeError(f"OpenAQ endpoint '{endpoint_name}' is not callable and has no known methods")

    def createGuiElements(self):
        return self.createGuiElemenents()

    def createGuiElemenents(self):
        # setup selection widgets

        self.countrySW = Dropdown(options=[], value=None, description='Country:', layout=Layout(width='260px'), disabled=False)
        self.citySW = Dropdown(options=[], value=None, description='City:', layout=Layout(width='260px'), disabled=False)
        self.locationSW = Dropdown(options=[], value=None, description='Location:', layout=Layout(width='520px'), disabled=False)
        self.filterTW = Text(value='', placeholder='Optional: filter locations by text', description='Filter:', layout=Layout(width='520px'))
        self.inpUSR.children += (VBox([self.countrySW, self.citySW, self.filterTW, self.locationSW], layout={'overflow': 'visible'}),)
        # set up  callback functions for the selection widgets

        self.countrySW.observe(self.countrySWCB, names='value')
        self.citySW.observe(self.citySWCB, names='value')
        self.locationSW.observe(self.locationSWCB, names='value')
        self.filterTW.observe(self._filter_cb, names='value')
        self._load_metadata()

    def _load_metadata(self) -> None:
        key = self._get_api_key()
        if not key:
            self._set_status("<b style='color:#b00'>OpenAQ API key not set.</b> Enter it above (recommended) or set environment variable <code>OPENAQ_API_KEY</code>.")
            self._disable_selection(True)
            return
        try:
            self._init_client(key)
        except Exception as e:
            self._set_status(f"<b style='color:#b00'>Failed to initialize OpenAQ client:</b><br><pre>{traceback.format_exc()}</pre>")
            self._disable_selection(True)
            return
        try:
            self._disable_selection(False)
            self._set_status('OpenAQ client ready.')
            self._load_countries()
            self._ready = True
        except Exception:
            self._set_status(f"<b style='color:#b00'>Failed to load OpenAQ metadata.</b><br><pre>{traceback.format_exc()}</pre>")
            self._disable_selection(True)
            self._ready = False

    def _disable_selection(self, disabled: bool) -> None:
        for w in (getattr(self, 'countrySW', None), getattr(self, 'citySW', None), getattr(self, 'locationSW', None), getattr(self, 'filterTW', None)):
            if w is not None:
                w.disabled = disabled

    def _load_countries(self) -> None:
        # get the list of countries. Set the default country selection 
        # to be the first country on the list and extract the corresponding 
        # country code

        df = self._call_api('countries', df=True, limit=1000)
        if 'code' not in df.columns and 'country' in df.columns:
            df = df.rename(columns={'country': 'code'})
        if 'name' not in df.columns and 'code' in df.columns:
            df['name'] = df['code']
        self.countries = df[[c for c in df.columns if c in ('id', 'code', 'name')]]
        names = list(self.countries['name'].dropna().astype(str))
        self.countrySW.options = names
        self.countrySW.value = names[0] if names else None
        if self.countrySW.value:
            self.countrySWCB({'type': 'change'})

    def updateCities(self):
        # get the list of cities for the country selected and set the 
        # default city selection to be the first city on the list

        if not self.ccode:
            self.cities = pd.DataFrame()
            self.citySW.options = []
            self.citySW.value = None
            return
        if self._client_mode == 'legacy':
            df = self._call_api('cities', df=True, country=self.ccode, limit=1000)
            if 'city' not in df.columns and 'name' in df.columns:
                df['city'] = df['name']
            if 'name' not in df.columns and 'city' in df.columns:
                df['name'] = df['city']
            self.cities = df
        else:
            loc = self._call_api('locations', df=True, iso=self.ccode, limit=1000)
            if 'locality' not in loc.columns:
                for cand in ('city', 'locality.name', 'localityName'):
                    if cand in loc.columns:
                        loc = loc.rename(columns={cand: 'locality'})
                        break
            loc['locality'] = loc.get('locality', pd.Series([None] * len(loc))).fillna('(unknown)').astype(str)
            cities = sorted(set(loc['locality'].tolist()))
            self.cities = pd.DataFrame({'name': cities, 'city': cities})
            self._country_locations = loc
        opts = list(self.cities['name'].dropna().astype(str)) if not self.cities.empty else []
        self.citySW.options = opts
        self.citySW.value = opts[0] if opts else None

    def updateLocations(self):
        # get the list of locations for the city selected and set the 
        # default location selection to be the first location on the list

        if not self.ccode:
            self.locations = pd.DataFrame()
            self.locationSW.options = []
            self.locationSW.value = None
            return
        if self._client_mode == 'legacy':
            if not self.city:
                self.locations = pd.DataFrame()
                self.locationSW.options = []
                self.locationSW.value = None
                return
            df = self._call_api('locations', df=True, city=self.city, limit=1000)
            if 'location' not in df.columns and 'name' in df.columns:
                df = df.rename(columns={'name': 'location'})
            self.locations = df
            options = list(self.locations['location'].dropna().astype(str))
            self.locationSW.options = options
            self.locationSW.value = options[0] if options else None
            self.location_id = None
            self.location = self.locationSW.value
            return
        loc = getattr(self, '_country_locations', None)
        if loc is None or not isinstance(loc, pd.DataFrame):
            loc = self._call_api('locations', df=True, iso=self.ccode, limit=1000)
        if 'name' in loc.columns and 'location' not in loc.columns:
            loc = loc.rename(columns={'name': 'location'})
        if 'locality' not in loc.columns:
            loc['locality'] = '(unknown)'
        if 'id' not in loc.columns:
            loc['id'] = None
        if self.city:
            loc_filtered = loc.loc[loc['locality'].fillna('(unknown)').astype(str) == str(self.city)]
        else:
            loc_filtered = loc
        self.locations = loc_filtered
        filt = (self.filterTW.value or '').strip().lower()
        if filt:
            self.locations = self.locations.loc[self.locations['location'].fillna('').astype(str).str.lower().str.contains(filt)]
        opts: List[Tuple[str, Any]] = []
        for _, row in self.locations.head(1000).iterrows():
            name = str(row.get('location', ''))
            lid = row.get('id')
            label = f'{name} (id:{lid})' if pd.notna(lid) else name
            opts.append((label, int(lid) if pd.notna(lid) else name))
        self.locationSW.options = opts
        self.locationSW.value = opts[0][1] if opts else None
        self._sync_location_state()
            #self.showQuery()

    def _sync_location_state(self):
        v = self.locationSW.value
        self.location_id = int(v) if isinstance(v, int) else None
        if self.location_id is not None and (not self.locations.empty) and ('id' in self.locations.columns):
            try:
                row = self.locations.loc[self.locations['id'] == self.location_id].iloc[0]
                self.location = str(row.get('location', ''))
            except Exception:
                self.location = None
        else:
            self.location = str(v) if v is not None else None

    def _filter_cb(self, change):
        if change.get('type') == 'change':
            # get list of locations and set the default location as the first location
            # on the list

            self.updateLocations()

    def countrySWCB(self, change):
        if change.get('type') == 'change' and self.countrySW.value:
            # set the country to the new user selected value given 
            # by the "value" attribute in the country selection widget.

            self.country = self.countrySW.value
            try:
                self.ccode = self.countries.loc[self.countries['name'] == self.country, 'code'].values[0]
            except Exception:
                self.ccode = None
            # get list of cities and set the default city as the first city
            # on the list

            self.updateCities()
            self.city = self.citySW.value
            # get list of locations and set the default location as the first location
            # on the list

            self.updateLocations()

    def citySWCB(self, change):
        if change.get('type') == 'change':
            # set the city to the new user selected value given 
            # by the "value" attribute in the city selection widget.

            self.city = self.citySW.value
            self.updateLocations()

    def locationSWCB(self, change):
        if change.get('type') == 'change':
            # set the location to the new user selected value given 
            # by the "value" attribute in the location selection widget.

            self._sync_location_state()

    def execQuery(self):
        try:
            if self.locations.empty:
                raise ValueError('No locations loaded')
            if self.location_id is not None and 'id' in self.locations.columns:
                row = self.locations.loc[self.locations['id'] == self.location_id]
            else:
                row = self.locations.loc[self.locations.get('location') == self.location]
            df = row.T
            with self.out_cp:
                self.out_cp.clear_output()
                display(df)
        except Exception:
            with self.out_cp:
                self.out_cp.clear_output()
                display(HTML(f'<pre>{traceback.format_exc()}</pre>'))
