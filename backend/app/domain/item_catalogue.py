from enum import Enum


class ItemType(str, Enum):
    AGRICULTURAL_COMMODITY = "AGRICULTURAL_COMMODITY"
    PURCHASED_PRODUCT = "PURCHASED_PRODUCT"
    RAW_MATERIAL = "RAW_MATERIAL"
    PACKAGING_MATERIAL = "PACKAGING_MATERIAL"
    FINISHED_GOOD = "FINISHED_GOOD"


class BaseUnit(str, Enum):
    KG = "KG"
    G = "G"
    QUINTAL = "QUINTAL"
    TON = "TON"
    L = "L"
    ML = "ML"
    PCS = "PCS"


ITEM_TYPE_VALUES = tuple(item_type.value for item_type in ItemType)
BASE_UNIT_VALUES = tuple(unit.value for unit in BaseUnit)

ITEM_CODE_PREFIXES = {
    ItemType.AGRICULTURAL_COMMODITY: "AGR",
    ItemType.PURCHASED_PRODUCT: "PUR",
    ItemType.RAW_MATERIAL: "RAW",
    ItemType.PACKAGING_MATERIAL: "PKG",
    ItemType.FINISHED_GOOD: "FG",
}
