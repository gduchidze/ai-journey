class Job:
    def __init__(self, name , cost):
        self.name = name
        self.cost = cost

    def __add__(self, other):
        # spec wants "name1+name2" -- need the literal "+" separator,
        # not just names jammed together
        return Job(name=f"{self.name}+{other.name}", cost=self.cost + other.cost)

    def __eq__(self, other):
        return self.name == other.name and self.cost == other.cost

    def __len__(self):
        # __len__ MUST return an int -- CPython's C-level size protocol
        # (PyObject_Size) requires it. If you return self.cost directly
        # and cost is a float, len() raises:
        #   TypeError: 'float' object cannot be interpreted as an integer
        # because len() means "count of something", which is inherently
        # a whole number -- Python won't silently truncate a float for you.
        return int(self.cost)

    def __hash__(self):
        # defining __eq__ makes Python set __hash__ = None automatically
        # (objects that compare equal must hash equal, so the default
        # identity-based hash can't be trusted anymore once equality is
        # overridden). Without this, putting a Job in a set/dict raises:
        #   TypeError: unhashable type: 'Job'
        return hash((self.name, self.cost))

    def __str__(self):
        return f"Job({self.name}: cost={self.cost})"

    def __repr__(self):
        return f"Job({self.name!r}, {self.cost})"


if __name__ == "__main__":
    print("Hello World")

    j1 = Job(name="job1", cost=10)
    j2 = Job(name="job2", cost=20)

    print(j1)
    print(j2)
    print(repr(j1))          # was never tested before -- now confirmed pasteable: Job('job1', 10)
    print(j1+j2)

    if j1 == j2:
        print("j1 and j2 are equal")
    else:
        print("j1 and j2 are not equal")

    # equality vs identity
    print(j1 == Job(j1.name, j1.cost))   # True -- same name+cost
    print(j1 is Job(j1.name, j1.cost))   # False -- different object

    print(len(j1))

    j_float = Job("deploy", 5.0)
    print(j_float)
    print(len(j_float))
    # ACTUAL: this works and prints 5 because __len__ already casts with
    # int(self.cost). If you comment out the int() and just `return
    # self.cost`, this same call raises:
    #   TypeError: 'float' object cannot be interpreted as an integer
    # Try that swap yourself, run it, then put int() back -- seeing the
    # real error is the point of this exercise, not just reading about it.

    # put several jobs in a set() -- breaks without __hash__ above
    jobs = {j1, j2, Job("job1", 10)}
    print(jobs)
    # ACTUAL: works now because __hash__ is defined. Without it, this line
    # raises TypeError: unhashable type: 'Job' -- try commenting out
    # __hash__ to see that error yourself, then restore it.
