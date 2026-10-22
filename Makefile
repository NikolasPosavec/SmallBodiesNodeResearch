# SIRIS4-FRAMEWORK Makefile

# Compiler
COMP ?= gfortran
CPPCOMP ?= g++

# GNU Compiler suite options
## Fortran
### Required options for gfortran
FOPT = -ffree-form -std=f2008 -fimplicit-none
### Optional choices
#### For developing
#FOPT += -fcheck=bounds,pointer -Wall -Wno-maybe-uninitialized
#### Minor optimization
#FOPT += -O1
#### Major optimization
FOPT += -Ofast -mtune=native
#### For debugging
#FOPT += -g -fbacktrace -ffpe-trap=invalid,zero,overflow,underflow
## C++
### Required options for C++
COPT = -std=c++17 -Wno-narrowing
### Where are include's
#COPT += -I/mingw64/include
COPT += -I/opt/homebrew/include
### Where are gfortran/quadmath runtime libraries (Homebrew gcc)
LDOPT = -L/opt/homebrew/lib -L/opt/homebrew/lib/gcc/current
#### For developing
#COPT += -g
#### Minor optimization
#COPT += -O1
#### Major optimization
COPT += -Ofast -mtune=native -frounding-math

###############################################################################

MKDIR = mkdir -p
DIRECTORIES = lib mod
LIBFILENAMES = sirisconstants sirisutils sirismath sirismaterial sirisnumint sirisgeometry sirismesh sirisgaussiansphere sirisray sirisradtrans
MPFFILES = mathroutines splinetools sirisinterface
MPCFILES =  detector geometry inputreader materials meshreader mray rng offreader outputwriter physicsengine sray tracer smaterial

###############################################################################

all : directories GS singleparticle singletwolayer multiparticle
.PHONY : all clean directories

singletwolayer : directories siris4lib single-two-layer-particle/single-two-layer-main.f
	$(COMP) $(FOPT) -o single-two-layer-particle/siris2l -J mod -L lib single-two-layer-particle/single-two-layer-main.f -lsiris4 

singleparticle : directories siris4lib single-particle/single-particle-main.f
	$(COMP) $(FOPT) -o single-particle/siris1p -J mod -L lib single-particle/single-particle-main.f -lsiris4 

GS : directories siris4lib GS/GS-main.f
	$(COMP) $(FOPT) -o GS/GS -J mod -L lib GS/GS-main.f -lsiris4

multiparticle : directories siris4lib $(addprefix multi-particle/,$(addsuffix .o,$(MPCFILES))) $(addprefix multi-particle/,$(addsuffix .o,$(MPFFILES))) multi-particle/main.cpp
	$(CPPCOMP) $(COPT) -o multi-particle/sirismp $(addprefix multi-particle/,$(addsuffix .o,$(MPCFILES))) $(addprefix multi-particle/,$(addsuffix .o,$(MPFFILES)))  multi-particle/main.cpp -L lib $(LDOPT) -lsiris4 -lgfortran -lquadmath $(shell $(COMP) -print-libgcc-file-name)

siris4lib : directories lib/libsiris4.a
	
lib/libsiris4.a : $(addprefix lib/,$(addsuffix .o,$(LIBFILENAMES))) 
	ar crv -s lib/libsiris4.a $^

lib/%.o : src/%.f
	$(COMP) $(FOPT) -c -J mod -o lib/$*.o src/$*.f

multi-particle/%.o : multi-particle/%.f90
	$(COMP) $(FOPT) -c -J mod -o multi-particle/$*.o multi-particle/$*.f90

multi-particle/%.o : multi-particle/%.cpp
	$(CPPCOMP) $(COPT) -c -o multi-particle/$*.o multi-particle/$*.cpp

clean : 
	rm -rf lib/*.o
	rm -rf lib/*.a
	rm -rf mod/*.mod
	rm -rf GS/GS.exe
	rm -rf GS/GS
	rm -rf single-particle/siris1p.exe
	rm -rf single-particle/siris1p
	rm -rf single-two-layer-particle/siris2l.exe
	rm -rf single-two-layer-particle/siris2l
	rm -rf multi-particle/*.o
	rm -rf multi-particle/sirismp.exe
	rm -rf multi-particle/sirismp

directories: ${DIRECTORIES}

${DIRECTORIES}:
	${MKDIR} ${DIRECTORIES}
