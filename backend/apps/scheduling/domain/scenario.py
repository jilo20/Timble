from dataclasses import asdict, dataclass

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PERIODS = [f"{(450 + 60 * i) // 60:02d}:{(450 + 60 * i) % 60:02d}" for i in range(13)]


@dataclass(frozen=True)
class SchedulingScenario:
    offerings: list
    faculty: list
    rooms: list
    blocks: list
    subjects: list
    rules: list
    days: list
    periods: list

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
