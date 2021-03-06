import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
import shutil
import unittest
import requests
from chazutsu.datasets.framework.dataset import Dataset


class SampleDataset(Dataset):

    def __init__(self):
        super().__init__(
            name="sample_dataset",
            site_url="https://github.com/chakki-works/chazutsu",
            download_url="https://github.com/chakki-works/chazutsu/archive/master.zip",
            description="sample dataset"
            )

    def extract(self, path):
        extracted = self.extract_file(path, "chazutsu-master/README.md")
        return extracted[0]


DATA_ROOT = os.path.join(os.path.dirname(__file__), "data")


class TestDataset(unittest.TestCase):

    def test_save_dataset(self):
        d = SampleDataset()
        path = d.save_dataset(DATA_ROOT)
        os.remove(path)
        self.assertTrue(path)
    
    def test_extract_file_zip(self):
        d = SampleDataset()
        path = d.save_dataset(DATA_ROOT)
        extracteds = d.extract_file(path, ["chazutsu-master/README.md", "chazutsu-master/docs/chazutsu.png"])
        for e in extracteds:
            os.remove(e)
        self.assertEqual(len(extracteds), 2)

    def test_extract_file_tar_gz(self):
        d = SampleDataset()
        d.download_url = d.download_url.replace(".zip", ".tar.gz")
        path = d.save_dataset(DATA_ROOT)
        extracteds = d.extract_file(path, ["chazutsu-master/LICENSE", "chazutsu-master/docs/feature.png"])
        for e in extracteds:
            os.remove(e)
        self.assertEqual(len(extracteds), 2)
        
    def test_train_test_split(self):
        sample_file_path = self._download_sample_file("for_split.txt")
        d = SampleDataset()
        test_size = 0.3
        total_count = d.get_line_count(sample_file_path)
        train_test_path = d.train_test_split(sample_file_path, test_size=test_size, keep_raw=False)
        test_count = d.get_line_count(train_test_path[1])

        self.assertFalse(os.path.exists(sample_file_path))
        for p in train_test_path:
            os.remove(p)

        self.assertTrue(test_count / total_count - test_size < 0.01)

    def test_make_samples(self):
        sample_file_path = self._download_sample_file("for_sample.txt")
        d = SampleDataset()
        sample_count = 30
        samples_path = d.make_samples(sample_file_path, sample_count=sample_count)
        line_count = d.get_line_count(samples_path)

        for p in [sample_file_path, samples_path]:
            os.remove(p)
        
        self.assertEqual(sample_count, line_count)
    
    def test_download(self):
        d = SampleDataset()
        resource = d.download(DATA_ROOT, sample_count=10)
        df = resource.data()

        shutil.rmtree(resource.root)
        self.assertTrue(resource.train_file_path)
        self.assertTrue(resource.test_file_path)
        self.assertTrue(resource.sample_file_path)
    
    def test_label_by_dir(self):
        test_root = os.path.join(DATA_ROOT, "test_label")
        if not os.path.exists(test_root):
            os.mkdir(test_root)
            for d in ["pos", "neg"]:
                os.mkdir(os.path.join(test_root, d))
                for f in ["test_" + d + "_{}.txt".format(i) for i in range(100)]:
                    p = os.path.join(test_root, d + "/" + f)
                    with open(p, mode="w", encoding="utf-8") as f:
                        f.write("source {}".format(p))
        
        d = SampleDataset()
        p = os.path.join(test_root, "test_label_by_dir.txt")
        d.label_by_dir(p, test_root, {"pos": 1, "neg": 0}, task_size=10)

        count = d.get_line_count(p)
        shutil.rmtree(test_root)
        self.assertEqual(100 * 2, count)

    def _download_sample_file(self, file_name):
        sample_file = "https://raw.githubusercontent.com/chakki-works/chazutsu/master/README.md"
        sample_file_path = os.path.join(DATA_ROOT, file_name)
        r = requests.get(sample_file)

        with open(sample_file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=128):
                f.write(chunk)

        return sample_file_path


if __name__ == "__main__":
    unittest.main()
