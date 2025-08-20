import cv2 as cv
import mediapipe as mp 
import mediapipe.python.solutions.hands
import numpy as np
from collections import deque
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from IconAnimator import IconAnimator
from DataProces import Data



class Menu():
    def __init__(self):
        # -----------------------------------菜单系统状态管理--------------------------------------- #
        self.frontPinchHistory = False          # 正手捏合的历史状态 (用于状态切换检测)(也可以是长按的判定)
        self.frontPinch = False                 # 当前正手单击瞬间的状态
        self.frontRelease = False               # 正手松开瞬间的状态
        self.Front = False                      # 当前是否为正手状态
        self.isMenuBall = False                 # 菜单球存在状态
        self.isMenu = False                     # 菜单存在状态
        self.PinchIndex = 0                     # 单击次数计数器
        # --------------------------------------图标坐标---------------------------------------------- #

        self.point_menuball = None              # 初始化菜单定位
        self.point_menu = None
        self.center_vol = None
        self.center_light = None
        self.menu_stop_point = None
        self.TowFingerCenter = None             # 手指坐标

        self.lenght_to_vol = None
        self.lenght_to_light = None

        # -----------------------------------图标动画器初始化------------------------------------------- #
        # 初始化图标动画器
        self.MenuBall_animator = IconAnimator(r"icon_images\image copy 3.png", max_scale=0.8, alpha=0.8, animation_duration=0.7)
        self.Menu_animator = IconAnimator(r'icon_images\image copy 4.png', max_scale=4, alpha=0.7, animation_duration=0.6)
        self.Volume_animator = IconAnimator(r"icon_images\image copy 5.png", max_scale=1, alpha=0.8, animation_duration=0.6)
        self.Light_animator = IconAnimator(r"icon_images\image copy 6.png", max_scale=1, alpha=0.8, animation_duration=0.6)

        # ------------------------------------数据处理器-----------------------------------------------------#
        self.data = Data()
        # ----------------------------------音量控制初始化------------------------------------ #
        # 获取系统默认音频输出设备
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))  # 音量控制接口
        
        # 获取系统音量范围
        self.volRange = self.volume.GetVolumeRange()
        self.minVol, self.maxVol = self.volRange[0], self.volRange[1]  # 音量最小值和最大值

        
    # 更新数据
    def updata(self,frontPinchHistory,frontPinch,frontRelease,Front,isMenuBall,isMenu,
               PinchIndex,point_menuball,point_menu,TowFingerCenter,TowFingerLenght):

        self.frontPinchHistory = frontPinchHistory          # 正手捏合的历史状态 (用于状态切换检测)(也可以是长按的判定)
        self.frontPinch = frontPinch                        # 当前正手单击瞬间的状态
        self.frontRelease = frontRelease                    # 正手松开瞬间的状态
        self.Front = Front                                  # 当前是否为正手状态
        self.isMenuBall = isMenuBall                        # 菜单球存在状态
        self.isMenu = isMenu                                # 菜单存在状态
        self.PinchIndex = PinchIndex                        # 单击次数计数器
        self.point_menu = point_menu                        # 初始化菜单定位
        self.point_menuball = point_menuball
        self.TowFingerCenter = TowFingerCenter              # 双指中心点
        self.TowFingerLenght = TowFingerLenght              # 双指距离

    def updata_center(self,center_vol,center_light):
        self.center_vol = center_vol
        self.center_light = center_light

    # 菜单球显示
    def AwakenMenuBall(self, img, point=None):
        imgHeight = img.shape[0]
        imgWidth = img.shape[1]

        if point == None:
            point = (imgWidth//2,imgHeight//2)

        return self.MenuBall_animator.draw_growing_matrix(img, (point[0]-15, point[1]-15))
                
    # 菜单显示
    def AwakenMenu(self, img, point=None):
        
        imgHeight = img.shape[0]
        imgWidth = img.shape[1]

        if point == None:
            point = (imgWidth//2,imgHeight//2)

        # 集成菜单图像
        Menu_img = self.Menu_animator.draw_growing_matrix(img, (point[0]-15, point[1]-15))              # 菜单背景
        Volume_img = self.Volume_animator.draw_growing_matrix(Menu_img, (point[0]-100, point[1]-15))    # 音量图标
        return self.Light_animator.draw_growing_matrix(Volume_img, (point[0]+75, point[1]-15))          # 亮度图标
    
        
    # **************************************** 启动菜单*****************************************#
    def RunMenu(self,img,draw_touchRange = True):

        # 获取图标中心坐标
        self.center_vol = self.Volume_animator.get_icon_center()
        self.center_light = self.Light_animator.get_icon_center()

        # ------------------------------计算手指到选项的距离---------------------------------#
        if self.center_vol is not None:
            self.lenght_to_vol = int(((self.center_vol[0] - self.TowFingerCenter[0])**2 + (self.center_vol[1] - self.TowFingerCenter[1])**2)**0.5)
            self.lenght_to_light = int(((self.center_light[0] - self.TowFingerCenter[0])**2 + (self.center_light[1] - self.TowFingerCenter[1])**2)**0.5)

            # print(f"center_vol:{self.center_vol}")
            # print(f"TowFingerCenter:{self.TowFingerCenter}")
            # print(f"lenght_to_vol:{self.lenght_to_vol}")
            # print(f"lenght_to_light:{self.lenght_to_light}")

        # -------------------------------------菜单界面------------------------------------- #
        if self.isMenuBall:
            return self.AwakenMenuBall(img,self.point_menuball)

        # ------------------------------进入菜单（手指长按进行菜单选择，松开确认）---------------------#
        elif self.isMenu:
            
            # 显示图标触发范围
            if self.center_vol and self.center_light and draw_touchRange:
                cv.circle(img,self.center_vol,50,(255,255,0),5)
                cv.circle(img,self.center_light,50,(255,255,0),5)

            # 点击判定
            if self.frontPinch:
                # print(f"单机成功！！！*************************************")
                self.menu_stop_point = self.point_menu

            # 长按判定
            elif self.frontPinchHistory and self.menu_stop_point:
                # print(f"长按中！！！***************************************")
                # print(f"lenght_to_vol 长按时 :{self.lenght_to_vol}")
                # print(f"lenght_to_light 长按时 :{self.lenght_to_light}")

                if self.lenght_to_vol is not None and self.lenght_to_light is not None:
                    if self.lenght_to_vol <= 120 :
                        print(f'选项：音量调节！！！')
                    if self.lenght_to_light <= 120 :
                        print(f'选项：亮度调节！！！')

                # 显示菜单
                return self.AwakenMenu(img,self.menu_stop_point)
            
            # 松手确认
            elif self.frontRelease and self.TowFingerCenter is not None:
                print(f"松手成功！！！*************************************")
                # pass
                if self.lenght_to_vol is not None and self.lenght_to_light is not None:
                    if self.lenght_to_vol <= 55 :
                        print(f'音量调节选择成功！！！')
                        self.controlVol(img,draw=True)

                    if self.lenght_to_light <= 55 :
                        print(f'亮度调节选择成功！！！')

            return self.AwakenMenu(img,self.point_menu)
        
    
    # ***************************************内置软件***************************************************** #
    # -------------------------------通过双指距离控制系统音量--------------------------------#
    def controlVol(self,img,exponent=1,draw=True):

        if self.TowFingerCenter is not None:
            
            # 使用指数映射计算音量百分比(显示用)
            vol_percent = self.data.ExponentialMap(self.TowFingerLenght, [40, 300], [0, 100], exponent)
            
            if draw:
                cv.putText(img, f"{int(vol_percent)}%", self.TowFingerCenter, 2, 1, color, 2)
            
            # 计算实际音量值并设置系统音量
            vol = self.data.ExponentialMap(self.TowFingerLenght, [40, 300], [self.minVol, self.maxVol], 0.17)
            self.volume.SetMasterVolumeLevel(vol, None)
            
            # 当距离过近时改变显示颜色(绿色)
            if self.TowFingerLenght <= 40:
                color = (0, 255, 0)
            else:
                color = (2, 81, 255)