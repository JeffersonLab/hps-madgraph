from hpsmc.generators import MG4, StdHepConverter
from hpsmc.base import Job
from hpsmc.run_params import RunParameters
from hpsmc.tools import Unzip, StdHepTool

ap = MG4(description="Generate A-prime events with APMASS param",
         name="ap",
         run_card="run_card_1pt05.dat",
         params={"APMASS": 40.0},
         outputs=["ap"],
         nevents=1000)

unzip = Unzip(inputs=["ap_events.lhe.gz"])

"""
Executes the equivalent of this command:

stdhep_lhe_tridents_displacetime ap_events.lhe ap.stdhep -s1 -l1

This should displace the AP by ~1 mm by setting the proper decay time.
"""
rand_seed = 1
z = 1.0
displ = StdHepTool(name="lhe_tridents_displacetime",
                   inputs=["ap_events.lhe"],
                   outputs=["ap.stdhep"],
                   args=["-s", str(rand_seed), "-l", str(z)])

dump = StdHepTool(name="print_stdhep",
                   inputs=["ap.stdhep"])
          
job = Job(name="AP test",
    components=[ap, unzip, displ, dump])

job.setup()
job.run()
job.cleanup()
