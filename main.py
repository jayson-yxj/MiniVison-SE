import numpy as np
import cv2 as cv
from HCI import HandHCI 

'''
暂时的测试用demo运行主程序文件
'''

mtx = np.array([
    [614.44602955, 0, 334.00803739],
    [0, 614.63411118, 239.27203493],
    [0, 0, 1]
], dtype=np.float32)

dist = np.array([
    -4.22046818e-01,
    1.58838910e-01,
    2.11172605e-03,
    3.35576757e-04,
    1.18813241e-01
], dtype=np.float32).reshape(1, 5) 


def main():
    HandFlipPath = r'video\HandFlip.mp4'
    HandFlipAndPinch2Path = r'video\HandFlipAndPinch.mp4'
    HandPinchMovePath = r'video\HandPinchMove.mp4'
    AllTestPath = r'video\AllTest.mp4'
    MenuChoicePath = r'video\MenuChoice.mp4'
    cap = cv.VideoCapture(MenuChoicePath)
    hand = HandHCI()

    while 1:
        succes,img = cap.read()

        if succes :
            # 获取左手的信息(flalse: 是否显示关键点)
            lfhand = hand.findLfHands(img,False)
            # print(lfhand)

            # print(hand.isFront(lfhand))

            # 判断正手捏合
            isFront = hand.isFront(lfhand)
            isPinch = hand.fingersPinch(lfhand)
            # print(f'isFront: {isFront}')
            # print(f'isPinch: {isPinch}')

            # 菜单球跳出
            img2 = hand.HandMenu(img,isFront,isPinch)
            
            if img2 is not None and img2.size > 0:
                img = img2

            cv.imshow("img",img)
        else:
            break

        if cv.waitKey(1) == 27:
            break


if __name__ == '__main__':
    main()