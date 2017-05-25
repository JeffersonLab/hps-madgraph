import os, subprocess, sys, shutil, argparse, getpass, json

class Component:

    def __init__(self, **kwargs):
        if "name" in kwargs:
            self.name = kwargs["name"]
        elif self.name is None:
            raise Exception("The name of a Component is required.")
        if "args" in kwargs:
            if not isinstance(kwargs["args"], list):
                raise Exception("The args are not a list.")
            self.args = kwargs["args"]
        else:
            self.args = []
        if "outputs" in kwargs:
            if not isinstance(kwargs["outputs"], list):
                raise Exception("The outputs arg is not a list.")
            self.outputs = kwargs["outputs"]
        else:
            self.outputs = []
        if "inputs" in kwargs:
            if not isinstance(kwargs["inputs"], list):
                raise Exception("The inputs arg is not a list.")
            self.inputs = kwargs["inputs"]
        else:
            self.inputs = []
        if "nevents" in kwargs:
            self.nevents = kwargs["nevents"]
        else:
            self.nevents = -1
        if "description" in kwargs:
            self.description = kwargs["description"]
        else:
            self.description = ""
        if "rand_seed" in kwargs:
            self.rand_seed = kwargs["rand_seed"]
        else:
            self.rand_seed = 1

    def execute(self):
        
        cl = [self.command]
        cl.extend(self.cmd_args())
                                  
        print "Component: executing '%s' with command %s" % (self.name, cl)
        proc = subprocess.Popen(cl, shell=False)
        proc.communicate()
                            
        return proc.returncode

    def cmd_exists(self):
        return subprocess.call("type " + self.command, shell=True, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

    def cmd_args(self):
        return self.args
    
    def setup(self):
        pass

    def cleanup(self):
        pass
    
class DummyComponent(Component):
    
    def __init__(self, **kwargs):
        print "DummyComponent: init"  
        Component.__init__(self, **kwargs)
        self.command = "dummy"
        
    def execute(self):
        print "DummyComponent: execute"
        
    def cmd_exists(self):
        return True
    
    def setup(self):
        print "DummyComponent: setup"
        
    def cleanup(self):
        print "DummyComponent: cleanup"
    

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
        if "job_num" in kwargs:
            self.job_num = kwargs["job_num"]
        else:
            self.job_num = 1
        if "output_files" in kwargs:
            self.output_files = kwargs["output_files"]
        else:
            self.output_files = {}
        if "output_dir" in kwargs:
            self.output_dir = kwargs["output_dir"]
            if self.output_dir:
                if not os.path.isabs(self.output_dir):
                    raise Exception("The output_dir should be absolute.")
        else:
            self.output_dir = None
        if "append_job_num" in kwargs:
            self.append_job_num = kwargs["append_job_num"]
        else:
            self.append_job_num = False
        if "job_num_pad" in kwargs:
            self.job_num_pad = kwargs["job_num_pad"]
        else:
            self.job_num_pad = 4
        if "ignore_return_codes" in kwargs:
            self.ignore_return_codes = kwargs["ignore_return_codes"]
        else:
            self.ignore_return_codes = False
        if "delete_existing" in kwargs:
            self.delete_existing = kwargs["delete_existing"]
        else:
            self.delete_existing = False
        if "inputs" in kwargs:
            self.inputs = kwargs["inputs"]
        else:
            self.inputs = {}

    def run(self):
        print "Job: running '%s'" % self.name
        if not len(self.components):
            raise Exception("Job has no components to run.")
        for i in range(0, len(self.components)):
            c = self.components[i]
            print "Job: executing '%s' with description '%s'" % (str(c.name), str(c.description))
            print "Job: command '%s' with inputs %s and outputs %s" % (c.command, str(c.inputs), str(c.outputs))
            retcode = c.execute()
            if not self.ignore_return_codes and retcode:
                raise Exception("Job: error code '%d' returned by '%s'" % (retcode, str(c.name)))

    def setup(self):
        if not os.path.exists(self.rundir):
            os.makedirs(self.rundir)
        os.chdir(self.rundir)
        for c in self.components:
            print "Job: setting up '%s'" % (c.name)
            c.rundir = self.rundir
            c.setup()
            if not c.cmd_exists():
                raise Exception("Command '%s' does not exist for '%s'." % (c.command, c.name))

    def cleanup(self):
        for c in self.components:
            print "Job: running cleanup for '%s'" % str(c.name)
            c.cleanup()
        if self.delete_rundir:
            print "Job: deleting run dir '%s'" % self.rundir
            shutil.rmtree(self.rundir)
    
    def copy_output_files(self):
        
        if self.output_dir:
        
            if not os.path.exists(self.output_dir):
                print "Job: creating output dir '%s'" % self.output_dir
                os.makedirs(self.output_dir, 0755)
               
            for output_file in self.output_files:
                if isinstance(output_file, basestring):
                    src_file = os.path.join(self.rundir, output_file)
                    dest_file = os.path.join(self.output_dir, output_file)
                elif isinstance(output_file, dict):
                    src, dest = output_file.iteritems().next()
                    src_file = os.path.join(self.rundir, src)
                    if not os.path.isabs(dest):
                        dest_file = os.path.join(self.output_dir, dest)
                    else:
                        dest_file = dest
                if self.append_job_num:
                    base,ext = os.path.splitext(dest_file)
                    dest_file = base + "_" + (("%0" + str(self.job_num_pad) + "d") % self.job_num) + ext
                if os.path.isfile(dest_file):
                    if self.delete_existing:
                        print "Job: deleting existing file at '%s'" % dest_file
                        os.remove(dest_file)
                    else:
                        raise Exception("Output file '%s' already exists." % dest_file)
                
                print "Job: copying '%s' to '%s'" % (src_file, dest_file)
                shutil.copyfile(src_file, dest_file)      
        else:
            
            print "Job: No output_dir was set so files will not be copied."
            
    def copy_input_files(self):
        for dest,src in self.inputs.iteritems():
            if not os.path.isabs(src):
                raise Exception("The input source file '%s' is not an absolute path." % src)
            if os.path.dirname(dest):
                raise Exception("The input file destination '%s' is not valid." % dest)
            print "Job: copying input '%s' to '%s'" % (src, os.path.join(self.rundir, dest))
            shutil.copyfile(src, os.path.join(self.rundir, dest))
            
class JobParameters:
    
    def __init__(self, filename):
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
                    
class JobStandardArgs:
    
    def create_parser(self):

        parser = argparse.ArgumentParser(description="Run an HPS MC job")
        parser.add_argument("-j", "--job",  help="Job number", type=int, default=1)
        parser.add_argument("-o", "--output-dir", help="Job output dir", default=os.getcwd())
        parser.add_argument("-s", "--seed", help="Job random seed", type=int, default=1)
        parser.add_argument("params", nargs=1, help="Job params in JSON format")
        return parser

    def parse_args(self):
        
        parser = self.create_parser()
        cl = parser.parse_args()

        self.job = cl.job
        self.output_dir = cl.output_dir
        self.params = cl.params[0]
        self.seed = cl.seed
