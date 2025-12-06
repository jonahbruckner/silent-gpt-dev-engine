+++
title = "“Operation not permitted” when creating directories and saving files in Azure App Service (FastAPI on Linux)"
date = "2025-12-02T12:17:50.930440"
slug = "operation-not-permitted-when-creating-directories-and-saving-files-in-azure-app-service-fastapi-on-linux"
description = "When deploying a FastAPI application on Azure App Service using a Linux environment, you might encounter the \"Operation not permitted\" error when trying to create directories or save files. This issue typically arises from the way Azure..."
+++

When deploying a FastAPI application on Azure App Service using a Linux environment, you might encounter the "Operation not permitted" error when trying to create directories or save files. This issue typically arises from the way Azure App Service manages file system permissions and the environment in which your application is running. This micro-tutorial will guide you through understanding the problem and provide a step-by-step solution.

## Why this happens

Azure App Service runs applications in a sandboxed environment with specific restrictions on file system access. The underlying file system is read-only for certain directories, and write access is limited to specific locations. When your FastAPI application attempts to create directories or save files outside of these designated areas, you will encounter the "Operation not permitted" error.

## Step-by-step solution

To resolve this issue, follow these steps:

1. **Identify the Correct Directory**: Azure App Service allows writing to specific directories, such as the `/home` directory. Ensure that your application targets these directories for file operations.

2. **Modify Your FastAPI Code**: Update your FastAPI code to point to the writable directory. Below is an example of how to create a directory and save a file in the correct location.

3. **Deploy Your Changes**: After making the necessary changes to your code, redeploy your FastAPI application to Azure App Service.

### Example Code

Here’s a complete example demonstrating how to create a directory and save a file in Azure App Service using FastAPI:

```python
from fastapi import FastAPI, HTTPException
import os

app = FastAPI()

# Define the writable directory path
writable_directory = "/home/site/wwwroot/uploads"

# Ensure the directory exists
os.makedirs(writable_directory, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: bytes):
    try:
        # Define the file path
        file_path = os.path.join(writable_directory, "uploaded_file.txt")
        
        # Write the file to the writable directory
        with open(file_path, "wb") as f:
            f.write(file)
        
        return {"message": "File uploaded successfully", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/")
async def list_files():
    try:
        # List files in the writable directory
        files = os.listdir(writable_directory)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Example variation

If you want to allow users to upload files with different names, you can modify the `upload_file` function to accept a filename parameter:

```python
from fastapi import UploadFile, File

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Define the file path using the original filename
        file_path = os.path.join(writable_directory, file.filename)
        
        # Write the file to the writable directory
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {"message": "File uploaded successfully", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Common errors & fixes

1. **Error: "Permission denied"**: This error occurs when trying to write to a directory outside of the allowed paths. Ensure you are writing to `/home` or `/home/site/wwwroot`.

2. **Error: "No such file or directory"**: This error may arise if the target directory does not exist. Use `os.makedirs(directory, exist_ok=True)` to create the directory if it doesn't exist.

3. **Error: "File too large"**: Azure App Service has a limit on the size of files that can be uploaded. Check the Azure documentation for the current limits and handle large files accordingly.

## Cheat sheet summary

- **Writable Directory**: Use `/home/site/wwwroot/uploads` or similar paths for file operations.
- **Creating Directories**: Use `os.makedirs(directory, exist_ok=True)` to ensure the directory exists.
- **File Upload**: Use FastAPI's `UploadFile` for handling file uploads.
- **Error Handling**: Use `HTTPException` to handle errors gracefully.

By following this micro-tutorial, you should be able to resolve the "Operation not permitted" error when creating directories and saving files in your FastAPI application on Azure App Service. Happy coding!
