"""Useful functions and class to manage input/output and config"""
import csv
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

# AUXILIARY FUNCTION

def init_logger(config_dict):
    logging.config.dictConfig(config_dict)

# CONFIG MANAGEMENT

def import_config(config_folder=None):
    Config = ConfigManager()
    config_path = Path(config_folder or r'config')
    if not config_path.exists():
        logger.warning(r"config folder doesn't exist at folder path %s. Create new config from template.yaml and save in .\config", config_path)
        Config.create_template('template.yaml',r'config')
        Config.loads_yaml(r'config')
    else:
        Config.loads_yaml(config_folder)
    return Config

class ConfigManager(dict):
    """Convinient way to load and manage all configuration files.
    This is just a bigger dict with some convinient methods.
    """
    
    def load_yaml(self, config_path: str) -> None:
        """Load yaml file, convert to dict, and update to the main dict

        Args:
            config_path (str): path to configuration file. Accept yaml format.
        """
        config_path = Path(config_path)
        config = config_path.stem
        values = yaml.safe_load(config_path.read_bytes())
        if config in self:
            logger.warning('%s is already loaded. Override old settings.', config)
        self.update({config:values})
        
    def loads_yaml(self, config_folder: str) -> None:
        """Load multiple yaml file in a folder"""
        folder_path = Path(config_folder)
        for config_path in folder_path.glob('*.yaml'):
            self.load_yaml(config_path)
        
    def create_template(self, template_path: str, destination_folder: str) -> None:
        template_path = Path(template_path)
        destination_folder = Path(destination_folder)
        destination_folder.mkdir(parents=True, exist_ok=True)
        template = yaml.safe_load(template_path.read_bytes())
        for config in template:
            with open(destination_folder / f'{config}.yaml', 'w') as f:
                yaml.dump(template[config], f)

# I/O MANAGEMENT

def check_xls(b64_data):
    """check hex signature of b64 file"""
    return len(b64_data) >= 8 and b64_data[:8].hex() == 'd0cf11e0a1b11ae1'

def check_xlsx(b64_data):
    """check hex signature of b64 file"""
    return len(b64_data) >= 4 and b64_data[:4].hex() == '504b0304'

def generate_from_csv(file_object):
    reader = csv.DictReader(file_object)
    for i,row in enumerate(reader):
        yield i,row
