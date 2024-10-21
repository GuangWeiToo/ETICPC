import os,shutil,requests, httpx
import downloadSTL, MakerBotAuto
from dotenv import load_dotenv
import tkinter as tk
from tkinter import simpledialog

load_dotenv()
apiKey=os.getenv('Api_Key')



#Get first 5 database queue rows and download from link
async def fetch_data():
    place=MakerBotAuto.place
    async with httpx.AsyncClient() as client:
        response = await client.get('https://eticapi.vercel.app/api/getQueueDataThenDelete',params={"key":apiKey,"place":place})  # Send the request
        rows = response.json()
    if rows!=[]:
        for row in rows:
            request_id=row['request_id']
            url=row['file_link']
            validSTL,filepath=downloadSTL.download_and_check_stl(url)
            #Check if onedrive downloads are STL files, #if STL are valid move file to local queue folder
            # if not (delete) then (update progress "as not able to print")
            
            if validSTL:
                currentFileLocation=filepath
                destinationFolder=MakerBotAuto.FolderPath+"\\"+"MakerBotQueue"
                fileName=os.path.basename(currentFileLocation)
                destination_path = os.path.join(destinationFolder, fileName)   #Move from zone to queue
                shutil.move(currentFileLocation, destination_path)
                
                requests.post('https://eticapi.vercel.app/api/updateProgress',params={"key":apiKey,"column":"progress","msg":"Print in queue","request_id":request_id})
                MakerBotAuto.addToList(fileName,request_id)
                print("Valid STL")
            else:
                os.remove(filepath,request_id)
                requests.post('https://eticapi.vercel.app/api/updateProgress',params={"key":apiKey,"column":"progress","msg":"Not able to print","request_id":request_id})
                print("Not valid STL")
    else:
        print("data is empty, most likely no more queue")
        
