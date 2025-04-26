from minio import Minio
from minio.error import S3Error
from django.conf import settings

class MinioClient:
    def __init__(self, endpoint, access_key, secret_key, secure=False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

    def upload_file(self, bucket_name, file_path, object_name):
        try:
            self.client.fput_object(bucket_name, object_name, file_path)
            print(f"File {file_path} uploaded to bucket {bucket_name} as {object_name}.")
        except S3Error as e:
            print(f"Error uploading file: {e}")

    def download_file(self, bucket_name, object_name, file_path):
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            print(f"File {object_name} downloaded from bucket {bucket_name} to {file_path}.")
        except S3Error as e:
            print(f"Error downloading file: {e}")

    def list_objects(self, bucket_name):
        try:
            objects = self.client.list_objects(bucket_name)
            for obj in objects:
                print(obj.object_name)
        except S3Error as e:
            print(f"Error listing objects: {e}")

def initialize_minio_bucket():
    """
    Initialize the MinIO bucket if it doesn't exist.
    """
    minio_client = MinioClient(
        endpoint=settings.MINIO_STORAGE_ENDPOINT,
        access_key=settings.MINIO_STORAGE_ACCESS_KEY,
        secret_key=settings.MINIO_STORAGE_SECRET_KEY,
        secure=settings.MINIO_STORAGE_SECURE
    )

    try:
        if not minio_client.client.bucket_exists(settings.MINIO_STORAGE_BUCKET_NAME):
            minio_client.client.make_bucket(settings.MINIO_STORAGE_BUCKET_NAME)
            print(f"Bucket '{settings.MINIO_STORAGE_BUCKET_NAME}' created successfully.")
        else:
            print(f"Bucket '{settings.MINIO_STORAGE_BUCKET_NAME}' already exists.")
    except Exception as e:
        print(f"Error initializing MinIO bucket: {e}")