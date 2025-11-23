"""
Model storage and versioning service for ML models.

This module handles saving, loading, and managing ML model versions with
metadata tracking and automatic cleanup of old versions.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import joblib

from app.core import get_logger, DatabaseError


logger = get_logger(__name__)


class ModelStorage:
    """Service for storing and managing ML models."""

    def __init__(self, base_path: str = "models"):
        """
        Initialize model storage.

        Args:
            base_path: Base directory for model storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model storage initialized at: {self.base_path}")

    def _get_model_dir(self, model_type: str, well_id: str) -> Path:
        """
        Get directory path for a specific model type and well.

        Args:
            model_type: Type of model (anomaly, predictive, performance)
            well_id: Well identifier

        Returns:
            Path to model directory
        """
        model_dir = self.base_path / model_type / well_id
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir

    def _generate_version_tag(self) -> str:
        """
        Generate timestamp-based version tag.

        Returns:
            Version tag string (e.g., "20251120_143000")
        """
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def save_model(
        self,
        model: Any,
        model_type: str,
        well_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save a trained model with metadata.

        Args:
            model: Trained model object
            model_type: Type of model (anomaly, predictive, performance)
            well_id: Well identifier
            metadata: Optional metadata dictionary

        Returns:
            Version tag of saved model

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            model_dir = self._get_model_dir(model_type, well_id)
            version = self._generate_version_tag()

            # Save model
            model_path = model_dir / f"{version}_model.pkl"
            joblib.dump(model, model_path, compress=3)

            # Save metadata
            if metadata is None:
                metadata = {}

            metadata.update({
                "model_type": model_type,
                "well_id": well_id,
                "version": version,
                "saved_at": datetime.utcnow().isoformat(),
                "model_file": model_path.name,
                "model_size_bytes": os.path.getsize(model_path),
            })

            metadata_path = model_dir / f"{version}_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            # Create "latest" symlink
            latest_model_link = model_dir / "latest_model.pkl"
            latest_metadata_link = model_dir / "latest_metadata.json"

            # Remove existing symlinks if they exist
            if latest_model_link.exists() or latest_model_link.is_symlink():
                latest_model_link.unlink()
            if latest_metadata_link.exists() or latest_metadata_link.is_symlink():
                latest_metadata_link.unlink()

            # Create new symlinks
            latest_model_link.symlink_to(model_path.name)
            latest_metadata_link.symlink_to(metadata_path.name)

            logger.info(
                f"Model saved successfully",
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                        "version": version,
                        "size_bytes": metadata["model_size_bytes"],
                    }
                }
            )

            # Cleanup old models (keep last 5 versions)
            self._cleanup_old_versions(model_dir, keep_versions=5)

            return version

        except Exception as e:
            logger.error(
                f"Failed to save model",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                    }
                }
            )
            raise DatabaseError(
                message="Failed to save model",
                operation="SAVE_MODEL",
                details={"model_type": model_type, "well_id": well_id}
            ) from e

    def load_model(
        self,
        model_type: str,
        well_id: str,
        version: Optional[str] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Load a trained model with metadata.

        Args:
            model_type: Type of model (anomaly, predictive, performance)
            well_id: Well identifier
            version: Specific version to load (default: latest)

        Returns:
            Tuple of (model, metadata)

        Raises:
            DatabaseError: If model not found or load fails
        """
        try:
            model_dir = self._get_model_dir(model_type, well_id)

            # Determine model path
            if version is None:
                model_path = model_dir / "latest_model.pkl"
                metadata_path = model_dir / "latest_metadata.json"
            else:
                model_path = model_dir / f"{version}_model.pkl"
                metadata_path = model_dir / f"{version}_metadata.json"

            # Check if model exists
            if not model_path.exists():
                raise DatabaseError(
                    message=f"Model not found: {model_type}/{well_id}",
                    operation="LOAD_MODEL",
                    details={
                        "model_type": model_type,
                        "well_id": well_id,
                        "version": version or "latest"
                    }
                )

            # Load model
            model = joblib.load(model_path)

            # Load metadata
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)

            logger.info(
                f"Model loaded successfully",
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                        "version": metadata.get("version", "unknown"),
                    }
                }
            )

            return model, metadata

        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to load model",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                        "version": version,
                    }
                }
            )
            raise DatabaseError(
                message="Failed to load model",
                operation="LOAD_MODEL",
                details={"model_type": model_type, "well_id": well_id}
            ) from e

    def model_exists(
        self,
        model_type: str,
        well_id: str,
        version: Optional[str] = None
    ) -> bool:
        """
        Check if a model exists.

        Args:
            model_type: Type of model
            well_id: Well identifier
            version: Specific version (default: latest)

        Returns:
            True if model exists, False otherwise
        """
        try:
            model_dir = self._get_model_dir(model_type, well_id)

            if version is None:
                model_path = model_dir / "latest_model.pkl"
            else:
                model_path = model_dir / f"{version}_model.pkl"

            return model_path.exists()

        except Exception as e:
            logger.warning(
                f"Error checking model existence",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                    }
                }
            )
            return False

    def list_versions(
        self,
        model_type: str,
        well_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all versions of a model.

        Args:
            model_type: Type of model
            well_id: Well identifier

        Returns:
            List of metadata dictionaries for all versions
        """
        try:
            model_dir = self._get_model_dir(model_type, well_id)
            versions = []

            # Find all metadata files
            for metadata_file in sorted(model_dir.glob("*_metadata.json"), reverse=True):
                if metadata_file.name != "latest_metadata.json":
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                        versions.append(metadata)

            logger.info(
                f"Listed {len(versions)} model versions",
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                        "count": len(versions),
                    }
                }
            )

            return versions

        except Exception as e:
            logger.error(
                f"Failed to list model versions",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                    }
                }
            )
            return []

    def delete_model(
        self,
        model_type: str,
        well_id: str,
        version: str
    ) -> bool:
        """
        Delete a specific model version.

        Args:
            model_type: Type of model
            well_id: Well identifier
            version: Version to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            model_dir = self._get_model_dir(model_type, well_id)
            model_path = model_dir / f"{version}_model.pkl"
            metadata_path = model_dir / f"{version}_metadata.json"

            deleted = False
            if model_path.exists():
                model_path.unlink()
                deleted = True

            if metadata_path.exists():
                metadata_path.unlink()
                deleted = True

            if deleted:
                logger.info(
                    f"Model deleted",
                    extra={
                        "extra_fields": {
                            "model_type": model_type,
                            "well_id": well_id,
                            "version": version,
                        }
                    }
                )

            return deleted

        except Exception as e:
            logger.error(
                f"Failed to delete model",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                        "version": version,
                    }
                }
            )
            return False

    def _cleanup_old_versions(
        self,
        model_dir: Path,
        keep_versions: int = 5
    ) -> int:
        """
        Cleanup old model versions, keeping only the most recent.

        Args:
            model_dir: Directory containing model versions
            keep_versions: Number of versions to keep

        Returns:
            Number of versions deleted
        """
        try:
            # Find all model files (excluding symlinks)
            model_files = [
                f for f in model_dir.glob("*_model.pkl")
                if not f.is_symlink() and f.name != "latest_model.pkl"
            ]

            # Sort by modification time (newest first)
            model_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Delete old versions
            deleted_count = 0
            for old_model in model_files[keep_versions:]:
                version = old_model.stem.replace("_model", "")
                metadata_file = model_dir / f"{version}_metadata.json"

                old_model.unlink()
                if metadata_file.exists():
                    metadata_file.unlink()

                deleted_count += 1

            if deleted_count > 0:
                logger.info(
                    f"Cleaned up {deleted_count} old model versions",
                    extra={
                        "extra_fields": {
                            "model_dir": str(model_dir),
                            "deleted_count": deleted_count,
                        }
                    }
                )

            return deleted_count

        except Exception as e:
            logger.warning(
                f"Error during model cleanup",
                exc_info=e,
                extra={"extra_fields": {"model_dir": str(model_dir)}}
            )
            return 0

    def get_model_info(
        self,
        model_type: str,
        well_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about the latest model.

        Args:
            model_type: Type of model
            well_id: Well identifier

        Returns:
            Model metadata dictionary or None if not found
        """
        try:
            model_dir = self._get_model_dir(model_type, well_id)
            metadata_path = model_dir / "latest_metadata.json"

            if not metadata_path.exists():
                return None

            with open(metadata_path, "r") as f:
                return json.load(f)

        except Exception as e:
            logger.warning(
                f"Failed to get model info",
                exc_info=e,
                extra={
                    "extra_fields": {
                        "model_type": model_type,
                        "well_id": well_id,
                    }
                }
            )
            return None
