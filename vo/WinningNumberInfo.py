import dataclasses


@dataclasses.dataclass
class WinningNumberInfo:
    id: int
    year: int
    month: int
    day: int
    winningNumber: list[int]
    bonusNumber: int
