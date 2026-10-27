"""Data message format between the checker and the learner's process.

Messages are length-prefixed JSON and never deserialize code.
"""

import base64
import io
import json
import os
import re
import struct
import sys
from typing import Any

MESSAGE_CAP = 4 * 2**20
DTYPE = re.compile(r"[<>|=]?[biufc]\d{1,2}")
BROKEN = "Tu código terminó o rompió el canal antes de dar un resultado."


def _qpy_bytes(circuit: Any, qpy: Any) -> bytes:
    buffer = io.BytesIO()
    qpy.dump(circuit, buffer)
    return buffer.getvalue()


class WireError(Exception):
    """The other end closed the channel or sent something that is not a valid message."""


def encode(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, tuple):
        return {"$": "tuple", "v": [encode(v) for v in value]}
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise TypeError("un diccionario con claves que no son texto")
        return {"$": "dict", "v": {k: encode(v) for k, v in value.items()}}
    if isinstance(value, complex):
        return {"$": "complex", "v": [value.real, value.imag]}
    if isinstance(value, bytes):
        return {"$": "bytes", "v": base64.b64encode(value).decode("ascii")}
    np = sys.modules.get("numpy")
    if np is not None:
        if isinstance(value, np.generic):
            return encode(value.item())
        if isinstance(value, np.ndarray) and value.dtype.kind in "biufc":
            return {"$": "array", "dtype": value.dtype.str, "v": encode(value.tolist())}
    if "qiskit" in sys.modules:
        from qiskit import QuantumCircuit, qpy
        from qiskit.quantum_info import (  # type: ignore[attr-defined]
            Operator,
            SparsePauliOp,
            Statevector,
        )

        if isinstance(value, QuantumCircuit):
            data = _qpy_bytes(value, qpy)
            try:
                qpy.load(io.BytesIO(data))
            except Exception:
                # qpy.dump accepts circuits that qpy.load cannot read. Retry
                # with the circuit decomposed into basic gates.
                data = _qpy_bytes(value.decompose(), qpy)
            return {"$": "circuit", "v": base64.b64encode(data).decode("ascii")}
        if isinstance(value, SparsePauliOp):
            return {"$": "sparse_pauli_op", "v": encode(value.to_list())}
        if isinstance(value, Statevector):
            return {"$": "statevector", "v": encode(value.data), "dims": list(value.dims())}
        if isinstance(value, Operator):
            return {
                "$": "operator",
                "v": encode(value.data),
                "in": list(value.input_dims()),
                "out": list(value.output_dims()),
            }
    raise TypeError(f"un valor de tipo {type(value).__name__}")


def decode(obj: Any) -> Any:
    if isinstance(obj, list):
        return [decode(v) for v in obj]
    if not isinstance(obj, dict):
        return obj
    kind: Any = obj.get("$")
    v: Any = obj.get("v")
    if kind == "tuple":
        return tuple(decode(x) for x in v)
    if kind == "dict":
        return {k: decode(x) for k, x in v.items()}
    if kind == "complex":
        return complex(v[0], v[1])
    if kind == "array":
        import numpy as np

        dtype = obj["dtype"]
        if not DTYPE.fullmatch(dtype):
            raise WireError(f"unsupported dtype: {dtype!r}")
        return np.array(decode(v), dtype=dtype)
    if kind == "bytes":
        return base64.b64decode(v, validate=True)
    if kind == "statevector":
        from qiskit.quantum_info import Statevector

        return Statevector(decode(v), dims=tuple(obj["dims"]))
    if kind == "operator":
        from qiskit.quantum_info import Operator

        return Operator(decode(v), input_dims=tuple(obj["in"]), output_dims=tuple(obj["out"]))
    if kind == "circuit":
        from qiskit import qpy

        return qpy.load(io.BytesIO(base64.b64decode(v, validate=True)))[0]
    if kind == "sparse_pauli_op":
        from qiskit.quantum_info import SparsePauliOp  # type: ignore[attr-defined]

        return SparsePauliOp.from_list(decode(v))
    raise WireError("a value with an unknown type")


def send(fd: int, message: dict[str, Any]) -> None:
    data = json.dumps(message).encode("utf-8")
    if len(data) > MESSAGE_CAP:
        raise WireError("message too large")
    view = memoryview(struct.pack(">I", len(data)) + data)
    try:
        while view:
            view = view[os.write(fd, view) :]
    except OSError as e:
        raise WireError(f"could not write: {e}") from e


def _read(fd: int, size: int) -> bytes:
    chunks: list[bytes] = []
    while size:
        try:
            chunk = os.read(fd, min(size, 65536))
        except OSError as e:
            raise WireError(f"could not read: {e}") from e
        if not chunk:
            raise WireError("the channel closed")
        chunks.append(chunk)
        size -= len(chunk)
    return b"".join(chunks)


def receive(fd: int) -> dict[str, Any]:
    (size,) = struct.unpack(">I", _read(fd, 4))
    if size > MESSAGE_CAP:
        raise WireError("message too large")
    try:
        message = json.loads(_read(fd, size))
    except (ValueError, RecursionError) as e:
        raise WireError("the message is not JSON") from e
    if not isinstance(message, dict):
        raise WireError("the message is not an object")
    return message
