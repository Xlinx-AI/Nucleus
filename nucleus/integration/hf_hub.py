"""
HfHub for nucleus: manage models and datasets on HuggingFace Hub.
Handles upload, download, info, tags, validation, async, with logging.
If your AI stack needs to touch HuggingFace, this is your bridge.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, List

try:
    from huggingface_hub import (
        create_repo,
        upload_file,
        upload_folder,
        hf_hub_download,
        snapshot_download,
        HfApi,
    )
except ImportError:
    raise ImportError("huggingface_hub is not installed. pip install huggingface_hub")

class HfHub:
    """
    HuggingFace Hub manager for nucleus. Upload/download/check models, datasets, info, tags.
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("HF_TOKEN")
        self.api = HfApi()
        self.logger = logging.getLogger("HfHub")
        if self.token:
            self.api.set_access_token(self.token)

    def download_model(self, repo_id: str, filename: Optional[str] = None) -> str:
        try:
            if filename:
                path = hf_hub_download(repo_id=repo_id, filename=filename)
            else:
                path = snapshot_download(repo_id)
            self.logger.info(f"Downloaded {repo_id} to {path}")
            return path
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise

    def upload_model(self, repo_id: str, local_path: str, repo_type: str = "model") -> bool:
        try:
            create_repo(repo_id=repo_id, repo_type=repo_type)
            if os.path.isfile(local_path):
                upload_file(
                    path_or_fileobj=local_path,
                    path_in_repo=os.path.basename(local_path),
                    repo_id=repo_id,
                )
            else:
                upload_folder(
                    folder_path=local_path,
                    repo_id=repo_id,
                    repo_type=repo_type
                )
            return True
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            return False

    def get_model_list(self, filter_criteria: Optional[Dict] = None) -> List[Dict]:
        try:
            models = self.api.list_models(filter=filter_criteria)
            return [model.to_dict() for model in models]
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []

    def get_model_tags(self, repo_id: str) -> List[str]:
        try:
            info = self.api.model_info(repo_id)
            return info.tags
        except Exception as e:
            self.logger.error(f"Failed to get tags: {e}")
            return []

    def validate_model(self, repo_id: str, expected_files: List[str]) -> bool:
        try:
            files = self.api.list_repo_files(repo_id)
            missing = set(expected_files) - set(files)
            if missing:
                self.logger.warning(f"Missing files: {missing}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False

    def get_model_info(self, model_id: str) -> Dict:
        try:
            info = self.api.model_info(model_id)
            return info.to_dict()
        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return {}

    async def download_model_async(self, *args, **kwargs):
        return await asyncio.to_thread(self.download_model, *args, **kwargs)

    async def upload_model_async(self, *args, **kwargs):
        return await asyncio.to_thread(self.upload_model, *args, **kwargs)