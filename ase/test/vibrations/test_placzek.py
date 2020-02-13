"""
Test Placzek type resonant Raman implementations
"""
import pytest

from ase.vibrations.placzek import Placzek, Profeta
from ase.calculators.h2morse import H2Morse, H2MorseExcitedStates


def test_placzek_run():
    atoms = H2Morse()
    name = 'placzek'
    pz = Placzek(atoms, H2MorseExcitedStates,
                 gsname=name, exname=name, txt='-')
    pz.run()


def test_profeta_run():
    atoms = H2Morse()
    name = 'profeta'
    pr = Profeta(atoms, H2MorseExcitedStates,
                 gsname=name, exname=name, txt='-')
    pr.run()


def test_overlap():
    """Test equality with and without overlap"""
    atoms = H2Morse()
    name = 'profeta'
    name = 'rrmorse'
    nstates = 3
    po = Profeta(atoms, H2MorseExcitedStates,
                 exkwargs={'nstates': nstates}, approximation='Placzek',
                 overlap=lambda x, y: x.overlap(y),
                 gsname=name, exname=name, txt='-')
    po.run()

    om = 1
    gam = 0.1
    poi = po.absolute_intensity(omega=om, gamma=gam)[-1]

    pr = Profeta(atoms, H2MorseExcitedStates,
                 exkwargs={'nstates': nstates}, approximation='Placzek',
                 gsname=name, exname=name,
                 txt=None)
    pri = pr.absolute_intensity(omega=om, gamma=gam)[-1]

    print('overlap', pri, poi, poi / pri)
    assert pri == pytest.approx(poi, 1e-4)


def test_compare_placzek_implementation_intensities():
    """Intensities of different Placzek implementations
    should be similar"""
    atoms = H2Morse()
    name = 'placzek'
    pz = Placzek(atoms, H2MorseExcitedStates,
                 gsname=name, exname=name, txt=None)
    pz.run()
    om = 1
    gam = 0.1
    pzi = pz.absolute_intensity(omega=om, gamma=gam)[-1]

    # Profeta using frozenset
    pr = Profeta(atoms, H2MorseExcitedStates, approximation='Placzek',
                 gsname=name, exname=name, txt=None)
    pri = pr.absolute_intensity(omega=om, gamma=gam)[-1]
    assert pzi == pytest.approx(pri, 1e-3)
    
    # Profeta using overlap
    name = 'profeta'
    pr = Profeta(atoms, H2MorseExcitedStates, approximation='Placzek',
                 gsname=name, exname=name,
                 overlap=lambda x, y: x.overlap(y),
                 txt=None)
    pr.run()
    pro = pr.absolute_intensity(omega=om, gamma=gam)[-1]
    assert pro == pytest.approx(pri, 1e-3)


def main():
    test_overlap()

if __name__ == '__main__':
    main()
