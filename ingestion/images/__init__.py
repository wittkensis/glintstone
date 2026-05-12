"""Image ingestion utilities — fetcher, thumbnailer, CDLI HTML parser.

Used by both:
- ``ingestion/connectors/cdli_images.py`` (background backfill)
- ``api/services/image_ondemand.py`` (lazy on-demand cache fill)
- ``ops/scripts/upload_local_images.py`` (one-time bulk upload of pre-downloaded set)
"""
