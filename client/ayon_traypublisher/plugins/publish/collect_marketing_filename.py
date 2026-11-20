import pyblish.api

from ayon_traypublisher.marketing_name import parse_marketing_filename


_MARKETING_DATA_KEYS = (
    "marketingRegion",
    "marketingFormat",
    "aspectRatio",
)


class CollectMarketingFilenameMetadata(pyblish.api.InstancePlugin):
    """Fill marketing region, format and aspect ratio from the filename.

    Values already stored on the representation are left unchanged.
    ``marketingGenerated`` is not set. This is the Tray Publisher counterpart
    of the Cavalry comp-imprint collector, which cannot run without a scene.
    """

    label = "Collect Marketing Filename Metadata"
    order = pyblish.api.CollectorOrder - 0.48
    families = ["simple.instance"]
    hosts = ["traypublisher"]

    def process(self, instance):
        for repre in instance.data.get("representations") or []:
            parsed = {}
            for candidate in _name_candidates(repre):
                for key, value in parse_marketing_filename(candidate).items():
                    parsed.setdefault(key, value)

            if not parsed:
                self.log.debug(
                    "No marketing metadata in representation '%s'.",
                    repre.get("name"),
                )
                continue

            data = repre.get("data")
            if data is None:
                data = {}
            elif not isinstance(data, dict):
                self.log.debug(
                    "Skipping marketing metadata for '%s'; data is %s.",
                    repre.get("name"),
                    type(data).__name__,
                )
                continue

            applied = []
            for key in _MARKETING_DATA_KEYS:
                value = parsed.get(key)
                if not value or data.get(key):
                    continue
                data[key] = value
                applied.append(key)

            if not applied:
                continue

            repre["data"] = data
            self.log.info(
                "Set %s on representation '%s'.",
                ", ".join(applied),
                repre.get("name"),
            )


def _name_candidates(repre):
    filenames = repre.get("files")
    if isinstance(filenames, str):
        yield filenames
    elif isinstance(filenames, (list, tuple)):
        for filename in filenames:
            if filename:
                yield filename
                break

    for key in ("name", "outputName"):
        value = repre.get(key)
        if value:
            yield str(value)
