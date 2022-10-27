import os
import shutil


def _duplicate_tests_with_future_annotations():
    # Type annotations have different behavior with and without the declaration
    # of using the future style.  Duplicate the tests with future annotations to
    # ensure consistent behavior.
    this_folder = os.path.dirname(__file__)
    future_annotations_folder = os.path.join(this_folder, 'future_annotations')
    os.makedirs(future_annotations_folder, exist_ok=True)
    with open(os.path.join(future_annotations_folder, '__init__.py'), 'w') as f:
        pass
    for filename in os.listdir(this_folder):
        if (filename.startswith('test_') and filename.endswith('.py')) or filename.endswith('_test.py'):
            with open(os.path.join(this_folder, filename), 'r') as f:
                code = f.read()
            with open(os.path.join(future_annotations_folder, filename), 'w') as f:
                f.write('from __future__ import annotations\n')
                f.write(code)
        # TODO: recurse into subfolders if/when subfolders are created


def _remove_future_annotations_tests():
    this_folder = os.path.dirname(__file__)
    future_annotations_folder = os.path.join(this_folder, 'future_annotations')
    shutil.rmtree(future_annotations_folder)


def pytest_configure(config):
    _duplicate_tests_with_future_annotations()


def pytest_unconfigure(config):
    _remove_future_annotations_tests()
