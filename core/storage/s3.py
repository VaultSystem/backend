import aioboto3

from core.settings import settings

from .base import Storage


class S3Storage(Storage):
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
        self.region = settings.AWS_S3_REGION_NAME

    async def upload(self, file_name: str, data: bytes) -> str:
        async with self.session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region,
        ) as s3:
            await s3.put_object(
                Bucket=self.bucket,
                Key=file_name,
                Body=data,
            )
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{file_name}"

    async def download(self, file_name: str) -> bytes:
        session = aioboto3.Session()

        async with session.client("s3") as s3:
            obj = await s3.get_object(Bucket=self.bucket, Key=file_name)
            return await obj["Body"].read()

    async def delete(self, file_name: str):
        session = aioboto3.Session()

        async with session.client("s3") as s3:
            await s3.delete_object(Bucket=self.bucket, Key=file_name)
