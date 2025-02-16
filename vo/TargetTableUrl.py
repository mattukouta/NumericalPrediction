import dataclasses


@dataclasses.dataclass
class TargetTableUrl:
    detailTableUrls: list[str]
    simpleTableUrls: list[str]

