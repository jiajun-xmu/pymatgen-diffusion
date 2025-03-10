# coding: utf-8
# Copyright (c) Materials Virtual Lab.
# Distributed under the terms of the BSD License.

from pymatgen import Structure, Lattice

__author__ = "Iek-Heng Chu"
__date__ = "01/16"

import unittest
import os
import json

import numpy as np
import matplotlib

matplotlib.use("pdf")

from pymatgen_diffusion.aimd.van_hove import VanHoveAnalysis, \
    RadialDistributionFunction, EvolutionAnalyzer
from pymatgen.analysis.diffusion_analyzer import DiffusionAnalyzer

tests_dir = os.path.dirname(os.path.abspath(__file__))


class VanHoveTest(unittest.TestCase):
    def test_van_hove(self):
        data_file = os.path.join(tests_dir, "cNa3PS4_pda.json")
        with open(data_file, "r") as j:
            data = json.load(j)
        obj = DiffusionAnalyzer.from_dict(data)

        vh = VanHoveAnalysis(diffusion_analyzer=obj, avg_nsteps=5, ngrid=101,
                             rmax=10.0,
                             step_skip=5, sigma=0.1, species=["Li", "Na"])

        check = np.shape(vh.gsrt) == (20, 101) and np.shape(vh.gdrt) == (
            20, 101)
        self.assertTrue(check)
        self.assertAlmostEqual(vh.gsrt[0, 0], 3.98942280401, 10)
        self.assertAlmostEqual(vh.gdrt[10, 0], 9.68574868168, 10)


class RDFTest(unittest.TestCase):
    def test_rdf(self):
        data_file = os.path.join(tests_dir, "cNa3PS4_pda.json")
        with open(data_file, "r") as j:
            data = json.load(j)
        obj = DiffusionAnalyzer.from_dict(data)

        structure_list = []
        for i, s in enumerate(obj.get_drift_corrected_structures()):
            structure_list.append(s)
            if i == 9: break
        species = ["Na", "P", "S"]

        # Test from_species
        obj = RadialDistributionFunction.from_species(
            structures=structure_list, ngrid=101, rmax=10.0, cell_range=1,
            sigma=0.1, species=species, reference_species=species)

        check = np.shape(obj.rdf)[0] == 101 and np.argmax(obj.rdf) == 34
        self.assertTrue(check)
        self.assertAlmostEqual(obj.rdf.max(), 1.634448, 4)

        # Test init
        s = structure_list[0]
        indices = [i for (i, site) in enumerate(s) if
                   site.species_string in species]
        obj = RadialDistributionFunction(
            structures=structure_list, ngrid=101, rmax=10.0, cell_range=1,
            sigma=0.1, indices=indices, reference_indices=indices)

        check = np.shape(obj.rdf)[0] == 101 and np.argmax(obj.rdf) == 34
        self.assertTrue(check)
        self.assertAlmostEqual(obj.rdf.max(), 1.634448, 4)

    def test_rdf_coordination_number(self):
        # create a simple cubic lattice
        coords = np.array([[0.5, 0.5, 0.5]])
        atom_list = ['S']
        lattice = Lattice.from_parameters(a=1.0, b=1.0, c=1.0, alpha=90,
                                          beta=90, gamma=90)
        structure = Structure(lattice, atom_list, coords)
        rdf = RadialDistributionFunction.from_species(
            structures=[structure], species=['S'],
            rmax=5.0, sigma=0.1, ngrid=500)
        self.assertEqual(rdf.coordination_number[100], 6.0)

    def test_rdf_two_species_coordination_number(self):
        # create a structure with interpenetrating simple cubic lattice
        coords = np.array([[0.0, 0.0, 0.0],
                           [0.5, 0.5, 0.5]])
        atom_list = ['S', 'Zn']
        lattice = Lattice.from_parameters(a=1.0, b=1.0, c=1.0, alpha=90,
                                          beta=90, gamma=90)
        structure = Structure(lattice, atom_list, coords)
        rdf = RadialDistributionFunction.from_species(
            structures=[structure], species=['S'], reference_species=['Zn'],
            rmax=5.0, sigma=0.1, ngrid=500)
        self.assertEqual(rdf.coordination_number[100], 8.0)

    def setUp(self):
        coords = np.array([[0.5, 0.5, 0.5]])
        atom_list = ['S']
        lattice = Lattice.from_parameters(a=1.0, b=1.0, c=1.0, alpha=90,
                                          beta=90, gamma=90)
        self.structure = Structure(lattice, atom_list, coords)

    def test_raises_valueerror_if_ngrid_is_less_than_2(self):
        with self.assertRaises(ValueError):
            rdf = RadialDistributionFunction.from_species(
                structures=[self.structure], ngrid=1)

    def test_raises_ValueError_if_sigma_is_not_positive(self):
        with self.assertRaises(ValueError):
            rdf = RadialDistributionFunction.from_species(
                structures=[self.structure], sigma=0)

    def test_raises_ValueError_if_species_not_in_structure(self):
        with self.assertRaises(ValueError):
            rdf = RadialDistributionFunction.from_species(
                structures=[self.structure], species=['Cl'])

    def test_raises_ValueError_if_reference_species_not_in_structure(self):
        with self.assertRaises(ValueError):
            rdf = RadialDistributionFunction.from_species(
                structures=[self.structure], species=['S'],
                reference_species=['Cl'])


class EvolutionAnalyzerTest(unittest.TestCase):
    def test_get_df(self):
        data_file = os.path.join(tests_dir, "cNa3PS4_pda.json")
        with open(data_file, "r") as j:
            data = json.load(j)
        obj = DiffusionAnalyzer.from_dict(data)

        structure_list = []
        for i, s in enumerate(obj.get_drift_corrected_structures()):
            structure_list.append(s)
            if i == 9: break
        eva = EvolutionAnalyzer(structure_list, rmax=10, step=1, time_step=2)
        rdf = eva.get_df(EvolutionAnalyzer.rdf, pair=("Na", "Na"))
        atom_dist = eva.get_df(EvolutionAnalyzer.atom_dist, specie="Na",
                               direction="c")
        check = np.shape(rdf) == (10, 101) and np.shape(atom_dist) == (
            10, 101) and eva.pairs[0] == ("Na", "Na")
        self.assertTrue(check)
        self.assertAlmostEqual(max(np.array(rdf)[0]), 1.772465, 4)


if __name__ == "__main__":
    unittest.main()
