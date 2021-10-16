#!/usr/bin/env python3 
# -*- coding: utf-8 -*- Python 3.8.8
#----------------------------------------------------------------------------
# Created By  : Nezzquikk
# Created Date: 2021/10/13
# version ='1.0.0'
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
import requests
import win32ui
import time
import sys
import cv2
import re
# ---------------------------------------------------------------------------
console = Console()
RELEASE_VERSION = [False, "v1.0.0"]
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
        versionNumber = requests.get("https://api.github.com/repos/Nezzquikk/NWMM-New-World-MiniMap/releases/latest").json()['name']
        if(versionNumber <= RELEASE_VERSION[1]):
            print(Panel(f"[bold green]YOUR VERSION IS UP-TO-DATE\nHAVE FUN[/bold green]"))
        else:
            print(Panel(f"[bold red]YOUR VERSION IS NOT UP-TO-DATE\nPLEASE UPDATE\n[/bold red][bold blue]Visit https://api.github.com/repos/Nezzquikk/NWMM-New-World-MiniMap/releases/latest[/bold blue]"))
        while True:
            def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
                blurred = cv2.GaussianBlur(image, kernel_size, sigma)
                sharpened = float(amount + 1) * image - float(amount) * blurred
                sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
                sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
                sharpened = sharpened.round().astype(np.uint8)
                if threshold > 0:
                    low_contrast_mask = np.absolute(image - blurred) < threshold
                    np.copyto(sharpened, image, where=low_contrast_mask)
                return sharpened


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
                time.sleep(0.1)
                self.lastCoordinate = playerLocation[0]
                self.progress.emit(playerLocation[0])
            except InterruptedError as e:
                print("yy")
                print(Panel(f"[bold red]{e}!"))
            except Exception as e:
                print(Panel(f"[bold red]Position not found!: {playerLocation}"))
                time.sleep(0.1)
                self.progress.emit(self.lastCoordinate)
            

class WebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("NWMM")
        self.defaultFlags = self.windowFlags()
        self.AUTO_FOLLOW_ON = True
        self.ISCIRCULAR = False
        self.STAYONTOP = True
        self.ISFRAMED = True
        self.initUI()
        """ Tesseract Path """
        pytesseract.pytesseract.tesseract_cmd = "Tesseract-OCR\\tesseract.exe" if RELEASE_VERSION[0] == True else TESSERACT_PATH
        """ if you want executable (Tesseract required in folder) use pyInstaller"""
        # pyinstaller -F --add-data "Tesseract-OCR;Tesseract-OCR" MiniMap.py || "Tesseract-OCR\\tesseract.exe" 
        self.webview = QWebEngineView()
        webpage = WebEnginePage(self.webview)
        self.useragent = QWebEngineProfile(self.webview)
        self.useragent.defaultProfile().setHttpUserAgent("Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko; googleweblight) Chrome/38.0.1025.166 Mobile Safari/535.19")
        self.webview.setPage(webpage)
        self.webview.setUrl(QUrl("https://www.newworld-map.com/#/"))
        self.setCentralWidget(self.webview)
        # self.setCentralWidget(self.webview)
        self.webview.loadFinished.connect(self.onLoadFinished)
        self.latestCoordinate = [0,0]
        self.webview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.webview.customContextMenuRequested.connect(self.on_context_menu)
        self.initContextMenu()
        # self.disableInterfaceUseability()
        self._get_pos_thread = MyGetPosThread(self)
        self._get_pos_thread.addPositionEventListener(self.onPosEvent)
        self._get_pos_thread.start()

   
    def onPosEvent(self, pos):
        if pos == "Key.delete":
            self.disableInterfaceUseability()
        elif pos == "Key.insert":
            self.enableInterfaceUseability()
            

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        pass
    

    def disableInterfaceUseability(self):
        print(Panel(f"[bold yellow]Disabled Interface[/bold yellow]"))
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoChildEventsForParent, True)
        self.setWindowFlags(Qt.X11BypassWindowManagerHint|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.show()


    def enableInterfaceUseability(self):
        print(Panel(f"[bold yellow]Enabled Interface[/bold yellow]"))
        self.setWindowFlags(self.defaultFlags)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_NoChildEventsForParent, False)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.show()
        
    
    def initUI(self, isWindowFramed=True):
        radius = 200.0 if self.ISCIRCULAR == True else 0.0
        self.painterPath = QPainterPath()
        self.resize(*SIZE_OF_MINIMAP) # size of MiniMap
        if isWindowFramed == False:
            self.painterPath.addRoundedRect(QRectF(self.rect()), radius, radius)
        mask = QRegion(self.painterPath.toFillPolygon().toPolygon())
        self.setMask(mask)


    def initContextMenu(self):
        self.popMenu = QMenu(self)
        self.toggle_follow_button = QAction("Disable auto-follow")
        self.toggle_viewmode_button = QAction("Change to Circular")
        self.toggle_WindowFrame_button = QAction("Disable Window Frame")
        self.toggle_stayOnTop_button = QAction("Disable Stay on Top")
        self.popMenu.addAction(self.toggle_follow_button)
        self.popMenu.addAction(self.toggle_stayOnTop_button)
        self.popMenu.addAction(self.toggle_viewmode_button)
        self.popMenu.addAction(self.toggle_WindowFrame_button)
        self.toggle_follow_button.triggered.connect(self.toggleAutoFollow)
        self.toggle_viewmode_button.triggered.connect(self.toggleViewMode)
        self.toggle_stayOnTop_button.triggered.connect(self.toggleStayOnTop)
        self.toggle_WindowFrame_button.triggered.connect(self.toggleWindowFrame)
        

    def on_context_menu(self, point):
        self.popMenu.exec_(self.webview.mapToGlobal(point))


    def toggleViewMode(self):
        self.ISCIRCULAR = not self.ISCIRCULAR
        if self.ISCIRCULAR == True:
            print(Panel(f"[bold yellow]Changed to Circular[/bold yellow]"))
            self.initUI(isWindowFramed=False)
            self.toggle_viewmode_button.setText('Change to Rectangle') 
        else:
            print(Panel(f"[bold yellow]Changed to Rectangle[/bold yellow]"))
            self.initUI(isWindowFramed=False)
            self.toggle_viewmode_button.setText('Change to Circular')
        self.show()
        

    def toggleWindowFrame(self):
        self.ISFRAMED = not self.ISFRAMED
        if self.ISFRAMED == True:
            print(Panel(f"[bold yellow]Enabled Window Frame[/bold yellow]"))
            self.toggle_WindowFrame_button.setText('Disable Window Frame') 
            self.initUI(isWindowFramed=True)
        else:
            print(Panel(f"[bold yellow]Disabled Window Frame[/bold yellow]"))
            self.toggle_WindowFrame_button.setText('Enable Window Frame') 
            self.initUI(isWindowFramed=False)
        
        self.show()
        
        
    def toggleStayOnTop(self):
        self.STAYONTOP = not self.STAYONTOP
        if self.STAYONTOP == True:
            print(Panel(f"[bold yellow]Enabled Stay on Top[/bold yellow]"))
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.toggle_stayOnTop_button.setText('Disable Stay on Top') 
        else:
            print(Panel(f"[bold yellow]Disabled Stay on Top[/bold yellow]"))
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.toggle_stayOnTop_button.setText('Enable Stay on Top')
        self.show()
        

    def toggleAutoFollow(self):
        if self.AUTO_FOLLOW_ON == True:
            print(Panel(f"[bold yellow]Disabled auto-follow[/bold yellow]"))
            self.toggle_follow_button.setText('Enable auto-follow') 
        else:
            print(Panel(f"[bold yellow]Enabled auto-follow[/bold yellow]"))
            self.toggle_follow_button.setText('Disable auto-follow')
        self.AUTO_FOLLOW_ON = not self.AUTO_FOLLOW_ON


    def onLoadFinished(self):
        """ Remove unnessecary stuff from Map """
        self.webview.page().runJavaScript("""
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
        self.worker.progress.connect(self.setMarker)
        self.thread.start()
    

    def follow_marker(self, location):
        if self.AUTO_FOLLOW_ON == True:
            x,y = location
            self.webview.page().runJavaScript("""window.mapX.panTo({lat: %s-14336, lng: %s});""" % (y,x))
    

    def setMarker(self, location):
        """ Credits to (@Seler - https://github.com/seler) for centering of player position"""
        x,y = location
        self.webview.page().runJavaScript("""window.markerX.setLatLng({lat: %s-14336, lng: %s});""" % (y,x))
        self.follow_marker(location)
        self.latestCoordinate = [x, y]
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    w.loop()
    sys.exit(app.exec_())         
