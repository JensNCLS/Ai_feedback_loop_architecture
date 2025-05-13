import os
import uuid
from datetime import datetime
from io import BytesIO
from minio import Minio
from django.conf import settings

def get_minio_client():
    """Create and return a MinIO client using settings from Django settings"""
    return Minio(
        settings.MINIO_STORAGE_ENDPOINT,
        access_key=settings.MINIO_STORAGE_ACCESS_KEY,
        secret_key=settings.MINIO_STORAGE_SECRET_KEY,
        secure=settings.MINIO_STORAGE_SECURE
    )

def ensure_bucket_exists(client, bucket_name):
    """Ensure the specified bucket exists, creating it if necessary"""
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created successfully")

def upload_image_to_minio(image_data, filename, bucket_name=None):
    """
    Upload an image to MinIO and return the object name.
    
    Args:
        image_data: Binary image data
        filename: Original filename
        bucket_name: MinIO bucket name (defaults to settings value if None)
        
    Returns:
        Tuple of (bucket_name, object_name)
    """
    if bucket_name is None:
        bucket_name = settings.MINIO_STORAGE_BUCKET_NAME
    
    # Create a unique object name to avoid collisions
    file_extension = os.path.splitext(filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    object_name = f"{timestamp}_{unique_id}{file_extension}"
    
    # Upload to MinIO
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
    """
    Retrieve image data from MinIO
    
    Args:
        bucket_name: MinIO bucket name
        object_name: Object name in the bucket
        
    Returns:
        Binary image data or None if not found
    """
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