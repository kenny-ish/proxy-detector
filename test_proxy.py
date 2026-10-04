import unittest

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

    def test_slot_address(self):
        self.assertIsNone(slot_address("0x" + "0" * 64))
        self.assertEqual(slot_address("0x" + "0" * 24 + IMPL), "0x" + IMPL)
        self.assertIsNone(slot_address("0x"))


if __name__ == "__main__":
    unittest.main()
