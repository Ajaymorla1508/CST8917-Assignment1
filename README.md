# CST8917-Assignment1
# Serverless Image Metadata Extraction Pipeline (Azure Functions)

## Author
**Ajay Morla**  
**Course:** CST8917 – Serverless Applications  
**Lab Title:** Serverless Image Metadata Extraction and Storage  

---

## Objective

To build a serverless pipeline using Azure Functions that automatically:
1. Triggers on blob upload (image file)
2. Extracts image metadata (e.g., dimensions, format, size)
3. Stores the extracted metadata in an Azure SQL Database

---

## Architecture

```plaintext
Azure Blob Storage (Trigger)
      ↓
Blob Trigger Function
      ↓
Durable Orchestrator Function
      ↓
  ┌─────────────┬──────────────┐
  ↓             ↓              ↓
ExtractMetadata  →   StoreMetadata (Azure SQL)
```
### Azure Resources Used
Azure Blob Storage (to store images)

Azure Function App (Python, Durable Functions)

Azure SQL Database (to store extracted metadata)

Azure Application Insights (for logs)

Azure Storage Account (function triggers)

### Project Structure
```bash
ImagePipeline/
│
├── BlobTriggerFunction/           # Starts orchestration on blob upload
│   └── __init__.py
│
├── OrchestratorFunction/         # Coordinates steps
│   └── __init__.py
│
├── ExtractMetadata/              # Extracts image metadata
│   └── __init__.py
│   └── function.json
│
├── StoreMetadata/                # Inserts metadata into SQL
│   └── __init__.py
│
└── host.json                     # Function host config
```
#### Function Details
1. BlobTriggerFunction
```python
import logging
import azure.functions as func
import azure.durable_functions as df

async def main(blob: func.InputStream, starter: str):
    client = df.DurableOrchestrationClient(starter)
    input_data = {
        "blob_name": blob.name
    }
    instance_id = await client.start_new("OrchestratorFunction", None, input_data)
    logging.info(f"Started orchestration with ID = '{instance_id}'.")
```
Purpose: Triggers when a new blob is uploaded. Starts the durable function orchestration.

2. OrchestratorFunction
python
Copy
Edit
import azure.durable_functions as df
import base64
import logging
from azure.storage.blob import BlobServiceClient
import os

async def main(context: df.DurableOrchestrationContext):
    input_data = context.get_input()
    blob_name = input_data["blob_name"]

  # Step 1: Download blob content
    blob_conn_str = os.environ["AzureWebJobsStorage"]
    blob_service = BlobServiceClient.from_connection_string(blob_conn_str)
    container_name = os.environ["BlobContainer"]
    blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
    content = await blob_client.download_blob().readall()

    image_input = {
        "content": content,
        "name": blob_name
    }

    # Step 2: Call extract function
    metadata = await context.call_activity("ExtractMetadata", image_input)

    # Step 3: Store metadata in DB
    await context.call_activity("StoreMetadata", metadata)
    return metadata
Purpose: Calls ExtractMetadata, then StoreMetadata.

3. ExtractMetadata Function
```python
from PIL import Image
import io
import logging

def main(input_data: dict) -> dict:
    content = input_data['content']
    name = input_data['name']
    image = Image.open(io.BytesIO(content))
    width, height = image.size
    format = image.format
    size_kb = len(content) / 1024

    metadata = {
        "file_name": name,
        "size_kb": round(size_kb, 2),
        "width": width,
        "height": height,
        "format": format
    }
    logging.info(f"Extracted metadata: {metadata}")
    return metadata
```
Purpose: Uses PIL to extract image size, format, dimensions, and returns a metadata dictionary.

4. StoreMetadata Function
```python
import logging
import pyodbc
import os

def main(metadata: dict) -> None:
    conn_str = os.environ["SqlConnectionString"]
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ImageMetadata ([FileName], [SizeKB], [Width], [Height], [Format])
                VALUES (?, ?, ?, ?, ?)""",
                metadata["file_name"], metadata["size_kb"],
                metadata["width"], metadata["height"],
                metadata["format"]
            )
            conn.commit()
        logging.info("Metadata stored successfully.")
    except Exception as e:
        logging.error(f"Error storing metadata: {e}")
        raise
```
Purpose: Inserts extracted metadata into Azure SQL Database.

### SQL Table Definition
```sql
CREATE TABLE ImageMetadata (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    FileName NVARCHAR(255),
    SizeKB FLOAT,
    Width INT,
    Height INT,
    Format NVARCHAR(20)
);
```
### Troubleshooting & Fixes
Issue	Cause	Fix
❌ Blob trigger was calling Orchestrator instead of Extract directly	Designed to use Durable pattern for chaining	❗ It's intentional — Orchestrator handles chaining (Extract → Store)
❌ Invalid column name 'SizeKB' in SQL	Case mismatch or missing table	✅ Enclosed column names in square brackets: [SizeKB]
❌ No module named 'PIL'	Missing dependency	✅ Added Pillow to requirements.txt
❌ Blob content not accessible in orchestrator	Blob client not configured properly	✅ Used BlobServiceClient with correct connection string and container name
❌ Function not triggering	Wrong storage/container or misconfigured bindings	✅ Verified container name in local.settings.json and function.json

✅ Environment Configuration
local.settings.json
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<your-storage-conn-string>",
    "SqlConnectionString": "<your-sql-conn-string>",
    "BlobContainer": "image-container",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```
requirements.txt
```txt
azure-functions
azure-durable-functions
pillow
pyodbc
azure-storage-blob
```
### Final Test Output:
1. Uploaded image to Blob Storage container.
2. Blob trigger activated.
3. Orchestration started.
4. Extracted metadata:

```json
{
  "file_name": "test_image.jpg",
  "size_kb": 150.23,
  "width": 800,
  "height": 600,
  "format": "JPEG"
}
Successfully stored in Azure SQL Database under ImageMetadata.
```

### Screenshots
💡 Add the following screenshots:

Blob uploaded in Azure Storage

Azure Function Logs (Orchestrator + Activities)

Metadata visible in Azure SQL Database

Visual Studio Code Function App Structure

🏁 Conclusion
This lab demonstrates a powerful use of serverless architecture and Durable Functions to automate image processing workflows using Azure. It showcases integration between Blob Storage, Azure Functions, Durable Orchestration, and SQL Database.
