from __future__ import annotations
import os
import platform
import sys
from importlib import import_module

def _try_import(name: str):
    try:
        mod = import_module(name)
        ver = getattr(mod, '__version__', None)
        return (True, ver)
    except Exception as e:
        return (False, str(e))

def main() -> None:
    print('GeoRAD diagnostics')
    print('------------')
    print(f'Python: {sys.version.split()[0]} ({platform.platform()})')
    print(f"OPENAQ_API_KEY set: {('YES' if bool(os.environ.get('OPENAQ_API_KEY')) else 'NO')}")
    deps = ['IPython', 'ipywidgets', 'pandas', 'matplotlib', 'seaborn', 'openaq', 'pydap', 'netCDF4', 'cartopy', 'windrose', 'nbformat', 'nbconvert', 'voila']
    print('\nDependencies:')
    for d in deps:
        ok, info = _try_import(d)
        if ok:
            print(f'  {d}' + (f' (version {info})' if info else ''))
        else:
            print(f' (error)   {d} ({info})')
    print('\nTip:')
    print('  - If OpenAQ panels fail, set OPENAQ_API_KEY or use the API key box at the top of the OpenAQ panels.')
if __name__ == '__main__':
    main()
