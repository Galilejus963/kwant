"""An example of how to directly implement a system without using
kwant.Builder.
"""

from __future__ import division
import numpy as np
import kwant
from kwant.physics.selfenergy import square_self_energy

__all__ = ['System' ]

class Lead(object):
    def __init__(self, width, t, potential):
        self.width = width
        self.t = t
        self.potential = potential

    def self_energy(self, fermi_energy):
        return square_self_energy(self.width, self.t, self.potential,
                                  fermi_energy)

class System(kwant.system.FiniteSystem):
    # Override abstract attributes.
    graph = None
    lead_neighbor_seqs = None

    def __init__(self, shape, hopping,
                 potential=0, lead_potentials=(0, 0),
                 return_scalars_as_matrix=True):
        """`potential` can be a container (indexed by a pair of integers) or a
        function (taking a pair of integers as its parameter) or a number.
        Checked in this order.
        """
        assert len(shape) == 2
        for s in shape:
            assert int(s) == s
            assert s >= 1

        self.as_matrix = return_scalars_as_matrix
        self.shape = shape
        if hasattr(potential, '__getitem__'):
            self.pot = potential.__getitem__
        elif hasattr(potential, '__call__'):
            self.pot = potential
        else:
            self.pot = lambda xy: potential
        self.t = hopping

        # Build rectangular mesh graph
        g = kwant.graph.Graph()
        increment = [1, shape[0]]
        for along, across in [(0, 1), (1, 0)]:
            # Add edges in direction "along".
            if shape[along] < 2: continue
            edges = np.empty((2 * shape[across], 2), dtype=int)
            edges[:shape[across], 0] = np.arange(
                0, shape[across] * increment[across], increment[across])
            edges[:shape[across], 1] = edges[:shape[across], 0]
            edges[:shape[across], 1] += increment[along]
            edges[shape[across]:, (0, 1)] = edges[:shape[across], (1, 0)]
            g.add_edges(edges)
            for i in xrange(shape[along] - 2):
                edges += increment[along]
                g.add_edges(edges)
        self.graph = g.compressed()

        self.lead_neighbor_seqs = []
        for x in [0, shape[0] - 1]:
            # We have to use list here, as numpy.array does not understand
            # generators.
            lead_neighbors = list(self.nodeid_from_pos((x, y))
                              for y in xrange(shape[1]))
            self.lead_neighbor_seqs.append(np.array(lead_neighbors))

        self.leads = [Lead(shape[1], hopping, lead_potentials[i])
                      for i in range(2)]

    def num_orbitals(self, site):
        """Return the number of orbitals of a site."""
        return 1

    def hamiltonian(self, i, j):
        """Return an submatrix of the tight-binding Hamiltonian."""
        if i == j:
            # An on-site Hamiltonian has been requested.
            result = 4 * self.t + self.pot(self.pos_from_nodeid(i))
        else:
            # A hopping element has been requested.
            result = -self.t
        if self.as_matrix:
            result = np.array([[result]], dtype=complex)
        return result

    def nodeid_from_pos(self, pos):
        for i in xrange(2):
            assert int(pos[i]) == pos[i]
            assert pos[i] >= 0 and pos[i] < self.shape[i]
        return pos[0] + pos[1] * self.shape[0]

    def pos_from_nodeid(self, nodeid):
        result = (nodeid % self.shape[0]), (nodeid // self.shape[0])
        assert result[1] >= 0 and result[1] < self.shape[1]
        return result


def main():
    sys = System((10, 5), 1)
    energies = [0.04 * i for i in xrange(100)]
    data = [kwant.solve(sys, energy).transmission(1, 0)
            for energy in energies]

    import pylab
    pylab.plot(energies, data)
    pylab.xlabel("energy [in units of t]")
    pylab.ylabel("conductance [in units of e^2/h]")
    pylab.show()


if __name__ == '__main__':
    main()