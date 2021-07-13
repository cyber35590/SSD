from common.config_base import config, log
from agent.archive import make_archive


log.info("lancement de l'agent")

backup = config.get_backup_dirs()
temp = config.get_temp_dir()

path = make_archive(temp, backup)
log.info(path)


