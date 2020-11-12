import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager(dict):
    """Convinient way to load and manage all configuration files.
    This is just a bigger dict with some convinient methods.
    Does ConfigManager have config.yaml??? What came first, ConfigManager, or config.yaml???
    What does it config.yaml do???
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