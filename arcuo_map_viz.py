import cv2
import numpy as np
import cv2.aruco as aruco
import glob
import time
import math
import json
import operator
import matplotlib.pyplot as plt
rlst = []
tlst = []
class ekf:
    def __init__(self):

        self.video = "test/video_0409_1.avi_20200416_135737.mp4"
        self.map = cv2.imread("map.jpg")
        self.json_file = "config_file/m_pos.json"
        self.cap = cv2.VideoCapture(self.video)
        #标定矩阵-kinectdk
        # self.mtx=np.array([[586.71992539,0., 642.5673099],
        #             [0.,577.7185321,358.14158103],
        #             [0.,0.,1.]])
        # self.dist=np.array([[ 0.06001582 , 0.10857292 ,-0.0030517  , 0.00037337 ,-0.28575739]])
        # self.mtx = np.array([[610.02350998 ,  0.   ,      639.15699463],
        #         [  0.  ,       609.26971495 ,362.31366881],
        #         [  0.  ,         0.     ,      1.        ]])
        # self.dist = np.array([[ 0.09543971 ,-0.09547887 ,-0.00080118 ,-0.00026294 , 0.05709619]])
        self.mtx = np.array([[598.66989512 ,  0.    ,     643.58799482],
                             [  0.      ,   598.87839865, 366.90019198],
                                [  0.      ,     0.     ,      1.        ]])
        self.dist = np.array([[ 0.09402367 ,-0.08942175 , 0.00062654  ,0.00052183  ,0.04827724]])
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.m_dic = self.read_json()
    def read_json(self):
        with open(self.json_file,'r') as load_f:
            load_dict = json.load(load_f)
            return load_dict
    def cut_img(self,image):
        n = np.array([[160,80],[1120,80],[1120,640],[160,640]])
        con2=np.array(n)
        cimg = np.zeros_like(image)
        cv2.drawContours(cimg, [con2.astype(int)], 0, (255,255,255), thickness=-1) 
                    #自适应阈值化
        imgroi= cv2.bitwise_and(cimg,image) 
        return imgroi
    def draw_pos(self,img,pos):
        new_pos = np.dot(pos,np.array([[0,-1],[1,0]]))
        new_pos = (int(new_pos[0]),int(2040-new_pos[1]))
       
        cv2.circle(img,new_pos,4,(0,0,255),5)
        
        return img
        
        
    def num(self,number):
        if number>0:
            return True
        else:
            return False

###------------------ ARUCO TRACKER ---------------------------
   
    def estimatePose1(self,img,corners,ids,point):
        if np.all(ids != None):
            rvec, tvec ,_ = aruco.estimatePoseSingleMarkers(corners, 0.095, self.mtx, self.dist)
            tvec = np.around( tvec, decimals=3)
            t_lst = tvec.tolist()
            r_lst = rvec.tolist()
            robot_lst = []
            rr_lst=[]
            for i in r_lst:
                x,y,z = self.rotationMatrixToEulerAngles(np.array(i[0]))
                x = np.around( x, decimals=3)
                y = np.around( y, decimals=3)
                z = np.around( z, decimals=3)
                rr_lst.append(y)
            for i in range(len(t_lst)):
                m_id = ids[t_lst.index(t_lst[i])][0]
                d = np.linalg.norm(np.array([t_lst[i][0][0],t_lst[i][0][2]]) - np.array([0,0]))*100
                t_pos = np.array([t_lst[i][0][0],t_lst[i][0][2]])
                x_y = [self.m_dic[str(m_id)][0],self.m_dic[str(m_id)][1]]
                rol_m = self.m_dic[str(m_id)][2]
                rol_r = rol_m+rr_lst[i]
                # print('rol:',rol_r,rr_lst[i])
                rol_r = -rol_r*math.pi/180
                rol_matrix = np.array([[math.cos(rol_r),-math.sin(rol_r)],[math.sin(rol_r),math.cos(rol_r)]])
                
                # print('maker_map_x_y:',x_y)
                # print('c_x_y_z:',t_lst[i][0])
                # print(np.dot(t_pos,rol_matrix)*100)

                
                pos = np.array(x_y)*60-np.dot(t_pos,rol_matrix)*100
                    
                robot_lst.append(pos.tolist())
                
            result_pos = np.mean(np.array(robot_lst),axis=0)
            # if robot_lst[0][0]<-300:
            #     cv2.imwrite('img_save/map_test8.jpg',point)
            frame = self.draw_pos(img,result_pos)
            # frame = self.draw_pos(img,np.array(robot_lst[0]))
            # frame = self.draw_pos(img,np.array(robot_lst[1]))
            # frame = self.draw_pos(img,np.array(robot_lst[2]))
            return frame
                
        else:
            return img
    def rotationMatrixToEulerAngles(self,rvecs):
        R = np.zeros((3, 3), dtype=np.float64)
        cv2.Rodrigues(rvecs, R)
        sy = math.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
        singular = sy < 1e-6
        if  not singular:
            x = math.atan2(R[2,1] , R[2,2])
            y = math.atan2(-R[2,0], sy)
            z = math.atan2(R[1,0], R[0,0])
        else :
            x = math.atan2(-R[1,2], R[1,1])
            y = math.atan2(-R[2,0], sy)
            z = 0
        #print('dst:', R)
        x = x*180.0/3.141592653589793
        y = y*180.0/3.141592653589793
        z = z*180.0/3.141592653589793
        return x,y,z
    def put_test_estimatePose(self,frame,corners,ids):
        if np.all(ids != None):
            rvec, tvec ,_ = aruco.estimatePoseSingleMarkers(corners, 0.095, self.mtx, self.dist)
            tvec = np.around(tvec, decimals=3)
            for i in range(0, ids.size):
                aruco.drawAxis(frame, self.mtx, self.dist, rvec[i], tvec[i], 0.1)
            aruco.drawDetectedMarkers(frame, corners)
            n=30
            m=0
            t_lst = tvec.tolist()
            r_lst = rvec.tolist()
            for i in t_lst:
                d = np.linalg.norm(np.array([i[0][0],i[0][2]]) - np.array([0,0]))
                d = np.around( d, decimals=3)
                cv2.putText(frame, "id:{},x,y,z: ".format(str(ids[t_lst.index(i)][0])) + str(i[0]), (0,450+n*m), self.font, 0.7, (0,255,0),2,cv2.LINE_AA)
            
                m+=1
            m=0
            for i in r_lst:
                x,y,z = self.rotationMatrixToEulerAngles(np.array(i[0]))
                x = np.around( x, decimals=3)
                y = np.around( y, decimals=3)
                z = np.around( z, decimals=3)
                cv2.putText(frame, "id:{},rol: ".format(str(ids[r_lst.index(i)][0])) + str(x)+' '+str(y)+' '+str(z), (0,550+n*m), self.font, 0.7, (0,255,0),2,cv2.LINE_AA)
                m+=1
            strg = ''
            for i in range(0, ids.size):
                strg += str(ids[i][0])+', '
            cv2.putText(frame, "Id: " + strg, (0,200), self.font, 0.7, (0,255,0),2,cv2.LINE_AA)
        else:
            cv2.putText(frame, "No Ids", (0,200), self.font, 0.7, (0,255,0),2,cv2.LINE_AA)
        return frame
    def run(self):
        while (True):
            ret, frame = self.cap.read()
            frame = self.cut_img(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
            parameters = aruco.DetectorParameters_create()
            parameters.adaptiveThreshConstant = 10
            corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
            move_point = self.put_test_estimatePose(frame,corners,ids)
            map_move = self.estimatePose1(self.map,corners,ids,move_point)
            map_move = cv2.resize(map_move,(0,0),fx=0.3, fy=0.3,interpolation=cv2.INTER_NEAREST)
            cv2.imshow('frame',map_move)
            cv2.imshow('frame1',move_point)
            
            
                
            # cv2.imwrite('img_save/map_result.jpg',map_move)
            if cv2.waitKey(1) & 0xFF ==ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    def run_img(self):
        img = cv2.imread("D:/python_vscode/work/kinect_video/6.jpg")
        # img = self.cut_img(img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
        parameters = aruco.DetectorParameters_create()
        parameters.adaptiveThreshConstant = 10
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
        move_point = self.put_test_estimatePose(img,corners,ids)
        map_move = self.estimatePose1(self.map,corners,ids,move_point)
        
        map_move = cv2.resize(map_move,(0,0),fx=0.3, fy=0.3,interpolation=cv2.INTER_NEAREST)
        # cv2.imwrite('img_save/map_test8.jpg',move_point)
        cv2.imshow('frame',map_move)
        cv2.imshow('frame1',move_point)
        cv2.waitKey(0)


if __name__ == "__main__":
    ekf_slam = ekf()
    ekf_slam.run()
