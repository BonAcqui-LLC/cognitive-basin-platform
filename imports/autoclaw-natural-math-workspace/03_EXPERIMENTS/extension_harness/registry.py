"""Stage 2 Extension Harness — Extension Registry."""

from .errors import ExtensionRegistrationError
from .manifest import ExtensionManifest


class ExtensionRegistry:
    """Registry of loaded extensions with hook dispatch."""

    def __init__(self):
        self._extensions = []
        self._by_key = {}

    def register(self, extension, manifest):
        """Register an extension module with its validated manifest.

        Args:
            extension: The extension module/object implementing hooks.
            manifest: A validated ExtensionManifest instance.

        Raises:
            ExtensionRegistrationError on duplicate or invalid manifest.
        """
        if not isinstance(manifest, ExtensionManifest):
            raise ExtensionRegistrationError(
                "manifest must be an ExtensionManifest instance"
            )

        key = (manifest.extension_id, manifest.extension_version)

        if key in self._by_key:
            existing = self._by_key[key]
            raise ExtensionRegistrationError(
                f"Duplicate extension {manifest.extension_id!r} "
                f"version {manifest.extension_version!r} "
                f"(already registered as {existing['manifest'].extension_name!r})"
            )

        entry = {
            "extension": extension,
            "manifest": manifest,
        }

        self._extensions.append(entry)
        self._by_key[key] = entry

    def get_all(self):
        """Return all registered (extension, manifest) pairs."""
        return [(entry["extension"], entry["manifest"]) for entry in self._extensions]

    def get_by_id(self, ext_id):
        """Return all entries for a given extension_id."""
        results = []
        for entry in self._extensions:
            if entry["manifest"].extension_id == ext_id:
                results.append((entry["extension"], entry["manifest"]))
        return results

    def get_hooks(self, hook_name):
        """Return all extension modules that implement *hook_name*.

        Each item is (extension_module, manifest).
        """
        results = []
        for entry in self._extensions:
            ext = entry["extension"]
            if hasattr(ext, hook_name) and callable(getattr(ext, hook_name)):
                results.append((ext, entry["manifest"]))
        return results

    def __len__(self):
        return len(self._extensions)

    def __repr__(self):
        ids = [e["manifest"].extension_id for e in self._extensions]
        return f"ExtensionRegistry({ids})"
