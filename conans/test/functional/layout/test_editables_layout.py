import textwrap

from conans.test.assets.genconanfile import GenConanfile
from conans.test.utils.tools import TestClient


def test_cpp_info_editable():

    client = TestClient()

    conan_hello = str(GenConanfile().with_import("import os"))
    conan_hello += """
    def layout(self):
        self.folders.source = "my_sources"
        self.folders.build = "my_build"

        self.cpp.local.includedirs = [os.path.join(self.folders.source, "my_include_source"),
                                      os.path.join(self.folders.build, "my_include")]
        self.cpp.local.libdirs = [os.path.join(self.folders.build, "my_libdir")]
        self.cpp.local.libs = ["hello"]
        self.cpp.local.frameworkdirs = []  # Empty list is also explicit priority declaration
        self.cpp.local.cxxflags = ["my_cxx_flag"]
        self.cpp.local.builddirs = [os.path.join(self.folders.source, "my_builddir_source")]

        self.cpp.package.libs = ["lib_when_package"]

    def package_info(self):
        # when editable: This one will be discarded because declared in build
        self.cpp_info.includedirs = ["package_include"]

        # when editable: This one will be discarded because declared in build
        self.cpp_info.libs.append("lib_when_package2")

        # when editable: This one will be discarded because declared in source
        self.cpp_info.cxxflags.append("my_cxx_flag2")

        # when editable: This one will be discarded because declared in source
        self.cpp_info.frameworkdirs.append("package_frameworks_path")

        # when editable: This one WONT be discarded as has not been declared in the editables layout
        self.cpp_info.cflags.append("my_c_flag")

     """

    client.save({"conanfile.py": conan_hello})
    client.run("create . hello/1.0@")

    conan_consumer = textwrap.dedent("""
    import os

    from conans import ConanFile, tools

    class HelloTestConan(ConanFile):
        settings = "os", "compiler", "build_type", "arch"
        requires = "hello/1.0"
        def build(self):
            info = self.dependencies["hello"].cpp_info
            self.output.warn("**includedirs:{}**".format(info.includedirs))
            self.output.warn("**libdirs:{}**".format(info.libdirs))
            self.output.warn("**builddirs:{}**".format(info.builddirs))
            self.output.warn("**frameworkdirs:{}**".format(info.frameworkdirs))
            self.output.warn("**libs:{}**".format(info.libs))
            self.output.warn("**cxxflags:{}**".format(info.cxxflags))
            self.output.warn("**cflags:{}**".format(info.cflags))
    """)
    # When hello is not editable
    client2 = TestClient(client.cache_folder)
    client2.save({"conanfile.py": conan_consumer})
    client2.run("create . lib/1.0@")
    assert "**includedirs:['package_include']**" in client2.out
    assert "**libdirs:['lib']**" in client2.out
    assert "**builddirs:['']**" in client2.out
    assert "**frameworkdirs:['Frameworks', 'package_frameworks_path']**" in client2.out
    assert "**libs:['lib_when_package', 'lib_when_package2']**" in client2.out
    assert "**cxxflags:['my_cxx_flag2']**" in client2.out
    assert "**cflags:['my_c_flag']**" in client2.out

    # When hello is editable
    client.save({"conanfile.py": conan_hello})
    client.run("editable add . hello/1.0@")

    # Create the consumer again, now it will use the hello editable
    client2.run("create . lib/1.0@")
    out = str(client2.out).replace("\\", "/").replace("//", "/")
    assert "**includedirs:['my_sources/my_include_source', 'my_build/my_include']**" in out
    assert "**libdirs:['my_build/my_libdir']**" in out
    assert "**builddirs:['my_sources/my_builddir_source']**" in out
    assert "**libs:['hello']**" in out
    assert "**cxxflags:['my_cxx_flag']**" in out
    assert "**cflags:['my_c_flag']**" in out
    assert "**frameworkdirs:[]**" in client2.out


def test_cpp_info_components_editable():

    client = TestClient()

    conan_hello = str(GenConanfile())
    conan_hello += """
    def layout(self):
        self.folders.source = "my_sources"
        self.folders.build = "my_build"

        self.cpp.local.components["foo"].includedirs = ["my_sources/my_include_source_foo",
                                                        "my_build/my_include_foo"]
        self.cpp.local.components["foo"].libdirs = ["my_build/my_libdir_foo"]
        self.cpp.local.components["foo"].libs = ["hello_foo"]
        self.cpp.local.components["foo"].cxxflags = ["my_cxx_flag_foo"]
        self.cpp.local.components["foo"].builddirs = ["my_sources/my_builddir_source_foo"]


        self.cpp.local.components["var"].includedirs = ["my_sources/my_include_source_var",
                                                        "my_build/my_include_var"]
        self.cpp.local.components["var"].libdirs = ["my_build/my_libdir_var"]
        self.cpp.local.components["var"].libs = ["hello_var"]
        self.cpp.local.components["var"].cxxflags = ["my_cxx_flag_var"]
        self.cpp.local.components["var"].builddirs = ["my_sources/my_builddir_source_var"]

        self.cpp.package.components["foo"].libs = ["lib_when_package_foo"]
        self.cpp.package.components["var"].libs = ["lib_when_package_var"]

    def package_info(self):
        # when editable: This one will be discarded because declared in build
        self.cpp_info.components["foo"].includedirs = ["package_include_foo"]

        # when editable: This one will be discarded because declared in build
        self.cpp_info.components["foo"].libs.append("lib_when_package2_foo")

        # when editable: This one will be discarded because declared in source
        self.cpp_info.components["foo"].cxxflags.append("my_cxx_flag2_foo")

        # when editable: This one WONT be discarded as has not been declared in the editables layout
        self.cpp_info.components["foo"].cflags.append("my_c_flag_foo")

        # when editable: This one will be discarded because declared in build
        self.cpp_info.components["var"].includedirs = ["package_include_var"]

        # when editable: This one will be discarded because declared in build
        self.cpp_info.components["var"].libs.append("lib_when_package2_var")

        # when editable: This one will be discarded because declared in source
        self.cpp_info.components["var"].cxxflags.append("my_cxx_flag2_var")

        # when editable: This one WONT be discarded as has not been declared in the editables layout
        self.cpp_info.components["var"].cflags.append("my_c_flag_var")
     """

    client.save({"conanfile.py": conan_hello})
    client.run("create . hello/1.0@")

    conan_consumer = textwrap.dedent("""
    import os

    from conans import ConanFile, tools

    class HelloTestConan(ConanFile):
        settings = "os", "compiler", "build_type", "arch"
        requires = "hello/1.0"
        def build(self):
            info = self.dependencies["hello"].cpp_info
            self.output.warn("**FOO includedirs:{}**".format(info.components["foo"].includedirs))
            self.output.warn("**FOO libdirs:{}**".format(info.components["foo"].libdirs))
            self.output.warn("**FOO builddirs:{}**".format(info.components["foo"].builddirs))
            self.output.warn("**FOO libs:{}**".format(info.components["foo"].libs))
            self.output.warn("**FOO cxxflags:{}**".format(info.components["foo"].cxxflags))
            self.output.warn("**FOO cflags:{}**".format(info.components["foo"].cflags))

            self.output.warn("**VAR includedirs:{}**".format(info.components["var"].includedirs))
            self.output.warn("**VAR libdirs:{}**".format(info.components["var"].libdirs))
            self.output.warn("**VAR builddirs:{}**".format(info.components["var"].builddirs))
            self.output.warn("**VAR libs:{}**".format(info.components["var"].libs))
            self.output.warn("**VAR cxxflags:{}**".format(info.components["var"].cxxflags))
            self.output.warn("**VAR cflags:{}**".format(info.components["var"].cflags))
    """)
    # When hello is not editable
    client2 = TestClient(client.cache_folder)
    client2.save({"conanfile.py": conan_consumer})
    client2.run("create . lib/1.0@")
    assert "**FOO includedirs:['package_include_foo']**" in client2.out
    assert "**FOO libdirs:[]**" in client2.out  # The components don't have default dirs
    assert "**FOO builddirs:[]**" in client2.out # The components don't have default dirs
    assert "**FOO libs:['lib_when_package_foo', 'lib_when_package2_foo']**" in client2.out
    assert "**FOO cxxflags:['my_cxx_flag2_foo']**" in client2.out
    assert "**FOO cflags:['my_c_flag_foo']**" in client2.out

    assert "**VAR includedirs:['package_include_var']**" in client2.out
    assert "**VAR libdirs:[]**" in client2.out  # The components don't have default dirs
    assert "**VAR builddirs:[]**" in client2.out  # The components don't have default dirs
    assert "**VAR libs:['lib_when_package_var', 'lib_when_package2_var']**" in client2.out
    assert "**VAR cxxflags:['my_cxx_flag2_var']**" in client2.out
    assert "**VAR cflags:['my_c_flag_var']**" in client2.out

    # When hello is editable
    client.save({"conanfile.py": conan_hello})
    client.run("editable add . hello/1.0@")

    # Create the consumer again, now it will use the hello editable
    client2.run("create . lib/1.0@")
    out = str(client2.out).replace("\\", "/").replace("//", "/")
    assert "**FOO includedirs:['my_sources/my_include_source_foo', " \
           "'my_build/my_include_foo']**" in out
    assert "**FOO libdirs:['my_build/my_libdir_foo']**" in out
    assert "**FOO builddirs:['my_sources/my_builddir_source_foo']**" in out
    assert "**FOO libs:['hello_foo']**" in out
    assert "**FOO cxxflags:['my_cxx_flag_foo']**" in out
    assert "**FOO cflags:['my_c_flag_foo']**" in out

    assert "**VAR includedirs:['my_sources/my_include_source_var', " \
           "'my_build/my_include_var']**" in out
    assert "**VAR libdirs:['my_build/my_libdir_var']**" in out
    assert "**VAR builddirs:['my_sources/my_builddir_source_var']**" in out
    assert "**VAR libs:['hello_var']**" in out
    assert "**VAR cxxflags:['my_cxx_flag_var']**" in out
    assert "**VAR cflags:['my_c_flag_var']**" in out

