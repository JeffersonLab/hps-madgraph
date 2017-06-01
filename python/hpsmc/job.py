import os, sys, shutil, argparse, getpass, json, logging
from component import Component

logger = logging.getLogger("job")

class Job:

    def __init__(self, **kwargs):
        
        if "name" in kwargs:
            self.name = kwargs["name"] 
        else:
            self.name = "HPS MC Job"
            
        self.delete_rundir = False
        if "rundir" in kwargs:
            self.rundir = kwargs["rundir"]
        else:
            if "LSB_JOBID" in os.environ:
                self.rundir = os.path.join("/scratch", getpass.getuser(), os.environ["LSB_JOBID"])
                self.delete_rundir = True
            else:
                self.rundir = os.getcwd()
                
        if "components" in kwargs:
            self.components = kwargs["components"]
        else:
            self.components = []            
            
        if "job_num_pad" in kwargs:
            self.job_num_pad = kwargs["job_num_pad"]
        else:
            self.job_num_pad = 4
                        
        if "delete_existing" in kwargs:
            self.delete_existing = kwargs["delete_existing"]
        else:
            self.delete_existing = False
            
        if "set_component_seeds" in kwargs:
            self.set_component_seeds = kwargs["set_component_seeds"]
        else:
            self.set_component_seeds = True
            
        self.params = None
        
        self.log_out = sys.stdout
        self.log_err = sys.stderr
            
    def parse_args(self):
        
        parser = argparse.ArgumentParser(description=self.name)
        parser.add_argument("-o", "--out", nargs=1, help="Log file for stdout from components")
        parser.add_argument("-e", "--err", nargs=1, help="Log file for stderr from components")
        parser.add_argument("-L", "--level", nargs=1, help="Global log level")
        parser.add_argument("params", nargs=1, help="Job params in JSON format")
        cl = parser.parse_args()
        
        if cl.level:
            level = logging.getLevelName(cl.level[0])
            logging.basicConfig(level=level)
        
        if cl.out:
            logger.info("stdout from execution will be redirected to '%s'" % cl.out[0])
            self.log_out = open(cl.out[0], "w")
            
        if cl.err:
            logger.info("stderr from execution will be redirected to '%s'" % cl.err[0])
            self.log_err = open(cl.err[0], "w")
        
        if cl.params:
            logger.info("Loading job params from '%s'" % cl.params[0])
            self.params = JobParameters(cl.params[0])
            logger.info(json.dumps(self.params.json_dict, indent=4, sort_keys=False))
        else:
            raise Exception("Missing required JSON file with job params.")
            
        if hasattr(self.params, "input_files"):
            self.input_files = self.params.input_files
        else:
            self.input_files = {}
            
        if hasattr(self.params, "output_files"):
            self.output_files = self.params.output_files
        else:
            self.output_files = {}
            
        if hasattr(self.params, "seed"):
            self.seed = self.params.seed
        else:
            logger.info("random seed is set to default value '%d'" % (self.seed))
            self.seed = 1
            
        if hasattr(self.params, "output_dir"):
            self.output_dir = self.params.output_dir
            if not os.path.isabs(self.output_dir):
                self.output_dir= os.path.abspath(self.output_dir)
                logger.info("changed output dir to abs path '%s'" % self.output_dir)
        else:
            self.output_dir = os.getcwd()

        if hasattr(self.params, "job_num"):
            self.job_num = self.params.job_num
        else:
            self.job_num = 1        
            
    def run(self): 
        if not len(self.components):
            raise Exception("Job has no components.")
        if not self.params:
            raise Exception("Job params were never parsed.")
        self.copy_input_files()
        self.setup()
        self.execute()
        self.copy_output_files()
        self.cleanup()
                      
    def execute(self):
        logger.info("running '%s'" % self.name)
        if not len(self.components):
            raise Exception("Job has no components to execute.")
        for i in range(0, len(self.components)):
            c = self.components[i]
            logger.info("executing '%s' with inputs %s and outputs %s" % (c.name, str(c.inputs), str(c.outputs)))
            c.execute(self.log_out, self.log_err)

    def setup(self):
        if not os.path.exists(self.rundir):
            os.makedirs(self.rundir)
        os.chdir(self.rundir)
        for c in self.components:
            logger.info("setting up '%s'" % (c.name))
            c.rundir = self.rundir
            if self.set_component_seeds:
                logger.info("setting seed on '%s' to '%d'" % (c.name, self.seed))
                c.seed = self.seed
            c.setup()
            if not c.cmd_exists():
                raise Exception("Command '%s' does not exist for '%s'." % (c.command, c.name))

    def cleanup(self):
        for c in self.components:
            logger.info("running cleanup for '%s'" % str(c.name))
            c.cleanup()
        if self.delete_rundir:
            logger.info("Job: deleting execute dir '%s'" % self.rundir)
            shutil.rmtree(self.rundir)
        if self.log_out != sys.stdout:
            self.log_out.close()
        if self.log_err != sys.stderr:
            self.log_err.close()
    
    def copy_output_files(self):
                
        if not os.path.exists(self.output_dir):
            logger.info("creating output dir '%s'" % self.output_dir)
            os.makedirs(self.output_dir, 0755)
               
        for src,dest in self.output_files.iteritems():
            src_file = os.path.join(self.rundir, src)
            dest_file = os.path.join(self.output_dir, dest)
            if os.path.isfile(dest_file):
                if self.delete_existing:
                    logger.info("deleting existing file at '%s'" % dest_file)
                    os.remove(dest_file)
                else:
                    raise Exception("Output file '%s' already exists." % dest_file)
            logger.info("copying '%s' to '%s'" % (src_file, dest_file))
            shutil.copyfile(src_file, dest_file)
            
    def copy_input_files(self):
        for dest,src in self.input_files.iteritems():
            if not os.path.isabs(src):
                raise Exception("The input source file '%s' is not an absolute path." % src)
            if os.path.dirname(dest):
                raise Exception("The input file destination '%s' is not valid." % dest)
            logger.info("copying input '%s' to '%s'" % (src, os.path.join(self.rundir, dest)))
            shutil.copyfile(src, os.path.join(self.rundir, dest))
            
class JobParameters:
    
    def __init__(self, filename = None):
        if filename:
            self.load(filename)
    
    def load(self, filename):
        rawdata = open(filename, 'r').read()
        self.json_dict = json.loads(rawdata)        

    def __getattr__(self, attr):
        if attr in self.json_dict:
            return self.json_dict[attr]
        else:
            raise AttributeError("%r has no attribute '%s'" %
                                 (self.__class__, attr))
    
    def __str__(self):
        return str(self.json_dict)
     