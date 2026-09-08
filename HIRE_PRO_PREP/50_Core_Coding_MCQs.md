# 50 High-Priority Core Coding Fundamentals MCQs for HirePro Assessment Preparation

**Q1. What is the key characteristic of dynamic typing in Python?**
A) Variables must be declared with their data types before use.
B) Variable data types are determined automatically at runtime based on the assigned value.
C) Variables cannot change their data type once initialized.
D) Data types are checked strictly at compile-time.
**Answer:** B
**Explanation:** Python is a dynamically typed language, meaning you do not need to explicitly declare a variable's data type; the interpreter infers it automatically during runtime execution.

**Q2. Which of the following built-in Python data types is classified as immutable?**
A) `list`
B) `dict`
C) `set`
D) `tuple`
**Answer:** D
**Explanation:** Tuples are immutable sequence types, meaning their elements cannot be modified, added, or removed after creation, unlike lists, dictionaries, and sets.

**Q3. What is the primary difference between the equality operators `==` and `is` in Python?**
A) `==` compares object memory addresses, while `is` compares values.
B) `==` compares the values of two objects, while `is` evaluates whether two references point to the exact same object in memory (identity check).
C) There is no functional difference; they are interchangeable aliases.
D) `is` is used exclusively for numeric types.
**Answer:** B
**Explanation:** The `==` operator checks for value equality, whereas the `is` operator checks for object identity (memory address matching).

**Q4. What does floor division (`//`) return in Python?**
A) Exact floating-point division results.
B) The remainder of a division operation.
C) The integer portion of the division quotient, rounded down towards the nearest integer.
D) The exponentiation result.
**Answer:** C
**Explanation:** Floor division divides input numbers and rounds down to the nearest integer, returning a whole number (or float if floats are involved, but truncated).

**Q5. How does Python handle memory management under the hood?**
A) Manual memory allocation and deallocation via pointers.
B) Automatic memory management using reference counting and a garbage collector.
C) Stack-only allocation that flushes after every function call.
D) Compulsory manual garbage collection triggers.
**Answer:** B
**Explanation:** Python automates memory management through reference counting (tracking how many references point to an object) and a cyclic garbage collector to reclaim unused memory.

**Q6. What is the output of the expression `3 * 1 ** 3` in Python?**
A) 27
B) 3
C) 1
D) 9
**Answer:** B
**Explanation:** Exponentiation (`**`) has higher precedence than multiplication (`*`). Therefore, `1 ** 3` evaluates to `1`, which is then multiplied by `3` to yield `3`.

**Q7. Which indentation standard is officially recommended by PEP 8 for Python code blocks?**
A) 1 tab character
B) 2 spaces
C) 4 spaces
D) 8 spaces
**Answer:** C
**Explanation:** PEP 8, the official style guide for Python code, recommends using 4 spaces per indentation level for optimal readability.

**Q8. What happens if a Python script contains inconsistent indentation (mixing tabs and spaces)?**
A) The interpreter automatically normalizes them.
B) It triggers a `SyntaxError` or `IndentationError`.
C) It executes with a performance warning.
D) It converts all tabs to spaces at runtime.
**Answer:** B
**Explanation:** Python relies strictly on indentation to define execution blocks; inconsistent spacing results in an `IndentationError` or `SyntaxError`.

**Q9. Which of the following functions can be used to obtain documentation and structural info about a built-in module or function in the interactive interpreter?**
A) `info()`
B) `doc()`
C) `help()`
D) `man()`
**Answer:** C
**Explanation:** The built-in `help()` function invokes the interactive help system or displays documentation strings for modules, classes, and methods.

**Q10. What is a Lambda function in Python?**
A) A multi-line anonymous function defined using the `def` keyword.
B) An anonymous inline function defined using the `lambda` keyword that can evaluate an expression.
C) A function executed asynchronously on a separate thread.
D) A deprecated legacy syntax element.
**Answer:** B
**Explanation:** Lambda functions are compact, anonymous inline functions that can take any number of arguments but contain only a single expression.

**Q11. How are string values formatted using modern Python f-strings?**
A) `"Value is {}".format(val)`
B) `f"Value is {val}"`
C) `"Value is %s" % val`
D) `string.format_map(val)`
**Answer:** B
**Explanation:** Formatted string literals (f-strings), introduced in Python 3.6, allow embedding expressions inside strings using prefix `f` and curly braces `{}`.

**Q12. What is the time complexity of looking up a key in a Python dictionary on average?**
A) O(N)
B) O(log N)
C) O(1)
D) O(N log N)
**Answer:** C
**Explanation:** Python dictionaries are backed by hash tables, providing an average O(1) time complexity for key lookups, insertions, and deletions.

**Q13. Which built-in collection type stores unique elements and supports mathematical set operations like unions and intersections?**
A) `list`
B) `tuple`
C) `set`
D) `dict`
**Answer:** C
**Explanation:** A `set` is an unordered collection of unique items that implements standard mathematical set theory operations.

**Q14. What does the `pass` statement do in Python?**
A) Terminates program execution immediately.
B) Serves as a null operation placeholder where code syntax requires a statement but no action is needed.
C) Skips the current iteration of a loop (like `continue`).
D) Passes control to an exception handler.
**Answer:** B
**Explanation:** `pass` is a syntactic placeholder used when a statement is required syntactically but you want no code or command to execute.

**Q15. Which module in the Python standard library provides double-ended queue operations with O(1) appends and pops from both ends?**
A) `queue`
B) `heapq`
C) `collections` (`deque`)
D) `array`
**Answer:** C
**Explanation:** `collections.deque` is optimized for fast O(1) appends and pops from both left and right ends, making it superior to lists for queue/stack structures.

**Q16. What is the output of `bool("False")` in Python?**
A) `False`
B) `True`
C) `None`
D) Raises a `ValueError`
**Answer:** B
**Explanation:** `"False"` is a non-empty string. In Python, all non-empty strings evaluate to boolean `True` when passed to `bool()`.

**Q17. Which keyword is used to handle runtime exceptions safely in Python blocks?**
A) `catch`
B) `except`
C) `handle`
D) `rescue`
**Answer:** B
**Explanation:** Python uses `try...except` blocks to catch and manage runtime exceptions gracefully.

**Q18. What is the scope resolution rule Python uses to resolve variable names?**
A) Global-Local rule
B) LEGB rule (Local, Enclosing, Global, Built-in)
C) First-In-First-Out rule
D) Static inheritance order
**Answer:** B
**Explanation:** Python resolves names using the LEGB rule, searching Local scopes first, then Enclosing scopes, Global scopes, and finally Built-in namespaces.

**Q19. How do you create a generator function in Python?**
A) By using the `generator` keyword in the function signature.
B) By using the `yield` keyword instead of `return` inside the function body.
C) By wrapping a function inside brackets `()`.
D) By inheriting from the `Iterator` base class.
**Answer:** B
**Explanation:** Functions containing the `yield` keyword return a generator iterator when called, allowing lazy evaluation and memory-efficient iteration.

**Q20. What is a Python package?**
A) A single `.py` source file containing helper utilities.
B) A directory of related Python modules containing an `__init__.py` file.
C) A compressed archive of compiled bytecode libraries.
D) An external executable binary package.
**Answer:** B
**Explanation:** Packages are directories structured with modules and an initialization file (`__init__.py`) that define hierarchical namespaces for code organization.

**Q21. What does the `zip()` function do when combining two lists of unequal lengths?**
A) Raises a `LengthMismatchError`.
B) Pads the shorter list with `None` values.
C) Stops aggregating as soon as the shortest iterable is exhausted.
D) Cycles through the shorter list infinitely.
**Answer:** C
**Explanation:** `zip()` aggregates elements from iterables, terminating automatically when the shortest input iterable is exhausted.

**Q22. Which operator is used for matrix multiplication introduced in Python 3.5?**
A) `*`
B) `@`
C) `**`
D) `&`
**Answer:** B
**Explanation:** The `@` operator is designated for matrix multiplication (calling the `__matmul__` magic method), widely used in libraries like NumPy.

**Q23. What is the purpose of the `__init__` method in Python classes?**
A) To destroy an object when garbage collected.
B) To initialize newly created object instances with attributes.
C) To compile class code into bytecode.
D) To serve as the static entry point for execution.
**Answer:** B
**Explanation:** `__init__` acts as the constructor method in Python classes, invoked automatically to set up initial state and instance variables.

**Q24. What is method overriding in Python object-oriented programming?**
A) Creating multiple methods with the exact same name but different argument counts inside the same class.
B) Providing a specific implementation of a method in a subclass that is already defined in its parent superclass.
C) Overwriting system-level built-in modules.
D) Bypassing access modifiers on private variables.
**Answer:** B
**Explanation:** Method overriding occurs when a child class implements a method with the same name and signature as its parent class to customize behavior.

**Q25. How do you declare a private-like variable or method inside a Python class to prevent accidental external access?**
A) By prefixing it with the keyword `private`.
B) By prefixing its name with a double underscore (`__`).
C) By enclosing the name in square brackets `[]`.
D) By writing the name in ALL_CAPS.
**Answer:** B
**Explanation:** Prefixing identifiers with a double underscore triggers name mangling in Python, making them harder (though not entirely impossible) to access directly from outside the class.

**Q26. What does the `super()` function do in inheritance hierarchies?**
A) Returns a reference to the child subclass instance.
B) Returns a proxy object that delegates method calls to a parent or sibling class.
C) Forces garbage collection of superclasses.
D) Overrides all parent methods simultaneously.
**Answer:** B
**Explanation:** `super()` allows child classes to call methods and initializers defined in their parent classes cleanly without hardcoding class names.

**Q27. Which built-in function returns the memory address or a unique integer identifier for any Python object?**
A) `address()`
B) `id()`
C) `memory()`
D) `hash()`
**Answer:** B
**Explanation:** The `id()` function returns an integer representing an object's unique identity (typically its memory address in CPython).

**Q28. What is the primary difference between `sys.argv` and `input()`?**
A) `sys.argv` reads command-line arguments passed to the script, while `input()` prompts the user for interactive console input at runtime.
B) `sys.argv` only accepts integers; `input()` accepts strings.
C) There is no difference; they are aliases.
D) `input()` is executed at compile time.
**Answer:** A
**Explanation:** `sys.argv` captures command-line parameters passed upon execution, whereas `input()` blocks execution to prompt the user for interactive typing in the terminal.

**Q29. What is a shallow copy versus a deep copy in Python?**
A) Shallow copies duplicate objects recursively; deep copies only copy references.
B) A shallow copy constructs a new collection object but populates it with references to the original nested child objects, whereas a deep copy recursively duplicates nested objects entirely.
C) Shallow copies are faster because they use multi-threading.
D) There is no functional difference in Python.
**Answer:** B
**Explanation:** Shallow copies (`copy.copy()`) copy outer structures while keeping inner references shared; deep copies (`copy.deepcopy()`) duplicate everything recursively.

**Q30. What is the role of the `__str__` magic method compared to `__repr__`?**
A) `__str__` is for debugging; `__repr__` is for end-users.
B) `__str__` provides an informal, readable string representation for users, while `__repr__` provides an unambiguous, formal representation meant for developers and debugging.
C) `__str__` handles string concatenations; `__repr__` handles slicing.
D) They perform identical tasks.
**Answer:** B
**Explanation:** `__str__` aims for human readability, whereas `__repr__` aims for programmatic clarity and precise object recreation details.

**Q31. Which core data structure backing mechanism allows Python dictionaries to maintain insertion order (since Python 3.7+)?**
A) A balanced Red-Black Tree.
B) A split-table hash map architecture maintaining a separate dense index array alongside the sparse hash table.
C) A doubly linked list connecting hash buckets directly.
D) A contiguous sorted array.
**Answer:** B
**Explanation:** Python's modern dictionary implementation splits entries into a compact dense array preserving insertion order and a sparse lookup table.

**Q32. What is monkey patching in Python?**
A) A debugging tool built into the standard library.
B) The dynamic modification of a class or module at runtime without altering its original source code file.
C) A technique for multi-threaded synchronization.
D) Compiling Python code into C extensions.
**Answer:** B
**Explanation:** Monkey patching allows developers to override or extend functions and methods at runtime dynamically, often used in testing or mocking.

**Q33. What does the `any()` built-in function return if passed an iterable where at least one element evaluates to truthy?**
A) `False`
B) `True`
C) Raises a `TypeError`
D) The first truthy element itself
**Answer:** B
**Explanation:** `any()` returns `True` if any element of the iterable is truthy; it returns `False` only if all elements are falsy (or the iterable is empty).

**Q34. What is the difference between `itertools.permutations()` and `itertools.combinations()`?**
A) Permutations account for element order; combinations do not consider order.
B) Combinations allow duplicate elements; permutations do not.
C) Permutations work only on strings; combinations work on numbers.
D) There is no difference.
**Answer:** A
**Explanation:** Permutations generate ordered sequences where arrangement matters (e.g., `(A, B)` differs from `(B, A)`), whereas combinations generate unordered selections.

**Q35. How does Python's Garbage Collector handle reference cycles (e.g., two objects referencing each other)?**
A) Reference counting cleans them up instantly.
B) A generational garbage collector scans for isolated reference cycles and deallocates them periodically.
C) They cause permanent memory leaks that can never be recovered.
D) The operating system terminates the process.
**Answer:** B
**Explanation:** While simple reference counting misses cyclic references, Python includes a generational cyclic garbage collector (`gc` module) to detect and purge isolated reference loops.

**Q36. What is a decorator in Python?**
A) A syntax rule for styling user interfaces.
B) A design pattern that takes a function as input, extends or modifies its behavior without explicitly modifying its source code, and returns a wrapper function.
C) A compiler directive for optimizing loops.
D) A tool for managing database connections.
**Answer:** B
**Explanation:** Decorators are higher-order functions that wrap other functions to add reusable behavior (such as logging, caching, or auth checks) transparently.

**Q37. What is the purpose of the `global` keyword inside a Python function?**
A) To make local variables accessible to multi-threaded child processes.
B) To indicate that a variable referenced inside the function refers to a variable defined in the global module scope rather than creating a local variable.
C) To export functions to external packages.
D) To optimize global variable lookup speeds.
**Answer:** B
**Explanation:** Using `global var_name` allows a function to modify a variable residing in the global namespace rather than binding a new local variable.

**Q38. What is the output of `type(1 / 2)` in Python 3?**
A) `<class 'int'>`
B) `<class 'float'>`
C) `<class 'double'>`
D) `<class 'number'>`
**Answer:** B
**Explanation:** Unlike Python 2, Python 3 division (`/`) always performs true division, returning a floating-point number even when dividing two integers.

**Q39. What is a namespace in Python?**
A) A dictionary mapping every name to its corresponding object, ensuring names are unique and avoiding naming collisions.
B) The memory layout of an array.
C) A keyword list reserved by the interpreter.
D) A network configuration setting.
**Answer:** A
**Explanation:** Namespaces map names to objects, structuring code scopes (local, global, built-in) so identical variable names can exist safely in separate contexts.

**Q40. What is the purpose of the `__slots__` attribute in a Python class?**
A) To limit the maximum number of instances a class can instantiate.
B) To explicitly declare instance attributes and prevent the creation of `__dict__` and `__weakref__` per instance, significantly reducing memory overhead.
C) To enforce strict type checking on attributes.
D) To make all class methods thread-safe.
**Answer:** B
**Explanation:** `__slots__` optimizes memory utilization for classes with thousands of instances by pre-allocating fixed storage slots instead of dynamic dictionaries.

**Q41. What does the `dir()` function return when called without arguments?**
A) The list of files in the current working directory.
B) A sorted list of names currently defined in the local namespace.
C) The system environment variables.
D) The list of installed third-party packages.
**Answer:** B
**Explanation:** When called without parameters, `dir()` returns the list of valid names and attributes in the current local scope.

**Q42. How does short-circuit evaluation work with logical operators (`and`, `or`) in Python?**
A) It evaluates all operands simultaneously using hardware concurrency.
B) It stops evaluating expression branches as soon as the final truth value is determined, returning the last evaluated object.
C) It throws an error if operands have mixed data types.
D) It converts all operands to boolean values first.
**Answer:** B
**Explanation:** Logical operators evaluate from left to right and short-circuit: `and` stops at the first falsy value, and `or` stops at the first truthy value, returning that exact object.

**Q43. What is the core difference between `asyncio.gather()` and `asyncio.wait()`?**
A) `gather()` returns results in the order tasks complete; `wait()` returns results sorted by execution time.
B) `gather()` is designed to run tasks concurrently and return an aggregated list of results, whereas `wait()` returns a tuple of two sets (`done`, `pending`) giving fine-grained control over task states.
C) `gather()` only works with threads, while `wait()` works with coroutines.
D) There is no difference.
**Answer:** B
**Explanation:** `gather` conveniently bundles results into a list, while `wait` provides low-level control by returning sets of completed and pending futures.

**Q44. What is a context manager in Python, and how is it typically implemented?**
A) A module that manages operating system threads using `import`.
B) An object that defines runtime context using `__enter__` and `__exit__` magic methods, commonly invoked via the `with` statement for safe resource handling (e.g., file IO).
C) A database migration tool.
D) A security sandbox for running untrusted code.
**Answer:** B
**Explanation:** Context managers handle setup and teardown phases automatically via the `with` statement, ensuring resources like files or database connections close properly.

**Q45. What happens when you modify a list while iterating over it using a standard `for` loop in Python?**
A) The loop automatically resizes and adjusts indices cleanly.
B) It can lead to skipped elements, unexpected behaviors, or runtime bugs because the loop relies on underlying index tracking.
C) It raises an immediate `RuntimeError` in all cases.
D) The interpreter halts execution.
**Answer:** B
**Explanation:** Mutating a collection during iteration alters its length and index mapping, frequently causing elements to be processed incorrectly or skipped.

**Q46. What is the purpose of the `__all__` variable in a Python module?**
A) To list all external packages required by the module.
B) To define a public API whitelist of names exported when a client performs a wildcard import (`from module import *`).
C) To enable multi-threaded execution across all CPU cores.
D) To store module metadata and author details.
**Answer:** B
**Explanation:** Setting `__all__` explicitly controls which symbols are imported into other namespaces when `from module import *` is executed.

**Q47. What is method resolution order (MRO) in Python?**
A) The order in which methods are compiled into bytecode.
B) The linear order in which base classes are searched when looking for a method, resolved using the C3 Linearization algorithm.
C) The alphabetical sorting of class methods.
D) The priority queue order for async task execution.
**Answer:** B
**Explanation:** MRO dictates how Python traverses inheritance hierarchies in complex multiple-inheritance scenarios, determined via the C3 linearization algorithm and accessible via `__mro__`.

**Q48. What is the difference between a shallow tuple and a tuple containing mutable objects (like a list)?**
A) Tuples containing mutable objects can change their own length.
B) While the tuple itself remains immutable (its references cannot be reassigned), the underlying mutable objects inside it can still be modified in place.
C) Mutable items inside tuples cause runtime errors upon creation.
D) Tuples cannot hold mutable objects.
**Answer:** B
**Explanation:** Tuple immutability applies strictly to the container's references; if a tuple holds a list, that list's internal contents can still be mutated.

**Q49. Why does Python use the Global Interpreter Lock (GIL)?**
A) To protect CPython's memory management from race conditions, ensuring that only one thread executes Python bytecode at a time.
B) To accelerate multi-threaded network input/output operations.
C) To encrypt global variable spaces.
D) To prevent infinite recursion in loops.
**Answer:** A
**Explanation:** The GIL simplifies CPython's memory handling by preventing multiple threads from executing native bytecode concurrently, though it restricts CPU-bound multi-threading performance.

**Q50. How can a Python developer bypass the GIL for CPU-bound parallel processing tasks?**
A) By using multiple coroutines inside `asyncio`.
B) By using the `multiprocessing` module to spawn separate independent OS processes, each with its own Python interpreter and memory space.
C) By increasing the thread priority level.
D) By writing the code inside a lambda function.
**Answer:** B
**Explanation:** Because each process in the `multiprocessing` module runs in its own distinct memory space with a separate GIL, true parallel execution across multiple CPU cores is achieved.
