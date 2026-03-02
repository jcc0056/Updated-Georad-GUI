# GeoRAD

GeoRAD is a collection of ipywidgets-based panels that can be combined into dashboards for air-quality and Earth-observation workflows.

The repo installs these Python packages:

- `georad`
- `panelobj`
- `openaqgui`
- `oaqtools`
- `nmtools`
- `gibstools`
- `radboard`
- `workbooks`

`import georad` is the main entry point.

## Install from GitHub

```bash
pip install git+https://github.com/<your-username>/<your-repo>.git
```

In Google Colab, use:

```python
!pip install git+https://github.com/<your-username>/<your-repo>.git
```

The repository name does not need to match the import name. After installation, import it as:

```python
from georad import AQDashBoard
AQDashBoard().show()
```

If you want the optional MERRA, GIBS, and Voila dependencies too, install the `full` option:

```bash
pip install "georad[full] @ git+https://github.com/<your-username>/<your-repo>.git"
```

## Local install

```bash
pip install -e .
```


To check your environment after install:

```bash
python -m georad.diagnostics
```

You can also use the console entry point:

```bash
georad-diagnostics
```

If OpenAQ panels need authentication, set `OPENAQ_API_KEY` in your environment or provide it in the widget.
