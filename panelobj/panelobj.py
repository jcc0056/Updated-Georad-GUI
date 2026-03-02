from ipywidgets import HBox, VBox, Button, Layout, HTML, Output, GridspecLayout, Dropdown, GridBox, Textarea, Text, Password

class PanelObject:

    def __init__(self, *args, **kwargs):
        if hasattr(self, 'title') == False:
            self.title = 'Panel Object'
        self.topLabel = HTML(disabled=True, layout=Layout(width='auto', grid_area='title'))
        self.setLabel()
        self.rule = HTML(disabled=True, layout=Layout(width='auto', grid_area='rule', flex_flow='column'))
        self.rule.value = '<div >' + '<hr></div>'
        self.spacer = HTML(disabled=True, layout=Layout(width='auto', grid_area='rule', flex_flow='column'))
        self.out_cp = Output(layout=Layout(width='auto', grid_area='output', overflow='visible', flex_flow='column'))
        self.inpUSR = HBox([], layout={'width': 'auto', 'overflow': 'visible', 'height': '100px'})
        self.objOUT = HBox([VBox([self.out_cp])], layout={'width': 'auto', 'overflow': 'visible', 'grid_area': 'output'})
        self.objLabel = HBox([self.topLabel], layout={'overflow': 'visible', 'width': 'auto', 'justify_content': 'center', 'flex_flow': 'column', 'align_item': 'stretch'})
        self.cp = VBox([self.objLabel, self.inpUSR, self.rule, self.spacer, self.objOUT], layout={'width': 'auto', 'overflow': 'visible', 'flex_flow': 'column'})
        self.pwdDict = {}

    def setLabel(self):
        self.topLabel.value = '<div style="background-color: #C0C0C0 ;' + 'padding: 1em 0em 0em 0em; border-bottom-style:solid;border-width:1px">' + '<b><center><h3>' + self.title + '</h3></center></b></div>'
