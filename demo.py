import numpy as np
import cv2 as cv
from HCI import HandHCI 

def main():
    AllTestPath = r'video\AllTest.mp4'
    cap = cv.VideoCapture(AllTestPath)
    hand = HandHCI()

    while 1:
        succes,img = cap.read()
        if succes :
            # 获取左手的信息
            lfhand = hand.findLfHands(img)
            # 获取右手的信息
            rthand = hand.findRtHands(img)

            # 右手控制音量
            hand.controlVol(img,rthand)

            # 获取捏合信息
            isFront = hand.isFront(lfhand,False)
            # 获取手的正反
            isPinch = hand.fingersPinch(lfhand,False)

            # 菜单球跳出
            img2 = hand.AwakenMenuBall(img,isFront,isPinch)
            # 菜单跳出
            img3 = hand.AwakenMenu(img)
            
            if img2 is not None and img2.size > 0:
                img = img2
                print(f'img2')
            elif img3 is not None and img3.size > 0:
                img = img3
                print(f'img3')

            cv.imshow("img",img)

        if cv.waitKey(1) == 27:
            break

if __name__ == '__main__':
    main()