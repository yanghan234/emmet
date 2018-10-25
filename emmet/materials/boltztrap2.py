import logging
from datetime import datetime

from monty.json import jsanitize
from monty.tempfile import ScratchDir
from pymatgen.core.structure import Structure
from pymatgen.electronic_structure.boltztrap2 import *

from maggma.builder import Builder

__author__ = "Francesco Ricci <francesco.ricci@uclouvain.be>"

class Boltztrap2DosBuilder(Builder):
    def __init__(self, materials, boltztrap, bandstructure_fs="bandstructure_fs", btz_cdos_fs=None, query={}, **kwargs):
        """
        Calculates Density of States (DOS) using BoltzTrap
        Saves the dos object

        Args:
            materials (Store): Store of materials documents
            boltztrap (Store): Store of boltztrap
            bandstructure_fs (str): Name of the GridFS where bandstructures are stored
            query (dict): dictionary to limit materials to be analyzed

        """

        self.materials = materials
        self.boltztrap = boltztrap
        self.bandstructure_fs = bandstructure_fs
        self.btz_cdos_fs = btz_cdos_fs
        self.query = query

        super().__init__(sources=[materials],
                         targets=[boltztrap],
                         **kwargs)

    def get_items(self):
        """
        Gets all materials that need a new DOS

        Returns:
            generator of materials to calculate DOS
        """

        self.logger.info("BoltzTrap Dos Builder Started")

        # All relevant materials that have been updated since boltztrap was last run
        # and a uniform bandstructure exists
        q = dict(self.query)
        q.update(self.materials.lu_filter(self.boltztrap))
        q["bandstructure.uniform_oid"] = {"$exists": 1}
        #q["output.bandgap"] = {"$gt": 0.0}
        mats = set(self.materials.distinct(self.materials.key, criteria=q))

        # initialize the gridfs
        bfs = gridfs.GridFS(self.materials.database, self.bandstructure_fs)

        self.logger.info(
            "Found {} new materials for calculating boltztrap dos".format(len(mats)))
        for m in mats:
            mat = self.materials.query(
                [self.materials.key, "structure", "input.parameters.NELECT", "bandstructure"], criteria={self.materials.key: m})

            # If a bandstructure oid exists
            if "uniform_bs_oid" in mat.get("bandstructure", {}):
                bs_json = bfs.get(mat["bandstructure"][
                                  "uniform_bs_oid"]).read()

                if "zlib" in mat["bandstructure"].get("uniform_bs_compression", ""):
                    bs_json = zlib.decompress(bs_json)

                bs_dict = json.loads(bs_json.decode())
                mat["bandstructure"]["uniform_bs"] = bs_dict

            yield mat

    def process_item(self, item):
        """
        Calculates dos running Boltztrap in DOS run mode

        Args:
            item (dict): a dict with a material_id, bs and a structure

        Returns:
            cdos: a complete dos object
        """
        self.logger.debug(
            "Calculating Boltztrap for {}".format(item[self.materials.key]))

        nelect = item["input"]["parameters"]["NELECT"]

        bs_dict = item["uniform_bandstructure"]["bs"]
        bs_dict['structure'] = item['structure']
        bs = BandStructure.from_dict(bs_dict)
        
        #projection are not available in the bs obj taken from the DB
        #either the DB has to be updated with projections or they need to be
        #loaded from the raw data
        projections = True if bs.proj else False
        
        with ScratchDir("."):
            if bs.is_spin_polarized:
                data_up = BandstructureLoader(bs,st,spin=1)
                data_dn = BandstructureLoader(bs,st,spin=-1)

                min_bnd = min(data_up.ebands.min(),data_dn.ebands.min())
                max_bnd = max(data_up.ebands.max(),data_dn.ebands.max())
                data_up.set_upper_lower_bands(min_bnd,max_bnd)
                data_dn.set_upper_lower_bands(min_bnd,max_bnd)
                bztI_up = BztInterpolator(data_up,energy_range=np.inf,curvature=False)
                bztI_dn = BztInterpolator(data_dn,energy_range=np.inf,curvature=False)
                dos_up = bztI_up.get_dos(partial_dos=projections)
                dos_dn = bztI_dn.get_dos(partial_dos=projections)
                cdos = merge_up_down_doses(dos_up,dos_dn)
                
            else:
                data = BandstructureLoader(bs,st)
                bztI = BztInterpolator(data,energy_range=np.inf,curvature=False)
                cdos = bztI.get_dos(partial_dos=projections)
                
        return {'cdos':cdos.as_dict()}

    def update_targets(self, items):
        """
        Inserts the new task_types into the task_types collection

        Args:
            items ([[dict]]): a list of list of thermo dictionaries to update
        """
        items = list(filter(None, items))

        btz_cdos_fs = gridfs.GridFS(self.materials.database,
                               self.btz_cdos_fs) if self.btz_cdos_fs else None

        if len(items) > 0:
            self.logger.info("Updating {} boltztrap dos".format(len(items)))

            for doc in items:
                if self.bta_fs:
                    btz_dos_doc = dict(doc["cdos"])
                    btz_dos_json = json.dumps(jsanitize(btz_dos_doc))
                    btz_dos_gz = zlib.compress(btz_dos_json)
                    btz_dos_oid = btz_dos_fs.put(btz_dos_gz)
                    doc['btz_dos_oid'] = btz_dos_oid
                    doc['btz_dos_compression'] = "zlib"

                del doc["cdos"]

            self.boltztrap.update(items)

        else:
            self.logger.info("No items to update")


