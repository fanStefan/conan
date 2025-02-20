import os
import textwrap

import pytest
from mock import Mock

from conan.tools.microsoft import MSBuild, MSBuildToolchain
from conans.model.conf import ConfDefinition, Conf
from conans.model.env_info import EnvValues
from conans.test.utils.mocks import ConanFileMock, MockSettings
from conans.test.utils.test_files import temp_folder
from conans.tools import load
from conans import ConanFile, Settings


def test_msbuild_cpu_count():
    c = ConfDefinition()
    c.loads(textwrap.dedent("""\
        tools.microsoft.msbuild:max_cpu_count=23
        tools.build:processes=10
    """))

    settings = MockSettings({"build_type": "Release",
                             "compiler": "gcc",
                             "compiler.version": "7",
                             "os": "Linux",
                             "arch": "x86_64"})
    conanfile = ConanFileMock()
    conanfile.settings = settings
    conanfile.conf = c.get_conanfile_conf(None)

    msbuild = MSBuild(conanfile)
    cmd = msbuild.command('project.sln')

    assert '/m:23' in cmd


def test_msbuild_toolset():
    settings = Settings({"build_type": ["Release"],
                         "compiler": {"msvc": {"version": ["19.3"]}},
                         "os": ["Windows"],
                         "arch": ["x86_64"]})
    conanfile = ConanFile(Mock(), None)
    conanfile.settings = "os", "compiler", "build_type", "arch"
    conanfile.initialize(settings, EnvValues())
    conanfile.settings.build_type = "Release"
    conanfile.settings.compiler = "msvc"
    conanfile.settings.compiler.version = "19.3"
    conanfile.settings.os = "Windows"
    conanfile.settings.arch = "x86_64"

    msbuild = MSBuildToolchain(conanfile)
    assert 'v143' in msbuild.toolset


@pytest.mark.parametrize("mode,expected_toolset", [
    ("icx", "Intel C++ Compiler 2021"),
    ("dpcpp", "Intel(R) oneAPI DPC++ Compiler"),
    ("classic", "Intel C++ Compiler 19.2")
])
def test_msbuild_toolset_for_intel_cc(mode, expected_toolset):
    settings = Settings({"build_type": ["Release"],
                         "compiler": {"intel-cc": {"version": ["2021.3"], "mode": [mode]},
                                      "msvc": {"version": ["19.3"], "cppstd": ["20"]}},
                         "os": ["Windows"],
                         "arch": ["x86_64"]})
    conanfile = ConanFile(Mock(), None)
    conanfile.settings = "os", "compiler", "build_type", "arch"
    conanfile.initialize(settings, EnvValues())
    conanfile.settings.build_type = "Release"
    conanfile.settings.compiler = "intel-cc"
    conanfile.settings.compiler.version = "2021.3"
    conanfile.settings.compiler.mode = mode
    conanfile.settings.os = "Windows"
    conanfile.settings.arch = "x86_64"

    msbuild = MSBuildToolchain(conanfile)
    assert expected_toolset == msbuild.toolset


def test_msbuild_standard():
    test_folder = temp_folder()

    settings = Settings({"build_type": ["Release"],
                         "compiler": {"msvc": {"version": ["19.3"], "cppstd": ["20"]}},
                         "os": ["Windows"],
                         "arch": ["x86_64"]})
    conanfile = ConanFile(Mock(), None)
    conanfile.folders.set_base_generators(test_folder)
    conanfile.install_folder = test_folder
    conanfile.conf = Conf()
    conanfile.conf["tools.microsoft.msbuild:installation_path"] = "."
    conanfile.settings = "os", "compiler", "build_type", "arch"
    conanfile.initialize(settings, EnvValues())
    conanfile.settings.build_type = "Release"
    conanfile.settings.compiler = "msvc"
    conanfile.settings.compiler.version = "19.3"
    conanfile.settings.compiler.cppstd = "20"
    conanfile.settings.os = "Windows"
    conanfile.settings.arch = "x86_64"

    msbuild = MSBuildToolchain(conanfile)
    props_file = os.path.join(test_folder, 'conantoolchain_release_x64.props')
    msbuild.generate()
    assert '<LanguageStandard>stdcpp20</LanguageStandard>' in load(props_file)


def test_resource_compile():
    test_folder = temp_folder()

    settings = Settings({"build_type": ["Release"],
                         "compiler": {"msvc": {"version": ["19.3"], "cppstd": ["20"]}},
                         "os": ["Windows"],
                         "arch": ["x86_64"]})
    conanfile = ConanFile(Mock(), None)
    conanfile.folders.set_base_generators(test_folder)
    conanfile.install_folder = test_folder
    conanfile.conf = Conf()
    conanfile.conf["tools.microsoft.msbuild:installation_path"] = "."
    conanfile.settings = "os", "compiler", "build_type", "arch"
    conanfile.settings_build = settings
    conanfile.initialize(settings, EnvValues())
    conanfile.settings.build_type = "Release"
    conanfile.settings.compiler = "msvc"
    conanfile.settings.compiler.version = "19.3"
    conanfile.settings.compiler.cppstd = "20"
    conanfile.settings.os = "Windows"
    conanfile.settings.arch = "x86_64"

    msbuild = MSBuildToolchain(conanfile)
    msbuild.preprocessor_definitions["MYTEST"] = "MYVALUE"
    props_file = os.path.join(test_folder, 'conantoolchain_release_x64.props')
    msbuild.generate()
    expected = """
        <ResourceCompile>
          <PreprocessorDefinitions>
             MYTEST=MYVALUE;%(PreprocessorDefinitions)
          </PreprocessorDefinitions>
        </ResourceCompile>"""
    props_file = load(props_file)  # Remove all blanks and CR to compare
    props_file = "".join(s.strip() for s in props_file.splitlines())
    assert "".join(s.strip() for s in expected.splitlines()) in props_file


@pytest.mark.parametrize("mode,expected_toolset", [
    ("icx", "Intel C++ Compiler 2021"),
    ("dpcpp", "Intel(R) oneAPI DPC++ Compiler"),
    ("classic", "Intel C++ Compiler 19.2")
])
def test_msbuild_and_intel_cc_props(mode, expected_toolset):
    test_folder = temp_folder()
    settings = Settings({"build_type": ["Release"],
                         "compiler": {"intel-cc": {"version": ["2021.3"], "mode": [mode]},
                                      "msvc": {"version": ["19.3"], "cppstd": ["20"]}},
                         "os": ["Windows"],
                         "arch": ["x86_64"]})
    conanfile = ConanFile(Mock(), None)
    conanfile.folders.set_base_generators(test_folder)
    conanfile.install_folder = test_folder
    conanfile.conf = Conf()
    conanfile.conf["tools.intel:installation_path"] = "my/intel/oneapi/path"
    conanfile.conf["tools.microsoft.msbuild:installation_path"] = "."
    conanfile.settings = "os", "compiler", "build_type", "arch"
    conanfile.initialize(settings, EnvValues())
    conanfile.settings.build_type = "Release"
    conanfile.settings.compiler = "intel-cc"
    conanfile.settings.compiler.version = "2021.3"
    conanfile.settings.compiler.mode = mode
    conanfile.settings.os = "Windows"
    conanfile.settings.arch = "x86_64"

    msbuild = MSBuildToolchain(conanfile)
    props_file = os.path.join(test_folder, 'conantoolchain_release_x64.props')
    msbuild.generate()
    assert '<PlatformToolset>%s</PlatformToolset>' % expected_toolset in load(props_file)
