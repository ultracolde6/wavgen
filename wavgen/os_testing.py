import shutil
import os.path
from pathlib import Path
import datetime

if __name__ == '__main__':
    date_dir = datetime.datetime.now().strftime("%Y\%m\%d")
    date_dir1 = datetime.datetime.now().strftime("%Y/%m/%d")
    year = datetime.datetime.now().strftime("%Y")
    month = datetime.datetime.now().strftime("%m")
    day = datetime.datetime.now().strftime("%d")

    new_dir = 'Y:/expdata-e6/data/fluo_images_delete'
    new_path_name = f'{new_dir}/{date_dir1}'
    print(new_path_name)
    new_path = Path(new_path_name)
    isdir = os.path.isdir(new_path)
    if not isdir:
        os.mkdir(f'{new_dir}/{year}')
        os.mkdir(f'{new_dir}/{year}/{month}')
        os.mkdir(f'{new_dir}/{year}/{month}/{day}')
        print(f'directory created')
