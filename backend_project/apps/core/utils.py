import os
import uuid
from datetime import datetime
from io import BytesIO
from minio import Minio
from django.conf import settings

def get_minio_client():
    return Minio(
        settings.MINIO_STORAGE_ENDPOINT,
        access_key=settings.MINIO_STORAGE_ACCESS_KEY,
        secret_key=settings.MINIO_STORAGE_SECRET_KEY,
        secure=settings.MINIO_STORAGE_SECURE
    )

def ensure_bucket_exists(client, bucket_name):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created successfully")

def upload_image_to_minio(image_data, filename, bucket_name=None):
    if bucket_name is None:
        bucket_name = settings.MINIO_STORAGE_BUCKET_NAME
    
    file_extension = os.path.splitext(filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    object_name = f"{timestamp}_{unique_id}{file_extension}"
    
    client = get_minio_client()
    ensure_bucket_exists(client, bucket_name)
    
    image_bytes = BytesIO(image_data)
    image_size = len(image_data)
    
    client.put_object(
        bucket_name,
        object_name,
        image_bytes,
        image_size,
        content_type=f'image/{file_extension[1:] if file_extension else "jpeg"}'
    )
    
    return bucket_name, object_name

def get_image_from_minio(bucket_name, object_name):
    client = get_minio_client()
    try:
        response = client.get_object(bucket_name, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except Exception as e:
        print(f"Error retrieving object from MinIO: {e}")
        return None