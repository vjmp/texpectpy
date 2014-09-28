import sys
from os.path import abspath, dirname
from StringIO import StringIO

TESTDIR = dirname(abspath(__file__))
sys.path.insert(0, dirname(TESTDIR))

from pytest import raises, fixture

import texpect

class TestLogging(object):
    def test_logger_is_correct(self, logger):
        assert logger is not None

    def test_logger_can_log(self, logger):
        logger.log("hello %s", "world")

    def test_logger_can_be_called(self, logger):
        logger("hello %s", "world")

    def test_can_redirect_to_stream(self, logger):
        stream = StringIO()
        logger.into(stream)
        logger.log('there %s is', 'it')
        assert 'LOG TEST: there it is\n' == stream.getvalue()

    def test_wont_write_newlines_twice(self, logger):
        stream = StringIO()
        logger.into(stream)
        logger.log('there %s is\n', 'it')
        assert 'LOG TEST: there it is\n' == stream.getvalue()

    def test_ignores_messages_before(self, logger):
        logger.log('this was before')
        stream = StringIO()
        logger.into(stream)
        logger.log('there %s is\n', 'it')
        assert 'LOG TEST: there it is\n' == stream.getvalue()

    def test_loggers_wont_interfere(self, logger, other_logger):
        stream, other = StringIO(), StringIO()
        logger.into(stream)
        other_logger.into(other)
        logger.log('this is logger')
        other_logger.log('this is other')
        logger.log('this is logger again')
        other_logger.log('this is other again')
        assert 'LOG TEST: this is logger\nLOG TEST: this is logger again\n' == stream.getvalue()
        assert 'LOG TEXT: this is other\nLOG TEXT: this is other again\n' == other.getvalue()

    def test_common_logging_also_works(self, logger, other_logger, single_logger):
        stream = StringIO()
        single_logger.into(stream)
        single_logger.log('this is single logger')
        logger.log('this is logger')
        other_logger.log('this is other logger')
        single_logger.log('this is single logger again')
        assert 'SINGLE: this is single logger\nLOG TEXT: this is other logger\nSINGLE: this is single logger again\n' == stream.getvalue()

    def test_can_record_return_values(self, logger):
        stream = StringIO()
        logger.into(stream)
        assert logger.returns(42, 64, 'Zzz') == (42, 64, 'Zzz')
        assert logger.returns('Hi') == 'Hi'
        assert logger.returns(('Bye',)) == ('Bye',)
        assert logger.returns(None) is None
        assert "LOG TEST: can_record_return_values returns (42, 64, 'Zzz')" in stream.getvalue()
        assert "\nLOG TEST: can_record_return_values returns ('Hi',)" in stream.getvalue()
        assert "\nLOG TEST: can_record_return_values returns (('Bye',),)" in stream.getvalue()
        assert "\nLOG TEST: can_record_return_values returns (None,)" in stream.getvalue()

from texpect import Approve

class TestApproving(object):
    @Approve('SINGLE')
    def test_approve_exists_and_works(self):
        single_logger().log('This is %r!', 'ok')
        logger().log('And this wont show up!')

    def test_fails_with_missing_ok_file(self, logger):
        with raises(AssertionError) as err:
            with Approve('SINGLE') as tool:
                logger.log('This content should not exist as ok file!')
        assert "texpect.fails_with_missing_ok_file.ok" in tool._approved
        assert "texpect.fails_with_missing_ok_file.nok" in tool._received

@fixture
def logger():
    return texpect.At({'TEST', 'LOG'})

@fixture
def other_logger():
    return texpect.At({'TEXT', 'LOG'}, {'MORE', 'LOG', 'DIMENSIONS'}, 'SINGLE')

@fixture
def single_logger():
    return texpect.At('SINGLE')

