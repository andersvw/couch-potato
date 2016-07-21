from lib.lirc_utils import LircConfig

TEST_CONFIG = """
begin remote
    name  test
        begin codes
            KEY_TEST           0xC03F
        end codes

        begin raw_codes
            name KEY_TEST_RAW
               9010    4478     591     591     568     560
                589    1668     599     586     563     563
                596     559     589     566     593     562
                597    1660     597    1661     596     589
                560    1667     590    1667     590    1668
                590    1668     591    1666     589     593
                566     563     596     559     590    1667
                590     592     567     561     600     555
                591     564     595    1662     595    1663
                595    1662     595     590     569    1659
                598    1659     598    1660     597    1660
                618   39354    9023    2242     590
        end raw_codes
end remote
"""


# noinspection PyClassHasNoInit
class TestLircConfig:
    def test_lirc_config(self):
        LircConfig(TEST_CONFIG, is_path=False)
        assert len(LircConfig.remotes) == 1

        remote_0 = LircConfig.remotes.values()[0]
        assert remote_0.name == "test"
        assert len(remote_0.keys) == 2
        assert len(remote_0.codes) == 1
        assert len(remote_0.raw_codes) == 1
