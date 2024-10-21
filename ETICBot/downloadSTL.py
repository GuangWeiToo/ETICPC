import os,MakerBotAuto
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time

def getOnedriveFile(url):
    download_directory_path =os.path.abspath(os.path.join(MakerBotAuto.FolderPath, "DecontaminationZone"))
    os.makedirs(download_directory_path, exist_ok=True)
    op = webdriver.ChromeOptions()
    p = {"download.default_directory" : download_directory_path}
    op.add_experimental_option("prefs", p)
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=op)
    driver.maximize_window()
    files_before = set(os.listdir(download_directory_path))
    driver.get(url+'&download=1')
    time.sleep(3)#sleep 3sec
    # Get the updated list of files after the download
    files_after = set(os.listdir(download_directory_path))
    # Determine the downloaded file(s) by taking the difference
    downloaded_files = files_after - files_before
    # If there is a new file downloaded, return its full path
    if downloaded_files:
        downloaded_file_name = downloaded_files.pop()  # Get the first (expected) downloaded file name
        downloaded_file_path = os.path.join(download_directory_path, downloaded_file_name)
        print(f"Downloaded file path: {downloaded_file_path}")
    else:
        downloaded_file_path = None
        print("No new files were downloaded.")
    driver.close()
    return downloaded_file_path

def is_stl(file_path):
    with open(file_path, 'rb') as file:
        file_content = file.read(1024) 
    if file_content.startswith(b'solid'):
        try:
            with open(file_path, 'r', errors='ignore') as file:
                first_line = file.readline().strip()
            if first_line.startswith('solid'):
                return True
        except UnicodeDecodeError:
            return False
    if len(file_content) > 84:
        return True
    return False


def download_and_check_stl(onedrive_url):
    file_content=getOnedriveFile(onedrive_url)
    # Check if it is an STL file
    if is_stl(file_content):
        return True, file_content  # Return both the status and the file path
    else:
        return False, file_content
