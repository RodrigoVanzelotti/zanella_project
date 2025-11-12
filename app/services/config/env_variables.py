import os
from dotenv import load_dotenv, set_key, dotenv_values

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(current_dir))

dotenv_file = "dev.settings.config.env"
dotenv_path = os.path.join(app_dir, "config", dotenv_file) 

def set_env_variables_from_dotenv():
    # load variables from .env file
    env_variables = dotenv_values(dotenv_path)

    for key, value in env_variables.items():
        os.environ[key] = value
