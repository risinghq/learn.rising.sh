"""Put limits on the job and run the learner's command.

    python -S launcher.py UID CPU_S DATA_BYTES FSIZE_BYTES NPROC -- COMMAND...

`sandbox.py` launches it as root. It sets the rlimits, drops the uid, restricts
sockets to AF_UNIX with seccomp and runs the command. If the `exec` fails, nothing starts.
"""

import ctypes
import os
import platform
import resource
import struct
import sys

PR_SET_NO_NEW_PRIVS = 38
PR_SET_SECCOMP = 22
SECCOMP_MODE_FILTER = 2

BPF_LD_W_ABS = 0x20
BPF_JEQ_K = 0x15
BPF_JGE_K = 0x35
BPF_RET_K = 0x06

RET_ALLOW = 0x7FFF0000
RET_KILL_PROCESS = 0x80000000
RET_ERRNO = 0x00050000
EACCES = 13
AF_UNIX = 1
X32_SYSCALL_BIT = 0x40000000

# machine -> (AUDIT_ARCH, number of the socket syscall)
ARCHES = {
    "x86_64": (0xC000003E, 41),
    "aarch64": (0xC00000B7, 198),
}


def socket_filter() -> tuple[bytes, int]:
    """Allow everything except socket(domain != AF_UNIX), which gets EACCES."""
    machine = platform.machine()
    if machine not in ARCHES:
        raise SystemExit(f"launcher: no network filter for {machine}")
    arch, sys_socket = ARCHES[machine]
    # Each tuple holds code, jt, jf and k.
    # Jumps are relative to the next instruction.
    prog = [
        (BPF_LD_W_ABS, 0, 0, 4),  # 0 arch
        (BPF_JEQ_K, 0, 7, arch),  # 1 other architecture: kill
        (BPF_LD_W_ABS, 0, 0, 0),  # 2 syscall number
        (BPF_JGE_K, 3, 0, X32_SYSCALL_BIT),  # 3 x32 ABI: deny
        (BPF_JEQ_K, 0, 3, sys_socket),  # 4 not socket: allow
        (BPF_LD_W_ABS, 0, 0, 16),  # 5 args[0], the domain
        (BPF_JEQ_K, 1, 0, AF_UNIX),  # 6 AF_UNIX: allow
        (BPF_RET_K, 0, 0, RET_ERRNO | EACCES),  # 7 deny
        (BPF_RET_K, 0, 0, RET_ALLOW),  # 8 allow
        (BPF_RET_K, 0, 0, RET_KILL_PROCESS),  # 9 kill
    ]
    return b"".join(struct.pack("=HBBI", *ins) for ins in prog), len(prog)


def install_seccomp() -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_NO_NEW_PRIVS")
    raw, count = socket_filter()
    buf = ctypes.create_string_buffer(raw, len(raw))

    class SockFprog(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]

    fprog = SockFprog(count, ctypes.addressof(buf))
    if libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(fprog), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_SECCOMP")


def main() -> None:
    argv = sys.argv[1:]
    sep = argv.index("--")
    uid, cpu_s, data_b, fsize_b, nproc = map(int, argv[:sep])
    cmd = argv[sep + 1 :]

    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
    resource.setrlimit(resource.RLIMIT_DATA, (data_b, data_b))
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize_b, fsize_b))
    resource.setrlimit(resource.RLIMIT_NPROC, (nproc, nproc))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))

    os.setgroups([])
    os.setgid(uid)
    os.setuid(uid)
    install_seccomp()
    os.execv(cmd[0], cmd)


if __name__ == "__main__":
    main()
