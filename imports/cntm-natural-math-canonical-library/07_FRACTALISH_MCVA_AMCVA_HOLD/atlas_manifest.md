# Atlas Manifest Strategy

The atlas should grow through manifests first, not through unreviewed file drops.

## Required Fields

- `id`
- `title`
- `domain`
- `subdomain`
- `source_url`
- `source_owner`
- `license_status`
- `license_note`
- `modality`
- `morphology_tags`
- `amcva_boundary_case`
- `notes`

## License Rule

If license status is unresolved, publish only the manifest entry with:

`license_status: license unresolved`

Do not publish the underlying asset.
