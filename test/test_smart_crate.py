# pylint: disable=protected-access
import unittest
import os

from src.serato_tools.smart_crate import SmartCrate
from test.utils.utils import get_print_val


base_expected = """vrsn (Version): '1.0/Serato ScratchLive Smart Crate'
rart (SmartCrate Match All): [ brut (Unknown Field): True ]
rlut (SmartCrate Live Update): [ brut (Unknown Field): True ]
rurt (SmartCrate Rule): [ trft (Rule Comparison): cond_aft_time (TIME_IS_AFTER) ], [ urkt (Rule Field): 25 (added) ], [ trtt (Rule Value Date): 5/13/2020 ]
rurt (SmartCrate Rule): [ trft (Rule Comparison): cond_dnc_str (STR_DOES_NOT_CONTAIN) ], [ urkt (Rule Field): 19 (grouping) ], [ trpt (Rule Value Text): GRP ]
rurt (SmartCrate Rule): [ trft (Rule Comparison): cond_is_str (STR_IS) ], [ urkt (Rule Field): 23 (year) ], [ trpt (Rule Value Text): 2000 ]
rurt (SmartCrate Rule): [ trft (Rule Comparison): cond_con_str (STR_CONTAINS) ], [ urkt (Rule Field): 21 (label) ], [ trpt (Rule Value Text): YT ]        
osrt (Sorting): [ tvcn (Column Name): ● ], [ brev (Reverse Order): True ]
ovct (Column): [ tvcn (Column Name): artist ], [ tvcw (Column Width): 211 ]
ovct (Column): [ tvcn (Column Name): label ], [ tvcw (Column Width): 54 ]
ovct (Column): [ tvcn (Column Name): song ], [ tvcw (Column Width): 315 ]
ovct (Column): [ tvcn (Column Name): bpm ], [ tvcw (Column Width): 47 ]
ovct (Column): [ tvcn (Column Name): key ], [ tvcw (Column Width): 57 ]
ovct (Column): [ tvcn (Column Name): genre ], [ tvcw (Column Width): 394 ]
ovct (Column): [ tvcn (Column Name): grouping ], [ tvcw (Column Width): 80 ]
ovct (Column): [ tvcn (Column Name): comment ], [ tvcw (Column Width): 281 ]
ovct (Column): [ tvcn (Column Name): added ], [ tvcw (Column Width): 76 ]
ovct (Column): [ tvcn (Column Name): composer ], [ tvcw (Column Width): 0 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Baha Men - Who Let The Dogs Out.mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Boysetsfire - Rookie.mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Outkast - Ms. Jackson.mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Darude - Sandstorm.mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Shaggy - Hope (feat. Prince Mydas).mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Shaggy - Angel (feat. Rayvon).mp3 ]
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Three 6 Mafia - Sippin On Some Syrup (feat. UGK) (Underground Kingz) & Project Pat).mp3 ]  
otrk (Track): [ ptrk (Track Path): Users/bvand/Music/DJ Tracks/Yusuf  Cat Stevens - Peace Train.mp3 ]"""


class TestCase(unittest.TestCase):
    def check_lines(self, given: str, expected: str):
        given = "\n".join([l.strip() for l in given.splitlines()])
        expected = "\n".join([l.strip() for l in expected.splitlines()])
        self.maxDiff = None
        self.assertMultiLineEqual(given, expected)

    def test_parse(self):
        file = os.path.abspath("test/data/TestSmartCrate.scrate")
        with open(file, mode="rb") as fp:
            file_data = fp.read()

        crate = SmartCrate(file)

        self.assertEqual(crate.raw_data, file_data, "raw_data read")
        self.check_lines(get_print_val(crate.print), base_expected)

    def test_add_rule(self):
        file = os.path.abspath("test/data/TestSmartCrate.scrate")

        crate = SmartCrate(file)
        crate.set_rule(SmartCrate.RuleField.ALBUM, SmartCrate.RuleComparison.STR_IS_NOT, "albo")
        self.check_lines(
            get_print_val(crate.print),
            base_expected
            + "\nrurt (SmartCrate Rule): [ trft (Rule Comparison): cond_isn_str (STR_IS_NOT) ], [ urkt (Rule Field): 8 (album) ], [ trpt (Rule Value Text): albo ]",
        )
