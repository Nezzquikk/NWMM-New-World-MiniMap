#!/usr/bin/env python3 
# -*- coding: utf-8 -*- Python 3.8.8
#----------------------------------------------------------------------------
# Created By  : Nezzquikk
# Created Date: 2021/10/13
# version ='1.1.0'
# ---------------------------------------------------------------------------
""" This is an interactive MiniMap that is reading player position with
    PyTesseract OCR and visualizing it on a New World Map with live marker """ 
# ---------------------------------------------------------------------------
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore          import *
from rich.console import Console
from PyQt5.QtGui        import *
from PyQt5.QtWidgets import *
from rich.panel import Panel
from pynput import keyboard
from win32 import win32gui
from ctypes import windll
from rich import print
from PIL import Image
import numpy as np
import pytesseract
import pyautogui
import requests
import win32ui
import time
import sys
import cv2
import re
import os
# ---------------------------------------------------------------------------
try:
    os.chdir(sys._MEIPASS)
except:
    pass
console = Console()
COMPILED_VERSION = [False, "v1.1.0"]
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DISPLAY_SIZE = [windll.user32.GetSystemMetrics(0),windll.user32.GetSystemMetrics(1)]
SIZE_OF_MINIMAP = (250,250)

""" PyQT5 is blocking main thread for rendering GUI thus using QThread and QWorker
    for processing OCR and player positioning """
class MyGetPosThread(QThread):
    positionSign  = pyqtSignal(str)
    def __init__(self, parent):
        QThread.__init__(self, parent)

    def addPositionEventListener(self, listener):
        self.positionSign.connect(listener)

    def on_press(self, key):
        self.positionSign.emit(str(key))

    def run(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(object)
    lastCoordinate = [0,0]

    def run(self):
        def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
            image = np.array(image)
            blurred = cv2.GaussianBlur(image, kernel_size, sigma)
            sharpened = float(amount + 1) * image - float(amount) * blurred
            sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
            sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
            sharpened = sharpened.round().astype(np.uint8)
            if threshold > 0:
                low_contrast_mask = np.absolute(image - blurred) < threshold
                np.copyto(sharpened, image, where=low_contrast_mask)
            return sharpened

        def isMenuOpened(self):
            image = np.load("resources/ingameMenu.npy")
            return(True if pyautogui.locateCenterOnScreen(image, confidence=0.7, region=(0,0, DISPLAY_SIZE[0] - (DISPLAY_SIZE[0]-300), DISPLAY_SIZE[1]), grayscale=True) != None else False)
            
        try:
            versionNumber = requests.get("https://api.github.com/repos/Nezzquikk/NWMM-New-World-MiniMap/releases/latest").json()['name']
            if(versionNumber <= COMPILED_VERSION[1]):
                print(Panel(f"[bold green]YOUR VERSION IS UP-TO-DATE\nHAVE FUN[/bold green]"))
            else:
                print(Panel(f"[bold red]YOUR VERSION IS NOT UP-TO-DATE\nPLEASE UPDATE\n[/bold red][bold blue]Visit https://api.github.com/repos/Nezzquikk/NWMM-New-World-MiniMap/releases/latest[/bold blue]"))
        except:
            pass
        
        while True:
            hwnd = win32gui.FindWindow(None, 'New World')
            if hwnd == 0:
                try:
                    print("Window not found!")
                    return
                finally:
                    pass
            left, top, right, bot = win32gui.GetWindowRect(hwnd)
            w = right - left
            h = bot - top
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
            saveDC.SelectObject(saveBitMap)
            windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            w, h = im.size
            screenshot = im.crop((DISPLAY_SIZE[0] - 268, 19, DISPLAY_SIZE[0], 35))
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            screenshot = np.array(screenshot) 
            screenshot = cv2.inRange(np.array(screenshot), np.array([100, 100, 100]), np.array([255, 255, 255]))
            screenshot = unsharp_mask(screenshot)
            # cv2.imwrite('image.png', screenshot)
            playerLocation = pytesseract.image_to_string(screenshot,  config='-c tessedit_char_whitelist=[].,0123456789')
            try:
                playerLocation = re.findall(r'\[(\d{1,5})[,.]{1,2}\d{1,3}[,.]{1,2}(\d{1,5})[,.]', playerLocation) 
                if int(playerLocation[0][0]) < 4300 or int(playerLocation[0][0]) > 14200 or int(playerLocation[0][1]) < -100 or int(playerLocation[0][1]) > 10000:
                    raise InterruptedError("INTERCEPTED OUT OF MAP JUMP")
                print(Panel(f"[bold]Position detected:[/bold] [bold green] {playerLocation} [/bold green]"))
                time.sleep(0.3)
                self.lastCoordinate = playerLocation[0]
                self.progress.emit({"location":playerLocation[0], "isMenuOpened": isMenuOpened(im)})
            except InterruptedError as e:
                print(Panel(f"[bold red]{e}!"))
            except Exception as e:
                print(Panel(f"[bold red]Position not found!: {playerLocation}"))
                time.sleep(0.1)
                self.progress.emit({"location":self.lastCoordinate, "isMenuOpened": isMenuOpened(im)})


class MapBorder(QWidget):
    def __init__(self):
        super(MapBorder, self).__init__()
        self.Map = MainWindow()
        self.Map.show()
        self.im = QPixmap("resources/border.png")
        self.im = self.im.scaledToWidth(350)
        self.label = QLabel()
        self.label.setPixmap(self.im)
        self.grid = QGridLayout()
        self.initButtons()
        self.grid.addWidget(self.label,0,0)
        self.setLayout(self.grid)
        self.setGeometry(0,0,0,0)
        self.setMouseTracking(True)
        self.invisible()
        self.zoomInButton.raise_()
        self.zoomOutButton.raise_()
        self.openFilterButton.raise_()
        self.autoFollowButton.raise_()
        self.offset = None
        self.installEventFilter(self)
        self.setMouseTracking(True)
        self.setStyleSheet("""
        QPushButton{
            border-radius:30px;
        }
        QPushButton:hover{
            margin: 4px 2px;
        }
        
        """)
        self.show()
    def numpyQImage(self, image):
        qImg = QImage()
        if image.dtype == np.uint8:
            if len(image.shape) == 2:
                channels = 1
                height, width = image.shape
                bytesPerLine = channels * width
                qImg = QImage(
                    image.data, width, height, bytesPerLine, QImage.Format_Indexed8
                )
                qImg.setColorTable([qRgb(i, i, i) for i in range(255)])
            elif len(image.shape) == 3:
                if image.shape[2] == 3:
                    height, width, channels = image.shape
                    bytesPerLine = channels * width
                    qImg = QImage(
                        image.data, width, height, bytesPerLine, QImage.Format_RGB888
                    )
                elif image.shape[2] == 4:
                    height, width, channels = image.shape
                    bytesPerLine = channels * width
                    qImg = QImage(
                        image.data, width, height, bytesPerLine, QImage.Format_ARGB32
                    )
        return qImg

    def initButtons(self):
            self.zoomInButton = QPushButton('-', self)
            self.zoomInButton.setObjectName("zoomIn")
            self.zoomInButton.move(217,23)
            self.zoomInButton.setIconSize(QSize(27,27))
            self.zoomInButton.setIcon(QIcon('resources/zoomIn.png'))
            self.zoomOutButton = QPushButton('-', self)
            self.zoomOutButton.setObjectName("zoomOut")
            self.zoomOutButton.move(272,93)
            self.zoomOutButton.setIconSize(QSize(27,27))
            self.zoomOutButton.setIcon(QIcon('resources/zoomOut.png'))
            self.openFilterButton = QPushButton(self)
            self.openFilterButton.setObjectName("filter")
            self.openFilterButton.move(250,53)
            self.openFilterButton.setIconSize(QSize(30,30))
            self.openFilterButton.setIcon(QIcon('resources/filter.png'))
            # self.openFilterButton.setIconSize(QSize(40,24))
            self.autoFollowButton = QPushButton(self)
            self.autoFollowButton.setObjectName("follow")
            self.autoFollowButton.move(35,240)
            self.autoFollowButton.setIconSize(QSize(25,25))
            self.autoFollowButton.setIcon(QIcon('resources/position.png'))
            self.zoomInButton.clicked.connect(lambda: self.zoomIntoMap(True))
            self.zoomOutButton.clicked.connect(lambda: self.zoomIntoMap(False))
            self.openFilterButton.clicked.connect(lambda: self.openFilterMenu())
            self.autoFollowButton.clicked.connect(lambda: self.Map.toggleAutoFollow())
            
            
    @pyqtSlot()
    def zoomIntoMap(self, isAdded):
        self.Map.webview.page().runJavaScript("""
        document.getElementById('map').__vue__.mapObject.setZoom(document.getElementById('map').__vue__.mapObject.getZoom()%s1)
        """ % ("+" if isAdded==True else "-"))

    @pyqtSlot()
    def openFilterMenu(self):
        self.Map.webview.page().runJavaScript("""
        document.querySelector("#main > div.v-application--wrap > header > div > button.v-app-bar__nav-icon.v-btn.v-btn--icon.v-btn--round.theme--dark.v-size--default").click();
        document.querySelector("#main > div.v-application--wrap > aside > div.v-navigation-drawer__content > div > div.__panel.__hidebar > div > div:nth-child(3) > button > span > i").remove();
        """)

    def invisible(self):
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoChildEventsForParent, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint|Qt.WindowStaysOnTopHint)
        self.raise_()
        self.show()
    

    def moveEvent(self, event):
        super(MapBorder, self).moveEvent(event)
        diff = event.pos() - event.oldPos()
        self.Map.move(event.pos().x()+60, event.pos().y()+5)
        geo = self.Map.geometry()
        geo.moveTopLeft(geo.topLeft() + diff)
        self.Map.setGeometry(geo)

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress:
            self.offset = event.pos()
        elif event.type() == QEvent.MouseMove and self.offset is not None:
            self.move(self.pos() - self.offset + event.pos())
            return True
        elif event.type() == QEvent.MouseButtonRelease:
            self.offset = None
        return super().eventFilter(source, event)

    
class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.move(300,500)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("NWMM")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.defaultFlags = self.windowFlags()
        self.AUTO_FOLLOW_ON = False
        self.ISCIRCULAR = True
        self.HAS_USER_FIXED_WINDOW = False
        self.IS_WINDOW_FIXED = False
        self.currentZoom = 2
        self.initUI()
        """ Tesseract Path """
        pytesseract.pytesseract.tesseract_cmd = "Tesseract-OCR\\tesseract.exe" if COMPILED_VERSION[0] == True else TESSERACT_PATH
        """ if you want executable (Tesseract required in folder) use pyInstaller"""
        # pyinstaller -F --add-data "Tesseract-OCR;Tesseract-OCR" MiniMap.py --add-data "resources;resources" || "Tesseract-OCR\\tesseract.exe" 
        self.webview = QWebEngineView()
        self.webview.setContextMenuPolicy(Qt.PreventContextMenu)
        webpage = WebEnginePage(self.webview)
        self.useragent = QWebEngineProfile(self.webview)
        self.useragent.defaultProfile().setHttpUserAgent("Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko; googleweblight) Chrome/38.0.1025.166 Mobile Safari/535.19")
        self.webview.setPage(webpage)
        self.webview.setUrl(QUrl("https://www.newworld-map.com/#/"))
        self.setCentralWidget(self.webview)
        self.webview.loadFinished.connect(self.onLoadFinished)
        self.latestCoordinate = [0,0]
        self._get_pos_thread = MyGetPosThread(self)
        self._get_pos_thread.addPositionEventListener(self.onPosEvent)
        self._get_pos_thread.start()
        self.setMouseTracking(True)
        self.loop()
        self.toggleViewMode()
        self.webview.focusProxy().installEventFilter(self)
        

    def eventFilter(self, obj, event):
        MapBorderUI.raise_()
        if obj is self.webview.focusProxy() and event.type() == event.MouseButtonPress:
            pass
        return super(MainWindow, self).eventFilter(obj, event)

   
    def onPosEvent(self, pos):
        if pos == "Key.delete":
            self.HAS_USER_FIXED_WINDOW = True
            self.disableInterfaceUseability()
        elif pos == "Key.insert":
            self.HAS_USER_FIXED_WINDOW = False
            self.enableInterfaceUseability()

    def disableInterfaceUseability(self):
        if self.IS_WINDOW_FIXED == False:
            self.IS_WINDOW_FIXED = True
            print(Panel(f"[bold yellow]Disabled Interface[/bold yellow]"))
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.setAttribute(Qt.WA_NoChildEventsForParent, True)
            self.setWindowFlags(Qt.X11BypassWindowManagerHint|Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            MapBorderUI.setAttribute(Qt.WA_NoSystemBackground, True)
            MapBorderUI.setAttribute(Qt.WA_TranslucentBackground, True)
            MapBorderUI.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            MapBorderUI.setAttribute(Qt.WA_NoChildEventsForParent, True)
            MapBorderUI.setWindowFlags(Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint|Qt.WindowStaysOnTopHint)
            MapBorderUI.raise_()
            MapBorderUI.show()
            self.show()


    def enableInterfaceUseability(self):
        if self.IS_WINDOW_FIXED == True:
            self.IS_WINDOW_FIXED = False
            print(Panel(f"[bold yellow]Enabled Interface[/bold yellow]"))
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.setAttribute(Qt.WA_NoChildEventsForParent, False)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setWindowFlags(self.defaultFlags)
            MapBorderUI.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            MapBorderUI.setAttribute(Qt.WA_NoChildEventsForParent, False)
            MapBorderUI.setWindowFlags(Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint|Qt.WindowStaysOnTopHint)
            MapBorderUI.raise_()
            MapBorderUI.show()
            self.show()
        
    
    def initUI(self, isWindowFramed=True):
        radius = 200.0
        self.painterPath = QPainterPath()
        self.resize(*SIZE_OF_MINIMAP) # size of MiniMap
        if isWindowFramed == False:
            self.painterPath.addRoundedRect(QRectF(self.rect()), radius, radius)
        mask = QRegion(self.painterPath.toFillPolygon().toPolygon())
        self.setMask(mask)

        


    """ DEPRECATED - DEACTIVATED FOR NOW """    
    def toggleViewMode(self):
        self.ISCIRCULAR = not self.ISCIRCULAR
        if self.ISCIRCULAR == True:
            print(Panel(f"[bold yellow]Changed to Circular[/bold yellow]"))
            self.initUI(isWindowFramed=False)
        else:
            print(Panel(f"[bold yellow]Changed to Circular[/bold yellow]"))
            self.initUI(isWindowFramed=False)
        self.show()
        
    """ DEPRECATED - DEACTIVATED FOR NOW """    
    def toggleWindowFrame(self):
        self.ISFRAMED = not self.ISFRAMED
        if self.ISFRAMED == True:
            print(Panel(f"[bold yellow]Enabled Window Frame[/bold yellow]"))
            self.initUI(isWindowFramed=True)
        else:
            print(Panel(f"[bold yellow]Disabled Window Frame[/bold yellow]"))
            self.initUI(isWindowFramed=False)
        
        self.show()
        
    """ DEPRECATED - DEACTIVATED FOR NOW """    
    def toggleStayOnTop(self):
        self.STAYONTOP = not self.STAYONTOP
        if self.STAYONTOP == True:
            print(Panel(f"[bold yellow]Enabled Stay on Top[/bold yellow]"))
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            print(Panel(f"[bold yellow]Disabled Stay on Top[/bold yellow]"))
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        

    def toggleAutoFollow(self):
        
        if self.AUTO_FOLLOW_ON == True:
            print(Panel(f"[bold yellow]Disabled auto-follow[/bold yellow]"))
        else:
            print(Panel(f"[bold yellow]Enabled auto-follow[/bold yellow]"))
        self.AUTO_FOLLOW_ON = not self.AUTO_FOLLOW_ON
        self.webview.page().runJavaScript("""
        document.querySelector("#main > div.v-application--wrap > div.v-snack.v-snack--has-background.v-snack--top > div").style="";
        document.querySelector("#main > div.v-application--wrap > div.v-snack.v-snack--has-background.v-snack--top > div > div.v-snack__content").style="margin-left:25%%;"
        document.querySelector("#main > div.v-application--wrap > div.v-snack.v-snack--has-background.v-snack--top > div > div.v-snack__content").innerHTML = "Auto-Follow %s!";
        setTimeout(()=> {
        document.querySelector("#main > div.v-application--wrap > div.v-snack.v-snack--has-background.v-snack--top > div").style="display:none";
        },1500)
        """ % ("turned ON" if self.AUTO_FOLLOW_ON == True else "turned OFF"))


    def onLoadFinished(self):
        """ Remove unnessecary stuff from Map """
        self.webview.page().runJavaScript("""
        document.querySelector("#main > div.v-application--wrap > header").style = "visibility:hidden;"
        document.querySelector("#main > div.v-application--wrap > header > div").style="height: 56px;margin-left: 40%;"
        document.querySelector("body").style="overflow: hidden;"
        document.querySelector("#nn_player").remove()
        document.querySelector("#main > div.v-application--wrap > footer").remove()
        document.querySelector("#main > div.v-application--wrap > header > div > button:nth-child(4)").remove()
        document.querySelector("#main > div.v-application--wrap > main").style = "padding: 0px 0px 0px";
        var style = document.createElement("style");style.innerHTML = 'body::-webkit-scrollbar {display: none;}';document.head.appendChild(style);
        document.querySelector("#main > div.v-application--wrap > aside").style = "margin-left:7%";
        setTimeout(() => {window.mapX=document.getElementById("map").__vue__.mapObject;window.markerX = window.L.marker({lat: 0, lng: 0});window.markerX.addTo(window.mapX);},1500);
        var x1 = setInterval(function() {
            if (document.querySelector("#main > div.v-menu__content.theme--light.menuable__content__active") !== null) {
                document.querySelector("#main > div.v-application--wrap > header").class = "height: 56px; margin-top: 0px; transform: translateY(0px); left: 0px; right: 0px; background-color: rgba(0, 0, 0, 0.0);"
                document.querySelector("#main > div.v-menu__content.theme--light.menuable__content__active").style = "max-height: 95%; min-width: 350px; top: 19px; left: 0px; transform-origin: left top; z-index: 9";
                document.querySelector("#menu_resources > div:nth-child(1) > div").remove()
                document.querySelector("#menu_resources > div:nth-child(3) > div").remove()
                document.querySelector("#menu_resources > div:nth-child(3)").style = "margin-left:25%;"
                clearInterval(x1)
            }
        }, 200);
        """)


    def loop(self):
        self.playerLocation = []
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.processThread)
        self.thread.start()


    def processThread(self, imageObjects):
        position = imageObjects['location']
        isMenuOpened = imageObjects['isMenuOpened']
        self.setMarker(position)
        if isMenuOpened == True and self.HAS_USER_FIXED_WINDOW == True:
            if self.IS_WINDOW_FIXED == True:
                self.enableInterfaceUseability()
        elif isMenuOpened == False and self.HAS_USER_FIXED_WINDOW == True:
            self.disableInterfaceUseability()
    

    def follow_marker(self, location):
        if self.AUTO_FOLLOW_ON == True:
            x,y = location
            #document.querySelector("#map > div.leaflet-pane.leaflet-map-pane > div.leaflet-pane.leaflet-marker-pane > img.leaflet-marker-icon.leaflet-zoom-animated.leaflet-interactive").src = "https://cdn-icons-png.flaticon.com/512/463/463714.png"
            self.webview.page().runJavaScript("""
            window.mapX.panTo({lat: %s-14336, lng: %s});
            
            """ % (y,x))
    

    def setMarker(self, location):
        x,y = location
        self.webview.page().runJavaScript("""window.markerX.setLatLng({lat: %s-14336, lng: %s});""" % (y,x))
        self.follow_marker(location)
        self.latestCoordinate = [x, y]
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    MapBorderUI = MapBorder()
    MapBorderUI.show()
    sys.exit(app.exec_())         
