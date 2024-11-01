from enum import Enum

class PlotPeriodType(Enum):
    GUNLUK = "günlük"
    AYLIK = "aylık"
    CEYREKLIK = "çeyreklik"
    YILLIK = "yıllık"

    def capitalize(self):
        return self.value.capitalize()
    def __str__(self) -> str:
        return self.value