import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import proxy
from proxy import classify_code, slot_address

IMPL = "bebebebebebebebebebebebebebebebebebebebe"


class ProxyTest(unittest.TestCase):
    def test_eoa(self):
        self.assertEqual(classify_code("0x"), ("eoa", None))

    def test_7702_delegation(self):
        self.assertEqual(classify_code("0xef0100" + IMPL), ("7702", "0x" + IMPL))

    def test_eip1167_clone(self):
        code = "0x363d3d373d3d3d363d73" + IMPL + "5af43d82803e903d91602b57fd5bf3"
        self.assertEqual(classify_code(code), ("clone", "0x" + IMPL))

    def test_regular_contract(self):
        self.assertEqual(classify_code("0x6080604052"), ("contract", None))

    @patch("proxy.rpc")
    def test_beacon_without_implementation_does_not_crash(self, mock_rpc):
        beacon_word = "0x" + "0" * 24 + "12" * 20
        zero_word = "0x" + "0" * 64

        def fake_rpc(_url, method, params):
            if method == "eth_getCode":
                return "0x6000"
            if method == "eth_getStorageAt":
                return beacon_word if params[1] == proxy.BEACON_SLOT else zero_word
            if method == "eth_call":
                return zero_word
            raise AssertionError(f"unexpected RPC method: {method}")

        mock_rpc.side_effect = fake_rpc
        output = io.StringIO()
        with patch("sys.argv", ["proxy.py", "0x1111111111111111111111111111111111111111"]), redirect_stdout(output):
            proxy.main()

        self.assertIn("implementation  none (beacon returned zero address)", output.getvalue())
        self.assertNotIn("target code", output.getvalue())

    def test_slot_address(self):
        self.assertIsNone(slot_address("0x" + "0" * 64))
        self.assertEqual(slot_address("0x" + "0" * 24 + IMPL), "0x" + IMPL)
        self.assertIsNone(slot_address("0x"))


if __name__ == "__main__":
    unittest.main()
