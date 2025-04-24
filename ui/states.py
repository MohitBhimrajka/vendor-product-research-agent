from enum import Enum, auto


class AppState(Enum):
    HOME                    = auto()
    GENERATING_VENDOR       = auto()
    VENDOR_DONE             = auto()

    GENERATING_PRODUCT_INIT = auto()
    AWAITING_FILTER         = auto()
    FILTERING               = auto()

    AWAITING_PHASE2         = auto()
    GENERATING_PHASE2       = auto()

    AWAITING_DEEPDIVE       = auto()
    GENERATING_DEEPDIVE     = auto()

    AWAITING_FINAL          = auto()
    GENERATING_FINAL        = auto()
    COMPLETE                = auto() 