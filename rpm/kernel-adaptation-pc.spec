# 
# Do NOT Edit the Auto-generated Part!
# Generated by: spectacle version 0.27
# 

Name:       kernel-adaptation-pc

# >> macros
%define extraver maui
%define kernel_version 3.15.6
%define kernel_version_build %{kernel_version}-%{extraver}
%define kernel_devel_dir %{_prefix}/src/kernels/%{kernel_version_build}
# << macros

Summary:    Kernel Adaptation %{kernel_target_hw}
Version:    3.15.6
Release:    1
Group:      Kernel/Linux Kernel
License:    GPLv2
URL:        http://www.kernel.org
Source0:    kernel-adaptation-pc-%{version}.tar.xz
Source1:    %{name}-x86.config
Source2:    %{name}-x86_64.config
Source100:  kernel-adaptation-pc.yaml
Requires(pre): kmod
Requires(pre): dracut >= 027
BuildRequires:  pkgconfig(ncurses)
BuildRequires:  bc
BuildRequires:  mer-kernel-checks
BuildRequires:  lz4
Provides:   kernel = %{kernel_version}

%description
Kernel for %{kernel_target_hw}.

%package devel
Summary:    Devel files for %{kernel_target_hw} kernel
Group:      Development/System
Requires:   %{name} = %{version}-%{release}
Provides:   kernel-devel = %{kernel_version}

%description devel
Devel for %{kernel_target_hw} kernel

%prep
%setup -q -n %{name}-%{version}

# >> setup
# This should go in the macro section
# Determine the kernel arch and what we're building
# kernel_arch: arm/mips/x86 (for now) .. the ARCH= for the kernel
#
%{lua:
arch = rpm.expand("%{_arch}")
if arch == "arm" or arch == "mips" then
rpm.define("builds_uImage 1")
rpm.define("kernel_arch " .. arch)
else
rpm.define("builds_firmware 1")
rpm.define("builds_vmlinuz 1")
rpm.define("kernel_arch x86")
end

-- This is the common/code name of the hardware adaptation
-- Primarily used in descriptions

name = rpm.expand("%{name}")
pat = "kernel%-adaptation%-(.+)"
start, finish, capture = string.find(name, pat)
if start == nil then
error("Package name "..name.." doesn't match reqired pattern "..pat)
else
rpm.define("kernel_target_hw " ..  capture)
end
}

# Verify the config meets the current Mer requirements
#/usr/bin/mer_verify_config .config

# Copy configuration
if [ "%{_arch}" = "x86_64" ]; then
cp %{SOURCE2} linux/.config
else
cp %{SOURCE1} linux/.config
fi

echo The target hw is %{kernel_target_hw}
echo The desc is %{summary}


# << setup

%build
# >> build pre
cd linux
perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = -%{extraver}/" Makefile
%if 0%{?builds_uImage}
# << build pre



# >> build post
%endif
%if 0%{?builds_vmlinuz}
#make %{?jobs:-j%jobs} %{?_smp_mflags} bzImage
make %{?_smp_mflags} bzImage
%endif
#make %{?jobs:-j%jobs} %{?_smp_mflags} modules
make %{?_smp_mflags} modules
# << build post

%install
rm -rf %{buildroot}
# >> install pre
cd linux
# << install pre

# >> install post

# Modules
make INSTALL_MOD_PATH=%{buildroot} modules_install
mkdir -p %{buildroot}/lib/modules/%{kernel_version_build}/
touch %{buildroot}/lib/modules/%{kernel_version_build}/modules.dep
find %{buildroot}/lib/modules/%{kernel_version_build} -name "*.ko" -type f -exec chmod u+x {} \;

# /boot
mkdir -p %{buildroot}/boot/
make INSTALL_PATH=%{buildroot}/boot/ install

%if 0%{?builds_uImage}
install -m 755 arch/%{kernel_arch}/boot/uImage %{buildroot}/boot/
%endif

%if 0%{?builds_vmlinuz}
install -m 755 arch/%{kernel_arch}/boot/bzImage %{buildroot}/boot/vmlinuz-%{kernel_version_build}
%endif

install -m 755 .config %{buildroot}/boot/config-%{kernel_version_build}
install -m 755 System.map %{buildroot}/boot/
install -m 755 System.map %{buildroot}/boot/System.map-%{kernel_version_build}

# And save the headers/makefiles etc for building modules against
#
# This all looks scary, but the end result is supposed to be:
# * all arch relevant include/ files
# * all Makefile/Kconfig files
# * all script/ files

mkdir -p %{buildroot}/%{kernel_devel_dir}

# dirs for additional modules per module-init-tools, kbuild/modules.txt
# first copy everything
cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` %{buildroot}/%{kernel_devel_dir}
cp Module.symvers %{buildroot}/%{kernel_devel_dir}
cp System.map %{buildroot}/%{kernel_devel_dir}
if [ -s Module.markers ]; then
cp Module.markers %{buildroot}/%{kernel_devel_dir}
fi
# then drop all but the needed Makefiles/Kconfig files
rm -rf %{buildroot}/%{kernel_devel_dir}/Documentation
rm -rf %{buildroot}/%{kernel_devel_dir}/scripts
rm -rf %{buildroot}/%{kernel_devel_dir}/include

# Copy all scripts
cp .config %{buildroot}/%{kernel_devel_dir}
cp -a scripts %{buildroot}/%{kernel_devel_dir}
if [ -d arch/%{karch}/scripts ]; then
cp -a arch/%{kernel_arch}/scripts %{buildroot}/%{kernel_devel_dir}/arch/%{kernel_arch}
fi
# FIXME - what's this trying to do ... if *lds expands to multiple files the -f test will fail.
if [ -f arch/%{karch}/*lds ]; then
cp -a arch/%{kernel_arch}/*lds %{buildroot}/%{kernel_devel_dir}/arch/%{kernel_arch}/
fi
# Clean any .o files from the 'scripts'
find %{buildroot}/%{kernel_devel_dir}/scripts/ -name \*.o -print0 | xargs -0 rm -f

# arch-specific include files
cp -a --parents arch/%{kernel_arch}/include %{buildroot}/%{kernel_devel_dir}

# arm has include files under plat- and mach- areas (x86/mips don't)
%if "%{?karch}" == "arm"
cp -a --parents arch/%{kernel_arch}/mach-*/include %{buildroot}/%{kernel_devel_dir}
cp -a --parents arch/%{kernel_arch}/plat-*/include %{buildroot}/%{kernel_devel_dir}
%endif

# normal include files
mkdir -p %{buildroot}/%{kernel_devel_dir}/include

# copy only include/* directories
cp -a $(find include -mindepth 1 -maxdepth 1 -type d) %{buildroot}/%{kernel_devel_dir}/include

# Make sure the Makefile and version.h have a matching timestamp so that
# external modules can be built. Also .conf
touch -r %{buildroot}/%{kernel_devel_dir}/Makefile %{buildroot}/%{kernel_devel_dir}/include/linux/version.h
touch -r %{buildroot}/%{kernel_devel_dir}/.config %{buildroot}/%{kernel_devel_dir}/include/linux/autoconf.h

# Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
cp %{buildroot}/%{kernel_devel_dir}/.config %{buildroot}/%{kernel_devel_dir}/include/config/auto.conf

# Remove vmlinuz
rm -f %{buildroot}/boot/vmlinuz

# << install post

%post
# >> post
depmod -a %{kernel_version_build}
dracut -q -f -N -a 'drm systemd-bootchart systemd' --kver %{kernel_version_build} || exit $?
# << post

%files
%defattr(-,root,root,-)
# >> files
/lib/modules/%{kernel_version_build}/*
/boot/System.map-%{kernel_version_build}
#/boot/System.map-%{kernel_version}
/boot/config-%{kernel_version_build}
# do we need this? should it be versioned only for x86
/boot/System.map
%if 0%{?builds_vmlinuz}
/boot/vmlinuz-%{kernel_version_build}
#/boot/vmlinuz-%{kernel_version}
#/boot/vmlinuz
%endif
%if 0%{?builds_uImage}
/boot/uImage
%endif
%if 0%{?builds_firmware}
/lib/firmware/*
%endif
# << files

%files devel
%defattr(-,root,root,-)
# >> files devel
/%{_prefix}/src/kernels/%{kernel_version_build}/*
/%{_prefix}/src/kernels/%{kernel_version_build}/.config
# << files devel
