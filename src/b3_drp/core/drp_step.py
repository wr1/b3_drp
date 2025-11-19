from pathlib import Path
from statesman import Statesman
from statesman.core.base import ManagedFile
from ..core.assign import assign_plies, load_config


class DrapeStep(Statesman):
    """Statesman step for draping plies onto the mesh."""

    workdir_key = "workdir"
    input_files = [
        ManagedFile(name="b3_msh/lm2.vtp", non_empty=True),
    ]
    output_files = ["b3_drp/draped.vtk"]
    dependent_sections = ["laminates"]

    def _execute(self):
        self.logger.info("Executing DrapeStep: Assigning plies to mesh.")
        config_dir = Path(self.config_path).parent
        workdir = config_dir / self.config["workdir"]
        grid_path = workdir / "b3_msh" / "lm2.vtp"
        matdb = self.config["matdb"]
        output_path = workdir / "b3_drp" / "draped.vtk"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = load_config(self.config_path)
        assign_plies(config_data, str(grid_path), matdb, str(output_path))
        self.logger.info(f"Draping completed, output saved to {output_path}")
