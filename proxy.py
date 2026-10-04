"""Classify an EVM address: EOA, delegated EOA, clone, proxy or contract."""
import argparse
import json
import urllib.request

IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
ZOS_SLOT = "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"
CLONE_PREFIX = "363d3d373d3d3d363d73"
CLONE_SUFFIX = "5af43d82803e903d91602b57fd5bf3"
DELEGATION_PREFIX = "ef0100"
IMPLEMENTATION = "0x5c60da1b"


def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "proxy-detector"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(resp["error"].get("message"))
    return resp["result"]


def slot_address(word):
    """Address stored in the low 20 bytes of a storage word, or None if the word is zero."""
    v = int(word, 16) if word and word != "0x" else 0
    return None if v == 0 else "0x" + format(v, "064x")[-40:]


def classify_code(code_hex):
    code = code_hex[2:].lower() if code_hex else ""
    if not code:
        return "eoa", None
    if code.startswith(DELEGATION_PREFIX) and len(code) == 46:
        return "7702", "0x" + code[6:]
    if code.startswith(CLONE_PREFIX) and code.endswith(CLONE_SUFFIX) and len(code) == 90:
        return "clone", "0x" + code[20:60]
    return "contract", None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("address")
    ap.add_argument("--rpc", default="https://ethereum-rpc.publicnode.com")
    a = ap.parse_args()
    addr = a.address
    code = rpc(a.rpc, "eth_getCode", [addr, "latest"])
    kind, target = classify_code(code)
    size = (len(code) - 2) // 2

    if kind == "eoa":
        print(f"{addr}: externally owned account (no code)")
        return
    if kind == "7702":
        print(f"{addr}: EOA with EIP-7702 delegation\n  delegate code at {target}")
        return
    if kind == "clone":
        print(f"{addr}: EIP-1167 minimal proxy (clone), {size} bytes\n  implementation {target} (immutable)")
        return

    storage = lambda slot: slot_address(rpc(a.rpc, "eth_getStorageAt", [addr, slot, "latest"]))
    impl, admin, beacon, zos = storage(IMPL_SLOT), storage(ADMIN_SLOT), storage(BEACON_SLOT), storage(ZOS_SLOT)
    print(f"{addr}: contract, {size} bytes of code")
    if beacon:
        impl = slot_address(rpc(a.rpc, "eth_call", [{"to": beacon, "data": IMPLEMENTATION}, "latest"]))
        print(f"  EIP-1967 beacon proxy\n  beacon          {beacon}\n  implementation  {impl}")
    elif impl:
        style = "transparent (admin set)" if admin else "UUPS or admin elsewhere (admin slot empty)"
        print(f"  EIP-1967 proxy, {style}\n  implementation  {impl}")
        if admin:
            print(f"  admin           {admin}")
    elif zos:
        print(f"  legacy OpenZeppelin (zos) proxy\n  implementation  {zos}")
    else:
        slot0 = storage("0x0")
        if size < 200 and slot0:
            print(f"  small contract with an address in slot 0, likely a Safe proxy\n  singleton       {slot0}")
        else:
            print("  no proxy pattern found: code is not upgradeable through a standard slot")
            return
    target = impl or zos or slot0
    if target:
        impl_size = (len(rpc(a.rpc, "eth_getCode", [target, "latest"])) - 2) // 2
        print(f"  target code     {impl_size} bytes")


if __name__ == "__main__":
    main()
