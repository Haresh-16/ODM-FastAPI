from fastapi import FastAPI, HTTPException
import os
import sys
import tempfile
from pyodm import Node, exceptions

app = FastAPI()

# Assuming your code is placed in a directory at the same level as this server script
sys.path.append('..')

# Function to process images
async def process_images(directory_path: str):
    node = Node("localhost", 3000)
    try:
        # Start a task
        print("Uploading images...")
        image_files = [os.path.join(directory_path, filename) for filename in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, filename))]
        num_images = len(image_files)
        task = node.create_task(image_files, {'dsm': True, 'orthophoto-resolution': 4})
        print(task.info())

        try:
            # Wait for task completion
            task.wait_for_completion()

            print("Task completed, downloading results...")
            # Retrieve results
            task.download_assets("./results")
            print("Assets saved in ./results (%s)" % os.listdir("./results"))

            # Restart task and compute dtm
            task.restart({'dtm': True})
            task.wait_for_completion()

            print("Task completed, downloading results...")
            task.download_assets("./results_with_dtm")
            print("Assets saved in ./results_with_dtm (%s)" % os.listdir("./results_with_dtm"))
        except exceptions.TaskFailedError as e:
            print("\n".join(task.output()))
            raise HTTPException(status_code=500, detail="Task failed")

    except exceptions.NodeConnectionError as e:
        print("Cannot connect: %s" % e)
        raise HTTPException(status_code=500, detail="Cannot connect to ODM Node")
    except exceptions.NodeResponseError as e:
        print("Error: %s" % e)
        raise HTTPException(status_code=500, detail="ODM Node responded with an error")

# Endpoint to process images
@app.post("/process_images")
async def process_images_endpoint():
    # Here, you might want to accept the directory path as a request parameter or use a fixed path.
    directory_path = r'/home/darkphoenix/images'
    await process_images(directory_path)
    return {"message": "Processing started, check server logs for details."}
