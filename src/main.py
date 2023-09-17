from gooey import Gooey, GooeyParser, local_resource_path
import json, os, time, sys
current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
parent_directory = os.path.dirname(current_directory)
from cryosparc.tools import CryoSPARC

import datetime
import functools
print = functools.partial(print, flush=True)

global global_cnt
global_cnt = 0
global global_tot
global_tot = 9
FILENAME = 'workspace_latest.json'

def save_args(args):
       with open(FILENAME, 'w') as file:
              json.dump(vars(args), file, indent=1)
       print(f'Settings saved to {FILENAME}')

       # Also save a copy with a timestamp
       timestamp = time.strftime('%Y%m%d_%H%M%S')
       filename = f'workspace_{timestamp}.json'
       with open(filename, 'w') as file:
              json.dump(vars(args), file, indent=1)
       print(f'Settings saved to {filename}')


def load_args(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}

@Gooey(program_name="Fully Atomatic CryoSPARC Workflow Tool", 
       program_description="Summed Micrographs -> Homogeneous Refined Map",
       tabbed_groups=True,
       navigation='Tabbed',
       advanced=True,
       optional_cols=2,
       required_cols=1,
       image_dir=local_resource_path('./images'),
       progress_regex=r"^progress: (?P<current>\d+)/(?P<total>\d+)$",
       progress_expr="current / total * 100",
       timing_options = {
        'show_time_remaining':True,
        'hide_time_remaining_on_complete':True,
       },
       hide_progress_msg=True,
       show_preview_warning=False,
       menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'Automatic CryoSPARC Workflow Tool',
                'description': '    This tool is designed to automate the process of importing summed micrographs \n into CryoSPARC, and then running a homogeneous refinement job.',
                'version': '0.0.1',
                'copyright': '2023',
                'website': 'https://open-em.cn/',
                'developer': 'https://github.com/Cellverse/',
                'license': 'MIT'
            },  {
                'type': 'Link',
                'menuTitle': 'Visit Our Site',
                'url': 'https://open-em.cn/'
            }]
        },{
        'name': 'Help',
        'items': [{
            'type': 'Link',
            'menuTitle': 'Documentation',
            'url': 'https://open-em.cn/'
        }]
       }]
)
def main():
       parser = GooeyParser()
       if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
              previous_args = load_args(sys.argv[1])
       else:
              previous_args = load_args(FILENAME)

       # Group: User Information
       user_info = parser.add_argument_group("User Info")
       user_info.add_argument("--License", required=True, default=previous_args.get('License', ''), help="CryoSPARC license ID", widget="PasswordField")
       user_info.add_argument('--Compute_num_cpus', required=True, default=previous_args.get('Compute_num_cpus', '8'), help="Number of CPUs to use for computation")
       user_info.add_argument("--Email", required=True, default=previous_args.get('Email', ''), help="CryoSPARC account")
       user_info.add_argument("--Password", required=True, default=previous_args.get('Password', ''), help="CryoSPARC password", widget="PasswordField")
       user_info.add_argument("--Host", required=True, default=previous_args.get('Host', '10.19.126.6'), help="CryoSPARC host address")
       user_info.add_argument("--Port", type=int, required=True, default=previous_args.get('Port', 39000), help="CryoSPARC port number")
       user_info.add_argument("--Project_ID", required=True, default=previous_args.get('Project_ID', ''), help="CryoSPARC Project ID")
       user_info.add_argument("--Workspace_title", required=True, default=previous_args.get('Workspace_title', ''), help="CryoSPARC Workspace title")
       user_info.add_argument("--Workspace_desc", default=previous_args.get('Workspace_desc', 'No description.'), help="CryoSPARC Workspace description")

       # Group: Micrographs Information
       mics_info = parser.add_argument_group("Import Micrographs")
       mics_info.add_argument('--Micrographs_data_path', default=previous_args.get('Micrographs_data_path', ''), required=True, help="Absolute path, wildcard-expression (e.g. /mount/data/somewhere/*.mrcs) that will be imported. MRC format supported.")
       mics_info.add_argument('--Pize_A', required=True, default=previous_args.get('Pize_A', ''), help="Pixel size of the micrograph data in Angstroms")
       mics_info.add_argument('--Accel_kv', required=True, default=previous_args.get('Accel_kv', '300'), help="Accelaration voltage in kV")
       mics_info.add_argument('--Cs_mm', default=previous_args.get('Cs_mm', '2.7'), help="Spherical aberration in mm")
       mics_info.add_argument('--Dose_eA2', default=previous_args.get('Dose_eA2', '20'), help="Dose per exposure in e/A^2")

       # Group: Topaz Extract
       topaz_extract_ = parser.add_argument_group("Topaz Extract")
       topaz_extract_.add_argument('--Exec_path', required=True, default=previous_args.get('Exec_path', ''), help="Absolute path that points to your Topaz executable file that is compiled for the correct CUDA version.")
       topaz_extract_.add_argument('--Pretrained', default=previous_args.get('Pretrained', 'ResNet8 (32 units)'),widget="Dropdown", choices=['ResNet8 (32 units)', 'ResNet8 (64 units)', 'ResNet16 (32 units)', 'ResNet16 (64 units)'],help="Select pretrained model to use for extraction.")
       topaz_extract_.add_argument('--Downsample_scale', default=previous_args.get('Downsample_scale', '8'), help="Rescaling factor to downsample images by. Only required when using provided pretrained model.")
       topaz_extract_.add_argument('--Extract_radius', default=previous_args.get('Extract_radius', '12'), help="Radius of regions to extract from micrograph. If negative, a radius value will be calculated using the other radius parameters.")
       topaz_extract_.add_argument('--Box_size_pix', default=previous_args.get('Box_size_pix', '360'), help="Size of box to be extracted from micrograph.")

       # Group: Homogeneous Refinement
       homo_refine = parser.add_argument_group("Homogeneous Refinement")
       homo_refine.add_argument('--Refine_symmetry', default=previous_args.get('Refine_symmetry','C1'), help='Symmetry String (C, D, I, O, T). E.g. C1, D7, C4, etc')
       homo_refine.add_argument('--Refine_defocus_refine', action='store_true', widget='CheckBox', default=previous_args.get('Refine_defocus_fine', True), help='Minimize over per-particle defocus at each iteration of refinement. The optimal defocus will be used for backprojection as well, and will be written out at each iteration. Defocus refinement will start only once refinement with current defocus values converges. Beware that with small/disordered proteins, defocus refinement may actually make resolutions worse.')
       homo_refine.add_argument('--Refine_ctf_global_refine', action='store_true', widget='CheckBox', default=previous_args.get('Refine_ctf_global_refine', True), help='Optimize the per-exposure-group CTF parameters (for higher-order aberrations) at each iteration of refinement. The optimal CTF will be used for backprojection as well, and will be written out at each iteration. CTF refinement will start only once refinement with current CTF values converges. Beware that with small/disordered proteins, CTF refinement may actually make resolutions worse.')

       args = parser.parse_args()
       save_args(args)

       cs, project, workspace, lane = create_cryosparc_workspace(args)
       import_micrographs_job       = import_micrographs(workspace, lane, args)
       ctf_estimation_job           = ctf_estimation(import_micrographs_job, workspace, lane, args)
       topaz_extract_job            = topaz_extract(ctf_estimation_job, workspace, lane, args)
       extract_particles_job        = extract_particles(topaz_extract_job, workspace, lane, args)
       twoD_classify_job            = twoD_classify(extract_particles_job, workspace, lane)
       select_2D_job                = select_2D(twoD_classify_job, workspace)
       abinit_job                   = abinit_reconstruction(select_2D_job, workspace, lane)
       refine_job                   = homo_refinement(abinit_job, workspace, lane, args)

       return 

def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.datetime.now()
        print('')
        print(f"Start Job: *** {func.__name__} *** at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        result = func(*args, **kwargs)

        end_time = datetime.datetime.now()
        duration = end_time - start_time
        print(f"End Job: *** {func.__name__} *** at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total time taken for {func.__name__}: {duration}")
        print('')
        global global_cnt, global_tot
        global_cnt += 1
        print("progress: {}/{}".format(global_cnt, global_tot))

        return result
 
    return wrapper
 
@timed
def create_cryosparc_workspace(args):
       CryoSPARC_Connect_Infomation = {'license': args.License,'email': args.Email,'password': args.Password,'host': args.Host,'base_port': args.Port}
       cs = CryoSPARC(**CryoSPARC_Connect_Infomation)
       project = cs.find_project(args.Project_ID)
       CryoSPARC_WorkSpace_Infomation = {'project_uid': args.Project_ID,'title': args.Workspace_title,'desc': args.Workspace_desc}
       workspace = cs.create_workspace(**CryoSPARC_WorkSpace_Infomation)
       lane = cs.get_lanes()[0]['name']
       return cs, project, workspace, lane
@timed
def import_micrographs(workspace, lane, args):
       Import_Micrographs_Infomation = {'blob_paths': args.Micrographs_data_path,"psize_A": args.Pize_A,"accel_kv": args.Accel_kv,"cs_mm": args.Cs_mm,"total_dose_e_per_A2": args.Dose_eA2,"compute_num_cpus": args.Compute_num_cpus,  }
       import_micrographs_job = workspace.create_job("import_micrographs", params=Import_Micrographs_Infomation)
       import_micrographs_job.queue(lane), import_micrographs_job.wait_for_done()
       return import_micrographs_job
@timed
def ctf_estimation(import_micrographs_job, workspace, lane, args):
       CTF_Estimation_Infomation = {'compute_num_cpus': args.Compute_num_cpus}
       ctf_estimation_job = workspace.create_job("ctf_estimation", connections={'exposures': (import_micrographs_job.uid, 'imported_micrographs')}, params=CTF_Estimation_Infomation)
       ctf_estimation_job.queue(lane), ctf_estimation_job.wait_for_done()
       return ctf_estimation_job
@timed
def topaz_extract(ctf_estimation_job, workspace, lane, args):
       Topaz_Extract_Infomation = {'exec_path': args.Exec_path,'num_distribute': args.Compute_num_cpus,'num_workers': args.Compute_num_cpus,'pretrained': args.Pretrained,'scale': args.Downsample_scale,'radius': args.Extract_radius}
       topaz_extract_job = workspace.create_job("topaz_extract",connections={'micrographs': (ctf_estimation_job.uid, 'exposures_success')},params=Topaz_Extract_Infomation)
       topaz_extract_job.queue(lane), topaz_extract_job.wait_for_done()
       return topaz_extract_job
@timed
def extract_particles(topaz_extract_job, workspace, lane, args):
       Extract_Particles_Infomation = {'box_size_pix': args.Box_size_pix,'compute_num_cores': args.Compute_num_cpus,}
       extract_particles_job = workspace.create_job("extract_micrographs_cpu_parallel",connections={"micrographs": (topaz_extract_job.uid, "micrographs"),"particles": (topaz_extract_job.uid, "particles"),},params=Extract_Particles_Infomation,)
       extract_particles_job.queue(lane), extract_particles_job.wait_for_done()
       return extract_particles_job
@timed       
def twoD_classify(extract_particles_job, workspace, lane):
       twoD_Classification_Infomation = {'class2D_K': 50,}
       twoD_classify_job = workspace.create_job("class_2D",connections={'particles': (extract_particles_job.uid, 'particles')},params=twoD_Classification_Infomation,)
       twoD_classify_job.queue(lane), twoD_classify_job.wait_for_done()
       return twoD_classify_job
@timed       
def select_2D(twoD_classify_job, workspace):
       select_2D_job = workspace.create_job("select_2D",connections={"particles": (twoD_classify_job.uid, "particles"),"templates": (twoD_classify_job.uid, "class_averages"),},)
       select_2D_job.queue(), select_2D_job.wait_for_status("waiting")
       class_info = select_2D_job.interact("get_class_info")
       for c in class_info:
              if 1.0 < c["res_A"] < 15.0 and c["num_particles_total"] > 100:
                     select_2D_job.interact("set_class_selected",{"class_idx": c["class_idx"],"selected": True,},)
       select_2D_job.interact("finish")
       select_2D_job.wait_for_done()
       return select_2D_job
@timed
def abinit_reconstruction(select_2D_job, workspace, lane):
       abinit_job = workspace.create_job("homo_abinit",connections={"particles": (select_2D_job.uid, "particles_selected")},)
       abinit_job.queue(lane), abinit_job.wait_for_done()
       return abinit_job
@timed
def homo_refinement(abinit_job, workspace, lane, args):
       Homogeneous_Refinement_Infomation = {'refine_symmetry': args.Refine_symmetry,'refine_defocus_refine': args.Refine_defocus_refine,'refine_ctf_global_refine': args.Refine_ctf_global_refine,}
       refine_job = workspace.create_job("homo_refine_new",connections={"particles": (abinit_job.uid, "particles_all_classes"),"volume": (abinit_job.uid, "volume_class_0"),},params=Homogeneous_Refinement_Infomation)
       refine_job.queue(lane), refine_job.wait_for_done()
       return refine_job
       
if __name__ == "__main__":
       main()


       
       
       
       

 

       
       
       
       
       
       
       
