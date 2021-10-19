# NWMM-New-World-MiniMap

# Features:
* Automatically grabs position from "New World" Instance
* Live visualisation of player position on MiniMap
* Circular MiniMap with Borders & working Buttons
* Stay-On-Top making the Map look like an Overlay!
* Automatically detects opened ingame menu for disabling overlaying
* Informative and structured debugging console
* Auto-version Checker upon startup
* Configurable
* Auto-Follow (credits to @seler)
* Resizeable
* Cross-Platform (untested)

# How to use:
1. Install Pytesseract on your system<br>
`pip install pytesseract`<br>
`https://github.com/UB-Mannheim/tesseract/wiki`
3. Install Script requirements<br>
`pip install -r requirements.txt`
4. Edit Pytesseract path in MiniMap.py
5. Start & Log into Game
6. Enable "Show FPS" in Settings -> Visuals
8. Run Script
9. Place the Map where you want it to be
10. Have Fun!

Note:
I have implemented an overlaying-mode so you don't loose anymore focus to the Map Window.
Press "Delete"-Key on your Keyboard to activate overlaying-mode
Press "Insert"-Key on your Keyboard to manually deactive overlaying-mode
On default: Automatic toggling of Overlaying-mode when pressing "ESC" (Ingame Menu)

# Bugs
* Bad OCR in daylight

INFO: It may be possible that one or the other library I use in this project (like PyWin32) is not compatible with newest version of Python
I recommend using Python 3.8 (I myself use Python 3.8.8)
Please downgrade or use the compiled executable version of this MiniMap.

# OCR-Optimization
A few filters applied ontop of the image crop to achieve better daylight OCR results<br>
Original<br>
![image](https://user-images.githubusercontent.com/62097381/137309863-f96e4095-3d73-4ed6-9d79-19bbfc5d43fc.png)<br>
filter applied::<br>
![image](https://user-images.githubusercontent.com/62097381/137309633-51ea348c-e078-4d71-92b3-bd05ca5928fe.png)
# Showcase




https://user-images.githubusercontent.com/62097381/137976408-4b29911c-b928-4a27-bd18-88d82eebfce7.mp4





# Credits
* Auto-Follow (credits to @seler)
* Map provided by StudioLoot (@https://studioloot.com/ / @https://www.newworld-map.com/#/)
