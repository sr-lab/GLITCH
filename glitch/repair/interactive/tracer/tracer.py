import subprocess
import threading

from typing import List
from glitch.repair.interactive.tracer.parser import parse_tracer_output
from glitch.repair.interactive.tracer.model import get_syscall_with_type, Syscall


class STrace(threading.Thread):
    def __init__(self, pid: str) -> None:
        threading.Thread.__init__(self)
        self.syscalls: List[Syscall] = []
        self.pid = pid

    def run(self) -> List[Syscall]:  # type: ignore
        proc = subprocess.Popen(
            [
                "sudo",
                "strace",
                "-v",
                "-s",
                "65536",
                "-e",
                "trace=file",
                "-f",
                "-p",
                self.pid,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        if proc.stdout is None:
            return self.syscalls

        for line in proc.stdout:
            if (
                line.startswith("strace: Process")
                or "+++ exited with" in line
                or "--- SIG" in line
            ):
                continue
            syscall = get_syscall_with_type(parse_tracer_output(line))
            if "/bin/synth-glitch" in syscall.args:
                # TODO don't break and just update
                break
            self.syscalls.append(syscall)

        return self.syscalls
