# SkyDataViewer

A tool to view sky photos with corresponding multispectral radiance measurements side-by-side. Additionally, it can be used to export and convert datasets of sky samples inteaded to be used for machine learning.

The original viewer was [clearskydataviewer](https://github.com/ProgramofComputerGraphics/clearskydataviewer), written by [Dan Knowlton](https://github.com/knowlonix) for the [Program Of Computer Graphics at Cornell](http://www.graphics.cornell.edu). Parts of his sky coordinate to UV angle calculations are retained in [`utility_angles.py`](blob/master/utility_angles.py).

### Prerequisites

The software developed in Python on a Windows box and intended to be cross-platform.  
Python modules required (version used):  
Python    (3.5.2)  
PyQt5     (5.11.2)  
pandas    (0.21.0)  
numpy     (1.14.2)  
pyqtgraph (0.10.0)  
Pillow    (5.2.0)  

### Instructions

Run the application.  
Select a data directory (which must have data organized in a specific way).  
Use the combobox dropdowns and sliders to select the capture date and exposure desired.  
Click and drag to select sampling pattern coordinates.  
View corresponding radiance measurements below.  

Right-click (mouse-secondary) on canvas for more selection and HUD options.  

To export, first run `Setup Export File` to specify parameters. Exports after that will be appended to the same file.  

### Controls

| control                | usage                                   |
|:-----------------------|:----------------------------------------|
| mouse-wheel            | moves the capture time slider           |
| mouse-primary-drag     | selects sampling pattern coordinates    |
| mouse-secondary        | context menu                            |
| mouse-wheel-click-hold | rotates sky photo                       |
| ctrl+selection         | adds to currently selected samples      |
| shift+selection        | removes from currently selected samples |
| ctrl+A                 | selects all samples                     |
| ctrl+I                 | selects inverse                         |

### Notes

Your Data Directory must be organized in a very specific way for the photos and radiance values to be correlated.  
[Here are real sky photos with radiance measurments organized and ready to use](https://spectralskylight.github.io/RadianceEstimationData)

Context menu -> `Graph Resolution` can be used to optimize plotting of radiance curves.  
1 = every wavelength, 2 = every other wavelength, etc.  
Adjusting this can significantly improve performance of the application.  

`Pixel Region` and `Pixel Weighting` refers to the pixel kernel used determine the final pixel color viewed and exported.  
The color can be seen in the bottom-right of the canvas.  

`res/settings.json` - Is a settings file generated on execution and contains default and saved settings as you use the application, which can be edited by hand. There is a menu option in Help which can be toggled to prevent overwriting of settings.

`res/dsetfix.py` - Is a script for searching/operating on exported sample datasets.
`res/ddirfix.py` - Is a script for cleaning/organizing a data directory with corresponding sky photos and radiance measurements.
