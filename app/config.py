from pydantic_settings import BaseSettings, SettingsConfigDict


####################################################################################################################################
# Important reading for setting environment variables: https://chatgpt.com/s/t_6962e79426a4819194633f55d9c553e7
# pydantic-settings loads variables in this order:
# 1. System environment variables (highest priority)
# 2. Variables from env_file (if provided)
# 3. Defaults (if any)

# So if we deploy and set variables like:

# ```
# export DATABASE_HOSTNAME=db.example.com
# export DATABASE_PASSWORD=supersecret
# ```

# Then those values will be used, even though we still have:
# ```
# env_file=".env"
# ```

# The `.env` file is simply ignored if the system variables exist.
####################################################################################################################################


# As per Pydantic version 1
# class Settings(BaseSettings):
#     database: str
#     database_hostname: str
#     database_port: str
#     database_password: str
#     database_name: str
#     database_username: str
#     secret_key: str
#     algorithm: str
#     access_token_expire_minutes: int

#     # In Pydantic (v1) and SQLModel, the nested Config class has a special meaning: 
#     # It is a declarative configuration pattern. Pydantic looks for a class literally named Config and uses its attributes to control behaviour.
#     class Config:
#         env_file = ".env"


# As per Pydantic version 2
class Settings(BaseSettings):
    database: str
    database_hostname: str
    database_port: int
    database_username: str
    database_password: str
    database_name: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

settings = Settings()
