# proxy-detector

Tells what kind of account an EVM address is, and for proxies, where the code actually lives. Worth
checking before trusting a contract, since a proxy's code can be changed. It uses `eth_getCode` and
`eth_getStorageAt`.

```
$ python proxy.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48: contract, 2186 bytes of code
  legacy OpenZeppelin (zos) proxy
  implementation  0x43506849d7c04f9138d1a2050bbf3a0c054402dd
  target code     23464 bytes
```

USDC's `FiatTokenProxy` predates EIP-1967 and still uses the old zos slot, so checking only the
EIP-1967 slot would miss it.

```bash
python proxy.py 0x... --rpc https://bsc-dataseed.bnbchain.org
```

| pattern | how it's detected |
|---|---|
| EOA | no code |
| EIP-7702 delegated EOA | code is `0xef0100 ++ delegate address` |
| EIP-1167 minimal proxy (clone) | bytecode `363d3d373d3d3d363d73 <impl> 5af43d82803e903d91602b57fd5bf3` |
| EIP-1967 proxy | non-zero implementation slot `keccak256("eip1967.proxy.implementation") - 1` |
| EIP-1967 beacon proxy | beacon slot set, implementation read with `beacon.implementation()` |
| legacy OpenZeppelin proxy | slot `keccak256("org.zeppelinos.proxy.implementation")` |
| Safe proxy (likely) | small contract whose storage slot 0 holds the singleton address |

The EIP-1967 admin slot is printed as well. A non-zero admin means a transparent proxy that the admin
address can upgrade. A zero admin with an implementation set usually means UUPS, where the upgrade
logic is in the implementation.

## Tests

```bash
python -m unittest -v
```
