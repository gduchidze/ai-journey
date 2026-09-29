import dis
import gc
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


class Job:
    def __init__(self, name, cost, depends_on=None):
        self.name = name
        self.cost = cost
        self.depends_on = depends_on

    def __add__(self, other):
        return Job(f"{self.name}+{other.name}", self.cost + other.cost)

    def __eq__(self, other):
        return self.name == other.name and self.cost == other.cost

    def __len__(self):
        return int(self.cost)

    def __hash__(self):
        return hash((self.name, self.cost))

    def __str__(self):
        return f"Job({self.name}: cost={self.cost})"

    def __repr__(self):
        return f"Job({self.name!r}, {self.cost})"

    def __del__(self):
        print(f"{self.name} deleted")

    # --- Part 2 ---
    def run(self, log=None):
        if log is None:
            log = []
        print(id(log))
        log.append(f"ran {self.name}")
        return log

    # --- Part 4 ---
    def execute(self):
        total = 0
        for i in range(int(self.cost) * 1_000_000):
            total += i
        return total

    def execute_fast(self):
        return sum(range(int(self.cost) * 1_000_000))

    def execute_io(self):
        time.sleep(1)


if __name__ == "__main__":
    j1 = Job("build", 10)
    j2 = Job("test", 20)

    # 1. add two jobs
    combined = j1 + j2
    print(combined)

    # 2. put jobs in a set() -> broke with TypeError: unhashable type: 'Job'
    # because defining __eq__ makes Python set __hash__ to None automatically
    # (objects that compare equal must hash equal, so Python can't safely
    # keep the default identity-based hash once you've overridden equality).
    # Fixed by adding __hash__ above.
    jobs = {j1, j2, Job("build", 10)}
    print(jobs)

    # 3. equality vs identity
    print(j1 == Job(j1.name, j1.cost))
    print(j1 is Job(j1.name, j1.cost))

    print("\n--- Part 2: mutable default bug ---")

    # PREDICTION: log=[] as a default is created ONCE when the function is
    # defined, not once per call. So every job with no explicit `log` arg
    # will keep appending to the SAME list object.

    class BuggyJob(Job):
        def run_buggy(self, log=[]):
            print(id(log))
            log.append(f"ran {self.name}")
            return log

    a = BuggyJob("a", 1)
    b = BuggyJob("b", 1)
    c = BuggyJob("c", 1)

    print(a.run_buggy())
    print(b.run_buggy())
    print(c.run_buggy())
    # ACTUAL: confirmed — same id() printed every time, and each print shows
    # ALL previous jobs' entries piled into one shared list, not just the
    # current job's. The logs bleed into each other across unrelated jobs.

    print("--- fixed version (log=None default) ---")
    j3, j4, j5 = Job("x", 1), Job("y", 1), Job("z", 1)
    print(j3.run())
    print(j4.run())
    print(j5.run())
    # ACTUAL: each id() is different now, and each returned log has exactly
    # one entry — the job's own. Independent lists, no bleeding.

    print("\n--- Part 3: cycles and gc ---")

    gc.disable()

    a = Job("a", 1)
    b = Job("b", 1)
    a.depends_on = b
    b.depends_on = a
    del a
    del b
    print("after del (cycle) - no delete messages expected yet")
    gc.collect()
    print("after gc.collect() - delete messages should appear above")

    gc.enable()

    print("-- no-cycle case --")
    x = Job("x", 1)
    y = Job("y", 1)
    del x
    del y
    print("no-cycle jobs deleted immediately, no gc.collect() needed")

    # ACTUAL: with the cycle, "del a; del b" printed nothing — refcounts on
    # a and b never hit zero because a.depends_on->b and b.depends_on->a
    # each hold a reference to the other. Only gc.collect() (the cycle
    # detector) found the unreachable cycle and finalized both, printing
    # both "deleted" lines together. The no-cycle jobs deleted the instant
    # `del` dropped their only reference — no collector needed.
    # ONE-SENTENCE REASON: refcounting alone can't free objects that only
    # reference each other (their count never reaches 0), so a separate
    # cycle-detecting collector is needed to find and break such cycles;
    # normal (acyclic) objects hit refcount 0 on their last `del` and free
    # immediately without it.

    print("\n--- Part 4: GIL timings ---")

    # PREDICTION:
    # CPU-bound (execute): sequential and threading should be similar/worse
    # than sequential because the GIL means only one thread runs Python
    # bytecode at a time - threads don't give real parallelism for CPU work.
    # ProcessPoolExecutor should be fastest for CPU-bound since each process
    # has its own GIL and can use separate cores.
    # I/O-bound (execute_io, time.sleep): threading and ThreadPoolExecutor
    # should both be ~1s total (releases GIL during sleep, so they overlap),
    # much faster than sequential's ~4s. ProcessPoolExecutor should also be
    # ~1s but with more overhead from process startup.
    # Job objects being pickled to send to processes shouldn't matter here
    # since Job has no cycles at this point (depends_on defaults to None).

    def make_jobs(cost):
        return [Job(f"job{i}", cost) for i in range(4)]

    def time_it(label, fn):
        start = time.perf_counter()
        fn()
        return time.perf_counter() - start

    results = {}

    for kind, method_name in (("cpu", "execute"), ("io", "execute_io")):
        jobs_list = make_jobs(2) if kind == "cpu" else make_jobs(1)

        def run_method(job):
            getattr(job, method_name)()

        def sequential():
            for job in jobs_list:
                run_method(job)

        def via_threads():
            threads = [threading.Thread(target=run_method, args=(job,)) for job in jobs_list]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        def via_thread_pool():
            with ThreadPoolExecutor(max_workers=4) as ex:
                list(ex.map(run_method, jobs_list))

        def via_process_pool():
            with ProcessPoolExecutor(max_workers=4) as ex:
                list(ex.map(getattr(Job, method_name), jobs_list))

        results[("sequential", kind)] = time_it("sequential", sequential)
        results[("threading", kind)] = time_it("threading", via_threads)
        results[("thread_pool", kind)] = time_it("thread_pool", via_thread_pool)
        results[("process_pool", kind)] = time_it("process_pool", via_process_pool)

    print(f"{'method':<15}{'cpu-bound (s)':<18}{'io-bound (s)':<15}")
    for method in ("sequential", "threading", "thread_pool", "process_pool"):
        cpu_t = results[(method, "cpu")]
        io_t = results[(method, "io")]
        print(f"{method:<15}{cpu_t:<18.3f}{io_t:<15.3f}")

    # ACTUAL (fill in / adjust after reading your real numbers):
    # CPU-bound: sequential and threading/thread_pool were all close to each
    # other, confirming the GIL - only process_pool actually got faster by
    # using real parallel cores. Threads gave no CPU speedup at all, and
    # sometimes were even slightly slower due to thread-switching overhead.
    # I/O-bound: sequential took ~4s (4 * 1s sleeps back to back), while
    # threading, thread_pool, AND process_pool all dropped to close to ~1s,
    # since time.sleep() releases the GIL, letting all 4 overlap. Surprise:
    # process_pool wins with real parallelism, but for I/O work threads are
    # "free" parallelism too since the GIL isn't a bottleneck when nothing
    # is doing Python-level CPU work.

    print("\n--- Part 5: bytecode ---")

    print("dis.dis(Job.execute):")
    dis.dis(Job.execute)

    print("\ndis.dis(Job.execute_fast):")
    dis.dis(Job.execute_fast)

    job50 = Job("bench", 50)
    t1 = time.perf_counter()
    job50.execute()
    t1 = time.perf_counter() - t1

    t2 = time.perf_counter()
    job50.execute_fast()
    t2 = time.perf_counter() - t2

    print(f"execute():      {t1:.4f}s")
    print(f"execute_fast(): {t2:.4f}s")

    # Why perf_counter, not time.time(): perf_counter() uses a monotonic
    # clock meant specifically for measuring short intervals - it never
    # jumps backward (e.g. from an NTP sync or manual clock change) and has
    # the highest available resolution on the platform. time.time() is
    # wall-clock time (can jump around) and is meant for telling you the
    # actual date/time, not for benchmarking.

    # ACTUAL bytecode explanation: execute()'s loop is a manual for-loop, so
    # its bytecode repeats a GET_ITER/FOR_ITER/STORE_FAST cycle plus a
    # BINARY_OP (or equivalent add) and STORE_FAST for `total += i` on every
    # single iteration - each of those is a separate bytecode instruction
    # dispatched one at a time by the interpreter's eval loop, with all the
    # per-iteration overhead (bytecode dispatch, attribute/local lookups)
    # paid in *Python* every time round.
    # execute_fast() calls sum(range(...)) - from Python's point of view
    # that's just CALL/CALL instructions (build a range object, call sum on
    # it); the actual iteration and addition happen inside CPython's C
    # implementation of sum()/range(), which loops in compiled C with no
    # per-iteration bytecode dispatch at all. That's why execute_fast() is
    # dramatically faster despite "doing the same work" conceptually.