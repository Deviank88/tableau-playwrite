import unittest

from tableau_operator.models import BiSpec


class BiSpecTests(unittest.TestCase):
    def test_validates_project_references(self):
        with self.assertRaisesRegex(ValueError, "unknown project"):
            BiSpec.from_dict(
                {
                    "name": "Sales BI",
                    "projects": [{"name": "Sandbox"}],
                    "datasources": [{"name": "Sales", "project": "Missing"}],
                }
            )

    def test_stable_hash_is_deterministic(self):
        data = {"name": "Sales BI", "projects": [{"name": "Sandbox"}]}
        self.assertEqual(BiSpec.from_dict(data).stable_hash(), BiSpec.from_dict(data).stable_hash())


if __name__ == "__main__":
    unittest.main()

