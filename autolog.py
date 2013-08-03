'''Automatic logging of calls.

Simple usage:

    import autolog

    @autolog.logged
    def add(a, b):
        return a + b

    class Adder(object):
        __metaclass__ = autolog.autolog
        def __init__(self, a):
            self.a = a
        def add(self, b):
            self.a += b
            return self
        def get(self):
            return self.a

    if __name__ == '__main__':
        print add(2, 2)
        print Adder(2).add(2).get()

Copyright (c) 2007 Claudio Jolowicz
This module is free software, and you may redistribute it and/or modify
it under the same terms as Python itself, so long as this copyright message
and disclaimer are retained in their original form.

IN NO EVENT SHALL THE AUTHOR BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT,
SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF
THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.

THE AUTHOR SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS" BASIS,
AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
'''

__author__ = "Claudio Jolowicz <jolowicz@gmail.com>"
__date__ = "1 April 2007"
__version__ = "0.2.2"
__all__ = ['logged', 'autolog']

class _logged(object):
    """Logging decorator implementation.

    This is an internal base class which provides the common
    implementation for the logged and logged.__get__ classes.
    """
    import sys
    log = sys.stderr

    def __init__(self, func):
        """Grab the function and get a printable representation."""
        object.__setattr__(self, '_func', func)

        if hasattr(func, '__name__') and func.__name__ != '<lambda>':
            object.__setattr__(self, '_repr', func.__name__)
        else:
            object.__setattr__(self, '_repr', repr(func))

    def __call__(self, *args, **kwargs):
        """Invoke the decorated function, logging its entry and exit."""
        args_repr = ', '.join(
            [repr(arg) for arg in args] +
            ['%s=%r' % (name, value) for name, value in kwargs.iteritems()])

        self.log.write('[call] %s(%s)\n' % (self._repr, args_repr))
        retval = self._func(*args, **kwargs)
        self.log.write('[exit] %s(%s) = %r\n' % (self._repr, args_repr, retval))

        return retval

    def __getattr__(self, name):
        return getattr(self._func, name)

    def __setattr__(self, name, value):
        setattr(self._func, name, value)

    def __delattr__(self, name):
        delattr(self._func, name)

class logged(_logged):
    r"""Decorator to log calls.

    To automatically log a function call, define the function as
    follows:

        from autolog import logged

        @logged
        def frobnicate(s):
          return ''.join(chr(ord(c)^42) for c in s)

    In this example, calling frobnicate('god') will result in the
    following log messages:

        [call] frobnicate('god')
        [exit] frobnicate('god') = 'MEN'

    To decorate a class or a lambda expression, use the alternative
    syntax:

        from autolog import logged

        class Empty: pass
        Empty = logged(Empty)

    Note that this only logs calls to the class object, not to its
    methods. Use the autolog metaclass if you want to decorate all
    methods of the class.

    To decorate a built-in, qualify it with the module name:

        __builtins__.__import__ = logged(__builtins__.__import__)
        __builtins__.str = logged(__builtins__.str)

    The decorated callable is logged before being called and after
    returning. The log message includes the name of the callable, the
    arguments, and the return value. If the callable does not have a
    name or is a lambda expression, its representation is logged
    instead. For bound methods, the log message includes the instance
    on which the method was called. For unbound methods, the log
    message includes the class object; the instance is included in the
    argument list.

    By default, the decorator logs to sys.stderr. To send the log
    messages to another file object (or any object that behaves like a
    file), assign the object to the `log' class attribute _before_ any
    decorated functions are declared. An example is given at the end
    of the source file.

    The decorator transparently wraps the callable in the sense that
    it has no effect on the return value and side effects except for
    writing to the log, and any attribute access is delegated to the
    wrapped object except for the decorator's own attributes.

    Known limitations.

    The decorator has been tested with user-defined and built-in
    functions, lambda expressions, bound and unbound methods, static
    and class methods, the __new__ method, built-in, old-style and
    new-style classes, callable objects, inner classes, properties,
    generators, and decorators themselves; it supports both positional
    and keyword arguments.

    Any function invoked by the decorator may cause an infinite
    recursion when decorated itself. Currently, the decorator invokes
    the following functions and methods:

        - __get__  on the decorated function
        - __repr__ on the instance of a bound method
        - __repr__ on the class of an unbound method
        - __repr__ on all arguments and return values

    FIXME: Mention builtins called by the decorator; logging them may
    cause infinite recursion, too. Example: hasattr (?)

    Obviously, the decorator also invokes the decorated function, but
    it is harmless if that function has already been decorated. As a
    simple rule, never decorate the __repr__ method of a class.

    If your class decorates __init__, make sure to catch an
    AttributeError in __repr__. This is necessary because __repr__
    will be called by the decorator before __init__ has completed. An
    example is given at the end of the source file.

    Decorating methods of built-in types (e.g. object.__new__ or
    dict.__update__) is not supported, since doing so results in a
    TypeError.

    Generator support is quite limited in the sense that only the
    instantiation of the generator is logged, not the actual
    iterations.

    While it may seem desirable to treat `yield' statements and
    `return' statements alike in terms of logging, doing so is
    problematic: Nothing differentiates a function containing a yield
    statement from a function returning a generator object.  Thus,
    full generator support implies modifying a function's return
    value, which violates the transparency of the function
    wrapper. Besides, this is not easily done, since the generator's
    next method is a read-only attribute.

    Subclassing the logged class.

    When deriving a class from the decorator, a few things should be
    kept in mind:

        (1) You should mirror the implementation of logged, separating
            the basic logic (_logged class) from the descriptor
            implementation (logged and logged.__get__ classes).

        (2) Your __get__ class should inherit from both logged.__get__
            and your _logged subclass. Use super to ensure all class
            constructors are called.

    This is best explained with an example:

        class _xlogged(_logged):
            def __init__(self, func):
                super(_xlogged, self).__init__(func)
            def __call__(self, *args, **kwargs):
                self.log.write('Extra logging...\n')
                return super(_xlogged, self).__call__(*args, **kwargs)

        class xlogged(_xlogged):
            class __get__(logged.__get__, _xlogged):
                def __init__(self, outer, instance, owner):
                    super(xlogged.__get__, self).__init__(outer, instance, owner)

    In this example, invoking a decorated function will produce the
    following call graph:

        T.func(obj)
         |- <function 'xlogged.__get__.__init__'>
         |   `- <function 'logged.__get__.__init__'>
         |       `- <function '_xlogged.__init__'>
         |           `- <function '_logged.__init__'>
         `- <function '_xlogged.__call__'>
             `- <function '_logged.__call__'>
                  `- <function 'T.func'>

    """
    class __get__(_logged):
        """
        Method object equivalent of logged.

        If a logged object is accessed from a containing class or
        instance, we need to invoke it as a bound or unbound method
        object. We get the method object from the decorated function's
        __get__ method and wrap it to take care of the logging.

        Implementation notes.

        In some cases we are not dealing with a method object at
        all. The decorated ``function'' may in fact be a callable
        attribute which has no __get__ method, and therefore cannot be
        bound. In this case we wrap the same object as the logged
        class; the only difference is that the containing class or
        instance appears in the log.

        Another case in which we must not bind the decorated function
        is the __new__ method. This method is special-cased by the
        type built-in such that it is automatically wrapped by
        staticmethod. Any time before the actual type construction
        (i.e. at the time of decoration), __new__ is still an ordinary
        function, so we need to explicitly preserve static method
        behaviour.
        """
        def __init__(self, outer, instance, owner):
            """Bind the method and get a printable representation."""
            # Get a method object and delegate to super.
            func = outer._func
            if hasattr(func, '__get__') and \
                   getattr(func, '__name__', None) != '__new__':
                func = func.__get__(instance, owner)
            super(logged.__get__, self).__init__(func)

            # Add instance or owner to the printable representation.
            if instance is not None:
                object.__setattr__(self, '_repr', '%r.%s' % (instance, self._repr))
            else: # owner is not None
                object.__setattr__(self, '_repr', '%r.%s' % (owner, self._repr))

def skip(func):
    func._skip_autolog = True
    return func

class autolog(type):
    """Metaclass to automatically log method invocations.

    To automatically log all method invocations in a class and its
    instances, include the following statement in the class
    declaration:

        __metaclass__ = autolog

    To enable logging for an already existing class, use:

        class Empty:
            pass

        Empty = autolog(Empty)

    This metaclass automatically decorates all methods or other
    callables in its classes with the `logged' decorator. More
    precisely, a class attribute is decorated iff it is not __repr__,
    and it either has a __get__ method which returns a callable for
    the class, or it does not have a __get__ method but is callable
    itself.

    Known limitations.

    To avoid infinite recursion, logging excludes a class's __repr__
    method, which is called by the decorator itself. If your class
    defines __init__, some care must be taken when writing a __repr__
    method because it will be called before __init__ has
    completed. (See the documentation of the logged class and the
    example at the end of the source file.)

    Implementation notes.

    Supporting properties requires some additional effort, because the
    property constructor is called before autolog has a chance to
    decorate the methods. Also, a property's fget, fset, and fdel
    methods are read-only attributes. This means that we have to
    replace the property with a new instance built from the decorated
    methods.
    """
    def __new__(cls, name, bases=None, dict=None):
        """Return a class with automatic logging of all methods."""
        if None in (bases, dict):
            # Alternative signature: autolog.__new__(<class 'T'>)
            name, bases, dict = name.__name__, name.__bases__, type({})(name.__dict__)

        for key, obj in dict.iteritems():
            if key == '__repr__':
                continue
            _obj = obj
            if hasattr(obj, '__get__'):
                _obj = obj.__get__(None, cls)
            if hasattr(_obj, '_skip_autolog'):
                continue
            if callable(_obj):
                dict[key] = logged(obj)
            elif getattr(obj, '__class__', None) is property:
                _dict = {}
                for _key in ('fget', 'fset', 'fdel'):
                    if getattr(obj, _key):
                        _dict[_key] = logged(getattr(obj, _key))
                dict[key] = property(**_dict)
        return type.__new__(cls, name, bases, dict)

def testsuite():
    class Torinese(object):
        """Example of an autologged class."""
        __metaclass__ = autolog

        # Decorating the constructor.
        def __init__(self, name):
            self.name = name

        # The method __repr__ is never decorated.
        # Accessing attributes may raise an AttributeError, because
        # __repr__ is called before the constructor has completed.
        def __repr__(self):
            try:
                return '%s(%r)' % (self.__class__.__name__, self.name)
            except AttributeError:
                return object.__repr__(self)

        # A normal method.
        def show(self, arg):
            print '%s says: "%s"' % (self.name, arg)

        # A class method.
        @classmethod
        def what(cls):
            return cls.__name__

        # A static method.
        @staticmethod
        def add(a, b):
            return a + b

        # A method calling another method.
        def talk(self):
            self.show("Funda nen, ma va neanch'avan.")

    #
    #  Test suite.
    #

    import unittest, StringIO, sys, re

    class AutologTestCase(unittest.TestCase):
        def setUp(self):
            _logged.log = StringIO.StringIO()

        def tearDown(self):
            sys.stdout.write(_logged.log.getvalue())
            _logged.log.close()

        def assertInLog(self, text):
            try:
                log = _logged.log.getvalue()
                self.assert_(text in log)
            except AssertionError:
                raise AssertionError, '%r not in %r' % (text, log)

        def assertLog(self, expect):
            def clean(s):
                # weed address references
                s = re.sub('0x[0-9a-f]+', '0x0', s)
                # strip whitespace
                s = '\n'.join(map(str.strip, s.strip().split('\n')))
                return s

            log = _logged.log.getvalue()
            self.assertEqual(clean(log), clean(expect))

        def testBuiltinImport(self):
            """Testing built-in __import__"""
            _import, __builtins__.__import__ = __builtins__.__import__, logged(__builtins__.__import__)
            import cPickle
            self.assert_('cPickle' in vars())
            self.assertInLog('__import__')
            __builtins__.__import__ = _import

        def testBuiltinAbs(self):
            """Testing built-in abs"""
            _abs, __builtins__.abs = __builtins__.abs, logged(__builtins__.abs)
            self.assertEqual(abs(-7), 7)
            self.assertInLog('abs')
            __builtins__.abs = _abs

        def testBuiltinBool(self):
            """Testing built-in bool"""
            _bool, __builtins__.bool = __builtins__.bool, logged(__builtins__.bool)
            self.assertEqual(bool(5), True)
            self.assertInLog('bool')
            __builtins__.bool = _bool

        def testBuiltinGetAttr(self):
            """Testing built-in getattr"""
            _getattr, __builtins__.getattr = __builtins__.getattr, logged(__builtins__.getattr)
            self.assertEqual(getattr(5, '__class__'), int)
            self.assertInLog('getattr')
            __builtins__.getattr = _getattr

        def testBuiltinStaticmethod(self):
            """Testing built-in staticmethod"""
            _staticmethod, __builtins__.staticmethod = __builtins__.staticmethod, logged(__builtins__.staticmethod)
            class Foo(object):
                @staticmethod
                def foo(): return 42
            self.assertInLog('staticmethod')
            __builtins__.staticmethod = _staticmethod

        def testBuiltinStr(self):
            """Testing built-in str"""
            _str, __builtins__.str = __builtins__.str, logged(__builtins__.str)
            self.assertEqual(str(5), "5")
            self.assertInLog('str')
            __builtins__.str = _str

        def testBuiltinDict(self):
            """Testing built-in dict"""
            _dict, __builtins__.dict = __builtins__.dict, logged(__builtins__.dict)
            self.assertEqual(dict(), {})
            self.assertInLog('dict')
            __builtins__.dict = _dict

        def testBuiltinDivmod(self):
            """Testing built-in divmod"""
            _divmod, __builtins__.divmod = __builtins__.divmod, logged(__builtins__.divmod)
            self.assertEqual(divmod(7, 2), (3, 1))
            __builtins__.divmod = _divmod

        def testBuiltinNew(self):
            """Testing built-in object.__new__ (not supported)"""
            try:
                _new, object.__new__ = object.__new__, logged(object.__new__)
                obj = object()
            except TypeError:
                pass

        def testFunction(self):
            """Testing user-defined function"""
            @logged
            def say():
                return "Funda nen, ma va neanch'avan."

            retval = say()
            self.assertEqual(retval, "Funda nen, ma va neanch'avan.")
            self.assertLog("""
            [call] say()
            [exit] say() = \"Funda nen, ma va neanch'avan.\"
            """)

        def testGenerator(self):
            """Testing generator"""
            @logged
            def squares(n):
                for i in range(n):
                    yield i * i

            retval = squares(3)
            self.assertEqual(0, retval.next())
            self.assertEqual(1, retval.next())
            self.assertEqual(4, retval.next())
            self.assertLog("""
            [call] squares(3)
            [exit] squares(3) = <generator object squares at 0xb7d7282c>
            """)

        def testLambdaExpression(self):
            """Testing lambda expression"""
            identity = logged(lambda x: x)

            retval = identity(identity)
            self.assertEqual(retval, identity)
            self.assertLog("""
            [call] <function <lambda> at 0xb7d5cfb4>(<__main__.logged object at 0xb7d8738c>)
            [exit] <function <lambda> at 0xb7d5cfb4>(<__main__.logged object at 0xb7d8738c>) = <__main__.logged object at 0xb7d8738c>
            """)

        def testOldStyleClass(self):
            """Testing old-style class"""
            class Empty: pass
            Empty = logged(Empty)

            retval = Empty()
            self.assert_(isinstance(retval, Empty._func))
            self.assertLog("""
            [call] Empty()
            [exit] Empty() = <__main__.Empty instance at 0xb7d7282c>
            """)

        def testNewStyleClass(self):
            """Testing new-style class"""
            class Void(object): pass
            Void = logged(Void)

            retval = Void()
            self.assert_(isinstance(retval, Void._func))
            self.assertLog("""
            [call] Void()
            [exit] Void() = <__main__.Void object at 0xb7d7276c>
            """)

        def testAttributeLambdaExpression(self):
            """Testing lambda expression in a class"""
            class Void(object):
                __nonzero__ = logged(lambda self: False)
            Void = logged(Void)

            obj = Void()
            retval = bool(obj)
            self.failIf(retval)
            self.assertLog("""
            [call] Void()
            [exit] Void() = <__main__.Void object at 0xb7d083ec>
            [call] <__main__.Void object at 0xb7d083ec>.<bound method Void.<lambda> of <__main__.Void object at 0xb7d083ec>>()
            [exit] <__main__.Void object at 0xb7d083ec>.<bound method Void.<lambda> of <__main__.Void object at 0xb7d083ec>>() = False
            """)

        def testConstructor(self):
            """Testing __init__ method"""
            retval = Torinese('Ludovico')
            self.assert_(isinstance(retval, Torinese))
            self.assertLog("""
            [call] <__main__.Torinese object at 0xb7d7282c>.__init__('Ludovico')
            [exit] <__main__.Torinese object at 0xb7d7282c>.__init__('Ludovico') = None
            """)

        def testBoundMethod(self):
            """Testing bound method"""
            obj = Torinese('Ludovico')
            obj.show("Com alle?")
            self.assertLog("""
            [call] <__main__.Torinese object at 0xb7d7276c>.__init__('Ludovico')
            [exit] <__main__.Torinese object at 0xb7d7276c>.__init__('Ludovico') = None
            [call] Torinese('Ludovico').show('Com alle?')
            [exit] Torinese('Ludovico').show('Com alle?') = None
            """)

        def testUnboundMethod(self):
            """Testing unbound method"""
            obj = Torinese('Ludovico')
            Torinese.show(obj, 'Coma na barca in tal pra.')
            self.assertLog("""
            [call] <__main__.Torinese object at 0xb7d7282c>.__init__('Ludovico')
            [exit] <__main__.Torinese object at 0xb7d7282c>.__init__('Ludovico') = None
            [call] <class '__main__.Torinese'>.show(Torinese('Ludovico'), 'Coma na barca in tal pra.')
            [exit] <class '__main__.Torinese'>.show(Torinese('Ludovico'), 'Coma na barca in tal pra.') = None
            """)

        def testClassMethod(self):
            """Testing class method"""
            retval = Torinese.what()
            self.assertEqual(retval, 'Torinese')
            self.assertLog("""
            [call] <class '__main__.Torinese'>.what()
            [exit] <class '__main__.Torinese'>.what() = 'Torinese'
            """)

        def testStaticMethod(self):
            """Testing static method"""
            retval = Torinese.add(2, 2)
            self.assertEqual(retval, 4)
            self.assertLog("""
            [call] <class '__main__.Torinese'>.add(2, 2)
            [exit] <class '__main__.Torinese'>.add(2, 2) = 4
            """)

        def testStaticMethodInside(self):
            """Testing associativity with staticmethod (staticmethod inside)"""
            # Associativity with staticmethod.
            class Static(object):
                def inside(a):
                    return a
                inside = logged(staticmethod(inside))

            self.assertEqual(Static.inside(4), 4)
            self.assertInLog('inside')

        def testStaticMethodOutside(self):
            """Testing associativity with staticmethod (staticmethod outside)"""
            # Associativity with staticmethod.
            class Static(object):
                def outside(a):
                    return a
                outside = staticmethod(logged(outside))

            self.assertEqual(Static.outside(4), 4)
            self.assertInLog('outside')

        def testNestedCall(self):
            """Testing nested call"""
            @logged
            def say():
                return "Funda nen, ma va neanch'avan."

            obj = Torinese('Ludovico')
            obj.talk()
            self.assertLog("""
            [call] <__main__.Torinese object at 0xb7d7282c>.__init__('Ludovico')
            [exit] <__main__.Torinese object at 0xb7d7282c>.__init__('Ludovico') = None
            [call] Torinese('Ludovico').talk()
            [call] Torinese('Ludovico').show(\"Funda nen, ma va neanch'avan.\")
            [exit] Torinese('Ludovico').show(\"Funda nen, ma va neanch'avan.\") = None
            [exit] Torinese('Ludovico').talk() = None
            """)

        def testCallableObject(self):
            """Testing callable object"""
            class Adder(object):
                def __init__(self, a):
                    self.a = a
                # Note that using __repr__ is safe here because __init__ is
                # not decorated.
                def __repr__(self):
                    return '%s(%r)' % (self.__class__.__name__, self.a)
                def __call__(self, b):
                    return self.a + b
            add21 = logged(Adder(21))

            retval = add21(21)
            self.assertEqual(retval, 42)
            self.assertLog("""
            [call] Adder(21)(21)
            [exit] Adder(21)(21) = 42
            """)

        def testInnerClass(self):
            """Testing inner class"""
            class Outer(object):
                class Inner(object):
                    pass
                Inner = logged(Inner)

            retval = Outer.Inner()
            self.assertLog("""
            [call] <class '__main__.Outer'>.Inner()
            [exit] <class '__main__.Outer'>.Inner() = <__main__.Inner object at 0xb7de254c>
            """)

        def testInnerClassAutolog(self):
            """Testing inner class of an autologged class"""
            class Outer_autolog(object):
                __metaclass__ = autolog

                class Inner(object):
                    pass

            retval = Outer_autolog.Inner()
            self.assertLog("""
            [call] <class '__main__.Outer_autolog'>.Inner()
            [exit] <class '__main__.Outer_autolog'>.Inner() = <__main__.Inner object at 0xb7d7290c>
            """)

        def testProperty(self):
            """Testing property"""
            class Thinker(object):
                def __init__(self):
                    self.__thought = None

                @logged
                def __getThought(self):
                    return self.__thought

                @logged
                def __setThought(self, thought):
                    self.__thought = thought

                thought = property(__getThought, __setThought)

            obj = Thinker()
            obj.thought = "I am hungry."
            retval = obj.thought
            self.assertEqual(retval, "I am hungry.")
            self.assertLog("""
            [call] __setThought(<__main__.Thinker object at 0xb7d1770c>, 'I am hungry.')
            [exit] __setThought(<__main__.Thinker object at 0xb7d1770c>, 'I am hungry.') = None
            [call] __getThought(<__main__.Thinker object at 0xb7d1770c>)
            [exit] __getThought(<__main__.Thinker object at 0xb7d1770c>) = 'I am hungry.'
            """)

        def testPropertyAutolog(self):
            """Testing property of an autologged class"""
            class Thinker_autolog(object):
                __metaclass__ = autolog

                def __init__(self):
                    self.__thought = None

                def __getThought(self):
                    return self.__thought

                def __setThought(self, thought):
                    self.__thought = thought

                thought = property(__getThought, __setThought)

            obj = Thinker_autolog()
            obj.thought = "Coffee..."
            retval = obj.thought
            self.assertEqual(retval, "Coffee...")
            self.assertLog("""\
            [call] <__main__.Thinker_autolog object at 0xb7d1768c>.__init__()
            [exit] <__main__.Thinker_autolog object at 0xb7d1768c>.__init__() = None
            [call] __setThought(<__main__.Thinker_autolog object at 0xb7d1768c>, 'Coffee...')
            [exit] __setThought(<__main__.Thinker_autolog object at 0xb7d1768c>, 'Coffee...') = None
            [call] __getThought(<__main__.Thinker_autolog object at 0xb7d1768c>)
            [exit] __getThought(<__main__.Thinker_autolog object at 0xb7d1768c>) = 'Coffee...'
            """)

        def testSubClassAutolog(self):
            """Testing autologged subclass of an autologged class"""
            class Neapolitano(Torinese):
                # Just inheriting the meta class is not enough (?!).
                __metaclass__ = autolog
                def show(self, arg):
                    print '%s shouts: "%s"' % (self.name, arg)

            obj = Neapolitano('Daniele')
            self.assert_(isinstance(obj, Neapolitano))
            obj.show("Ue!")
            self.assertLog("""\
            [call] <__main__.Neapolitano object at 0xb7d6a44c>.__init__('Daniele')
            [exit] <__main__.Neapolitano object at 0xb7d6a44c>.__init__('Daniele') = None
            [call] Neapolitano('Daniele').show('Ue!')
            [exit] Neapolitano('Daniele').show('Ue!') = None
            """)

        def testClassNewAutolog(self):
            """Testing __new__ method of an autologged class"""
            class Milanese(object):
                __metaclass__ = autolog

                # Decorating __new__.
                def __new__(cls, name):
                    obj = object.__new__(cls)
                    obj.name = name
                    return obj

                # A user-defined method.
                def show(self, arg):
                    print '%s whispers: "%s"' % (self.name, arg)

                # The method __repr__ is never decorated.
                # Accessing attributes may raise an AttributeError, because
                # __repr__ is called before the constructor has completed.
                def __repr__(self):
                    try:
                        return '%s(%r)' % (self.__class__.__name__, self.name)
                    except AttributeError:
                        return object.__repr__(self)

            obj = Milanese('Guido')
            self.assert_(isinstance(obj, Milanese))
            obj.show("Madonna...")
            self.assertLog("""\
            [call] <class '__main__.Milanese'>.__new__(<class '__main__.Milanese'>, 'Guido')
            [exit] <class '__main__.Milanese'>.__new__(<class '__main__.Milanese'>, 'Guido') = Milanese('Guido')
            [call] Milanese('Guido').show('Madonna...')
            [exit] Milanese('Guido').show('Madonna...') = None
            """)

        def testClassNewPosterior(self):
            """Testing __new__ method, decorated after type construction"""
            class NewConfusion(object):
                def __new__(cls):
                    return object.__new__(cls)
            NewConfusion.__new__ = logged(NewConfusion.__new__)

            obj = NewConfusion()
            self.assertInLog('__new__')

        def testClassNewPosteriorDict(self):
            """Testing __new__ method, decorated after type construction using __dict__"""
            class NewerConfusion(object):
                def __new__(cls):
                    return object.__new__(cls)
            NewerConfusion.__new__ = logged(NewerConfusion.__dict__['__new__'])

            obj = NewerConfusion()
            self.assertInLog('__new__')

        def testSubclassingLogged(self):
            """Testing subclassing the logged class"""
            class _xlogged(_logged):
                def __init__(self, func):
                    super(_xlogged, self).__init__(func)
                def __call__(self, *args, **kwargs):
                    self.log.write('Extra logging...\n')
                    return super(_xlogged, self).__call__(*args, **kwargs)

            class xlogged(_xlogged):
                class __get__(logged.__get__, _xlogged):
                    def __init__(self, outer, instance, owner):
                        super(xlogged.__get__, self).__init__(outer, instance, owner)

            class Foo(object):
                @xlogged
                def __init__(self):
                    pass

            obj = Foo()
            self.assertLog("""\
            Extra logging...
            [call] <__main__.Foo object at 0xb7d24bcc>.__init__()
            [exit] <__main__.Foo object at 0xb7d24bcc>.__init__() = None
            """)

        def testConvertType(self):
            """Testing type conversion"""
            class Foo(object):
                def __init__(self):
                    pass
            Foo = autolog(Foo)
            obj = Foo()
            self.assertLog("""\
            [call] <__main__.Foo object at 0xb7d4c38c>.__init__()
            [exit] <__main__.Foo object at 0xb7d4c38c>.__init__() = None
            """)

    return unittest.TestLoader().loadTestsFromTestCase(AutologTestCase)

if __name__ == '__main__':
    import unittest, sys, StringIO

    _stdout, sys.stdout = sys.stdout, StringIO.StringIO()

    unittest.TextTestRunner(verbosity=2).run(testsuite())

    _stdout, sys.stdout = sys.stdout, _stdout

    if '--verbose' in sys.argv[1:]:
        sys.stdout.write(_stdout.getvalue())
