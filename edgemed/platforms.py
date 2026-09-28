"""Supported native runtime targets; Python alone is not the platform boundary."""

import platform


def target(system=None, machine=None):
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    if machine in {"arm64", "aarch64"}:
        arch = "arm64"
    elif machine in {"x86_64", "amd64"}:
        arch = "x86_64"
    else:
        raise RuntimeError(f"Unsupported native architecture: {machine}; 64-bit ARM or x86-64 is required")
    if system == "Darwin":
        return f"macos-{arch}"
    if system == "Linux":
        return f"linux-{arch}"
    raise RuntimeError(f"Unsupported native operating system: {system}")
