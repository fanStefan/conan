import logging
import os

import patch_ng

from conans.errors import ConanException

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable


class PatchLogHandler(logging.Handler):
    def __init__(self, conanfile, patch_file):
        logging.Handler.__init__(self, logging.DEBUG)
        self._output = conanfile.output
        self.patchname = patch_file or "patch_ng"

    def emit(self, record):
        logstr = self.format(record)
        if record.levelno == logging.WARN:
            self._output.warn("%s: %s" % (self.patchname, logstr))
        else:
            self._output.info("%s: %s" % (self.patchname, logstr))


def patch(conanfile, base_path=None, patch_file=None, patch_string=None, strip=0, fuzz=False, **kwargs):
    """ Applies a diff from file (patch_file)  or string (patch_string)
        in base_path directory or current dir if None
    :param base_path: Base path where the patch should be applied.
    :param patch_file: Patch file that should be applied.
    :param patch_string: Patch string that should be applied.
    :param strip: Number of folders to be stripped from the path.
    :param output: Stream object.
    :param fuzz: Should accept fuzzy patches.
    :param kwargs: Extra parameters that can be added and will contribute to output information
    """

    patch_type = kwargs.get('patch_type')
    patch_description = kwargs.get('patch_description')

    if patch_type or patch_description:
        patch_type_str = ' ({})'.format(patch_type) if patch_type else ''
        patch_description_str = ': {}'.format(patch_description) if patch_description else ''
        conanfile.output.info('Apply patch{}{}'.format(patch_type_str, patch_description_str))

    patchlog = logging.getLogger("patch_ng")
    patchlog.handlers = []
    patchlog.addHandler(PatchLogHandler(conanfile, patch_file))

    if patch_file:
        patchset = patch_ng.fromfile(patch_file)
    else:
        patchset = patch_ng.fromstring(patch_string.encode())

    if not patchset:
        raise ConanException("Failed to parse patch: %s" % (patch_file if patch_file else "string"))

    root = os.path.join(conanfile.source_folder, base_path) if base_path else conanfile.source_folder
    if not patchset.apply(strip=strip, root=root, fuzz=fuzz):
        raise ConanException("Failed to apply patch: %s" % patch_file)


def apply_conandata_patches(conanfile):
    """
    Applies patches stored in 'conanfile.conan_data' (read from 'conandata.yml' file). It will apply
    all the patches under 'patches' entry that matches the given 'conanfile.version'. If versions are
    not defined in 'conandata.yml' it will apply all the patches directly under 'patches' keyword.

    Example of 'conandata.yml' without versions defined:

    ```
    patches:
    - patch_file: "patches/0001-buildflatbuffers-cmake.patch"
      base_path: "source_subfolder"
    - patch_file: "patches/0002-implicit-copy-constructor.patch"
      patch_type: backport
      patch_source: https://github.com/google/flatbuffers/pull/5650
      patch_description: Needed to build with modern clang compilers (adapted to 1.11.0 tagged sources).
    ```

    Example of 'conandata.yml' with different patches for different versions:
    ```
    patches:
      "1.11.0":
        - patch_file: "patches/0001-buildflatbuffers-cmake.patch"
        - patch_file: "patches/0002-implicit-copy-constructor.patch"
          patch_type: backport
          patch_source: https://github.com/google/flatbuffers/pull/5650
          patch_description: Needed to build with modern clang compilers (adapted to 1.11.0 tagged sources).
      "1.12.0":
        - patch_file: "patches/0001-buildflatbuffers-cmake.patch"
    ```
    """

    patches = conanfile.conan_data.get('patches')

    if isinstance(patches, dict):
        assert conanfile.version, "Can only be applied if conanfile.version is already defined"
        entries = patches.get(conanfile.version, [])
    elif isinstance(patches, Iterable):
        entries = patches
    else:
        return
    for it in entries:
        if "patch_file" in it:
            # The patch files are located in the root src
            patch_file = os.path.join(conanfile.folders.base_source, it.pop("patch_file"))
            patch(conanfile, patch_file=patch_file, **it)
        elif "patch_string" in it:
            patch(conanfile, **it)
        else:
            raise ConanException("The 'conandata.yml' file needs a 'patch_file' or 'patch_string'"
                                 " entry for every patch to be applied")
