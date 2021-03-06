#!/usr/bin/env python
# Copyright (c) PLUMgrid, Inc.
# Licensed under the Apache License, Version 2.0 (the "License")

from bcc import BPF
import ctypes as ct
import random
import time
from unittest import main, TestCase

class TestArray(TestCase):
    def test_simple(self):
        b = BPF(text="""BPF_TABLE("array", int, u64, table1, 128);""")
        t1 = b["table1"]
        t1[ct.c_int(0)] = ct.c_ulonglong(100)
        t1[ct.c_int(127)] = ct.c_ulonglong(1000)
        for i, v in t1.items():
            if i.value == 0:
                self.assertEqual(v.value, 100)
            if i.value == 127:
                self.assertEqual(v.value, 1000)
        self.assertEqual(len(t1), 128)

    def test_native_type(self):
        b = BPF(text="""BPF_TABLE("array", int, u64, table1, 128);""")
        t1 = b["table1"]
        t1[0] = ct.c_ulonglong(100)
        t1[-2] = ct.c_ulonglong(37)
        t1[127] = ct.c_ulonglong(1000)
        for i, v in t1.items():
            if i.value == 0:
                self.assertEqual(v.value, 100)
            if i.value == 127:
                self.assertEqual(v.value, 1000)
        self.assertEqual(len(t1), 128)
        self.assertEqual(t1[-2].value, 37)
        self.assertEqual(t1[-1].value, t1[127].value)

    def test_perf_buffer(self):
        self.counter = 0

        class Data(ct.Structure):
            _fields_ = [("ts", ct.c_ulonglong)]

        def cb(cpu, data, size):
            self.assertGreater(size, ct.sizeof(Data))
            event = ct.cast(data, ct.POINTER(Data)).contents
            self.counter += 1

        text = """
BPF_PERF_OUTPUT(events);
int kprobe__sys_nanosleep(void *ctx) {
    struct {
        u64 ts;
    } data = {bpf_ktime_get_ns()};
    events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
"""
        b = BPF(text=text)
        b["events"].open_perf_buffer(cb)
        time.sleep(0.1)
        b.kprobe_poll()
        self.assertGreater(self.counter, 0)

if __name__ == "__main__":
    main()
