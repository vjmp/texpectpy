# texpect.Approve for Python 2.7.x

## What is it?

Quick experiment to do Approval Testing in Python. So instead of writing
tests first, you spike and stabilize and create Approval tests afterwards.
And as an expert, you verify outputs once and let automation run forever.

Tools used to get that effect are:

* Python decorator class "Approve" (it is also a context manager).
* Logger like utility "At" with multi-dimension logging targets.

**Note:** this is not production ready code, just a quick proof-of-concept.
Search Google or YouTube for "Approval Tests" and "TextTest" for more details.

## Possible workflow for legacy apps

1. Checkout your legacy application from repo. Spike is also legacy, since
   it does not have tests, yet.
1. Go and instrument it with "texpect.At" loggers.
1. Create approval test using unit testing tools.
1. Run those tests and examine results and coverage.
1. Move **.nok** files to **.ok** files as they mature.
1. Repeat from step 2 until you are happy about your coverage.
1. Now your features are locked down.
1. Start refactoring ...

## Quick example

### Somewhere in test case world

    # in file "test/test_calculator.py"

    from texpect import Approve

    @Approve({'Primary', 'Context'}, 'Secondary')
    def test_application_lockdown(self):
        calculator = Calculator()
        calculator.push(1)
        calculator.push(1)
        calculator.add()
        calculator.tape()
        del calculator

Notes about above test:

* there are no asserts
* you just run your application and do operations
* after test is executed, @Approve does its thing
* it is only interested in "Primary Context" and "Secondary"
* using "test/calculator.application_lockdown.ok" file
* if that does not exist, file "test/calculator.application_lockdown.nok"
* against given "context sets"/dimensions (multiple dimensions are allowed)
* see: test/test_sample_calculator.py for real runnable example
* use command "py.test test" to run it
* expect approves those test outputs and does **.not** to **.ok** transition
  (you or someone else)

### Somewhere in application world

    import texpect

    LOGGER = texpect.At({'Primary', 'Context'})
    TRACER = texpect.At({'Trace', 'Context'})

    :

    def push(self, input):
        TRACER.log("entering push with %r", input)
        value = round(float(input), 4)
        TRACER.log("value rounded from %r to %r", input, value)
        LOGGER.log("Pushing value %r into stack.", value)
        self._stack.append(value)
        TRACER.log("leaving push of %r", input)
        return TRACER.returns(value)

Notes about above test:

* two loggers are created, each with different context
* you can use multiple contexts in loggers
* and they can overlap (but here they don't)
* TRACER uses both "log" and "returns" methods
* LOGGER is used just once
* no functionality of this legacy app was changed, except for additional logging

## Toolset for testing texpect

* Python 2.7.5 (CPython)
* py.test

## Additional ideas/TODOs

* add a file backend for logging, so that it can be used as normal log tool
* better documentation and more examples
* better description of "dimensions" logging
* verify performance (and improve if needed)
* verify threads and locks
* if this is going to stay, do the travis dance
* is this suitable stuff for pypi? who authorizes pypi access?

