import os
from conans import ConanFile, CMake, tools
from conans.util import files


class LibRealsenseConan(ConanFile):
    name = "librealsense"
    license = "https://raw.githubusercontent.com/IntelRealSense/librealsense/master/LICENSE"
    description = "Intel RealSense SDK https://realsense.intel.com"
    url = ""
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    options = {
        "shared": [True, False],
        "with_examples": [True, False]
    }

    default_options = {
        "shared": True,
        "with_examples": False
    }

    short_paths = True
    _cmake = None
    

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        self.requires("glfw/3.3.2@zyq/stable")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "{}-{}".format(self.name, self.version)
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["BUILD_EXAMPLES"] = self.options.with_examples

        # if self.settings.os == "Linux":
            # for now disable graphical examples .. problem with glfw linking / x11
            # self._cmake.definitions["BUILD_GRAPHICAL_EXAMPLES"] = "OFF"
        # else:
        self._cmake.definitions["BUILD_GRAPHICAL_EXAMPLES"] = self.options.with_examples

        # don't build additional examples
        self._cmake.definitions["BUILD_PCL_EXAMPLES"] = False
        self._cmake.definitions["BUILD_NODEJS_BINDINGS"] = False
        self._cmake.definitions["BUILD_PYTHON_BINDINGS"] = False
        self._cmake.definitions["BUILD_UNIT_TESTS"] = False

        # hints to find GLFW
        # self._cmake.definitions["CMAKE_INCLUDE_PATH"] = ":".join(self.deps_cpp_info["glfw"].include_paths)
        # self._cmake.definitions["CMAKE_LIBRARY_PATH"] = ":".join(self.deps_cpp_info["glfw"].lib_paths)


        # what is this ??
        self._cmake.definitions["ENABLE_ZERO_COPY"] = False
        self._cmake.definitions["BUILD_RS400_EXTRAS"] = True

        if self.options.shared:
            self._cmake.definitions["BUILD_SHARED_LIBS"] = True
            self._cmake.definitions["BUILD_WITH_STATIC_CRT"] = False
            if tools.os_info.is_macos:
                self._cmake.definitions["CMAKE_MACOSX_RPATH"] = True
        else:
            self._cmake.definitions["BUILD_SHARED_LIBS"] = False

        self._cmake.configure(build_folder=self._build_subfolder, source_folder=self._source_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        libs = tools.collect_libs(self)
        self.cpp_info.libs = [l for l in libs if "realsense-file" not in l]
        self.user_info.realsense_file_library_name = [l for l in libs if "realsense-file" in l][0]
        # ??????
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
