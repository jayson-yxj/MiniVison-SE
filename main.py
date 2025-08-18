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
    cap = cv.VideoCapture(AllTestPath)
    hand = HandHCI()

    while 1:
        succes,img = cap.read()

        if succes :
            # 获取左手的信息
            lfhand = hand.findLfHands(img)
            # print(lfhand)

            # print(hand.isFront(lfhand))

            # 判断正手捏合(flalse: 是否显示关键点)
            isFront = hand.isFront(lfhand,False)
            isPinch = hand.fingersPinch(lfhand,False)
            # print(f'isFront: {isFront}')
            # print(f'isPinch: {isPinch}')

            # 菜单球跳出
            img2 = hand.AwakenMenuBall(img,isFront,isPinch)
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