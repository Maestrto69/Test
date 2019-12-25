import os
import cv2
import numpy as np
import os
import time

from modules.face_identification.face_identification_for_add\
        import face_identification

from aza_All_Go_to_DB import specific_go_to_DB


dataset_dir = 'dataset'

if __name__ == '__main__':
    identificator = face_identification()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('Убедитесь, что папка с Вашим именем находится в папке {}'\
                .format(dataset_dir))
        name = ''
        while len(name) == 0 or not os.path.isdir(dataset_dir + os.path.sep + name):
            name = input('Введите имя папки: ')
            if not os.path.isdir(dataset_dir + os.path.sep + name):
                print('Папка с таким именем не найдена')
        specific_go_to_DB(dataset_dir, name, face_identificator=identificator)

        os.system('cls' if os.name == 'nt' else 'clear')
        print('Фотографии загружены в базу данных')
        time.sleep(3)
