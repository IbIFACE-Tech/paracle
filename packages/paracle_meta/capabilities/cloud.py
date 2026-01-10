"""
Cloud Capability - AWS, GCP, and Azure cloud service integration.

Provides unified interface for cloud operations:
- Object storage (S3, GCS, Azure Blob)
- Serverless functions (Lambda, Cloud Functions, Azure Functions)
- Container services (ECS, Cloud Run, ACI)
- Secrets management (Secrets Manager, Secret Manager, Key Vault)
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .base import BaseCapability, CapabilityResult


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


@dataclass
class CloudConfig:
    """Configuration for cloud capability."""

    # AWS settings
    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_profile: str | None = None

    # GCP settings
    gcp_project: str | None = None
    gcp_credentials_file: str | None = None
    gcp_region: str = "us-central1"

    # Azure settings
    azure_subscription_id: str | None = None
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None
    azure_resource_group: str | None = None

    # General settings
    default_provider: CloudProvider = CloudProvider.AWS
    timeout: int = 60


@dataclass
class StorageObject:
    """Represents a cloud storage object."""

    key: str
    size: int = 0
    last_modified: str | None = None
    etag: str | None = None
    content_type: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class CloudCapability(BaseCapability):
    """
    Cloud services capability for AWS, GCP, and Azure.

    Provides unified interface for:
    - Object storage operations
    - Serverless function invocation
    - Container service management
    - Secrets management

    Example:
        capability = CloudCapability(config=CloudConfig(
            default_provider=CloudProvider.AWS,
            aws_region="us-west-2"
        ))

        # Upload to S3
        result = await capability.storage_put(
            bucket="my-bucket",
            key="data/file.json",
            data='{"hello": "world"}'
        )

        # Invoke Lambda
        result = await capability.function_invoke(
            name="my-function",
            payload={"action": "process"}
        )
    """

    name = "cloud"
    description = "AWS, GCP, and Azure cloud service operations"

    def __init__(self, config: CloudConfig | None = None):
        """Initialize cloud capability."""
        self.config = config or CloudConfig()
        self._clients: dict[str, Any] = {}
        self._check_availability()

    def _check_availability(self) -> None:
        """Check which cloud SDKs are available."""
        self._aws_available = False
        self._gcp_available = False
        self._azure_available = False

        try:
            import boto3  # noqa: F401

            self._aws_available = True
        except ImportError:
            pass

        try:
            from google.cloud import storage  # noqa: F401

            self._gcp_available = True
        except ImportError:
            pass

        try:
            from azure.storage.blob import BlobServiceClient  # noqa: F401

            self._azure_available = True
        except ImportError:
            pass

    @property
    def is_available(self) -> bool:
        """Check if at least one cloud SDK is available."""
        return self._aws_available or self._gcp_available or self._azure_available

    def _get_aws_client(self, service: str) -> Any:
        """Get or create AWS client."""
        if not self._aws_available:
            raise RuntimeError("boto3 not installed. Install with: pip install boto3")

        import boto3

        cache_key = f"aws_{service}"
        if cache_key not in self._clients:
            session_kwargs = {}
            if self.config.aws_profile:
                session_kwargs["profile_name"] = self.config.aws_profile
            if self.config.aws_access_key_id:
                session_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
                session_kwargs["aws_secret_access_key"] = (
                    self.config.aws_secret_access_key
                )

            session = boto3.Session(**session_kwargs)
            self._clients[cache_key] = session.client(
                service, region_name=self.config.aws_region
            )

        return self._clients[cache_key]

    def _get_gcp_storage_client(self) -> Any:
        """Get or create GCP storage client."""
        if not self._gcp_available:
            raise RuntimeError(
                "google-cloud-storage not installed. "
                "Install with: pip install google-cloud-storage"
            )

        from google.cloud import storage

        if "gcp_storage" not in self._clients:
            kwargs = {}
            if self.config.gcp_project:
                kwargs["project"] = self.config.gcp_project
            if self.config.gcp_credentials_file:
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_file(
                    self.config.gcp_credentials_file
                )
                kwargs["credentials"] = credentials

            self._clients["gcp_storage"] = storage.Client(**kwargs)

        return self._clients["gcp_storage"]

    def _get_azure_blob_client(self) -> Any:
        """Get or create Azure Blob client."""
        if not self._azure_available:
            raise RuntimeError(
                "azure-storage-blob not installed. "
                "Install with: pip install azure-storage-blob"
            )

        from azure.identity import ClientSecretCredential
        from azure.storage.blob import BlobServiceClient

        if "azure_blob" not in self._clients:
            # Try connection string first
            conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
            if conn_str:
                self._clients["azure_blob"] = BlobServiceClient.from_connection_string(
                    conn_str
                )
            elif self.config.azure_client_id:
                credential = ClientSecretCredential(
                    tenant_id=self.config.azure_tenant_id,
                    client_id=self.config.azure_client_id,
                    client_secret=self.config.azure_client_secret,
                )
                account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL", "")
                self._clients["azure_blob"] = BlobServiceClient(
                    account_url, credential=credential
                )
            else:
                raise RuntimeError(
                    "Azure credentials not configured. "
                    "Set AZURE_STORAGE_CONNECTION_STRING or provide client credentials."
                )

        return self._clients["azure_blob"]

    async def execute(
        self,
        operation: str,
        provider: str | None = None,
        **kwargs: Any,
    ) -> CapabilityResult:
        """
        Execute a cloud operation.

        Args:
            operation: Operation to perform (storage_get, storage_put, etc.)
            provider: Cloud provider (aws, gcp, azure)
            **kwargs: Operation-specific parameters

        Returns:
            CapabilityResult with operation output
        """
        provider = provider or self.config.default_provider.value

        operations = {
            # Storage
            "storage_get": self._storage_get,
            "storage_put": self._storage_put,
            "storage_delete": self._storage_delete,
            "storage_list": self._storage_list,
            # Functions
            "function_invoke": self._function_invoke,
            "function_list": self._function_list,
            # Secrets
            "secret_get": self._secret_get,
            "secret_put": self._secret_put,
            # Container
            "container_run": self._container_run,
        }

        if operation not in operations:
            return CapabilityResult(
                success=False,
                output={"error": f"Unknown operation: {operation}"},
                error=f"Supported operations: {list(operations.keys())}",
            )

        try:
            result = await operations[operation](provider, **kwargs)
            return CapabilityResult(success=True, output=result)
        except Exception as e:
            return CapabilityResult(
                success=False, output={"error": str(e)}, error=str(e)
            )

    # =========================================================================
    # Storage Operations
    # =========================================================================

    async def _storage_get(
        self, provider: str, bucket: str, key: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Get object from cloud storage."""
        if provider == "aws":
            return await self._aws_s3_get(bucket, key)
        elif provider == "gcp":
            return await self._gcp_storage_get(bucket, key)
        elif provider == "azure":
            return await self._azure_blob_get(bucket, key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _aws_s3_get(self, bucket: str, key: str) -> dict[str, Any]:
        """Get object from S3."""
        s3 = self._get_aws_client("s3")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: s3.get_object(Bucket=bucket, Key=key)
        )

        body = await loop.run_in_executor(None, lambda: response["Body"].read())

        return {
            "data": body.decode("utf-8"),
            "content_type": response.get("ContentType"),
            "last_modified": str(response.get("LastModified")),
            "etag": response.get("ETag"),
            "size": response.get("ContentLength"),
        }

    async def _gcp_storage_get(self, bucket: str, key: str) -> dict[str, Any]:
        """Get object from GCS."""
        client = self._get_gcp_storage_client()

        loop = asyncio.get_event_loop()

        def get_blob():
            bucket_obj = client.bucket(bucket)
            blob = bucket_obj.blob(key)
            data = blob.download_as_string()
            return {
                "data": data.decode("utf-8"),
                "content_type": blob.content_type,
                "size": blob.size,
                "updated": str(blob.updated),
            }

        return await loop.run_in_executor(None, get_blob)

    async def _azure_blob_get(self, container: str, blob_name: str) -> dict[str, Any]:
        """Get blob from Azure."""
        client = self._get_azure_blob_client()

        loop = asyncio.get_event_loop()

        def get_blob():
            blob_client = client.get_blob_client(container=container, blob=blob_name)
            data = blob_client.download_blob().readall()
            properties = blob_client.get_blob_properties()
            return {
                "data": data.decode("utf-8"),
                "content_type": properties.content_settings.content_type,
                "size": properties.size,
                "last_modified": str(properties.last_modified),
            }

        return await loop.run_in_executor(None, get_blob)

    async def _storage_put(
        self,
        provider: str,
        bucket: str,
        key: str,
        data: str | bytes,
        content_type: str = "application/octet-stream",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Put object to cloud storage."""
        if isinstance(data, str):
            data = data.encode("utf-8")

        if provider == "aws":
            return await self._aws_s3_put(bucket, key, data, content_type)
        elif provider == "gcp":
            return await self._gcp_storage_put(bucket, key, data, content_type)
        elif provider == "azure":
            return await self._azure_blob_put(bucket, key, data, content_type)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _aws_s3_put(
        self, bucket: str, key: str, data: bytes, content_type: str
    ) -> dict[str, Any]:
        """Put object to S3."""
        s3 = self._get_aws_client("s3")

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: s3.put_object(
                Bucket=bucket, Key=key, Body=data, ContentType=content_type
            ),
        )

        return {
            "success": True,
            "etag": response.get("ETag"),
            "version_id": response.get("VersionId"),
        }

    async def _gcp_storage_put(
        self, bucket: str, key: str, data: bytes, content_type: str
    ) -> dict[str, Any]:
        """Put object to GCS."""
        client = self._get_gcp_storage_client()

        loop = asyncio.get_event_loop()

        def upload_blob():
            bucket_obj = client.bucket(bucket)
            blob = bucket_obj.blob(key)
            blob.upload_from_string(data, content_type=content_type)
            return {
                "success": True,
                "generation": blob.generation,
                "md5_hash": blob.md5_hash,
            }

        return await loop.run_in_executor(None, upload_blob)

    async def _azure_blob_put(
        self, container: str, blob_name: str, data: bytes, content_type: str
    ) -> dict[str, Any]:
        """Put blob to Azure."""
        from azure.storage.blob import ContentSettings

        client = self._get_azure_blob_client()

        loop = asyncio.get_event_loop()

        def upload_blob():
            blob_client = client.get_blob_client(container=container, blob=blob_name)
            result = blob_client.upload_blob(
                data,
                content_settings=ContentSettings(content_type=content_type),
                overwrite=True,
            )
            return {"success": True, "etag": result.get("etag")}

        return await loop.run_in_executor(None, upload_blob)

    async def _storage_delete(
        self, provider: str, bucket: str, key: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Delete object from cloud storage."""
        loop = asyncio.get_event_loop()

        if provider == "aws":
            s3 = self._get_aws_client("s3")
            await loop.run_in_executor(
                None, lambda: s3.delete_object(Bucket=bucket, Key=key)
            )
        elif provider == "gcp":
            client = self._get_gcp_storage_client()
            await loop.run_in_executor(
                None, lambda: client.bucket(bucket).blob(key).delete()
            )
        elif provider == "azure":
            client = self._get_azure_blob_client()
            await loop.run_in_executor(
                None,
                lambda: client.get_blob_client(container=bucket, blob=key).delete_blob(
                    delete_snapshots="include"
                ),
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return {"success": True, "deleted": key}

    async def _storage_list(
        self,
        provider: str,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """List objects in cloud storage."""
        loop = asyncio.get_event_loop()

        if provider == "aws":
            s3 = self._get_aws_client("s3")
            response = await loop.run_in_executor(
                None,
                lambda: s3.list_objects_v2(
                    Bucket=bucket, Prefix=prefix, MaxKeys=max_keys
                ),
            )
            objects = [
                StorageObject(
                    key=obj["Key"],
                    size=obj.get("Size", 0),
                    last_modified=str(obj.get("LastModified")),
                    etag=obj.get("ETag"),
                ).__dict__
                for obj in response.get("Contents", [])
            ]
        elif provider == "gcp":
            client = self._get_gcp_storage_client()

            def list_blobs():
                bucket_obj = client.bucket(bucket)
                blobs = bucket_obj.list_blobs(prefix=prefix, max_results=max_keys)
                return [
                    StorageObject(
                        key=blob.name,
                        size=blob.size or 0,
                        last_modified=str(blob.updated),
                        content_type=blob.content_type,
                    ).__dict__
                    for blob in blobs
                ]

            objects = await loop.run_in_executor(None, list_blobs)
        elif provider == "azure":
            client = self._get_azure_blob_client()

            def list_blobs():
                container_client = client.get_container_client(bucket)
                blobs = container_client.list_blobs(name_starts_with=prefix)
                result = []
                for i, blob in enumerate(blobs):
                    if i >= max_keys:
                        break
                    result.append(
                        StorageObject(
                            key=blob.name,
                            size=blob.size or 0,
                            last_modified=str(blob.last_modified),
                            content_type=blob.content_settings.content_type
                            if blob.content_settings
                            else None,
                        ).__dict__
                    )
                return result

            objects = await loop.run_in_executor(None, list_blobs)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return {"objects": objects, "count": len(objects)}

    # =========================================================================
    # Serverless Functions
    # =========================================================================

    async def _function_invoke(
        self,
        provider: str,
        name: str,
        payload: dict | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Invoke a serverless function."""
        loop = asyncio.get_event_loop()

        if provider == "aws":
            lambda_client = self._get_aws_client("lambda")
            response = await loop.run_in_executor(
                None,
                lambda: lambda_client.invoke(
                    FunctionName=name,
                    InvocationType=kwargs.get("invocation_type", "RequestResponse"),
                    Payload=json.dumps(payload or {}),
                ),
            )
            result_payload = await loop.run_in_executor(
                None, lambda: response["Payload"].read()
            )
            return {
                "status_code": response.get("StatusCode"),
                "result": json.loads(result_payload) if result_payload else None,
                "function_error": response.get("FunctionError"),
            }
        elif provider == "gcp":
            # GCP Cloud Functions via HTTP
            raise NotImplementedError(
                "GCP Cloud Functions invocation requires HTTP endpoint. "
                "Use HTTP capability instead."
            )
        elif provider == "azure":
            # Azure Functions via HTTP
            raise NotImplementedError(
                "Azure Functions invocation requires HTTP endpoint. "
                "Use HTTP capability instead."
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _function_list(
        self, provider: str, **kwargs: Any
    ) -> dict[str, list[dict[str, Any]]]:
        """List serverless functions."""
        loop = asyncio.get_event_loop()

        if provider == "aws":
            lambda_client = self._get_aws_client("lambda")
            response = await loop.run_in_executor(
                None, lambda: lambda_client.list_functions(MaxItems=50)
            )
            functions = [
                {
                    "name": fn["FunctionName"],
                    "runtime": fn.get("Runtime"),
                    "memory": fn.get("MemorySize"),
                    "timeout": fn.get("Timeout"),
                    "last_modified": fn.get("LastModified"),
                }
                for fn in response.get("Functions", [])
            ]
            return {"functions": functions}
        else:
            raise NotImplementedError(
                f"Function listing not implemented for {provider}"
            )

    # =========================================================================
    # Secrets Management
    # =========================================================================

    async def _secret_get(
        self, provider: str, name: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Get a secret from cloud secrets manager."""
        loop = asyncio.get_event_loop()

        if provider == "aws":
            sm = self._get_aws_client("secretsmanager")
            response = await loop.run_in_executor(
                None,
                lambda: sm.get_secret_value(SecretId=name),
            )
            return {
                "name": response.get("Name"),
                "value": response.get("SecretString"),
                "version_id": response.get("VersionId"),
            }
        elif provider == "gcp":
            # Requires google-cloud-secret-manager
            try:
                from google.cloud import secretmanager
            except ImportError:
                raise RuntimeError(
                    "google-cloud-secret-manager not installed. "
                    "Install with: pip install google-cloud-secret-manager"
                )

            def get_secret():
                client = secretmanager.SecretManagerServiceClient()
                version = kwargs.get("version", "latest")
                secret_name = (
                    f"projects/{self.config.gcp_project}/secrets/{name}/versions/{version}"
                )
                response = client.access_secret_version(name=secret_name)
                return {
                    "name": name,
                    "value": response.payload.data.decode("utf-8"),
                }

            return await loop.run_in_executor(None, get_secret)
        elif provider == "azure":
            # Requires azure-keyvault-secrets
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient
            except ImportError:
                raise RuntimeError(
                    "azure-keyvault-secrets not installed. "
                    "Install with: pip install azure-keyvault-secrets azure-identity"
                )

            def get_secret():
                vault_url = kwargs.get(
                    "vault_url", os.environ.get("AZURE_VAULT_URL", "")
                )
                credential = DefaultAzureCredential()
                client = SecretClient(vault_url=vault_url, credential=credential)
                secret = client.get_secret(name)
                return {
                    "name": secret.name,
                    "value": secret.value,
                    "version": secret.properties.version,
                }

            return await loop.run_in_executor(None, get_secret)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _secret_put(
        self, provider: str, name: str, value: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Store a secret in cloud secrets manager."""
        loop = asyncio.get_event_loop()

        if provider == "aws":
            sm = self._get_aws_client("secretsmanager")

            async def put_or_create():
                try:
                    return await loop.run_in_executor(
                        None,
                        lambda: sm.put_secret_value(SecretId=name, SecretString=value),
                    )
                except sm.exceptions.ResourceNotFoundException:
                    return await loop.run_in_executor(
                        None,
                        lambda: sm.create_secret(Name=name, SecretString=value),
                    )

            response = await put_or_create()
            return {"success": True, "name": response.get("Name")}
        else:
            raise NotImplementedError(f"Secret storage not implemented for {provider}")

    # =========================================================================
    # Container Services
    # =========================================================================

    async def _container_run(
        self,
        provider: str,
        image: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run a container in cloud container service."""
        loop = asyncio.get_event_loop()

        if provider == "aws":
            # ECS Fargate
            ecs = self._get_aws_client("ecs")

            task_def = kwargs.get("task_definition")
            cluster = kwargs.get("cluster", "default")
            subnets = kwargs.get("subnets", [])
            security_groups = kwargs.get("security_groups", [])

            if not task_def:
                raise ValueError("task_definition is required for ECS")

            response = await loop.run_in_executor(
                None,
                lambda: ecs.run_task(
                    cluster=cluster,
                    taskDefinition=task_def,
                    launchType="FARGATE",
                    networkConfiguration={
                        "awsvpcConfiguration": {
                            "subnets": subnets,
                            "securityGroups": security_groups,
                            "assignPublicIp": "ENABLED",
                        }
                    },
                ),
            )

            tasks = response.get("tasks", [])
            return {
                "success": True,
                "tasks": [
                    {
                        "task_arn": t.get("taskArn"),
                        "status": t.get("lastStatus"),
                    }
                    for t in tasks
                ],
            }
        else:
            raise NotImplementedError(
                f"Container run not implemented for {provider}. "
                "Consider using ContainerCapability for local Docker."
            )

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def storage_get(
        self, bucket: str, key: str, provider: str | None = None
    ) -> CapabilityResult:
        """Get object from cloud storage."""
        return await self.execute(
            "storage_get", provider=provider, bucket=bucket, key=key
        )

    async def storage_put(
        self,
        bucket: str,
        key: str,
        data: str | bytes,
        content_type: str = "application/octet-stream",
        provider: str | None = None,
    ) -> CapabilityResult:
        """Put object to cloud storage."""
        return await self.execute(
            "storage_put",
            provider=provider,
            bucket=bucket,
            key=key,
            data=data,
            content_type=content_type,
        )

    async def storage_delete(
        self, bucket: str, key: str, provider: str | None = None
    ) -> CapabilityResult:
        """Delete object from cloud storage."""
        return await self.execute(
            "storage_delete", provider=provider, bucket=bucket, key=key
        )

    async def storage_list(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
        provider: str | None = None,
    ) -> CapabilityResult:
        """List objects in cloud storage."""
        return await self.execute(
            "storage_list",
            provider=provider,
            bucket=bucket,
            prefix=prefix,
            max_keys=max_keys,
        )

    async def function_invoke(
        self,
        name: str,
        payload: dict | None = None,
        provider: str | None = None,
    ) -> CapabilityResult:
        """Invoke a serverless function."""
        return await self.execute(
            "function_invoke", provider=provider, name=name, payload=payload
        )

    async def secret_get(
        self, name: str, provider: str | None = None, **kwargs: Any
    ) -> CapabilityResult:
        """Get a secret from cloud secrets manager."""
        return await self.execute("secret_get", provider=provider, name=name, **kwargs)

    async def secret_put(
        self, name: str, value: str, provider: str | None = None
    ) -> CapabilityResult:
        """Store a secret in cloud secrets manager."""
        return await self.execute(
            "secret_put", provider=provider, name=name, value=value
        )

    async def run(self, operation: str, **kwargs: Any) -> CapabilityResult:
        """Run a cloud operation (alias for execute)."""
        return await self.execute(operation, **kwargs)
