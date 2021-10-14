#!/usr/bin/env python3 
# -*- coding: utf-8 -*- Python 3.8.8
#----------------------------------------------------------------------------
# Created By  : Nezzquikk
# Created Date: 2021/10/13
# version ='0.8.1'
# ---------------------------------------------------------------------------
""" This is an interactive MiniMap that is reading player position with
    PyTesseract OCR and visualizing it on a New World Map with live marker """ 
# ---------------------------------------------------------------------------
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore          import *
from PyQt5.QtGui        import *
from PyQt5.QtWidgets import *
from win32 import win32gui
from ctypes import windll
from PIL import Image
import numpy as np
import pytesseract
import win32ui
import sys
import cv2
import re
# ---------------------------------------------------------------------------

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DISPLAY_SIZE = [windll.user32.GetSystemMetrics(0),windll.user32.GetSystemMetrics(1)]
SIZE_OF_MINIMAP = (250,250)
FRAMELESS_WINDOW = True

""" PyQT5 is blocking main thread for rendering GUI thus using QThread and QWorker
    for processing OCR and player positioning """
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(object)
    lastCoordinate = [0,0]

    def run(self):
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
            """ OCR section for 1920 x 1080 """
            screenshot = im.crop((DISPLAY_SIZE[0] - 268, 19, 1920, 35))
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            screenshot = np.array(screenshot) 
            screenshot = cv2.inRange(np.array(screenshot), np.array([100, 100, 100]), np.array([255, 255, 255]))
            screenshot = unsharp_mask(screenshot)
            playerLocation = pytesseract.image_to_string(screenshot,  config='-c tessedit_char_whitelist=[].,0123456789')
            print("PlayerPosition:", playerLocation)
            try:
                playerLocation = re.findall(r'\[(\d{1,5})[,.]{1,2}\d{1,3}[,.]{1,2}(\d{1,5})[,.]', playerLocation) 
                self.lastCoordinate = playerLocation[0]
                self.progress.emit(playerLocation[0])
            except:
                print("Coordinates not found!")
                self.progress.emit(self.lastCoordinate)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("New World Interactive Map by Nezzquikk")
        self.AUTO_FOLLOW_ON = True
        self.ISCIRCULAR = True
        self.STAYONTOP = True
        self.initUI()
        """ Tesseract Path """
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        """ if you want executable (Tesseract required in folder) use pyInstaller"""
        # pyinstaller -F --add-data "Tesseract-OCR;Tesseract-OCR" MiniMap.py || "Tesseract-OCR\\tesseract.exe" 
        self.webview = QWebEngineView()
        webpage = QWebEnginePage(self.webview)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.move(QCursor.pos())
        self.useragent = QWebEngineProfile(self.webview)
        self.useragent.defaultProfile().setHttpUserAgent("Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko; googleweblight) Chrome/38.0.1025.166 Mobile Safari/535.19")
        self.webview.setPage(webpage)
        self.webview.setUrl(QUrl("https://www.newworld-map.com/#/"))
        self.setCentralWidget(self.webview)
        self.webview.loadFinished.connect(self.onLoadFinished)
        self.webview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.latestCoordinate = [0,0]
        self.webview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.webview.customContextMenuRequested.connect(self.on_context_menu)
        self.initContextMenu()
 

    def initContextMenu(self):
        self.popMenu = QMenu(self)
        self.toggle_follow_button = QAction("Disable auto-follow")
        self.toggle_viewmode_button = QAction("Change to Rectangular")
        self.popMenu.addAction(self.toggle_follow_button)
        self.toggle_follow_button.triggered.connect(self.toggleAutoFollow)
        self.popMenu.addAction(self.toggle_viewmode_button)
        self.toggle_viewmode_button.triggered.connect(self.toggleViewMode)
        self.toggle_stayOnTop_button = QAction("Disable Stay on Top")
        self.popMenu.addAction(self.toggle_stayOnTop_button)
        self.toggle_stayOnTop_button.triggered.connect(self.toggleStayOnTop)
        

    def on_context_menu(self, point):
        self.popMenu.exec_(self.webview.mapToGlobal(point))


    def toggleViewMode(self):
        self.ISCIRCULAR = not self.ISCIRCULAR
        if self.ISCIRCULAR == True:
            self.initUI()
            self.toggle_viewmode_button.setText('Change to Circular') 
        else:
            self.initUI()
            self.toggle_viewmode_button.setText('Change to Rectangular')


    def toggleStayOnTop(self):
        if self.STAYONTOP == True:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.toggle_stayOnTop_button.setText('Enable Stay On Top') 
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.toggle_stayOnTop_button.setText('Disable Stay on Top')
        self.show()
        self.STAYONTOP = not self.STAYONTOP


    def toggleAutoFollow(self):
        print(self.AUTO_FOLLOW_ON)
        if self.AUTO_FOLLOW_ON == True:
            self.toggle_follow_button.setText('Enable auto-follow') 
        else:
            self.toggle_follow_button.setText('Disable auto-follow')
        self.AUTO_FOLLOW_ON = not self.AUTO_FOLLOW_ON


    def onLoadFinished(self):
        """ Remove unnessecary stuff from Map """
        self.webview.page().runJavaScript('document.querySelector("#main > div.v-application--wrap > header > div").style="height: 56px;margin-left: 40%;"')
        self.webview.page().runJavaScript('document.querySelector("body").style="overflow: hidden;"')
        self.webview.page().runJavaScript('document.querySelector("#nn_player").remove()')
        self.webview.page().runJavaScript('document.querySelector("#main > div.v-application--wrap > footer").remove()')
        self.webview.page().runJavaScript('document.querySelector("#main > div.v-application--wrap > header > div > button:nth-child(4)").remove()')
        self.webview.page().runJavaScript('document.querySelector("#main > div.v-application--wrap > main").style = "padding: 0px 0px 0px";')
        self.webview.page().runJavaScript("""var style = document.createElement("style");style.innerHTML = 'body::-webkit-scrollbar {display: none;}';document.head.appendChild(style);""")
        self.webview.page().runJavaScript('document.querySelector("#main > div.v-application--wrap > aside").style = "margin-left:7%";')
        self.webview.page().runJavaScript('setTimeout(() => {window.mapX=document.getElementById("map").__vue__.mapObject;window.markerX = window.L.marker({lat: 0, lng: 0});window.markerX.addTo(window.mapX);},1500);')
        

    def initUI(self):
        if FRAMELESS_WINDOW == True:
            # self.setWindowFlags(Qt.Tool)
            radius = 200.0 if self.ISCIRCULAR == True else 0.0
            self.painterPath = QPainterPath()
            self.resize(*SIZE_OF_MINIMAP) # size of MiniMap
            self.painterPath.addRoundedRect(QRectF(self.rect()), radius, radius)
            mask = QRegion(self.painterPath.toFillPolygon().toPolygon())
            self.setMask(mask)


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
