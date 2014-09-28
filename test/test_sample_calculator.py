import sys
from os.path import abspath, dirname

TESTDIR = dirname(abspath(__file__))
sys.path.insert(0, dirname(TESTDIR))

from texpect import Approve, At

CALCULATOR_LOCKDOWN = {'Calculator', 'Lockdown'}
LOGGER = At(CALCULATOR_LOCKDOWN)

class Calculator(object):
    def __init__(self):
        LOGGER.log("Calculator created.")
        self._stack = None
        self._decimals = 2
        self.clear()

    def __del__(self):
        LOGGER.log("Calculator destroyed with stack:")
        self.tape()

    def _tape_form(self):
        return "|o| %%+%d.%df |o|" % (15 + self._decimals, self._decimals)

    def _text_form(self):
        return "|o| %%%ds |o|" % (15 + self._decimals)

    def clear(self):
        self._stack = list()
        LOGGER.log(self._text_form(), "<new tape>")

    def tape(self):
        text_form = self._text_form()
        LOGGER.log(text_form, '<start of tape>')
        form = self._tape_form()
        for item in self._stack:
            LOGGER.log(form, item)
        LOGGER.log(text_form, '<end of tape>')

    def precision(self, decimals):
        self._decimals = max(0, int(decimals))
        LOGGER.log("Changing precision to %r decimals.", self._decimals)

    def push(self, value):
        value = round(float(value), self._decimals)
        LOGGER.log("Pushing value %r into stack.", value)
        self._stack.append(value)

    def pop(self):
        return LOGGER.returns(self._stack.pop())

    def swap(self):
        second = self.pop()
        first = self.pop()
        LOGGER.log("Swapping %r with %r.", first, second)
        self.push(second)
        self.push(first)

    def add(self):
        second = self.pop()
        first = self.pop()
        result = first + second
        LOGGER.log("Adding %r to %r yields %r.", first, second, result)
        self.push(result)

    def substract(self):
        second = self.pop()
        first = self.pop()
        result = first - second
        LOGGER.log("Substracting %r from %r yields %r.", first, second, result)
        self.push(result)

    def multiply(self):
        second = self.pop()
        first = self.pop()
        result = first * second
        LOGGER.log("Multiplying %r with %r yields %r.", first, second, result)
        self.push(result)

    def divide(self):
        second = self.pop()
        first = self.pop()
        result = first / second
        LOGGER.log("Dividing %r by %r yields %r.", first, second, result)
        self.push(result)


class TestSampleCalculator(object):
    @Approve(CALCULATOR_LOCKDOWN)
    def test_calculator_lockdown(self):
        calculator = Calculator()
        calculator.push(-100)
        calculator.push(6.66666666)
        calculator.push(42)
        calculator.push(21)
        calculator.tape()
        calculator.precision(4)
        calculator.tape()
        calculator.add()
        calculator.push(3)
        calculator.substract()
        calculator.push(2.22)
        calculator.multiply()
        calculator.swap()
        calculator.divide()
        calculator.tape()
        calculator.clear()
        del calculator

