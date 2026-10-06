import logging

from django.db import transaction

logger = logging.getLogger(__name__)


def delete_inspection(inspection):
    """Delete an inspection and its photo.

    An asset that was created automatically and has no inspections left would
    only be an empty pin on the map, so it is removed too. Assets someone named
    or curated are always kept.

    Returns (asset_id, asset_removed). asset_id is None if it had no asset.
    """
    asset = inspection.infrastructure
    asset_id = asset.pk if asset is not None else None
    image = inspection.image
    asset_removed = False

    with transaction.atomic():
        inspection.delete()
        if (
            asset is not None
            and asset.auto_created
            and not asset.inspections.exists()
        ):
            asset.delete()
            asset_removed = True

    # Remove the stored photo. A failure here must not undo the delete.
    try:
        image.delete(save=False)
    except Exception:
        logger.exception("Could not remove image file for deleted inspection")

    return asset_id, asset_removed