CXXFLAGS=-shared -fPIC --no-gnu-unique -Wall -g -DWLR_USE_UNSTABLE -std=c++2b -O2
INCLUDES = `pkg-config --cflags pixman-1 libdrm hyprland pangocairo libinput libudev wayland-server xkbcommon lua`
SRC = $(wildcard src/*.cpp)
TARGET = Hyprspace.so
PREFIX ?= /usr/local
LIBDIR ?= $(PREFIX)/lib

all:
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(SRC) -o $(TARGET)

install:
	install -D -m 0755 $(TARGET) $(DESTDIR)$(LIBDIR)/$(TARGET)

clean:
	rm ./$(TARGET)

withhyprpmheaders: export PKG_CONFIG_PATH = $(XDG_DATA_HOME)/hyprpm/headersRoot/share/pkgconfig
withhyprpmheaders: all

.PHONY: test
test:
	mkdir -p build
	$(CXX) -std=c++23 -Wall -Wextra -pedantic tests/preview_navigation.cpp -o build/preview-navigation-test
	./build/preview-navigation-test
	$(CXX) -std=c++23 -Wall -Wextra -pedantic tests/overview_geometry.cpp -o build/overview-geometry-test
	./build/overview-geometry-test
