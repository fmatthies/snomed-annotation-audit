import pathlib
import tempfile
import unittest

import h5py
import numpy as np

from snomed_annotation_audit.hdf5_handling.metadata import (
    inspect_hdf5_metadata,
    format_hdf5_metadata_summary,
)

_STRING_DTYPE = h5py.string_dtype(encoding="utf-8")


class TestHdf5MetadataSummary(unittest.TestCase):
    def test_summarizes_compact_audit_ready_hdf5(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hdf5_path = pathlib.Path(tmpdir) / "concepts.hdf5"
            with h5py.File(hdf5_path, "w") as h5_file:
                concepts = h5_file.create_group("concepts")
                concepts.attrs["policy_date"] = "20240401"
                concepts.attrs["release_date"] = "20260401"
                concepts.attrs["rf2_view"] = "full"
                concepts.create_dataset("codes", data=np.asarray(["100", "200"], dtype=object), dtype=_STRING_DTYPE)
                concepts.create_dataset("fsn", data=np.asarray(["Old (finding)", "New (finding)"], dtype=object), dtype=_STRING_DTYPE)
                concepts.create_dataset("active", data=np.asarray([False, True], dtype=bool))
                policy_views = h5_file.create_group("policy_views")
                whitelist = policy_views.create_group("whitelist").create_group("0")
                whitelist.create_dataset("concept_index", data=np.asarray([1], dtype=np.int64))
                blacklist = policy_views.create_group("blacklist").create_group("0")
                blacklist.create_dataset("concept_index", data=np.asarray([], dtype=np.int64))

            summary = inspect_hdf5_metadata(hdf5_path)
            text = format_hdf5_metadata_summary(summary)
            markdown = format_hdf5_metadata_summary(summary, markdown=True, include_path=False)

        self.assertTrue(summary.audit_ready)
        self.assertEqual(summary.concept_count, 2)
        self.assertEqual(summary.active_concept_count, 1)
        self.assertIn("Audit-ready: yes", text)
        self.assertIn("inclusion list/0: 1 concepts", text)
        self.assertNotIn("Historical associations", text)
        self.assertNotIn("Semantic tags", text)
        self.assertIn("### HDF5 metadata summary", markdown)
        self.assertNotIn(str(hdf5_path), markdown)


if __name__ == "__main__":
    unittest.main()
