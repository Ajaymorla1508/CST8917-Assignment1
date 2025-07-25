import os
import io
import logging
from azure.storage.blob import BlobServiceClient
from PIL import Image

def main(input_data: dict) -> dict:
    blob_name = input_data.get('blob_name')
    if not blob_name:
        raise ValueError("Missing 'blob_name' in input data")

    connect_str = os.getenv("AzureWebJobsStorage")
    if not connect_str:
        raise ValueError("Missing AzureWebJobsStorage environment variable")

    # Split blob_name into container and blob path
    container_name = blob_name.split('/')[0]  # e.g., 'images-input'
    blob_path = '/'.join(blob_name.split('/')[1:])  # e.g., 'pets.jpeg'

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)

    # Download blob content as bytes
    blob_bytes = blob_client.download_blob().readall()

    # Open image and extract metadata
    image = Image.open(io.BytesIO(blob_bytes))
    width, height = image.size
    format = image.format
    size_kb = len(blob_bytes) / 1024

    metadata = {
        "file_name": blob_path,
        "size_kb": round(size_kb, 2),
        "width": width,
        "height": height,
        "format": format
    }

    logging.info(f"Extracted metadata: {metadata}")
    return metadata

