import os,GetRequests, asyncio
import sys
import requests
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import simpledialog,messagebox
from dotenv import load_dotenv
load_dotenv()
apiKey=os.getenv('Api_Key')

fileList = []
FolderPath = r'C:\MAKERBOT_Printing'
place= None

apiKey = os.getenv('SupaApi_Key')

class WatcherHandler(FileSystemEventHandler):#watchdog to observe if folder moved or new file added
    def on_moved(self, event):
        if event.is_directory and "MAKERBOT_Printing" in event.src_path:
            global FolderPath
            FolderPath = event.dest_path
            print(f"Folder moved to: {FolderPath}")
    def on_created(self, event):
        # If a new file is created in the folder, show the popup
        if not event.is_directory:
            print(f"New file created: {event.src_path}")
            folderName = None
            folder_path = os.path.dirname(event.src_path)
            if "Completed3D_Prints" in folder_path:
                folderName = "Completed3D_Prints"
            elif "Incompleted3D_Prints" in folder_path:
                folderName = "Incompleted3D_Prints"
                
            if folderName:
                show_input_popup(folderName)


def addToList(fileName, request_id):
    fileList.append((fileName, request_id))
    
async def getPlace():
    # List of valid places
    valid = ['eticM', 'eticLI']
    root = tk.Tk()
    root.withdraw()
    
    # Loop until valid input is provided
    while True:
        try:
            place = simpledialog.askstring("Input", "Please enter the 'place':")
            
            if place is None:
                messagebox.showerror("Exiting", "Operation cancelled by user.")
                root.quit()
                root.destroy()
                sys.exit()
                return None 
            
            
            if not place:
                raise ValueError("Place cannot be empty")
            
            # Check if the input is in the valid list
            if place in valid:
                return place
            else:
                raise ValueError(f"'{place}' is not a valid place. Valid options are: {', '.join(valid)}")

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
        
async def RunAutomation():
    checking = True
    defaultFolderPath = r'C:\MAKERBOT_Printing'

    if not os.path.exists(defaultFolderPath):
        os.makedirs(defaultFolderPath)
        os.makedirs(os.path.join(defaultFolderPath, "MakerBotQueue"))
        os.makedirs(os.path.join(defaultFolderPath, "Completed3D_Prints"))
        os.makedirs(os.path.join(defaultFolderPath, "Incompleted3D_Prints"))
    global place
    place= await getPlace()
    while checking:
        await GetRequests.fetch_data()
        print("fetched data")

def monitor_folder(folder_path):
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()

def checkMatchedFiles(folder):
    files = os.listdir(folder)#get items in completed folder
    if any(os.path.isfile(os.path.join(folder, f)) for f in files): #if there are any files in the specified  folder
        for file in fileList:
            if file is not None:
                fileName = file[0]
                requestID = file[1]
                if fileName in files:
                    return fileName,requestID

def show_input_popup(folderName): 
    root = tk.Tk() 
    root.withdraw() # Hide the main window 
    user_input = None
    completed_folder = os.path.join(FolderPath, "Completed3D_Prints")
    incompleted_folder = os.path.join(FolderPath, "Incompleted3D_Prints")
    
    if(folderName=="Completed3D_Prints"):
        try:
            filename,requestid=checkMatchedFiles(completed_folder)
            while not user_input:
                requests.post('https://eticapi.vercel.app/api/updateProgress', params={"key":apiKey, "column":'progress',"msg":"Completed","request_id":requestid})
                user_input = simpledialog.askstring("Input", "A new file was added as complete. Enter location/locker# for person to pick up:")
                if not user_input:  # If input is None or empty, show the prompt again
                    tk.messagebox.showerror("Input Error", "Input is required! Please enter a location/locker#.")
                # If valid input is provided, send the data
            requests.post('https://eticapi.vercel.app/api/updateProgress',params={"key":apiKey,"column":'pick_up_location',"msg":user_input,"request_id":requestid})
            os.remove(os.path.join(completed_folder, filename))
        except Exception as e:
            print(f"An error occurred: {e}. Most likely because the file dropped in the completed folder are not from the database")
    elif(folderName=="Incompleted3D_Prints"):
        try:
            checkMatchedFiles(incompleted_folder)
            while not user_input:
                user_input = simpledialog.askstring("Input", "A new file was added as complete. Enter reason for incompletion:")
                if not user_input:  # If input is None or empty, show the prompt again
                    tk.messagebox.showerror("Input Error", "Input is required! Please enter reason.")
                # If valid input is provided, send the data
            requests.post('https://eticapi.vercel.app/api/updateProgress',params={"key":apiKey,"column":'progress',"msg":"Incompleted. Reason:"+user_input,"request_id":requestid})
            os.remove(os.path.join(incompleted_folder, filename))
        except Exception as e:
            print(f"An error occurred: {e}. Most likely because the file dropped in the incompleted folder are not from the database")  
            
# Function to run the watchdog observer
def run_observer():
    folder_to_monitor = r'C:\MAKERBOT_Printing'
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_to_monitor, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)  # Keep the observer running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Running both RunAutomation and watchdog observer concurrently
if __name__ == "__main__":
    # Create a thread for the watchdog observer
    observer_thread = threading.Thread(target=run_observer)
    
    # Start the observer thread
    observer_thread.start()
    
    # Run the automation function on the main thread
    asyncio.run(RunAutomation())

    # Wait for the observer thread to finish (if needed)
    observer_thread.join()
