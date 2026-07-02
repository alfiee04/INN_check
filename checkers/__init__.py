
from .vestnik_gosreg import VestnikGosregChecker
from .transparent_biz import TransparentBizChecker
from .bo_nalog import BoNalogChecker
from .rmsp import RmspChecker
from .zakupki_rnp import ZakupkiRnpChecker
from .zakupki_19_28 import Zakupki1928Checker
from .fedresurs import FedresursChecker
from .bankrot_fedresurs import BankrotFedresursChecker
from .kad_arbitr import KadArbitrChecker
from .fssp import FsspChecker
from .minjust import MinjustChecker
from .manual_section import ManualSectionChecker
from .search_media import CompanyMediaSearchChecker, PersonMediaSearchChecker
from .person_pb_nalog import PersonTransparentBizChecker
from .passport_validity import PassportValidityChecker
from .sudact import SudactChecker
from .rso_nalog import RsoNalogChecker


ALL_CHECKERS = [

    VestnikGosregChecker(),

    TransparentBizChecker(),

    BoNalogChecker(),

    RmspChecker(),

    ZakupkiRnpChecker(),

    Zakupki1928Checker(),

    FedresursChecker(),

    BankrotFedresursChecker(),

    KadArbitrChecker(),

    FsspChecker(),

    MinjustChecker(),

    ManualSectionChecker("Официальный сайт", "Оставлено для ручного анализа по ТЗ."),

    CompanyMediaSearchChecker(),

    ManualSectionChecker(
        "Характеристика учредителей и руководителей юридического лица",
        "Заполняется по анкете/документам: учредители, доли, руководитель."
    ),

    PersonTransparentBizChecker(),

    PassportValidityChecker(),

    SudactChecker(),

    RsoNalogChecker(),

    PersonMediaSearchChecker(),
]
