from __future__ import annotations

def main() -> None:
    msg = '\nGeoRAD is an ipywidgets/Jupyter dashboard.\n\nQuick start (inside a Jupyter Notebook/Lab cell):\n\n    from georad import AQDashBoard\n    AQDashBoard().show()\n\nTo diagnose your environment, you can run:\n\n    python -m georad.diagnostics\n\n\n'.strip()
    print(msg)
if __name__ == '__main__':
    main()
